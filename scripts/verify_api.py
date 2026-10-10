"""Exercise the running server against both real samples. Saves only actual computation."""
import argparse,json,ssl,time
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--base',default='http://127.0.0.1:8000')
    parser.add_argument('--prefix',default='')
    args=parser.parse_args();base=args.base.rstrip('/')
    out=ROOT/'runtime';out.mkdir(exist_ok=True)
    client=httpx.Client(timeout=300,verify=ssl.create_default_context(),follow_redirects=True)
    health=client.get(base+'/api/health').json();print('health',health)
    bad=client.post(base+'/api/analyze',files={'file':('bad.png',b'not an image','image/png')});assert bad.status_code==422;print('corrupt upload',bad.status_code)
    for sample in client.get(base+'/api/samples').json():
        response=client.get(base+sample['url']);response.raise_for_status();image=response.content
        started=time.perf_counter()
        upload=client.post(base+'/api/analyze',files={'file':(sample['id']+'.jpg',image,'image/jpeg')});upload.raise_for_status();job=upload.json()
        if 'result' not in job:
            key=job['job_id']
            for _ in range(200):
                job=client.get(base+f'/api/jobs/{key}').json()
                if job['status']!='running': break
                time.sleep(.5)
        assert job['status']=='complete',job
        result=job['result'];roofs=[r for r in result['regions'] if r['kind']=='roof'];assert len(roofs)>=2
        assert all(0<=x<=result['width'] and 0<=y<=result['height'] for r in roofs for x,y in r['polygon'])
        settings={k:sample[k] for k in ('latitude','longitude','timezone','meters_per_pixel','north_angle')};settings['date']='2026-06-21'
        start_sim=time.perf_counter();response=client.post(base+'/api/simulate',json={'regions':result['regions'],'settings':settings});response.raise_for_status();sim=response.json();elapsed=time.perf_counter()-start_sim
        assert sim['ranking'] and sim['roofs'][sim['ranking'][0]]['daily_kwh']>0
        assert all(f['ghi']==0 and all(v['power_kw']==0 for v in f['roofs'].values()) for f in sim['frames'] if f['elevation']<=0)
        report={'sample':sample['id'],'detected_roofs':len(roofs),'vegetation_regions':len(result['regions'])-len(roofs),'inference_seconds':result['inference_seconds'],'simulation_seconds':round(elapsed,2),'total_workflow_seconds':round(time.perf_counter()-started,2),'result':result,'simulation':sim}
        (out/f'{args.prefix}{sample["id"]}-verified.json').write_text(json.dumps(report),encoding='utf-8')
        print({k:v for k,v in report.items() if k not in ('result','simulation')},flush=True)

if __name__=='__main__':main()
