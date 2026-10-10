"""Build a captioned 2:40 walkthrough from real browser captures, never synthetic app results."""
from pathlib import Path
import json,subprocess
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'DEMO_ASSETS'

def chart():
    data=json.loads((ASSETS/'sample-analysis.json').read_text(encoding='utf-8'))
    t=np.arange(len(data['frames']))/6
    plt.rcParams.update({'figure.facecolor':'#101510','axes.facecolor':'#172015','text.color':'#e6eddf','axes.labelcolor':'#b5c4a5','xtick.color':'#9bac8e','ytick.color':'#9bac8e','axes.edgecolor':'#3c4b33','font.family':'DejaVu Sans'})
    fig,(a,b)=plt.subplots(2,1,figsize=(12,7),sharex=True,gridspec_kw={'height_ratios':[2,1]},constrained_layout=True)
    for key,color in [('R01','#d9f36a'),('R02','#70dcd5')]:
        r=data['roofs'][key]
        a.plot(t,r['power_series'],label=f"{key} · {r['capacity_kwp']:.1f} kWp · {r['daily_kwh']:.1f} kWh/day",color=color,lw=2.3)
        b.plot(t,np.array(r['shade_series'])*100,label=key,color=color,lw=1.8)
    a.set_title('SolarShift / a calculated clear-sky day',loc='left',fontsize=19,pad=17);a.set_ylabel('Estimated power (kW)');a.legend(frameon=False,labelcolor='#cddbc2');a.grid(alpha=.12)
    b.set_ylabel('Sample points shaded (%)');b.set_xlabel('Local hour · June 21, 2026 · America/Los_Angeles');b.set_xlim(0,24);b.set_ylim(0,100);b.set_xticks(range(0,25,3));b.grid(alpha=.12)
    fig.savefig(ASSETS/'day-profile.png',dpi=150);plt.close(fig)

def render():
    frames=ASSETS/'frames';sequence=[]
    def hold(name,seconds):sequence.append((frames/name,seconds))
    hold('intro.jpg',15);hold('analysis.jpg',6);hold('vision.jpg',9);hold('noon.jpg',18)
    # 25-second chronological sequence: every screenshot is an actual UI time selection.
    day=sorted(frames.glob('day-*.jpg'))
    for f in day:sequence.append((f,25/len(day)))
    hold('day-030.jpg',6);hold('day-126.jpg',6);hold('edit.jpg',20);hold('comparison.jpg',20);hold('method.jpg',20)
    for f in day:sequence.append((f,15/len(day)))
    assert abs(sum(d for _,d in sequence)-160)<1e-6
    concat=ROOT/'runtime'/'demo-concat.txt'
    concat.write_text(''.join(f"file '{p.as_posix()}'\nduration {d:.8f}\n" for p,d in sequence)+f"file '{sequence[-1][0].as_posix()}'\n",encoding='utf-8')
    subtitles=[
      (0,15,'SOLARSHIFT\nTurn any rooftop into solar intelligence.'),
      (15,30,'Real aerial pixels → pretrained RF-DETR building masks\nCaptured from the running application.'),
      (30,48,'Roof area, estimated capacity and clear-sky daily energy\nAll calculated from the detected geometry and editable assumptions.'),
      (48,73,'Move through a real computed solar day.\nSun direction, shadows, irradiance and rooftop power change together.'),
      (73,85,'Before sunrise and after sunset:\nSun below the horizon → zero modeled production.'),
      (85,105,'Review the geometry. Drag vertices or add a manual region.\nHeight, scale and roof tilt are assumptions that users can correct.'),
      (105,125,'Compare total generation and kWh per installed kWp.\nLarger roofs and better exposure answer different planning questions.'),
      (125,145,'NREL solar position + Ineichen irradiance + geometric shadows.\nPreliminary clear-sky planning; weather and unknown structures are excluded.'),
      (145,160,'Real segmentation. Editable geometry. Solar physics.\ngithub.com/Planetech0071/SolarShift'),
    ]
    def stamp(seconds):return f'{seconds//3600:02}:{seconds//60%60:02}:{seconds%60:02},000'
    srt=ASSETS/'SolarShift-demo.srt'
    srt.write_text('\n'.join(f'{i}\n{stamp(a)} --> {stamp(b)}\n{text}\n' for i,(a,b,text) in enumerate(subtitles,1)),encoding='utf-8')
    # Run inside asset directory to keep subtitle filter paths portable and avoid drive-colon escaping.
    vf="scale=1920:940:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:0:color=0x101510,setsar=1,subtitles=SolarShift-demo.srt:force_style='FontName=Arial,FontSize=20,PrimaryColour=&H00E4F0D8,OutlineColour=&H00101510,BorderStyle=1,Outline=1,Alignment=2,MarginV=26'"
    command=['ffmpeg','-hide_banner','-loglevel','warning','-y','-f','concat','-safe','0','-i',str(concat),'-vf',vf,'-t','160','-r','24','-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(ASSETS/'SolarShift-demo.mp4')]
    subprocess.run(command,cwd=ASSETS,check=True)
    print('Rendered actual UI walkthrough:',ASSETS/'SolarShift-demo.mp4',flush=True)

if __name__=='__main__':chart();render()
