#!/usr/bin/env python3
"""Original G-Bot workshop illustration: authored pixels -> real page-one Apple II HGR.

Requires Pillow. No random inputs, external artwork, fonts or Rockfall imports.
Palette/parity encoding follows the workshop's Rockfall gen_land.py convention;
all previews are decoded from the emitted 8192-byte screen, never the paint canvas.
"""
from pathlib import Path
from PIL import Image, ImageDraw
import hashlib

W, H = 280, 192
K, V, G, B, O, T = range(6)  # black, violet, green, blue, orange, white
ROOT = Path(__file__).resolve().parents[1]
FONT = {
 'G':['01110','10000','10111','10001','01110'],
 'B':['11110','10001','11110','10001','11110'],
 'O':['01110','10001','10001','10001','01110'],
 'T':['11111','00100','00100','00100','00100'],
 'R':['11110','10001','11110','10100','10010'],
 'E':['11111','10000','11110','10000','11111'],
 'P':['11110','10001','11110','10000','10000'],
 'A':['01110','10001','11111','10001','10001'],
 'I':['111','010','010','010','111'],
 'S':['01111','10000','01110','00001','11110'],
 '0':['111','101','101','101','111'],
 '1':['010','110','010','010','111'],
 '-':['000','000','111','000','000'],
 ' ':['00']*5,
}

class Paint:
    def __init__(self):
        self.im = Image.new('L', (W,H), K)
        self.d = ImageDraw.Draw(self.im)
    def rect(self, box, c): self.d.rectangle(box, fill=c)
    def line(self, pts, c, width=1): self.d.line(pts, fill=c, width=width)
    def poly(self, pts, c): self.d.polygon(pts, fill=c)
    def ellipse(self, box, c): self.d.ellipse(box, fill=c)
    def dot(self,x,y,c):
        if 0 <= x < W and 0 <= y < H: self.im.putpixel((x,y),c)
    def text(self,x,y,s,c,scale=1):
        for ch in s:
            glyph=FONT[ch]
            for dy,row in enumerate(glyph):
                for dx,v in enumerate(row):
                    if v=='1': self.rect((x+dx*scale,y+dy*scale,x+(dx+1)*scale-1,y+(dy+1)*scale-1),c)
            x+=(len(glyph[0])+1)*scale
    def texture(self,box,c,mod=4):
        x0,y0,x1,y1=box
        for y in range(y0,y1+1):
            for x in range(x0,x1+1):
                if (x+2*y)%mod==0: self.dot(x,y,c)


