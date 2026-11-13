#!/usr/bin/env python3
"""Bounded, real Disk II boot and frame-by-frame integration tests in Bobbin:
workshop repair, rear door, streamed power room, fuse hunt, lit power room,
security room with its patrolling guard, the lab with its flickering scientist,
and round trips through all four rooms.
Usage: python3 tests/workshop_test.py enhanced|plus [--bobbin /path/bobbin-ai]
Pillow supplies the independent art oracle and screenshot export.
"""
import argparse,json,os,pty,re,socket,subprocess,tempfile,time,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def offset(y):return (y&7)*1024+((y>>3)&7)*128+(y//64)*40

def put_actor(out,frames,size,ax,ay,rows,n):
    f=frames[n*size:(n+1)*size]
    for r in range(rows):
        row=f[r*9:r*9+9]
        for b in range(4):
            if row[b]:
                at=offset(ay+r)+ax+b
                out[at]=(out[at]&(~row[b]&127))|row[4+b]|row[8]

def expected(room,sprites,x,y,frame):
    out=bytearray(room); f=sprites[frame*572:(frame+1)*572]
    for row in range(44):
        a=f[row*13:row*13+13]
        mask=sum(v<<(b*7) for b,v in enumerate(a[:6]))<<(x%7)
        bits=sum(v<<(b*7) for b,v in enumerate(a[6:12]))<<(x%7)
        for b in range(7):
            m=(mask>>(b*7))&127; v=(bits>>(b*7))&127
            at=offset(y+row)+x//7+b
            if m:out[at]=(out[at]&(~m&127))|v|a[12]
    return bytes(out)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('machine',choices=['plus','enhanced'],default='enhanced',nargs='?')
    ap.add_argument('--bobbin',default='/workspace/apple2/bin/bobbin-ai');args=ap.parse_args()
    sys.path.insert(0,str(ROOT/"tools"))
    from gen_workshop import room as room_art,status_rows
    from gen_power_room import room as power_art
    from gen_security import room as security_art
    from gen_lab import room as lab_art,frames as sci_art
    arts={(1,False):power_art(False),(1,True):power_art(True),(2,False):security_art(False),(2,True):security_art(True),(3,False):lab_art()}
    guards=(ROOT/'art/guard-sprites.bin').read_bytes()
    scis=(ROOT/'art/scientist-sprites.bin').read_bytes()
    from gen_banks import aux as aux_track
    auxes={r:aux_track(r)[0] for r in range(4)}
    # Doors read only aux sectors 4..end-1 (the rest is scratch or empty).
    auxend={r:max(i for i,v in enumerate(auxes[r]) if v)//256+1 for r in range(4)}
    from gen_workshop import ENTER_MSG
    ROOMNAMES=('workshop','power','security','lab')
    from gen_workshop import MESSAGES as TEXTS,MSG_ROOMS
    assert scis==sci_art()
    def background(repair=0,msg=0,where=0,fuse=0,lit=False,labopen=False):
        flag=(lit and where==1) or (labopen and where==2)
        out=bytearray(room_art(repair==3) if where==0 else arts[(where,bool(flag))])
        for row,data in enumerate(status_rows(msg,fuse==1)):
            out[offset(177+row):offset(177+row)+40]=data
        return bytes(out)
    failures=[]
    def ok(condition,description):
        print(('PASS ' if condition else 'FAIL ')+description,flush=True)
        if not condition:failures.append(description)
    label=(ROOT/'build/gbot.lbl').read_text()
    mainpc=int(re.search(r'al ([0-9A-F]+) \.main',label).group(1),16)
    room=(ROOT/'art/workshop-room.hgr').read_bytes();sprites=(ROOT/'art/gbot-sprites.bin').read_bytes()
    with tempfile.TemporaryDirectory(prefix='gbot-test-') as temp:
        sock=temp+'/ctl.sock';disk=temp+'/gbot.dsk';original=(ROOT/'disk/gbot-after-hours.dsk').read_bytes();Path(disk).write_bytes(original)
        master,slave=pty.openpty()
        proc=subprocess.Popen([args.bobbin,'--simple','--remain','--no-turbo','-m',args.machine,'--disk',disk,'--control-socket',sock],stdin=slave,stdout=slave,stderr=slave,start_new_session=True);os.close(slave)
        def q(cmd):
            with socket.socket(socket.AF_UNIX) as s:
                s.settimeout(120);s.connect(sock);s.sendall(json.dumps(cmd).encode()+b'\n');out=b''
                while not out.endswith(b'\n'):out+=s.recv(65536)
            result=json.loads(out)
            if not result.get('ok'):raise RuntimeError(result)
            return result
        def wait(fun,seconds=3):
            end=time.monotonic()+seconds
            while time.monotonic()<end:
                try:
                    if fun():return True
                except (OSError,ValueError):pass
                time.sleep(.008)
            return False
        def peek(addr,n):
            return b''.join(bytes(q({'cmd':'peek','addr':a,'len':min(4096,addr+n-a)})['data']) for a in range(addr,addr+n,4096))
        def poke(a,d):q({'cmd':'poke','addr':a,'data':d})
        def state():return peek(0x70,20)
        def where():return peek(0x8A,1)[0]
        def lit():
            transit,panel=peek(0x8B,2)
            return where()==1 and panel==3 and transit==0
        def current_bg():
            repair,near,msg=peek(0x83,3)
            return background(repair,msg,where(),peek(0x8D,1)[0],lit(),peek(0x9D,1)[0]==1)
        def actor():return peek(0x9F,5)   # ACTX ACTY ACTH ACTSHOW ACTVIS
        def compose(bg,st):
            if where()<2:return expected(bg,sprites,st[0],st[1],st[7])
            ax,ay,ah,show,vis=actor()
            if not vis:return expected(bg,sprites,st[0],st[1],st[7])
            art,size=(guards,270) if show<6 else (scis,360)
            n=show if show<6 else show-6
            out=bytearray(bg)
            if st[1]>=ay+ah-44:   # G-Bot's feet nearer the viewer: actor drawn first
                put_actor(out,art,size,ax,ay,ah,n);return expected(bytes(out),sprites,st[0],st[1],st[7])
            out=bytearray(expected(bg,sprites,st[0],st[1],st[7]));put_actor(out,art,size,ax,ay,ah,n);return bytes(out)
        pages={0:expected(background(),sprites,126,104,0),1:expected(background(),sprites,126,104,0)}
        cycles=[];poses=set();shifts=set();checks=0
        def verify():
            nonlocal checks
            st=state();page=st[6]
            canonical=current_bg()
            if peek(0x8000,8192)!=canonical:raise AssertionError("canonical background not expected room/status art")
            pages[page]=compose(canonical,st)
            for n in (0,1):
                actual=peek(0x2000+n*8192,8192)
                if actual!=pages[n]:
                    diffs=[i for i,(a,b) in enumerate(zip(actual,pages[n])) if a!=b]
                    raise AssertionError('page%d mismatch, %d bytes; first %s; state %s'%(n,len(diffs),diffs[:12],list(st)))
            poses.add(st[7]);shifts.add(st[0]%7);checks+=1
            return st
        transitions=[];banks_seen=set();doors=[];door_times={};door_shots=set()
        LOADERS=(0x0805,0x0808)   # LOADROOM / LOADONE entries: a disk read starts
        def at_read(pc,first,room0):
            # Every door: before the first disk read the ENTERING line is already
            # on BOTH pages (whichever is displayed), and keys typed now must not
            # move G-Bot once he arrives.
            nxt=peek(0x98,1)[0]   # (ROOM is already the new room here)
            if first and nxt!=room0:      # (the fuse fit reloads in place)
                msg=peek(0x85,1)[0]; fuse=peek(0x8D,1)[0]==1
                want=status_rows(ENTER_MSG[nxt],fuse)
                good=msg==ENTER_MSG[nxt]
                for n in (0,1):
                    page=peek(0x2000+n*8192,8192)
                    good=good and all(page[offset(177+r):offset(177+r)+40]==want[r] for r in range(5))
                doors.append((room0,nxt,good))
                if not good:raise AssertionError('door %d->%d: ENTERING line not on both pages before the read'%(room0,nxt))
                if (room0,nxt) not in door_shots and nxt!=room0:
                    door_shots.add((room0,nxt));capture('entering_%s_from_%s'%(ROOMNAMES[nxt],ROOMNAMES[room0]),'door')
            # An impatient key mid-load: unflushed, 'S' would turn G-Bot round
            # at the arrival doorway and walk him straight back out.
            if first:q({'cmd':'keys','text':'S'})
        def frame(key=None,check=True):
            if key is not None:q({'cmd':'keys','text':key})
            room_before=(where(),lit())
            for a in LOADERS:q({'cmd':'break_set','addr':a})
            before=q({'cmd':'cpu'});q({'cmd':'resume'})
            # A room change streams 8K from the emulated Disk II: allow seconds. The
            # generous bound also rides out a stalled (suspended) host.
            reads=0
            while True:
                if not wait(lambda:q({'cmd':'cpu'})['paused'],60):raise RuntimeError('frame deadline exceeded: %s'%q({'cmd':'cpu'}))
                after=q({'cmd':'cpu'})
                if after['pc'] not in LOADERS:break
                at_read(after['pc'],reads==0,room_before[0]);reads+=1
                q({'cmd':'resume'})
            for a in LOADERS:q({'cmd':'break_clear','addr':a})
            if (where(),lit())!=room_before:
                # Transition rebuilt BOTH pages from the new room, robot on each.
                transitions.append((after['frames']-before['frames'])*17030+after['cycles'])
                door_times.setdefault((room_before[0],where()),[]).append(transitions[-1])
                # ...and the room's aux track (message bank, actor frames) is in.
                w=where();e=auxend[w]*256
                if peek(0x9E,1)[0]!=w or peek(0x1440,e-0x440)!=auxes[w][0x440:e]:
                    raise AssertionError('aux track for room %d not loaded'%w)
                banks_seen.add(w)
                st=state()
                pages[0]=pages[1]=compose(current_bg(),st)
                arrived=st[:3]
                if peek(0xAD,1)[0]!=4:raise AssertionError('no input lockout after the door')
                st=verify() if check else st
                for n in range(4):st=frame('A' if n==0 else None,check=check)   # keys typed now are dropped
                if st[:3]!=arrived:raise AssertionError('keys typed during the door moved G-Bot: %s -> %s'%(list(arrived),list(st[:3])))
                return st
            # Bobbin resets cycle_count at each video frame AND on resume.
            # Completed video frames plus the final partial frame approximate
            # this whole game tick (full-frame instruction overshoot <~18 cycles).
            cycles.append((after['frames']-before['frames'])*17030+after['cycles'])
            return verify() if check else state()
        def press(key,n=6):
            st=frame(key)
            for _ in range(n-1):st=frame()
            return st
        def position(x,y,direction=0):
            # Controlled fixtures exercise obstacle edges, not alternative input.
            poke(0x70,[x,y,direction,0]);frame();frame()
        def capture(name,prefix='workshop'):
            import sys
            sys.path.insert(0,str(ROOT/'tools'));from gen_concept import decode
            st=state();mem=peek(0x2000+st[6]*8192,8192)
            path=ROOT/'screenshots'/(prefix+'_'+name+'_'+args.machine+'.png')
            image=decode(mem);image.save(path.with_name(path.stem+'-280.png'))
            from PIL import Image
            image.resize((1120,768),Image.Resampling.NEAREST).save(path)
            print('SCREENSHOT '+str(path),flush=True)
        try:
            if not wait(lambda:q({'cmd':'ping'})['ok'],5):raise RuntimeError('socket startup timeout')
            q({'cmd':'break_set','addr':mainpc})
            if not wait(lambda:q({'cmd':'cpu'})['paused'],40):raise RuntimeError('boot deadline exceeded')
            ok(peek(0x7F,1)==b'\xa5','self-boot to workshop on '+args.machine)
            ok(peek(0x9E,1)==b'\0' and peek(0x1440,0xBC0)==auxes[0][0x440:],'boot read the workshop message bank (track 7) to $1440')
            ok(sum(len(v) for v in MSG_ROOMS.values())>=len(TEXTS),'every status message is in a room bank')
            verify();capture('idle')
            ok(peek(0x83,1)==b'\0', 'terminal boots visibly faulted, not repaired')
            st=state();start=st[:2]
            for key,dir,dx,dy in [('D',2,8,0),('S',0,0,8),('A',1,-8,0),('W',3,0,-8)]:
                before=state();after=press(key)
                ok((after[0],after[1],after[2])==(before[0]+dx,before[1]+dy,dir),'WASD '+key+' moves eight pixels, faces correctly and stops')
            ok(state()[:2]==start,'closed movement path returns precisely to spawn')
            # Bobbin maps host LF to Return; inject raw Apple high-bit $8A for Down.
            for key,dir in [('\x15',2),('\x8A',0),('\x08',1),('\x0B',3)]:
                before=state();after=press(key)
                ok(after[:2]!=before[:2] and after[2]==dir,'Apple arrow code '+hex(ord(key))+' moves correctly')
            if args.machine=='enhanced':
                before=state();after=press('d');ok(after[0]==before[0]+8,'lowercase IIe controls')
            # Sweep each shift remainder with movement and both foot poses.
            for _ in range(7):press('D',4)
            ok(shifts==set(range(7)),'all seven shifted sprite alignments, exact native-byte compositing')
            # Front-view walking screenshot; return to a clean composition.
            position(126,104);frame('S');capture('walking');press('W');position(126,104)
            after=frame(' ');ok(after[7]==13,'Space previews extended probe')
            ok(peek(0x83,1)==b'\0' and peek(0x85,1)==b'\x05','far probe gives NO CONTACT without repair')
            frame('R');ok(peek(0x83,1)==b'\0','R alone cannot repair a distant/uninspected terminal')
            capture('probe')
            for _ in range(10):frame()
            ok(state()[:2]==bytes([126,104]) and state()[7]==0,'probe retracts without movement or room changes')
            # Collision fixtures test every wall and both solid benches.
            for x,y,key,want,desc in [(14,104,'A',(14,104),'west wall'),(224,104,'D',(224,104),'east wall'),(126,48,'W',(126,48),'north wall'),(126,120,'S',(126,120),'south wall'),(56,64,'W',(56,64),'bench front'),(86,52,'A',(86,52),'bench side'),(210,70,'W',(210,70),'terminal front'),(190,52,'D',(190,52),'terminal side')]:
                position(x,y);after=press(key);ok(tuple(after[:2])==want,desc+' blocks fairly with no sprite corruption')
            # Before the repair the rear door stays sealed, with a reason.
            position(122,50,3);after=press('W')
            ok(tuple(after[:2])==(122,48) and where()==0 and peek(0x85,1)==b'\x0c','rear door is sealed before the workbench repair')
            position(126,104)
            # Real idle loop: one full blink period plus enough to catch both pages.
            before=state()[:2];blink=False
            for _ in range(132):
                st=frame();blink|=st[7]==12
            ok(blink,'periodic idle eye blink observed')
            ok(state()[:2]==before and state()[3]==0,'stable idle: no sticky last-key drift')
            capture('final')
            # Reach the service apron using real controls, not a teleport fixture.
            for _ in range(11):press('A',4)
            for _ in range(5):press('W',4)
            ok(tuple(state()[:2])==(38,64) and peek(0x84,1)==b'\x01','walk from spawn to reachable left workbench service position')
            ok(peek(0x85,1)==b'\x01','context prompt identifies Space to inspect')
            frame('R');ok(peek(0x83,1)==b'\0','reconnect requires inspecting the fault first')
            press(' ')
            ok(peek(0x83,1)==b'\x01' and peek(0x85,1)==b'\x02','probe diagnoses loose lead and offers R or Escape')
            capture('fault')
            # Space repeat cannot auto-confirm. Only R makes the repair.
            for _ in range(12):frame(' ')
            ok(peek(0x83,1)==b'\x01','held/repeating Space does not complete repair')
            frame('\x1B');ok(peek(0x83,1)==b'\0','Escape cancels inspection without restoring power')
            for _ in range(10):frame()
            press(' ');press('D',4);press('D',4);press('D',4);press('D',4)
            ok(peek(0x83,1)==b'\0','walking away cancels diagnosis safely')
            for _ in range(4):press('A',4)
            press(' ');frame('R')
            ok(peek(0x83,1)==b'\x02' and peek(0x85,1)==b'\x03','R starts bounded visible reconnect sequence')
            capture('repairing')
            before=state()[:2]
            for _ in range(8):frame('D')
            ok(state()[:2]==before and peek(0x83,1)==b'\x02','repair holds position briefly, cannot be interrupted by walk repeat')
            for _ in range(18):frame()
            ok(peek(0x83,1)==b'\x03' and peek(0x85,1)==b'\x04','repair completes: terminal waveform, conduit light and green door indicator')
            frame();frame();capture('online')
            for _ in range(12):frame(' ')
            ok(peek(0x83,1)==b'\x03' and peek(0x85,1)==b'\x06','re-probing reports ONLINE and never toggles back')
            frame('R');ok(peek(0x83,1)==b'\x03','repeated reconnect is idempotent')
            before=state()[0];after=press('D')
            ok(after[0]==before+8,'normal movement resumes after repair')
            # Sweep all alignments after dynamic room changes; exact BOTH-page checks.
            for _ in range(7):press('D',4)
            for _ in range(7):press('A',4)
            position(126,104)
            for _ in range(55):frame()
            capture('restored')
            ok({0,1,2,3,4,5,6,7,8,9,10,11,12,13}<=poses,'all 14 standing/walk/facing/blink/probe frames exercised')
            ok(peek(0x8000,8192)==background(3,4) and peek(0xA000,8008)==sprites,'canonical online background synchronized; source sprites unchanged')
            # ---- Through the unlocked door into the DARK POWER ROOM ----
            workshop_cycles=list(cycles)
            position(122,64);press('W',4);press('W',4);press('W',4)
            ok(where()==1 and tuple(state()[:3])==(122,120,3),'unlocked door: walking north into it streams in the power room')
            ok(peek(0x8000,8192)==background(3,8,1),'dark power room loaded from tracks 8-9 with its own status line')
            ok(peek(0x83,1)==b'\x03','repair state survives the room change')
            for _ in range(4):frame()
            capture('arrive','power')
            # Collisions: walls, closed side of the south edge, dead generator.
            for x,y,key,want,desc in [(14,104,'A',(14,104),'power west wall'),(224,104,'D',(224,104),'power east wall'),(90,48,'W',(90,48),'power north wall'),(40,120,'S',(40,120),'power south wall beside doorway'),(200,70,'W',(200,70),'generator front'),(148,52,'D',(148,52),'generator side')]:
                position(x,y);after=press(key);ok(tuple(after[:2])==want and where()==1,desc+' blocks fairly with no sprite corruption')
            position(126,96);frame(' ')
            ok(peek(0x85,1)==b'\x0b','probing empty darkness reports nothing to probe')
            for _ in range(12):frame()
            # Real controls from the doorway to the breaker panel.
            position(122,120,3)
            for _ in range(9):press('A',4)
            for _ in range(9):press('W',4)
            ok(tuple(state()[:2])==(50,48) and peek(0x84,1)==b'\x01' and peek(0x85,1)==b'\x09','walk to breaker panel; prompt offers Space')
            press(' ',4)
            ok(peek(0x85,1)==b'\x0a' and where()==1,'probing breaker panel reports NO POWER - FIND FUSE')
            capture('panel','power')
            frame('R');ok(peek(0x83,1)==b'\x03','R in the power room changes nothing')
            for _ in range(7):press('D',4)
            for _ in range(7):press('A',4)
            # Back through the lit doorway to the workshop.
            for _ in range(9):press('D',4)
            for _ in range(9):press('S',4)
            ok(where()==1 and tuple(state()[:2])==(122,120),'standing in the doorway does not leave yet')
            press('S',4)
            ok(where()==0 and tuple(state()[:3])==(122,48,0),'walking south through the doorway returns to the workshop door')
            ok(peek(0x83,1)==b'\x03' and peek(0x8000,8192)==background(3,4),'workshop reloaded with repair kept: online art, lights and status')
            for _ in range(4):frame()
            capture('return')
            for _ in range(3):press('S',4)
            ok(state()[1]==72 and where()==0,'normal workshop movement after return')
            press('W',4);press('W',4);press('W',4);press('W',4)
            ok(where()==1,'second trip into the power room')
            press('S',4);ok(where()==0,'and back again')
            # ---- Fuse hunt, lit power room, security room and its guard ----
            press('W',4)
            ok(where()==1 and tuple(state()[:3])==(122,120,3),'back in the dark power room')
            position(14,90,1);after=press('A')
            ok(where()==1 and tuple(after[:2])==(14,90) and peek(0x85,1)==bytes([21]),'west security door sealed without power')
            position(50,50);press(' ',4)
            ok(peek(0x85,1)==b'\x0a' and peek(0x8C,1)==b'\0','panel without a fuse: NO POWER - FIND FUSE, nothing to fit')
            frame('R');ok(peek(0x8C,1)==b'\0','R cannot fit a fuse G-Bot does not have')
            for _ in range(12):frame()
            # Real controls from the doorway to the locker.
            position(122,120,3)
            for _ in range(8):press('W',4)
            ok(tuple(state()[:2])==(122,56) and peek(0x84,1)==b'\x02' and peek(0x85,1)==bytes([13]),'locker prompt: OLD LOCKER: SPACE TO PROBE')
            capture('locker','power')
            press(' ',4)
            ok(peek(0x8D,1)==b'\x01' and peek(0x85,1)==bytes([14]),'probing the locker finds the fuse')
            ok(peek(0x8000,8192)==background(3,14,1,1),'carried fuse shown in the status-line HUD')
            capture('fuse','power')
            for _ in range(10):frame()
            press(' ',4);ok(peek(0x85,1)==bytes([15]) and peek(0x8D,1)==b'\x01','locker is empty afterwards')
            for _ in range(9):press('A',4)
            ok(tuple(state()[:2])==(50,56) and peek(0x84,1)==b'\x01','walk to the panel carrying the fuse')
            press(' ',4)
            ok(peek(0x8C,1)==b'\x01' and peek(0x85,1)==bytes([16]),'panel offers FUSE FITS: R TO FIT / ESC CANCEL')
            frame('\x1B');ok(peek(0x8C,1)==b'\0' and peek(0x8D,1)==b'\x01','Escape cancels; the fuse stays carried')
            for _ in range(12):frame(' ')
            ok(peek(0x8C,1)==b'\x01','held/repeating Space never fits the fuse')
            frame('R');ok(peek(0x8C,1)==b'\x02' and peek(0x85,1)==bytes([17]),'R starts FITTING FUSE')
            for _ in range(8):frame('A')
            ok(tuple(state()[:2])==(50,56),'fitting holds G-Bot in place')
            for _ in range(24):frame()
            ok(peek(0x8C,1)==b'\x03' and peek(0x8D,1)==b'\x02' and lit(),'fuse fitted: power restored')
            ok(peek(0x8000,8192)==background(3,18,1,2,True),'lit power room streamed from tracks 10-11, POWER RESTORED message, HUD fuse gone')
            for _ in range(4):frame()
            capture('lit','power')
            press(' ',4);ok(peek(0x85,1)==bytes([20]),'probing the live panel: PANEL ONLINE')
            # Lit state persists across a trip to the workshop and back.
            position(122,120,0);press('S',4)
            ok(where()==0 and peek(0x83,1)==b'\x03','power room -> workshop after the fit')
            press('W',4);press('W',4)
            ok(where()==1 and lit() and peek(0x8000,8192)==background(3,peek(0x85,1)[0],1,2,True),'power room stays lit after leaving and returning')
            # Security room: the west door now opens.
            position(14,90,1);press('A',4)
            ok(where()==2 and tuple(state()[:3])==(224,104,1),'west door opens into the security room at its checkpoint')
            ok(peek(0x92,1)==b'\x01' and peek(0x85,1)==bytes([23]),'guard is dormant and rebooting on first entry')
            ok(peek(0x1800,1620)==guards,'guard frames resident at $1800 from track 15')
            frame();capture('arrive','security')
            gxs=[]
            for _ in range(45):frame();gxs.append(peek(0x8F,1)[0])
            ok(peek(0x92,1)==b'\x02','guard wakes and starts patrolling')
            for i in range(190):
                frame();gxs.append(peek(0x8F,1)[0])
                if i==20:capture('patrol','security')
            steps=[b-a for a,b in zip(gxs,gxs[1:])]
            ok(set(steps)<={-1,0,1} and min(gxs)==2 and max(gxs)==30 and tuple(state()[:2])==(224,104),'readable patrol: one byte at a time, bounces at both ends, spawn is safe')
            # Touching the guard: back to the checkpoint with a message, no lives.
            poke(0x8F,[16,0,0]);position(112,80,1)
            ok(tuple(state()[:3])==(224,104,1) and peek(0x85,1)==bytes([24]),'touching the guard returns G-Bot to the entry checkpoint')
            capture('caught','security')
            # The new north lab door is sealed until the desk is probed.
            poke(0x8F,[3,1,0]);position(122,50,3);press('W',4)
            ok(where()==2 and tuple(state()[:2])==(122,48) and peek(0x85,1)==bytes([29]) and peek(0x9D,1)==b'\0','lab door sealed before the desk: LAB DOOR LOCKED - TRY THE DESK')
            ok(peek(0x8000,8192)==background(3,29,2,2,labopen=False),'lab-door lock lamp is orange while sealed')
            capture('labdoor_locked','security')
            position(224,104,1)
            # Cross the lane with real controls while the guard is away east.
            poke(0x8F,[3,1,0]);frame()
            for _ in range(15):press('A',4)
            for _ in range(6):press('W',4)
            for _ in range(4):press('A',4)
            ok(tuple(state()[:2])==(72,56) and peek(0x84,1)==b'\x01' and peek(0x85,1)==bytes([26]),'timed crossing reaches the security desk safely')
            press(' ',4);ok(peek(0x85,1)==bytes([27]),'probing the desk: MONITORS: EVERY CAMERA SHOWS NOBODY')
            capture('desk','security')
            ok(peek(0x9D,1)==b'\x01','probing the desk releases the lab door (LABOPEN)')
            ok(peek(0x8000,8192)==background(3,27,2,2,labopen=True),'lock lamp on the security art turns green')
            for _ in range(100):
                frame()
                if peek(0x85,1)==bytes([30]):break
            ok(peek(0x85,1)==bytes([30]),'desk line runs on: ...AND THE LAB DOOR CLICKS OPEN')
            capture('labdoor_open','security')
            position(60,54,3);press('W');ok(tuple(state()[:2])==(60,54),'security desk is solid')
            # Round trips through all three rooms.
            position(224,104,2);press('D',4)
            ok(where()==1 and tuple(state()[:3])==(14,90,2) and lit(),'east door returns to the lit power room')
            press('A',4);ok(where()==2 and peek(0x92,1)==b'\x02','re-entering: guard keeps patrolling (no second reboot)')
            press('D',4);ok(where()==1,'security -> power')
            position(122,106,0);press('S',4);press('S',4)
            ok(where()==0 and peek(0x83,1)==b'\x03' and peek(0x8000,8192)==background(3,4),'power -> workshop with every repair kept')
            press('W',4);ok(where()==1 and lit(),'workshop -> lit power room')
            position(14,90,1);press('A',4);ok(where()==2,'and on to security again')
            # ---- THE LAB ----
            poke(0x8F,[3,1,0]);position(122,50,3);press('W',4)
            ok(where()==3 and tuple(state()[:3])==(122,120,3),'open north door streams in the lab from tracks 16-17')
            ok(peek(0x9E,1)==b'\x03' and peek(0x1800,1440)==scis,'scientist frames streamed to $1800 from track 18')
            ok(peek(0x85,1)==bytes([31]),'arrival line: THE LAB: SOMETHING IS STILL RUNNING')
            for _ in range(3):frame()
            capture('arrive','lab')
            # Flicker: hidden -> ghost -> solid -> ghost -> next spot; every frame exact.
            phases=set();shows=set();spots=set();hidden=False;shot=set()
            for _ in range(250):
                frame()
                spot,timer,phase=peek(0xA6,3);ax,ay,ah,show,vis=actor()
                phases.add(phase);hidden|=vis==0
                if vis:shows.add(show);spots.add(spot)
                if phase==2 and 'scientist' not in shot and timer<30:capture('scientist','lab');shot.add('scientist')
                if phase in (1,3) and show in (8,9) and 'flicker' not in shot:capture('flicker','lab');shot.add('flicker')
            ok(phases=={0,1,2,3} and hidden,'scientist cycles gone / flickering in / here / flickering out')
            ok({6,7}&shows and {8,9}&shows,'solid and ghost (alternate-row) scientist frames both drawn')
            ok(len(spots)>=2,'she reappears at a different spot (%d spots seen)'%len(spots))
            ok(tuple(state()[:2])==(122,120),'harmless: G-Bot is never moved by her')
            # Fixed probes, scientist out of sync (hidden).
            def hide():poke(0xA6,[0,250,0]);poke(0x88,[0])   # scientist away; last line expired
            hide();position(30,56,3)
            ok(peek(0x84,1)==b'\x04' and peek(0x85,1)==bytes([40]),'consoles prompt')
            press(' ',4);ok(peek(0x85,1)==bytes([41]) and peek(0xA9,1)==b'\x01','CONSOLE: LOOP 4,817. PHASE DRIFT! (diagnosed)')
            capture('consoles','lab')
            for _ in range(60):
                frame()
                if peek(0x85,1)==bytes([44]):break
            ok(peek(0x85,1)==bytes([44]),'console prompt: PHASE DRIFT: R TO TUNE / ESC CANCEL')
            frame('\x1B');ok(peek(0xA9,1)==b'\0' and peek(0x85,1)==bytes([48]),'Escape cancels the diagnosis: TUNING CANCELLED')
            poke(0x88,[0]);press(' ',4);frame('R')
            ok(peek(0xA9,1)==b'\x02' and peek(0x85,1)==bytes([0x80|7]),'R starts tuning: phase 1/3 meter, cursor centred')
            frame('\x1B');ok(peek(0xA9,1)==b'\0','Escape cancels tuning too')
            poke(0x88,[0]);press(' ',4)
            for _ in range(4):press('D',4)
            ok(peek(0xA9,1)==b'\0' and state()[0]==62,'walking away cancels the diagnosis')
            hide();position(122,58,3);press('W');ok(tuple(state()[:2])==(122,58),'time-chamber dais is solid (front)')
            hide();position(176,50,1);press('A');ok(tuple(state()[:2])==(176,50),'time-chamber dais is solid (side)')
            hide();position(122,60,3)
            ok(peek(0x84,1)==b'\x01' and peek(0x85,1)==bytes([32]),'time chamber prompt')
            press(' ',4);ok(peek(0x85,1)==bytes([33]),'CHAMBER: LOOP ACTIVE. DO NOT DISTURB')
            capture('chamber','lab')
            for _ in range(100):
                frame()
                if peek(0x85,1)==bytes([43]):break
            ok(peek(0x85,1)==bytes([43]),'chamber line runs on: THE RING HUMS. IT KNOWS YOU.')
            hide();position(200,56,3)
            ok(peek(0x84,1)==b'\x02' and peek(0x85,1)==bytes([34]),'parking bay recognises him: WELCOME BACK, G-BOT')
            capture('bay','lab')
            press(' ',4);ok(peek(0x85,1)==bytes([35]),'BAY: G-BOT. LAST SERVICE: TONIGHT.')
            for _ in range(100):
                frame()
                if peek(0x85,1)==bytes([36]):break
            ok(peek(0x85,1)==bytes([36]),'bay line runs on: ...AND TONIGHT. AND TONIGHT.')
            hide();position(122,100,0);frame(' ');ok(peek(0x84,1)==b'\0' and peek(0x85,1)==bytes([28]),'empty floor: NOTHING TO PROBE HERE')
            for _ in range(10):frame()
            # The scientist herself, pinned visible at spot 1.
            poke(0xA6,[1,250,2]);poke(0x88,[0]);position(140,100,2)
            ok(peek(0x84,1)==b'\x03' and peek(0x85,1)==bytes([37]),'scientist nearby: SCIENTIST! SPACE TO SAY HELLO')
            press(' ',4);ok(peek(0x85,1)==bytes([38]),'SCIENTIST: ...BEFORE THE MORNING SHI-')
            capture('hello','lab')
            poke(0xA6,[1,4,3])
            for _ in range(100):
                frame()
                if peek(0x85,1)==bytes([39]):break
            ok(peek(0x85,1)==bytes([39]),'...AND SHE FLICKERED OUT MID-WORD')
            # ---- The console puzzle: tune three phases, then she can talk ----
            hide();position(30,56,3);press(' ',4);poke(0x88,[0]);frame('R')
            before=tuple(state()[:2])
            frame('D');frame('D')
            ok(peek(0xAB,1)==b'\x09' and tuple(state()[:2])==before and peek(0x85,1)==bytes([0x89]),'A/D move the phase cursor, not G-Bot')
            capture('tuning','lab')
            frame('R');ok(peek(0x85,1)==bytes([47]) and peek(0xAA,1)==b'\0' and peek(0xA9,1)==b'\x02','R off target fails gracefully: OUT OF PHASE - KEEP TUNING')
            for _ in range(5):frame('D')
            frame('D');ok(peek(0xAB,1)==b'\x0e','cursor stops at the right end')
            for _ in range(3):frame('A')
            ok(peek(0x85,1)==bytes([0x80|11]),'cursor on the target shows the lock-on star')
            capture('phase_aligned','lab')
            frame('R');ok(peek(0xAA,1)==b'\x01' and peek(0x85,1)==bytes([46]) and peek(0xAB,1)==b'\x07','phase 1 locked: LOCKED! NEXT PHASE...')
            for _ in range(5):frame('A')
            frame('R');ok(peek(0xAA,1)==b'\x02','phase 2 locked')
            frame('D');frame('D');frame('R')
            ok(peek(0xA9,1)==b'\x03' and peek(0xAC,1)==b'\x01' and peek(0x85,1)==bytes([49]),'phase 3 locked: console in phase, she speaks')
            ok(tuple(peek(0xA6,1)+peek(0xA8,1))==(2,2),'she stabilises solid at the console')
            frame();frame();capture('talk','lab')
            seq=[49];solid=True;held=True
            for _ in range(700):
                st=frame(' ' if len(seq)==2 and _%7==0 else ('A' if len(seq)==3 and _%9==0 else None))
                m=peek(0x85,1)[0]
                if m!=seq[-1]:
                    seq.append(m)
                    if m==55:capture('warning','lab')
                    if m==56:
                        ok(peek(0xAC,1)==b'\0' and peek(0xA8,1)==b'\x03','mid-word, she slips out of phase (TALK off, flickering out)')
                        frame();capture('flicker_out','lab')
                if seq[-1]<56:
                    ax,ay,ah,show,vis=actor()
                    solid&=vis==1 and show in (6,7) and (ax,ay)==(9,60)
                    held&=tuple(st[:2])==before
                if m==57:break
            ok(seq==list(range(49,58)),'dialogue plays in order: %s'%seq)
            ok(solid,'she stays solid in one place for the whole conversation')
            ok(held,'G-Bot listens: Space and walk keys are ignored while she talks')
            for _ in range(60):frame()
            ok(peek(0xA9,1)==b'\x03','console stays in phase')
            press(' ',4);ok(peek(0x85,1)==bytes([58]),'re-probe: CONSOLE: IN PHASE. NO FULL POWER!')
            for _ in range(100):
                frame()
                if peek(0x85,1)==bytes([42]):break
            ok(peek(0x85,1)==bytes([42]),'reminder runs on: LAB CLOCK SAYS 6:02. NOBODY AGREES.')
            # Back out: guard frames reload, state persists.
            position(122,106,0);press('S',4);press('S',4)
            ok(where()==2 and tuple(state()[:3])==(122,48,0),'lab doorway returns to the security north door')
            ok(peek(0x9E,1)==b'\x02' and peek(0x1800,1620)==guards,'guard frames re-streamed from track 15')
            ok(peek(0x92,1)==b'\x02' and peek(0x9D,1)==b'\x01','guard still patrolling, lab door still open')
            frame();capture('from_lab','security')
            press('W',4);ok(where()==3,'security -> lab again')
            position(122,106,0);press('S',4);press('S',4);ok(where()==2,'lab -> security')
            poke(0x8F,[3,1,0]);position(224,104,2);press('D',4);ok(where()==1 and lit(),'security -> lit power room')
            position(122,106,0);press('S',4);press('S',4);ok(where()==0 and peek(0x8000,8192)==background(3,4),'-> workshop, repairs kept')
            press('W',4);ok(where()==1 and lit(),'workshop -> power')
            position(14,90,1);press('A',4);ok(where()==2 and peek(0x9D,1)==b'\x01','power -> security, lab door still unlocked')
            poke(0x8F,[3,1,0]);position(122,50,3);press('W',4)
            ok(where()==3 and peek(0x83,1)==b'\x03' and peek(0x8C,1)==b'\x03' and peek(0x8D,1)==b'\x02' and peek(0x1800,1440)==scis and peek(0xA9,1)==b'\x03','full round trip: back in the lab with every state kept, console in phase')
            hide();position(30,56,3);press(' ',4);ok(peek(0x85,1)==bytes([58]) and peek(0xAC,1)==b'\0','console still online after the round trip; she does not repeat herself')
            ok(banks_seen=={0,1,2,3},'every room loaded its own message bank')
            ok(0<min(transitions) and len(transitions)>=24 and max(transitions)<1700000,'%d room transitions, slowest %d cycles (~%.2f s at 1 MHz)'%(len(transitions),max(transitions),max(transitions)/1020484))
            for (a,b),t in sorted(door_times.items()):
                print('DOOR %-8s -> %-8s x%d  max %7d cycles (~%.2f s)'%(ROOMNAMES[a],ROOMNAMES[b],len(t),max(t),max(t)/1020484),flush=True)
            ok(len(doors)>=20 and all(g for _,_,g in doors) and len({(a,b) for a,b,_ in doors})==6,'%d doors (all six directions): ENTERING line on both pages before the first disk read'%len(doors))
            ok(len(door_shots)==6,'screenshots of every ENTERING line')
            ok(peek(0xAD,1)==b'\0','keys typed during every load were discarded (lockout checked after each door)')
            cycles[:]=[c for c in cycles if c not in transitions]
            ok(peek(0x0800,4)==original[:4],'resident loader entry is preserved')
            ok(0<min(cycles) and max(cycles)<100000,'bounded 1 MHz frame budget: max %d cycles, mean %d (~%.1f fps)'%(max(cycles),sum(cycles)//len(cycles),1000000/(sum(cycles)/len(cycles))))
            print('EXACT PAGE CHECKS',checks,'BOTH PAGES, 8192 bytes each',flush=True)
        finally:
            proc.terminate()
            try:proc.wait(timeout=3)
            except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=3)
            os.close(master)
        ok(Path(disk).read_bytes()==original,'boot, walk, repair and room streaming never write the disk')
    print('RESULT: '+('FAIL' if failures else 'PASS'),flush=True)
    return bool(failures)
if __name__=='__main__':raise SystemExit(main())
