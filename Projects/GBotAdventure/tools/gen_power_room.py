#!/usr/bin/env python3
"""Original POWER ROOM backgrounds for G-Bot: After Hours. Pillow is ART-ONLY.

room(False): the DARK power room -- dotted, half-seen outlines, a warm wedge of
workshop light through the doorway, a few standby indicators and one glint in
the old locker (the fuse). Disk tracks 7-8.
room(True): the same room after the fuse is fitted -- solid outlines, the bulb
lit, gauge needle up, breakers set, west security door unlocked. Tracks 9-10.
"""
from pathlib import Path
import math
from PIL import Image
from gen_concept import Paint, K,V,G,B,O,T,encode,decode,row_offset
from gen_workshop import message_pixels,finish,clock_hands,FLOOR
ROOT=Path(__file__).resolve().parents[1]

def lit(x,c):
    """Nearest x on which a single HGR bit of colour c actually shows."""
    if c in (B,V): return x-(x&1)
    if c in (G,O): return x|1
    return x

def dots(p,pts,c,stride=4,phase=0):
    """Barely-visible outline: one dot every `stride` pixels along a polyline."""
    if stride<=1:
        p.line(pts,c); return
    n=phase
    for (x0,y0),(x1,y1) in zip(pts,pts[1:]):
        steps=max(abs(x1-x0),abs(y1-y0),1)
        for i in range(steps):
            if n%stride==0:
                x=x0+(x1-x0)*i//steps; y=y0+(y1-y0)*i//steps
                p.dot(lit(x,c),y,c)
            n+=1

