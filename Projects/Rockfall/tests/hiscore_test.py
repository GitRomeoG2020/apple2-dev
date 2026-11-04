#!/usr/bin/env python3
"""High-score table test: boot disk/rockfall.dsk in bobbin-ai, check the default table at $1B00 and on the
title screen, the HUD HI value, a qualifying game over (initials typed + arrow-cycled + RETURN, inserted in
the right place), a new top score feeding the HUD HI, and a non-qualifying score skipping entry.
Saves PNGs of the initials entry screen and the table.  Usage: hiscore_test.py [enhanced|plus]"""
import subprocess,time,os,sys,json,pty,re
sys.path.insert(0,'/workspace/apple2/tests'); from sock import send
MACH=sys.argv[1] if len(sys.argv)>1 else 'enhanced'
D=os.path.dirname(os.path.abspath(__file__))+'/..'; SOCK='/tmp/rfhs_'+MACH+'.sock'
if os.path.exists(SOCK): os.remove(SOCK)
import shutil; DSK='/tmp/rf_%s_%s.dsk'%(os.path.basename(__file__)[:-3],MACH); shutil.copy(D+'/disk/rockfall.dsk',DSK)   # games may save scores: never touch the repo disk
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
key=lambda c,t=0.15:(q({'cmd':'keys','text':c}),time.sleep(t))
FAIL=[]
def ok(c,msg): print(('PASS ' if c else 'FAIL ')+msg); c or FAIL.append(msg)
TL=lambda r:0x400+(r&7)*0x80+(r>>3)*0x28
def text():
    out=[]
    for r in range(24):
        out.append(''.join(chr((b&0x3F)+(0x40 if (b&0x3F)<0x20 else 0)) for b in peek(TL(r),40)))
    return out
def table():
    t=peek(0x1B00,0x30); return [(bytes(x&0x7F for x in t[i*8:i*8+3]).decode(),'%02X%02X'%(t[i*8+4],t[i*8+3]),'%02X'%t[i*8+5]) for i in range(5)],t
def textpng(path):
    from PIL import Image,ImageDraw,ImageFont
    mem=[peek(TL(r),40) for r in range(24)]; im=Image.new('RGB',(40*14,24*16)); d=ImageDraw.Draw(im)
    try: f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf',13)
    except Exception: f=ImageFont.load_default()
    for r in range(24):
        for c,b in enumerate(mem[r]):
            ch=chr((b&0x3F)+(0x40 if (b&0x3F)<0x20 else 0)); inv=b<0x80
            if inv: d.rectangle([c*14,r*16,c*14+13,r*16+15],fill=(255,255,255) if b<0x40 else (90,255,90))
            d.text((c*14+3,r*16+1),ch,font=f,fill=(0,0,0) if inv else (255,255,255))
    im.save(path); print('screenshot:',path)
def screen(): return '\n'.join(text())
L=open(D+'/build/rockfall.lst').read(); M=open(D+'/build/rockfall.map').read()
ROD=int(re.search(r'^RODATA\s+([0-9A-F]+)',M,re.M).group(1),16)
FA=ROD+int(re.search(r'^([0-9A-F]+)r 2 .*?\bfont:',L,re.M).group(1),16)
time.sleep(6)
F=peek(FA,24*5); GL={tuple(F[g*5:g*5+5]):'0123456789CDEHIPR SOATLV'[g] for g in range(24)}
A=lambda y:(y&7)*0x400+((y>>3)&7)*0x80+(y>>6)*0x28
def hud(): pg=peek(0x2000,0x2000); return ''.join(GL.get(tuple(pg[A(186+r)+c] for r in range(5)),'?') for c in range(26))
def die(score,level=1):
    poke(0x63,[score&0xFF,score>>8]); poke(0xA7,[level]); poke(0x67,[1]); time.sleep(3.5)
def wait_text(s,t=6):
    t0=time.time()
    while time.time()-t0<t:
        if s in screen(): return True
        time.sleep(0.1)
    return False
# --- defaults ---
tb,raw=table(); print('table at $1B00:',tb,' magic',raw[0x28:0x2B])
ok(tb==[('A2D','0250','04'),('ROM','0150','03'),('GRK','0100','02'),('HGR','0050','02'),('SPK','0025','01')] and raw[0x28:0x2B]==b'RF\x01','default table + magic at $1B00')
wait_text('R O C K F A L L',35); time.sleep(0.3); sc=screen(); print('== title (score view of the attract loop) ==\n'+sc)
ok('HIGH SCORES' in sc and '1. A2D  0250  LV04' in sc and '2. ROM  0150  LV03' in sc and '5. SPK  0025  LV01' in sc,'table shown on the title screen')
textpng(D+'/tests/hiscore_title_'+MACH+'.png')
key(' '); time.sleep(1.5); h=hud(); print('HUD:',repr(h)); ok('HI 0250' in h,'HUD HI = top entry (0250)')
# --- qualifying: 175 at level 3 -> rank 2 (index 1) ---
die(0x175,3); ok(wait_text('ENTER YOUR INITIALS'),'qualifying score -> initials entry'); time.sleep(0.3)
print('RANK',peek(0xAD,1)[0]); ok(peek(0xAD,1)[0]==1,'rank 2 for 0175')
print('== entry ==\n'+screen()); textpng(D+'/tests/hiscore_entry_'+MACH+'.png')
key('r'); key('\x15'); key('\x15'); key('\x15'); key('\x08'); key('\r'); key('G')   # R, A->D->C (right x3, left), RETURN, G
ok(wait_text('ANY KEY: PLAY AGAIN'),'entry finished after 3 letters')
tb,_=table(); print('table:',tb)
ok(tb==[('A2D','0250','04'),('RCG','0175','03'),('ROM','0150','03'),('GRK','0100','02'),('HGR','0050','02')],'inserted at rank 2 with initials RCG and level 3; SPK dropped')
sc=screen(); print('== table after game over ==\n'+sc); ok('2. RCG  0175  LV03' in sc,'table shown after game over')
inv=peek(TL(8)+10,20); ok(all(b<0x80 for b in inv),'new entry row in inverse')
textpng(D+'/tests/hiscore_table_'+MACH+'.png')
# --- new top score ---
key('A',1.5); die(0x300,5); ok(wait_text('ENTER YOUR INITIALS'),'top score -> entry'); key('T'); key('O'); key('P')
ok(wait_text('ANY KEY: PLAY AGAIN'),'entry done'); tb,_=table(); print('table:',tb); ok(tb[0]==('TOP','0300','05') and tb[1][0]=='A2D','new #1 inserted at top')
key('A',1.5); h=hud(); print('HUD:',repr(h)); ok('HI 0300' in h,'HUD HI follows the new top entry')
# --- non-qualifying ---
die(0x10); time.sleep(1); sc=screen(); print('== non-qualifying ==\n'+sc)
ok('ENTER YOUR INITIALS' not in sc and 'ANY KEY: PLAY AGAIN' in sc and peek(0xAD,1)[0]==0xFF,'non-qualifying score skips entry')
tb2,_=table(); ok(tb2==tb,'table unchanged')
key('\x1b',1); wait_text('R O C K F A L L',35); time.sleep(0.3); sc=screen(); ok('1. TOP  0300  LV05' in sc,'ESC -> title shows updated table')
q({'cmd':'quit'})
print('RESULT:','PASS' if not FAIL else 'FAIL %s'%FAIL)
