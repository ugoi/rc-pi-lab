#!/usr/bin/env python3
"""Render measured device PWM, never application angle commands."""
import argparse, json, math
from pathlib import Path
from PIL import Image, ImageDraw

def state(row):
    width=row['high_us'][0]
    period=row['period_us']
    valid=800 <= width <= 2200 and 15000 <= period <= 25000
    return valid, max(0,min(180,(width-1000)*.18))

def draw(row):
    valid,angle=state(row)
    im=Image.new('RGB',(800,520),'#102033'); d=ImageDraw.Draw(im)
    d.text((28,20),'Pi 3 Linux -> ServoKit -> Linux I2C -> PCA9685 -> PWM',fill='white')
    d.rounded_rectangle((240,265,560,400),radius=16,fill='#27678e',outline='#78cfff',width=3)
    d.text((340,365),'VIRTUAL SERVO',fill='white')
    cx,cy=400,300
    for a in (0,90,180):
        t=math.radians(180-a); x=cx+190*math.cos(t); y=cy-190*math.sin(t)
        d.text((x-10,y-10),str(a),fill='#b9d5ea')
    if valid:
        t=math.radians(180-angle); x=cx+155*math.cos(t); y=cy-155*math.sin(t)
        d.line((cx,cy,x,y),fill='#ffbd51',width=15); d.ellipse((x-10,y-10,x+10,y+10),fill='white')
    d.ellipse((cx-15,cy-15,cx+15,cy+15),fill='#dbeaff')
    text=f"PWM {row['high_us'][0]:.2f} us / {row['period_us']:.2f} us"
    d.text((28,430),text,fill='white')
    d.text((28,452),f"seq {row['seq']} | {row['event']} | virtual time {row['ns']/1e9:.3f} s",fill='#b9d5ea')
    d.text((28,478),f'Ideal angle {angle:.2f} deg' if valid else 'NO VALID SERVO PULSE (no position claim)',fill='#ffbd51')
    return im

def main():
    p=argparse.ArgumentParser(); p.add_argument('trace'); p.add_argument('out'); a=p.parse_args()
    rows=[json.loads(s) for s in Path(a.trace).read_text().splitlines()]
    selected=[]; last=None
    for r in rows:
        if r['event'] not in ('stop','bridge_open','reset'): continue
        key=(r['high_us'][0],r['period_us'])
        if key!=last: selected.append(r); last=key
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    for i,r in enumerate(selected): draw(r).save(out/f'frame-{i:03}.png')
    (out/'measured-states.json').write_text(json.dumps(selected,indent=2)+'\n')
    template=Path(__file__).with_name('viewer-template.html').read_text()
    (out/'servo-viewer.html').write_text(template.replace('MEASUREMENTS_JSON',json.dumps(selected)))
    # Fixed 2s/state presentation, not a real-time performance measurement.
    with (out/'frames.txt').open('w') as f:
        for i in range(len(selected)):
            f.write(f"file 'frame-{i:03}.png'\nduration 2\n")
        if selected: f.write(f"file 'frame-{len(selected)-1:03}.png'\n")
    print(json.dumps(selected,indent=2))
if __name__=='__main__': main()
