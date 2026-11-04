#!/usr/bin/env python3
"""Power-ups test: boot disk/rockfall.dsk in bobbin-ai and check
 - drops: a destroyed boulder drops a capsule ~1 in 3, a hit flyer ~1 in 2; the capsule blinks (2 frames),
   falls 1 row/frame, is drawn exactly (both-page model) and vanishes at the landscape line;
 - pickup on contact with the ship -> timer PTIME (200 ticks ~10 s); collecting again refreshes it;
 - SHIELD: bubble drawn instead of the ship; a rock hit is absorbed (rock destroyed), shield gone, next hit kills;
 - COOL: HEAT reset to 0 and stays 0 while firing, label reads COOL, back to HEAT when it ends;
 - SPREAD: one shot = 3 bolts (center + 10 px left/right), each can hit a rock;
 - HUD: no HI; active power-ups packed side by side (icon + shrinking bar), timers decrease and expire;
   level banner pauses the timers; a new game clears everything;
 - frame time with capsule / spread bolts / shield vs plain play.
Saves PNGs: capsule falling, 3 stacked in the HUD, shield bubble, spread shot.  Usage: powerup_test.py [enhanced|plus]"""
import subprocess,time,os,sys,json,pty,re,shutil
sys.path.insert(0,'/workspace/apple2/tests'); from sock import send
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import flymodel
MACH=sys.argv[1] if len(sys.argv)>1 else 'enhanced'
D=T+'/..'; SOCK='/tmp/rfpow_'+MACH+'.sock'
if os.path.exists(SOCK): os.remove(SOCK)
DSK='/tmp/rf_pow_%s.dsk'%MACH; shutil.copy(D+'/disk/rockfall.dsk',DSK)
m,s=pty.openpty()
p=subprocess.Popen(['/workspace/apple2/bin/bobbin-ai','--simple','--remain','--no-turbo','-m',MACH,'--disk',DSK,'--control-socket',SOCK],stdin=s,stdout=s,stderr=s,start_new_session=True)
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
key=lambda c,t=0.05:(q({'cmd':'keys','text':c}),time.sleep(t))
A=lambda y:(y&7)*0x400+((y>>3)&7)*0x80+(y>>6)*0x28
L=open(D+'/build/rockfall.lst').read(); M=open(D+'/build/rockfall.map').read()
ROD=int(re.search(r'^RODATA\s+([0-9A-F]+)',M,re.M).group(1),16)
lab=lambda n:ROD+int(re.search(r'^([0-9A-F]+)r 2 .*?\b'+n+':',L,re.M).group(1),16)
RW=[1,2,3,3]; RH=[6,8,14,14]; PTS=[3,5,15]; NAMES=['pebble','rock','boulder']
FAIL=[]
def ok(c,msg): print(('PASS ' if c else 'FAIL ')+msg); c or FAIL.append(msg)
def st():
    z=peek(0x50,0xA0); g=lambda a:z[a-0x50]
    return dict(DEAD=g(0x67),SCORE=int('%02X%02X'%(g(0x64),g(0x63))),BACK=g(0x92),FRAME=g(0x90),LON=g(0x94),LY=g(0x98),PX=g(0x5C),SPEED=g(0x61),LEVEL=g(0xA7),
        RON=[g(0x88+i) for i in range(5)],RY=[g(0x78+i) for i in range(5)],RCOL=[g(0x70+i) for i in range(5)],RSIZE=[g(0xD0+i) for i in range(5)],RHP=[g(0xD8+i) for i in range(5)],PK=g(0xBA),FON=g(0xB3))
def norocks(): poke(0x88,[0]*5); poke(0x80,[0xFF]*5)
def quiet(): norocks(); poke(0xB8,[0xFF,0x7F]); poke(0x5E,[0])
def alive():
    for t in range(30):
        if not st()['DEAD']: return
        time.sleep(3 if t==0 else 0.6); key('A'); time.sleep(0.5)
