#!/usr/bin/env python3
"""Boss meteor test: boot disk/rockfall.dsk in bobbin-ai and check
 - every 3rd level a boss is due: normal spawns stop, the boss enters in slot 0 once the field is clear;
 - it drifts and sheds pebbles, never more than 2 shed rocks (no table overrun);
 - 7 laser hits destroy it: +100, burst popup, shield/cool capsule, speed +1, normal spawns resume;
 - reaching the ship row kills the ship (or costs the shield);
 - pages stay exact with the boss on screen.  Usage: boss_test.py [enhanced|plus]"""
import subprocess,time,os,sys,json,pty,re,shutil
sys.path.insert(0,'/workspace/apple2/tests'); from sock import send
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import flymodel
MACH=sys.argv[1] if len(sys.argv)>1 else 'enhanced'
D=T+'/..'; SOCK='/tmp/rfboss_'+MACH+'.sock'
if os.path.exists(SOCK): os.remove(SOCK)
DSK='/tmp/rf_boss_%s.dsk'%MACH; shutil.copy(D+'/disk/rockfall.dsk',DSK)
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
RSPR=[peek(lab(n),RW[i]*RH[i]) for i,n in enumerate(['pebble','rock','boulder','boulder_cracked','boss_spr'])]
key(' '); time.sleep(1.5)
B=lambda:peek(0xD5,3)
def bst(): z=st(); b=B(); z.update(BCNT=b[0],BOSS=b[1],BTIM=b[2],CON=peek(0xEB,1)[0],CTYPE=peek(0xEE,1)[0],PUT=peek(0xE8,1)[0]); return z
def bolt(y,lx2):
    k=(2*lx2)%7
    poke(0x94,[1]); poke(0x95,[(2*lx2)//7]); poke(0x96,[[3,6,12,24,48,96,64][k]]); poke(0x97,[1 if k==6 else 0]); poke(0x98,[y]); poke(0x99,[lx2])
def summon():
    alive(); quiet(); time.sleep(0.15)
    q({'cmd':'pause'}); poke(0xD6,[0]); poke(0xD5,[2]); poke(0x62,[14]); poke(0xA8,[2]); poke(0xE8,[200])   # shield on
    z=st(); c=0 if z['PX']>70 else 39; rock(0,0,c,145); lv=z['LEVEL']; q({'cmd':'resume'})
    return lv
lv=summon(); time.sleep(0.4); z=bst()
print('after level-up: LEVEL %02X BOSS %d BCNT %d RON %s'%(z['LEVEL'],z['BOSS'],z['BCNT'],z['RON']))
ok(z['LEVEL']!=lv and z['BOSS'] in (1,2) and z['BCNT']==0,'3rd level-up makes a boss due')
for t in range(40):
    z=bst()
    if z['BOSS']==2: break
    time.sleep(0.25)
ok(z['BOSS']==2 and z['RON'][0] and z['RSIZE'][0]==4 and z['RHP'][0]==7,'boss enters in slot 0 with 7 HP (RSIZE %d RHP %d)'%(z['RSIZE'][0],z['RHP'][0]))
# shed / no overrun; keep the shield topped up
mx=0; cols=set(); sizes=set(); maxshed=0
for t in range(40):
    poke(0xE8,[200]); z=bst()
    if z['BOSS']!=2: break
    sh=[i for i in range(1,5) if z['RON'][i]]; maxshed=max(maxshed,len(sh)); sizes|={z['RSIZE'][i] for i in sh}; cols.add(z['RCOL'][0])
    ok(z['RSIZE'][0]==4 and all(z['RSIZE'][i]!=4 for i in range(1,5)),'only slot 0 holds the boss') if t%10==0 else None
    time.sleep(0.12)
print('shed max %d sizes %s boss cols %s RY %d'%(maxshed,sizes,sorted(cols),z['RY'][0]))
ok(1<=maxshed<=2 and sizes<={0},'boss sheds pebbles, at most 2 at once')
ok(len(cols)>1,'boss drifts sideways')
q({'cmd':'pause'}); poke(0x78,[20]); q({'cmd':'resume'})
n,z,sv,pgs=exact(); ok(n==0,'pages exact with the boss on screen'); png(pgs[1-z['BACK']],T+'/boss_%s.png'%MACH)
# HP drain
q({'cmd':'pause'}); poke(0x78,[20]); poke(0xA4,[0]); poke(0xA5,[0]); poke(0xEB,[0]); poke(0xBA,[0]); z=bst(); sc0=z['SCORE']; sp0=z['SPEED']; q({'cmd':'resume'})
hp=[]
for h in range(7):
    q({'cmd':'pause'}); poke(0xE8,[200]); z=bst(); c=z['RCOL'][0]; bolt(z['RY'][0]+12,(c*7)//2+8); q({'cmd':'resume'}); time.sleep(0.15)
    z=bst(); hp.append(z['RHP'][0] if z['BOSS']==2 else 0)
print('HP after each hit',hp,'score %d -> %d speed %d -> %d CON %d CTYPE %d PK %d'%(sc0,z['SCORE'],sp0,z['SPEED'],z['CON'],z['CTYPE'],z['PK']))
ok(hp==[6,5,4,3,2,1,0],'7 hits drain the boss one at a time')
ok(z['BOSS']==0 and not z['RON'][0],'boss destroyed')
ok(z['SCORE']-sc0>=100,'kill gives +100')
ok(z['CON']==1 and z['CTYPE'] in (0,1),'guaranteed shield/cool capsule')
ok(z['SPEED']==min(5,sp0+1),'speed up a notch')
time.sleep(2); z=bst(); ok(any(z['RON']) and 4 not in [z['RSIZE'][i] for i in range(5) if z['RON'][i]],'normal rocks resume')
# fail path: shield absorbs
def atrow(put):
    summon(); time.sleep(0.4)
    for t in range(40):
        poke(0xE8,[200]); z=bst()
        if z['BOSS']==2: break
        time.sleep(0.25)
    q({'cmd':'pause'}); poke(0x88,[1,0,0,0,0]); poke(0x78,[112]); poke(0xE8,[put]); poke(0xD7,[200]); q({'cmd':'resume'}); time.sleep(0.6); return bst()
z=atrow(150); print('shielded: DEAD %d BOSS %d PUT %d'%(z['DEAD'],z['BOSS'],z['PUT']))
ok(not z['DEAD'] and z['BOSS']==0 and z['PUT']==0,'boss at the ship row breaks the shield')
z=atrow(0); print('unshielded: DEAD %d BOSS %d'%(z['DEAD'],z['BOSS']))
ok(z['DEAD'] and z['BOSS']==0,'boss at the ship row is a ship hit')
p.kill(); print('ALL PASS' if not FAIL else 'FAILURES: %s'%FAIL); sys.exit(1 if FAIL else 0)
