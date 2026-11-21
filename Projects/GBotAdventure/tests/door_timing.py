#!/usr/bin/env python3
"""Measure every door transition in Bobbin: cycles from the door trigger
(transition entry) to the first disk read, and to control returning to the
main loop. Usage: python3 tests/door_timing.py [enhanced|plus]
Drives transitions by setting the engine's own door request (TRANSIT etc.)
at the main-loop breakpoint, in the same order a player walks them."""
import json,os,pty,re,socket,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
machine=sys.argv[1] if len(sys.argv)>1 else 'enhanced'
lbl=(ROOT/'build/gbot.lbl').read_text()
def sym(n):return int(re.search(r'al ([0-9A-F]+) \.'+n+r'\b',lbl).group(1),16)
MAIN=sym('main')
MARKS=bool(os.environ.get('MARKS'))   # also stop at each read (adds <=1 frame of error per stop)
TRANS=sym('transition') if MARKS else None
with tempfile.TemporaryDirectory() as tmp:
    disk=tmp+'/d.dsk';Path(disk).write_bytes((ROOT/'disk/gbot-after-hours.dsk').read_bytes());sock=tmp+'/s'
    m,s=pty.openpty()
    p=subprocess.Popen(['/workspace/apple2/bin/bobbin-ai','--simple','--remain','--no-turbo','-m',machine,'--disk',disk,'--control-socket',sock],stdin=s,stdout=s,stderr=s,start_new_session=True);os.close(s)
    def q(c):
        with socket.socket(socket.AF_UNIX) as k:
            k.settimeout(60);k.connect(sock);k.sendall(json.dumps(c).encode()+b'\n');o=b''
            while not o.endswith(b'\n'):o+=k.recv(65536)
        return json.loads(o)
    def until_paused(t=60):
        end=time.monotonic()+t
        while time.monotonic()<end:
            try:
                r=q({'cmd':'cpu'})
                if r['paused']:return r
            except OSError:pass
            time.sleep(.005)
        raise RuntimeError('timeout')
    def now(r):return r['frames']*17030+r['cycles']
    try:
        while True:
            try:q({'cmd':'ping'});break
            except OSError:time.sleep(.05)
        for a in ((MAIN,TRANS,0x0805,0x0808,0x080B) if MARKS else (MAIN,)):q({'cmd':'break_set','addr':a})
        until_paused()
        for _ in range(3):q({'cmd':'resume'});until_paused()
        poke=lambda a,d:q({'cmd':'poke','addr':a,'data':d})
        poke(0x83,[3]);poke(0x8D,[2]);poke(0x9D,[1])   # all doors open
        if os.environ.get('MUTE'):poke(0xB7,[1])   # SOUNDOFF: no room motifs, pure door cost
        names=['WORKSHOP','POWER ROOM','SECURITY','THE LAB','SUBSTATION','WING B']
        # First the dark power room (breaker off) both ways, then every door
        # with the power room lit.
        route=[(0,1,122,120,3),(0,0,122,48,0),
               (3,1,122,120,3),(3,2,224,104,1),(3,3,122,120,3),(3,2,122,48,0),(3,1,14,90,2),(3,0,122,48,0),(3,1,122,120,3)]
        if 'SUB_TRACK' in (ROOT/'src/layout.inc').read_text():
            poke(0xA9,[3])   # console in phase: the substation door opens
            route+=[(3,4,14,90,2),(3,1,224,104,1)]
        if 'WINGB_TRACK' in (ROOT/'src/layout.inc').read_text():
            poke(0x92,[3])   # the guard remembers: the wing B door opens
            route+=[(3,2,224,104,1),(3,5,224,110,1),(3,2,14,110,2)]
        # Muted door costs of main at fedc2c8 (before the substation), same
        # route; a door may differ by up to one disk sector of rotation phase.
        BASE=[810799,840021,765307,966568,893664,980519,698840,838141,765353]
        SLACK=16000
        bad=[];times=[]
        room=0
        for panel,nxt,x,y,d in route:
            poke(0x8C,[panel])
            names[1]='POWER ROOM' if panel==3 else 'POWER DARK'
            poke(0x98,[nxt,x,y,d]);poke(0x8B,[1])
            r=q({'cmd':'cpu'});t0=now(r);first=None;reads=0;marks=[]   # the door's game tick starts
            while True:
                q({'cmd':'resume'});r=until_paused()
                if r['pc']==TRANS:continue
                if r['pc'] in (0x0805,0x0808,0x080B):
                    marks.append('%s@%d'%({0x0805:'room',0x0808:'aux',0x080B:'off'}[r['pc']],(now(r)-t0)//1000))
                    if r['pc']==0x080B:continue
                    reads+=1
                    if first is None:first=now(r)-t0
                elif r['pc']==MAIN:break
            total=now(r)-t0
            if MARKS:print('   ',' '.join(marks),'(k cycles)')
            print('%-11s -> %-11s %8d cycles (%.2f s)'%(names[room],names[nxt],total,total/1020484)+(' first read at %d'%first if MARKS else ''),flush=True)
            times.append(total);room=nxt
        if os.environ.get('MUTE') and not MARKS:
            for i,(t,base) in enumerate(zip(times,BASE)):
                if t>base+SLACK:bad.append(i)
            print('DOORS vs main: total %+d cycles over %d doors; worst %+d'%(sum(times[:9])-sum(BASE),len(BASE),max(t-b for t,b in zip(times,BASE))),flush=True)
            print('RESULT: '+('FAIL doors slower: %s'%bad if bad else 'PASS no door slower than main'),flush=True)
            if bad:raise SystemExit(1)
    finally:
        p.terminate();p.wait(timeout=5);os.close(m)
