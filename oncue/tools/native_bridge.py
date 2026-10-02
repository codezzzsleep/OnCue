#!/usr/bin/env python3
"""Drive the existing Makepad native control bridge, not a web app.
No credentials, provider configuration, or Matrix network calls are used here.
"""
import argparse,json,time,urllib.parse,urllib.request

class Bridge:
    def __init__(self, port):
        self.base=f'http://127.0.0.1:{port}'
        self.http=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def get(self,path,**params):
        url=self.base+'/'+path+'?'+urllib.parse.urlencode(params)
        with self.http.open(url,timeout=20) as r: return json.load(r)
    def snap(self,query=''):
        rows=self.get('snap',q=query).get('s',[])
        return [r for r in rows if r.get('v',1)!=0 and r.get('r',[0,0,0,0])[2]>0 and r.get('ty')!='Splash']
    def click(self,text=None,id=None):
        rows=[r for r in self.snap() if (text is None or r.get('t')==text) and (id is None or r.get('i')==id)]
        if len(rows)!=1: raise ValueError(f'Expected unique visible widget, found {len(rows)}: {rows}')
        x,y,w,h=rows[0]['r']; result=self.get('click',x=x+w/2,y=y+h/2,wait=1)
        time.sleep(.15)
        return {'target':rows[0],'result':result}
    def key(self,code,**mods): return self.get('k',k='press',c=code,wait=1,**mods)
    def fill(self,id,text):
        self.click(id=id)
        self.key('KeyA',ctrl=1)
        self.key('Backspace')
        return self.get('t',t=text,wait=1)
    def scroll(self,x,y,dy): return self.get('m',k='scroll',x=x,y=y,dy=dy,wait=1)
    def app_scroll(self,dy):
        x,y,w,h=next(r['r'] for r in self.snap() if r.get('i')=='app_scroll')
        return self.scroll(x+w-18,y+h*.55,dy)
    def reveal(self,text=None,id=None):
        # Scroll only the OnCue container, never a text field or the Shell.
        self.app_scroll(-5000)
        for _ in range(12):
            rows=[r for r in self.snap() if (text is None or r.get('t')==text) and (id is None or r.get('i')==id)]
            if len(rows)==1 and rows[0]['r'][3]>=20: return rows[0]
            self.app_scroll(150)
        raise ValueError(f'Cannot reveal widget text={text!r} id={id!r}')
    def click_app(self,text=None,id=None):
        self.reveal(text=text,id=id)
        return self.click(text=text,id=id)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--port',type=int,default=8771)
    p.add_argument('op',choices=['snap','click','fill','get','scroll']); p.add_argument('args',nargs='*'); a=p.parse_args(); b=Bridge(a.port)
    if a.op=='snap': out=b.snap(a.args[0] if a.args else '')
    elif a.op=='click': out=b.click(id=a.args[0][1:]) if a.args[0].startswith('#') else b.click(text=a.args[0])
    elif a.op=='fill': out=b.fill(a.args[0],a.args[1])
    elif a.op=='scroll': out=b.scroll(*map(float,a.args))
    else: out=b.get(a.args[0],**dict(v.split('=',1) for v in a.args[1:]))
    print(json.dumps(out,ensure_ascii=False,indent=2))