def draw():
    p=Paint()
    # Cool, recessive workshop walls. Broken horizontal seams, not a noisy backdrop.
    p.rect((0,0,279,130),K)
    # Large unlit areas let the phosphor face read first.
    for x,y in ((18,20),(46,20),(115,20),(235,18),(195,52),(202,91),(12,85)):
        p.line([(x,y),(x+8,y)],B)
    p.line([(92,35),(92,67)],B)
    p.line([(206,44),(206,88)],B)
    for x,y in ((10,32),(89,32),(202,34),(267,34),(12,98),(201,96)):
        p.rect((x,y,x+1,y+1),O)
    for y in (29,61,94):
        p.line([(0,y),(91,y)],B); p.line([(193,y),(279,y)],B)
    p.line([(7,0),(7,125)],B,2)
    p.line([(270,0),(270,128)],B,2)
    # Overhead conduit and suspended task lamp, warm pool of light.
    p.line([(0,8),(211,8),(211,17)],B,3)
    p.line([(0,7),(210,7)],T)
    p.line([(73,8),(73,22)],O,2)
    p.poly([(58,23),(85,23),(94,30),(49,30)],K)
    p.line([(58,23),(85,23),(94,30),(49,30),(58,23)],O)
    p.rect((56,30,87,32),T)
    for y in range(35,83,3):
        for x in range(54-(y-35)//4,91+(y-35)//4,8):
            if (x+y)%5==0: p.dot(x,y,O)
    # Wall pegboard and deliberately recognizable hand tools.
    p.rect((14,43,70,78),K)
    p.line([(14,78),(14,43),(70,43)],B)
    p.texture((18,46,67,75),O,13)
    p.line([(23,52),(23,66)],T,2)
    p.line([(19,48),(19,52),(23,55),(27,52),(27,48)],T,2)
    p.line([(38,50),(38,63)],O,3); p.line([(38,63),(38,71)],T)
    p.line([(49,50),(57,58),(57,69)],T,2)
    p.line([(49,50),(54,47)],T,2)
    # Left workbench: CRT oscilloscope, board, spool and drawers.
    p.poly([(0,95),(71,95),(88,107),(0,107)],O)
    p.line([(0,95),(71,95),(88,107)],T)
    p.rect((0,108,78,112),K); p.line([(0,109),(78,109)],O)
    p.rect((5,113,59,148),K)
    for y in (115,127,139):
        p.rect((8,y,55,y+9),B); p.rect((27,y+2,37,y+3),K)
        p.line([(9,y),(54,y)],O)
    p.line([(66,113),(67,148)],B,4)
    p.poly([(17,79),(22,74),(49,74),(54,80),(54,94),(17,94)],K)
    p.line([(17,94),(17,79),(22,74),(49,74)],T)
    p.rect((22,79,44,90),B); p.rect((24,81,42,88),K)
    p.line([(25,85),(28,85),(30,82),(32,87),(34,83),(38,85),(41,85)],G)
    p.rect((47,82,49,84),O); p.rect((47,88,49,90),T)
    p.rect((24,95,47,96),B)
    p.poly([(57,98),(68,98),(76,103),(63,103)],G)
    for x in (63,67,71): p.line([(x,99),(x+2,102)],K)
    p.ellipse((3,87,13,95),B); p.ellipse((6,89,10,92),K)
    # Rear right: shadowed equipment bay with a sleeping service terminal.
    p.rect((216,38,263,128),K)
    p.line([(215,129),(215,37),(264,37),(264,129)],B,2)
    p.line([(219,42),(259,42),(259,123)],V)
    p.rect((225,51,251,69),B); p.rect((228,54,248,66),K)
    p.line([(232,62),(240,62)],G)
    for y in (78,82,86): p.line([(226,y),(249,y)],B)
    p.rect((226,96,230,98),O)
    p.line([(235,97),(249,97)],B)
    p.line([(225,111),(250,111)],B)
    p.text(223,24,'01',B)
    # Clock: its hands still disagree with the rest of the quiet room.
    p.ellipse((178,15,202,35),B); p.ellipse((182,18,198,32),K)
    p.line([(190,20),(190,26),(195,26)],O)
    # Perspective floor and cable loops. Sparse rather than solid neon.
    p.poly([(0,131),(279,131),(279,191),(0,191)],K)
    p.line([(0,132),(279,132)],B)
    for x in (-170,-45,75,205,340,465):
        p.line([(140+(x-140)//4,132),(x,191)],B)
    for y in (143,161,187): p.line([(0,y),(279,y)],B)
    p.line([(48,145),(49,153),(65,158),(83,158),(91,164),(88,172),(64,173),(58,177),(60,183),(89,185),(111,179)],O,2)
    p.line([(252,127),(247,138),(231,140),(227,150),(208,156)],B,2)
    # Hero's grounding shadow masks floor seams.
    p.ellipse((91,158,192,177),K)
    p.texture((104,171,182,176),O,6)
    # Legs and oversized staggered work boots, with accordion ankle joints.
    for x,y in ((111,140),(151,142)):
        p.rect((x,y,x+17,y+16),K)
        p.rect((x+3,y,x+13,y+14),B)
        for yy in range(y+2,y+12,4): p.line([(x+2,yy),(x+14,yy)],T)
    p.poly([(109,151),(129,151),(133,159),(132,168),(99,168),(99,160)],K)
    p.poly([(110,153),(127,153),(130,159),(102,160)],T)
    p.poly([(102,162),(129,161),(129,165),(101,165)],O)
    p.line([(102,167),(130,167)],T)
    p.poly([(151,153),(171,153),(184,161),(184,170),(149,170),(145,164)],K)
    p.poly([(152,155),(169,155),(179,161),(149,162)],T)
    p.poly([(151,164),(181,163),(181,167),(151,167)],O)
    p.line([(153,169),(183,169)],T)
    for x,y in ((106,163),(115,163),(157,165),(168,165)):
        p.line([(x,y),(x+2,y)],K)
    # Arms behind the body: bent left elbow and telescoping right probe.
    p.line([(108,113),(90,108),(81,89)],K,14)
    p.line([(106,110),(92,105),(84,89)],O,8)
    p.line([(103,108),(94,103),(86,89)],T,3)
    p.ellipse((86,99,98,111),K); p.ellipse((89,101,95,108),B)
    p.line([(171,111),(185,119),(196,116)],K,14)
    p.line([(172,109),(185,116),(196,113)],O,7)
    p.line([(174,107),(184,112)],T,3)
    p.ellipse((180,112,190,122),K); p.ellipse((182,113,187,118),T)
    p.line([(194,114),(207,108)],K,8)
    p.line([(194,113),(207,107)],T,4)
    p.line([(200,111),(201,108)],K,2)
    p.line([(206,107),(215,102)],G,2)
    p.line([(216,99),(216,104)],T)
    # Open grabber delicately holding a loose little logic module.
    p.poly([(78,89),(74,83),(75,74),(79,70),(82,72),(78,77),(79,82),(85,83),(90,78),(91,72),(94,73),(94,82),(87,90)],K)
    p.line([(80,87),(76,81),(77,75),(80,72)],T,3)
    p.line([(84,87),(91,81),(92,74)],O,3)
    p.rect((79,68,89,76),K); p.rect((81,69,87,74),G)
    for x in (80,84,88): p.line([(x,66),(x,68)],T)
    # Sloping Apple-II-like main enclosure and side panel.
    p.poly([(108,99),(163,96),(179,110),(179,137),(166,147),(108,144),(99,132),(100,111)],K)
    p.poly([(107,102),(160,99),(172,110),(111,113),(103,110)],T)
    p.poly([(105,113),(167,112),(168,140),(110,140),(103,131)],T)
    p.poly([(170,112),(176,111),(176,135),(170,140)],O)
    p.line([(109,142),(165,144),(176,136)],B,2)
    # Recessed chest disk slot, latch and amber activity light.
    p.rect((115,115,160,125),K)
    p.line([(117,117),(156,117)],O)
    p.rect((119,120,154,121),B)
    p.rect((139,117,145,121),T)
    p.rect((156,121,158,123),O)
    # Tiny keyboard-like tool selector on the belly, individual key caps.
    p.poly([(112,128),(160,128),(163,136),(114,136)],K)
    for row in range(2):
        for key in range(9):
            x=116+key*5+row
            p.rect((x,129+row*3,x+2,130+row*3),O if key>6 else T)
    p.line([(126,137),(148,137)],K)
    for x,y in ((107,116),(164,115),(111,137),(164,137)): p.rect((x,y,x+1,y+1),K)
    p.line([(105,123),(107,125),(106,128)],O)
    # A battered service sticker and chips along the cream-colored lower lip.
    p.line([(108,132),(111,133)],O)
    for xx in range(115,164,7): p.line([(xx,139),(xx+2,139)],K)
    # Neck collar.
    p.rect((125,94,151,102),K); p.rect((128,95,148,99),O)
    p.line([(130,96),(146,96)],T)
    # Head: asymmetric top/side facets and beveled cream CRT bezel.
    p.poly([(102,47),(112,40),(162,40),(180,52),(180,91),(170,101),(106,99),(96,89),(96,57)],K)
    p.poly([(102,48),(113,42),(161,42),(172,49),(109,51)],T)
    p.poly([(174,51),(178,54),(178,89),(172,96),(169,93),(170,57)],O)
    p.poly([(102,51),(165,51),(171,57),(169,92),(164,97),(106,95),(99,88),(99,58)],T)
    # Cream impression = sparse warm hatching, not an impossible beige palette.
    p.line([(103,91),(109,94),(163,94)],O,2)
    for yy in range(60,87,3): p.line([(102,yy),(103,yy)],K)
    for xx in range(113,155,6): p.line([(xx,95),(xx+2,95)],K)
    p.line([(101,58),(101,85)],O)
    p.poly([(109,56),(160,55),(165,61),(163,85),(158,90),(111,88),(105,83),(105,62)],K)
    p.line([(110,58),(159,57),(163,61)],B)
    p.line([(108,64),(108,80)],G)
    # Expressive phosphor eyes, a raised brow and crooked friendly smile.
    p.line([(117,65),(122,62),(129,63)],G,2)
    p.line([(143,63),(152,65)],G,2)
    p.rect((118,68,129,76),G); p.rect((143,69,154,77),G)
    p.rect((122,68,127,74),K); p.rect((146,69,151,75),K)
    p.line([(127,81),(131,84),(142,84),(148,80)],G,2)
    # Glass gleam in an otherwise dark display and battered casing marks.
    p.line([(112,60),(117,60)],T)
    p.line([(111,62),(113,62)],G)
    p.line([(155,45),(162,46)],K)
    p.line([(157,46),(160,46)],O)
    p.line([(102,87),(105,89)],K)
    p.line([(167,66),(168,71)],K)
    for y in (61,66,71,76,81): p.line([(174,y),(176,y-1)],K)
    p.rect((111,92,113,93),K); p.rect((159,92,161,93),G)
    # Bent aerial with orange cap: curious, not military.
    p.line([(150,40),(153,33),(159,30)],K,3)
    p.line([(150,39),(153,33),(159,30)],T)
    p.rect((158,28,162,30),O)
    # A few purposeful scuffs and floor detritus.
    p.line([(211,167),(218,166),(222,168)],O)
    p.rect((28,173,34,175),B); p.rect((30,172,32,173),T)
    # Small signature/title only; the face, not typography, owns the composition.
    p.rect((198,173,271,189),K)
    p.text(207,177,'G-BOT',T)
    p.line([(207,185),(254,185)],O)
    return p.im


def row_offset(y):
    """Offset into $2000 page: interleaved 8-line bands and three 64-line blocks."""
    return ((y & 7) << 10) | (((y >> 3) & 7) << 7) | ((y >> 6) * 40)


def encode(canvas):
    out=bytearray(8192)
    for y in range(H):
        for b in range(40):
            colors=[canvas.getpixel((7*b+i,y)) for i in range(7)]
            phase=int(sum(c in (B,O) for c in colors)>sum(c in (V,G) for c in colors))
            value=phase<<7
            for i,c in enumerate(colors):
                x=b*7+i
                if c==T or (c in (V,B) and x%2==0) or (c in (G,O) and x%2==1):
                    value|=1<<i
            out[row_offset(y)+b]=value
    return bytes(out)


def decode(screen):
    """Discrete artifact preview, same neighbor/parity model as Rockfall.

    Adjacent lit bits become white; isolated bits take parity/byte-phase colors.
    This is a crisp digital approximation, not an analog NTSC/CRT simulation.
    """
    assert len(screen)==8192
    im=Image.new('RGB',(W,H))
    for y in range(H):
        row=screen[row_offset(y):row_offset(y)+40]
        bits=[(v>>i)&1 for v in row for i in range(7)]
        for x,on in enumerate(bits):
            if not on: continue
            if (x and bits[x-1]) or (x<W-1 and bits[x+1]): color=(255,255,255)
            elif row[x//7]&128: color=(20,207,253) if x%2==0 else (255,106,60)
            else: color=(255,68,253) if x%2==0 else (20,245,60)
            im.putpixel((x,y),color)
    return im


def validate(screen):
    assert len(screen)==8192
    used=[row_offset(y)+b for y in range(H) for b in range(40)]
    assert len(set(used))==7680 and min(used)==0 and max(used)==8183
    assert all(screen[i]==0 for i in set(range(8192))-set(used))
    assert encode(draw())==screen, 'Non-deterministic art'
    assert any(v&128 for v in screen) and any(v&127 for v in screen)


def main():
    art=ROOT/'art'; art.mkdir(exist_ok=True)
    data=encode(draw()); validate(data)
    (art/'gbot-workshop.hgr').write_bytes(data)
    image=decode((art/'gbot-workshop.hgr').read_bytes())
    image.save(art/'gbot-workshop-280.png')
    image.resize((W*4,H*4),Image.Resampling.NEAREST).save(art/'gbot-workshop.png')
    print(f'HGR: {len(data)} bytes; 7680 display bytes + 512 zero padding bytes')
    print('SHA-256:',hashlib.sha256(data).hexdigest())
    print('Preview:',art/'gbot-workshop.png')

if __name__=='__main__': main()
