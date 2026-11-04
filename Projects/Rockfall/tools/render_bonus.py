#!/usr/bin/env python3
"""Model of the bonus-hit sound (rockfall.s 'bonus': tone loop over bnper/bnlen) -> WAV preview.
Usage: render_bonus.py out.wav   (plays the arpeggio twice, 0.4 s apart)"""
import sys,wave,struct
CLK=1023000; SR=44100
NOTES=[(1047,15),(1319,15),(1568,15),(2093,15),(2637,15),(3136,15),(4186,15),(2093,10),(3136,10),(4186,20)]  # same as bnper/bnlen
def bonus():
    t=[];c=0
    for f,ms in NOTES:
        per=(500000//f-15)//5; n=ms*f//500     # ca65 integer maths
        for i in range(n): c+=4; t.append(c); c+=3+5*per-1+21
        c+=45                                    # per-note overhead (table fetch, jsr/rts)
    return t,c
t,c=bonus(); print('bonus: %d toggles, %d cycles = %.1f ms'%(len(t),c,c/CLK*1e3))
seq=[(t,c),(None,int(0.4*CLK)),(t,c),(None,int(0.4*CLK))]
samples=[];lvl=1
for tg,n in seq:
    idx=sorted(tg or []); j=0
    for s in range(int(n/CLK*SR)):
        while j<len(idx) and idx[j]<=s*CLK/SR: lvl=-lvl; j+=1
        samples.append(lvl)
out=[];y=0;px=0
for x in samples: y=0.995*(y+x-px); px=x; out.append(int(max(-1,min(1,y))*12000))
w=wave.open(sys.argv[1],'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes(struct.pack('<%dh'%len(out),*out)); w.close()
