"""Download reproducible public-domain USGS/NAIP orthophotos, never generated imagery."""
import json, math, ssl
from pathlib import Path
import httpx
from PIL import Image
from io import BytesIO

ROOT=Path(__file__).resolve().parents[1]
SAMPLES=[('davis','Davis · California',38.5465,-121.7442),('sacramento','Sacramento · California',38.5721,-121.489)]

def fetch():
    dest=ROOT/'public'/'samples'; dest.mkdir(parents=True,exist_ok=True)
    metadata=[]
    for key,name,lat,lon in SAMPLES:
        ground_width,ground_height=220,165
        c=math.cos(math.radians(lat)); radius=6378137
        x=radius*math.radians(lon); y=radius*math.log(math.tan(math.pi/4+math.radians(lat)/2))
        w,h=ground_width/c,ground_height/c
        bbox=[x-w/2,y-h/2,x+w/2,y+h/2]
        params={'bbox':','.join(map(str,bbox)),'bboxSR':3857,'imageSR':3857,'size':'1200,900','format':'jpg','f':'image'}
        base='https://imagery.nationalmap.gov/arcgis/rest/services/USGSNAIPImagery/ImageServer/exportImage'
        r=httpx.get(base,params=params,timeout=90,follow_redirects=True,verify=ssl.create_default_context()); r.raise_for_status()
        im=Image.open(BytesIO(r.content)); im.save(dest/f'{key}.jpg',quality=95)
        metadata.append({'id':key,'name':name,'latitude':lat,'longitude':lon,'timezone':'America/Los_Angeles','meters_per_pixel':ground_width/1200,'north_angle':0,'url':f'/samples/{key}.jpg','source':'USGS National Map orthoimagery / USDA NAIP','license':'US government public domain imagery; see ATTRIBUTION.md','download_url':str(r.url),'extent_epsg3857':bbox,'dimensions':[1200,900]})
        print(key,im.size,len(r.content))
    (dest/'index.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')

if __name__=='__main__': fetch()
