#!/usr/bin/env python3
"""Original DARK POWER ROOM background for G-Bot: After Hours. Pillow is ART-ONLY.

The room is deliberately almost black: dotted, half-seen outlines, a warm wedge
of workshop light spilling through the doorway G-Bot just came through, and a
few standby indicators. Output is a native 8192-byte HGR screen (tracks 7-8).
"""
from pathlib import Path
from PIL import Image
from gen_concept import Paint, K,V,G,B,O,T,encode,decode,row_offset
from gen_workshop import message_pixels
ROOT=Path(__file__).resolve().parents[1]

def lit(x,c):
    """Nearest x on which a single HGR bit of colour c actually shows."""
    if c in (B,V): return x-(x&1)
    if c in (G,O): return x|1
    return x

def dots(p,pts,c,stride=4,phase=0):
    """Barely-visible outline: one dot every `stride` pixels along a polyline."""
    n=phase
    for (x0,y0),(x1,y1) in zip(pts,pts[1:]):
        steps=max(abs(x1-x0),abs(y1-y0),1)
        for i in range(steps):
            if n%stride==0:
                x=x0+(x1-x0)*i//steps; y=y0+(y1-y0)*i//steps
                p.dot(lit(x,c),y,c)
            n+=1

def room():
    import math
    p=Paint()
    # Room shell: the same depth as the workshop, but only hinted at.
    dots(p,[(6,153),(6,3),(273,3),(273,153)],B,8)
    dots(p,[(9,75),(271,75)],B,10)
    dots(p,[(9,80),(271,80)],V,12,3)
    # Ceiling pipe run and a dead bulb hanging on its cord.
    dots(p,[(10,12),(270,12)],B,6)
    dots(p,[(10,16),(178,16),(178,26)],V,8)
    dots(p,[(140,16),(140,30)],B,4)
    dots(p,[(135,31),(145,31),(147,35),(140,40),(133,35),(135,31)],B,3)
    # BREAKER PANEL -- the hint for the next goal; the clearest shape here.
    dots(p,[(40,22),(92,22),(92,70),(40,70),(40,22)],V,3)
    dots(p,[(44,26),(88,26),(88,66),(44,66),(44,26)],B,6,1)
    for y in (32,40,48):                       # three rows of tripped breakers
        for x in (50,58,66):
            p.dot(lit(x,B),y,B); p.dot(lit(x,B),y+2,B); p.dot(lit(x+2,B),y+4,B)
    # Empty fuse holder: two clips and nothing between them.
    p.line([(75,32),(83,32)],O); p.line([(75,46),(83,46)],O)
    dots(p,[(76,35),(76,43)],O,3); dots(p,[(82,35),(82,43)],O,3)
    p.rect((51,58,52,59),O)                    # standby lamp: the only steady glow
    dots(p,[(46,62),(70,62)],B,6)
    # Heavy feed cable from panel down the wall and across to the generator.
    dots(p,[(92,52),(104,52),(104,92),(176,92),(186,86)],O,6)
    # DEAD GENERATOR: big drum on a skid, gauge needle resting on zero.
    dots(p,[(186,40),(264,40),(266,46),(266,104),(184,104),(184,46),(186,40)],B,4)
    dots(p,[(190,44),(262,44)],V,6,2)
    for x in (196,212,228,244):
        dots(p,[(x,48),(x,98)],B,10,x%3)
    dots(p,[(182,106),(268,106),(270,112),(180,112),(182,106)],V,5)
    for i in range(0,360,24):                  # gauge ring and resting needle
        x=226+round(11*math.cos(math.radians(i))); y=68+round(8*math.sin(math.radians(i)))
        p.dot(lit(x,B),y,B)
    p.line([(219,72),(225,68)],O)
    p.dot(lit(246,G),86,G); p.dot(lit(250,G),86,G)   # sleeping controller LEDs
    dots(p,[(196,30),(196,40)],V,4); dots(p,[(254,30),(254,40)],V,4)
    dots(p,[(190,30),(260,30)],V,7)
    # A storage locker, almost entirely swallowed by the dark.
    dots(p,[(112,30),(160,30),(160,72),(112,72),(112,30)],V,9)
    # Floor seams: dimmer further from the door.
    for x in (-210,-58,85,225,370,520):
        dots(p,[(140+(x-140)//5,81),(x,158)],B,9)
    for y,s in ((93,16),(113,12),(137,9)):
        dots(p,[(9,y),(271,y)],B,s)
    # Warm workshop light spilling through the open doorway behind G-Bot:
    # a cone of isolated orange dots, dense at the threshold, fading out.
    for y in range(104,157):
        t=(y-104)/52                           # 0 far .. 1 at the threshold
        half=22+round(26*(1-t))
        if y%2: continue
        gap=4 if t>0.8 else 6 if t>0.55 else 10 if t>0.3 else 16
        for x in range(142-half,142+half+1):
            if (x*7+y*5+(y*y)%7)%gap==0 and abs(x-142)<=half-(0 if t>0.5 else 4):
                p.dot(lit(x,O),y,O)
    p.line([(118,157),(166,157)],T)
    dots(p,[(8,157),(116,157)],O,8); dots(p,[(168,157),(272,157)],O,8)
    p.line([(116,151),(116,157)],O); p.line([(167,151),(167,157)],O)
    # Same native HUD as the workshop.
    p.line([(8,160),(271,160)],B)
    p.text(46,163,'G-BOT: AFTER HOURS',T,2)
    data=bytearray(encode(p.im))
    for row,values in enumerate(message_pixels('WASD/ARROWS WALK   SPACE PROBE')):
        data[row_offset(186+row):row_offset(186+row)+40]=values
    return bytes(data)

def main():
    data=room()
    assert data==room(), 'Power room generation must be deterministic'
    used={row_offset(y)+b for y in range(192) for b in range(40)}
    assert all(data[i]==0 for i in set(range(8192))-used), 'Nonzero HGR holes'
    (ROOT/'art/power-room.hgr').write_bytes(data)
    (ROOT/'build').mkdir(exist_ok=True)
    decode(data).resize((1120,768),Image.Resampling.NEAREST).save(ROOT/'build/power-room-design.png')
    lit_bits=sum(bin(v&127).count('1') for v in data[:])
    print('Power room: 8192 bytes,',lit_bits,'lit pixels of 53760')
if __name__=='__main__':main()
