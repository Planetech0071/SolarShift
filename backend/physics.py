"""pvlib solar physics + opaque extruded-polygon shadows at each receiving roof height."""
import math
import numpy as np
import pandas as pd
import pvlib
from shapely.geometry import Polygon
from shapely.affinity import translate
from shapely.ops import unary_union
from shapely import contains_xy
from .contracts import Region, Settings

def shadow_vector(azimuth: float, elevation: float, height: float, scale: float, north_angle: float=0):
    if elevation <= 0 or height <= 0: return (0.0, 0.0)
    # North is image-up at zero rotation; azimuth clockwise from true north.
    a = math.radians(azimuth + north_angle)
    length = height / math.tan(math.radians(elevation)) / scale
    return (-math.sin(a)*length, math.cos(a)*length)

def project_shadow(polygon: Polygon, dx: float, dy: float):
    """Sweep an arbitrary simple footprint; preserve concavity instead of convexifying it."""
    coords=list(polygon.exterior.coords)
    pieces=[polygon, translate(polygon, xoff=dx, yoff=dy)]
    for a,b in zip(coords, coords[1:]):
        quad=Polygon([a,b,(b[0]+dx,b[1]+dy),(a[0]+dx,a[1]+dy)])
        if quad.area > 1e-9: pieces.append(quad)
    return unary_union(pieces)

def sample_roof(polygon: Polygon):
    # Adaptive rectangular lattice in original image coordinates. Up to ~225 samples.
    x0,y0,x1,y1=polygon.bounds
    step=max(math.sqrt(polygon.area/180), max(x1-x0,y1-y0)/20, 1)
    xx,yy=np.meshgrid(np.arange(x0+step/2,x1,step), np.arange(y0+step/2,y1,step))
    x,y=xx.ravel(),yy.ravel()
    inside=contains_xy(polygon,x,y)
    pts=np.column_stack([x[inside],y[inside]])
    if len(pts)==0:
        p=polygon.representative_point(); pts=np.array([[p.x,p.y]])
    return pts, step

def simulate(regions: list[Region], s: Settings):
    # Local civil day, including DST boundaries. Explicit timezone avoids longitude/time mismatch.
    start=pd.Timestamp(s.date).tz_localize(s.timezone)
    end=pd.Timestamp(s.date + pd.Timedelta(days=1)).tz_localize(s.timezone)
    times=pd.date_range(start,end,freq='10min')
    solar=pvlib.solarposition.get_solarposition(times,s.latitude,s.longitude,method='nrel_numpy')
    clear=pvlib.location.Location(s.latitude,s.longitude,s.timezone,altitude=0).get_clearsky(times,model='ineichen',solar_position=solar,linke_turbidity=s.turbidity)
    daylight=solar.apparent_elevation.to_numpy()>0
    clear.loc[~daylight,['ghi','dni','dhi']]=0
    roofs=[r for r in regions if r.kind=='roof']
    polygons={r.id:Polygon(r.polygon) for r in regions}
    points={r.id:sample_roof(polygons[r.id]) for r in roofs}
    beam={}; diffuse={}
    roof_data={}
    for r in roofs:
        poa=pvlib.irradiance.get_total_irradiance(r.tilt,r.azimuth,solar.apparent_zenith,solar.azimuth,clear.dni,clear.ghi,clear.dhi,model='isotropic',albedo=0.2)
        beam[r.id]=np.where(daylight,poa.poa_direct.to_numpy(),0)
        diffuse[r.id]=np.where(daylight,poa.poa_diffuse.to_numpy(),0)
        area=polygons[r.id].area*s.meters_per_pixel**2
        panel_count=math.floor(area*s.coverage/s.panel_area)
        usable=panel_count*s.panel_area
        capacity=usable*s.efficiency # 1 kW/m² STC
        pts,step=points[r.id]
        roof_data[r.id]={'id':r.id,'area_m2':round(area,2),'usable_m2':round(usable,2),'panels':panel_count,'capacity_kwp':round(capacity,3),'samples':pts.round(2).tolist(),'sample_step':round(step,2),'daily_kwh':0,'sun_hours':0,'power_series':[],'shade_series':[]}
    frames=[]
    for k, row in enumerate(solar.itertuples()):
        elevation=float(row.apparent_elevation); azimuth=float(row.azimuth)
        frame={'minute':int((times[k].tz_localize(None)-start.tz_localize(None)).total_seconds()/60),'time':times[k].strftime('%H:%M'),'iso':times[k].isoformat(),'azimuth':round(azimuth,2),'elevation':round(elevation,2),'ghi':round(float(clear.ghi.iloc[k]),1),'roofs':{}}
        # Cache all blockers for each receiving plane; identical roof heights share projections.
        projected={}
        for r in roofs:
            pts,_=points[r.id]
            if not daylight[k]: shade=np.ones(len(pts),dtype=bool)
            else:
                if r.height not in projected:
                    pieces=[]
                    for caster in regions:
                        dh=caster.height-r.height
                        if dh<=0.01: continue
                        dx,dy=shadow_vector(azimuth,elevation,dh,s.meters_per_pixel,s.north_angle)
                        pieces.append(project_shadow(polygons[caster.id],dx,dy))
                    projected[r.height]=unary_union(pieces) if pieces else Polygon()
                # All objects taller than this receiving plane can block direct light.
                shadow=projected[r.height]
                shade=contains_xy(shadow,pts[:,0],pts[:,1])
            fraction=float(shade.mean()) if daylight[k] else 0.0
            poa=float(beam[r.id][k]*(1-fraction)+diffuse[r.id][k]) if daylight[k] else 0.0
            d=roof_data[r.id]
            power=d['capacity_kwp']*poa/1000*s.performance_ratio
            d['power_series'].append(round(power,4)); d['shade_series'].append(round(fraction,4))
            frame['roofs'][r.id]={'shade':round(fraction,3),'power_kw':round(power,3),'poa':round(poa,1),'sunlit':round(1-fraction,3) if daylight[k] else 0,'shaded_samples':np.flatnonzero(shade).tolist() if daylight[k] else []}
        frames.append(frame)
    hour_steps=np.diff(times.asi8)/3.6e12
    for r in roofs:
        d=roof_data[r.id]
        p=np.array(d['power_series']); d['daily_kwh']=round(float(np.sum((p[1:]+p[:-1])/2*hour_steps)),2)
        lit=np.array([f['roofs'][r.id]['sunlit'] for f in frames]); d['sun_hours']=round(float(np.sum((lit[1:]+lit[:-1])/2*hour_steps)),2)
    daylight_times=[f['time'] for f in frames[:-1] if f['elevation']>0]
    ranking=sorted(roof_data,key=lambda key:roof_data[key]['daily_kwh'],reverse=True)
    return {'frames':frames,'roofs':roof_data,'ranking':ranking,'sunrise':daylight_times[0] if daylight_times else None,'sunset':daylight_times[-1] if daylight_times else None,'method':'NREL SPA · Ineichen clear sky · isotropic POA · 10-minute trapezoidal integration','assumptions':s.model_dump(mode='json'),'sample_interval_minutes':10,'notice':'Preliminary clear-sky estimate. Confirm geometry, scale and heights. Clouds, terrain, wiring mismatch and diffuse shading are not modeled. Sunrise/sunset labels are the first/last positive-elevation 10-minute samples.'}
