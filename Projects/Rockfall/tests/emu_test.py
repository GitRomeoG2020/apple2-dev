#!/usr/bin/env python3
"""Boot disk/rockfall.dsk in bobbin-ai, drive it over the control socket, check HGR/zero page."""
import subprocess,time,os,sys,json,pty
sys.path.insert(0,'/workspace/apple2/tests'); from sock import send
MACH=sys.argv[1] if len(sys.argv)>1 else 'enhanced'
D=os.path.dirname(os.path.abspath(__file__))+'/..'; SOCK='/tmp/rf_'+MACH+'.sock'
if os.path.exists(SOCK): os.remove(SOCK)
m,s=pty.openpty()
p=subprocess.Popen(['/workspace/apple2/bin/bobbin-ai','--simple','--remain','--no-turbo','-m',MACH,'--disk',D+'/disk/rockfall.dsk','--control-socket',SOCK],stdin=s,stdout=s,stderr=s,start_new_session=True)
os.close(s)
def q(o): return json.loads(send(json.dumps(o),SOCK))
for i in range(50):
    try: q({'cmd':'ping'}); break
    except Exception: time.sleep(0.2)
def peek(a,n):
    r=q({'cmd':'peek','addr':a,'len':n}); d=r.get('data') or r.get('bytes') or r.get('hex')
    return bytes.fromhex(d.replace(' ','')) if isinstance(d,str) else bytes(d)
def zp(): z=peek(0x50,0x40); return dict(PX=z[0x0C],DIR=z[0x0E],SPEED=z[0x11],SCORE='%02X%02X'%(z[0x14],z[0x13]),DEAD=z[0x17],RY=list(z[0x28:0x2D]),RCOL=list(z[0x20:0x25]),RON=list(z[0x38:0x3D]))
def text(rows):
    t=q({'cmd':'screen'}); return t
def hgr():
    mem=peek(0x2000,0x1000)+peek(0x3000,0x1000)
    A=lambda y:(y&7)*0x400+((y>>3)&7)*0x80+(y>>6)*0x28
    return [[(mem[A(y)+b]>>i)&1 for b in range(40) for i in range(7)] for y in range(160)]
def art(bm,step=4):
    # 2x2 cells -> 140x80 chars
    out=[]
    for y in range(0,160,step):
        out.append(''.join('#' if any(bm[yy][xx] for yy in range(y,y+step) for xx in range(x,x+3)) else '.' for x in range(0,279,3)))
    return '\n'.join(out)
