#!/usr/bin/env python3
"""High-score disk save test (bobbin-ai). Uses temp copies of disk/rockfall.dsk.
 1. qualifying game over + initials -> loader wrsect writes track 0 / physical sector 15; bobbin turns the
    nibbles back into the .dsk when the motor spins down (so a changed file also proves the motor went off);
    the sector bytes must equal the table in RAM, valid check bytes, and nothing else on the disk may change
 2. reboot the same image: the loader reads the sector and the title shows the saved table
 3. corrupted sector -> defaults
 4. write-protected disk (bobbin-ai-wp, BOBBIN_WRITE_PROTECT=1: $C08E bit 7 set, writes dropped) ->
    'DISK WRITE PROTECTED' message, scores kept in memory, disk unchanged, game continues
Usage: save_test.py [enhanced|plus]"""
import subprocess,time,os,sys,json,pty,shutil
sys.path.insert(0,'/workspace/apple2/tests'); from sock import send
MACH=sys.argv[1] if len(sys.argv)>1 else 'enhanced'
D=os.path.dirname(os.path.abspath(__file__))+'/..'; SOCK='/tmp/rfsv_'+MACH+'.sock'
ORIG=open(D+'/disk/rockfall.dsk','rb').read()
FAIL=[]
def ok(c,msg): print(('PASS ' if c else 'FAIL ')+msg); c or FAIL.append(msg)
class Emu:
    def __init__(s,dsk,wp=False):
        if os.path.exists(SOCK): os.remove(SOCK)
        m,sl=pty.openpty(); env=dict(os.environ)
        if wp: env['BOBBIN_WRITE_PROTECT']='1'; env['BOBBIN_ROMDIR']='/workspace/apple2/bobbin-ai/src/roms'
        s.p=subprocess.Popen(['/workspace/apple2/bin/'+('bobbin-ai-wp' if wp else 'bobbin-ai'),'--simple','--remain','--no-turbo','-m',MACH,'--disk',dsk,'--control-socket',SOCK],stdin=sl,stdout=sl,stderr=sl,start_new_session=True,env=env)
        os.close(sl); s.m=m
        for i in range(50):
            try: s.q({'cmd':'ping'}); break
            except Exception: time.sleep(0.2)
    def q(s,o): return json.loads(send(json.dumps(o),SOCK))
    def peek(s,a,n): return bytes(s.q({'cmd':'peek','addr':a,'len':n})['data'])
    def poke(s,a,d): s.q({'cmd':'poke','addr':a,'data':d})
    def key(s,c,t=0.15): s.q({'cmd':'keys','text':c}); time.sleep(t)
    def screen(s): return '\n'.join(s.q({'cmd':'screen'})['lines'])
    def wait(s,txt,t=8):
        t0=time.time()
        while time.time()-t0<t:
            if txt in s.screen(): return True
            time.sleep(0.1)
        return False
    def die(s,score,level):
        s.poke(0x63,[score&0xFF,score>>8]); s.poke(0xA7,[level]); s.poke(0x4E,[1]); s.poke(0x67,[1])
    def quit(s):
        try: s.q({'cmd':'quit'})
        except Exception: pass
        time.sleep(0.5); s.p.kill()
def sector(path): return open(path,'rb').read()[15*256:16*256]
def table(b): return [(bytes(x&0x7F for x in b[i*8:i*8+3]).decode(),'%02X%02X'%(b[i*8+4],b[i*8+3]),'%02X'%b[i*8+5]) for i in range(5)]
def valid(b):
    x=0
    for v in b[:44]: x^=v
    return b[40:43]==b'RF\x01' and x==0
# ---------- 1. save ----------
DSK='/tmp/rf_save_%s.dsk'%MACH; shutil.copy(D+'/disk/rockfall.dsk',DSK)
e=Emu(DSK); time.sleep(6)
ok(e.wait('1. A2D  0250  LV04',20),'fresh disk: default table on the title')
e.key(' ',1.5); e.die(0x175,3)
ok(e.wait('ENTER YOUR INITIALS'),'qualifying score -> initials'); time.sleep(0.3)
t0=time.time(); e.key('R'); e.key('C'); e.q({'cmd':'keys','text':'G'})
saw_saving=False
while time.time()-t0<8:
    sc=e.screen()
    if 'SAVING' in sc: saw_saving=True
    if 'ANY KEY: PLAY AGAIN' in sc: break
    time.sleep(0.02)
