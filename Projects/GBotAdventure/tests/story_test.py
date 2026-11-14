#!/usr/bin/env python3
"""Twist two in Bobbin, driven fast with state pokes and real keys: the
substation door (sealed until the console is in phase), the main breaker's
choice, the REFUSE path to its hook (trickle lead -> time chamber -> TO BE
CONTINUED), the RESTORE rerun (strobe, loop reset, LOOPS counter, the lines
that remember it), a muted second rerun, and the new doors' timing.
Usage: python3 tests/story_test.py [enhanced|plus]"""
import json,os,pty,re,socket,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
machine=sys.argv[1] if len(sys.argv)>1 else 'enhanced'
lbl=(ROOT/'build/gbot.lbl').read_text()
def sym(n):return int(re.search(r'al ([0-9A-F]+) \.'+n+r'\b',lbl).group(1),16)
MAIN,FLASH=sym('main'),sym('flash_shot')
PX,REPAIR,MESSAGE,FEEDBACK,ROOM,PANEL,FUSE,GSTATE,LABOPEN,CONSOLE,TUNESTEP,TUNEPOS,TALK=0x70,0x83,0x85,0x88,0x8A,0x8C,0x8D,0x92,0x9D,0xA9,0xAA,0xAB,0xAC
SOUNDOFF,SPKCNT,JINGLES,LOOPS,CHOICE,REFUSED,LEAD,WAKE=0xB7,0xBF,0xC1,0xCB,0xCC,0xCD,0xCE,0xCF
NAMES=('workshop','power','security','lab','substation')
failures=[]
def ok(c,d):
    print(('PASS ' if c else 'FAIL ')+d,flush=True)
    if not c:failures.append(d)
