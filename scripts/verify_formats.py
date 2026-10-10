"""Run after verify_api; exercise PNG and large WEBP through real inference."""
import time,json
from pathlib import Path
import httpx
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
client=httpx.Client(base_url='http://127.0.0.1:8000',timeout=120)
results=[]
for name,mime in [('upload-check.png','image/png'),('high-resolution.webp','image/webp')]:
    path=ROOT/'runtime'/name
    if not path.exists():
        image=Image.open(ROOT/'public/samples'/('sacramento.jpg' if mime=='image/png' else 'davis.jpg'))
        if mime=='image/webp': image=image.resize((2400,1800))
        image.save(path)
    width,height=Image.open(path).size
    response=client.post('/api/analyze',files={'file':(name,path.read_bytes(),mime)});response.raise_for_status();key=response.json()['job_id']
    for _ in range(240):
        job=client.get('/api/jobs/'+key).json()
        if job['status']!='running':break
        time.sleep(.5)
    assert job['status']=='complete',job
    r=job['result'];assert (r['width'],r['height'])==(width,height)
    assert all(0<=x<=width and 0<=y<=height for region in r['regions'] for x,y in region['polygon'])
    roofs=[v for v in r['regions'] if v['kind']=='roof'];assert roofs
    row={'format':mime,'display_dimensions':[width,height],'inference_dimensions':r['inference_size'],'roof_candidates':len(roofs),'inference_seconds':r['inference_seconds']}
    results.append(row);print(row,flush=True)
(ROOT/'runtime'/'format-checks.json').write_text(json.dumps(results,indent=2))
