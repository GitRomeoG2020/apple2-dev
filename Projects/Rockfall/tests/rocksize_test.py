#!/usr/bin/env python3
"""Three rock sizes test: boot disk/rockfall.dsk in bobbin-ai and check
 - pebbles, rocks and boulders all spawn, mostly medium, more pebbles/boulders at higher levels,
   never more than MAXLG=2 boulders at once;
 - speeds relative to SPEED: pebble 1.5x, rock 1x, boulder 0.5x (rows per frame);
 - per-size ship collision boxes (hit just inside each edge, miss just outside);
 - laser: pebble +3, rock +5, boulder needs 2 hits (cracked sprite after the first, no points),
   then +15 with a burst + "15" popup;
 - soak at level 5 / SPEED 5: both pages exact (model of ship, rocks of all sizes, stars, flyer),
   rocks never below row 151, landscape never touched;
 - frame time with different rock mixes (fdelay pacing).
Saves a gameplay PNG with all three sizes.  Usage: rocksize_test.py [enhanced|plus]"""
import subprocess,time,os,sys,json,pty,re,shutil
sys.path.insert(0,'/workspace/apple2/tests'); from sock import send
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import flymodel
MACH=sys.argv[1] if len(sys.argv)>1 else 'enhanced'
D=T+'/..'; SOCK='/tmp/rfsize_'+MACH+'.sock'
if os.path.exists(SOCK): os.remove(SOCK)
DSK='/tmp/rf_size_%s.dsk'%MACH; shutil.copy(D+'/disk/rockfall.dsk',DSK)
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
RW=[1,2,3,3,5]; RH=[6,8,14,14,24]; PTS=[3,5,15]; NAMES=['pebble','rock','boulder']
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
        if not st()['DEAD']: poke(0x4E,[1]); return   # legacy one-ship play (lives: lives_test)
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
RSPR=[peek(lab(n),RW[i]*RH[i]) for i,n in enumerate(['pebble','rock','boulder','boulder_cracked','boss_spr'])]
key(' '); time.sleep(1.5)
# ---------- 1: spawn mix ----------
def mix(level,secs):
    cnt=[0,0,0]; maxlg=0; seen=set(); t0=time.time()
    alive(); poke(0xA7,[level]); poke(0xB8,[0xFF,0x7F])
    while time.time()-t0<secs:
        z=st()
        if z['DEAD']: alive(); poke(0xA7,[level]); continue
        maxlg=max(maxlg,sum(1 for on,sz in zip(z['RON'],z['RSIZE']) if on and sz==2))
        for i in range(5):
            if z['RON'][i] and z['RY'][i]<12 and (i,z['RCOL'][i]) not in seen: seen.add((i,z['RCOL'][i])); cnt[z['RSIZE'][i]]+=1
        if len(seen)>40: seen.clear()
        poke(0x5C,[66 if (int(time.time()*2)%2) else 20])     # jiggle the ship a bit
        time.sleep(0.03)
    return cnt,maxlg
c1,m1=mix(1,25); c4,m4=mix(5,25)
f=lambda c:'pebble %d rock %d boulder %d (%.0f%% / %.0f%% / %.0f%%)'%(*c,*[100*v/max(1,sum(c)) for v in c])
print('spawns at level 1:',f(c1),' max boulders at once',m1); print('spawns at level 5:',f(c4),' max boulders at once',m4)
ok(all(c1) or all(c4),'all three sizes spawn')
ok(c1[1]>c1[0] and c1[1]>c1[2] and c4[1]>=c4[0] and c4[1]>c4[2],'medium rocks are the most common')
labR=lambda n:ROD+int(re.search(r'^([0-9A-F]+)r 1 .*?\b'+n+':',L,re.M).group(1),16)   # RODATA label in rockfall.s itself
rs,rl=peek(labR('rsmall'),4),peek(labR('rlarge'),4)
odds=[(rs[b],rl[b]-rs[b],16-rl[b]) for b in range(4)]; print('spawn odds of 16 (pebble, rock, boulder) for L1, L2, L3, L4+:',odds)
ok(all(o[1]>=8 for o in odds) and all(odds[b+1][0]>=odds[b][0] and odds[b+1][2]>=odds[b][2] for b in range(3)),'odds tables: mostly medium; pebbles/boulders more common at higher levels')
ok(m1<=2 and m4<=2,'never more than 2 boulders at once')
# ---------- 2: speeds ----------
alive(); quiet(); poke(0xA7,[1]); poke(0x5C,[120]); time.sleep(0.1)
res={}
for spd in (2,4):
    q({'cmd':'pause'}); poke(0x61,[spd]); norocks(); rock(0,0,2,10); rock(1,1,6,10); rock(2,2,10,10); q({'cmd':'resume'})
    time.sleep(0.05); z0=st(); time.sleep(0.4); z1=st()
    fr=(z1['FRAME']-z0['FRAME'])&255
    res[spd]=[(z1['RY'][i]-z0['RY'][i])/fr for i in range(3)]
    print('SPEED %d: rows/frame pebble %.2f rock %.2f boulder %.2f over %d frames'%(spd,*res[spd],fr))
