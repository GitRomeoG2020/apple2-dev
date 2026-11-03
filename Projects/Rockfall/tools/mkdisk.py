#!/usr/bin/env python3
"""mkdisk.py rockfall.bin out.dsk : build a self-booting 140K DOS-order .dsk.
rockfall.bin = 4096-byte track-0 loader image + game image (loads at $6000).
256-byte chunk i of the file goes to track i//16, PHYSICAL sector i%16.
Byte 4 (loader 'ntracks') is set to the number of game tracks (ceil(game/4096))."""
import sys
P2L=[0,7,14,6,13,5,12,4,11,3,10,2,9,1,8,15]   # physical -> DOS 3.3 logical (.dsk file order)
b=bytearray(open(sys.argv[1],'rb').read())
g=len(b)-4096; assert 0<g<=0x6000, 'game is %d bytes; max 24576 ($6000-$BFFF)'%g
b[4]=(g+4095)//4096
img=bytearray(143360)
for i in range(0,len(b),256):
    c=b[i:i+256]; o=(i//4096)*4096+P2L[(i//256)%16]*256; img[o:o+len(c)]=c
open(sys.argv[2],'wb').write(img)
