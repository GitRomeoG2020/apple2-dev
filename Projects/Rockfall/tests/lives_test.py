#!/usr/bin/env python3
"""Lives + heat test: boot disk/rockfall.dsk in bobbin-ai and check
 - a game starts with 3 ships, HUD col 16 = ship glyph, col 17 = lives digit;
 - a rock hit without shield: DEAD during the crash beat, then respawn (DEAD 0), lives -1,
   field cleared and re-staggered, score kept, HUD updated;
 - shield still absorbs a hit without costing a ship;
 - a boss in play when the ship dies is due again (BOSS 1), boss reaching the ship row costs a ship;
 - the last ship lost = game over (DEAD stays set, lives 0);
 - held fire overheats on the 6th shot (HEATSHOT 16; was the 5th at 18).
Usage: lives_test.py [enhanced|plus]"""
import subprocess,time,os,sys,json,pty,shutil
sys.path.insert(0,'/workspace/apple2/tests'); from sock import send
MACH=sys.argv[1] if len(sys.argv)>1 else 'enhanced'
D=os.path.dirname(os.path.abspath(__file__))+'/..'; SOCK='/tmp/rflives_'+MACH+'.sock'
if os.path.exists(SOCK): os.remove(SOCK)
DSK='/tmp/rf_lives_%s.dsk'%MACH; shutil.copy(D+'/disk/rockfall.dsk',DSK)
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
GL={tuple(FONT[g*5:g*5+5]):('0123456789CDEHIPR SOATLV' +'xxx^')[g] for g in range(28)}
FAIL=[]
def ok(c,msg): print(('PASS ' if c else 'FAIL ')+msg); c or FAIL.append(msg)
def st():
    z=peek(0x4E,0xA0); g=lambda a:z[a-0x4E]
    return dict(LIVES=g(0x4E),DEAD=g(0x67),PX=g(0x5C),RON=[g(0x88+i) for i in range(5)],RWAIT=[g(0x80+i) for i in range(5)],
                SCORE=int('%02X%02X'%(g(0x64),g(0x63))),HEAT=g(0xA4),OVH=g(0xA5),BOSS=peek(0xD6,1)[0],PUT=peek(0xE8,1)[0])
def hud(pg=0x2000):
    mm=peek(pg,0x1000)+peek(pg+0x1000,0x1000); return ''.join(GL.get(tuple(mm[A(186+r)+c] for r in range(5)),'?') for c in range(1,19))
def norocks(): poke(0x88,[0]*5); poke(0x80,[0xFF]*5)
def quiet(): norocks(); poke(0xB8,[0xFF,0x7F]); poke(0x5E,[0])
def hit():
    """drop a medium rock onto the ship (speed 0); returns (state while dying, state ~2.5 s later)"""
    quiet(); poke(0x61,[0])
    q({'cmd':'pause'}); poke(0x5C,[71]); poke(0xD0,[1]); poke(0xD8,[1]); poke(0xE0,[0]); poke(0x70,[20]); poke(0x78,[135]); poke(0x88,[1]); q({'cmd':'resume'})
    time.sleep(0.15); a=st()
    for t in range(30):
        time.sleep(0.15); b=st()
        if not b['DEAD']: break
    return a,b
time.sleep(6); key(' '); time.sleep(1.0); quiet(); time.sleep(0.3)
z=st(); h=hud(); print('start: LIVES %d HUD %r'%(z['LIVES'],h))
ok(z['LIVES']==3 and h[15:17]=='^3' and h[:4]=='0000' and 'SPD' in h and 'LV' in h,'new game: 3 ships, HUD shows ship icon + 3')
poke(0x63,[0x42,0x01])
a,b=hit(); print('hit 1: during DEAD %d LIVES %d; after DEAD %d LIVES %d RON %s RWAIT %s SCORE %d'%(a['DEAD'],a['LIVES'],b['DEAD'],b['LIVES'],b['RON'],b['RWAIT'],b['SCORE']))
ok(a['DEAD']==1,'rock hit marks the ship dead during the crash')
ok(b['DEAD']==0 and b['LIVES']==2,'respawn: play continues with 2 ships')
ok(b['SCORE']==142,'score kept across a lost ship')
time.sleep(0.3); h=hud(); print('HUD %r'%h); ok(h[15:17]=='^2','HUD shows 2')
# shield absorbs
quiet(); poke(0xE8,[200]); a,b=hit(); ok(b['DEAD']==0 and b['LIVES']==2 and b['PUT']==0,'shield absorbs a hit, no ship lost')
# boss in play, ship hit by a rock -> boss due again
quiet(); poke(0xD6,[2]); poke(0xD0,[4]); poke(0x78,[10]); poke(0x70,[5])
q({'cmd':'pause'}); poke(0x88,[1]); poke(0x5C,[71]); poke(0xD0+1,[1]); poke(0xD8+1,[1]); poke(0xE0+1,[0]); poke(0x71,[20]); poke(0x79,[135]); poke(0x89,[1]); q({'cmd':'resume'})
for t in range(30):
    time.sleep(0.15); b=st()
    if b['LIVES']==1 and not b['DEAD']: break
print('boss death: LIVES %d BOSS %d DEAD %d'%(b['LIVES'],b['BOSS'],b['DEAD']))
ok(b['LIVES']==1 and b['BOSS'] in (1,2),'ship lost during a boss: boss re-enters (due again)')
# last ship: game over
for t in range(40):
    b=st()
    if b['BOSS']==2: break
    time.sleep(0.25)
q({'cmd':'pause'}); poke(0x88,[1,0,0,0,0]); poke(0x78,[112]); poke(0xE8,[0]); poke(0xD7,[200]); q({'cmd':'resume'}); time.sleep(3.0)
b=st(); print('boss at ship row, last ship: LIVES %d DEAD %d BOSS %d'%(b['LIVES'],b['DEAD'],b['BOSS']))
ok(b['LIVES']==0 and b['DEAD']==1 and b['BOSS']==0,'boss at the ship row costs the last ship: game over')
# new game resets lives
time.sleep(1.5)
for t in range(20):
    if not st()['DEAD']: break
    key('A'); time.sleep(0.6)
z=st(); ok(z['LIVES']==3 and not z['DEAD'],'new game restores 3 ships')
# heat: held fire
quiet(); time.sleep(4); shots=0; last=st()['HEAT']; t0=time.time(); ov=False
while time.time()-t0<5:
    q({'cmd':'keys','text':' '}); norocks(); z=st()
    if z['HEAT']>last: shots+=1
    last=z['HEAT']
    if z['OVH']: ov=True; break
    time.sleep(0.03)
print('held fire: overheat %s after %d shots, %.2f s'%(ov,shots,time.time()-t0))
ok(ov and 6<=shots<=7,'held fire overheats on the ~6th shot (was 5)')
p.kill()
print('RESULT:', 'PASS' if not FAIL else 'FAIL %s'%FAIL); sys.exit(1 if FAIL else 0)
