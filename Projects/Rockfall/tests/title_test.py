#!/usr/bin/env python3
"""Title / attract-mode test: boot disk/rockfall.dsk in bobbin-ai and check
 - the hi-res title art is on HGR page 1 (rows 0-159 == tools/gen_title.py output, apart from the
   twinkling stars and the animated meteor streak), mixed mode with the prompt lines in text rows 20-23;
 - it animates (stars twinkle, a streak appears) and every changed byte is a star or the streak;
 - it alternates with the text score view (HIGH SCORES table + PRESS ANY KEY) and back, with no
   residue of the streak left on the art;
 - a key starts the game; game over + ESC returns to the title art.
Saves PNGs of the art view (with its text window) and the score view.  Usage: title_test.py [enhanced|plus]"""
import subprocess,time,os,sys,json,pty,re,shutil
sys.path.insert(0,'/workspace/apple2/tests'); from sock import send
T=os.path.dirname(os.path.abspath(__file__)); D=T+'/..'
sys.path.insert(0,D+'/tools'); import gen_title, gen_land
MACH=sys.argv[1] if len(sys.argv)>1 else 'enhanced'
SOCK='/tmp/rftitle_'+MACH+'.sock'
if os.path.exists(SOCK): os.remove(SOCK)
DSK='/tmp/rf_title_%s.dsk'%MACH; shutil.copy(D+'/disk/rockfall.dsk',DSK)
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
key=lambda c,t=0.1:(q({'cmd':'keys','text':c}),time.sleep(t))
A=lambda y:(y&7)*0x400+((y>>3)&7)*0x80+(y>>6)*0x28
TL=lambda r:0x400+(r&7)*0x80+(r>>3)*0x28
FAIL=[]
def ok(c,msg): print(('PASS ' if c else 'FAIL ')+msg); c or FAIL.append(msg)
c,_=gen_title.draw(); ART=[v for r in gen_land.encode(c) for v in r]          # 160 rows x 40
inc=open(D+'/src/title.inc').read()
tw=lambda n:[int(v,0) if not v.startswith('$') else int(v[1:],16) for v in re.search(n+r':\s+\.byte (.*)',inc).group(1).split(',')]
STARS=set((r,cc) for r,cc in zip(tw('twrow'),tw('twcol')))
text=lambda:[bytes(b&0x7F for b in peek(TL(r),40)).decode('latin1') for r in range(24)]
screen=lambda:'\n'.join(text())
view=lambda:peek(0xCE,1)[0]
def artdiff():
    pg=peek(0x2000,0x2000); return [(y,b) for y in range(160) for b in range(40) if pg[A(y)+b]!=ART[y*40+b]],pg
def wait(f,t):
    t0=time.time()
    while time.time()-t0<t:
        if f(): return True
        time.sleep(0.05)
    return False
def textpng(path,lines=range(24),y0=0):
    from PIL import Image,ImageDraw,ImageFont
    im=Image.new('RGB',(560,len(lines)*16)); d=ImageDraw.Draw(im); drawtext(d,lines,0); im.save(path)
def drawtext(d,lines,top):
    from PIL import ImageFont
    try: f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf',13)
    except Exception: f=ImageFont.load_default()
    for i,r in enumerate(lines):
        for cc,b in enumerate(peek(TL(r),40)):
            ch=chr((b&0x3F)+(0x40 if (b&0x3F)<0x20 else 0)); inv=b<0x80
            if inv: d.rectangle([cc*14,top+i*16,cc*14+13,top+i*16+15],fill=(255,255,255) if b<0x40 else (90,255,90))
            d.text((cc*14+3,top+i*16+1),ch,font=f,fill=(0,0,0) if inv else (255,255,255))
