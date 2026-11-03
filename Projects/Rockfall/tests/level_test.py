#!/usr/bin/env python3
"""Levels test: boot disk/rockfall.dsk in bobbin-ai, force speed-up steps by poking DODGE=14 (next dodged
rock triggers a step), check LEVEL advances every LEVELSPD=3 steps (also past the SPEED cap), the
"LEVEL N" banner is drawn on both pages for ~1.5 s then fully erased, star colour mode cycles, and a new
game resets to level 1.  Saves a PNG of the banner.  Usage: level_test.py [enhanced|plus]"""
import subprocess,time,os,sys,json,pty
sys.path.insert(0,'/workspace/apple2/tests'); from sock import send
MACH=sys.argv[1] if len(sys.argv)>1 else 'enhanced'
D=os.path.dirname(os.path.abspath(__file__))+'/..'; SOCK='/tmp/rflv_'+MACH+'.sock'
PNG=D+'/tests/level_banner_'+MACH+'.png'
if os.path.exists(SOCK): os.remove(SOCK)
m,s=pty.openpty()
p=subprocess.Popen(['/workspace/apple2/bin/bobbin-ai','--simple','--remain','--no-turbo','-m',MACH,'--disk',D+'/disk/rockfall.dsk','--control-socket',SOCK],stdin=s,stdout=s,stderr=s,start_new_session=True)
os.close(s); q=lambda o:json.loads(send(json.dumps(o),SOCK))
for i in range(50):
    try: q({'cmd':'ping'}); break
    except Exception: time.sleep(0.2)
def peek(a,n):
    out=b''
    while n>0:
        k=min(n,0x1000); out+=bytes(q({'cmd':'peek','addr':a,'len':k})['data']); a+=k; n-=k
    return out
poke=lambda a,d:q({'cmd':'poke','addr':a,'data':d})
def st():
    z=peek(0x50,0x60); return dict(SPEED=z[0x11],DODGE=z[0x12],DEAD=z[0x17],LEVEL=z[0x57],SPDUPS=z[0x58],LVLUP=z[0x59],SMODE=z[0x5A],BACK=z[0x42])
key=lambda c:(q({'cmd':'keys','text':c}),time.sleep(0.05))
A=lambda y:(y&7)*0x400+((y>>3)&7)*0x80+(y>>6)*0x28
FAIL=[]
def ok(c,msg): print(('PASS ' if c else 'FAIL ')+msg); c or FAIL.append(msg)
F=None
def banner_text(mem):
    out=''
    for c in range(16,24):
        g=tuple(mem[A(74+2*r)+c] for r in range(5)); g2=tuple(mem[A(75+2*r)+c] for r in range(5))
        out+=GL.get(g,'?') if g==g2 else '?'
    return out
def like(t,want): return sum(a==b for a,b in zip(t,want))>=len(want)-1   # a frozen rock/star XORed over one glyph is OK
def png(mem,path):
    from PIL import Image
    im=Image.new('RGB',(280,192)); px=im.load()
    for y in range(192):
        bits=[];hb=[]
        for b in range(40):
            v=mem[A(y)+b]
            for i in range(7): bits.append((v>>i)&1); hb.append(v>>7)
        for x in range(280):
            if not bits[x]: continue
            if (x>0 and bits[x-1]) or (x<279 and bits[x+1]): col=(255,255,255)
            elif hb[x]: col=(20,207,253) if x%2==0 else (255,106,60)
            else: col=(255,68,253) if x%2==0 else (20,245,60)
            px[x,y]=col
    im.resize((560,384),Image.NEAREST).save(path)
def alive():
    for t in range(20):
        if not st()['DEAD']: return
        time.sleep(3 if t==0 else 0.6); key('A'); time.sleep(0.5)
def step(setup=()):
    """force one speed-up step (after applying setup pokes); returns (state before, state after)"""
    for attempt in range(5):
        alive()
        for a,v in setup: poke(a,[v])
        z0=st(); poke(0x62,[14])
        t0=time.time()
        while time.time()-t0<8:
            z=st()
            if z['DEAD']: break
            if z['SPDUPS']!=z0['SPDUPS'] or z['LEVEL']!=z0['LEVEL']: return z0,z
            time.sleep(0.01)
        print('  (died or timed out during step, retrying from a new game)')
        if not setup: return None,None
    return None,None
time.sleep(6); key(' '); time.sleep(1.5)
LEVELSPD=3
lbl=open(D+'/build/rockfall.map').read()
import re
L=open(D+'/build/rockfall.lst').read(); ROD=int(re.search(r'^RODATA\s+([0-9A-F]+)',lbl,re.M).group(1),16)
FA=ROD+int(re.search(r'^([0-9A-F]+)r 2 .*?\bfont:',L,re.M).group(1),16)
F=peek(FA,24*5); GL={tuple(F[g*5:g*5+5]):'0123456789CDEHIPR SOATLV'[g] for g in range(24)}
z=st(); print('new game:',z); ok(z['LEVEL']==1 and z['SPDUPS']==0 and z['SMODE']==0,'new game starts at LEVEL 1, SPDUPS 0, white stars')
# --- 3 steps -> level 2 ---
lv_ok=True; n=0; banner=None
while n<LEVELSPD:
    z0,z=step()
    if z is None: alive(); n=0; continue      # a death resets the game -> start counting again
    n+=1; print('  step %d: SPEED %d->%d SPDUPS %d->%d LEVEL %02X->%02X LVLUP %d'%(n,z0['SPEED'],z['SPEED'],z0['SPDUPS'],z['SPDUPS'],z0['LEVEL'],z['LEVEL'],z['LVLUP']))
    if n<LEVELSPD: lv_ok&= z['LEVEL']==1 and z['SPDUPS']==n
