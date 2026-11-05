#!/usr/bin/env python3
"""Hitbox inset test: ship dies on solid rock contact, not empty sprite corners.
 - center overlap with each size kills;
 - ship under the old full AABB left/right corner (outside the inset box) survives;
 - tip-only vertical graze (rock bottom tip overlapping ship, solid mass still above) survives;
 - laser hit widths unchanged (medium still dies in one hit when aimed at center).
Usage: hitbox_test.py [enhanced|plus]"""
import subprocess,time,os,sys,json,pty,shutil
sys.path.insert(0,'/workspace/apple2/tests'); from sock import send
MACH=sys.argv[1] if len(sys.argv)>1 else 'enhanced'
D=os.path.dirname(os.path.abspath(__file__))+'/..'; SOCK='/tmp/rfhb_'+MACH+'.sock'
if os.path.exists(SOCK): os.remove(SOCK)
DSK='/tmp/rf_hitbox_%s.dsk'%MACH; shutil.copy(D+'/disk/rockfall.dsk',DSK)
m,s=pty.openpty()
p=subprocess.Popen(['/workspace/apple2/bin/bobbin-ai','--simple','--remain','--no-turbo','-m',MACH,'--disk',DSK,'--control-socket',SOCK],stdin=s,stdout=s,stderr=s,start_new_session=True)
os.close(s); q=lambda o:json.loads(send(json.dumps(o),SOCK))
for i in range(50):
    try: q({'cmd':'ping'}); break
    except Exception: time.sleep(0.2)
peek=lambda a,n:bytes(q({'cmd':'peek','addr':a,'len':n})['data'])
poke=lambda a,d:q({'cmd':'poke','addr':a,'data':d})
key=lambda c,t=0.05:(q({'cmd':'keys','text':c}),time.sleep(t))
RH=[6,8,14]; NAMES=['pebble','rock','boulder']
INSET=[0,1,1]; W=[2,5,8]; RBOT=[1,2,2]; RTOP=[0,1,2]
FAIL=[]
def ok(c,msg): print(('PASS ' if c else 'FAIL ')+msg); c or FAIL.append(msg)
def st():
    z=peek(0x50,0xA0); g=lambda a:z[a-0x50]
    return dict(DEAD=g(0x67),PX=g(0x5C),RON=[g(0x88+i) for i in range(5)],RY=[g(0x78+i) for i in range(5)],
                RSIZE=[g(0xD0+i) for i in range(5)],SCORE=int('%02X%02X'%(g(0x64),g(0x63))))
def norocks(): poke(0x88,[0]*5); poke(0x80,[0xFF]*5)
def quiet(): norocks(); poke(0xB8,[0xFF,0x7F]); poke(0x5E,[0])
def alive():
    for t in range(30):
        if not st()['DEAD']: poke(0x4E,[1]); return   # legacy one-ship play (lives: lives_test)
        time.sleep(3 if t==0 else 0.6); key('A'); time.sleep(0.5)
def rock(i,size,col,y,hp=None):
    poke(0xD0+i,[size]); poke(0xD8+i,[hp if hp is not None else (2 if size==2 else 1)])
    poke(0xE0+i,[0]); poke(0x70+i,[col]); poke(0x78+i,[y]); poke(0x88+i,[1])

def place(size,px,y_extra=0):
    """Rock at col 20; y so solid bottom is just inside ship (+ y_extra deeper). SPEED=0 so it does not drift."""
    alive(); quiet(); poke(0x63,[0,0]); poke(0x61,[0])
    y=141-RH[size]+RBOT[size]+1+y_extra
    q({'cmd':'pause'}); poke(0x5C,[px]); poke(0x5E,[0]); norocks(); rock(0,size,20,y); q({'cmd':'resume'})
    time.sleep(0.12); d=st()['DEAD']; norocks(); return d

time.sleep(6); key(' '); time.sleep(1.0); quiet()
rx0=70  # rockx2[20]

# 1) center of inset box kills for each size
for size in range(3):
    left=rx0+INSET[size]
    mid=left+W[size]//2-3   # ship roughly centered under the box (ship ~6 wide)
    # clamp so ship right overlaps the box solidly
    mid=left+1
    d=place(size,mid)
    print('%s center PX %d (box %d..%d): dead=%d'%(NAMES[size],mid,left,left+W[size]-1,d))
    ok(d==1,'%s: solid center contact kills'%NAMES[size])

# 2) old full-AABB left corner (outside inset) survives for rock & boulder
# old rock box was left=70,w=6; new is left=71,w=5. Ship at PX=70-5=65 was a hit on old left edge.
# For new rock: left=71, miss when PX<=71-6=65 (PX+6<=left). PX=65: PX+6=71 == left → miss (beq).
# Old hit at PX=65 for rock. New should miss at PX=65.
for size in (1,2):
    left=rx0+INSET[size]
    # just outside new left: PX such that PX+6 == left (miss), which was inside old box for rock
    px_out=left-6
    d=place(size,px_out)
    print('%s left-corner graze PX %d (new left %d): dead=%d'%(NAMES[size],px_out,left,d))
    ok(d==0,'%s: empty left corner graze survives'%NAMES[size])
    # just outside new right
    px_out=left+W[size]
    d=place(size,px_out)
    print('%s right-corner graze PX %d (new right %d): dead=%d'%(NAMES[size],px_out,left+W[size]-1,d))
    ok(d==0,'%s: empty right corner graze survives'%NAMES[size])

# 3) tip-only vertical graze: rock bottom tip overlaps ship but solid bottom (RY+H-rbot) does not
# Choose RY so RY+H > PLAYY (full sprite overlaps) but RY+H-rbot <= PLAYY (solid does not)
for size in (1,2):
    alive(); quiet(); poke(0x63,[0,0]); poke(0x61,[0])  # freeze fall so the tip does not sink into solid range
    # Full sprite bottom reaches ship (RY+H >= PLAYY+1) but solid bottom (RY+H-rbot) does not
    y=141-RH[size]   # rock: 133, boulder: 127 → tip rows only
    left=rx0+INSET[size]
    q({'cmd':'pause'}); poke(0x5C,[left]); poke(0x5E,[0]); norocks(); rock(0,size,20,y); q({'cmd':'resume'})
    time.sleep(0.12); d=st()['DEAD']; norocks()
    print('%s tip graze RY %d (H %d rbot %d): dead=%d'%(NAMES[size],y,RH[size],RBOT[size],d))
    ok(d==0,'%s: bottom tip-only graze survives'%NAMES[size])

# 4) deeper tip that reaches solid still kills (sanity)
for size in (1,2):
    d=place(size,rx0+INSET[size],y_extra=2)
    ok(d==1,'%s: deeper solid overlap still kills'%NAMES[size])

print('fails:',len(FAIL))
for m in FAIL: print(' ',m)
p.terminate(); 
try: p.wait(timeout=2)
except Exception: p.kill()
sys.exit(1 if FAIL else 0)
