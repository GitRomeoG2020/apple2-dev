#!/usr/bin/env python3
"""Original SUBSTATION background for G-Bot: After Hours. Pillow is ART-ONLY.

The small room behind the power room's east door: the MAIN BREAKER, its big
knife switch resting OFF on a striped plinth, cables climbing to the ceiling, a
wall transformer under a sign that says what it thinks of the idea, and a
coiled trickle lead on a hook. Its clock disagrees with everyone (11:59).
Drawn into $8000 from stamps on its aux track (tools/gen_stamps.py).
"""
from pathlib import Path
import math
from PIL import Image
from gen_concept import Paint, K,V,G,B,O,T,decode,row_offset
from gen_workshop import finish,clock_hands,FLOOR
from gen_power_room import lit, dots
ROOT=Path(__file__).resolve().parents[1]
NAME='SUBSTATION'
BREAKER=(102,176)   # cabinet x span (collision and the breaker apron, src/sfx.s)

def room():
    p=Paint()
    # Shell, same depth and HUD as the other rooms.
    p.line([(6,3),(273,3),(273,FLOOR-5)],B,2)
    p.line([(6,3),(6,FLOOR-4)],B,2)
    p.line([(9,7),(269,7)],V)
    p.line([(9,75),(271,75)],O)
    p.line([(9,80),(271,80)],B)
    # The clock: one minute to midnight, of course.
    p.ellipse((14,8,36,28),B); p.ellipse((17,10,33,26),K)
    clock_hands(p,25,18,NAME,4,7)
    for a in range(0,360,90):
        p.dot(lit(25+round(9*math.cos(math.radians(a))),T),18+round(9*math.sin(math.radians(a))),T)
    # Cables from the ceiling down into the cabinet.
    for x,c in ((114,B),(122,V),(158,V),(166,B)):
        p.line([(x,7),(x,14)],c,2)
    p.line([(40,11),(114,11)],B); p.line([(40,11),(40,30)],B)
    # THE MAIN BREAKER: a tall cabinet, its knife switch resting OFF.
    p.rect((102,14,178,92),K)
    p.line([(102,92),(102,14),(178,14),(178,92)],B,2)
    p.line([(108,20),(172,20),(172,72),(108,72),(108,20)],V)
    p.text(126,23,'MAIN',T)
    for x in (124,156):                       # hinges and the two blades, hanging down
        p.rect((x-3,34,x+3,38),T)
        p.line([(x,38),(x+2,60)],T,2)
        p.rect((x-3,40,x+3,42),O)              # the empty jaws above (switch is off)
    p.line([(126,62),(158,62)],T,2)            # the crossbar handle
    p.rect((139,62,141,68),O)                  # its grip
    p.line([(130,45),(152,45),(152,55),(130,55),(130,45)],B); p.text(134,48,'OFF',T)   # its window
    for i in range(6): p.dot(lit(150+i*4,O if i%2 else G),78,O if i%2 else G)   # meter dots
    p.line([(112,84),(168,84)],B)
    # The striped plinth.
    p.poly([(96,92),(184,92),(190,102),(90,102)],K)
    p.line([(96,92),(184,92),(190,102),(90,102),(96,92)],T)
    for x in range(94,188,10): p.line([(x,101),(x+5,93)],O)
    # The coiled trickle lead on a hook beside the cabinet.
    p.line([(186,30),(190,30),(190,34)],T)
    for i in range(3):
        p.ellipse((184+i,34+i*5,196-i,44+i*5),O); p.ellipse((186+i,36+i*5,194-i,42+i*5),K)
    p.line([(190,52),(188,62)],O); p.rect((186,62,190,65),T)    # its plug
    # Wall transformer, under a sign with an opinion.
    p.line([(206,22),(258,22),(258,44),(206,44),(206,22)],O)
    p.text(214,26,'DO NOT',T); p.text(216,35,'RERUN',T)
    p.rect((210,50,254,72),K)
    p.line([(210,72),(210,50),(254,50),(254,72)],B,2)
    for x in range(216,252,6): p.line([(x,53),(x,69)],V)
    p.rect((228,46,236,50),T)                  # bushing
    p.line([(232,46),(232,40)],B)
    # West door back to the power room, in perspective on the left wall.
    door=[(9,92),(30,98),(30,146),(9,152)]
    p.line(door+[door[0]],T)
    dots(p,[(13,96),(26,100)],B,4)
    p.rect((32,112,33,115),G)
    p.text(11,84,'PWR',G)
    # Floor: the same rays and seams as the lab, a warning box under the plinth.
    for x in (-210,-58,85,225,370,520):
        p.line([(140+(x-140)//5,81),(x,FLOOR+1)],B)
    for y in (113,137): p.line([(9,y),(271,y)],B)
    for x in range(100,184,8): p.line([(x,108),(x+4,108)],O)
    p.line([(8,FLOOR),(272,FLOOR)],O)
    return finish(p,NAME)

def main():
    data=room(); assert data==room(), 'Substation generation must be deterministic'
    used={row_offset(y)+b for y in range(192) for b in range(40)}
    assert all(data[i]==0 for i in set(range(8192))-used), 'Nonzero HGR holes'
    (ROOT/'art/substation-room.hgr').write_bytes(data)
    (ROOT/'build').mkdir(exist_ok=True)
    decode(data).resize((1120,768),Image.Resampling.NEAREST).save(ROOT/'build/substation-design.png')
    print('Substation 8192 bytes,',sum(bin(v&127).count('1') for v in data),'lit pixels')
if __name__=='__main__':main()