def room(on=False):
    p=Paint()
    S=(lambda s:1) if on else (lambda s:s)     # powered: every outline solid
    # Room shell: the same depth as the workshop.
    dots(p,[(6,FLOOR-4),(6,3),(273,3),(273,FLOOR-4)],B,S(8))
    # The room's clock, stopped when the power went (9:41).
    if on:
        p.ellipse((14,30,34,48),B); p.ellipse((16,32,32,46),K)
        clock_hands(p,24,39,'POWER ROOM',4,6)
    else:
        for i in range(0,360,40):
            p.dot(lit(24+round(10*math.cos(math.radians(i))),B),39+round(9*math.sin(math.radians(i))),B)
        clock_hands(p,24,39,'POWER ROOM',4,6,B)
    dots(p,[(9,75),(271,75)],B,S(10))
    dots(p,[(9,80),(271,80)],V,S(12),3)
    # Ceiling pipe run and the bulb hanging on its cord.
    dots(p,[(10,12),(270,12)],B,S(6))
    dots(p,[(10,16),(178,16),(178,26)],V,S(8))
    dots(p,[(140,16),(140,30)],B,S(4))
    if on:
        p.poly([(135,31),(145,31),(147,35),(140,40),(133,35)],T)
        for a in range(20,170,25):              # warm rays
            r0,r1=12,22
            c=math.cos(math.radians(a)); s=math.sin(math.radians(a))
            dots(p,[(140+round(r0*c),35+round(r0*s)),(140+round(r1*c),35+round(r1*s))],O,2)
    else:
        dots(p,[(135,31),(145,31),(147,35),(140,40),(133,35),(135,31)],B,3)
    # BREAKER PANEL.
    dots(p,[(40,22),(92,22),(92,70),(40,70),(40,22)],V,S(3))
    dots(p,[(44,26),(88,26),(88,66),(44,66),(44,26)],B,S(6),1)
    for y in (32,40,48):
        for x in (50,58,66):
            if on:                              # breakers set: up, lit green
                p.line([(lit(x,G),y),(lit(x,G),y+3)],G); p.dot(lit(x,T),y,T)
            else:                               # tripped: dim, sagging
                p.dot(lit(x,B),y,B); p.dot(lit(x,B),y+2,B); p.dot(lit(x+2,B),y+4,B)
    p.line([(75,32),(83,32)],O); p.line([(75,46),(83,46)],O)
    if on:                                      # the fuse, seated in its clips
        p.rect((77,33,81,45),T); p.line([(77,39),(81,39)],O)
    else:                                       # empty holder
        dots(p,[(76,35),(76,43)],O,3); dots(p,[(82,35),(82,43)],O,3)
    p.rect((51,58,52,59),G if on else O)        # standby lamp -> run lamp
    dots(p,[(46,62),(70,62)],B,S(6))
    # Feed cable from panel to the generator.
    dots(p,[(92,52),(104,52),(104,92),(176,92),(186,86)],O,S(6) if not on else 2)
    # GENERATOR on its skid.
    dots(p,[(186,40),(264,40),(266,46),(266,104),(184,104),(184,46),(186,40)],B,S(4))
    dots(p,[(190,44),(262,44)],V,S(6),2)
    for x in (196,212,228,244):
        dots(p,[(x,48),(x,98)],B,10 if not on else 3,x%3)
    dots(p,[(182,106),(268,106),(270,112),(180,112),(182,106)],V,S(5))
    if on: p.ellipse((215,60,237,76),K)
    for i in range(0,360,24 if not on else 12):   # gauge ring
        x=226+round(11*math.cos(math.radians(i))); y=68+round(8*math.sin(math.radians(i)))
        p.dot(lit(x,T if on else B),y,T if on else B)
    if on: p.line([(226,68),(232,61)],G)        # needle up in the green
    else: p.line([(219,72),(225,68)],O)         # needle resting on zero
    p.dot(lit(246,G),86,G); p.dot(lit(250,G),86,G)
    if on:
        for x in (240,244,248,252): p.dot(lit(x,O),92,O)
    dots(p,[(196,30),(196,40)],V,S(4)); dots(p,[(254,30),(254,40)],V,S(4))
    dots(p,[(190,30),(260,30)],V,S(7))
    # The old storage locker. In the dark one glint gives the fuse away.
    dots(p,[(112,30),(160,30),(160,72),(112,72),(112,30)],V,S(9))
    dots(p,[(136,32),(136,70)],V,S(9))
    for y in (44,46): p.dot(lit(130,G),y,G)     # locker handles
    for y in (44,46): p.dot(lit(142,G),y,G)
    if not on:
        p.line([(120,57),(125,57)],T); p.line([(122,55),(123,55)],T)   # glint
        p.line([(122,59),(123,59)],T)
    # WEST SECURITY DOOR, in perspective on the left wall.
    door=[(9,92),(30,98),(30,146),(9,152)]
    if on: p.line(door+[door[0]],T)
    else: dots(p,door+[door[0]],V,3)
    dots(p,[(13,96),(26,100)],B,S(4))
    p.rect((32,112,33,115),G if on else O)      # its lock lamp
    if on:
        p.text(11,84,'SEC',G)
    # Floor seams.
    for x in (-210,-58,85,225,370,520):
        dots(p,[(140+(x-140)//5,81),(x,FLOOR+1)],B,9 if not on else 4)
    for y,s in ((93,16),(113,12),(137,9)):
        dots(p,[(9,y),(271,y)],B,s if not on else 4)
    if not on:
        # Warm workshop light spilling through the open doorway.
        for y in range(104,FLOOR):
            t=(y-104)/(FLOOR-105)
            half=22+round(26*(1-t))
            if y%2: continue
            gap=4 if t>0.8 else 6 if t>0.55 else 10 if t>0.3 else 16
            for x in range(142-half,142+half+1):
                if (x*7+y*5+(y*y)%7)%gap==0 and abs(x-142)<=half-(0 if t>0.5 else 4):
                    p.dot(lit(x,O),y,O)
    p.line([(118,FLOOR),(166,FLOOR)],T)
    dots(p,[(8,FLOOR),(116,FLOOR)],O,8); dots(p,[(168,FLOOR),(272,FLOOR)],O,8)
    p.line([(116,FLOOR-6),(116,FLOOR)],O); p.line([(167,FLOOR-6),(167,FLOOR)],O)
    return finish(p,'POWER ROOM')

def main():
    used={row_offset(y)+b for y in range(192) for b in range(40)}
    (ROOT/'build').mkdir(exist_ok=True)
    for on,name in ((False,'power-room'),(True,'power-room-lit')):
        data=room(on)
        assert data==room(on), 'Power room generation must be deterministic'
        assert all(data[i]==0 for i in set(range(8192))-used), 'Nonzero HGR holes'
        (ROOT/'art'/(name+'.hgr')).write_bytes(data)
        decode(data).resize((1120,768),Image.Resampling.NEAREST).save(ROOT/'build'/(name+'-design.png'))
        print(name,': 8192 bytes,',sum(bin(v&127).count('1') for v in data),'lit pixels')
if __name__=='__main__':main()
