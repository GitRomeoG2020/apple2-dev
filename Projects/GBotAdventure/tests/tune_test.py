#!/usr/bin/env python3
"""Room-entry tunes in Bobbin: the boot motif, the first-entry guarantee, the
random 1-in-2 choice (checked against the documented rule door by door), the
M toggle, and what a tune costs a door. Doors are driven like
tests/door_timing.py (the engine's own door request, set at the main loop).
Usage: python3 tests/tune_test.py [enhanced|plus]"""
import json,os,pty,re,socket,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
machine=sys.argv[1] if len(sys.argv)>1 else 'enhanced'
lbl=(ROOT/'build/gbot.lbl').read_text()
MAIN=int(re.search(r'al ([0-9A-F]+) \.main\b',lbl).group(1),16)
SOUNDOFF,SPKCNT,SEED,VISITED,TUNES,TUNELAST,TUNED,TUNERND=0xB7,0xBF,0xC5,0xC6,0xC7,0xC8,0xC9,0xCA
TICKS=0x81
NAMES=('workshop','power','security','lab')
# Door times without a tune (59109b6, before tunes; identical on IIe and II+).
BASE={(0,1):799450,(1,2):1000616,(2,3):927709,(3,2):997492,(2,1):732919,(1,0):872204}
FRAME=17100            # timing granularity: one video frame (17,030 cycles)
LIMIT=510242           # a tune may add at most ~0.5 s to a door
failures=[]
def ok(c,d):
    print(('PASS ' if c else 'FAIL ')+d,flush=True)
    if not c:failures.append(d)
