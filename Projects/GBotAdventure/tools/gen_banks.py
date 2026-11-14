#!/usr/bin/env python3
"""Per-room "aux" tracks, each read whole into $1000-$1FFF with its room, and
the stamp pool: one 4K track read at boot into language-card bank 1
($D000-$DFFF), shared by every stamp-built room.
$1000-$143F is the engine's per-frame sprite scratch and status line buffer
(contents on disk are zero), $1440 the room's message bank, $1800 the room's
actor frames (guard or scientist), and any bank overflow after the frames.
Bank entries: id, length, glyphs...; $FE lo hi continues elsewhere; $FF ends.
Stamp-built rooms (tools/gen_stamps.py): each variant's header (stamp count,
address lows, highs) and script sit at $1000 of its room's aux track ("aux"
home: read with the room, drawn before the scratch area is reused) or in the
pool ("pool" home: drawn with no disk read, e.g. the power room lighting up
when the fuse goes in). Stamps go first-fit into the home's free bytes, then
the pool's. The engine maps bank 1 while it draws.
Run after gen_workshop.py, gen_security.py and gen_lab.py. Standard library only.
"""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from gen_workshop import MESSAGES,MSG_ROOMS,GLYPHS
BASE=0x1000; BANK=0x1440; ACTOR=0x1800; END=0x2000
ACTORS={0:None,1:None,2:'guard-sprites.bin',3:'scientist-sprites.bin'}
NAMES={0:'workshop',1:'power',2:'security',3:'lab'}
POOLBASE=0xD000; POOLEND=0xE000
# Stamp variants in engine order: rooms 0-3 as first entered, 4 = lit power room.
VARIANTS=('workshop','power','security','lab','powerlit')
def _security():
    from gen_stamps import security
    return security()
def _workshop():
    from gen_stamps import workshop
    return workshop()
def _lab():
    from gen_stamps import lab
    return lab()
def _power(on):
    def f():
        from gen_stamps import power
        return power(on)
    return f
# variant: (room, home, compiler). Every room is stamp-built now.
STAMPED={'workshop':(0,'aux',_workshop),'power':(1,'aux',_power(False)),'security':(2,'aux',_security),
         'lab':(3,'aux',_lab),'powerlit':(1,'pool',_power(True))}

def entries(room):
    for i in MSG_ROOMS[room]:
        text=MESSAGES[i]
        yield bytes([i,len(text)])+bytes(GLYPHS.index(ch) for ch in text)

def bank_image(room):
    out=bytearray(END-BASE)
    frames=(ROOT/'art'/ACTORS[room]).read_bytes() if ACTORS[room] else b''
    out[ACTOR-BASE:ACTOR-BASE+len(frames)]=frames
    regions=[(BANK,ACTOR)] if frames else [(BANK,END)]
    if frames: regions.append((ACTOR+len(frames),END))
    items=list(entries(room)); r=0; at=regions[0][0]
    taken=[(ACTOR,ACTOR+len(frames))]; start=at
    for item in items:
        if at+len(item)+3>regions[r][1]:     # leave room for a continuation
            r+=1; assert r<len(regions), NAMES[room]+' bank does not fit'
            nxt=regions[r][0]; out[at-BASE:at-BASE+3]=bytes([0xFE,nxt&255,nxt>>8])
            taken.append((start,at+3)); at=start=nxt
        out[at-BASE:at-BASE+len(item)]=item; at+=len(item)
    out[at-BASE]=0xFF; taken.append((start,at+1))
    assert all(v==0 for v in out[:BANK-BASE]), 'scratch area must stay empty on disk'
    used=sum(len(x) for x in items)+1
    return out,taken,used

_BUILT=None
def build():
    """All four aux images, the pool image, each variant's header address,
    bank bytes per room and free bytes left in each aux and the pool."""
    global _BUILT
    if _BUILT:return _BUILT
    from gen_stamps import place
    imgs={};free={};used={};bankend={}
    for room in range(4):
        out,taken,used[room]=bank_image(room)
        bankend[room]=(max(b for a,b in taken if b>a)-BASE+255)//256
        imgs[room]=out; free[room]=[True]*len(out)
        for a,b in taken:
            for k in range(a-BASE,b-BASE):free[room][k]=False
    pool=bytearray(POOLEND-POOLBASE); pfree=[True]*len(pool)
    hdr={}
    homes=[r for r,h,_ in STAMPED.values() if h=='aux']
    assert len(homes)==len(set(homes)),'one aux-home variant per room (its header is at $1000)'
    for key in VARIANTS:
        if key not in STAMPED:continue
        room,home,fn=STAMPED[key]; script,lib=fn()
        areas=[(imgs[room],free[room],BASE)] if home=='aux' else []
        areas.append((pool,pfree,POOLBASE))
        hdr[key]=place(areas,script,lib)
    # Aux sectors each variant's door reads: an aux-home stamped variant all
    # of it from sector 0; any other just the bank (and actor frames), 4..
    sectors=[]
    for v,key in enumerate(VARIANTS):
        room=v if v<4 else 1
        data=imgs[room]
        if key in STAMPED and STAMPED[key][1]=='aux':
            sectors.append((0,max(i for i,x in enumerate(data) if x)//256+1))
        else:sectors.append((4,bankend[room]))
    _BUILT=({r:bytes(imgs[r]) for r in imgs},bytes(pool),hdr,used,
            {r:sum(free[r]) for r in free},sum(pfree),sectors)
    return _BUILT

def aux(room):
    imgs,pool,hdr,used,*_=build()
    return imgs[room],used[room]

def main():
    imgs,pool,hdr,used,left,pleft,sectors=build()
    firsts=[a for a,b in sectors];ends=[b for a,b in sectors]
    for room in range(4):
        data=imgs[room]
        (ROOT/'art'/('aux-'+NAMES[room]+'.bin')).write_bytes(data)
        print('aux-%s.bin: %d messages, %d bank bytes, door reads sectors %d-%d, %d bytes free'%(NAMES[room],len(MSG_ROOMS[room]),used[room],firsts[room],ends[room]-1,left[room]))
    print('lit power room: door reads aux sectors %d-%d'%(firsts[4],ends[4]-1))
    (ROOT/'art/stamp-pool.bin').write_bytes(pool)
    print('stamp-pool.bin: %d bytes used, %d free'%(len(pool)-pleft,pleft))
    for k,a in hdr.items():print('  %s: header $%04X'%(k,a))
    # Doors read only the aux sectors that hold data (4..end-1): sectors 0-3
    # are scratch, and the tail of a short bank track is empty. A stamp-built
    # room's aux track is read from sector 0 (its script sits in the scratch).
    lo=[hdr.get(k,0)&255 for k in VARIANTS];hi=[hdr.get(k,0)>>8 for k in VARIANTS]
    (ROOT/'src/auxend.inc').write_text('; Generated by tools/gen_banks.py; do not hand edit.\n'
        '; per variant: workshop, power room, security, lab, lit power room\n'
        'auxend: .byte '+','.join(map(str,ends))+'   ; aux sectors a door reads: auxfirst..auxend-1\n'
        'auxfirst: .byte '+','.join(map(str,firsts))+'   ; (0: the stamp script is in sectors 0-3)\n'
        '; stamp header address; 0: full art\n'
        'stamplo: .byte '+','.join('$%02X'%v for v in lo)+'\n'
        'stamphi: .byte '+','.join('$%02X'%v for v in hi)+'\n')
if __name__=='__main__':main()
