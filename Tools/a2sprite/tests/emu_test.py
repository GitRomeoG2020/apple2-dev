#!/usr/bin/env python3
"""End-to-end: load shape table + sprite blitter into bobbin-ai, DRAW, read HGR memory, decode to ASCII."""
import subprocess,time,os,sys,json,pty
sys.path.insert(0,'/workspace/apple2/tests'); from sock import send
D=os.path.dirname(os.path.abspath(__file__)); SOCK='/tmp/a2s.sock'
if os.path.exists(SOCK): os.remove(SOCK)
m,s=pty.openpty()
p=subprocess.Popen(['/workspace/apple2/bin/bobbin-ai','--simple','--remain','-m','plus','--control-socket',SOCK],stdin=s,stdout=s,stderr=s,start_new_session=True)
os.close(s); time.sleep(1.5)
def q(o): return send(json.dumps(o),SOCK)
def keys(t): q({'cmd':'keys','text':t+'\r'}); time.sleep(0.6)
shp=open(D+'/shapes.bin','rb').read(); blit=open(D+'/blit.bin','rb').read()
print('load shapes:',q({'cmd':'load','addr':0x6000,'hex':shp.hex()})[:80])
print('load blit  :',q({'cmd':'load','addr':0x6100,'hex':blit.hex()})[:80])
keys('POKE 232,0: POKE 233,96'); keys('HGR : HCOLOR= 3: SCALE= 1: ROT= 0')
keys('DRAW 1 AT 140,96'); keys('DRAW 2 AT 160,96'); keys('CALL 24832'); time.sleep(1)
mem=b''
for a in (0x2000,0x3000):
    r=json.loads(q({'cmd':'peek','addr':a,'len':4096}))
    if a==0x2000: print('peek keys:',list(r.keys()))
    d=r.get('data') or r.get('bytes') or r.get('hex')
    mem+=bytes.fromhex(d.replace(' ','')) if isinstance(d,str) else bytes(d)
def addr(y): return (y&7)*0x400+((y>>3)&7)*0x80+(y>>6)*0x28
bmp=[[ (mem[addr(y)+b]>>i)&1 for b in range(40) for i in range(7)] for y in range(192)]
def show(x0,x1,y0,y1):
    for y in range(y0,y1): print('%3d '%y+''.join('#' if bmp[y][x] else '.' for x in range(x0,x1)))
print('\nShapes region x=136..172, y=92..106 (DRAW 1 AT 140,96 square, DRAW 2 AT 160,96 arrow):'); show(136,172,92,106)
sq={(x,y) for y in range(192) for x in range(280) if bmp[y][x] and 130<=x<155}
want={(140+x,96) for x in range(8)}|{(148,96+y) for y in range(8)}|{(148-x,104) for x in range(8)}|{(140,104-y) for y in range(8)}
print('square pixels match expected:',sq==want,len(sq),'set')
ar={(x-160,y-96) for y in range(192) for x in range(155,175) if bmp[y][x]}
wa={(x,y-4) for x,y in [(0,0),(1,1),(2,2),(3,3),(4,4),(3,5),(2,6),(1,7),(0,8)]+[(0,i) for i in range(1,8)]}
print('arrow pixels match expected:',ar==wa)
print('\nSprite blit (face_s3 at byte col 10 = x 70..90, rows 38..48):'); show(68,92,38,48)
fx={(x,y) for y in range(38,48) for x in range(60,100) if bmp[y][x]}
face=[[0,1,1,1,1,1,0],[1,0,0,0,0,0,1],[1,0,1,0,1,0,1],[1,0,0,0,0,0,1],[1,0,1,1,1,0,1],[1,0,0,0,0,0,1],[0,1,1,1,1,1,0]]
fw={(70+5+3+x,40+y) for y in range(7) for x in range(7) if face[y][x]}
print('sprite pixels match expected (x offset 5 in sprite + shift 3):',fx==fw)
print('raw bytes row 40, cols 10-12:',[hex(mem[addr(40)+10+i]) for i in range(3)])
q({'cmd':'quit'}); time.sleep(0.5); p.kill()