# ---- starfield / screen-integrity check ----
import re
L=open(D+'/build/rockfall.lst').read(); M=open(D+'/build/rockfall.map').read()
ROD=int(re.search(r'^RODATA\s+([0-9A-F]+)',M,re.M).group(1),16)
lab=lambda n:ROD+int(re.search(r'^([0-9A-F]+)r 2 .*?\b'+n+':',L,re.M).group(1),16)
A_ROCK,A_SLO,A_SHI=lab('rock'),lab('ship_shift_lo'),lab('ship_shift_hi')
NST=36
def expected():
    """Rebuild the screen from game state: ground + XOR(ship, live rocks, stars)."""
    z=peek(0x50,0x48); st=peek(0x1800,0x90)
    e=[[0]*40 for _ in range(160)]; e[158]=[0x7F]*40; e[159]=[0x7F]*40
    def x(data,col,y,w,h):
        for r in range(h):
            for b in range(w): e[y+r][col+b]^=data[r*w+b]
    px=z[0x0C]; sh=peek(A_SLO,7); hi=peek(A_SHI,7); k=(px*2)%7
    x(peek(sh[k]|hi[k]<<8,24),(px*2)//7,148,3,8)
    rk=peek(A_ROCK,16)
    for i in range(5):
        if z[0x38+i]: x(rk,z[0x20+i],z[0x28+i],2,8)
    for i in range(NST): e[st[0x60+i]][st[i]]^=st[0x30+i]
    return e,[(st[i],st[0x30+i],st[0x60+i]) for i in range(NST)]
def actual():
    mem=peek(0x2000,0x1000)+peek(0x3000,0x1000); A=lambda y:(y&7)*0x400+((y>>3)&7)*0x80+(y>>6)*0x28
    return [list(mem[A(y):A(y)+40]) for y in range(160)]
def check(tag,tries=6):
  # a pause can land mid-frame (a rock erased but not yet redrawn); real garbage persists, so retry
  for t in range(tries):
    n,st,bad=check1()
    if n==0: break
    time.sleep(0.037)
  print('[%s] stray/missing bytes vs ship+rocks+stars+ground model: %d %s (samples %d)'%(tag,n,bad[:5],t+1))
  return n,st
def check1():
    q({'cmd':'pause'})
    try:
        e,st=expected(); a=actual()
    finally: q({'cmd':'resume'})
    bad=[(y,b,a[y][b],e[y][b]) for y in range(160) for b in range(40) if a[y][b]!=e[y][b]]
    return len(bad),st,bad
def starpix(st): return sum(bin(m).count('1') for c,m,y in st)
def key(c): q({'cmd':'keys','text':c}); time.sleep(0.05)
time.sleep(6)
print('== title screen ==\n'+'\n'.join(q({'cmd':'screen'})['lines']))
key(' '); time.sleep(1.5)
z=zp(); print('after start:',z)
n,st0=check('start'); print('stars:',NST,'lit star pixels:',starpix(st0),'sample (col,mask,row):',st0[:4])
time.sleep(0.5); n,st1=check('+0.5s')
moved=sum(1 for a,b in zip(st0,st1) if b[2]!=a[2]); print('stars that moved down in 0.5s:',moved,'rows:',[ (a[2],b[2]) for a,b in zip(st0,st1)][:6])
bm=hgr(); print('== HGR snapshot (3x4 px per char) ==\n'+art(bm))
px0=z['PX']
for i in range(10): key('\x08')     # left arrow
time.sleep(0.3); z=zp(); print('after 10x left arrow: PX',px0,'->',z['PX'])
px1=z['PX']
for i in range(15): key('L')
time.sleep(0.3); z=zp(); print('after 15x L: PX',px1,'->',z['PX'])
# 30 s soak: wander left/right, restart on death, check screen integrity every 2 s
tot=0; deaths=0; t0=time.time(); i=0
while time.time()-t0<30:
    key('\x08' if (i//6)%2 else 'L'); i+=1; time.sleep(0.25)
    if i%8==0:
        z=zp()
        if z['DEAD']: deaths+=1; time.sleep(2.5); key('A'); time.sleep(0.5); continue
        n,_=check('soak %ds score %s'%(time.time()-t0,z['SCORE'])); tot+=n
print('soak done: total mismatched bytes',tot,'deaths/restarts',deaths)
z=zp(); print('after soak:',z)
print('== HGR after soak ==\n'+art(hgr()))
# force collision: when rock 0 is idle, preset the RNG so it spawns right above the ship
def rnd(x):
    x=(x<<1)&0x1ff; c=x>>8; x&=255
    if c: x^=0x1D
    return x or 0x5A
def tocol(v):
    while v>=39: v-=39
    return v
# force collision: when rock 0 is idle, pause and spawn it by hand right above the ship
# (state poked AND its XOR image drawn into HGR, so the game's later erase stays consistent)
for t in range(400):
    q({'cmd':'pause'}); z=zp()
    if z['RON'][0]==0: break
    q({'cmd':'resume'}); time.sleep(0.01)
want=max(0,(z['PX']*2+7)//7-1); rk=peek(A_ROCK,16)
for r in range(8):
    a=0x2000+(r&7)*0x400+want; cur=peek(a,2)
    q({'cmd':'poke','addr':a,'data':[cur[0]^rk[2*r],cur[1]^rk[2*r+1]]})
q({'cmd':'poke','addr':0x70,'data':[want]}); q({'cmd':'poke','addr':0x78,'data':[0]}); q({'cmd':'poke','addr':0x88,'data':[1]})
q({'cmd':'resume'})
print('forcing rock 0 into column',want,'ship PX',z['PX'])
time.sleep(4)
z=zp(); print('after forced rock:',z)
print('== text screen ==\n'+'\n'.join(q({'cmd':'screen'})['lines']))
print('== HGR at game over ==\n'+art(hgr())); check('game over')
time.sleep(3); key('A'); time.sleep(1); print('restart:',zp()); check('after restart')
q({'cmd':'quit'}); time.sleep(0.5); p.kill()
