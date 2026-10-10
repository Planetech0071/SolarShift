import io, json, logging, time, uuid, threading, os
from contextlib import asynccontextmanager
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from PIL import Image, ImageOps, UnidentifiedImageError
from .contracts import SimulationRequest
from .physics import simulate
from . import vision

ROOT=Path(__file__).resolve().parents[1]
pool=ThreadPoolExecutor(max_workers=1)
jobs={}; jobs_lock=threading.Lock()
Image.MAX_IMAGE_PIXELS=40_000_000

def is_serverless(): return os.getenv('VERCEL')=='1'

@asynccontextmanager
async def lifespan(app):
    if not is_serverless(): pool.submit(vision.warmup)
    yield

app=FastAPI(title='SolarShift',version='1.0.0',lifespan=lifespan)

@app.middleware('http')
async def response_headers(request,call_next):
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='same-origin'
    if request.url.path.startswith('/api/jobs/'):
        response.headers['Cache-Control']='no-store'
    return response

@app.get('/api/health')
def health(): return {'ok':True,'vision':vision.status,'physics':'pvlib SPA / Ineichen','on_demand':is_serverless(),'upload_limit_mb':4 if is_serverless() else 20}

@app.get('/api/samples')
def samples(): return json.loads((ROOT/'public'/'samples'/'index.json').read_text())

def run_job(key,image):
    def progress(value,label):
        with jobs_lock: jobs[key].update(progress=value,label=label)
    try:
        result=vision.analyze(image,progress)
        with jobs_lock: jobs[key].update(status='complete',progress=100,label='Analysis complete',result=result)
    except Exception:
        logging.exception('Image analysis failed')
        with jobs_lock: jobs[key].update(status='error',label='Model inference failed. Check server logs or use manual roof drawing.',error='Model inference unavailable. Check /api/health and server logs.')

@app.post('/api/analyze',status_code=202)
async def analyze(file: UploadFile):
    with jobs_lock:
        if sum(j['status']=='running' for j in jobs.values())>=3: raise HTTPException(429,'Analysis queue is full. Please retry shortly.')
    limit_mb=4 if is_serverless() else 20
    data=await file.read(limit_mb*1024*1024+1)
    if len(data)>limit_mb*1024*1024: raise HTTPException(413,f'Use an image smaller than {limit_mb} MB.')
    try:
        image=Image.open(io.BytesIO(data))
        if image.format not in ('JPEG','PNG','WEBP'): raise HTTPException(415,'Choose a JPG, PNG or WEBP image.')
        if image.width<64 or image.height<64: raise HTTPException(422,'Use an image at least 64 × 64 pixels.')
        if image.width>20000 or image.height>20000: raise HTTPException(422,'Maximum image dimension is 20000 pixels.')
        image=ImageOps.exif_transpose(image).convert('RGB'); image.load()
    except HTTPException: raise
    except (UnidentifiedImageError,OSError,ValueError,Image.DecompressionBombError,Image.DecompressionBombWarning): raise HTTPException(422,'This image is corrupt or too large to decode. Try another image.')
    if is_serverless():
        # A response owns all inference work. No job polling depends on instance affinity.
        try:
            result=await run_in_threadpool(vision.analyze,image)
        except Exception as e:
            logging.exception('Image analysis failed')
            raise HTTPException(503,'Image analysis is unavailable. Please retry shortly.') from e
        return {'status':'complete','result':result}
    key=uuid.uuid4().hex
    with jobs_lock:
        now=time.time()
        if sum(j['status']=='running' for j in jobs.values())>=3: raise HTTPException(429,'Analysis queue is full. Please retry shortly.')
        for old in list(jobs):
            if jobs[old]['status']!='running' and now-jobs[old]['created']>3600: del jobs[old]
        completed=[k for k,j in jobs.items() if j['status']!='running']
        while len(jobs)>=50 and completed:
            del jobs[completed.pop(0)]
        jobs[key]={'status':'running','progress':5,'label':'Image validated · preparing tiles','created':now}
    pool.submit(run_job,key,image)
    return {'job_id':key}

@app.get('/api/jobs/{key}')
def job(key:str):
    with jobs_lock:
        if key not in jobs: raise HTTPException(404,'Analysis expired. Please run it again.')
        return dict(jobs[key])

@app.post('/api/simulate')
def simulation(request:SimulationRequest):
    if not any(r.kind=='roof' for r in request.regions): raise HTTPException(422,'Draw or detect at least one rooftop.')
    try: return simulate(request.regions,request.settings)
    except Exception as e:
        logging.exception('Simulation failed'); raise HTTPException(422,'Unable to simulate these settings. Check date, timezone and polygons.') from e

app.mount('/',StaticFiles(directory=ROOT/'public',html=True),name='frontend')