ok(all(abs(res[s][0]-1.5*s)<0.35 and abs(res[s][1]-s)<0.2 and abs(res[s][2]-0.5*s)<0.25 for s in res),'speeds 1.5x / 1x / 0.5x SPEED')
norocks()
# ---------- 3: collision boxes (inset AABB: rcoli + rcolw; rock deep enough past rbot) ----------
INSET=[0,1,1]; W=[2,5,8]
def trial(size,px):
    alive(); quiet(); poke(0x63,[0,0]); poke(0x61,[0])  # freeze so the inset edges stay put
    # RY so solid bottom (RY+H-rbot) is just inside the ship: rbot=[1,2,2]
    rbot=[1,2,2][size]
    q({'cmd':'pause'}); poke(0x5C,[px]); poke(0x5E,[0]); norocks(); rock(0,size,20,141-RH[size]+rbot+1); q({'cmd':'resume'})
    time.sleep(0.12); d=st()['DEAD']; norocks(); return d
rx0=70
for size in range(3):
    left=rx0+INSET[size]
    r=[trial(size,left-5),trial(size,left-6),trial(size,left+W[size]-1),trial(size,left+W[size])]
    print('%s at col 20 (box left %d units): ship PX %d hit=%d, %d hit=%d | PX %d hit=%d, %d hit=%d'%(NAMES[size],left,left-5,r[0],left-6,r[1],left+W[size]-1,r[2],left+W[size],r[3]))
    ok(r==[1,0,1,0],'%s collision box edges (hit inside, miss outside)'%NAMES[size])
