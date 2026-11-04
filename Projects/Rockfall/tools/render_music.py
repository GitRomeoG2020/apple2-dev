#!/usr/bin/env python3
"""Render the title music to a WAV by simulating the 1-bit speaker cycle by cycle.

Mirrors `music` in src/rockfall.s exactly: per title tick, MSEGN iterations of a 63-cycle
loop; the lead accumulator carry toggles the speaker at cycle 24 of the iteration, the bass
carry at cycle 53. Between segments the CPU spends GAP cycles (sequencer + vibrato + title
animation + key poll) with the speaker idle; the sequencer and vibrato then advance exactly
as the 6502 code does. The square wave is box-filtered down to 44.1 kHz and DC-blocked.
Usage: render_music.py [out.wav] [loops=1] [gap_cycles=1100]"""
import sys,os,wave,struct
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import gen_music as G
OUT=sys.argv[1] if len(sys.argv)>1 else '/workspace/apple2/games/rockfall_title_music.wav'
LOOPS=int(sys.argv[2]) if len(sys.argv)>2 else 1
GAP=int(sys.argv[3]) if len(sys.argv)>3 else 1100
SR=44100; VIBS=3
S=G.streams(); NT=G.notes(S); INC=[G.inc(m) for m in NT]; idx={m:i for i,m in enumerate(NT)}
def events(v):
    intro,loop=S[v]; ex=lambda part:[(INC[idx[m]],t) for m,t in part]
    yield from ex(intro)
    for _ in range(LOOPS): yield from ex(loop)
def run():
    lead=events('lead'); bass=events('bass')
    a1=a2=0; i1=i2=0; b1=0; c1=c2=1; vib=0; spk=0
    edges=[]; cyc=0                       # toggle times in CPU cycles
    while True:
        for k in range(G.SEGN):
            a1+=i1
            if a1>>16: a1&=0xFFFF; spk^=1; edges.append(cyc+24)
            a2+=i2
            if a2>>16: a2&=0xFFFF; spk^=1; edges.append(cyc+53)
            cyc+=G.LOOPCYC
        c1-=1
        if c1==0:
            try: b1,c1=next(lead)
            except StopIteration: return edges,cyc
        c2=(c2-1)&255
        if c2==0:
            try: i2,c2=next(bass)
            except StopIteration: return edges,cyc
        vib=(vib+1)%(4*VIBS); d=b1>>7; i1=b1
        if VIBS<=vib<2*VIBS: i1=b1+d
        elif vib>=3*VIBS: i1=b1-d
        cyc+=GAP
def main():
    edges,total=run(); n=int(total/G.CPU*SR)+1
    buf=[0.0]*n; level=-1.0; last=0.0; e=0
    step=G.CPU/SR
    for i in range(n):                    # box filter: fraction of each sample at +1
        t0=i*step; t1=t0+step; acc=0.0; t=t0
        while e<len(edges) and edges[e]<t1:
            acc+=level*(max(edges[e],t0)-t); t=max(edges[e],t0); level=-level; e+=1
        acc+=level*(t1-t); buf[i]=acc/step
    out=[]; y=0.0; px=0.0
    for x in buf: y=x-px+0.995*y; px=x; out.append(int(max(-1,min(1,y*0.6))*32767))
    os.makedirs(os.path.dirname(OUT),exist_ok=True)
    with wave.open(OUT,'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(struct.pack('<%dh'%len(out),*out))
    print('%s: %.1f s, %d toggles, %.2f ms/tick'%(OUT,n/SR,len(edges),(G.SEGN*G.LOOPCYC+GAP)/G.CPU*1000))
if __name__=='__main__': main()
