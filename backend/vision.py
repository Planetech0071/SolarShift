"""Actual pretrained RF-DETR instance masks plus explicitly heuristic vegetation regions."""
import os, ssl, threading, time
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
from shapely.geometry import Polygon

MODEL_ID='merve/rf-detr-seg-satellite-buildings'
MODEL_REVISION='05b80dce9a57701724ad6a0fc052827c8b724257'
ROOT=Path(__file__).resolve().parents[1]
_model=None; _processor=None; _device='cpu'; _lock=threading.Lock()
status={'ready':False,'model':MODEL_ID,'device':'loading','error':None}

def load_model():
    global _model,_processor,_device
    if _model is not None: return
    import torch, httpx
    from huggingface_hub import set_client_factory
    from transformers import AutoImageProcessor, RfDetrForInstanceSegmentation
    set_client_factory(lambda: httpx.Client(verify=ssl.create_default_context(),follow_redirects=True,timeout=120))
    local=ROOT/'models'/'buildings'
    source=str(local) if (local/'model.safetensors').exists() else MODEL_ID
    _device='cuda' if torch.cuda.is_available() and os.getenv('SOLARSHIFT_CPU')!='1' else 'cpu'
    torch.set_num_threads(min(4,os.cpu_count() or 1))
    processor=AutoImageProcessor.from_pretrained(source,revision=MODEL_REVISION)
    model=RfDetrForInstanceSegmentation.from_pretrained(source,revision=MODEL_REVISION).to(_device).eval()
    if source==MODEL_ID:
        local.mkdir(parents=True,exist_ok=True)
        processor.save_pretrained(local); model.save_pretrained(local)
        (local/'provenance.txt').write_text(f'{MODEL_ID}\nrevision={MODEL_REVISION}\nApache-2.0\n',encoding='utf-8')
    _processor=processor; _model=model
    status.update(ready=True,device=_device,error=None)

def warmup():
    try:
        with _lock: load_model()
    except Exception as e: status.update(error=str(e),device='unavailable')

def mask_polygon(mask, min_area=80):
    contours,_=cv2.findContours(mask.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    if not contours: return None
    contour=max(contours,key=cv2.contourArea)
    if cv2.contourArea(contour)<min_area: return None
    epsilon=max(1.2,cv2.arcLength(contour,True)*0.007)
    vertices=cv2.approxPolyDP(contour,epsilon,True).reshape(-1,2)
    if len(vertices)<3: return None
    p=Polygon(vertices)
    if not p.is_valid: p=p.buffer(0)
    if p.geom_type!='Polygon' or p.area<min_area: return None
    p=p.simplify(1.5,preserve_topology=True)
    return [[round(x,2),round(y,2)] for x,y in list(p.exterior.coords)[:-1]]

def vegetation(image, roofs):
    # Excess green + saturation/color gating. Does not distinguish canopy from grass.
    arr=np.asarray(image); hsv=cv2.cvtColor(arr,cv2.COLOR_RGB2HSV)
    r,g,b=arr[:,:,0].astype(float),arr[:,:,1].astype(float),arr[:,:,2].astype(float)
    mask=((2*g-r-b>22)&(hsv[:,:,0]>27)&(hsv[:,:,0]<95)&(hsv[:,:,1]>30)&(hsv[:,:,2]>25)).astype(np.uint8)
    occupied=np.zeros(mask.shape,np.uint8)
    for roof in roofs: cv2.fillPoly(occupied,[np.array(roof['polygon'],np.int32)],1)
    mask[occupied==1]=0
    mask=cv2.morphologyEx(mask,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
    mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
    contours,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    regions=[]
    for c in sorted(contours,key=cv2.contourArea,reverse=True):
        area=cv2.contourArea(c)
        # Large green patches could be grass; keep only compact potential canopy regions.
        if area<120 or area>image.width*image.height*0.055: continue
        single=np.zeros(mask.shape,np.uint8); cv2.drawContours(single,[c],-1,1,-1)
        poly=mask_polygon(single,100)
        if poly:
            regions.append({'id':f'V{len(regions)+1:02}','kind':'vegetation','polygon':poly,'confidence':None,'source':'excess-green heuristic · verify canopy','height':10,'tilt':0,'azimuth':180})
        if len(regions)>=25: break
    return regions

def analyze(image: Image.Image, progress=lambda *_:None):
    import torch
    start=time.perf_counter()
    with _lock:
        progress(15,'Loading pretrained building model')
        load_model()
        # Tile a bounded inference image, while returning coordinates at original resolution.
        original_size=image.size
        inference=image.copy(); inference.thumbnail((1800,1800),Image.Resampling.LANCZOS)
        sx,sy=original_size[0]/inference.width,original_size[1]/inference.height
        tile=640; stride=512
        def origins(length):
            if length<=tile: return [0]
            return sorted(set(list(range(0,length-tile+1,stride))+[length-tile]))
        tiles=[(x,y) for y in origins(inference.height) for x in origins(inference.width)]
        candidates=[]
        for index,(x,y) in enumerate(tiles):
            crop=inference.crop((x,y,min(x+tile,inference.width),min(y+tile,inference.height)))
            inputs=_processor(images=crop,return_tensors='pt').to(_device)
            with torch.inference_mode(): outputs=_model(**inputs)
            results=_processor.post_process_instance_segmentation(outputs,threshold=0.45,mask_threshold=0.5,target_sizes=[(crop.height,crop.width)])[0]
            segmentation=results['segmentation'].cpu().numpy()
            for segment in results['segments_info']:
                poly=mask_polygon(segmentation==segment['id'])
                if not poly: continue
                translated=[[(a+x)*sx,(b+y)*sy] for a,b in poly]
                # Crop-edge fragments lose priority in overlap deduplication.
                edge=any(a<2 or b<2 or a>crop.width-3 or b>crop.height-3 for a,b in poly)
                candidates.append((float(segment['score']),translated,edge))
            progress(20+int(65*(index+1)/len(tiles)),f'Segmenting aerial pixels · tile {index+1}/{len(tiles)}')
        roofs=[]; kept=[]
        for confidence,poly,edge in sorted(candidates,key=lambda v:(not v[2],v[0]),reverse=True):
            p=Polygon(poly)
            if not p.is_valid or p.area<80*sx*sy: continue
            if any(p.intersection(other).area/min(p.area,other.area)>0.5 for other in kept): continue
            kept.append(p)
            roofs.append({'id':f'R{len(roofs)+1:02}','kind':'roof','polygon':[[round(a,2),round(b,2)] for a,b in poly],'confidence':round(confidence,3),'source':'RF-DETR pretrained instance mask','height':8,'tilt':10,'azimuth':180})
            if len(roofs)>=50: break
        progress(90,'Vectorizing masks and checking vegetation')
        veg=vegetation(image,roofs)
    return {'regions':roofs+veg,'width':image.width,'height':image.height,'model':MODEL_ID,'device':_device,'inference_seconds':round(time.perf_counter()-start,2),'inference_size':inference.size,'tiles':len(tiles),'warnings':['Vegetation is a color heuristic; verify canopy and remove grass. Heights and panel tilt are assumptions.','Detected building masks are approximate roof candidates; review boundaries before interpreting area.'],'model_revision':MODEL_REVISION}
