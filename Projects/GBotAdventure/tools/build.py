#!/usr/bin/env python3
"""Reproducible dependency-light build: Python standard library + ca65/ld65.
Uses checked-in native art; regeneration separately requires Pillow.
"""
from pathlib import Path
import argparse, re, shutil, subprocess
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
    print('Built',out,'(boot: code T1-3 and stamp pool T4 into the language card, workshop + frames T5-8, aux T9; aux tracks and the lab T9-14; T15-34 free; read-only 140K disk)')

def make_disk(binary):
    # Boot track, 12K code (T1-3), workshop room + frames (T4-7), then the
    # aux tracks and full-art rooms in the order of src/layout.inc.
    b=bytearray(binary)
    layout=dict(re.findall(r'^(\w+)=(\d+)',(ROOT/'src/layout.inc').read_text(),re.M))
    want=[('CODE_TRACKS',1),('POOL_TRACK',4),('WORKSHOP_TRACK',5),('WORKAUX_TRACK',9),
          ('POWERAUX_TRACK',10),('GUARD_TRACK',11),('LAB_TRACK',12),('SCI_TRACK',14),('FREE_TRACK',15)]
    for k,t in want[1:]:assert int(layout[k])==t,(k,layout[k],'gbot.cfg order')
    assert int(layout['CODE_TRACKS'])==3 and b[4]==3, 'boot reads code tracks 1-3'
    assert b[0]==5, 'boot ROM loads sectors 0-4'
    assert len(b)==4096*int(layout['FREE_TRACK']), len(b)
    p2l=[0,7,14,6,13,5,12,4,11,3,10,2,9,1,8,15]
    out=bytearray(143360)
    for i in range(0,len(b),256):
        chunk=b[i:i+256]; offset=(i//4096)*4096+p2l[(i//256)%16]*256
        out[offset:offset+len(chunk)]=chunk
    return bytes(out)
if __name__=='__main__':main()
