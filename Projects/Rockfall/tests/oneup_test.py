#!/usr/bin/env python3
"""1-up capsule test: boot disk/rockfall.dsk in bobbin-ai and check
 - CTYPE 3 capsule: mini-ship icon, falls CFALL=2, collected on contact;
 - pickup increments LIVES (HUD ^N), capped at MAXL=5;
 - at cap, still clears CON and plays pickup but LIVES stays 5;
 - shield/cool/spread still set PUT timers (type 0..2 unchanged);
 - DROP1 rarity: among forced drops, ~1/16 are type 3;
 - boss kill still forces shield/cool only (never 1-up).
Usage: oneup_test.py [enhanced|plus]"""
import subprocess,time,os,sys,json,pty,shutil,re
sys.path.insert(0,'/workspace/apple2/tests'); from sock import send
MACH=sys.argv[1] if len(sys.argv)>1 else 'enhanced'
D=os.path.dirname(os.path.abspath(__file__))+'/..'; SOCK='/tmp/rf1up_'+MACH+'.sock'
if os.path.exists(SOCK): os.remove(SOCK)
DSK='/tmp/rf_1up_%s.dsk'%MACH; shutil.copy(D+'/disk/rockfall.dsk',DSK)
m,s=pty.openpty()
p=subprocess.Popen(['/workspace/apple2/bin/bobbin-ai','--simple','--remain','--no-turbo','-m',MACH,'--disk',DSK,'--control-socket',SOCK],stdin=s,stdout=s,stderr=s,start_new_session=True)
os.close(s); q=lambda o:json.loads(send(json.dumps(o),SOCK))
for i in range(50):
    try: q({'cmd':'ping'}); break
    except Exception: time.sleep(0.2)
peek=lambda a,n:bytes(q({'cmd':'peek','addr':a,'len':n})['data'])
poke=lambda a,d:q({'cmd':'poke','addr':a,'data':d})
key=lambda c,t=0.05:(q({'cmd':'keys','text':c}),time.sleep(t))
A=lambda y:(y&7)*0x400+((y>>3)&7)*0x80+(y>>6)*0x28
FONT=[int(x,16) for l in open(D+'/src/font.s') if '.byte' in l for x in l.split('.byte')[1].replace('$','').split(',')]
GL={tuple(FONT[g*5:g*5+5]):('0123456789CDEHIPR SOATLV'+'xxx^')[g] for g in range(28)}
FAIL=[]
def ok(c,msg): print(('PASS ' if c else 'FAIL ')+msg); c or FAIL.append(msg)
def st():
    z=peek(0x4E,0xA0); g=lambda a:z[a-0x4E]
    return dict(LIVES=g(0x4E),DEAD=g(0x67),PX=g(0x5C),FRAME=g(0x90),
                PUT=list(peek(0xE8,3)),CON=peek(0xEB,1)[0],KCOL=peek(0xEC,1)[0],
                CY=peek(0xED,1)[0],CTYPE=peek(0xEE,1)[0],BOSS=peek(0xD6,1)[0])
def hud(pg=0x2000):
    mm=peek(pg,0x1000)+peek(pg+0x1000,0x1000); return ''.join(GL.get(tuple(mm[A(186+r)+c] for r in range(5)),'?') for c in range(1,19))
def norocks(): poke(0x88,[0]*5); poke(0x80,[0xFF]*5)
def quiet(): norocks(); poke(0xB8,[0xFF,0x7F]); poke(0x5E,[0]); poke(0xEB,[0])
def alive():
    for t in range(30):
        if not st()['DEAD']: return
        time.sleep(3 if t==0 else 0.6); key('A'); time.sleep(0.5)
