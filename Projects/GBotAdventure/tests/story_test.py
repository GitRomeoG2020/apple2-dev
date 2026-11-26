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
SOUNDOFF,SPKCNT,JINGLES,LOOPS,CHOICE,REFUSED,LEAD,WAKE,HESIT,DEJA=0xB7,0xBF,0xC1,0xCB,0xCC,0xCD,0xCE,0xCF,0xD0,0xD1
NAMES=('workshop','power','security','lab','substation','wingb')
MINUTE,GMET,GX,CAMJOB,PAGES=0xD2,0xD3,0x8F,0xD5,0xD6
sys.path.insert(0,str(ROOT/'tools'))
from gen_workshop import clock_icon,fuse_icon,page_icon,message_pixels,CHAPTER,GOALS
from gen_chapter import patches
PATCH={n:(bx,bytes(d)) for n,bx,d in patches()}
from gen_concept import row_offset
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
    def hud():
        """Which carried icon both pages show in status columns 38-39."""
        got=set()
        for pg in (0x2000,0x4000):
            rows=[peek(pg+row_offset(177+r)+38,2) for r in range(5)]
            got.add('clock' if rows==clock_icon() else 'fuse' if rows==fuse_icon() else 'page' if rows==page_icon() else None)
        return got.pop() if len(got)==1 else 'mixed'
    def labclock():
        """The lab clock's last digit, if $8000 and both pages agree."""
        cols=[bytes(b(base+row_offset(169+r)+38) for r in range(5)) for base in (0x8000,0x2000,0x4000)]
        for d in '0123456789':
            want=bytes(message_pixels(d)[r][19] for r in range(5))
            if all(c==want for c in cols):return d
        return None
    def shows(name,bases=(0x8000,)):
        """Does the room (and the given pages) hold chapter patch `name`?"""
        (c0,w,r0,h),data=PATCH[name]
        return all(b''.join(peek(base+row_offset(r0+r)+c0,w) for r in range(h))==data for base in bases)
    def frames(n):
        for _ in range(n):step()
    def door(nxt,x,y,d):
        poke(0x98,[nxt,x,y,d]);poke(0x8B,[1]);t=step()
        if b(ROOM)!=nxt:raise AssertionError('door to %d failed'%nxt)
        frames(4);return t
    def at(x,y,d):poke(PX,[x,y,d,0]);frames(2)
    def hide():poke(0xA6,[0,250,0]);poke(FEEDBACK,[0])
    def hesitate(want_msg,shoot=None):
        """Space at the breaker, first time this loop: the deja-vu glitch,
        then the prompt. Returns (ticks, cycles, poses seen, sfx id)."""
        t=step(' ');ticks=1;poses=[b(0x77)];msg=b(MESSAGE);h=b(HESIT);c0=b(CHOICE);fx=b(0xC4)
        ok(msg==want_msg and h==1 and c0==0,'first probe this loop: message %d, no prompt yet (got %d, HESIT %d, CHOICE %d)'%(want_msg,msg,h,c0))
        while b(CHOICE)==0 and ticks<80:
            t+=step();ticks+=1;poses.append(b(0x77));fx=8 if b(0xC4)==8 else fx
            if shoot and ticks==7:shot(shoot)
        return ticks,t,poses,fx
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
        # 0) T: G-Bot's current goal, one per progress state (pokes; the
        # workshop at boot). Some goals run on to a second line of directions.
        def goal(want,why):
            hide();step('T');frames(1);got=[b(MESSAGE)]
            if len(want)>1:got=runs_to(want[-1],300)
            ok(got==list(want),'T, %s: %s (%s)'%(why,' / '.join(CHAPTER[w] for w in want),[hex(g) for g in got]))
        ok(b(MESSAGE)==0,'boot: WORKBENCH OFFLINE - CHECK LEFT BENCH (the controls line offers T:TASK)')
        TSTATES=[((0,0,0,0,0,0,0,0),(0xE0,),'at boot'),((3,0,0,0,0,0,0,0),(0xE1,),'workbench fixed'),
                 ((3,1,0,0,0,0,0,0),(0xE2,),'carrying the fuse'),((3,2,0,0,0,0,0,0),(0xE3,0xE4),'power on'),
                 ((3,2,1,0,0,0,0,0),(0xE5,0xE6),'lab door open'),((3,2,1,3,0,0,0,0),(0xE7,0xE8),'she warned him (points at N, no Y needed)'),
                 ((3,2,1,3,1,0,0,0),(0xE9,),'carrying the lead'),((3,2,1,3,2,1,0,0),(0xEA,0xEB),'carrying the minute'),
                 ((3,2,1,3,2,2,0,0),(0xEC,0xED),'the guard awake, monitors snowed'),((3,2,1,3,2,2,3,0),(0xEE,),'cameras fixed'),
                 ((3,2,1,3,2,3,3,0),(0xEF,0xF0),'the second minute'),((3,2,1,3,2,4,3,0),(0xF1,),'the coffee awake'),
                 ((3,2,1,3,2,4,3,1),(0xF2,0xF3),'the page'),((3,2,1,0,0,0,3,1),(0xE5,0xE6),'after a Y rerun (page kept)'),
                 ((3,2,1,3,0,0,3,1),(0xE7,0xE8),'a rerun, warned again: still N')]
        for st,want,why in TSTATES:
            for a,v in zip((REPAIR,FUSE,LABOPEN,CONSOLE,LEAD,MINUTE,CAMJOB,PAGES),st):poke(a,[v])
            goal(want,why)
            if why=='at boot':frames(2);shot('22_goal_at_boot')
        for a in (REPAIR,FUSE,LABOPEN,CONSOLE,LEAD,MINUTE,CAMJOB,PAGES):poke(a,[0])
        hide();poke(REPAIR,[1]);step('T');frames(1)
        ok(b(MESSAGE) not in GOALS and b(FEEDBACK)==0,'T with a prompt up (an inspected job) does nothing')
        poke(REPAIR,[0]);frames(2)
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
        at(120,56,3);ticks,cyc,poses,fx=hesitate(94,'2_hesitation')
        ok(13 in poses and 12 in poses and 0 in poses and poses.index(13)<poses.index(12),'the glitch: probe arm up, stalls, eyes flicker (poses %s)'%poses)
        ok(510000<=cyc<=1100000,'it lasts %.2f s (%d ticks), then the prompt'%(cyc/1020484,ticks))
        ok(fx==8,'a crackle plays as he glitches (sound on)')
        ok(b(MESSAGE)==70 and b(DEJA)==1,'then: RESTORE FULL POWER?  Y YES / N NO');frames(2);shot('3_choice_prompt')
        print('HESITATION %d ticks, %d cycles (%.2f s)'%(ticks,cyc,cyc/1020484),flush=True)
        step('\x1b');frames(1);ok(b(CHOICE)==0 and b(MESSAGE)==69,'Escape cancels the choice')
        step(' ');frames(2);ok(b(CHOICE)==1 and b(HESIT)==0 and b(MESSAGE)==70,'the second probe in the same loop asks at once (no deja vu)');step('\x1b');frames(1)
        step(' ');frames(2);step('S');frames(6);ok(b(CHOICE)==0,'walking away cancels the choice')
        at(120,56,3);step(' ');frames(9)
        for k in 'ABCQT':step(k)
        ok(b(CHOICE)==1 and b(LOOPS)==0 and b(REFUSED)==0 and b(MESSAGE)==70,'other keys (T too) do not answer it or hide it')
        # 3) REFUSE
        step('N');frames(1)
        ok(b(REFUSED)==1 and b(LEAD)==1 and b(MESSAGE)==75,'N: G-BOT: NO. SHE SAID NO FULL POWER. -- he takes the trickle lead');shot('4_refuse')
        seq=runs_to(77);shot('5_refuse_new_task');ok(seq[-2:]==[76,77],'...BUT THIS TRICKLE LEAD MIGHT HELP. -> NEW TASK: TRICKLE LEAD TO THE CHAMBER (%s)'%seq)
        seq=runs_to(0xD8,300);ok(seq==[77,0xD8],'G-Bot thinks out loud: G-BOT: THE LAB CHAMBER! PLUG THIS IN. (%s)'%seq)
        frames(70);hide();at(200,104,1);ok(b(MESSAGE)==78,'away from the breaker: BREAKER STAYS OFF. SHE WAS RIGHT.')
        # back to the lab with the lead
        t_out=door(1,224,104,1)
        ok(b(ROOM)==1,'substation -> power room')
        door(2,224,104,1);poke(0x8F,[3,1,0]);door(3,122,120,3);hide()
        at(30,56,3);step(' ');frames(1);seq=runs_to(97,250)
        ok(seq[0]==90 and 97 not in seq,'after N the console says CONSOLE: BREAKER OFF. GOOD BOT. and no substation hint (%s)'%seq)
        frames(30);hide()
        at(122,60,3);ok(b(0x84)==1 and b(MESSAGE)==92,'chamber with the lead: CHAMBER: SPACE TO PLUG IN THE LEAD')
        j0=b(JINGLES);step(' ');frames(1)
        ok(b(LEAD)==2 and b(MESSAGE)==85 and b(JINGLES)==j0+1,'Space: TRICKLE LEAD IN. THE RING TICKS ONCE. (stinger)')
        seq=runs_to(99,700);ok(seq==[85,86,87,88,89,98,99],"the lead runs on: ...ONE MINUTE! ...CARRY TIME, G-BOT. G-BOT: I'M... TICKING? SCIENTIST: TAKE IT TO SOMETHING STUCK, NEW TASK: UNSTICK SOMETHING FROZEN (%s)"%seq)
        ok(b(JINGLES)==j0+2 and b(0xC4)==23,'I\'M... TICKING? plays a tick, tock')
        ok(b(MINUTE)==1,'the chamber charged him with one carried minute')
        frames(2);ok(hud()=='clock','the HUD shows a little clock (not the lead) on both pages')
        ok(labclock()=='3','the lab HUD clock now says 6:03');shot('6_carrying_time')
        seq=runs_to(0xD9,300);ok(seq==[99,0xD9],'...G-BOT: THE GUARD IS STUCK. BUMP HIM! (%s)'%seq);frames(2);shot('24_think_aloud_guard')
        frames(60);hide();at(30,56,3);step(' ');frames(1);ok(b(MESSAGE)==93,'console while carrying: CONSOLE: LOOP HOLDS. 6:03 AND TICKING')
        frames(60);hide();at(122,60,3);step(' ');frames(1);ok(b(MESSAGE)==100,'chamber: CHAMBER: ONE MINUTE CARRIED. GO!')
        # 3b) CARRYING TIME: the guard remembers
        frames(60);at(122,106,0);door(2,122,48,0);poke(GSTATE,[2]);frames(2);hide();at(150,104,1);frames(2)
        ok(b(MESSAGE)==102,'security, carrying the minute: G-BOT: THE GUARD... IS STUCK TOO.')
        at(14,110,1);step('A');frames(1);ok(b(ROOM)==2 and b(MESSAGE)==107,'the new west door: WING B SEALED - GUARD HAS THE CODE');shot('10_wing_b_sealed')
        frames(70);j0=b(JINGLES);gx=b(GX);at(gx*7,80,0)
        ok(b(GSTATE)==3 and b(MINUTE)==2 and b(GMET)==1 and b(ROOM)==2 and b(PX+1)==80,'touching the guard with the minute: no zap, he stops for good')
        ok(b(MESSAGE)==103 and b(JINGLES)==j0+1,'GUARD: BEEP? WHERE DID THE NIGHT GO? (tick)');gx=b(GX);at(gx*7-34 if gx*7-34>=14 else gx*7+30,84,2 if gx*7-34>=14 else 1);shot('11_guard_remembers')
        ok(hud() is None,'the minute is spent: the HUD clock clears')
        seq=runs_to(106,600);ok(seq==[103,104,105,106],'GUARD: G-BOT! YOU KEEP PASSING ME! / WING B CODE IS 6-0-4. GO ON. / THE MINUTE IS SPENT. WING B UNSEALED. (%s)'%seq)
        ok(b(JINGLES)==j0+2,'the unseal plays the unlock stinger')
        seq=runs_to(0xDA,300);ok(seq==[106,0xDA],'...G-BOT: HIS MONITORS DIED. HIS DESK? (%s)'%seq)
        gx=b(GX);frames(40);ok(b(GX)==gx,'the guard stays put')
        at(b(GX)*7,80,1);frames(6);ok(b(PX)==b(GX)*7 and b(PX+1)==80,'and catches nobody any more')
        frames(70);hide();at(150,104,1);frames(2);ok(b(MESSAGE)==0xB8,'security now: GUARD: MY MONITORS! ALL STATIC!')
        ok(shows('static',(0x8000,0x2000,0x4000)),'waking him turned his monitor wall to snow (room and both pages)')
        hide();step('T');frames(2);ok(b(MESSAGE)==0xEC,"T in security, guard awake (real flags): GOAL: FIX THE GUARD'S DESK MONITORS");shot('23_goal_monitors')
        frames(120);hide()
        # 3c) WING B
        n=len(door_msgs);at(14,110,1);t0=step('A');t_wing=t0;frames(4)
        ok(b(ROOM)==5 and tuple(peek(PX,3))==(224,110,1),'west door: into WING B (224,110 facing west)')
        ok(door_msgs[n:]==[109],'door line: ENTERING WING B...')
        ok(b(MESSAGE)==111,'WING B: THE ARCHIVE, STOPPED AT 3:07');shot('12_wing_b')
        at(120,60,3);step('W');frames(4);ok(b(PX+1)==56,'the coffee counter is solid (G-Bot stops at y=56)')
        at(120,56,3);ok(b(0x84)==1 and b(MESSAGE)==112,'COFFEE MACHINE: SPACE TO PROBE')
        j0=b(JINGLES);step(' ');frames(1);ok(b(MESSAGE)==114,'Space: A DROP OF COFFEE, FROZEN IN MIDAIR.')
        seq=runs_to(116,600);ok(seq==[114,115,116],'G-BOT: THAT WILL TAKE ANOTHER MINUTE. / ...MAYBE THE CHAMBER HAS ONE MORE? (the hint; %s)'%seq)
        ok(b(JINGLES)==j0 and b(0xC4)==2,'the hint chimes (no stinger: not the end any more)');at(56,60,2);shot('13_coffee_hint')
        seq=runs_to(0xDB,300);ok(seq==[116,0xDB],"...G-BOT: FIRST, FIX THE GUARD'S DESK. (cameras still down; %s)"%seq)
        frames(70);hide();at(200,56,3);ok(b(0x84)==2 and b(MESSAGE)==113,'LOOP LOG: SPACE TO PROBE')
        step(' ');frames(1);seq=runs_to(118,300);ok(seq==[117,118],"LOOP LOG: 4,817 TALLY MARKS. NEAT. / LAST ENTRY: DON'T FLIP THE BREAKER. (%s)"%seq)
        frames(70);n=len(door_msgs);at(224,110,2);t_wback=step('D');frames(4)
        ok(b(ROOM)==2 and tuple(peek(PX,3))==(14,110,2) and door_msgs[n:]==[61],'east door: back to security (14,110 facing east)')
        # 3d) THE SECOND MINUTE: the chamber is empty; security's monitors
        ok(shows('static'),'security: the monitor wall is snow since the guard woke (arrival patch in $8000)')
        door(3,122,120,3);hide();frames(2);ok(labclock()=='4','the lab HUD clock now says 6:04')
        at(30,56,3);step(' ');frames(1);ok(b(MESSAGE)==101,'console: CONSOLE: 6:04! SOMETHING WOKE UP.')
        seq=runs_to(0xDD,400);ok(seq==[101,0xB1,0xDD],"...CONSOLE: SECURITY MONITORS: NO SIGNAL / G-BOT: THE GUARD'S DESK. LOOSE CABLE? (%s)"%seq)
        frames(60);hide();at(122,60,3);step(' ');frames(1);ok(b(MESSAGE)==0xB0 and b(MINUTE)==2,'chamber: CHAMBER: EMPTY. FIX SOMETHING NEARBY.')
        seq=runs_to(0xB1,300);ok(seq==[0xB0,0xB1],'...CONSOLE: SECURITY MONITORS: NO SIGNAL (%s)'%seq)
        frames(60);at(122,106,0);door(2,122,48,0);frames(2)
        ok(shows('static'),'security again: still snow')
        at(150,104,1);frames(2);ok(b(MESSAGE)==0xB8,'security: GUARD: MY MONITORS! ALL STATIC!');shot('15_monitors_static')
        at(40,56,3);ok(b(0x84)==1 and b(MESSAGE)==26,'the desk: SECURITY DESK: SPACE TO PROBE')
        step(' ');frames(2);ok(b(CAMJOB)==1 and b(MESSAGE)==0xB9,'Space: MONITORS: STATIC! R RECONNECT / ESC')
        step('\x1b');frames(1);ok(b(CAMJOB)==0,'Escape cancels')
        step(' ');frames(2);at(150,104,1);frames(2);ok(b(CAMJOB)==0,'walking away cancels too')
        at(40,56,3);step(' ');frames(2);j0=b(JINGLES);step('R');frames(1)
        ok(b(CAMJOB)==2 and b(MESSAGE)==0xBA,'R: RECONNECTING CAMERAS... HOLD STILL');shot('16_reconnecting')
        for _ in range(40):
            if b(CAMJOB)==3:break
            step()
        frames(1);ok(b(CAMJOB)==3 and b(JINGLES)==j0+1 and b(0xC4)==10,'the cameras are back: the repair jingle')
        ok(b(MESSAGE)==0xBB,'GUARD: I CAN SEE! THANKS, G-BOT.')
        ok(shows('feeds'),'the feeds are back in the room ($8000)')
        at(150,104,1);frames(3);ok(shows('feeds',(0x8000,0x2000,0x4000)),'...and on both pages')
        at(40,60,1);shot('17_i_can_see')
        seq=runs_to(0xDE,500);ok(seq==[0xBB,0xBC,0xBD,0xDE],'GUARD: CAMERA 4... A FLOATING DROP? / ...FAR AWAY, THE CHAMBER RECHARGES. / G-BOT: BACK TO THE LAB CHAMBER, THEN. (%s)'%seq)
        frames(70);hide();at(150,104,1);frames(2);ok(b(MESSAGE)==108,'security now: GUARD: OFF DUTY. WING B IS OPEN.')
        door(3,122,120,3);hide();frames(2)
        at(30,56,3);step(' ');frames(1);ok(b(MESSAGE)==0xB5,'console: CONSOLE: CAMERAS UP. CHAMBER CHARGED.')
        frames(60);hide();at(122,60,3);j0=b(JINGLES);step(' ');frames(1)
        ok(b(MINUTE)==3 and b(MESSAGE)==0xB2 and b(JINGLES)==j0+1,'chamber: CHAMBER: CHARGED! A SECOND MINUTE. (tick)')
        frames(2);ok(hud()=='clock','the HUD clock is back');shot('18_second_minute')
        seq=runs_to(0xDF,500);ok(seq==[0xB2,0xB3,0xB4,0xDF],"G-BOT: TICKING AGAIN. COFFEE TIME? / NEW TASK: WAKE THE COFFEE MACHINE / G-BOT: WING B. SECURITY'S WEST DOOR. (%s)"%seq)
        frames(60);hide();at(30,56,3);step(' ');frames(1);ok(b(MESSAGE)==0xB6,'console: CONSOLE: 6:04 AND TICKING. AGAIN!')
        frames(60);hide();at(122,60,3);step(' ');frames(1);ok(b(MESSAGE)==100 and b(MINUTE)==3,'chamber: CHAMBER: ONE MINUTE CARRIED. GO!')
        # 3e) THE SCIENTIST'S NOTES: the coffee wakes
        frames(60);at(122,106,0);door(2,122,48,0);door(5,224,110,1);frames(2)
        at(120,56,3);j0=b(JINGLES);t0=step(' ');frames(1)
        ok(b(MINUTE)==4 and b(MESSAGE)==0xC0 and b(JINGLES)==j0+1 and b(0xC4)==25,'the second minute: ...PLIP! THE DROP FINALLY LANDS. (the drop falls: %.2f s)'%(t0/1020484))
        ok(shows('awake'),'the coffee machine is awake: scowl, full cup, steam ($8000)')
        ok(hud() is None and b(PAGES)==0,'the HUD clock clears; no page yet')
        seq=runs_to(0xC5,900);ok(seq==[0xC0,0xC1,0xC2,0xC3,0xC4,0xC5],'COFFEE: FINALLY! 4,817 NIGHTS OF DRIP / SHE ALWAYS SAID ONE MORE CUP. / THEN 11:59:59. THEN NOTHING. / SHE LEFT THIS IN MY FILTER. / GOT A NOTEBOOK PAGE! (%s)'%seq)
        frames(2);ok(b(PAGES)==1 and hud()=='page','the HUD shows the notebook page')
        at(56,60,2);shot('19_notebook_page');at(120,56,3)
        seq=runs_to(0xCA,900);ok(seq==[0xC5,0xC6,0xC7,0xC8,0xC9,0xCA],'PAGE: 11:59:59. FULL POWER. A LOOP. / NOT A FLOOD. A TRICKLE ENDS IT. / I HID THE REST. ROOM BY ROOM. / COFFEE: NOW SHOO. / NEW TASK: FIND THE OTHER PAGES (%s)'%seq)
        j1=b(JINGLES);seq=runs_to(0xCB,300);ok(seq==[0xCA,0xCB],'TO BE CONTINUED: HER MISSING NOTES (%s)'%seq)
        ok(j1==j0+2,'NEW TASK: FIND THE OTHER PAGES plays the hook stinger');at(56,60,2);shot('20_to_be_continued')
        frames(70);hide();at(120,56,3);step(' ');frames(1);ok(b(MESSAGE)==0xCC,'the coffee again: COFFEE: BREWING. GO FIND HER PAGES.')
        frames(70);at(224,110,2);step('D');frames(4);ok(b(ROOM)==2,'back to security')
        door(5,224,110,1);frames(2);ok(shows('awake'),'wing B again: the machine stays awake this loop')
        door(2,14,110,2);ok(shows('feeds'),'security keeps its feeds')
        door(3,122,120,3);hide();frames(2);ok(labclock()=='5','the lab HUD clock now says 6:05')
        at(30,56,3);step(' ');frames(1);ok(b(MESSAGE)==0xB7,'console: CONSOLE: 6:05! SOMEONE IS GRUMPY.')
        frames(60);hide();at(122,60,3);step(' ');frames(1);ok(b(MESSAGE)==91,'chamber: CHAMBER: RECHARGING. NEXT MINUTE SOON')
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
        ok(b(LOOPS)==1 and b(MESSAGE)==0xD1,'LOOPS=1; G-BOT: BAD IDEA. BUT I KEPT THE PAGE.');shot('8_restore_wake')
        seq=runs_to(0xD7,400);ok(seq==[0xD1,0xD7],'...G-BOT: NEXT TIME I LISTEN TO HER. N. (%s)'%seq)
        goal((0xE5,0xE6),'after the rerun (real flags)')
        ok((b(PAGES),b(CAMJOB))==(1,3) and hud()=='page','the page and the cameras survive the rerun (HUD: the page)')
        ok((b(REPAIR),b(PANEL),b(FUSE),b(LABOPEN))==(3,3,2,1),'the machines remember him: workbench, fuse and lab door stay fixed')
        ok((b(CONSOLE),b(GSTATE),b(LEAD),b(REFUSED),b(WAKE),b(MINUTE))==(0,0,0,0,0,0),'the console drifts again, the guard will reboot, the lead is back on its hook, the minute is lost')
        ok(b(GMET)==1,'(but the guard met him once)')
        frames(4)
        door(1,122,120,3);at(224,104,2);step('D');frames(2);ok(b(ROOM)==1 and b(MESSAGE)==66,'the substation is sealed again until she is heard')
        door(2,224,104,1);frames(2);ok(b(GSTATE)==1 and b(MESSAGE)==110,'the guard reboots, faintly: GUARD: ...HAVE WE MET? REBOOTING.');shot('14_have_we_met')
        at(14,110,1);step('A');frames(1);ok(b(ROOM)==2 and b(MESSAGE)==107,'wing B is sealed again')
        # the next night: the guard woken again (poked), the cameras stay fixed
        poke(GSTATE,[3]);poke(MINUTE,[2]);door(1,122,120,3);door(2,224,104,1);frames(2)
        ok(shows('feeds'),'next night, guard awake: no snow (the cameras stayed fixed)')
        door(5,224,110,1);frames(2);ok(not shows('awake'),'wing B: the drop is frozen again')
        at(120,56,3);step(' ');frames(1);ok(b(MESSAGE)==0xCD,'G-BOT: FROZEN AGAIN. I KEPT THE PAGE.')
        seq=runs_to(0xDC,800);ok(seq==[0xCD,115,116,0xDC],'...THAT WILL TAKE ANOTHER MINUTE. / ...MAYBE THE CHAMBER HAS ONE MORE? / G-BOT: THE LAB CHAMBER MUST BE READY! (cameras fixed; %s)'%seq)
        frames(70);poke(MINUTE,[3]);hide();at(120,56,3);step(' ');frames(1)
        ok(b(MESSAGE)==0xCE and b(MINUTE)==4 and shows('awake'),'a second minute again: ...PLIP! THE DROP LANDS. AGAIN.')
        seq=runs_to(0xD0,600);ok(seq==[0xCE,0xCF,0xD0],'COFFEE: YOU AGAIN?! YOU GOT THE PAGE. / ANOTHER NIGHT. SHOO. (%s)'%seq)
        ok(b(PAGES)==1,'(still one page)');at(56,60,2);shot('21_you_again')
        poke(GSTATE,[0]);poke(MINUTE,[0]);door(2,14,110,2)
        poke(0x8F,[3,1,0]);door(3,122,120,3);hide()
        at(30,56,3);step(' ');frames(1);ok(b(MESSAGE)==79 and b(CONSOLE)==1,'CONSOLE: LOOP 4,818. PHASE DRIFT!')
        poke(CONSOLE,[2]);poke(TUNESTEP,[2]);poke(TUNEPOS,[9]);poke(FEEDBACK,[0]);step('R')
        ok(b(CONSOLE)==3 and b(TALK)==1 and b(MESSAGE)==81,'in phase again: SCIENTIST: G-BOT! WAIT. AGAIN?');shot('9_scientist_again')
        seq=runs_to(67,900);ok(seq==[81,82,83,55,56,57,67],'she remembers, warns again, is cut off again: %s'%seq)
        seq=runs_to(0xD6,500);ok(seq==[67,96,0xD6],'the nudge: ...THE SUBSTATION: EAST OF POWER ROOM / G-BOT: BUT SHE SAID NO FULL POWER... (%s)'%seq)
        goal((0xE7,0xE8),'warned again (real flags): the substation, and N')
        frames(80);hide();at(30,56,3);step(' ');frames(1);ok(b(MESSAGE)==58,'console re-probe: CONSOLE: IN PHASE. NO FULL POWER!')
        seq=runs_to(97,300);ok(seq==[58,97],'...then SUBSTATION OPEN: EAST OF POWER ROOM (%s)'%seq);frames(2);shot('0_substation_hint')
        seq=runs_to(42,300);ok(seq==[97,42],'...then LAB CLOCK SAYS 6:02. NOBODY AGREES. (%s)'%seq)
        # 5) a second rerun, muted
        frames(100);at(122,106,0);door(2,122,48,0);door(1,14,90,2)
        step('M');frames(2);ok(b(SOUNDOFF)==1,'M: sound off')
        door(4,14,90,2);at(120,56,3);s0=spk();ticks2,_,_,_=hesitate(95)
        ok(b(CHOICE)==1 and spk()==s0,'after a rerun: G-BOT: ...I HAVE DONE THIS BEFORE. then the prompt (muted: no clicks)')
        t_wake2=step('Y')
        ok(b(ROOM)==0 and b(LOOPS)==2 and b(MESSAGE)==0xD1,'second rerun: LOOPS=2; G-BOT: BAD IDEA. BUT I KEPT THE PAGE.')
        ok(spk()==s0,'sound off: the rerun and the wake make no speaker clicks')
        frames(4);door(1,122,120,3);door(2,224,104,1);poke(0x8F,[3,1,0]);door(3,122,120,3);hide()
        at(30,56,3);step(' ');frames(1);ok(b(MESSAGE)==80,'CONSOLE: LOOP 4,8??. YOU AGAIN?!')
        poke(CONSOLE,[2]);poke(TUNESTEP,[2]);poke(TUNEPOS,[9]);poke(FEEDBACK,[0]);step('R')
        ok(b(MESSAGE)==84,'SCIENTIST: AGAIN?! STOP FLIPPING IT!')
        # 6) door timing
        print('DOOR power -> substation %d cycles (%.2f s); substation -> power %d (%.2f s); wake after the flash %d (%.2f s), whole muted rerun %d (%.2f s)'%(t_in,t_in/1020484,t_out,t_out/1020484,t_wake,t_wake/1020484,t_wake2,t_wake2/1020484),flush=True)
        ok(t_in<1500000 and t_out<1500000,'substation doors under 1.5 s with a motif')
        print('DOOR security -> wing B %d cycles (%.2f s); wing B -> security %d (%.2f s)'%(t_wing,t_wing/1020484,t_wback,t_wback/1020484),flush=True)
        ok(t_wing<1500000 and t_wback<1500000,'wing B doors under 1.5 s with a motif')
    finally:
        p.terminate();p.wait(timeout=5);os.close(m)
print('RESULT: '+('FAIL' if failures else 'PASS'),flush=True)
raise SystemExit(bool(failures))
