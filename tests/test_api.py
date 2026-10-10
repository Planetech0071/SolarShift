from io import BytesIO
from PIL import Image
from fastapi.testclient import TestClient
from backend.app import app
from backend import vision
from backend.vision import mask_polygon
import numpy as np
import pytest

client=TestClient(app)

def test_health_and_samples():
    assert client.get('/api/health').status_code==200
    samples=client.get('/api/samples').json()
    assert len(samples)==2
    for s in samples:
        assert s['meters_per_pixel']>0
        assert client.get(s['url']).status_code==200

def test_corrupt_image_rejected():
    r=client.post('/api/analyze',files={'file':('bad.png',b'corrupt','image/png')})
    assert r.status_code==422

def test_unsupported_image_and_small_image_rejected():
    for format,size,code in [('GIF',(100,100),415),('PNG',(10,10),422)]:
        b=BytesIO();Image.new('RGB',size).save(b,format=format)
        r=client.post('/api/analyze',files={'file':('file',b.getvalue(),'image/png')})
        assert r.status_code==code

def test_upload_size_limit():
    r=client.post('/api/analyze',files={'file':('large.jpg',b'x'*(20*1024*1024+1),'image/jpeg')})
    assert r.status_code==413

def test_mask_vector_coordinates():
    mask=np.zeros((100,200),np.uint8);mask[20:70,30:140]=1
    points=mask_polygon(mask)
    assert min(x for x,y in points)==30
    assert min(y for x,y in points)==20
    assert max(x for x,y in points)==139
    assert max(y for x,y in points)==69

@pytest.mark.parametrize('body',[{'regions':[],'settings':{}},{'regions':[{'id':'x','polygon':[[0,0],[10,10],[0,10],[10,0]]}],'settings':{}},{'regions':[{'id':'x','polygon':[[0,0],[10,0],[10,10]],'height':-1}],'settings':{}},{'regions':[{'id':'x','polygon':[[0,0],[10,0],[10,10]]}],'settings':{'timezone':'invalid'}}])
def test_invalid_simulation_inputs(body):
    assert client.post('/api/simulate',json=body).status_code==422

def test_non_roof_simulation_rejected():
    r=client.post('/api/simulate',json={'regions':[{'id':'x','kind':'vegetation','polygon':[[0,0],[10,0],[10,10]]}],'settings':{}})
    assert r.status_code==422

def test_unknown_job():
    assert client.get('/api/jobs/not-a-job').status_code==404

def test_serverless_analysis_returns_result_without_polling(monkeypatch):
    monkeypatch.setenv('VERCEL','1')
    result={'regions':[],'width':100,'height':100}
    monkeypatch.setattr(vision,'analyze',lambda image:result)
    b=BytesIO();Image.new('RGB',(100,100)).save(b,format='PNG')
    r=client.post('/api/analyze',files={'file':('image.png',b.getvalue(),'image/png')})
    assert r.status_code==202
    assert r.json()=={'status':'complete','result':result}
    assert client.get('/api/health').json()['upload_limit_mb']==4

def test_serverless_upload_limit(monkeypatch):
    monkeypatch.setenv('VERCEL','1')
    r=client.post('/api/analyze',files={'file':('large.jpg',b'x'*(4*1024*1024+1),'image/jpeg')})
    assert r.status_code==413

def test_serverless_inference_failure_is_retryable(monkeypatch):
    monkeypatch.setenv('VERCEL','1')
    def failure(image): raise RuntimeError('Internal model details')
    monkeypatch.setattr(vision,'analyze',failure)
    b=BytesIO();Image.new('RGB',(100,100)).save(b,format='PNG')
    r=client.post('/api/analyze',files={'file':('image.png',b.getvalue(),'image/png')})
    assert r.status_code==503
    assert 'Internal model details' not in r.text
