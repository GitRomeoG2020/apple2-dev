#!/usr/bin/env python3
"""Original playable workshop and 42x44 G-Bot frames. Pillow is ART-ONLY.
Checked-in native binaries let ca65 builds run without Python/Pillow on Windows.
Sprite rows: 6 opaque bytes, 6 pixel bytes, one shared phase byte.
Every x in the engine is even, preserving artifact color parity when shifting.
"""
from pathlib import Path
from PIL import Image, ImageDraw
from gen_concept import Paint, K,V,G,B,O,T,encode,decode,row_offset,FONT
ROOT=Path(__file__).resolve().parents[1]
FONT.update({
 'C':['01111','10000','10000','10000','01111'],
 'D':['11110','10001','10001','10001','11110'],
 'F':['11111','10000','11110','10000','10000'],
 'H':['10001','10001','11111','10001','10001'],
 'L':['10000','10000','10000','10000','11111'],
 'M':['10001','11011','10101','10001','10001'],
 'N':['10001','11001','10101','10011','10001'],
 'U':['10001','10001','10001','10001','01110'],
 'W':['10001','10001','10101','11011','10001'],
 'K':['10001','10010','11100','10010','10001'],
 'V':['10001','10001','10001','01010','00100'],
 'Y':['10001','01010','00100','00100','00100'],
 '+':['000','010','111','010','000'],
 ':':['0','1','0','1','0'],
 '/':['00001','00010','00100','01000','10000'],
})
SW,SH=42,44
CLEAR=6