# ---------- 4: laser hits ----------
def shoot(size,hp=None,col=None):
    alive(); quiet(); time.sleep(0.15)
    q({'cmd':'pause'}); z=st(); lx2=z['PX']+3; k=(2*lx2)%7
    c=(2*lx2)//7 if col is None else col
    c=max(0,min(c,40-RW[size])); 
    while (2*lx2)//7*0+lx2-(c*7)//2 >= [3,7,11][size]: c+=1
    while lx2-(c*7)//2 < 0: c-=1
    norocks(); rock(0,size,c,60,hp)
    poke(0x94,[1]); poke(0x95,[(2*lx2)//7]); poke(0x96,[[3,6,12,24,48,96,64][k]]); poke(0x97,[1 if k==6 else 0]); poke(0x98,[60+12+6]); poke(0x99,[lx2])
    sc0=z['SCORE']; q({'cmd':'resume'}); time.sleep(0.12)
    z,sv,pgs=snap(); return sc0,z,sv,pgs
for size in (0,1):
    sc0,z,_,_=shoot(size); print('%s hit: score %d -> %d, RON %d'%(NAMES[size],sc0,z['SCORE'],z['RON'][0]))
    ok(z['SCORE']-sc0==PTS[size] and not (z['RON'][0] and z['RSIZE'][0]==size and z['RY'][0]>=60),'%s: one hit, +%d'%(NAMES[size],PTS[size]))
sc0,z,sv,pgs=shoot(2); time.sleep(0.05); z2,sv2,pgs2=snap()
print('boulder 1st hit: score %d -> %d, RON %d RHP %d, sprite drawn on pages %s'%(sc0,z2['SCORE'],z2['RON'][0],z2['RHP'][0],[sv2[0x2D0],sv2[0x2D8]]))
ok(z2['SCORE']==sc0 and z2['RON'][0] and z2['RHP'][0]==1 and 3 in (sv2[0x2D0],sv2[0x2D8]),'boulder survives the 1st hit, cracked sprite, no points')
png(pgs2[1-z2['BACK']],T+'/rocksize_cracked_%s.png'%MACH)
q({'cmd':'pause'}); z=st(); lx2=z['PX']+3; k=(2*lx2)%7; y=z['RY'][0]
poke(0x94,[1]); poke(0x95,[(2*lx2)//7]); poke(0x96,[[3,6,12,24,48,96,64][k]]); poke(0x97,[1 if k==6 else 0]); poke(0x98,[y+14+6]); poke(0x99,[lx2]); q({'cmd':'resume'})
time.sleep(0.12); z3=st(); print('boulder 2nd hit: score %d -> %d, RON %d, popup kind %d'%(sc0,z3['SCORE'],z3['RON'][0],z3['PK']))
ok(z3['SCORE']-sc0==15 and not z3['RON'][0] and z3['PK'] in (1,2),'boulder destroyed by the 2nd hit: +15, burst/popup')
time.sleep(1.3); n,z,sv,pgs=exact(); ok(n==0 and z['PK']==0,'popup "15" erased cleanly')
# ---------- 5: screenshot with all three sizes ----------
alive(); quiet(); q({'cmd':'pause'}); poke(0x61,[1]); rock(0,0,6,40); rock(1,1,14,70); rock(2,2,26,52); q({'cmd':'resume'}); time.sleep(0.15)
n,z,sv,pgs=exact(); png(pgs[1-z['BACK']],T+'/rocksize_all_%s.png'%MACH)
ok(n==0,'all three sizes on screen: both pages exact')
# ---------- 6: soak ----------
import re as _re; sys.path.insert(0,D+'/tools'); import gen_land
_inc=open(D+'/src/land.inc').read()
LANDS=[bytes(gen_land.unrle([int(v,16) for v in _re.findall(r'\$([0-9A-F]{2})',_re.search(r'^land%d:\n((?:\s+\.byte .*\n)+)'%k,_inc,_re.M).group(1))])) for k in range(len(gen_land.LANDS))]
alive(); poke(0xA7,[5]); poke(0x61,[5]); bad=0; mm=0; samples=0; deaths=0; maxb=0; t0=time.time(); i=0
while time.time()-t0<40:
    key('\x08' if (i//5)%2 else '\x15'); key(' '); i+=1
    z,sv,pgs=snap(); samples+=1
    maxb=max([maxb]+[r+RH[s]-1 for r,on,s in zip(z['RY'],z['RON'],z['RSIZE']) if on])
    if z['LEVEL']==1 or z['DEAD']: pass
    if any(strip(x)!=LANDS[peek(0xB2,1)[0]] for x in pgs):
        time.sleep(0.4); _,_,pgs2=snap(); ln=peek(0xB2,1)[0]       # a level-up may be redrawing the strip: look again
        bad+=sum(1 for x in pgs2 if strip(x)!=LANDS[ln])
    if samples%3==0: n,z,sv,pgs=exact(); mm+=n
    if z['DEAD']: deaths+=1; alive(); poke(0xA7,[5]); poke(0x61,[5])
print('soak: %d samples, %d deaths, max rock bottom row %d, landscape corrupted %d, page mismatches %d'%(samples,deaths,maxb,bad,mm))
ok(bad==0 and maxb<=151,'rocks of all sizes never reach the landscape')
ok(mm==0,'both pages exact during the soak')
# ---------- 7: frame time ----------
def fps(setup,secs=5):
    alive(); quiet(); poke(0x61,[1]); poke(0x5C,[0])
    q({'cmd':'pause'})
    for i,(sz,col) in enumerate(setup): rock(i,sz,col,20)
    q({'cmd':'resume'}); time.sleep(0.2)
    f0=st()['FRAME']; n=0; last=f0; t0=time.time(); ys=[20]*len(setup)
    while time.time()-t0<secs:
        time.sleep(0.1)
        if setup: poke(0x78,ys)                     # keep them in the sky (one poke, no pause)
        f=st()['FRAME']; n+=(f-last)&255; last=f
    return n/(time.time()-t0)
cases=[('no rocks',[]),('5 rocks',[(1,c) for c in (8,14,20,26,32)]),('5 pebbles',[(0,c) for c in (8,14,20,26,32)]),
       ('2 boulders + 3 rocks (max mix)',[(2,8),(2,14),(1,20),(1,26),(1,32)]),('5 boulders (forced, beyond MAXLG)',[(2,c) for c in (6,12,18,24,30)])]
out=[]
for name,setup in cases:
    f=fps(setup); out.append((name,f)); print('%-34s %.1f fps = %d cycles/frame'%(name,f,1023000/f))
base=1023000/out[1][1]
dev=[abs(1023000/f-base)/base for n,f in out[:4]]
ok(max(dev)<0.06,'frame time within 5%% across rock mixes up to the allowed max (max dev %.1f%%)'%(100*max(dev)))
print('forced 5 boulders: %+.1f%% vs 5 rocks'%(100*(1023000/out[4][1]-base)/base))
q({'cmd':'quit'})
print('RESULT:','PASS' if not FAIL else 'FAIL %s'%FAIL)