ok(lv_ok,'LEVEL stays 1 for the first %d speed-ups'%(LEVELSPD-1))
ok(z['LEVEL']==2 and z['SPDUPS']==0 and z['SMODE']==1,'LEVEL 2 after %d speed-ups (SPDUPS reset, star mode 1=violet)'%LEVELSPD)
# --- banner: catch it while the game waits ---
t0=time.time(); seen=None
while time.time()-t0<3:
    q({'cmd':'pause'}); z=st()
    if z['LVLUP']:
        q({'cmd':'resume'}); time.sleep(0.3); q({'cmd':'pause'}); z=st()
        pgs=[peek(0x2000,0x2000),peek(0x4000,0x2000)]; seen=time.time()-t0
        q({'cmd':'resume'}); break
    q({'cmd':'resume'}); time.sleep(0.01)
if seen is not None:
    txt=[banner_text(pg) for pg in pgs]; print('banner decoded page1=%r page2=%r'%tuple(txt))
    ok(like(txt[0],'LEVEL 2 ') and like(txt[1],'LEVEL 2 '),'LEVEL 2 banner on both HGR pages')
    png(pgs[1-z['BACK']],PNG); print('banner screenshot:',PNG)
    t1=time.time()
    while st()['LVLUP'] and time.time()-t1<5: time.sleep(0.02)
    dur=time.time()-t1+seen+0.3; print('banner visible ~%.2fs (wall, --no-turbo)'%dur); ok(1.0<dur+0.3<2.5,'banner lasts ~1.5 s')
    time.sleep(0.1); pg2=[peek(0x2000,0x2000),peek(0x4000,0x2000)]
    ok(all('L' not in banner_text(pg) and 'V' not in banner_text(pg) for pg in pg2),'banner erased from both pages after it ends')
    ok(not st()['DEAD'],'play continues after the banner')
else: ok(False,'banner seen')
# --- steps past the SPEED cap still count: SPEED=5, SPDUPS=2 -> level 3 ---
z0,z=step([(0x61,5),(0xA8,2),(0xA7,2),(0xAA,1)])
if z: print('  capped step: SPEED %d->%d LEVEL %02X->%02X SMODE %d'%(z0['SPEED'],z['SPEED'],z0['LEVEL'],z['LEVEL'],z['SMODE']))
ok(z is not None and z['SPEED']==5 and z['LEVEL']==3 and z['SMODE']==2,'level still advances with SPEED capped at 5 (LEVEL 3, star mode 2=green)')
sv0=peek(0x1800,0x60); time.sleep(4)
# star colours: respawned stars should be single pixels of the right parity (mode 2 = odd x = green)
sv=peek(0x1800,0x60); cols=sv[0:36]; msk=sv[0x30:0x30+36]
single=[(c,mk) for i,(c,mk) in enumerate(zip(cols,msk)) if bin(mk).count('1')==1 and (c,mk)!=(sv0[i],sv0[0x30+i])]   # respawned since level 3
par=[(c*7+mk.bit_length()-1)%2 for c,mk in single]
print('stars respawned in level 3: %d single-pixel (coloured), parities %s'%(len(single),par)); ok(single and all(x==1 for x in par) if st()['SMODE']==2 else True,'coloured stars have green (odd-x) parity')
# --- level 10 banner shows two digits; game over resets to 1 ---
for tries in range(4):   # a crash on the level-up frame ends the game before the banner: retry
    z0,z=step([(0x61,5),(0xA8,2),(0xA7,9)])
    t0=time.time()
    while not st()['LVLUP'] and time.time()-t0<2: time.sleep(0.01)
    time.sleep(0.3); q({'cmd':'pause'}); zz=st(); t=[banner_text(peek(0x2000,0x2000))]; q({'cmd':'resume'})
    if not zz['DEAD']: break
    print('  (crashed on the level-up frame, retrying)')
print('level 9->%02X, banner %r'%(z['LEVEL'] if z else -1,t[0]),zz); ok(z and z['LEVEL']==0x10 and like(t[0],'LEVEL 10'),'BCD level 10 banner')
time.sleep(2); poke(0x67,[1]); time.sleep(1); alive(); time.sleep(1)
z=st(); print('after game over + new game:',z); ok(z['LEVEL']==1 and z['SPDUPS']==0 and z['SMODE']==0,'new game resets LEVEL to 1')
q({'cmd':'quit'})
print('RESULT:','PASS' if not FAIL else 'FAIL %s'%FAIL)
