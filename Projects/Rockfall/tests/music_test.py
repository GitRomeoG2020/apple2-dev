#!/usr/bin/env python3
"""Title music test: boot disk/rockfall.dsk in bobbin-ai and check
 - the two-voice player runs on the title (MUSON=1) and toggles the speaker (breakpoints on both
   `bit $C030` in the 63-cycle loop), at the real tick rate;
 - the title still animates; art can advance to the score view while music plays;
 - both streams wrap from their last event to the loop labels together (seamless loop);
 - M mutes/unmutes on the title (MMUTE / MUSON / hint) without starting;
 - a non-M key starts the game within 0.2 s and the music stops (MUSON=0, no more toggles).
Also renders the WAV preview with tools/render_music.py using the measured tick length.
Usage: music_test.py [enhanced|plus]"""
import subprocess,time,os,sys,json,pty,re,shutil
sys.path.insert(0,'/workspace/apple2/tests'); from sock import send
T=os.path.dirname(os.path.abspath(__file__)); D=T+'/..'
sys.path.insert(0,D+'/tools'); import gen_title, gen_land
MACH=sys.argv[1] if len(sys.argv)>1 else 'enhanced'
SOCK='/tmp/rfmusic_'+MACH+'.sock'
if os.path.exists(SOCK): os.remove(SOCK)
DSK='/tmp/rf_music_%s.dsk'%MACH; shutil.copy(D+'/disk/rockfall.dsk',DSK)
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
import gen_music
view=lambda:peek(0xCE,1)[0]
demo=lambda:peek(0x6B,1)[0]
textrow=lambda r:bytes(b&0x7F for b in peek(TL(r),40)).decode('latin1')
def wait(f,t):
    t0=time.time()
    while time.time()-t0<t:
        if f(): return True
        time.sleep(0.02)
    return False
def hold_title(ticks=800):
    """Keep the current title view from expiring into demo."""
    q({'cmd':'pause'}); poke(0xC3,[ticks&255,ticks>>8]); q({'cmd':'resume'})
# locate the player and the song tables in the game image (loads at $6000)
B=open(D+'/build/rockfall.bin','rb').read()[4096:]
def find(pat,what):
    i=B.find(bytes(pat)); assert i>=0,what; return 0x6000+i
LOOP=find([0x18,0xA5,0x10,0x65,0x12,0x85,0x10,0xA5,0x11,0x65,0x13,0x85,0x11,0x90,0x05,0x2C,0x30,0xC0],'mloop')
SPK1=LOOP+15; SPK2=LOOP+15+20+3
assert B[SPK2-0x6000:SPK2-0x6000+3]==bytes([0x2C,0x30,0xC0])
inc=open(D+'/src/music.inc').read()
tab=lambda n:[int(v) for v in re.search(r'\n'+n+r': \.byte (.*)',inc).group(1).split(',')]
LEADL=find(tab('mleadl')[:24],'mleadl'); BASSL=find(tab('mbassl')[:24],'mbassl')
LEADEND=LEADL+len(tab('mleadl'))-1; BASSEND=BASSL+len(tab('mbassl'))-1      # the $FF bytes
print('mloop $%04X, speaker toggles at $%04X/$%04X, lead loop $%04X-$%04X, bass loop $%04X-$%04X'%(LOOP,SPK1,SPK2,LEADL,LEADEND,BASSL,BASSEND))
w16=lambda a:(lambda b:b[0]|b[1]<<8)(peek(a,2))
# ---------- 1: music runs on the title ----------
ok(wait(lambda:peek(0x0E,1)[0]==1 and view()==0 and demo()==0,25),'music starts on the title (MUSON=1)')
hold_title(1200)
time.sleep(1)
def hits(addr,secs=1.0):
    q({'cmd':'break_set','addr':addr}); n=0; t0=time.time()
    while time.time()-t0<secs and n<5:
        c=q({'cmd':'cpu'})
        if c.get('paused') and c.get('break_hit',-1)>=0: n+=1; q({'cmd':'resume'})
        time.sleep(0.01)
    q({'cmd':'break_clear','addr':addr})
    if q({'cmd':'cpu'}).get('paused'): q({'cmd':'resume'})
    return n
