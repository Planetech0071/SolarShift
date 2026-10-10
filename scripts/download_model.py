from backend.vision import warmup,status
warmup()
if not status['ready']: raise RuntimeError(status['error'])
print('Pretrained model downloaded and ready:',status['model'])
