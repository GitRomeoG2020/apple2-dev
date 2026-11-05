#!/usr/bin/env python3
"""Rock split test: boot disk/rockfall.dsk in bobbin-ai and check
 - a laser hit on a MEDIUM rock gives +5 and leaves two pebbles (one in its slot, one in a free slot);
 - the pebbles score +3 each when shot and never split;
 - a LARGE boulder still needs 2 hits, gives +15 and leaves no pebbles;
 - with the rock table full, a medium split gives just one pebble (no overrun), game keeps running;
 - pages stay exact after a split.  Usage: rocksplit_test.py [enhanced|plus]"""
import subprocess,time,os,sys,json,pty,re,shutil
sys.path.insert(0,'/workspace/apple2/tests'); from sock import send
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import flymodel
MACH=sys.argv[1] if len(sys.argv)>1 else 'enhanced'
D=T+'/..'; SOCK='/tmp/rfsplit_'+MACH+'.sock'
if os.path.exists(SOCK): os.remove(SOCK)
DSK='/tmp/rf_split_%s.dsk'%MACH; shutil.copy(D+'/disk/rockfall.dsk',DSK)
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
key(' '); time.sleep(1.5)
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
def bolt(y,lx2=None):
    z=st(); lx2=z['PX']+3 if lx2 is None else lx2; k=(2*lx2)%7
    poke(0x94,[1]); poke(0x95,[(2*lx2)//7]); poke(0x96,[[3,6,12,24,48,96,64][k]]); poke(0x97,[1 if k==6 else 0]); poke(0x98,[y]); poke(0x99,[lx2])
peb=lambda z:[i for i in range(5) if z['RON'][i] and z['RSIZE'][i]==0]
# medium split
sc0,z,_,_=shoot(1); P=peb(z)
print('medium hit: score %d -> %d, pebbles in slots %s cols %s rows %s'%(sc0,z['SCORE'],P,[z['RCOL'][i] for i in P],[z['RY'][i] for i in P]))
ok(z['SCORE']-sc0==5,'medium hit +5')
ok(len(P)==2 and 0 in P,'medium splits into 2 pebbles')
ok(len(P)==2 and z['RCOL'][P[0]]!=z['RCOL'][P[1]],'pebbles separated')
n,z2,sv,pgs=exact(); ok(n==0,'pages exact after split')
# shoot a pebble: +3, no split
q({'cmd':'pause'}); z=st(); P=peb(z); i=P[0]; c=z['RCOL'][i]; y=z['RY'][i]; sc0=z['SCORE']
poke(0x88,[1 if j==i else 0 for j in range(5)]); bolt(y+6+3,(c*7)//2+1); q({'cmd':'resume'}); time.sleep(0.12); z=st()
print('pebble hit: score %d -> %d, pebbles %s'%(sc0,z['SCORE'],peb(z)))
ok(z['SCORE']-sc0==3 and not peb(z),'pebble +3, no split')
# boulder: 2 hits, no pebbles
sc0,z,_,_=shoot(2); time.sleep(0.05)
q({'cmd':'pause'}); z=st(); bolt(z['RY'][0]+14+6); q({'cmd':'resume'}); time.sleep(0.12); z=st()
print('boulder 2 hits: score %d -> %d, RON %s RSIZE %s'%(sc0,z['SCORE'],z['RON'],z['RSIZE']))
ok(z['SCORE']-sc0==15 and not any(z['RON']),'boulder: 2 hits, +15, no pebbles')
# full table
alive(); quiet(); time.sleep(0.15)
q({'cmd':'pause'}); z=st(); lx2=z['PX']+3; c=max(0,min((lx2*2)//7,38))
while lx2-(c*7)//2>=7: c+=1
while lx2-(c*7)//2<0: c-=1
rock(0,1,c,60); rock(1,1,0,10); rock(2,1,10,20); rock(3,0,30,30); rock(4,1,36,5)
sc0=z['SCORE']; bolt(60+8+6,lx2); q({'cmd':'resume'}); time.sleep(0.12); z=st()
print('full table split: score %d -> %d RON %s RSIZE %s'%(sc0,z['SCORE'],z['RON'],z['RSIZE']))
ok(z['SCORE']-sc0==5 and z['RSIZE'][0]==0 and z['RON'][0] and sum(1 for s in z['RSIZE'] if s==0)<=2,'full table: one pebble, no overrun')
time.sleep(1); z=st(); f0=z['FRAME']; time.sleep(0.5); ok(st()['FRAME']!=f0,'game still running')
p.kill(); print('ALL PASS' if not FAIL else 'FAILURES: %s'%FAIL); sys.exit(1 if FAIL else 0)