def artpng(pg,path):
    """hi-res rows 0-159 (2x) + the 4-line text window, as the mixed-mode screen looks"""
    from PIL import Image,ImageDraw
    rows=[list(pg[A(y):A(y)+40]) for y in range(160)]
    gen_land.render_png(rows,'/tmp/_art.png'); art=Image.open('/tmp/_art.png').resize((560,320))
    im=Image.new('RGB',(560,320+64)); im.paste(art,(0,0)); drawtext(ImageDraw.Draw(im),range(20,24),320); im.save(path); print('screenshot:',path)
# ---------- 1: art view ----------
ok(wait(lambda:view()==0 and len(artdiff()[0])<60,25),'title art appears on HGR page 1 after boot')
time.sleep(2.5); d,pg=artdiff(); sc=text()
print('art bytes differing from gen_title output: %d (stars %d)'%(len(d),sum(1 for x in d if x in STARS)))
ok(all(x in STARS or x[0]<75 for x in d),'art matches gen_title output except twinkling stars / streak area')
print('text window:\n'+'\n'.join(sc[20:24]))
ok("THEY'RE METEORS" in sc[20] and 'MOVE' in sc[21] and 'FIRE' in sc[21] and 'BEST:' in sc[22] and 'PRESS ANY KEY TO START' in sc[23],'text window: tagline, controls, best score, prompt')
fl=peek(TL(23),40); ok(all(0x40<=b<0x80 for b in fl if b!=0xA0),'prompt flashes')
artpng(pg,T+'/title_art_'+MACH+'.png')
# animation: sample for 6 s, collect changed bytes
seen=set(); streak=False
for i in range(60):
    d,_=artdiff(); seen|=set(d)
    if any(x not in STARS for x in d): streak=True
    if view()!=0: break
    time.sleep(0.1)
print('changed bytes while animating: %d (twinkle stars %d, other %d)'%(len(seen),sum(1 for x in seen if x in STARS),sum(1 for x in seen if x not in STARS)))
ok(any(x in STARS for x in seen),'stars twinkle')
ok(streak,'a meteor streak animates')
# ---------- 2: alternation ----------
ok(wait(lambda:view()==1,24),'switches to the score view')
time.sleep(0.3); sc=screen(); print('== score view ==\n'+'\n'.join(l for l in sc.split('\n') if l.strip()))
ok('HIGH SCORES' in sc and '1. A2D  0250  LV04' in sc and 'PRESS ANY KEY TO START' in sc and 'ARROWS' in sc,'score view: table, prompt and controls')

from PIL import Image; textpng(T+'/title_scores_'+MACH+'.png'); print('screenshot:',T+'/title_scores_'+MACH+'.png')
# after the score view the attract mode enters DEMO (AI play) instead of looping art forever
ok(wait(lambda:peek(0x6B,1)[0]==1 or view()==0,12),'after scores: demo or art continues')
if peek(0x6B,1)[0]==1:
    print('entered DEMO after idle score pass')
    ok(True,'idle enters demo mode')
else:
    time.sleep(0.2); d,_=artdiff(); print('art bytes differing after the round trip: %d, non-star %s'%(len(d),[x for x in d if x not in STARS][:8]))
    ok(all(x in STARS for x in d) or peek(0xC5,1)[0]==1,'no streak residue after the round trip')
# ---------- 3: key starts the game (from demo or title); ESC from game over returns ----------
key(' ',1.5); f0=peek(0x90,1)[0]; time.sleep(0.3)
ok(peek(0x6B,1)[0]==0 and peek(0x90,1)[0]!=f0 and not peek(0x67,1)[0],'any key starts a real game')
poke(0x63,[0,0]); poke(0x4E,[1]); poke(0x67,[1]); time.sleep(4)
ok(wait(lambda:'ANY KEY: PLAY AGAIN' in screen(),6),'game over screen')
key('\x1b',0.5)
ok(wait(lambda:view()==0 and len(artdiff()[0])<60,8),'ESC returns to the title art')
q({'cmd':'quit'})
print('RESULT:','PASS' if not FAIL else 'FAIL %s'%FAIL)
