#!/usr/bin/env python3
"""Cycle-accurate model of pew + crackle speaker toggles (1.023 MHz) -> WAV preview.
Usage: render_sfx.py build/rockfall.bin out.wav"""
import sys,wave,struct
CLK=1023000; ORG=0x800; PEW=0x6DE  # pew offset in bin (from listing)
binf=open(sys.argv[1],'rb').read()
def pew():
    t=[];c=0;per=23;fr=0
    while True:
        c+=4; t.append(c)               # bit SPKR (toggle at end of access)
        c+=3+5*per-1
        fr+=204; per+=1+(fr>>8); fr&=255
        c+=20+(3 if per<140 else 2)
        if per>=140: return t,c
def crackle():
    t=[];c=0
    for y in range(96):
        a=ORG+PEW+y; c+=4+(1 if (a&0xFF00)!=((ORG+PEW)&0xFF00) else 0)
        x=(binf[PEW+y]&0x1F)+1; c+=6+5*x-1+4; t.append(c); c+=7
    return t,c
pt,pc=pew(); ct,cc=crackle()
print('pew: %d toggles, %d cyc = %.2f ms, first half-period %d cyc (%.0f Hz), last %d (%.0f Hz)'%(len(pt),pc,pc/CLK*1e3,pt[1]-pt[0],CLK/2/(pt[1]-pt[0]),pt[-1]-pt[-2],CLK/2/(pt[-1]-pt[-2])))
print('crackle: %d toggles, %d cyc = %.2f ms'%(len(ct),cc,cc/CLK*1e3))
SR=44100; seq=[(pt,pc),(None,int(0.3*CLK)),(ct,cc),(None,int(0.5*CLK))]*2
seq+= [(pt,pc),(None,int(0.05*CLK)),(ct,cc),(None,int(0.3*CLK))]
samples=[];lvl=1;
for tg,n in seq:
    tg=set(tg or []); ns=int(n/CLK*SR); idx=sorted(tg); j=0
    for s in range(ns):
        cyc=s*CLK/SR
        while j<len(idx) and idx[j]<=cyc: lvl=-lvl; j+=1
        samples.append(lvl)
# speaker is DC-coupled-ish: simple high-pass so silence returns to 0
out=[];y=0;px=0
for x in samples: y=0.995*(y+x-px); px=x; out.append(int(max(-1,min(1,y))*12000))
w=wave.open(sys.argv[2],'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes(struct.pack('<%dh'%len(out),*out)); w.close()
