#!/usr/bin/env python3
"""mkdisk.py game.bin out.dsk : write a 4K boot image onto track 0 of a blank 140K DOS-order .dsk.
Physical sector p of track 0 gets bytes p*256..p*256+255 (boot ROM loads physical order)."""
import sys
P2L=[0,7,14,6,13,5,12,4,11,3,10,2,9,1,8,15]   # physical -> DOS 3.3 logical (.dsk file order)
b=open(sys.argv[1],'rb').read(); assert len(b)<=4096
b=b.ljust(4096,b'\0'); img=bytearray(143360)
for p in range(16): img[P2L[p]*256:P2L[p]*256+256]=b[p*256:p*256+256]
open(sys.argv[2],'wb').write(img)
