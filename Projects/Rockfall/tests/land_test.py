#!/usr/bin/env python3
"""Landscape test: boot disk/rockfall.dsk in bobbin-ai and check the static landscape strip
(rows LANDY..LANDY+31): level 1 shows landscape 0 on both HGR pages; each forced level-up swaps in
landscape (LEVEL-1) mod NLAND on both pages (cycling); a soak with fast rocks, movement and laser fire
never changes a landscape byte; a new game resets to landscape 0.  Saves in-game PNGs per landscape.
Usage: land_test.py [enhanced|plus]"""
import subprocess,time,os,sys,json,pty,re,shutil
sys.path.insert(0,'/workspace/apple2/tests'); from sock import send
MACH=sys.argv[1] if len(sys.argv)>1 else 'enhanced'
D=os.path.dirname(os.path.abspath(__file__))+'/..'; SOCK='/tmp/rfland_'+MACH+'.sock'
if os.path.exists(SOCK): os.remove(SOCK)
DSK='/tmp/rf_land_%s.dsk'%MACH; shutil.copy(D+'/disk/rockfall.dsk',DSK)
sys.path.insert(0,D+'/tools'); import gen_land
LANDY=152; H=gen_land.H
# expected strip bytes, decoded from the generated src/land.inc
inc=open(D+'/src/land.inc').read(); LAND=[]; NAMES=[n for n,_ in gen_land.LANDS]
for k in range(len(NAMES)):
    blk=re.search(r'^land%d:\n((?:\s+\.byte .*\n)+)'%k,inc,re.M).group(1)
    LAND.append(bytes(gen_land.unrle([int(v,16) for v in re.findall(r'\$([0-9A-F]{2})',blk)])))
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
def st():
    z=peek(0x50,0x70); return dict(SPEED=z[0x11],DEAD=z[0x17],LEVEL=z[0x57],SPDUPS=z[0x58],LVLUP=z[0x59],BACK=z[0x42],LANDN=z[0x62],RY=list(z[0x28:0x2D]),RON=list(z[0x38:0x3D]))
strip=lambda mem:b''.join(mem[A(y):A(y)+40] for y in range(LANDY,LANDY+H))
FAIL=[]
def ok(c,msg): print(('PASS ' if c else 'FAIL ')+msg); c or FAIL.append(msg)
def which(sb): return next((k for k,l in enumerate(LAND) if l==sb),None)
def snap():
    q({'cmd':'pause'})
    try: z=st(); pg=[peek(0x2000,0x2000),peek(0x4000,0x2000)]
    finally: q({'cmd':'resume'})
    return z,pg
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
    for t in range(25):
        if not st()['DEAD']: poke(0x4E,[1]); return   # legacy one-ship play (lives: lives_test)
        time.sleep(3 if t==0 else 0.6); key('A'); time.sleep(0.5)
def norocks(): poke(0x88,[0]*5); poke(0x80,[0xFF]*5)
bcd=lambda v:(v>>4)*10+(v&15)
time.sleep(6); key(' '); time.sleep(1.5)
z,pg=snap(); print('new game:',z)
ok(z['LEVEL']==1 and z['LANDN']==0 and which(strip(pg[0]))==0 and which(strip(pg[1]))==0,'level 1 shows landscape 0 (%s) on both pages'%NAMES[0])
png(pg[1-z['BACK']],D+'/tests/land_0_%s_%s.png'%(NAMES[0].lower(),MACH))
# --- force level-ups: levels 2..NLAND+2 -> landscapes 1..NLAND-1,0,1 ---
for n in range(2,len(LAND)+3):
    for attempt in range(6):
        alive(); norocks(); z0=st()
        if z0['LEVEL']!=n-1:     # died earlier -> new game is level 1: jump the counter
            poke(0xA7,[((n-1)//10)<<4|(n-1)%10]); poke(0xB2,[(n-2)%len(LAND)])
        poke(0xA8,[2]); poke(0x62,[14])
        poke(0x88,[1]); poke(0x78,[143]); poke(0x70,[0])   # rock 0 lands now -> the dodge that levels up
        t0=time.time()
        while time.time()-t0<3 and not st()['LVLUP']: time.sleep(0.005)
        while time.time()-t0<6 and st()['LVLUP']: time.sleep(0.02)
        norocks(); time.sleep(0.15)
        z,pg=snap()
        if not z['DEAD'] and bcd(z['LEVEL'])==n: break
        print('  (retry level %d: %s)'%(n,z))
    want=(n-1)%len(LAND); got=[which(strip(x)) for x in pg]
    print('level %d: LANDN=%d strips page1=%s page2=%s'%(n,z['LANDN'],got[0],got[1]))
    ok(bcd(z['LEVEL'])==n and z['LANDN']==want and got==[want,want],'level %d shows landscape %d (%s) on both pages'%(n,want,NAMES[want]))
    if n<=len(LAND): png(pg[1-z['BACK']],D+'/tests/land_%d_%s_%s.png'%(want,NAMES[want].lower(),MACH))
# --- soak: fast rocks, movement and fire; landscape bytes never change ---
alive(); poke(0x61,[5]); bad=0; samples=0; deaths=0; maxry=0; t0=time.time(); i=0
while time.time()-t0<40:
    key('\x08' if (i//5)%2 else '\x15'); key(' '); i+=1; time.sleep(0.03)
    z,pg=snap(); samples+=1
    sz=peek(0xD0,5); maxry=max([maxry]+[r+[6,8,14][k]-1 for r,on,k in zip(z['RY'],z['RON'],sz) if on])   # rock bottom row
    if any(strip(x)!=LAND[z['LANDN']] for x in pg):
        time.sleep(0.4); z,pg=snap()      # a level-up may be redrawing the strip right now: look again
        for x in pg:
            if strip(x)!=LAND[z['LANDN']]: bad+=1
    if z['DEAD']: deaths+=1; alive(); poke(0x61,[5])
print('soak: %d samples, %d deaths, max rock bottom row %d, corrupted strips %d'%(samples,deaths,maxry,bad))
ok(bad==0 and samples>50,'rocks/stars/laser never touch the landscape during a 40 s soak (SPEED 5)')
ok(maxry<=151,'rocks never drawn below row 151 (max bottom row %d)'%maxry)
# --- new game resets ---
alive(); poke(0xA7,[3]); poke(0xB2,[2]); time.sleep(0.1); poke(0x67,[1]); time.sleep(1); alive(); time.sleep(1)
z,pg=snap(); print('after game over + new game:',z)
ok(z['LEVEL']==1 and z['LANDN']==0 and [which(strip(x)) for x in pg]==[0,0],'new game resets to landscape 0 on both pages')
q({'cmd':'quit'})
print('RESULT:','PASS' if not FAIL else 'FAIL %s'%FAIL)
