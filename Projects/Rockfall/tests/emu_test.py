#!/usr/bin/env python3
"""Boot disk/rockfall.dsk in bobbin-ai, drive it over the control socket, check both HGR pages,
page flipping, laser, collision and restart.  Usage: emu_test.py [enhanced|plus]"""
import subprocess,time,os,sys,json,pty,re
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
    out=b''
    while n>0:
        k=min(n,0x1000); r=q({'cmd':'peek','addr':a,'len':k}); d=r.get('data') or r.get('bytes') or r.get('hex')
        out+=bytes.fromhex(d.replace(' ','')) if isinstance(d,str) else bytes(d); a+=k; n-=k
    return out
def zp():
    z=peek(0x50,0x60)
    return dict(PX=z[0x0C],DIR=z[0x0E],SPEED=z[0x11],SCORE='%02X%02X'%(z[0x14],z[0x13]),DEAD=z[0x17],
                RY=list(z[0x28:0x2D]),RCOL=list(z[0x20:0x25]),RON=list(z[0x38:0x3D]),FRAME=z[0x40],BACK=z[0x42],LON=z[0x44],LY=z[0x48])
A=lambda y:(y&7)*0x400+((y>>3)&7)*0x80+(y>>6)*0x28
def page(pg): return peek(0x2000*(pg+1),0x2000)
def rows(mem,n=192): return [list(mem[A(y):A(y)+40]) for y in range(n)]
def art(mem,y0=0,y1=192,step=4):
    bm=[[(mem[A(y)+b]>>i)&1 for b in range(40) for i in range(7)] for y in range(192)]
    return '\n'.join(''.join('#' if any(bm[yy][xx] for yy in range(y,min(y+step,192)) for xx in range(x,x+3)) else '.' for x in range(0,279,3)) for y in range(y0,y1,step))
