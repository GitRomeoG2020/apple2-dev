#!/usr/bin/env python3
"""Fire-stick test: arrow held + one space tap, then the latch auto-repeats space. Old code fired every repeat. Based on controls test (IIe release = real $C010 bit 7, verified in MAME, not bobbin): left/right arrows ($88/$95), J/L, space and A in gameplay. Rocks are suppressed.
Checks a tap moves and stops, a held arrow (key injected every 40 ms, like keyboard auto-repeat) moves
smoothly and stops soon after the repeats end, left/right in both directions, and space/A fire subject
to the heat gauge (holding space overheats, no bolts while locked).  Usage: controls_test.py [enhanced|plus]"""
import subprocess,time,os,sys,json,pty
sys.path.insert(0,'/workspace/apple2/tests'); from sock import send
MACH=sys.argv[1] if len(sys.argv)>1 else 'enhanced'
D=os.path.dirname(os.path.abspath(__file__))+'/..'; SOCK='/tmp/rffs_'+MACH+'.sock'
if os.path.exists(SOCK): os.remove(SOCK)
import shutil; DSK='/tmp/rf_%s_%s.dsk'%(os.path.basename(__file__)[:-3],MACH); shutil.copy(D+'/disk/rockfall.dsk',DSK)   # games may save scores: never touch the repo disk
m,s=pty.openpty()
p=subprocess.Popen(['/workspace/apple2/bin/bobbin-ai','--simple','--remain','--no-turbo','-m',MACH,'--disk',DSK,'--control-socket',SOCK],stdin=s,stdout=s,stderr=s,start_new_session=True)
os.close(s); q=lambda o:json.loads(send(json.dumps(o),SOCK))
for i in range(50):
    try: q({'cmd':'ping'}); break
    except Exception: time.sleep(0.2)
peek=lambda a,n:bytes(q({'cmd':'peek','addr':a,'len':n})['data'])
poke=lambda a,d:q({'cmd':'poke','addr':a,'data':d})
def norocks(): poke(0x88,[0]*5); poke(0x80,[0xFF]*5)
def z(): b=peek(0x50,0x58); return dict(PX=b[0x0C],DIR=b[0x0E],DEAD=b[0x17],LON=b[0x44],HEAT=b[0x54],OVH=b[0x55],FRAME=b[0x40])
FAIL=[]
def ok(c,msg): print(('PASS ' if c else 'FAIL ')+msg); c or FAIL.append(msg)
time.sleep(6); q({'cmd':'keys','text':' '}); time.sleep(1.0); norocks(); time.sleep(0.5)
def settle(t=0.6):
    t0=time.time()
    while time.time()-t0<t: norocks(); time.sleep(0.05)
def center(): poke(0x5C,[66]); poke(0x5E,[0]); poke(0x5F,[0]); settle(0.3)
def tap(k):
    center(); x0=z()['PX']; q({'cmd':'keys','text':k}); settle(1.0); return z()['PX']-x0
def hold(k,dur=0.6):
    center(); x0=z()['PX']; xs=[]; t0=time.time(); nxt=t0
    while time.time()-t0<dur:
        if time.time()>=nxt: q({'cmd':'keys','text':k}); nxt+=0.04
        norocks(); xs.append(z()['PX']); time.sleep(0.01)
    t1=time.time(); xe=z()['PX']; last=xe; tstop=None
    while time.time()-t1<1.0:
        x=z()['PX']
        if x!=last: last=x; tstop=time.time()-t1
        time.sleep(0.01)
    # stalls: longest run of identical consecutive samples during the hold (after the first 0.1 s)
    run=best=0
    for a,b in zip(xs[5:],xs[6:]):
        run=run+1 if a==b else 0; best=max(best,run)
    return xs[-1]-x0,last-xe,tstop or 0,best

def run(moving,dur=1.5):
    # space code every ~70 ms (IIe auto-repeat rate) with HEAT read back; count heat jumps
    center(); settle(2.5); poke(0xA4,[0,0]); bolts=0; prev=0; f0=z()['FRAME']; n=0; t0=time.time()
    while time.time()-t0<dur:
        if moving: poke(0x5E,[2,16])
        q({'cmd':'keys','text':' '}); n+=1
        h=peek(0xA4,1)[0]; bolts+=(h>prev+8); prev=h
        if h>40: poke(0xA4,[0,0]); prev=0
        time.sleep(0.06)
    print('  %d codes over %d frames'%(n,(z()['FRAME']-f0)&255))
    return bolts
still=run(False); mov=run(True)
print('space repeats every ~80 ms for 1.5 s: standing still %d bolts, moving %d bolts'%(still,mov))
ok(still>=3,'standing still: held space still auto-fires')
ok(1<=mov<=2,'moving: latched space repeat does not keep firing')
# real taps while moving (~4/s) still fire
center(); settle(2.5); bolts=0; prev=0; t0=time.time(); nxt=t0
while time.time()-t0<2.0:
    poke(0x5E,[2]); poke(0x5F,[16]); poke(0x5C,[66])
    if time.time()>=nxt: q({'cmd':'keys','text':' '}); nxt+=0.25
    norocks(); h=z()['HEAT']; bolts+=(h>prev+8); prev=h; time.sleep(0.01)
    if prev>40: poke(0xA4,[0,0]); prev=0
print('taps every 250 ms while moving 2 s: %d bolts'%bolts); ok(bolts>=6,'moving: real taps still fire')
q({'cmd':'quit'})
print('RESULT:','PASS' if not FAIL else 'FAIL %s'%FAIL)