print('initials -> table screen in %.2fs (saw SAVING...: %s)'%(time.time()-t0,saw_saving))
sc=e.screen(); err=e.peek(0xB1,1)[0]; ram=e.peek(0x1B00,256)
ok(err==0 and 'NOT SAVED' not in sc,'save reported OK (SAVERR=0)')
t1=time.time(); sec=sector(DSK)
while sec==ORIG[15*256:16*256] and time.time()-t1<6: time.sleep(0.2); sec=sector(DSK)
print('disk image changed %.1fs after the table appeared (bobbin syncs at motor spin-down)'%(time.time()-t1))
print('sector T0 S15 on disk:',table(sec)); print('table in RAM:        ',table(ram))
ok(sec[:44]==ram[:44] and valid(sec),'T0/S15 bytes in the .dsk == $1B00 table, valid check bytes')
ok(table(sec)[1]==('RCG','0175','03'),'saved entry #2 = RCG 0175 LV03')
img=open(DSK,'rb').read(); diff=[i for i in range(len(img)) if img[i]!=ORIG[i]]
ok(all(15*256<=i<16*256 for i in diff),'nothing outside T0/S15 changed (%d bytes differ, all in the sector)'%len(diff))
e.key('A',1.5); ok(not e.peek(0x67,1)[0],'game continues after the save')
e.quit()
# ---------- 2. reboot ----------
e=Emu(DSK); time.sleep(6); e.wait('R O C K F A L L',35); time.sleep(0.3); sc=e.screen(); print('== title after reboot ==\n'+'\n'.join(l for l in sc.split('\n') if l.strip()))
ok('2. RCG  0175  LV03' in sc and '1. A2D  0250  LV04' in sc,'reboot: saved table loaded from disk')
ok(table(e.peek(0x1B00,48))==table(sec),'reboot: $1B00 == saved sector')
# second save on the same disk (new #1), then reboot again
e.key(' ',1.5); e.die(0x400,6); ok(e.wait('ENTER YOUR INITIALS'),'second qualifying score'); time.sleep(0.3)
e.key('T'); e.key('O'); e.key('P'); ok(e.wait('ANY KEY: PLAY AGAIN'),'second entry done'); time.sleep(2.5); e.quit()
e=Emu(DSK); time.sleep(6); e.wait('R O C K F A L L',35); time.sleep(0.3); sc=e.screen(); ok('1. TOP  0400  LV06' in sc and '3. RCG  0175  LV03' in sc,'second save persisted across reboot')
e.quit()
# ---------- 3. corrupt sector -> defaults ----------
b=bytearray(open(DSK,'rb').read()); b[15*256+3]^=0x11; open(DSK,'wb').write(b)
e=Emu(DSK); time.sleep(6); e.wait('R O C K F A L L',35); time.sleep(0.3); sc=e.screen(); ok('1. A2D  0250  LV04' in sc and 'TOP' not in sc,'bad check byte -> defaults')
e.quit()
# ---------- 4. write protected ----------
DWP='/tmp/rf_wp_%s.dsk'%MACH; shutil.copy(D+'/disk/rockfall.dsk',DWP)
e=Emu(DWP,wp=True); time.sleep(6); e.key(' ',1.5); e.die(0x300,4)
ok(e.wait('ENTER YOUR INITIALS'),'WP: initials entry'); time.sleep(0.3)
t0=time.time(); e.key('W'); e.key('P'); e.key('X'); ok(e.wait('ANY KEY: PLAY AGAIN'),'WP: no hang (table screen after %.1fs)'%(time.time()-t0))
sc=e.screen(); print('== WP screen ==\n'+'\n'.join(l for l in sc.split('\n') if l.strip()))
ok('DISK WRITE PROTECTED - NOT SAVED' in sc and e.peek(0xB1,1)[0]==1,'WP: message shown, SAVERR=1')
ok(table(e.peek(0x1B00,48))[0]==('WPX','0300','04') and '1. WPX  0300  LV04' in sc,'WP: scores kept in memory')
time.sleep(2.5); ok(open(DWP,'rb').read()==ORIG,'WP: disk image unchanged')
e.key('A',1.5); ok(not e.peek(0x67,1)[0],'WP: next game starts')
e.die(0x10,1); time.sleep(3); sc=e.screen(); ok('NOT SAVED' not in sc,'WP message cleared on a non-qualifying game over')
e.quit()
print('RESULT:','PASS' if not FAIL else 'FAIL %s'%FAIL)