L=open(D+'/build/rockfall.lst').read(); M=open(D+'/build/rockfall.map').read()
ROD=int(re.search(r'^RODATA\s+([0-9A-F]+)',M,re.M).group(1),16)
lab=lambda n:ROD+int(re.search(r'^([0-9A-F]+)r 2 .*?\b'+n+':',L,re.M).group(1),16)
A_ROCK,A_SLO,A_SHI,A_FONT=lab('rock'),lab('ship_shift_lo'),lab('ship_shift_hi'),lab('font')
NST=36
def expected(pg,sv):
    """Page pg rebuilt from what the game saved as drawn there: ground + XOR(ship, rocks, bolt, stars)."""
    e=[[0]*40 for _ in range(160)]; e[158]=[0x7F]*40; e[159]=[0x7F]*40
    if not sv[0x2BC+pg]: return e
    def x(data,col,y,w,h):
        for r in range(h):
            for b in range(w): e[y+r][col+b]^=data[r*w+b]
    px=sv[0x2B0+pg]; k=(px*2)%7
    x(peek(SL[k]|SH[k]<<8,24),(px*2)//7,148,3,8)
    for i in range(5):
        if sv[0x280+pg*8+i]: x(RK,sv[0x290+pg*8+i],sv[0x2A0+pg*8+i],2,8)
    if sv[0x2B2+pg]:
        c,m1,m2,y=sv[0x2B4+pg],sv[0x2B6+pg],sv[0x2B8+pg],sv[0x2BA+pg]
        for r in range(12):
            e[y+r][c]^=m1
            if m2: e[y+r][c+1]^=m2
    return e
def expected2(pg,sv):
    e=expected(pg,sv)
    if sv[0x2BC+pg]:
        for i in range(NST):
            j=pg*64+i; e[sv[0x200+j]][sv[0x100+j]]^=sv[0x180+j]
    return e
def check1():
    q({'cmd':'pause'})
    try: sv=peek(0x1800,0x300); pgs=[page(0),page(1)]; z=zp()
    finally: q({'cmd':'resume'})
    res=[]
    for pg in (0,1):
        # back page may be mid-render; only the shown page (1-BACK) must match exactly, but check both
        e=expected2(pg,sv); a=rows(pgs[pg],160)
        res.append([(y,b,a[y][b],e[y][b]) for y in range(160) for b in range(40) if a[y][b]!=e[y][b]])
    return res,z,pgs
def check(tag,tries=8):
    for t in range(tries):
        res,z,pgs=check1()
        if not res[0] and not res[1]: break
        time.sleep(0.023)
    print('[%s] mismatched bytes page1=%d page2=%d (shown=page%d) %s (samples %d)'%(tag,len(res[0]),len(res[1]),2-z['BACK'],(res[0]+res[1])[:4],t+1))
    return len(res[0])+len(res[1]),pgs
def key(c): q({'cmd':'keys','text':c}); time.sleep(0.05)
SL=SH=RK=None
time.sleep(6)
SL,SH,RK=peek(A_SLO,7),peek(A_SHI,7),peek(A_ROCK,16)
print('== title screen ==\n'+'\n'.join(q({'cmd':'screen'})['lines']))
key(' '); time.sleep(1.5)
z=zp(); print('after start:',z)
# page-flip evidence: sample BACK + frame counter
seen=set(); f0=z['FRAME']; t0=time.time()
for i in range(40): seen.add(zp()['BACK']); time.sleep(0.013)
z=zp(); print('BACK values seen in 0.6s:',sorted(seen),' frames advanced:',(z['FRAME']-f0)&255,'in %.2fs'%(time.time()-t0))
n,pgs=check('start')
print('== page 1 ($2000) ==\n'+art(pgs[0])); print('== page 2 ($4000) ==\n'+art(pgs[1]))
# status line decode (rows 172-176) identical on both pages
st=[rows(pg)[172:177] for pg in pgs]; print('status area identical on both pages:',st[0]==st[1])
F=peek(A_FONT,18*5); glyph={tuple(F[g*5:g*5+5]):'0123456789CDEHIPR '[g] for g in range(18)}
dec=lambda pg:''.join(glyph.get(tuple(rows(pg)[172+r][c] for r in range(5)),'?') for c in range(40))
print('status decoded:',repr(dec(pgs[0])))
sv=peek(0x1800,0x100); st0=[(sv[0x60+i]) for i in range(NST)]
time.sleep(0.5); sv=peek(0x1800,0x100); print('stars that moved down in 0.5s:',sum(1 for i in range(NST) if sv[0x60+i]!=st0[i]))
px0=zp()['PX']
for i in range(10): key('\x08')
time.sleep(0.3); print('after 10x left: PX',px0,'->',zp()['PX'])
# --- laser test: fire, then (paused) put rock 0 in the bolt's path and check +5 ---
def alive():
    for t in range(20):
        if not zp()['DEAD']: return
        time.sleep(3); key('A'); time.sleep(0.5)
alive()
for tries in range(6):
    q({'cmd':'keys','text':' '}); ok=False
    for i in range(30):
        q({'cmd':'pause'}); z=zp()
        if z['LON'] and z['LY']>=100 and not z['DEAD']: ok=True; break
        q({'cmd':'resume'}); time.sleep(0.005)
    if ok: break
lx2=peek(0x99,1)[0]; col=min(38,(lx2*2)//7); sc0=z['SCORE']
q({'cmd':'poke','addr':0x70,'data':[col]}); q({'cmd':'poke','addr':0x78,'data':[z['LY']-30]}); q({'cmd':'poke','addr':0x88,'data':[1]})
print('bolt in flight: LY=%d bolt x=%dpx; rock 0 placed at byte col %d row %d (fire attempts %d)'%(z['LY'],lx2*2,col,z['LY']-30,tries+1))
q({'cmd':'resume'}); tr=[]
for i in range(12): z=zp(); tr.append((z['LON'],z['LY'],z['RON'][0],z['RY'][0],z['SCORE'])); time.sleep(0.01)
print('trace (LON,LY,RON0,RY0,SCORE):',tr)
z=zp(); print('laser hit: score %s -> %s  (+5 expected, dodge +1s possible)'%(sc0,z['SCORE']))
check('after laser hit')
# fire a few more and capture the bolt mid-flight on the shown page
q({'cmd':'keys','text':' '}); time.sleep(0.03); q({'cmd':'pause'}); z=zp(); pg=1-z['BACK']; img=page(pg); q({'cmd':'resume'})
print('== shown page%d with bolt (LON=%d LY=%d) ==\n'%(pg+1,z['LON'],z['LY'])+art(img,0,160))
# --- soak ---
tot=0; deaths=0; t0=time.time(); i=0
while time.time()-t0<30:
    key('\x08' if (i//6)%2 else 'L'); i+=1
    if i%3==0: key(' ')
    time.sleep(0.2)
    if i%8==0:
        z=zp()
        if z['DEAD']: deaths+=1; time.sleep(3.5); key('A'); time.sleep(0.5); continue
        n,_=check('soak %ds score %s'%(time.time()-t0,z['SCORE'])); tot+=n
print('soak done: total mismatched bytes',tot,'deaths/restarts',deaths)
print('after soak:',zp())
# --- forced collision: pause, stop the ship, drop rock 0 right onto it ---
alive(); q({'cmd':'pause'}); z=zp()
want=max(0,(z['PX']*2+7)//7-1)
q({'cmd':'poke','addr':0x5E,'data':[0]}); q({'cmd':'poke','addr':0x93,'data':[0,0]})
q({'cmd':'poke','addr':0x70,'data':[want]}); q({'cmd':'poke','addr':0x78,'data':[140]}); q({'cmd':'poke','addr':0x88,'data':[1]})
q({'cmd':'resume'}); print('forcing rock 0 into column',want,'ship PX',z['PX'])
time.sleep(4); z=zp(); print('after forced rock:',z)
print('== text screen (page 1 text, mixed mode) ==\n'+'\n'.join(q({'cmd':'screen'})['lines'][20:24]))
n,pgs=check('game over'); print('== page 1 at game over ==\n'+art(pgs[0],0,160))
code=peek(0x800,0x300); print('code at $0800 intact (boot byte $10, first opcodes):',code[:4].hex())
time.sleep(1); key('A'); time.sleep(1); print('restart:',zp()); check('after restart')
q({'cmd':'quit'}); time.sleep(0.5); p.kill()