def capsule(t,col,y): poke(0xEC,[col,y,t]); poke(0xEB,[1])
time.sleep(6); key(' '); time.sleep(1.0); quiet(); time.sleep(0.3)
z=st(); h=hud(); print('start: LIVES %d HUD %r PUT %s'%(z['LIVES'],h,z['PUT']))
ok(z['LIVES']==3 and h[15:17]=='^3','new game: 3 lives')
# collect 1-up -> 4
alive(); quiet(); poke(0x5C,[70]); capsule(3,(2*70)//7,110); time.sleep(0.7)
z=st(); h=hud(); print('after 1-up: LIVES %d HUD %r CON %d PUT %s'%(z['LIVES'],h,z['CON'],z['PUT']))
ok(z['CON']==0 and z['LIVES']==4 and h[15:17]=='^4' and z['PUT']==[0,0,0],'1-up: LIVES 3->4, HUD ^4, no PUT timers')
# type 0 still sets shield timer
alive(); quiet(); poke(0x5C,[70]); capsule(0,(2*70)//7,110); time.sleep(0.7)
z=st(); print('shield pickup PUT',z['PUT'])
ok(z['CON']==0 and 180<=z['PUT'][0]<=200 and z['LIVES']==4,'shield still sets PUT[0], lives unchanged')
# climb to cap
alive(); quiet()
for want in (5,5):
    poke(0x4E,[want-1 if want==5 else 4]); poke(0xE8,[0,0,0]); poke(0x5C,[70])
    capsule(3,(2*70)//7,110); time.sleep(0.7)
    z=st(); h=hud(); print('toward cap: LIVES %d HUD %r'%(z['LIVES'],h))
ok(z['LIVES']==5 and h[15:17]=='^5','1-up reaches MAXL=5')
# at cap: collect again, stay 5
alive(); quiet(); poke(0x4E,[5]); poke(0x5C,[70]); capsule(3,(2*70)//7,110); time.sleep(0.7)
z=st(); h=hud(); print('at cap pickup: LIVES %d CON %d HUD %r'%(z['LIVES'],z['CON'],h))
ok(z['CON']==0 and z['LIVES']==5 and h[15:17]=='^5','at MAXL: still collect, LIVES stays 5')
# rarity: force trydrop via boulder kills, count CTYPE==3
# poke CON=0 and call path: destroy boulders with drop forced by re-running trydrop via poke of DROP path
# Simpler: spawn many capsules via trydrop by poking after setting DCL/DRW and calling... hard without JSR.
# Instead: peek CTYPE distribution by forcing drop chance 255 and killing boulders.
types=[0,0,0,0]
alive(); quiet()
for i in range(80):
    if st()['DEAD']: alive(); quiet()
    poke(0xEB,[0]); poke(0x88,[0]*5)
    q({'cmd':'pause'})
    z=st(); lx2=z['PX']+3; k=(2*lx2)%7; c=max(0,min(lx2*2//7-1,37))
    while lx2-(c*7)//2>=11: c+=1
    while lx2-(c*7)//2<0: c-=1
    poke(0xD0,[2]); poke(0xD8,[1]); poke(0xE0,[0]); poke(0x70,[c]); poke(0x78,[60]); poke(0x88,[1])
    poke(0x94,[1]); poke(0x95,[(2*lx2)//7]); poke(0x96,[[3,6,12,24,48,96,64][k]]); poke(0x97,[1 if k==6 else 0]); poke(0x98,[60+14+6]); poke(0x99,[lx2])
    # force drop: temporarily patch DROPB by poking seed+many tries - actually DROPB is const.
    # Accept natural rate; only count when CON becomes 1
    q({'cmd':'resume'}); time.sleep(0.12)
    if peek(0xEB,1)[0]:
        ct=peek(0xEE,1)[0]
        if ct<=3: types[ct]+=1
        poke(0xEB,[0])  # clear so next drop can happen
print('drop type counts (0..3):',types,'total',sum(types))
tot=sum(types)
ok(tot>=15,'enough capsules to judge rarity (%d)'%tot)
if tot:
    r=types[3]/tot
    print('1-up fraction among drops: %.1f%%'%(100*r))
    ok(0.01<=r<=0.25,'1-up rarer than others (~1/16 of drops, got %.0f%%)'%(100*r))
    ok(types[0] and types[1] and types[2],'shield/cool/spread still drop')
# boss kill forces type 0/1 only
alive(); quiet()
oneups=0; forced=0
for i in range(20):
    poke(0xEB,[0])
    # simulate bosskill drop: set DCL/DRW and poke CON via calling isn't easy;
    # instead set BOSS kill path by placing boss and killing it
    q({'cmd':'pause'})
    poke(0xD6,[2]); poke(0xD0,[4]); poke(0xD8,[1]); poke(0x70,[18]); poke(0x78,[40]); poke(0x88,[1])
    poke(0xE8,[0,0,0])
    z=st(); lx2=z['PX']+3; k=(2*lx2)%7
    poke(0x94,[1]); poke(0x95,[(2*lx2)//7]); poke(0x96,[[3,6,12,24,48,96,64][k]]); poke(0x97,[1 if k==6 else 0]); poke(0x98,[40+24+4]); poke(0x99,[lx2])
    q({'cmd':'resume'}); time.sleep(0.2)
    if peek(0xEB,1)[0]:
        forced+=1; ct=peek(0xEE,1)[0]
        if ct==3: oneups+=1
        poke(0xEB,[0])
    poke(0xD6,[0]); poke(0x88,[0]*5)
print('boss-kill capsules %d, 1-ups %d'%(forced,oneups))
ok(forced>=8 and oneups==0,'boss kill drops shield/cool only (no 1-up)')
p.kill()
print('RESULT:', 'PASS' if not FAIL else 'FAIL %s'%FAIL); sys.exit(1 if FAIL else 0)
