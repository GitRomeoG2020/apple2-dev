#!/usr/bin/env python3
"""Bonus flyer test (comet / satellite): boot disk/rockfall.dsk in bobbin-ai and check
 - forcing the spawn timer spawns a flyer that crosses the sky and despawns off the far edge,
   and the next-spawn timer is re-armed to FTMIN..FTMIN+510 frames;
 - all four sprites/directions (comet & satellite, left->right and right->left) cross and leave;
 - mid-flight both pages match the model (stars+ship+flyer from the per-page copies), and the
   sky rows are clean (stars only) once it is gone: no XOR residue;
 - a laser hit gives 50 (comet) / 100 (satellite), runs the bonus sound, shows burst + points,
   and the popup is erased afterwards;
 - landscape strip and HUD never corrupted;
 - cycles per frame (render and whole loop) with and without a flyer.
Saves PNGs of a comet, a satellite and the hit popup.  Usage: flyer_test.py [enhanced|plus]"""
import subprocess,time,os,sys,json,pty,re,shutil
sys.path.insert(0,'/workspace/apple2/tests'); from sock import send
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import flymodel
MACH=sys.argv[1] if len(sys.argv)>1 else 'enhanced'
D=T+'/..'; SOCK='/tmp/rffly_'+MACH+'.sock'
if os.path.exists(SOCK): os.remove(SOCK)
DSK='/tmp/rf_fly_%s.dsk'%MACH; shutil.copy(D+'/disk/rockfall.dsk',DSK)
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
key=lambda c:(q({'cmd':'keys','text':c}),time.sleep(0.05))
A=lambda y:(y&7)*0x400+((y>>3)&7)*0x80+(y>>6)*0x28
L=open(D+'/build/rockfall.lst').read(); M=open(D+'/build/rockfall.map').read()
ROD=int(re.search(r'^RODATA\s+([0-9A-F]+)',M,re.M).group(1),16)
def code(n): return 0x6000+int(re.search(r'^([0-9A-F]+)r 1 .*?\b'+n+r':',L,re.M).group(1),16)
lab=lambda n:ROD+int(re.search(r'^([0-9A-F]+)r 2 .*?\b'+n+':',L,re.M).group(1),16)
A_BONUS,A_RENDER,A_FLIP,A_LOOP=code('bonus'),code('render'),code('flip'),code('loop')
A_AFTERBONUS=0x6000+int(re.search(r'^([0-9A-F]+)r 1 +20 rr rr +jsr bonus',L,re.M).group(1),16)+3
def st():
    z=peek(0x50,0x80)
    g=lambda a:z[a-0x50]
    return dict(DEAD=g(0x67),SCORE='%02X%02X'%(g(0x64),g(0x63)),BACK=g(0x92),FRAME=g(0x90),LON=g(0x94),LY=g(0x98),PX=g(0x5C),
        FON=g(0xB3),FX=g(0xB4),FY=g(0xB5),FDIR=g(0xB6),FTYPE=g(0xB7),FT=g(0xB8)|g(0xB9)<<8,PK=g(0xBA),PT=g(0xBE),FS=g(0xC1))
FAIL=[]
def ok(c,msg): print(('PASS ' if c else 'FAIL ')+msg); c or FAIL.append(msg)
def norocks(): poke(0x88,[0]*5); poke(0x80,[0xFF]*5)
def quiet(): norocks(); poke(0xB8,[0xFF,0x7F])    # no rocks, no natural flyer for ~13 min
def alive():
    for t in range(25):
        if not st()['DEAD']: poke(0x4E,[1]); return   # legacy one-ship play (lives: lives_test)
        time.sleep(3 if t==0 else 0.6); key('A'); time.sleep(0.5)
def snap():
    q({'cmd':'pause'})
    try: z=st(); sv=peek(0x1800,0x300); pg=[peek(0x2000,0x2000),peek(0x4000,0x2000)]
    finally: q({'cmd':'resume'})
    return z,sv,pg
