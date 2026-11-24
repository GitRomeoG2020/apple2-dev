#!/usr/bin/env python3
"""Original WING B background for G-Bot: After Hours. Pillow is ART-ONLY.

The archive behind the security room's west door, sealed until the guard
remembers his code. Filing cabinets, a whiteboard where somebody has been
keeping a loop log for a very long time, and the coffee machine: one drop of
coffee hanging in midair under its spout, frozen, waiting for another minute.
Its clock disagrees with everyone (3:07). Drawn into $8000 from stamps on its
aux track (tools/gen_stamps.py).
"""
from pathlib import Path
import math
from PIL import Image
from gen_concept import Paint, K,V,G,B,O,T,decode,row_offset
from gen_workshop import finish,clock_hands,FLOOR
from gen_power_room import lit, dots
ROOT=Path(__file__).resolve().parents[1]
NAME='WING B'

def room(stage=0):
    """stage 0: the drop frozen in midair (the room as drawn from stamps);
    1-2: it falls (a second carried minute); 3: the machine awake and grumpy,
    the cup full and steaming (patched in RAM, tools/gen_chapter.py)."""
    p=Paint()
    # Shell, same depth and HUD as the other rooms.
    p.line([(6,3),(273,3),(273,FLOOR-5)],B,2)
    p.line([(6,3),(6,FLOOR-4)],B,2)
    p.line([(9,7),(269,7)],V)
    p.line([(9,75),(271,75)],O)
    p.line([(9,80),(271,80)],B)
    # The clock: 3:07, stopped like everything else in here.
    p.ellipse((14,8,36,28),B); p.ellipse((17,10,33,26),K)
    clock_hands(p,25,18,NAME,4,7)
    # Filing cabinets, left back wall: ARCHIVE.
    p.text(46,14,'ARCHIVE',T)
    for x in (42,70):
        p.rect((x,24,x+24,74),K)
        p.line([(x,74),(x,24),(x+24,24),(x+24,74)],B,2)
        for y in (32,46,60):
            p.line([(x+4,y),(x+20,y),(x+20,y+10),(x+4,y+10),(x+4,y)],V)
            p.rect((x+10,y+4,x+14,y+5),T)
    # THE COFFEE MACHINE on its counter: one drop, frozen in midair.
    p.rect((112,18,168,72),K)
    p.line([(112,72),(112,18),(168,18),(168,72)],B,2)
    p.text(122,22,'COFFEE',T)
    p.line([(118,32),(162,32)],B)
    p.rect((122,36,132,44),G)                  # its little screen: ON
    if stage==3:                               # ...awake: an orange scowl
        p.rect((122,36,132,44),O)
        p.line([(123,37),(126,39)],K,2); p.line([(131,37),(128,39)],K,2)
        p.rect((124,42,130,43),K)
    for i in range(3): p.rect((140+i*7,38,143+i*7,41),T if stage<3 else O)   # buttons
    p.rect((134,48,146,52),T)                  # spout
    p.rect((139,53,141,55),B)
    dy=(0,3,6,None)[stage]
    if dy is not None: p.rect((139,58+dy,141,60+dy),T)   # THE DROP (frozen, then falling)
    p.line([(132,62),(148,62),(146,70),(134,70),(132,62)],T)   # the cup, waiting
    p.line([(148,64),(151,64),(151,67),(147,67)],T)
    if stage==3:                               # full, and steaming
        p.rect((135,64,145,68),O)
        for x in (134,144):                    # (clear of the spout's drip)
            p.rect((x,59,x+1,60),T); p.rect((x+2,57,x+3,58),T); p.rect((x,55,x+1,56),T)
    # The counter.
    p.poly([(96,72),(184,72),(190,100),(90,100)],K)
    p.line([(96,72),(184,72),(190,100),(90,100),(96,72)],T)
    p.line([(93,86),(187,86)],B)
    # The loop log: a whiteboard full of tally marks.
    p.line([(196,16),(262,16),(262,56),(196,56),(196,16)],T)
    p.text(205,20,'LOOP LOG',T)
    for row,y in enumerate((30,40)):
        for g in range(5 if row==0 else 3):
            x=202+g*12
            for k in range(4): p.line([(x+k*2,y),(x+k*2,y+6)],B)
            p.line([(x-1,y+5),(x+8,y+1)],O)
    p.line([(238,44),(258,44)],B)              # ...and a line trailing off
    p.line([(210,58),(248,58)],B)              # pen tray
    # East door back to security, in perspective on the right wall.
    door=[(271,96),(252,102),(252,150),(271,156)]
    p.poly(door,K); p.line(door+[door[0]],T)
    p.line([(256,106),(256,146)],B)
    p.rect((246,118,247,121),G)
    p.text(246,86,'SEC',T)
    # Floor: the same rays and seams as the lab.
    for x in (-210,-58,85,225,370,520):
        p.line([(140+(x-140)//5,81),(x,FLOOR+1)],B)
    for y in (113,137): p.line([(9,y),(271,y)],B)
    p.line([(8,FLOOR),(272,FLOOR)],O)
    return finish(p,NAME)

def main():
    data=room(); assert data==room(), 'Wing B generation must be deterministic'
    used={row_offset(y)+b for y in range(192) for b in range(40)}
    assert all(data[i]==0 for i in set(range(8192))-used), 'Nonzero HGR holes'
    (ROOT/'art/wingb-room.hgr').write_bytes(data)
    (ROOT/'build').mkdir(exist_ok=True)
    decode(data).resize((1120,768),Image.Resampling.NEAREST).save(ROOT/'build/wingb-design.png')
    print('Wing B 8192 bytes,',sum(bin(v&127).count('1') for v in data),'lit pixels')
if __name__=='__main__':main()