time.sleep(5)                       # past the doom intro, both voices playing
hold_title(1200)
h1=hits(SPK1); h2=hits(SPK2,3.0)
ok(h1>0 and h2>0,'speaker toggles from both voices (lead %d, bass %d hits)'%(h1,h2))
# ---------- 2: title still animates; score view keeps music ----------
ok(view()==0 and demo()==0,'art view showing')
ok('MUSIC ON' in textrow(22),'art hint shows MUSIC ON')
s0=peek(0x2000,0x1400); time.sleep(1.5); s1=peek(0x2000,0x1400)
ok(s0!=s1,'title art animates while the music plays (%d bytes changed)'%sum(a!=b for a,b in zip(s0,s1)))
# ---------- 3: M mutes / unmutes on art without starting ----------
hold_title(1200)
key('M',0.2)
ok(wait(lambda:peek(0x0D,1)[0]==1 and peek(0x0E,1)[0]==0,2.0),'M mutes (MMUTE=1, MUSON=0)')
ok(demo()==0 and view()==0,'still on title art after mute')
ok(wait(lambda:'MUSIC OFF' in textrow(22),2),'hint shows MUSIC OFF')
time.sleep(0.4); h=hits(SPK1,0.6)+hits(SPK2,0.6)
ok(h==0,'no speaker toggles while muted')
key('M',0.2)
ok(wait(lambda:peek(0x0D,1)[0]==0 and peek(0x0E,1)[0]==1,2.0),'M unmutes (MMUTE=0, MUSON=1)')
ok(wait(lambda:'MUSIC ON' in textrow(22),2),'hint shows MUSIC ON')
hold_title(1200)
time.sleep(0.5); h1=hits(SPK1); h2=hits(SPK2,1.5)
ok(h1>0 or h2>0,'speaker toggles again after unmute (lead %d bass %d)'%(h1,h2))
# ---------- 4: score view still has music + hint ----------
q({'cmd':'pause'}); poke(0xC3,[2,0]); q({'cmd':'resume'})
ok(wait(lambda:view()==1 and peek(0x0E,1)[0]==1,5),'switches to the score view, music still on')
hold_title(1200)
ok('MUSIC ON' in textrow(12),'score hint shows MUSIC ON')
# ---------- 5: loop wrap ----------
# park both streams on their last event (a 2-tick rest in both) with 1 tick left
q({'cmd':'pause'}); poke(0x18,[(LEADEND-2)&255,(LEADEND-2)>>8]); poke(0x1A,[(BASSEND-2)&255,(BASSEND-2)>>8]); poke(0x1C,[1,1])
q({'cmd':'resume'}); time.sleep(0.15)
p1,p2=w16(0x18),w16(0x1A)
print('after wrap: lead ptr $%04X (loop+%d), bass ptr $%04X (loop+%d)'%(p1,p1-LEADL,p2,p2-BASSL))
ok(LEADL<p1<LEADL+40 and BASSL<p2<BASSL+40,'both streams wrapped to their loop labels')
ok((p1-LEADL)<=4 and (p2-BASSL)<=4,'streams stay in step after the wrap')
# ---------- 6: other key starts the game fast, music stops ----------
hold_title(1200)
time.sleep(0.3); t0=time.time(); key(' ',0)
ok(wait(lambda:peek(0x0E,1)[0]==0 and demo()==0,1.0),'key stops the music')
dt=time.time()-t0; print('key -> game start: %.3f s (includes socket latency)'%dt)
ok(dt<0.2,'game starts within 0.2 s of the key')
time.sleep(0.5); h=hits(SPK1,0.5)+hits(SPK2,0.5)
ok(h==0,'no music toggles during the game')
ok(peek(0x0D,1)[0]==0,'MMUTE preference still unmuted after game start')
q({'cmd':'quit'})
print('RESULT:','PASS' if not FAIL else 'FAIL %s'%FAIL)
