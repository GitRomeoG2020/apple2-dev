#!/usr/bin/env python3
"""Original SECURITY ROOM background and guard-robot frames. Pillow is ART-ONLY.

art/security-room.hgr  -- native 8192-byte HGR screen, disk tracks 11-12.
art/guard-sprites.bin  -- 6 masked 28x30 frames, 270 bytes each (track 13 ->
                          $1800). Rows: 4 opacity bytes, 4 pixel bytes, phase.
The guard moves in whole bytes, so each pose is stored for even and odd byte
columns (HGR artifact colour depends on absolute pixel parity).
Frame n = pose*2 + (column & 1); poses: 0 dormant, 1 patrol A, 2 patrol B.
"""
from pathlib import Path
import math
from PIL import Image, ImageDraw
from gen_concept import Paint, K,V,G,B,O,T,encode,decode,row_offset
from gen_workshop import message_pixels,finish,clock_hands,FLOOR
from gen_power_room import lit, dots
ROOT=Path(__file__).resolve().parents[1]
GW,GH=28,30
GY=93                 # guard sprite top row; its feet stand on y=122
CLEAR=6

def room(open_=False):
    p=Paint()
    # Shell, same depth and HUD as the other rooms.
    p.line([(6,3),(273,3),(273,FLOOR-5)],B,2)
    p.line([(6,3),(6,FLOOR-4)],B,2)
    p.line([(9,7),(269,7)],V)
    for y in (34,70): p.line([(104,y),(206,y)],B)
    p.line([(9,75),(271,75)],O)
    p.line([(9,80),(271,80)],B)
    # Monitor wall over the desk: six little camera feeds.
    p.rect((12,12,102,64),K)
    p.line([(12,64),(12,12),(102,12),(102,64)],V,2)
    feeds=[(16,16),(44,16),(72,16),(16,40),(44,40),(72,40)]
    for i,(x,y) in enumerate(feeds):
        p.line([(x,y),(x+24,y),(x+24,y+20),(x,y+20),(x,y)],B)
        p.rect((x+2,y+2,x+22,y+18),K)
        if i==0:   # workshop: its rear door
            p.line([(x+8,y+16),(x+8,y+6),(x+16,y+6),(x+16,y+16)],B); p.dot(lit(x+14,G),y+11,G)
        elif i==1: # power room: the generator, gauge up
            p.line([(x+5,y+16),(x+5,y+7),(x+19,y+7),(x+19,y+16)],B); p.dot(lit(x+12,G),y+10,G)
        elif i==2: # corridor in perspective
            for a,b in (((x+3,y+3),(x+9,y+9)),((x+21,y+3),(x+15,y+9)),((x+3,y+17),(x+9,y+11)),((x+21,y+17),(x+15,y+11))):
                p.line([a,b],B)
            p.line([(x+9,y+9),(x+15,y+9),(x+15,y+11),(x+9,y+11),(x+9,y+9)],V)
        elif i==3: # static
            for yy in range(y+3,y+18,2):
                for xx in range(x+3+(yy%3),x+22,4): p.dot(xx,yy,T)
        elif i==4: # a small green-faced robot... on camera right now
            p.rect((x+9,y+5,x+15,y+10),T); p.rect((x+10,y+6,x+14,y+9),K)
            p.dot(lit(x+11,G),y+7,G); p.dot(lit(x+13,G),y+7,G)
            p.rect((x+9,y+11,x+15,y+15),T)
        else:      # REC light and an empty hallway
            p.line([(x+3,y+15),(x+21,y+15)],B); p.rect((x+3,y+3,x+5,y+5),O)
    # Security desk: heavy console with keys, phone and a mug.
    p.poly([(10,70),(96,70),(104,78),(10,78)],B)
    p.line([(10,70),(96,70),(104,78)],T)
    p.rect((12,79,100,96),K)
    p.line([(12,96),(12,79),(100,79),(100,96)],V)
    for x in range(18,92,6):
        p.line([(x,83),(x+3,83)],T)
    p.rect((20,88,40,92),O); p.rect((60,88,92,92),G)
    p.rect((78,63,88,69),T); p.rect((80,64,86,68),K); p.line([(77,66),(75,66)],T)  # phone
    p.rect((26,64,31,69),O); p.line([(32,65),(33,67)],O)                          # mug
    # Chair pushed back.
    p.line([(64,98),(64,110)],B,2); p.line([(56,110),(72,110)],V)
    p.rect((56,86,72,97),K); p.line([(56,97),(56,86),(72,86),(72,97)],B)
    # SECURITY sign over the north door to the lab; wall clock (its hands
    # disagree with the workshop's).
    p.text(120,20,'SECURITY',T)
    p.rect((116,30,170,74),K)
    p.line([(116,74),(116,30),(170,30),(170,74)],B,2)
    p.line([(120,72),(120,34),(166,34),(166,72)],V)
    p.line([(143,35),(143,71)],B)
    p.text(134,40,'LAB',O)
    p.rect((173,50,174,54),G if open_ else O)       # lock lamp (patched in RAM)
    p.ellipse((180,6,200,24),B); p.ellipse((183,8,197,22),K)
    clock_hands(p,190,15,'SECURITY',3,6)
    # Ceiling cameras on brackets, watching the floor.
    for x,sgn in ((112,1),(250,-1)):
        p.line([(x,8),(x,14)],B,2)
        p.poly([(x-8*sgn,14),(x+8*sgn,14),(x+10*sgn,20),(x-6*sgn,20)],T)
        p.rect((x+9*sgn-1,16,x+9*sgn+1,18),K); p.dot(lit(x-4*sgn,O),17,O)
    # Evidence lockers, right back wall.
    p.rect((208,26,262,74),K)
    p.line([(208,74),(208,26),(262,26),(262,74)],B,2)
    for x in (226,244): p.line([(x,28),(x,73)],B)
    for x in (218,236,254): p.rect((x,46,x+3,48),O)
    for y in (32,36): p.line([(212,y),(222,y)],V); p.line([(230,y),(240,y)],V); p.line([(248,y),(258,y)],V)
    # Floor perspective and seams.
    for x in (-210,-58,85,225,370,520):
        p.line([(140+(x-140)//5,81),(x,FLOOR+1)],B)
    for y in (93,137): p.line([(9,y),(271,y)],B)
    # PATROL LANE: hazard stripes along the guard's track, dock at its west end.
    p.line([(9,115),(271,115)],O); p.line([(9,127),(271,127)],O)
    for x in range(12,268,12):
        p.line([(x,124),(x+4,118)],T)
    p.rect((10,128,44,131),B); p.line([(12,129),(42,129)],T)
    # EAST DOOR back to the power room, open, lamp green.
    door=[(271,96),(252,102),(252,150),(271,156)]
    p.poly(door,K); p.line(door+[door[0]],T)
    p.line([(256,106),(256,146)],B)
    p.rect((246,118,247,121),G)
    p.line([(8,FLOOR),(272,FLOOR)],O)
    return finish(p,'SECURITY')

def guard(pose):
    """Squat dome-headed security unit. pose 0 dormant, 1/2 patrol steps."""
    im=Image.new('L',(GW,GH),CLEAR); d=ImageDraw.Draw(im)
    awake=pose>0
    # Beacon.
    d.rectangle((11,0,16,3),fill=K)
    d.rectangle((12,1,15,2),fill=(T if pose==1 else O) if awake else B)
    # Dome head with a wide visor.
    d.polygon([(8,4),(19,4),(23,8),(23,14),(4,14),(4,8)],fill=K)
    d.polygon([(9,5),(18,5),(21,8),(6,8)],fill=T)
    d.rectangle((5,9,22,13),fill=K)
    if awake:
        d.rectangle((6,10,21,12),fill=O)
        ex=9 if pose==1 else 16              # the eye sweeps as it rolls
        d.rectangle((ex,10,ex+2,12),fill=T)
    else:
        d.line([(7,11),(20,11)],fill=B)       # visor dark, standby line
    # Neck and armoured torso with a badge.
    d.rectangle((10,14,17,15),fill=K)
    d.rectangle((3,15,24,23),fill=K)
    d.rectangle((4,16,23,22),fill=B)
    d.line([(4,16),(23,16)],fill=T)
    d.polygon([(13,17),(15,19),(13,21),(11,19)],fill=T)   # badge
    # Stubby arms.
    for x in (0,25):
        d.rectangle((x,16,x+2,21),fill=K); d.line([(x+1,17),(x+1,20)],fill=T)
    # Tread base: lugs shift between the two patrol poses.
    d.rectangle((1,24,26,29),fill=K)
    d.line([(2,25),(25,25)],fill=T); d.line([(2,29),(25,29)],fill=T)
    off=0 if pose!=2 else 2
    for x in range(3+off,24,4): d.rectangle((x,26,x+1,28),fill=T)
    return im

def encode_guard(im,parity):
    out=bytearray()
    for y in range(GH):
        mask=[];data=[];colors=[]
        for b in range(4):
            m=v=0
            for i in range(7):
                x=b*7+i; c=im.getpixel((x,y)); ax=parity*7+x
                if c!=CLEAR: m|=1<<i; colors.append(c)
                if c==T or (c in (V,B) and ax%2==0) or (c in (G,O) and ax%2==1): v|=1<<i
            mask.append(m);data.append(v)
        phase=128 if sum(c in (B,O) for c in colors)>sum(c in (V,G) for c in colors) else 0
        out.extend(mask+data+[phase])
    return bytes(out)

def frames():
    return b''.join(encode_guard(guard(pose),par) for pose in range(3) for par in (0,1))

def lamp_patch():
    """Bytes that change when the lab door unlocks (applied by the engine)."""
    a,b=room(False),room(True)
    return [(i,a[i],b[i]) for i in range(8192) if a[i]!=b[i]]

def main():
    data=room()
    assert data==room()
    assert 0<len(lamp_patch())<=16
    lp=lamp_patch()
    inc=['; Generated by tools/gen_security.py; do not hand edit.',
         '; Lab-door lock lamp on the security room art: orange (locked) -> green.',
         f'SECPATCH_COUNT={len(lp)}',
         'secpatchlo:','.byte '+','.join(str(i&255) for i,_,_ in lp),
         'secpatchhi:','.byte '+','.join(str(i>>8) for i,_,_ in lp),
         'secpatch_off:','.byte '+','.join(str(a) for _,a,_ in lp),
         'secpatch_on:','.byte '+','.join(str(b) for _,_,b in lp)]
    (ROOT/'src/security.inc').write_text('\n'.join(inc)+'\n')
    used={row_offset(y)+b for y in range(192) for b in range(40)}
    assert all(data[i]==0 for i in set(range(8192))-used), 'Nonzero HGR holes'
    (ROOT/'art/security-room.hgr').write_bytes(data)
    f=frames(); assert len(f)==6*270
    (ROOT/'art/guard-sprites.bin').write_bytes(f)
    # Preview: guard composited at two columns with the engine's exact rule.
    screen=bytearray(data)
    for col,n in ((6,2),(19,5)):
        fr=f[n*270:(n+1)*270]
        for r in range(GH):
            row=fr[r*9:r*9+9]
            for b in range(4):
                at=row_offset(GY+r)+col+b
                if row[b]: screen[at]=(screen[at]&(~row[b]&127))|row[4+b]|row[8]
    (ROOT/'build').mkdir(exist_ok=True)
    decode(bytes(screen)).resize((1120,768),Image.Resampling.NEAREST).save(ROOT/'build/security-design.png')
    print('Security room 8192 bytes; guard frames',len(f),'bytes')
if __name__=='__main__':main()