def room():
    p=Paint()
    # Back wall: a deep, quiet workshop rather than a busy neon maze.
    p.line([(6,3),(273,3),(273,152)],B,2)
    p.line([(6,3),(6,153)],B,2)
    p.line([(9,7),(269,7)],T)
    for y in (34,70):
        p.line([(9,y),(271,y)],B)
    for x in (63,139,211):
        p.line([(x,9),(x,69)],B)
    p.line([(9,75),(271,75)],O)
    p.line([(9,80),(271,80)],B)
    # Ceiling conduit and small warm task light.
    p.line([(11,14),(96,14),(96,23)],B,2)
    p.line([(11,13),(94,13)],T)
    p.poly([(86,23),(103,23),(110,28),(79,28)],O)
    p.line([(83,29),(106,29)],T,2)
    # Pegboard tools: open wrench, screwdriver, pliers.
    p.rect((17,37,82,58),K)
    for y in (38,44,50,56):
        for x in range(19,82,8): p.dot(x,y,O)
    p.line([(28,40),(28,51)],T,2)
    p.line([(24,37),(24,40),(28,43),(32,40),(32,37)],T)
    p.rect((44,39,47,45),O); p.line([(45,46),(45,54)],T)
    p.line([(60,38),(64,43),(61,53)],T)
    p.line([(68,38),(64,43),(68,53)],O)
    # Left bench, small oscilloscope, parts tray and sturdy drawers.
    p.poly([(13,66),(84,66),(96,75),(13,75)],O)
    p.line([(13,66),(83,66),(95,74)],T)
    p.rect((14,77,87,81),B)
    p.rect((18,82,66,101),K)
    for y in (83,92):
        p.rect((19,y,65,y+7),B)
        p.line([(21,y),(63,y)],O)
        p.rect((39,y+3,46,y+3),K)
    p.line([(83,81),(83,103)],B,3)
    p.line([(18,101),(66,101)],B)
    p.rect((23,50,52,65),K)
    p.line([(23,65),(23,50),(49,50),(53,54),(53,65)],T)
    p.rect((27,54,45,62),B); p.rect((29,55,43,60),K)
    p.line([(29,59),(32,59),(34,56),(36,60),(38,57),(41,58)],G)
    p.rect((48,55,50,56),O); p.rect((48,60,50,61),T)
    p.poly([(61,69),(76,69),(82,73),(63,73)],G)
    for x in (65,71,77): p.line([(x,69),(x+2,72)],K)
    # Rear door -- decoration only in this first, single-room milestone.
    p.rect((113,28,172,74),K)
    p.line([(113,74),(113,28),(172,28),(172,74)],B,2)
    p.line([(117,72),(117,32),(168,32),(168,72)],V)
    p.line([(142,33),(142,71)],B)
    p.rect((159,51,162,54),O)
    p.rect((130,20,156,24),K)
    p.text(132,20,'01',O)
    # Clock, sleeping terminal, fan vents and cable loops.
    p.ellipse((183,18,205,34),B); p.ellipse((186,20,202,32),K)
    p.line([(194,22),(194,27),(199,27)],O)
    p.rect((225,40,263,109),K)
    p.line([(225,109),(225,40),(263,40),(263,109)],B,2)
    p.line([(229,44),(259,44),(259,105)],V)
    p.rect((232,49,252,64),B); p.rect((235,52,249,61),K)
    p.line([(237,58),(244,58)],G)
    for y in (71,75,79): p.line([(233,y),(253,y)],B)
    p.rect((233,87,236,89),O)
    p.line([(241,88),(252,88)],B)
    p.line([(233,99),(253,99)],B)
    p.line([(223,53),(215,53),(215,86),(221,93)],B)
    # Floor perspective, subtle seams. Movable sprite covers these cleanly.
    for x in (-210,-58,85,225,370,520):
        p.line([(140+(x-140)//5,81),(x,158)],B)
    for y in (93,113,137,157): p.line([(9,y),(271,y)],B)
    p.line([(8,157),(272,157)],O)
    # Rubber service mat, spare screws, coiled cable. None block movement.
    p.poly([(112,113),(170,113),(183,148),(99,148)],K)
    p.line([(112,113),(170,113),(183,148),(99,148),(112,113)],V)
    for y in (120,127,134,141): p.line([(110,y),(172,y)],B)
    p.line([(49,104),(50,111),(68,115),(80,120),(77,127),(61,129),(59,135),(74,139)],O)
    p.rect((26,142,31,144),B); p.line([(28,141),(29,141)],T)
    p.line([(208,144),(216,143),(220,146)],O)
    # Native HGR lettering keeps both text pages and resident loader untouched.
    p.line([(8,160),(271,160)],B)
    p.text(46,163,'G-BOT: AFTER HOURS',T,2)
    mini={
      'A':['010','101','111','101','101'], 'B':['110','101','110','101','110'],
      'C':['011','100','100','100','011'], 'D':['110','101','101','101','110'],
      'E':['111','100','110','100','111'], 'H':['101','101','111','101','101'],
      'I':['111','010','010','010','111'], 'K':['101','101','110','101','101'],
      'L':['100','100','100','100','111'], 'O':['010','101','101','101','010'],
      'P':['110','101','110','100','100'], 'R':['110','101','110','101','101'],
      'S':['011','100','010','001','110'], 'T':['111','010','010','010','010'],
      'W':['101','101','111','111','101'], '/':['001','001','010','100','100'],
      ' ':['000']*5, '-':['000','000','111','000','000'],
      '+':['000','010','111','010','000'], ':':['000','010','000','010','000'],
    }
    def small(x,y,text,color):
        for ch in text:
            for yy,line in enumerate(mini[ch]):
                for xx,v in enumerate(line):
                    if v=='1':p.rect((x+xx*2,y+yy,x+xx*2+1,y+yy),color)
            x+=8
    small(28,177,'WASD/ARROWS WALK - SPACE PROBE',T)
    small(48,186,'II+: HOLD REPT TO REPEAT',B)
    return encode(p.im)

def robot(direction=0,pose=0,blink=False,probe=False):
    im=Image.new('L',(SW,SH),CLEAR); d=ImageDraw.Draw(im)
    def r(b,c): d.rectangle(b,fill=c)
    def l(points,c,w=1): d.line(points,fill=c,width=w)
    def poly(points,c): d.polygon(points,fill=c)
    # Stable black silhouette includes the soles; body bob gives foot weight.
    bob=1 if pose==2 else 0
    # Ankle bellows and broad, staggered boots.
    for x,dy in ((10+(-1 if pose==1 else 1 if pose==2 else 0),-1 if pose==1 else 0),
                 (24+(1 if pose==1 else -1 if pose==2 else 0),-1 if pose==2 else 0)):
        r((x,33,x+7,39),K); r((x+2,34,x+5,39),B)
        l([(x+1,35),(x+6,35)],T); l([(x+1,37),(x+6,37)],T)
        poly([(x,38+dy),(x+7,38+dy),(x+10,41+dy),(x+10,43+dy),(x-2,43+dy),(x-2,41+dy)],K)
        poly([(x+1,39+dy),(x+6,39+dy),(x+8,41+dy),(x-1,41+dy)],T)
        l([(x-1,42+dy),(x+8,42+dy)],O)
        l([(x-1,43+dy),(x+9,43+dy)],T)
    # Grabber arm and probe: silhouette, elbow pin, metal upper edge.
    l([(10,26+bob),(6,29+bob),(4,25+bob)],K,5)
    l([(10,26+bob),(6,29+bob),(4,25+bob)],O,2)
    l([(7,28+bob),(8,28+bob)],T,2)
    l([(3,26+bob),(1,23+bob),(1,21+bob)],K,3)
    l([(3,25+bob),(1,23+bob),(1,21+bob)],T)
    l([(4,25+bob),(6,23+bob),(6,21+bob)],T)
    end=40 if probe else 37
    l([(31,26+bob),(34,29+bob),(end,26+bob)],K,5)
    l([(31,25+bob),(34,28+bob),(end,25+bob)],O,2)
    l([(34,28+bob),(end,25+bob)],T)
    if probe: l([(38,24+bob),(41,23+bob)],B)
    # Familiar sloped cream computer body, recessed drive, keyboard-like belly.
    poly([(11,21+bob),(28,21+bob),(33,25+bob),(32,34+bob),(10,34+bob),(8,29+bob)],K)
    poly([(12,22+bob),(27,22+bob),(30,25+bob),(11,25+bob)],T)
    r((10,26+bob,29,32+bob),T)
    r((30,26+bob,31,32+bob),O)
    r((13,26+bob,27,29+bob),K)
    l([(14,27+bob),(25,27+bob)],B)
    r((21,26+bob,23,27+bob),T)
    r((26,28+bob,27,29+bob),K if blink else O)
    l([(13,31+bob),(27,31+bob)],K)
    for x in (14,18,22,26): r((x,31+bob,x+1,31+bob),T)
    l([(11,33+bob),(28,33+bob)],O)
    # Neck and big CRT head: face occupies 20x11 pixels, never shrunk to a dot.
    r((17,19+bob,25,23+bob),K); l([(18,21+bob),(24,21+bob)],T)
    poly([(9,4+bob),(13,2+bob),(29,2+bob),(34,6+bob),(34,18+bob),(31,22+bob),(9,21+bob),(6,18+bob),(6,7+bob)],K)
    poly([(10,4+bob),(14,3+bob),(28,3+bob),(31,5+bob),(11,5+bob)],T)
    poly([(9,6+bob),(30,6+bob),(32,8+bob),(31,19+bob),(28,21+bob),(10,20+bob),(8,18+bob),(8,8+bob)],T)
    l([(33,7+bob),(33,17+bob),(31,20+bob)],G)
    r((10,8+bob,29,18+bob),K)
    l([(10,18+bob),(12,19+bob),(28,19+bob)],G)
    if direction==3:
        # Rear vents and service-label LED; this is an actual directional pose.
        for y in (10,13,16): l([(13,y+bob),(26,y+bob)],T)
        r((27,16+bob,28,17+bob),G)
    else:
        glance=-2 if direction==1 else 2 if direction==2 else 0
        if blink:
            l([(12,13+bob),(17,13+bob)],G)
            l([(23,13+bob),(28,13+bob)],G)
        else:
            l([(12,9+bob),(16,9+bob)],G)
            l([(24,10+bob),(28,10+bob)],G)
            r((12,11+bob,17,15+bob),G); r((23,11+bob,28,15+bob),G)
            r((14+glance//2,11+bob,15+glance//2,14+bob),K)
            r((25+glance//2,11+bob,26+glance//2,14+bob),K)
        l([(17,16+bob),(19,18+bob),(23,18+bob),(25,16+bob)],G)
        l([(11,8+bob),(13,8+bob)],T)
    # A small scuff and the crooked aerial from the portrait.
    l([(26,4+bob),(28,4+bob)],K)
    l([(26,2+bob),(28,0),(30,0)],T)
    r((30,0,31,1),G)
    out=bytearray()
    for y in range(SH):
        phase=128 if y>=23 else 0
        mask=[]; data=[]
        for b in range(6):
            m=v=0
            for i in range(7):
                x=b*7+i; c=im.getpixel((x,y))
                if c!=CLEAR: m|=1<<i
                if c==T or (c in (V,B) and x%2==0) or (c in (G,O) and x%2==1): v|=1<<i
            mask.append(m); data.append(v)
        out.extend(mask+data+[phase])
    return bytes(out)

def main():
    (ROOT/'build').mkdir(exist_ok=True)
    data=room(); (ROOT/'art/workshop-room.hgr').write_bytes(data)
    frames=[robot(d,p) for d in range(4) for p in range(3)]
    frames += [robot(blink=True),robot(probe=True)]
    assert all(len(f)==44*13 for f in frames)
    assert data==room(), 'Workshop generation must be deterministic'
    used={row_offset(y)+b for y in range(192) for b in range(40)}
    assert all(data[i]==0 for i in set(range(8192))-used), 'Nonzero HGR holes'
    for frame in frames:
        for off in range(0,len(frame),13):
            row=frame[off:off+13]
            assert row[12] in (0,128) and all(v<128 for v in row[:12])
            assert all((v&~m)==0 for m,v in zip(row[:6],row[6:12])), 'Pixels outside opacity'
    (ROOT/'art/gbot-sprites.bin').write_bytes(b''.join(frames))
    # Preview composited native bytes at even x; exact same source format as engine.
    screen=bytearray(data); x0,y0=126,104
    f=frames[0]
    for y in range(44):
        m=f[y*13:y*13+6]; v=f[y*13+6:y*13+12]; phase=f[y*13+12]
        for b in range(6):
            at=row_offset(y0+y)+x0//7+b
            screen[at]=((screen[at]&(~m[b]&127))|v[b]|phase) if m[b] else screen[at]
    decode(screen).crop((0,0,280,160)).resize((1120,640),Image.Resampling.NEAREST).save(ROOT/'build/workshop-design.png')
    print('Workshop: 8192 bytes; 14 masked 42x44 frames:',len(b''.join(frames)),'bytes')
if __name__=='__main__':main()