def rock(i,size,col,y,hp=None):
    poke(0xD0+i,[size]); poke(0xD8+i,[hp if hp is not None else (2 if size==2 else 1)]); poke(0xE0+i,[0]); poke(0x70+i,[col]); poke(0x78+i,[y]); poke(0x88+i,[1])
def snap():
    q({'cmd':'pause'})
    try: z=st(); sv=peek(0x1800,0x300); pg=[peek(0x2000,0x2000),peek(0x4000,0x2000)]
    finally: q({'cmd':'resume'})
    return z,sv,pg
def model(pg,sv):
    e=[[0]*40 for _ in range(152)]
    if not sv[0x2BC+pg]: return e
    def x(d,col,y,w,h):
        for r in range(h):
            for b in range(w):
                if 0<=y+r<152: e[y+r][col+b]^=d[r*w+b]
    px=sv[0x2B0+pg]
    if not flymodel.shield(sv,pg): x(SHIP[(px*2)%7],(px*2)//7,140,3,8)
    for i in range(5):
        if sv[0x280+pg*8+i]: sp=sv[0x2D0+pg*8+i]; x(RSPR[sp],sv[0x290+pg*8+i],sv[0x2A0+pg*8+i],RW[sp],RH[sp])
    for i in range(36):
        j=pg*64+i; e[sv[0x200+j]][sv[0x100+j]]^=sv[0x180+j]
    return flymodel.apply(e,sv,pg,FONT)
def mism(sv,pgs,pages=(0,1)):
    return sum(1 for pg in pages for y,row in enumerate(model(pg,sv)) for b in range(40) if pgs[pg][A(y)+b]!=row[b])
def exact(tries=8):
    """snapshot until the shown page matches the model (the back page may be caught mid-render; frames with
    a laser bolt in flight are not modelled and are skipped). Returns (mismatches, z, sv, pages)."""
    last=None
    for t in range(tries):
        z,sv,pgs=snap()
        if sv[0x2B2] or sv[0x2B3]: time.sleep(0.02); continue
        n=mism(sv,pgs,(1-z['BACK'],))      # the shown page; the back page may be mid-render
        if n==0: return 0,z,sv,pgs
        last=(n,z,sv,pgs); time.sleep(0.023)
    if last is None: return 0,z,sv,pgs
    n,z,sv,pgs=last
    for pg in (1-z['BACK'],):
        e=model(pg,sv); bad=[(y,b,pgs[pg][A(y)+b],e[y][b]) for y in range(152) for b in range(40) if pgs[pg][A(y)+b]!=e[y][b]]
        if bad: print('  mismatch page%d:'%(pg+1),bad[:6],'BACK',z['BACK'],'PK',z['PK'],'FON',z['FON'],'DEAD',z['DEAD'])
    return n,z,sv,pgs
strip=lambda mem:b''.join(mem[A(y):A(y)+40] for y in range(152,184))
def png(mem,path):
    from PIL import Image
    im=Image.new('RGB',(280,192)); px=im.load()
    for y in range(192):
        bits=[];hb=[]
        for b in range(40):
            v=mem[A(y)+b]
            for i in range(7): bits.append((v>>i)&1); hb.append(v>>7)
        for xx in range(280):
            if not bits[xx]: continue
            if (xx>0 and bits[xx-1]) or (xx<279 and bits[xx+1]): col=(255,255,255)
            elif hb[xx]: col=(20,207,253) if xx%2==0 else (255,106,60)
            else: col=(255,68,253) if xx%2==0 else (20,245,60)
            px[xx,y]=col
    im.resize((560,384),Image.NEAREST).save(path); print('screenshot:',path)
time.sleep(6); FONT=peek(lab('font'),120); SL,SH=peek(lab('ship_shift_lo'),7),peek(lab('ship_shift_hi'),7)
SHIP={k:peek(SL[k]|SH[k]<<8,24) for k in range(7)}
RSPR=[peek(lab(n),RW[i]*RH[i]) for i,n in enumerate(['pebble','rock','boulder','boulder_cracked'])]
import re as _re; sys.path.insert(0,D+'/tools'); import gen_land
_inc=open(D+'/src/land.inc').read()
LANDS=[bytes(gen_land.unrle([int(v,16) for v in _re.findall(r'\$([0-9A-F]{2})',_re.search(r'^land%d:\n((?:\s+\.byte .*\n)+)'%k,_inc,_re.M).group(1))])) for k in range(len(gen_land.LANDS))]

PUT=0xE8; CON=0xEB; KCOL=0xEC; CY=0xED; CTYPE=0xEE; SON=0xEF; HEAT=0xA4; OVH=0xA5; LVLUP=0xA9
z0=lambda a,n=1:list(peek(a,n))
GL={tuple(FONT[g*5:g*5+5]):'0123456789CDEHIPR SOATLV'[g] for g in range(24)}
FONTX=peek(lab('font'),27*5); ICON={tuple(FONTX[g*5:g*5+5]):n for g,n in ((24,'shield'),(25,'cool'),(26,'spread'))}
BARW=[0,1,3,7,15,31,63,127]
def hudmem(): return peek(0x2000,0x2000)
def hudtext(m): return ''.join(GL.get(tuple(m[A(186+r)+c] for r in range(5)),'?') for c in range(1,19))
def slots(m):
    out=[]
    for c in (19,21,23):
        g=tuple(m[A(186+r)+c] for r in range(5))
        if not any(g): out.append(None); continue
        bar=m[A(187)+c+1]; out.append((ICON.get(g,'?'),BARW.index(bar) if bar in BARW else -1))
    return out
def label(m): return ''.join(GL.get(tuple(m[A(186+r)+c] for r in range(5)),'?') for c in range(26,30))
def fresh():
    alive(); quiet(); poke(PUT,[0,0,0]); poke(CON,[0]); poke(SON,[0,0]); poke(0x61,[1]); time.sleep(0.1)
def capsule(t,col,y): poke(KCOL,[col,y,t]); poke(CON,[1])
def boulder_kill():
    """shoot a 1-hp boulder above the ship; returns True if a capsule appeared"""
    q({'cmd':'pause'}); z=st(); lx2=z['PX']+3; k=(2*lx2)%7; c=max(0,min(lx2*2//7-1,37))
    while lx2-(c*7)//2>=11: c+=1
    while lx2-(c*7)//2<0: c-=1
    norocks(); poke(CON,[0]); rock(0,2,c,60,1)
    poke(0x94,[1]); poke(0x95,[(2*lx2)//7]); poke(0x96,[[3,6,12,24,48,96,64][k]]); poke(0x97,[1 if k==6 else 0]); poke(0x98,[60+14+6]); poke(0x99,[lx2])
    q({'cmd':'resume'}); time.sleep(0.1); r=st()
    return (not r['RON'][0] or r['RY'][0]<60), z0(CON)[0]
key(' '); time.sleep(1.5)
# ---------- 1: drops ----------
fresh(); kills=drops=0
for i in range(60):
    if st()['DEAD']: fresh()
    k,d=boulder_kill(); kills+=k; drops+=d
print('boulders destroyed %d, capsules dropped %d (%.0f%%)'%(kills,drops,100*drops/max(1,kills)))
ok(kills>=55 and 0.15<=drops/kills<=0.55,'boulder drops a capsule about 1 in 3')
fresh(); fh=fd=0
for i in range(30):
    if st()['DEAD']: fresh()
    q({'cmd':'pause'}); z=st(); lx2=z['PX']+3; k=(2*lx2)%7; poke(CON,[0])
    poke(0xB4,[lx2+9,60,0,i%2]); poke(0xB3,[1])          # FX FY FDIR FTYPE, then FON
    poke(0x94,[1]); poke(0x95,[(2*lx2)//7]); poke(0x96,[[3,6,12,24,48,96,64][k]]); poke(0x97,[1 if k==6 else 0]); poke(0x98,[60+7+6]); poke(0x99,[lx2])
    q({'cmd':'resume'}); time.sleep(0.1); r=st(); fh+=(r['FON']==0); fd+=z0(CON)[0]
    time.sleep(1.2)                                         # let the popup finish
print('flyers hit %d, capsules dropped %d'%(fh,fd))
ok(fh>=28 and 0.2<=fd/fh<=0.8,'a hit flyer drops a capsule about 1 in 2')
# ---------- 2: capsule falls, blinks, drawn exactly, vanishes at the landscape ----------
fresh(); poke(0x5C,[130]); capsule(2,8,10); time.sleep(0.05)
a=st()['FRAME'],z0(CY)[0]; time.sleep(0.5); b=st()['FRAME'],z0(CY)[0]
rate=(b[1]-a[1])/((b[0]-a[0])&255); print('capsule fall rate %.2f rows/frame'%rate)
ok(abs(rate-1)<0.1,'capsule falls 1 row per frame')
n,z,sv,pgs=exact(); png(pgs[1-z['BACK']],T+'/powerup_capsule_%s.png'%MACH)
ok(n==0 and sv[0x2F4+1-z['BACK']],'capsule drawn exactly (model) on the shown page')
seen=set()
for i in range(12):
    _,sv,_=snap(); seen.add(sv[0x2FA]); seen.add(sv[0x2FB]); time.sleep(0.03)
ok({4,5}<=seen,'capsule glows: blinks between 2 frames (seen %s)'%sorted(seen))
lastcy=0
while z0(CON)[0]:                                          # lowest row the capsule was actually drawn at
    v=peek(0x1AF4,6); lastcy=max([lastcy]+[v[4+i] for i in (0,1) if v[i]]); time.sleep(0.005)
time.sleep(0.1); z,sv,pgs=snap()
ok(lastcy<=152-9 and all(strip(x)==LANDS[peek(0xB2,1)[0]] for x in pgs) and not st()['DEAD'],'capsule vanishes at the landscape line (last top row %d), landscape intact'%lastcy)
n,z,sv,pgs=exact(); ok(n==0,'capsule erased cleanly')
# ---------- 3: pickup + refresh ----------
fresh(); px=st()['PX']; capsule(0,(2*px)//7,110); time.sleep(0.6)
p=z0(PUT,3); print('after pickup: timers',p,'CON',z0(CON)[0])
ok(z0(CON)[0]==0 and 180<=p[0]<=200 and not st()['DEAD'],'capsule collected on contact: SHIELD timer ~200')
poke(PUT,[40]); capsule(0,(2*px)//7,110); time.sleep(0.6); p2=z0(PUT)[0]
ok(p2>=180,'collecting the same type again refreshes the timer (40 -> %d)'%p2)
# ---------- 4: SHIELD ----------
fresh(); poke(PUT,[200]); time.sleep(0.15)
n,z,sv,pgs=exact(); png(pgs[1-z['BACK']],T+'/powerup_shield_%s.png'%MACH)
ok(n==0 and sv[0x2E0+1-z['BACK']],'shield bubble drawn instead of the ship (exact model)')
px=st()['PX']; q({'cmd':'pause'}); norocks(); rock(0,1,(2*px)//7,132); q({'cmd':'resume'}); time.sleep(0.25)
z=st(); print('shield hit: DEAD %d, shield timer %d, rock on %d'%(z['DEAD'],z0(PUT)[0],z['RON'][0]))
ok(not z['DEAD'] and z0(PUT)[0]==0 and not (z['RON'][0] and z['RY'][0]>=120),'shield absorbs one hit (rock destroyed), then breaks')
n,z,sv,pgs=exact(); ok(n==0 and not sv[0x2E0] and not sv[0x2E1],'plain ship back after the break, both pages clean')
q({'cmd':'pause'}); norocks(); rock(0,1,(2*px)//7,132); q({'cmd':'resume'}); time.sleep(0.25)
ok(st()['DEAD']==1,'next hit without shield kills')
# ---------- 5: COOL ----------
fresh(); poke(HEAT,[40]); px=st()['PX']; capsule(1,(2*px)//7,110); time.sleep(0.6)
m=hudmem(); print('COOL picked: HEAT %d label %r'%(z0(HEAT)[0],label(m)))
ok(z0(HEAT)[0]==0 and label(m)=='COOL','COOL: heat reset to 0, gauge label COOL')
mx=0
for i in range(25): key(' ',0.06); mx=max(mx,z0(HEAT)[0]); ok_ovh=z0(OVH)[0]
ok(mx==0 and ok_ovh==0,'COOL: 25 rapid shots, heat stays 0 (max %d), no overheat'%mx)
poke(PUT+1,[2]); time.sleep(0.3); m=hudmem()
ok(label(m)=='HEAT' and z0(PUT+1)[0]==0,'COOL expired: label back to HEAT')
for i in range(6): key(' ',0.12)
ok(z0(HEAT)[0]>0,'heat builds again after COOL (%d)'%z0(HEAT)[0])
# ---------- 6: SPREAD ----------
fresh(); poke(PUT+2,[200]); poke(0x5C,[60]); time.sleep(0.4)
def colfor(x2,w=7):
    c=(2*x2)//7
    while x2-(c*7)//2>=w: c+=1
    while x2-(c*7)//2<0: c-=1
    return c
lx2=63; q({'cmd':'pause'}); norocks()
for i,x2 in enumerate((lx2-5,lx2,lx2+5)): rock(i,1,colfor(x2,7),40)
sc0=st()['SCORE']; q({'cmd':'resume'})
key(' ',0)
shot=None
for i in range(40):
    z,sv,pgs=snap()
    if sv[0x2E2+2*(1-z['BACK'])] and sv[0x2E3+2*(1-z['BACK'])] and 60<z['LY']<120: shot=(z,sv,pgs); break
def mism_bolt(sv,pgs,pg):
    e=model(pg,sv)
    if sv[0x2B2+pg]:                       # centre bolt (not in the shared model)
        c,m1,m2,y=sv[0x2B4+pg],sv[0x2B6+pg],sv[0x2B8+pg],sv[0x2BA+pg]
        for r in range(12):
            e[y+r][c]^=m1
            if m2: e[y+r][c+1]^=m2
    return sum(1 for y in range(152) for b in range(40) if pgs[pg][A(y)+b]!=e[y][b])
if shot: png(shot[2][1-shot[0]['BACK']],T+'/powerup_spread_%s.png'%MACH); n=mism_bolt(shot[1],shot[2],1-shot[0]['BACK'])
ok(shot is not None and n==0,'one shot = 3 bolts on screen (center + both sides), drawn exactly')
time.sleep(0.4); z=st(); print('spread vs 3 rocks: score %d -> %d, RON %s'%(sc0,z['SCORE'],z['RON'][:3]))
# rocks respawn within 0.4 s, so RON is not reliable here; +15 = three +5 rock kills
ok(z['SCORE']-sc0>=15 and (z['SCORE']-sc0)%5==0,'all 3 bolts hit (3 rocks destroyed, +15)')
# ---------- 7: HUD stacked, timers decrease and expire ----------
fresh(); poke(PUT,[200,150,100]); time.sleep(0.2); m=hudmem(); s1=slots(m); print('HUD text %r slots %s'%(hudtext(m),s1))
ok(' HI' not in hudtext(m) and hudtext(m).startswith('SC ') and 'SPD' in hudtext(m) and 'LV' in hudtext(m),'HUD keeps SC SPD LV, no HI')
ok([s and s[0] for s in s1]==['shield','cool','spread'] and s1[0][1]>=s1[1][1]>=s1[2][1]>0,'all 3 power-ups stacked with bars')
png(peek(0x2000,0x2000),T+'/powerup_hud_%s.png'%MACH)
p0=z0(PUT,3); time.sleep(2); p1=z0(PUT,3); print('timers %s -> %s in 2 s'%(p0,p1))
ok(all(30<=a-b<=60 for a,b in zip(p0,p1)),'timers decrease ~20 ticks/s')
poke(PUT,[0,0,40]); time.sleep(0.2); s2=slots(hudmem()); print('spread only:',s2)
ok(s2[0] and s2[0][0]=='spread' and s2[1] is None and s2[2] is None,'slots repack left when others end')
t0=time.time(); poke(PUT+2,[200])
while z0(PUT+2)[0] and time.time()-t0<15:
    if st()['DEAD']: break
    norocks(); time.sleep(0.1)
dur=time.time()-t0; print('spread lasted %.1f s'%dur); s3=slots(hudmem())
ok(9<=dur<=11.5 and s3==[None,None,None],'power-up lasts ~10 s then expires, HUD slots empty')
# banner pauses timers
fresh(); poke(PUT,[200,0,0]); time.sleep(0.1); poke(LVLUP,[1]); time.sleep(0.3)
a=z0(PUT)[0]; time.sleep(0.8); b=z0(PUT)[0]; lv=z0(LVLUP)[0]
ok(lv==1 and a==b,'level banner pauses the timers (%d -> %d)'%(a,b))
time.sleep(1.5)
# ---------- 8: new game clears ----------
alive(); poke(PUT,[200,200,200]); capsule(1,10,20); poke(0x67,[1]); time.sleep(3.5); key('A'); time.sleep(1); alive(); time.sleep(0.3)
p=z0(PUT,3); c=z0(CON)[0]; s=slots(hudmem()); print('new game: timers',p,'CON',c,'slots',s)
ok(p==[0,0,0] and c==0 and s==[None,None,None] and label(hudmem())=='HEAT','new game clears power-ups, capsule and HUD slots')
# ---------- 9: frame time ----------
def fps(setup,secs=5):
    alive(); quiet(); poke(0x61,[1]); poke(0x5C,[0])
    q({'cmd':'pause'})
    for i,(sz,col) in enumerate(setup): rock(i,sz,col,20)
    q({'cmd':'resume'}); time.sleep(0.2)
    f0=st()['FRAME']; n=0; last=f0; t0=time.time()
    while time.time()-t0<secs:
        time.sleep(0.1); poke(0x78,[20]*len(setup)) if setup else None
        if extra: extra()
        f=st()['FRAME']; n+=(f-last)&255; last=f
    return n/(time.time()-t0)
def capk(): poke(CY,[20]); poke(CON,[1]); poke(KCOL,[30])
def boltk(): poke(0x94,[1,8,3,0,100])                     # LON LC LM1 LM2 LY: centre bolt kept in flight
def sidek(): boltk(); poke(SON,[1,1]); poke(0xF1,[30,40]); poke(0xF3,[8,11]); poke(0xF5,[3,12,0,0])
def shk(): poke(PUT,[200])
def allk(): capk(); sidek(); shk()
R5=[(1,c) for c in (8,14,20,26,32)]; MX=[(2,8),(2,14),(1,20),(1,26),(1,32)]
cases=[('5 rocks',R5,None),('5 rocks + capsule',R5,capk),('5 rocks + 1 bolt (normal shot)',R5,boltk),('5 rocks + 3 bolts (spread shot)',R5,sidek),('5 rocks + shield',R5,shk),
       ('5 rocks + capsule + 3 bolts + shield',R5,allk),('max mix + capsule + 3 bolts + shield',MX,allk)]
out=[]
for name,setup,extra in cases:
    f=fps(setup); out.append((name,f)); print('%-40s %.1f fps = %d cycles/frame'%(name,f,1023000/f))
    poke(PUT,[0,0,0]); poke(CON,[0])
base=1023000/out[0][1]; dev=[(n,100*(1023000/f-base)/base) for n,f in out]
for n,d in dev: print('  %-40s %+.1f%% vs 5 rocks'%(n,d))
sp=100*(out[2][1]/out[3][1]-1); print('  spread shot vs normal shot: %+.1f%%'%sp)
ok(abs(dev[1][1])<2.5 and abs(dev[4][1])<2.5 and abs(sp)<2.5,'capsule, shield and spread extras each within ~2% (spread vs a normal shot)')
print('worst case (all at once): %+.1f%%'%max(abs(d) for n,d in dev))
q({'cmd':'quit'})
print('RESULT:','PASS' if not FAIL else 'FAIL %s'%FAIL)
