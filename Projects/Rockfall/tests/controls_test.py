#!/usr/bin/env python3
"""Controls test (IIe release = real $C010 bit 7, verified in MAME, not bobbin): left/right arrows ($88/$95), J/L, space and A in gameplay. Rocks are suppressed.
Checks a tap moves and stops, a held arrow (key injected every 40 ms, like keyboard auto-repeat) moves
smoothly and stops soon after the repeats end, left/right in both directions, and space/A fire subject
to the heat gauge (holding space overheats, no bolts while locked).  Usage: controls_test.py [enhanced|plus]"""
import subprocess,time,os,sys,json,pty
sys.path.insert(0,'/workspace/apple2/tests'); from sock import send
MACH=sys.argv[1] if len(sys.argv)>1 else 'enhanced'
D=os.path.dirname(os.path.abspath(__file__))+'/..'; SOCK='/tmp/rfct_'+MACH+'.sock'
if os.path.exists(SOCK): os.remove(SOCK)
m,s=pty.openpty()
p=subprocess.Popen(['/workspace/apple2/bin/bobbin-ai','--simple','--remain','--no-turbo','-m',MACH,'--disk',D+'/disk/rockfall.dsk','--control-socket',SOCK],stdin=s,stdout=s,stderr=s,start_new_session=True)
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
res={}
for name,k,sgn in (('right arrow','\x15',1),('left arrow','\x08',-1),('L','L',1),('J','J',-1)):
    d=tap(k); hd,over,ts,stall=hold(k)
    print('%-11s tap moved %+d units; held 0.6s moved %+d, after release coasted %+d units (%.2fs), longest stall %d samples'%(name,d,hd,over,ts,stall))
    ok(d*sgn>0,'%s tap moves the ship the right way'%name)
    ok(hd*sgn>=15 and stall<=8,'%s held: continuous movement'%name)
    if MACH=='plus': ok(abs(over)<=8 and abs(d)<=20,'%s II+: tap = ~16 frames, release stops within 8 units'%name)
    else: print('  (IIe stop-on-release uses the $C010 any-key-down bit; bobbin keeps it set after a key, so it is not checked here)')
    res[name]=(d,hd,over)
ok(res['right arrow'][1]>0 and res['left arrow'][1]<0,'arrows move in opposite directions')
# --- fire ---
center(); settle(2.5); h0=z()['HEAT']
for k,name in ((' ','space'),('A','A')):
    settle(2.5); a=z(); q({'cmd':'keys','text':k}); time.sleep(0.05); b=z()
    print('%s: HEAT %d->%d LON %d'%(name,a['HEAT'],b['HEAT'],b['LON'])); ok(b['HEAT']>=a['HEAT']+10 and b['LON'],'%s fires (bolt + heat)'%name)
settle(2.5); samp=[]; t0=time.time()
while time.time()-t0<3:
    q({'cmd':'keys','text':' '}); norocks(); samp.append(z()); time.sleep(0.04)
ov=[i for i,x in enumerate(samp) if x['OVH']]
newb=sum(1 for a,b in zip(samp,samp[1:]) if a['OVH'] and b['OVH'] and b['LON'] and not a['LON'])
print('held space 3s: overheated after %s samples, new bolts while locked %d'%(ov[0] if ov else None,newb))
ok(bool(ov) and newb==0,'held space overheats; locked laser does not fire')
# arrow + space together (IIe: moving while firing)
center(); x0=z()['PX']; t0=time.time(); f=0
while time.time()-t0<1.0:
    q({'cmd':'keys','text':'\x15'}); time.sleep(0.02); q({'cmd':'keys','text':' '} if f%5==0 else {'cmd':'keys','text':'\x15'}); f+=1; norocks(); time.sleep(0.02)
print('right arrow + space mixed 1s: moved %+d'%(z()['PX']-x0)); ok(z()['PX']-x0>=20,'moving while firing')
ok(not z()['DEAD'],'still alive')
q({'cmd':'quit'})
print('RESULT:','PASS' if not FAIL else 'FAIL %s'%FAIL)
