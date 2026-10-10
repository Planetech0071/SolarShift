import math
import numpy as np
import pytest
from shapely.geometry import Polygon, Point
from backend.physics import shadow_vector, project_shadow, simulate
from backend.contracts import Region, Settings, SimulationRequest

def roof(id='R1',x=0,y=0,height=8):
    return Region(id=id,polygon=[(x,y),(x+20,y),(x+20,y+20),(x,y+20)],height=height,tilt=0)

@pytest.mark.parametrize('azimuth,expected',[(0,(0,10)),(90,(-10,0)),(180,(0,-10)),(270,(10,0))])
def test_cardinal_shadows(azimuth,expected):
    assert shadow_vector(azimuth,45,10,1)==pytest.approx(expected,abs=1e-8)

def test_shadow_length_elevation_scale_north():
    assert shadow_vector(90,30,10,.5)[0]==pytest.approx(-20/math.tan(math.radians(30)))
    assert shadow_vector(0,45,10,1,90)==pytest.approx((-10,0),abs=1e-8)
    assert shadow_vector(0,-1,10,1)==(0,0)
    assert shadow_vector(0,45,0,1)==(0,0)

def test_partial_shadow_on_receiving_roof():
    caster=Polygon([(20,0),(30,0),(30,20),(20,20)])
    dx,dy=shadow_vector(90,45,10,1)
    projected=project_shadow(caster,dx,dy)
    receiver=Polygon([(0,0),(20,0),(20,20),(0,20)])
    assert projected.intersection(receiver).area/receiver.area==pytest.approx(.5)

def test_concavity_not_convex_hull():
    p=Polygon([(0,0),(20,0),(20,5),(5,5),(5,20),(0,20)])
    shadow=project_shadow(p,0,2)
    assert not shadow.contains(Point(15,15))

def test_night_energy_area_and_integration():
    s=Settings(latitude=45.4642,longitude=9.19,timezone='Europe/Rome',meters_per_pixel=.5,date='2026-06-21')
    data=simulate([roof()],s);r=data['roofs']['R1']
    assert r['area_m2']==100
    assert r['panels']==32 and r['usable_m2']==64
    assert r['capacity_kwp']==pytest.approx(14.08)
    assert all(f['roofs']['R1']['power_kw']==0 and f['roofs']['R1']['sunlit']==0 and f['ghi']==0 for f in data['frames'] if f['elevation']<=0)
    assert r['daily_kwh']==pytest.approx(np.trapz(r['power_series'],dx=1/6),abs=.01)
    assert 60<r['daily_kwh']<120

def test_location_and_height_change_shading():
    s=Settings(latitude=38.5,longitude=-121.7,timezone='America/Los_Angeles',meters_per_pixel=1,date='2026-06-21')
    regions=[roof(),roof('R2',x=22,height=8)]
    flat=simulate(regions,s)
    regions[1].height=30
    tall=simulate(regions,s)
    assert tall['roofs']['R1']['daily_kwh']<flat['roofs']['R1']['daily_kwh']
    assert any(0<f['roofs']['R1']['shade']<1 for f in tall['frames'])
    elsewhere=simulate(regions,s.model_copy(update={'latitude':-38.5}))
    assert elsewhere['roofs']['R1']['daily_kwh']!=tall['roofs']['R1']['daily_kwh']

def test_equal_height_casters_do_not_shade_roof():
    s=Settings(meters_per_pixel=1)
    single=simulate([roof()],s);pair=simulate([roof(),roof('R2',x=22)],s)
    assert single['roofs']['R1']['daily_kwh']==pair['roofs']['R1']['daily_kwh']

def test_scale_and_coverage_capacity_consistency():
    a=simulate([roof()],Settings(meters_per_pixel=.5,coverage=.6))['roofs']['R1']
    b=simulate([roof()],Settings(meters_per_pixel=1,coverage=.6))['roofs']['R1']
    assert b['area_m2']==4*a['area_m2']
    assert b['capacity_kwp']==pytest.approx(4*a['capacity_kwp'])

def test_polar_night_zero():
    data=simulate([roof()],Settings(latitude=85,longitude=0,timezone='UTC',date='2026-12-21'))
    assert data['roofs']['R1']['daily_kwh']==0
    assert data['sunrise'] is None

def test_dst_day_integrates_actual_hours():
    data=simulate([roof()],Settings(timezone='Europe/Rome',latitude=45,longitude=9,date='2026-03-29'))
    assert len(data['frames'])==139
    assert data['roofs']['R1']['daily_kwh']>0

def test_invalid_geometry_timezone_and_duplicate_ids():
    with pytest.raises(ValueError): Region(id='x',polygon=[(0,0),(20,20),(0,20),(20,0)])
    with pytest.raises(ValueError): Settings(timezone='not/a/timezone')
    with pytest.raises(ValueError): SimulationRequest(regions=[roof(),roof()],settings=Settings())