def lfsr(s):
    s=s or 0x5A
    s=(s<<1)^(0x1D if s&0x80 else 0)
    return s&0xFF
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
    def peek(a,n=1):return bytes(q({'cmd':'peek','addr':a,'len':n})['data'])
    def poke(a,d):q({'cmd':'poke','addr':a,'data':d})
    def step(key=None):
        if key:q({'cmd':'keys','text':key})
        q({'cmd':'resume'});return until_paused()
    def spk():a,b=peek(SPKCNT,2);return a|b<<8
    try:
        while True:
            try:q({'cmd':'ping'});break
            except OSError:time.sleep(.05)
        q({'cmd':'break_set','addr':MAIN});until_paused()
        ok(peek(VISITED,3)==bytes([1,1,0]) and peek(TUNES)==b'\x01','boot plays the workshop motif and counts the workshop as entered (%s)'%list(peek(VISITED,3)))
        for _ in range(3):step()
        poke(0x83,[3]);poke(0x8D,[2]);poke(0x9D,[1]);poke(0x8C,[3])   # all doors open, power room lit
        cycle=[(1,122,120,3),(2,224,104,1),(3,122,120,3),(2,122,48,0),(1,14,90,2),(0,122,48,0)]
        doors=[]
        def door(nxt,x,y,d,idle):
            for _ in range(idle):step()        # the player's own pace varies the timing
            room=peek(0x8A)[0];seed=peek(SEED)[0];ticks=peek(TICKS)[0];vis=peek(VISITED)[0];n0=peek(TUNES)[0];s0=spk()
            poke(0x98,[nxt,x,y,d]);poke(0x8B,[1])
            r=q({'cmd':'cpu'});t0=now(r);r=step();t=now(r)-t0
            if peek(0x8A)[0]!=nxt:raise AssertionError('door %d->%d did not happen'%(room,nxt))
            tuned,rnd=peek(TUNED)[0],peek(TUNERND)[0]
            first=not vis&(1<<nxt)
            want_seed=lfsr(seed);want_rnd=want_seed^ticks
            play=(first or rnd<128) and not peek(SOUNDOFF)[0]
            motif=nxt if not rnd&0x40 else rnd&3
            rec=dict(a=room,b=nxt,t=t,tuned=tuned,first=first,rnd=rnd,motif=peek(TUNELAST)[0],clicks=(spk()-s0)&0xFFFF,
                     rule=(peek(SEED)[0]==want_seed and rnd==want_rnd and tuned==int(play) and peek(TUNES)[0]==(n0+play)&255 and (not play or peek(TUNELAST)[0]==motif)))
            doors.append(rec)
            print('%-8s -> %-8s %8d cycles (%.2f s) %s'%(NAMES[room],NAMES[nxt],t,t/1020484,('motif %d'%rec['motif'] if tuned else '-')+(' first' if first else '')),flush=True)
            for _ in range(4):step()            # input lockout
            return rec
        # 1) first-ever entries, then many doors at a varying pace
        for k in range(8):
            for j,(nxt,x,y,d) in enumerate(cycle):door(nxt,x,y,d,1+(k*7+j*3)%5)
        firsts=[r for r in doors if r['first']]
        ok(len(firsts)==3 and all(r['tuned'] for r in firsts),'first-ever entry to power, security and lab always plays a motif')
        ok(all(r['rule'] for r in doors),'every door follows the rule: 8-bit LFSR mixed with the frame count; first entry or 1 in 2; room motif or any (%d doors)'%len(doors))
        rest=[r for r in doors if not r['first']]
        played=sum(r['tuned'] for r in rest)
        ok(0.3<=played/len(rest)<=0.7,'roughly 1 in 2 later doors play a motif (%d of %d)'%(played,len(rest)))
        motifs={r['motif'] for r in rest if r['tuned']}
        ok(len(motifs)>=3,'random choice: %d different motifs heard (%s)'%(len(motifs),sorted(motifs)))
        ok(any(r['tuned'] and r['motif']==r['b'] for r in rest) and any(r['tuned'] and r['motif']!=r['b'] for r in rest),'both a room\'s own motif and another room\'s motif occur')
        ok(all(r['clicks']>=200 for r in doors if r['tuned']) and all(r['clicks']==72 for r in doors if not r['tuned']),'a tune replaces the door chirp (chirp alone: 72 clicks)')
        # 2) door time: plain doors as before; a tune adds at most ~0.5 s
        for key in sorted(BASE):
            plain=[r['t'] for r in doors if (r['a'],r['b'])==key and not r['tuned']]
            tuned=[r['t'] for r in doors if (r['a'],r['b'])==key and r['tuned']]
            if plain:ok(max(plain)<=BASE[key]+FRAME,'door %s -> %s without a tune: %.2f s (was %.2f s)'%(NAMES[key[0]],NAMES[key[1]],max(plain)/1020484,BASE[key]/1020484))
            if tuned:ok(max(tuned)-BASE[key]<=LIMIT,'door %s -> %s with a tune: %.2f s (+%.2f s)'%(NAMES[key[0]],NAMES[key[1]],max(tuned)/1020484,(max(tuned)-BASE[key])/1020484))
        # 3) M off: no tunes, not even on a first entry, and doors as before
        step('M');ok(peek(SOUNDOFF)==b'\x01','M: sound off')
        for _ in range(30):step()
        poke(VISITED,[1]);n=len(doors);s0=spk()
        for j,(nxt,x,y,d) in enumerate(cycle*2):door(nxt,x,y,d,1+j%5)
        off=doors[n:]
        ok(not any(r['tuned'] for r in off) and spk()==s0 and peek(VISITED)[0]==15,'sound off: no tunes (first entries included), no clicks, rooms still marked entered')
        ok(all(r['t']<=BASE[(r['a'],r['b'])]+FRAME for r in off),'sound off: every door as fast as before tunes')
        step('M');ok(peek(SOUNDOFF)==b'\0','M: sound on')
        for _ in range(30):step()
        poke(VISITED,[1]);n=len(doors)
        for nxt,x,y,d in cycle[:3]:door(nxt,x,y,d,2)
        ok(all(r['tuned'] for r in doors[n:]),'sound on again: first entries play again')
    finally:
        p.terminate();p.wait(timeout=5);os.close(m)
print('RESULT: '+('FAIL' if failures else 'PASS'),flush=True)
raise SystemExit(bool(failures))