with tempfile.TemporaryDirectory() as tmp:
    disk=tmp+'/d.dsk';Path(disk).write_bytes((ROOT/'disk/gbot-after-hours.dsk').read_bytes());sock=tmp+'/s'
    m,s=pty.openpty()
    p=subprocess.Popen(['/workspace/apple2/bin/bobbin-ai','--simple','--remain','--no-turbo','-m',machine,'--disk',disk,'--control-socket',sock],stdin=s,stdout=s,stderr=s,start_new_session=True);os.close(s)
    def q(c):
        with socket.socket(socket.AF_UNIX) as k:
            k.settimeout(120);k.connect(sock);k.sendall(json.dumps(c).encode()+b'\n');o=b''
            while not o.endswith(b'\n'):o+=k.recv(65536)
        return json.loads(o)
    def until_paused(t=120):
        end=time.monotonic()+t
        while time.monotonic()<end:
            try:
                r=q({'cmd':'cpu'})
                if r['paused']:return r
            except OSError:pass
            time.sleep(.005)
        raise RuntimeError('timeout')
    def now(r):return r['frames']*17030+r['cycles']
    def peek(a,n=1):return b''.join(bytes(q({'cmd':'peek','addr':x,'len':min(4096,a+n-x)})['data']) for x in range(a,a+n,4096))
    def b(a):return peek(a)[0]
    def poke(a,d):q({'cmd':'poke','addr':a,'data':d})
    def spk():x,y=peek(SPKCNT,2);return x|y<<8
    door_msgs=[]
    def step(key=None):
        """One main-loop tick; returns its cycles. Stops at a disk read to see
        the door's status line."""
        if key:q({'cmd':'keys','text':key})
        r0=q({'cmd':'cpu'});t0=now(r0)
        q({'cmd':'break_set','addr':0x0808})
        while True:
            q({'cmd':'resume'});r=until_paused()
            if r['pc']==0x0808:door_msgs.append(b(MESSAGE));continue
            break
        q({'cmd':'break_clear','addr':0x0808})
        return now(r)-t0
    shots=[]
    def shot(name):
        sys.path.insert(0,str(ROOT/'tools'));from gen_concept import decode
        from PIL import Image
        mem=peek(0x2000+b(0x76)*8192,8192);path=ROOT/'screenshots'/('story_%s_%s.png'%(name,machine))
        image=decode(mem);image.save(path.with_name(path.stem+'-280.png'))
        image.resize((1120,768),Image.Resampling.NEAREST).save(path);shots.append(path)
        print('SCREENSHOT '+str(path),flush=True)
    def frames(n):
        for _ in range(n):step()
    def door(nxt,x,y,d):
        poke(0x98,[nxt,x,y,d]);poke(0x8B,[1]);t=step()
        if b(ROOM)!=nxt:raise AssertionError('door to %d failed'%nxt)
        frames(4);return t
    def at(x,y,d):poke(PX,[x,y,d,0]);frames(2)
    def hide():poke(0xA6,[0,250,0]);poke(FEEDBACK,[0])
    def runs_to(msg,limit=400):
        seen=[b(MESSAGE)]
        for _ in range(limit):
            step()
            if b(MESSAGE)!=seen[-1]:seen.append(b(MESSAGE))
            if seen[-1]==msg:break
        return seen
    try:
        while True:
            try:q({'cmd':'ping'});break
            except OSError:time.sleep(.05)
        q({'cmd':'break_set','addr':MAIN});until_paused()
        frames(3)
        poke(REPAIR,[3]);poke(PANEL,[3]);poke(FUSE,[2]);poke(LABOPEN,[1])
        frames(2)
        door(1,122,120,3);ok(b(ROOM)==1,'to the lit power room')
        # 1) the substation door: sealed until the console is in phase
        at(224,104,2);step('D');frames(2)
        ok(b(ROOM)==1 and b(MESSAGE)==66,'east door: SUBSTATION SEALED - NEEDS LAB OK (console still drifting)')
        poke(CONSOLE,[3]);poke(FEEDBACK,[0]);at(224,104,2)
        t_in=None
        q({'cmd':'keys','text':'D'});t_in=step();frames(4)
        ok(b(ROOM)==4 and tuple(peek(PX,3))==(14,90,2),'console in phase: the east door opens into the substation (14,90 facing east)')
        ok(door_msgs[-1]==65,'door line: ENTERING SUBSTATION... (from the story bank)')
        ok(b(MESSAGE)==68,'arrival: SUBSTATION: THE BIG SWITCH');shot('1_substation_arrival')
        # 2) the breaker and the choice
        at(120,56,3);ok(b(0x84)==1 and b(MESSAGE)==69,'breaker apron: MAIN BREAKER: SPACE TO PROBE');shot('2_breaker')
        at(120,60,3);step('W');frames(4);ok(b(0x71)==56,'cabinet front stops G-Bot at y=56')
        at(120,56,3);step(' ');frames(2);ok(b(CHOICE)==1 and b(MESSAGE)==70,'Space: RESTORE FULL POWER?  Y YES / N NO');shot('3_choice_prompt')
        step('\x1b');frames(1);ok(b(CHOICE)==0 and b(MESSAGE)==69,'Escape cancels the choice')
        step(' ');frames(2);step('S');frames(6);ok(b(CHOICE)==0,'walking away cancels the choice')
        at(120,56,3);step(' ');frames(9)
        for k in 'ABCQ':step(k)
        ok(b(CHOICE)==1 and b(LOOPS)==0 and b(REFUSED)==0,'other keys do not answer it')
        # 3) REFUSE
        step('N');frames(1)
        ok(b(REFUSED)==1 and b(LEAD)==1 and b(MESSAGE)==75,'N: G-BOT: NO. SHE SAID NO FULL POWER. -- he takes the trickle lead');shot('4_refuse')
        seq=runs_to(77);shot('5_refuse_new_task');ok(seq[-2:]==[76,77],'...BUT THIS TRICKLE LEAD MIGHT HELP. -> NEW TASK: TRICKLE LEAD TO THE CHAMBER (%s)'%seq)
        frames(70);at(200,104,1);ok(b(MESSAGE)==78,'away from the breaker: BREAKER STAYS OFF. SHE WAS RIGHT.')
        # back to the lab with the lead
        t_out=door(1,224,104,1)
        ok(b(ROOM)==1,'substation -> power room')
        door(2,224,104,1);poke(0x8F,[3,1,0]);door(3,122,120,3);hide()
        at(122,60,3);ok(b(0x84)==1 and b(MESSAGE)==92,'chamber with the lead: CHAMBER: SPACE TO PLUG IN THE LEAD')
        j0=b(JINGLES);step(' ');frames(1)
        ok(b(LEAD)==2 and b(MESSAGE)==85 and b(JINGLES)==j0+1,'Space: TRICKLE LEAD IN. THE RING TICKS ONCE. (stinger)')
        seq=runs_to(89,600);ok(seq==[85,86,87,88,89],'the lead runs on to the hook: %s'%seq)
        ok(b(JINGLES)==j0+2,'TO BE CONTINUED plays its stinger');shot('6_to_be_continued')
        frames(60);hide();at(30,56,3);step(' ');frames(1);ok(b(MESSAGE)==93,'console after the lead: CONSOLE: LOOP HOLDS. 6:03 AND TICKING')
        frames(60);hide();at(122,60,3);step(' ');frames(1);ok(b(MESSAGE)==91,'chamber again: CHAMBER: 6:03. NEXT MINUTE... SOON.')
        # 4) RESTORE: back to the breaker, Y
        frames(60);at(122,106,0);door(2,122,48,0);door(1,14,90,2);door(4,14,90,2)
        at(120,56,3);step(' ');frames(2)
        q({'cmd':'break_set','addr':FLASH});q({'cmd':'keys','text':'Y'});q({'cmd':'resume'});r=until_paused()
        ok(r['pc']==FLASH,'Y: the rerun strobe starts')
        page=b(0x76);shown=peek(0x2000+page*8192,8192);other=peek(0x2000+(page^1)*8192,8192)
        inv=sum(1 for a,c in zip(shown,other) if (a^c)&127==127)
        ok(inv>7000,'the flash shows the room negative (%d of 8192 bytes inverted)'%inv);shot('7_restore_flash')
        q({'cmd':'break_clear','addr':FLASH})
        n=len(door_msgs);t_wake=step()
        ok(b(ROOM)==0 and tuple(peek(PX,3))==(126,104,0),'the loop resets: G-Bot wakes in the workshop')
        ok(door_msgs[n:]==[72],'its door line: G-BOT REBOOTING... 12:15 AGAIN')
        ok(b(LOOPS)==1 and b(MESSAGE)==73,'LOOPS=1; G-BOT: ...THAT WAS A BAD IDEA. AGAIN.');shot('8_restore_wake')
        ok((b(REPAIR),b(PANEL),b(FUSE),b(LABOPEN))==(3,3,2,1),'the machines remember him: workbench, fuse and lab door stay fixed')
        ok((b(CONSOLE),b(GSTATE),b(LEAD),b(REFUSED),b(WAKE))==(0,0,0,0,0),'the console drifts again, the guard will reboot, the lead is back on its hook')
        frames(4)
        door(1,122,120,3);at(224,104,2);step('D');frames(2);ok(b(ROOM)==1 and b(MESSAGE)==66,'the substation is sealed again until she is heard')
        door(2,224,104,1);frames(2);ok(b(GSTATE)==1 and b(MESSAGE)==23,'the guard reboots')
        poke(0x8F,[3,1,0]);door(3,122,120,3);hide()
        at(30,56,3);step(' ');frames(1);ok(b(MESSAGE)==79 and b(CONSOLE)==1,'CONSOLE: LOOP 4,818. PHASE DRIFT!')
        poke(CONSOLE,[2]);poke(TUNESTEP,[2]);poke(TUNEPOS,[9]);poke(FEEDBACK,[0]);step('R')
        ok(b(CONSOLE)==3 and b(TALK)==1 and b(MESSAGE)==81,'in phase again: SCIENTIST: G-BOT! WAIT. AGAIN?');shot('9_scientist_again')
        seq=runs_to(67,900);ok(seq==[81,82,83,55,56,57,67],'she remembers, warns again, is cut off again: %s'%seq)
        # 5) a second rerun, muted
        frames(100);at(122,106,0);door(2,122,48,0);door(1,14,90,2)
        step('M');frames(2);ok(b(SOUNDOFF)==1,'M: sound off')
        door(4,14,90,2);at(120,56,3);step(' ');frames(2);s0=spk();t_wake2=step('Y')
        ok(b(ROOM)==0 and b(LOOPS)==2 and b(MESSAGE)==74,'second rerun: LOOPS=2; G-BOT: ...STILL A BAD IDEA. AGAIN.')
        ok(spk()==s0,'sound off: the rerun and the wake make no speaker clicks')
        frames(4);door(1,122,120,3);door(2,224,104,1);poke(0x8F,[3,1,0]);door(3,122,120,3);hide()
        at(30,56,3);step(' ');frames(1);ok(b(MESSAGE)==80,'CONSOLE: LOOP 4,8??. YOU AGAIN?!')
        poke(CONSOLE,[2]);poke(TUNESTEP,[2]);poke(TUNEPOS,[9]);poke(FEEDBACK,[0]);step('R')
        ok(b(MESSAGE)==84,'SCIENTIST: AGAIN?! STOP FLIPPING IT!')
        # 6) door timing
        print('DOOR power -> substation %d cycles (%.2f s); substation -> power %d (%.2f s); wake after the flash %d (%.2f s), whole muted rerun %d (%.2f s)'%(t_in,t_in/1020484,t_out,t_out/1020484,t_wake,t_wake/1020484,t_wake2,t_wake2/1020484),flush=True)
        ok(t_in<1500000 and t_out<1500000,'substation doors under 1.5 s with a motif')
    finally:
        p.terminate();p.wait(timeout=5);os.close(m)
print('RESULT: '+('FAIL' if failures else 'PASS'),flush=True)
raise SystemExit(bool(failures))
