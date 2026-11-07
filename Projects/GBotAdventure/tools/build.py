#!/usr/bin/env python3
"""Reproducible dependency-light build: Python standard library + ca65/ld65.
Uses checked-in native art; regeneration separately requires Pillow.
"""
from pathlib import Path
import argparse, shutil, subprocess
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(); p.add_argument('--cc65',type=Path)
    args=p.parse_args()
    candidates=[args.cc65,ROOT.parents[1]/'Tools/cc65/bin',Path('/workspace/apple2/bin')]
    def tool(name):
        for folder in candidates:
            if folder:
                for suffix in ('','.exe'):
                    if (folder/(name+suffix)).is_file():return str(folder/(name+suffix))
        found=shutil.which(name)
        if not found:raise SystemExit('Missing '+name+': use --cc65 /path/to/bin')
        return found
    build=ROOT/'build'; build.mkdir(exist_ok=True); (ROOT/'disk').mkdir(exist_ok=True)
    for name in ('boot','gbot'):
        subprocess.run([tool('ca65'),name+'.s','-o',str(build/(name+'.o')),'-l',str(build/(name+'.lst'))],cwd=ROOT/'src',check=True)
    subprocess.run([tool('ld65'),'-C','gbot.cfg',str(build/'boot.o'),str(build/'gbot.o'),'-o',str(build/'gbot.bin'),'-m',str(build/'gbot.map'),'-Ln',str(build/'gbot.lbl')],cwd=ROOT/'src',check=True)
    disk=make_disk((build/'gbot.bin').read_bytes()); out=ROOT/'disk/gbot-after-hours.dsk'; out.write_bytes(disk)
    print('Built',out,'(24576-byte load, read-only 140K disk)')

def make_disk(binary):
    b=bytearray(binary); size=len(b)-4096
    assert 0<size<=24576
    b[4]=(size+4095)//4096
    p2l=[0,7,14,6,13,5,12,4,11,3,10,2,9,1,8,15]
    out=bytearray(143360)
    for i in range(0,len(b),256):
        chunk=b[i:i+256]; offset=(i//4096)*4096+p2l[(i//256)%16]*256
        out[offset:offset+len(chunk)]=chunk
    return bytes(out)
if __name__=='__main__':main()
