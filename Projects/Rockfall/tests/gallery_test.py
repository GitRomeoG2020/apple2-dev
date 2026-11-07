#!/usr/bin/env python3
"""Hidden gallery integration test on a disposable disk. Usage: gallery_test.py enhanced|plus.
Checks both title entrances, eight exact RLE scenes on both pages, navigation,
paused attract timer, restored art, gameplay state/highscore/disk isolation and mute.
"""
import subprocess,time,os,sys,json,pty,re,shutil
sys.path.insert(0,'/workspace/apple2/tests'); from sock import send
MACH=sys.argv[1] if len(sys.argv)>1 else 'enhanced'
D=os.path.dirname(os.path.abspath(__file__))+'/..'; SOCK='/tmp/rfgallery_'+MACH+'.sock'
if os.path.exists(SOCK): os.remove(SOCK)
DSK='/tmp/rf_gallery_%s.dsk'%MACH; shutil.copy(D+'/disk/rockfall.dsk',DSK)
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

FAIL=[]
def ok(c,msg):
    print(('PASS ' if c else 'FAIL ')+msg,flush=True)
    if not c: FAIL.append(msg)
def wait(f,t=5):
    end=time.monotonic()+t
    while time.monotonic()<end:
        if f(): return True
        time.sleep(.03)
    return False
def strip(page):
    mem=peek(page,8192)
    return b''.join(mem[A(y):A(y)+40] for y in range(152,184))
def scene(n): return peek(0xB2,1)==bytes([n]) and all(strip(pg)==LAND[n] for pg in (0x2000,0x4000))
def timer(n):
    q({'cmd':'pause'}); poke(0xC3,[n&255,n>>8]); q({'cmd':'resume'})
def state(): return [peek(a,n) for a,n in ((0x4E,1),(0x63,4),(0x6B,1),(0x88,5),(0xA7,1),(0x1B00,44))]
original=open(DSK,'rb').read()
try:
    ok(wait(lambda:peek(0xCE,1)==b'\0' and peek(0x0E,1)==b'\1',25),'boot to title art with music')
    timer(1200)
    poke(0xB2,[6]); before=state()
    key('G'); ok(wait(lambda:scene(0)),'G from title art opens Mountains on both pages')
    ok(peek(0x0E,1)==b'\1','gallery keeps enabled music')
    tc=peek(0xC3,2); time.sleep(.25)
    ok(peek(0xC3,2)==tc,'title/demo countdown paused')
    key('GG'); time.sleep(.2)
    ok(scene(0) and state()==before,'repeated G cannot start a game or change gameplay state')
    for n in range(1,8):
        key('D' if n%2 else '\x15')
        ok(wait(lambda n=n:scene(n)),NAMES[n]+' exact strip, both pages')
    # Capture the actual HGR page through the emulator; render its artifact colors.
    from PIL import Image
    mem=peek(0x2000,8192); im=Image.new('RGB',(280,192)); px=im.load()
    for y in range(192):
        bits=[]; hb=[]
        for b in mem[A(y):A(y)+40]:
            bits += [(b>>i)&1 for i in range(7)]; hb += [b>>7]*7
        for x in range(280):
            if bits[x]:
                px[x,y]=(255,255,255) if (x and bits[x-1]) or (x<279 and bits[x+1]) else ((20,207,253) if x%2==0 else (255,106,60)) if hb[x] else ((255,68,253) if x%2==0 else (20,245,60))
    path=os.path.abspath(D+'/screenshots/gallery_'+MACH+'.png')
    im.resize((840,576),Image.Resampling.NEAREST).save(path); print('SCREENSHOT '+path,flush=True)
    key(' '); ok(wait(lambda:scene(0)),'space wraps Harbor to Mountains')
    key('\x08'); ok(wait(lambda:scene(7)),'left wraps Mountains to Harbor')
    key('A'); ok(wait(lambda:scene(6)),'A selects previous landscape')
    ok(state()==before,'score, lives, rocks, level, demo and highscore table unchanged')
    key('\x1b'); ok(wait(lambda:peek(0xB2,1)==b'\6' and strip(0x2000)!=LAND[6]),'Escape restores title art and borrowed landscape state')
    timer(1200); key('M'); ok(peek(0x0D,2)==b'\1\0','mute preference set on title')
    timer(1); ok(wait(lambda:peek(0xCE,1)==b'\1'),'advance to high-score title view')
    timer(1200); key('g' if MACH=='enhanced' else 'G')
    ok(wait(lambda:scene(0)),'G from high scores opens gallery')
    ok(peek(0x0D,2)==b'\1\0','gallery respects session mute')
    key('\x1b'); ok(wait(lambda:peek(0xCE,1)==b'\0' and strip(0x2000)!=LAND[0]),'Escape from muted gallery restores title art')
    ok(peek(0x0D,2)==b'\1\0' and state()==before,'return preserves mute and gameplay/highscores')
    timer(1200); key('M'); key(' ')
    ok(wait(lambda:peek(0x4E,1)==b'\3' and peek(0x0E,1)==b'\0'),'normal title key still starts real game')
finally:
    p.terminate(); p.wait(timeout=5); os.close(m)
ok(open(DSK,'rb').read()==original,'gallery and ordinary start never write highscore disk')
print('RESULT: '+('FAIL' if FAIL else 'PASS'),flush=True)
sys.exit(bool(FAIL))
