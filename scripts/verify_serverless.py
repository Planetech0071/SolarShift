"""Exercise actual CPU model inference and physics with the stateless hosting path."""
import json
import os
import time
from pathlib import Path

os.environ['VERCEL'] = '1'
os.environ['SOLARSHIFT_CPU'] = '1'

from fastapi.testclient import TestClient
from backend.app import app

ROOT = Path(__file__).resolve().parents[1]


def main():
    reports = []
    with TestClient(app) as client:
        assert client.get('/api/health').json()['on_demand']
        for sample in client.get('/api/samples').json():
            start = time.perf_counter()
            data = (ROOT / 'public' / sample['url'].lstrip('/')).read_bytes()
            response = client.post('/api/analyze', files={'file': (sample['id']+'.jpg', data, 'image/jpeg')})
            response.raise_for_status()
            job = response.json()
            assert job['status'] == 'complete' and 'job_id' not in job
            result = job['result']
            assert result['device'] == 'cpu'
            roofs = [r for r in result['regions'] if r['kind'] == 'roof']
            assert len(roofs) >= 2
            settings = {k: sample[k] for k in ('latitude', 'longitude', 'timezone', 'meters_per_pixel', 'north_angle')}
            settings['date'] = '2026-06-21'
            response = client.post('/api/simulate', json={'regions': result['regions'], 'settings': settings})
            response.raise_for_status()
            simulation = response.json()
            assert simulation['roofs'][simulation['ranking'][0]]['daily_kwh'] > 0
            assert all(v['power_kw'] == 0 for frame in simulation['frames'] if frame['elevation'] <= 0 for v in frame['roofs'].values())
            report = {'sample': sample['id'], 'roofs': len(roofs), 'device': result['device'], 'inference_seconds': result['inference_seconds'], 'workflow_seconds': round(time.perf_counter()-start, 2)}
            reports.append(report)
            print(report, flush=True)
    (ROOT / 'runtime').mkdir(exist_ok=True)
    (ROOT / 'runtime' / 'serverless-check.json').write_text(json.dumps(reports, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