def model(pg,sv):
    e=[[0]*40 for _ in range(152)]
    if not sv[0x2BC+pg]: return e
    px=sv[0x2B0+pg]; d=SHIP[(px*2)%7]
    for r in range(8 if not flymodel.shield(sv,pg) else 0):
        for b in range(3): e[140+r][(px*2)//7+b]^=d[r*3+b]
    for i in range(36):
        j=pg*64+i; e[sv[0x200+j]][sv[0x100+j]]^=sv[0x180+j]
    return flymodel.apply(e,sv,pg,FONT)
def mism(sv,pgs,y0=0,y1=152):
    n=0
    for pg in (0,1):
        e=model(pg,sv)
        for y in range(y0,y1): n+=sum(1 for b in range(40) if pgs[pg][A(y)+b]!=e[y][b])
    return n
def matches(tries=40,y0=0,y1=152):
    for t in range(tries):
        z,sv,pgs=snap()
        if sv[0x2B2] or sv[0x2B3]: time.sleep(0.03); continue      # bolt on screen: not modelled here
        n=mism(sv,pgs,y0,y1)
        if n==0: return 0,z,pgs
        time.sleep(0.023)
    return n,z,pgs
strip=lambda mem:b''.join(mem[A(y):A(y)+40] for y in range(152,184))
hud=lambda mem:b''.join(mem[A(y):A(y)+30] for y in range(186,191))     # labels + numbers (bar excluded)
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
time.sleep(6); FONT=peek(lab('font'),24*5); SL,SH=peek(lab('ship_shift_lo'),7),peek(lab('ship_shift_hi'),7); SHIP={k:peek(SL[k]|SH[k]<<8,24) for k in range(7)}
key(' '); time.sleep(1.5); quiet(); time.sleep(0.5)
z,sv,pgs=snap(); LAND0=[strip(x) for x in pgs]; HUD0=[hud(x) for x in pgs]
ok(LAND0[0]==LAND0[1] and HUD0[0]==HUD0[1],'baseline: landscape and HUD identical on both pages')
def integrity(pgs,tag):
    good=all(strip(x)==LAND0[0] for x in pgs) and all(hud(x)==HUD0[0] for x in pgs)
    if not good: print('  integrity broken at',tag)
    return good
# ---------- 1: forced timer -> natural spawn, crossing, despawn, timer re-armed ----------
poke(0xB8,[1,0]); t0=time.time(); tr=[]; intact=True
while time.time()-t0<5:
    norocks(); z,sv,pgs=snap(); intact&=integrity(pgs,'natural')
    if z['FON']: tr.append(z['FX'])
    elif tr: break
    time.sleep(0.02)
z=st(); d=[b-a for a,b in zip(tr,tr[1:])]
print('natural spawn: FX samples %d first %s last %s, dir %d type %d, crossing %.2fs, next timer %d frames'%(len(tr),tr[:3],tr[-3:],z['FDIR'],z['FTYPE'],time.time()-t0,z['FT']))
mono=all(x>0 for x in d) if z['FDIR']==0 else all(x<0 for x in d)
ok(len(tr)>10 and mono and not z['FON'],'forced timer spawns a flyer that crosses and despawns')
ok(400<=z['FT']<=910,'next flyer timer re-armed to 400..910 frames (~10-23 s)')
ok(intact,'landscape + HUD untouched during the crossing')
# ---------- 2: every type x direction; model check mid-flight; clean sky after ----------
shots={}
for ftype in (0,1):
    for fdir in (0,1):
        alive(); quiet(); time.sleep(0.1)
        q({'cmd':'pause'}); poke(0xB4,[0 if fdir==0 else 154]); poke(0xB5,[20]); poke(0xB6,[fdir]); poke(0xB7,[ftype]); poke(0xB3,[1]); q({'cmd':'resume'})
        t0=time.time(); xs=[]; mid=None; intact=True; fss=set()
        while time.time()-t0<5:
            norocks(); z=st()
            if not z['FON']: break
            xs.append(z['FX']); fss.add(z['FS'])
            if mid is None and 60<=z['FX']<=94:
                n,zz,pgs=matches(); mid=n; intact&=integrity(pgs,'mid')
                nm='comet' if ftype==0 else 'satellite'
                if (nm,fdir) not in shots: png(pgs[1-zz['BACK']],T+'/flyer_%s_%s_%s.png'%(nm,'right' if fdir==0 else 'left',MACH)); shots[(nm,fdir)]=1
            time.sleep(0.02)
        dur=time.time()-t0; time.sleep(0.1)
        n2,z2,pgs=matches(); intact&=integrity(pgs,'after')
        clean=all(pgs[pg][A(y)+b]==model(pg,peek(0x1800,0x300))[y][b] or True for pg in (0,1) for y in range(0) for b in range(0))
        rng=(xs[0],xs[-1]) if xs else None
        desc='%s %s'%('comet' if ftype==0 else 'satellite','L->R' if fdir==0 else 'R->L')
        print('%s: FX %s in %.2fs (%d samples), sprites %s, mid-flight mismatches %s, after %d'%(desc,rng,dur,len(xs),sorted(fss),mid,n2))
        want_fs={0:{fdir},1:{2,3}}[ftype]
        ok(xs and not z2['FON'] and (xs[-1]>=140 if fdir==0 else xs[-1]<=14) and 1.0<dur<4,'%s crosses the whole sky and despawns'%desc)
        ok(fss<=want_fs and (ftype==0 or fss=={2,3}),'%s uses the right sprite%s'%(desc,' (beacon blinks)' if ftype else ''))
        ok(mid==0 and n2==0 and intact,'%s: both pages exact mid-flight, sky clean after, landscape/HUD intact'%desc)
# ---------- 3: hits ----------
def fire_at(ftype):
    """put a flyer just above a bolt that is in flight; returns (score before, after, bonus seen, cycles in bonus)"""
    alive(); quiet(); time.sleep(0.2)
    q({'cmd':'pause'}); z=st()
    lx2=z['PX']+3; k=(2*lx2)%7
    fx=lx2+14-5-2     # flyer centred over the bolt after its next 2-unit move
    bid=q({'cmd':'break_set','addr':A_BONUS}); bid2=q({'cmd':'break_set','addr':A_AFTERBONUS})
    poke(0xB4,[fx]); poke(0xB5,[30]); poke(0xB6,[0]); poke(0xB7,[ftype]); poke(0xB3,[1])
    poke(0x94,[1]); poke(0x95,[(2*lx2)//7]); poke(0x96,[[3,6,12,24,48,96,64][k]]); poke(0x97,[1 if k==6 else 0]); poke(0x98,[30+12+4]); poke(0x99,[lx2])
    sc0=z['SCORE']; q({'cmd':'resume'})
    c0=c1=None; t0=time.time()
    while time.time()-t0<3:
        c=q({'cmd':'cpu'})
        if c.get('paused') and c.get('break_hit',-1)>=0:
            if c0 is None:
                c0=time.time(); q({'cmd':'break_clear','addr':A_BONUS})
            else: c1=time.time(); break
            q({'cmd':'resume'})
        time.sleep(0.001)
    for b in (bid,bid2): q({'cmd':'break_clear','addr':A_BONUS}); q({'cmd':'break_clear','addr':A_AFTERBONUS})
    q({'cmd':'resume'}); time.sleep(0.02)
    z,sv,pgs=snap()
    return sc0,z,c0 is not None,int((c1-c0)*1023000) if c1 else None,pgs
for ftype,pts in ((0,50),(1,100)):
    nm='comet' if ftype==0 else 'satellite'
    sc0,z,seen,cyc,pgs=fire_at(ftype)
    gain=int(z['SCORE'])-int(sc0)
    print('%s hit: score %s -> %s (+%d), bonus sound entered %s, sound ran %s cycles of wall-clock time (~%.0f ms), FON %d PK %d PT %d'%(nm,sc0,z['SCORE'],gain,seen,cyc,(cyc or 0)/1023,z['FON'],z['PK'],z['PT']))
    ok(gain==pts and not z['FON'],'%s hit gives +%d and removes the flyer'%(nm,pts))
    ok(seen and cyc and 60000<cyc<300000,'bonus sound plays on a %s hit (~%.0f ms)'%(nm,(cyc or 0)/1023))
    ok(z['PK'] in (1,2),'hit popup shown (kind %d)'%z['PK'])
    time.sleep(0.15); z,sv,pgs=snap(); png(pgs[1-z['BACK']],T+'/flyer_hit_%s_%s.png'%(nm,MACH))
    n,_,_=matches(); print('  popup frame mismatches vs model:',n)
    time.sleep(1.3); n2,z2,pgs=matches()
    HUD0[:]=[hud(pgs[0])]*2   # score changed: new HUD baseline (both pages must agree)
    ok(n==0 and n2==0 and z2['PK']==0 and integrity(pgs,'hit'),'%s popup drawn exactly, then fully erased; landscape/HUD intact'%nm)
# ---------- 4: performance ----------
def fps(on,secs=6):
    """real-time (--no-turbo, 1.023 MHz) frame rate from the FRAME counter -> cycles per frame"""
    keepfly(on); f0=st()['FRAME']; n=0; t0=time.time(); last=f0; tl=t0
    while time.time()-t0<secs:
        time.sleep(0.1); keepfly(on); f=st()['FRAME']; n+=(f-last)&255; last=f
    return n/(time.time()-t0)
def keepfly(on):
    norocks()
    if on: poke(0xB4,[60]); poke(0xB6,[0]); poke(0xB3,[1]); poke(0xB5,[20])
    else: poke(0xB3,[0]); poke(0xB8,[0xFF,0x7F])
alive(); quiet(); poke(0xBE,[0]); poke(0xBA,[0]); res={}
for on in (0,1,0,1): res.setdefault(on,[]).append(fps(on))
for on in (0,1):
    f=sum(res[on])/len(res[on]); res[on]=f
    print('%s flyer: %.1f fps = %d cycles/frame'%('with' if on else 'no  ',f,1023000/f))
dr=1023000/res[1]-1023000/res[0]; print('flyer cost: %+d cycles/frame (%+.1f%%)'%(dr,100*dr/(1023000/res[0])))
ok(abs(dr)/(1023000/res[0])<0.05,'frame time with a flyer within 5%% of without (%+.1f%%)'%(100*dr/(1023000/res[0])))
q({'cmd':'quit'})
print('RESULT:','PASS' if not FAIL else 'FAIL %s'%FAIL)
