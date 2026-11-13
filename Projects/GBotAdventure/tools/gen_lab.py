#!/usr/bin/env python3
"""Original THE LAB background and flickering-scientist frames. Pillow is ART-ONLY.

art/lab-room.hgr        -- native 8192-byte HGR screen, disk tracks 14-15.
art/scientist-sprites.bin -- 4 masked 28x40 frames, 360 bytes each (track 16
                           -> $1800 when G-Bot enters the lab). Rows: 4 opacity
                           bytes, 4 pixel bytes, phase. Frame = pose*2 + (column&1);
                           pose 0 solid, 1 out-of-sync ghost (alternate rows).
"""
from pathlib import Path
import math
from PIL import Image, ImageDraw
from gen_concept import Paint, K,V,G,B,O,T,encode,decode,row_offset
from gen_workshop import message_pixels,finish,clock_hands,FLOOR
from gen_power_room import lit, dots
ROOT=Path(__file__).resolve().parents[1]
SW,SH=28,40
CLEAR=6
SPOTS=[(4,92),(25,100),(9,60)]   # scientist (byte column, top row); feet at row+39

def room():
    p=Paint()
    # Shell and back wall.
    p.line([(6,3),(273,3),(273,FLOOR-5)],B,2)
    p.line([(6,3),(6,FLOOR-4)],B,2)
    p.line([(9,7),(269,7)],V)
    p.line([(9,75),(271,75)],O)
    p.line([(9,80),(271,80)],B)
    # Lab clock: yet another time (about two minutes past six).
    p.ellipse((14,8,36,28),B); p.ellipse((17,10,33,26),K)
    clock_hands(p,25,18,'THE LAB',4,7)
    for a in range(0,360,90):
        p.dot(lit(25+round(9*math.cos(math.radians(a))),T),18+round(9*math.sin(math.radians(a))),T)
    # Consoles along the left back wall: racks, scopes, a big switch, printout.
    p.rect((10,32,94,86),K)
    p.line([(10,86),(10,32),(94,32),(94,86)],B,2)
    for x0 in (14,42,70):
        p.rect((x0,36,x0+20,50),B); p.rect((x0+2,38,x0+18,48),K)
    p.line([(17,44),(20,40),(23,46),(26,41),(30,44)],G)          # waveform
    p.line([(45,47),(48,47),(48,40),(53,40),(53,47),(59,47)],G)  # square wave
    for i in range(5): p.dot(lit(73+i*4,O),42+(i%2)*3,O)        # bar dots
    p.line([(10,56),(94,56)],T)
    for y in (60,66,72):
        for x in range(14,92,6):
            p.dot(lit(x+(y%4),G if (x+y)%3 else O),y,G if (x+y)%3 else O)
    p.rect((76,60,86,82),B); p.line([(81,62),(81,74)],T,2); p.rect((79,60,83,62),O)  # lever
    p.poly([(16,80),(40,80),(44,90),(20,90)],T)                  # printout curling
    for y in (83,86): p.line([(21,y),(38,y)],K)
    # THE TIME CHAMBER: a standing ring on a striped dais, humming violet/green.
    p.ellipse((102,10,178,90),T); p.ellipse((106,13,174,87),K)
    p.ellipse((110,17,170,83),B); p.ellipse((113,20,167,80),K)
    for i in range(120):                                          # the loop, spiralling
        a=i*0.37; r=2+i*0.22
        x=140+round(r*math.cos(a)); y=50+round(r*0.95*math.sin(a))
        c=V if i%2 else G
        p.dot(lit(x,c),y,c)
    for a in (0,60,120,180,240,300):                              # clamps on the ring
        x=140+round(38*math.cos(math.radians(a))); y=50+round(40*math.sin(math.radians(a)))
        p.rect((x-2,y-2,x+2,y+2),O)
    p.poly([(98,90),(182,90),(190,100),(90,100)],K)
    p.line([(98,90),(182,90),(190,100),(90,100),(98,90)],T)
    for x in range(96,186,10): p.line([(x,99),(x+5,91)],O)
    p.line([(94,96),(60,96),(56,86)],B)                            # cable to consoles
    p.line([(186,96),(206,96),(206,92)],B)                         # cable to the bay
    # PARKING / CHARGING BAY: a painted G-Bot outline and his name.
    p.rect((198,24,266,100),K)
    p.line([(198,100),(198,24),(266,24),(266,100)],B,2)
    p.text(213,28,'G-BOT',T)
    p.line([(208,36),(256,36)],O)
    outline=[(219,44),(223,42),(239,42),(244,46),(244,58),(241,62),(220,62),(216,58),(216,47),(219,44)]
    dots(p,outline,V,2)                                            # head
    dots(p,[(220,63),(220,74),(242,74),(242,63)],V,2)              # body
    dots(p,[(222,75),(222,84),(228,84)],V,2); dots(p,[(236,75),(236,84),(242,84)],V,2)
    p.line([(232,25),(232,38)],B); p.rect((230,38,234,40),T)        # charging arm
    p.rect((252,44,255,47),G); p.text(248,50,'+',G)                 # CHARGE lamp
    p.poly([(200,100),(264,100),(270,112),(194,112)],B)
    for x in (214,230,246): p.line([(x,103),(x+4,108),(x+8,103)],T)   # chevrons
    # Floor, a dropped clipboard page and a coffee cup still warm-looking.
    for x in (-210,-58,85,225,370,520):
        p.line([(140+(x-140)//5,81),(x,FLOOR+1)],B)
    for y in (113,137): p.line([(9,y),(271,y)],B)
    p.poly([(60,140),(72,138),(74,146),(62,148)],T)
    p.rect((210,140,214,145),O); p.line([(215,141),(216,143)],O)
    # Doorway back to the security room.
    p.line([(118,FLOOR),(166,FLOOR)],T)
    p.line([(116,FLOOR-6),(116,FLOOR)],O); p.line([(167,FLOOR-6),(167,FLOOR)],O)
    p.line([(8,FLOOR),(114,FLOOR)],O); p.line([(170,FLOOR),(272,FLOOR)],O)
    return finish(p,'THE LAB')

def scientist():
    """A scientist in a lab coat with a clipboard, mid-stride, mid-sentence."""
    im=Image.new('L',(SW,SH),CLEAR); d=ImageDraw.Draw(im)
    # Hair and head, glasses.
    d.ellipse((9,0,19,11),fill=K)
    d.rectangle((10,1,18,4),fill=O)                 # hair
    d.rectangle((10,5,18,10),fill=T)                # face
    d.rectangle((10,6,13,7),fill=K); d.rectangle((15,6,18,7),fill=K)   # glasses
    d.line([(12,9),(16,9)],fill=O)                  # mouth (talking)
    # Lab coat, collar, pocket pens.
    d.polygon([(6,12),(22,12),(25,30),(3,30)],fill=K)
    d.polygon([(7,13),(21,13),(23,29),(5,29)],fill=T)
    d.line([(14,13),(14,29)],fill=K)
    d.polygon([(11,13),(14,17),(17,13)],fill=B)     # shirt and tie
    d.line([(18,18),(18,21)],fill=G); d.line([(20,18),(20,21)],fill=O)
    # Arm holding a clipboard.
    d.rectangle((0,17,7,27),fill=K)
    d.rectangle((1,18,6,26),fill=O)                 # clipboard
    d.line([(2,20),(5,20)],fill=T); d.line([(2,23),(5,23)],fill=T)
    d.rectangle((2,17,5,18),fill=T)                 # clip
    # Trousers and shoes.
    d.rectangle((8,30,20,37),fill=K)
    d.rectangle((9,30,12,36),fill=B); d.rectangle((16,30,19,36),fill=B)
    d.rectangle((7,37,13,39),fill=K); d.rectangle((15,37,22,39),fill=K)
    d.line([(8,38),(12,38)],fill=T); d.line([(16,38),(21,38)],fill=T)
    return im

def encode_actor(im,parity,ghost=False):
    out=bytearray()
    for y in range(SH):
        mask=[];data=[];colors=[]
        for b in range(4):
            m=v=0
            for i in range(7):
                x=b*7+i; c=im.getpixel((x,y)); ax=parity*7+x
                if c==CLEAR or (ghost and y%2): continue
                m|=1<<i; colors.append(c)
                if c==T or (c in (V,B) and ax%2==0) or (c in (G,O) and ax%2==1): v|=1<<i
            mask.append(m);data.append(v)
        phase=128 if sum(c in (B,O) for c in colors)>sum(c in (V,G) for c in colors) else 0
        out.extend(mask+data+[phase])
    return bytes(out)

def frames():
    im=scientist()
    return b''.join(encode_actor(im,par,ghost) for ghost in (False,True) for par in (0,1))

def main():
    data=room(); assert data==room()
    used={row_offset(y)+b for y in range(192) for b in range(40)}
    assert all(data[i]==0 for i in set(range(8192))-used), 'Nonzero HGR holes'
    (ROOT/'art/lab-room.hgr').write_bytes(data)
    f=frames(); assert len(f)==4*360
    (ROOT/'art/scientist-sprites.bin').write_bytes(f)
    screen=bytearray(data)
    for (col,top),n in zip(SPOTS,(0,3,0)):
        fr=f[n*360:(n+1)*360]
        for r in range(SH):
            row=fr[r*9:r*9+9]
            for b in range(4):
                at=row_offset(top+r)+col+b
                if row[b]: screen[at]=(screen[at]&(~row[b]&127))|row[4+b]|row[8]
    (ROOT/'build').mkdir(exist_ok=True)
    decode(bytes(screen)).resize((1120,768),Image.Resampling.NEAREST).save(ROOT/'build/lab-design.png')
    print('Lab 8192 bytes; scientist frames',len(f),'bytes')
if __name__=='__main__':main()
