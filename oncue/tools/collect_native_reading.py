#!/usr/bin/env python3
"""Collect visible OnCue pages by clicking its real native reader controls."""
import argparse,json,time
from pathlib import Path
from native_bridge import Bridge

def bottom(b):
    rect=next(r['r'] for r in b.snap() if r.get('i')=='app_scroll')
    x,y,w,h=rect
    b.scroll(x+w-18,y+h*.6,3000)

def reader(b):
    rows=b.snap(); box=next(r['r'] for r in rows if r.get('i')=='readout')
    x,y,w,h=box
    labels=[r for r in rows if r.get('ty')=='Label' and r['r'][0]>=x and r['r'][1]>=y and r['r'][0]+r['r'][2]<=x+w+1 and r['r'][1]+r['r'][3]<=y+h+1]
    return {'rect':box,'text':'\n'.join(r['t'] for r in labels),'labels':labels}

def pages(b):
    bottom(b)
    b.click(text='上一页')
    # Page indicator belongs to the result header, after the source pane.
    def index():
        candidates=[r for r in b.snap() if r.get('ty')=='Label' and r.get('t','').startswith('第 ') and r.get('i')!='cue_msg_page_label']
        text=candidates[-1]['t']; nums=[int(s) for s in text.split() if s.isdigit()]
        return nums[0],nums[1]
    cur,total=index()
    for _ in range(cur-1): b.click(text='上一页')
    result=[]
    for i in range(total):
        bottom(b); result.append(reader(b))
        if i+1<total: b.click(text='下一页')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--port',type=int,default=8771);p.add_argument('--out',type=Path,required=True);a=p.parse_args();b=Bridge(a.port)
    if a.out.exists():p.error('output exists; use a new evidence path')
    records={}
    for title in ('A 顺着说','B 换问法','C 换玩法'):
        b.click_app(text=title)
        # Expand by single steps; full-text collection uses each reader page.
        for _ in range(30):
            b.click_app(text='下一句');bottom(b)
            state=next(r['t'] for r in b.snap() if r.get('i')=='cue_status')
            if '全部' in state:break
        else:raise RuntimeError('Too many dialogue lines')
        records[title]={'pages':pages(b),'status':state}
    b.click(text='相关原文');records['相关原文']={'pages':pages(b)}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:''.join(p['text'] for p in v['pages']) for k,v in records.items()},ensure_ascii=False,indent=2))
