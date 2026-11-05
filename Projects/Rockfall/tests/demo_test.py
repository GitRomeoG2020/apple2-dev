#!/usr/bin/env python3
"""Demo / attract-mode test: boot disk/rockfall.dsk in bobbin-ai and check
 - after one idle title art + score pass, DEMO=1 and the game is playing (ship/rocks move);
 - HUD can show DEMO glyphs; score may rise from AI fire/dodges;
 - any key clears DEMO and starts a real game (LIVES=3, DEMO=0);
 - a death in demo returns to the title (no high-score save / no game-over initials).
Speeds the title timers via poke so the test does not wait ~20 s. Usage: demo_test.py [enhanced|plus]"""
import subprocess,time,os,sys,json,pty,shutil
sys.path.insert(0,'/workspace/apple2/tests'); from sock import send
MACH=sys.argv[1] if len(sys.argv)>1 else 'enhanced'
D=os.path.dirname(os.path.abspath(__file__))+'/..'; SOCK='/tmp/rfdemo_'+MACH+'.sock'
if os.path.exists(SOCK): os.remove(SOCK)
DSK='/tmp/rf_demo_%s.dsk'%MACH; shutil.copy(D+'/disk/rockfall.dsk',DSK)
m,s=pty.openpty()
p=subprocess.Popen(['/workspace/apple2/bin/bobbin-ai','--simple','--remain','--no-turbo','-m',MACH,'--disk',DSK,'--control-socket',SOCK],stdin=s,stdout=s,stderr=s,start_new_session=True)
os.close(s); q=lambda o:json.loads(send(json.dumps(o),SOCK))
for i in range(50):
    try: q({'cmd':'ping'}); break
    except Exception: time.sleep(0.2)
peek=lambda a,n:bytes(q({'cmd':'peek','addr':a,'len':n})['data'])
poke=lambda a,d:q({'cmd':'poke','addr':a,'data':d})
key=lambda c,t=0.1:(q({'cmd':'keys','text':c}),time.sleep(t))
A=lambda y:(y&7)*0x400+((y>>3)&7)*0x80+(y>>6)*0x28
TL=lambda r:0x400+(r&7)*0x80+(r>>3)*0x28
FONT=[int(x,16) for l in open(D+'/src/font.s') if '.byte' in l for x in l.split('.byte')[1].replace('$','').split(',')]
GL={tuple(FONT[g*5:g*5+5]):('0123456789CDEHIPR SOATLV'+'xxx^'+'M')[g] for g in range(29)}
FAIL=[]
def ok(c,msg): print(('PASS ' if c else 'FAIL ')+msg); c or FAIL.append(msg)
def wait(f,t):
    t0=time.time()
    while time.time()-t0<t:
        if f(): return True
        time.sleep(0.05)
    return False
demo=lambda: peek(0x6B,1)[0]
view=lambda: peek(0xCE,1)[0]
tc=lambda: peek(0xC3,2)[0]|peek(0xC3,2)[1]<<8
def endview():
    """Wait until the title timer is in a real ARTT/SCORET countdown, then expire it."""
    # ARTT=1300, SCORET=450; ignore ZP garbage (~$FFxx) before the loop arms the timer
    ok(wait(lambda: 20 < tc() <= 1400,10),'title timer armed')
    q({'cmd':'pause'}); poke(0xC3,[1,0]); q({'cmd':'resume'})
def st():
    z=peek(0x4E,0xA0); g=lambda a:z[a-0x4E]
    return dict(DEMO=peek(0x6B,1)[0],LIVES=g(0x4E),DEAD=g(0x67),PX=g(0x5C),DIR=g(0x5E),
                FRAME=g(0x90),SCORE=int('%02X%02X'%(g(0x64),g(0x63))),RON=[g(0x88+i) for i in range(5)],
                LEVEL=g(0xA7))
def hud(pg=0x2000):
    mm=peek(pg,0x1000)+peek(pg+0x1000,0x1000)
    return ''.join(GL.get(tuple(mm[A(186+r)+c] for r in range(5)),'?') for c in range(1,24))
def screen():
    return '\n'.join(bytes(b&0x7F for b in peek(TL(r),40)).decode('latin1') for r in range(24))
# boot to title art
ok(wait(lambda: view()==0,25),'title art after boot')
# compress art wait, then score wait, then demo
# end art timer once, wait for score view, then end score timer into demo
endview()
ok(wait(lambda: view()==1,15),'score view after short art timer')
time.sleep(0.25)
# snapshot high-score magic page before demo (must be unchanged after demo death)
hs0=peek(0x1B00,0x30)
endview()
ok(wait(lambda: demo()==1,12),'idle score pass enters DEMO')
time.sleep(0.8); z=st(); print('demo start:',z,'HUD',repr(hud()))
ok(z['DEMO']==1 and z['LIVES']==3 and not z['DEAD'],'demo: DEMO=1, 3 lives, not dead')
ok(z['FRAME']>0,'demo: game loop running')
# AI should eventually move or fire (DIR or score or LON) — give it a few seconds
moved=False; px0=z['PX']; sc0=z['SCORE']
for i in range(40):
    time.sleep(0.15); z=st()
    if z['PX']!=px0 or z['SCORE']!=sc0 or z['DIR']:
        moved=True; break
print('AI activity after %.1fs: PX %d->%d DIR %d SCORE %d->%d'%(i*0.15,px0,z['PX'],z['DIR'],sc0,z['SCORE']))
ok(moved,'demo AI moves or scores')
# any key -> real game
key(' '); time.sleep(1.0); z=st(); print('after key:',z)
ok(z['DEMO']==0 and z['LIVES']==3 and not z['DEAD'] and z['SCORE']==0,'key starts a real game (DEMO=0, score reset)')
# force back to title then demo, then force a death -> title, no HS write
# return via ESC from a forced game over is heavy; poke path: enter demo again
# jump by resetting through title: kill ship until title... easier: poke DEMO death path
# Start demo again: go to title with ESC after quick game over
poke(0x63,[0,0]); poke(0x4E,[1]); poke(0x67,[1]); poke(0xE8,[0])
ok(wait(lambda: 'ANY KEY: PLAY AGAIN' in screen() or 'G A M E' in screen(),8),'real game over')
key('\x1b',0.5)
ok(wait(lambda: view()==0 and demo()==0,8),'ESC to title')
endview()
ok(wait(lambda: view()==1,15),'score view again')
time.sleep(0.2)
endview()
ok(wait(lambda: demo()==1,12),'re-enters demo')
time.sleep(0.5)
# force ship death in demo
q({'cmd':'pause'})
poke(0xE8,[0]); poke(0x5C,[71]); poke(0x88,[1,0,0,0,0]); poke(0x80,[0xFF]*5)
poke(0xD0,[1]); poke(0xD8,[1]); poke(0xE0,[0]); poke(0x70,[20]); poke(0x78,[135])
q({'cmd':'resume'})
ok(wait(lambda: view()==0 and demo()==0,10),'demo death returns to title')
hs1=peek(0x1B00,0x30)
ok(hs0==hs1,'demo did not rewrite the high-score page')
q({'cmd':'quit'})
print('RESULT:','PASS' if not FAIL else 'FAIL %s'%FAIL)
sys.exit(1 if FAIL else 0)
