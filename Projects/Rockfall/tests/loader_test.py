#!/usr/bin/env python3
"""Multi-track loader test: pad build/rockfall.bin's game image with a known pattern up to
SIZE bytes (default 24576 = 6 tracks, the max), build a disk with tools/mkdisk.py, boot it
in bobbin-ai and compare RAM $6000.. with the image after the game starts.  Also times boot.
Usage: loader_test.py [enhanced|plus] [size]"""
import subprocess,time,os,sys,json,pty
sys.path.insert(0,'/workspace/apple2/tests'); from sock import send
MACH=sys.argv[1] if len(sys.argv)>1 else 'enhanced'; SIZE=int(sys.argv[2]) if len(sys.argv)>2 else 24576
D=os.path.dirname(os.path.abspath(__file__))+'/..'; SOCK='/tmp/rfl_'+MACH+'.sock'
b=bytearray(open(D+'/build/rockfall.bin','rb').read()); g=len(b)-4096
b+=bytes(((i>>8)*37+(i&255)*11+((i>>3)&0x1F))&255 for i in range(g,SIZE))   # pattern: differs per page & offset
open('/tmp/rf_pad.bin','wb').write(b); subprocess.check_call(['python3',D+'/tools/mkdisk.py','/tmp/rf_pad.bin','/tmp/rf_pad.dsk'])
if os.path.exists(SOCK): os.remove(SOCK)
m,s=pty.openpty()
p=subprocess.Popen(['/workspace/apple2/bin/bobbin-ai','--simple','--remain','--no-turbo','-m',MACH,'--disk','/tmp/rf_pad.dsk','--control-socket',SOCK],stdin=s,stdout=s,stderr=s,start_new_session=True)
os.close(s); q=lambda o:json.loads(send(json.dumps(o),SOCK))
for i in range(50):
    try: q({'cmd':'ping'}); break
    except Exception: time.sleep(0.1)
t0=time.time(); tl=None
while time.time()-t0<30:
    sc='\n'.join(q({'cmd':'screen'})['lines'])
    if tl is None and 'LOADING' in sc: tl=time.time()-t0
    if tl is not None and 'LOADING' not in sc: break
    time.sleep(0.05)
tt=time.time()-t0
def peek(a,n):
    out=b''
    while n>0:
        k=min(n,0x1000); out+=bytes(q({'cmd':'peek','addr':a,'len':k})['data']); a+=k; n-=k
    return out
q({'cmd':'pause'}); ram=peek(0x6000,SIZE); ld=peek(0x800,8); q({'cmd':'quit'}); time.sleep(0.3); p.kill()
img=bytes(b[4096:])
bad=[i for i in range(SIZE) if ram[i]!=img[i]]
print('machine %s: image %d bytes = %d tracks (ntracks byte %d); LOADING seen at %.2fs, loader done (LOADING gone) at %.2fs (wall clock, --no-turbo)'%(MACH,SIZE,(SIZE+4095)//4096,ld[4],tl or -1,tt))
for t in range((SIZE+4095)//4096):
    seg=range(t*4096,min(SIZE,t*4096+4096)); nb=sum(1 for i in seg if ram[i]!=img[i])
    print('  track %d -> $%04X-$%04X: %d/%d bytes match'%(t+1,0x6000+seg[0],0x6000+seg[-1],len(seg)-nb,len(seg)))
print('RESULT: %s (%d mismatches%s)'%('PASS' if not bad else 'FAIL',len(bad),'' if not bad else ', first at $%04X'%(0x6000+bad[0])))
sys.exit(1 if bad else 0)
