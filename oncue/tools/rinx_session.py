#!/usr/bin/env python3
"""Native Rinx test conveniences: load a reviewed dev bundle and size its frame.
This tool drives normal Makepad input events. It does not modify host APIs.
"""
import argparse,json,time
from native_bridge import Bridge

def module(b):
    return next(r for r in b.snap() if r.get('ty')=='RinxModuleView')['r']

def resize(b,width,height):
    # Existing macOS-style native frame: 32-point title, no inset. Confirm from
    # module snapshot after a physical bottom-right drag; never set app geometry.
    x,y,w,h=module(b)
    for _ in range(3):
        if w==width and h==height-32: break
        # Super + right-drag is the host's existing resize gesture, from a
        # point safely inside the lower-right quadrant (outside the dock).
        px=x+w*.75; py=y+h*.75
        dx=width-w; dy=(height-32)-h
        b.get('m',k='down',x=px,y=py,b=1,logo=1)
        b.get('m',k='move',x=px+dx,y=py+dy,b=1,logo=1)
        b.get('m',k='up',x=px+dx,y=py+dy,b=1,logo=1,wait=1)
        time.sleep(.3); x,y,w,h=module(b)
    if (w,h)!=(width,height-32): raise RuntimeError(f'Resize mismatch: requested {width}x{height}, module {w}x{h}')
    card=next((r for r in b.get('snap',q='card').get('s',[]) if r.get('i')=='card' and r.get('ty')=='Splash'),None)
    return {'rinx_frame':[x,y-32,w,h+32], 'module':[x,y,w,h], 'embedded_app':card.get('r') if card else None}

def load(b,path,room=None):
    b.click(text='Back'); b.click(text='Import an app'); b.fill('path',path)
    if room is not None: b.fill('room',room)
    b.click(text='Review bundle')
    notice=[r for r in b.snap('notice') if r.get('i')=='notice']
    b.click(text='Run')
    return {'review':notice,'bundle':path}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--port',type=int,default=8771)
    p.add_argument('op',choices=['resize','load']);p.add_argument('args',nargs='+');a=p.parse_args();b=Bridge(a.port)
    out=resize(b,*map(int,a.args)) if a.op=='resize' else load(b,a.args[0],a.args[1] if len(a.args)>1 else None)
    print(json.dumps(out,ensure_ascii=False,indent=2))
