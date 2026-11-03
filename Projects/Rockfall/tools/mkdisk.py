#!/usr/bin/env python3
"""mkdisk.py rockfall.bin out.dsk : build a self-booting 140K DOS-order .dsk.
rockfall.bin = 4096-byte track-0 loader image + game image (loads at $6000).
256-byte chunk i of the file goes to track i//16, PHYSICAL sector i%16.
Track 0 physical sector 15 = the high-score table (src/hsdef.inc defaults, from the loader image);
it is checked here ("RF", version 1, EOR of bytes $00-$2B = 0).
Byte 4 (loader 'ntracks') is set to the number of game tracks (ceil(game/4096))."""
import sys
P2L=[0,7,14,6,13,5,12,4,11,3,10,2,9,1,8,15]   # physical -> DOS 3.3 logical (.dsk file order)
b=bytearray(open(sys.argv[1],'rb').read())
g=len(b)-4096; assert 0<g<=0x6000, 'game is %d bytes; max 24576 ($6000-$BFFF)'%g
b[4]=(g+4095)//4096
img=bytearray(143360)
for i in range(0,len(b),256):
    c=b[i:i+256]; o=(i//4096)*4096+P2L[(i//256)%16]*256; img[o:o+len(c)]=c
hs=img[15*256:15*256+44]   # track 0: physical 15 = logical 15
x=0
for v in hs: x^=v
assert hs[40:43]==b'RF\x01' and x==0, 'high-score sector (T0 S15) missing/invalid'
open(sys.argv[2],'wb').write(img)
