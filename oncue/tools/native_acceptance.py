#!/usr/bin/env python3
"""Record Rinx-native acceptance through input and screenshots, never model mocks.
The caller selects an already running OnCue bundle and private Rinx data directory.
Only synthetic drafts are read from disk; no credentials or other app data are read.
"""
import argparse,json,os,re,subprocess,time
from pathlib import Path
from native_bridge import Bridge
from rinx_session import module,resize

class Recorder:
    def __init__(self,b,out):
        self.b=b;self.out=Path(out);self.out.mkdir(parents=True,exist_ok=False);self.actions=[]
    def status(self):
        return next((r['t'] for r in self.b.snap('cue_status') if r.get('i')=='cue_status'),'')
    def record(self,kind,**data):
        self.actions.append({'at':time.time(),'kind':kind,**data})
        (self.out/'actions.json').write_text(json.dumps(self.actions,ensure_ascii=False,indent=2)+'\n')
    def click(self,text):
        result=self.b.click_app(text=text);self.record('click',text=text,target=result['target']['r'],status=self.status())
    def capture(self,name):
        x,y,w,h=module(self.b);frame=[x,y-32,w,h+32]
        env=os.environ.copy();env['DISPLAY']=':99';env['XAUTHORITY']='/srv/oncue-runtime/state/xauthority'
        path=self.out/(name+'.png')
        if path.exists():raise ValueError('Capture already exists')
        subprocess.run(['ffmpeg','-nostdin','-v','error','-f','x11grab','-video_size',f'{w}x{h+32}','-i',f':99+{x},{y-32}','-frames:v','1',str(path)],env=env,check=True)
        self.record('capture',path=path.name,frame=frame)
    def result_index(self):
        candidates=[r for r in self.b.snap() if r.get('ty')=='Label' and r.get('t','').startswith('第 ') and r.get('i')!='cue_msg_page_label']
        if not candidates:raise RuntimeError('Result page counter not visible')
        nums=list(map(int,re.findall(r'\d+',candidates[-1]['t'])))
        return nums[0],nums[1]
    def collect_pages(self,name,all_screens=True):
        self.b.app_scroll(5000)
        cur,total=self.result_index()
        for _ in range(cur-1):self.b.click(text='上一页')
        result=[]
        for i in range(total):
            self.b.app_scroll(5000)
            rows=self.b.snap();box=next(r['r'] for r in rows if r.get('i')=='readout');x,y,w,h=box
            labels=[r for r in rows if r.get('ty')=='Label' and r['r'][0]>=x and r['r'][1]>=y and r['r'][0]+r['r'][2]<=x+w+1 and r['r'][1]+r['r'][3]<=y+h+1]
            text='\n'.join(r['t'] for r in labels)
            if not text:raise RuntimeError(f'Empty reader at {name} {i+1}')
            result.append({'page':i+1,'rect':box,'text':text})
            if all_screens or i in (0,total//2,total-1):self.capture(f'{name}-{i+1:02}')
            if i+1<total:self.b.click(text='下一页')
        self.record('reader',name=name,pages=result)
        return ''.join(r['text'] for r in result)
    def playback(self):
        self.click('A 顺着说');self.click('重播');self.click('下一句')
        assert '1 /' in self.status() or '全部 1 ' in self.status(),self.status()
        self.click('播放');time.sleep(3.0)
        resumed=self.status()
        assert '播完' in resumed or '2 /' in resumed or '全部' in resumed,resumed
        self.record('resume',status=resumed)
        if '播完' not in resumed:
            self.click('暂停')
            paused=self.status();self.b.app_scroll(5000);before=self.result_index()
            time.sleep(3.1);assert self.status()==paused and self.result_index()==before
            self.record('pause_stable',seconds=3.1,status=paused)
            self.click('播放');time.sleep(1.6)
            after_play=self.status()
            assert after_play!=paused,after_play
        else:
            paused=resumed
        self.click('B 换问法');self.b.app_scroll(5000)
        before=self.result_index();time.sleep(1.8);assert self.result_index()==before
        self.record('old_timer_isolated',seconds=1.8,index=before)
        self.click('播放');time.sleep(1.6)
        b_playing=self.status()
        assert '换个问法' in b_playing or 'B' in b_playing or '2 /' in b_playing,b_playing
        self.record('route_b_playing',status=b_playing)
        self.click('重播')
    def read_routes(self):
        result={}
        for label in ('A 顺着说','B 换问法','C 换玩法'):
            self.click(label)
            for _ in range(20):
                self.click('下一句')
                if '全部' in self.status():break
            else:raise RuntimeError('Dialogue did not finish')
            result[label]=self.collect_pages(label,False)
        self.click('摘要');result['摘要']=self.collect_pages('摘要',True)
        assert len(set(result[k] for k in ('A 顺着说','B 换问法','C 换玩法')))==3
        return result
    def read_long_message(self):
        self.click('载入群聊')
        for _ in range(60):
            time.sleep(.5)
            if '原消息已载入' in self.status():break
        time.sleep(2)
        pages=[]
        for i in range(15):
            rows=self.b.snap()
            box=next((r['r'] for r in rows if r.get('i')=='msg_readout'),None)
            if not box:break
            x,y,w,h=box
            labels=[r for r in rows if r.get('ty')=='Label' and r['r'][0]>=x and r['r'][1]>=y and r['r'][0]+r['r'][2]<=x+w+1 and r['r'][1]+r['r'][3]<=y+h+1]
            page_text='\n'.join(r['t'] for r in labels)
            if page_text and (not pages or pages[-1]!=page_text):pages.append(page_text)
            try:self.b.click(text='下一条')
            except Exception:break
            time.sleep(.8)
        self.record('long_message_read',pages=len(pages),total_chars=sum(len(p) for p in pages))
        return pages
    def draft(self,label,text,data_dir):
        self.b.reveal(id='cue_draft');self.b.fill('cue_draft',text);self.click('存 '+label)
        assert '回读确认' in self.status(),self.status()
        uid=(Path(data_dir)/'latest_user_id.txt').read_text().strip()
        path=Path(data_dir)/'miniapps'/uid.encode().hex()/'oncue-screening-room'/('take-'+label.lower()+'.txt')
        actual=path.read_text();assert actual==text
        self.record('independent_readback',slot=label,exact=True,characters=len(text))
        self.click('显示 '+label);shown=self.collect_pages('draft-'+label,False);assert shown==text,(shown,text)
        self.b.reveal(id='cue_draft');self.b.fill('cue_draft','')
        self.click('取 '+label);self.b.reveal(id='cue_draft')
        actual=next(r.get('val') for r in self.b.snap() if r.get('i')=='cue_draft');assert actual==text
        self.record('restore',slot=label,exact=True)
    def reopen_check(self,text,data_dir):
        self.click('Back')
        time.sleep(3)
        b2=self.b
        # Navigate to the mini-apps library (has Import an app button)
        for _ in range(6):
            rows=b2.snap()
            if any(r.get('t')=='Import an app' for r in rows): break
            if any(r.get('i')=='discover_mini_apps' for r in rows):
                nav=[r for r in rows if r.get('i')=='discover_mini_apps'][0]
                x,y,w,h=nav['r']
                b2.get('click',x=x+w/2,y=y+h/2,wait=1)
            time.sleep(1.0)
        # Open the import form
        for _ in range(6):
            rows=b2.snap()
            if any(r.get('ty')=='TextInput' and r.get('i')=='path' for r in rows): break
            btn=[r for r in rows if r.get('i')=='import_app']
            if btn:
                x,y,w,h=btn[0]['r']
                b2.get('click',x=x+w/2,y=y+h/2,wait=1)
            time.sleep(1.0)
        rows=b2.snap()
        assert any(r.get('ty')=='TextInput' and r.get('i')=='path' for r in rows),'Import form not open; visible='+str([(r.get('i'),r.get('t'),r.get('ty')) for r in rows if r.get('ty') in ('Button','TextInput','NavigationBarButton')][:10])
        b2.fill('path','/srv/oncue-runtime/dev/047-final-3'); time.sleep(.5)
        try: b2.click(text='Review bundle'); time.sleep(1.0)
        except Exception: pass
        b2.click(text='Run'); time.sleep(4)
        for _ in range(20):
            time.sleep(.5)
            if any(r.get('i')=='cue_status' for r in b2.snap()): break
        status=next((r['t'] for r in b2.snap('cue_status') if r.get('i')=='cue_status'), '')
        assert '草稿' in status or '恢复' in status,status
        for _ in range(20):
            try:
                b2.reveal(id='cue_draft')
                break
            except Exception:
                time.sleep(.5)
        actual=next(r.get('val') for r in b2.snap() if r.get('i')=='cue_draft')
        assert actual==text,(actual,text)
        self.record('reopen_restored',exact=True,characters=len(text))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--port',type=int,default=8771);p.add_argument('--out',required=True);p.add_argument('--mode',choices=['routes','playback','draft','reopen'],required=True);p.add_argument('--size',default='990x613');p.add_argument('--data-dir',default='/srv/oncue-rinx-data-rinxchat');a=p.parse_args()
    b=Bridge(a.port);r=Recorder(b,a.out);r.record('geometry',**resize(b,*map(int,a.size.split('x'))))
    if a.mode=='routes':r.record('complete_routes',contents=r.read_routes())
    elif a.mode=='playback':r.playback();r.capture('playback')
    elif a.mode=='reopen':
        text='重开验证：关闭后重新导入，草稿应自动恢复。\n第二行保留。'
        # Ensure the app is loaded before saving the draft
        rows=r.b.snap()
        if not any(x.get('i')=='cue_status' for x in rows):
            if not any(x.get('t')=='Import an app' for x in rows):
                try: r.b.click(id='discover_mini_apps'); time.sleep(1.2)
                except Exception: pass
                try: r.b.click(id='import_app'); time.sleep(1.2)
                except Exception: pass
            r.b.fill('path','/srv/oncue-runtime/dev/047-final-3'); time.sleep(.5)
            try: r.b.click(text='Review bundle'); time.sleep(1)
            except Exception: pass
            r.b.click(text='Run'); time.sleep(3)
            for _ in range(20):
                time.sleep(.5)
                if any(x.get('i')=='cue_status' for x in r.b.snap()): break
        r.draft('A',text,a.data_dir)
        r.reopen_check(text,a.data_dir)
    else:
        text='  草稿首行：中午再确认，尚未发送。\n中段保留空格   和组合 é、家人👩‍👩‍👧‍👦、肤色👍🏽、旗帜🇨🇳。\n最后一行 END-A  '
        r.draft('A',text,a.data_dir)
        r.draft('B','版本 B\n换个问法：当天回来可以吗？\n保留另一份原文 END-B',a.data_dir)
    r.record('complete',passed=True)
    print('PASS',a.mode,a.size,a.out)
