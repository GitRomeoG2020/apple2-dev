#!/usr/bin/env python3
"""Stamp-built SECURITY ROOM: compile the original art (gen_security.room) into
a small stamp library plus a room script, which the engine runs at door time to
draw the background into $8000 (see `stamps` in src/gbot.s).

Script commands (all coordinates in HGR rows and byte columns):
  $00                          end
  $01 row col n glyphs*n       text from the resident status font (5 rows)
  $02 col bit y n adx(2) ady f  line from pixel col*7+bit, Bresenham exactly as Pillow draws it; ORs
                               pixels in (f: 1 x steps left, 2 x-major, 4 even
                               pixels only, 8 odd pixels only, $10 palette bit,
                               $20 y steps up)
  $03 row col len p bytes*p    a row of a repeating p-byte pattern
  $04 row col w h bytes*w      a block: the same w bytes on h rows
  $05 id row col               a stamp from the library
  $06 count dx                 repeat the last line count times, dx pixels apart
Library stamp: h, then per row one or more spans: column offset, length
(bit 7 set: another span follows on this row), bytes. Length 0: empty row.
Everything except text and lines writes final bytes, so the order of those is
free; the compiler checks the result against the original art byte for byte.
Run after gen_security.py. Standard library plus Pillow (for the source art).
"""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from gen_concept import row_offset
from gen_workshop import GLYPHS,REPAIR_FONT,FLOOR,CLOCKS,message_pixels

def font_byte(ch,r):
    return message_pixels(ch.center(40))[r][20] if False else _fb(ch,r)
_FB={}
def _fb(ch,r):
    if (ch,r) not in _FB:
        rows=message_pixels(' '*20+ch+' '*19)  # 40 chars, glyph at column 20
        for rr in range(5):_FB[(ch,rr)]=rows[rr][20]
    return _FB[(ch,r)]

def bres(x0,y0,x1,y1):
    """Pillow's 1-pixel line (checked against ImageDraw)."""
    pts=[];dx=abs(x1-x0);dy=abs(y1-y0);xs=1 if x1>x0 else -1;ys=1 if y1>y0 else -1
    if dx>dy:
        e=2*dy-dx
        for _ in range(dx+1):
            pts.append((x0,y0))
            if e>=0:y0+=ys;e-=2*dx
            e+=2*dy;x0+=xs
    else:
        e=2*dx-dy
        for _ in range(dy+1):
            pts.append((x0,y0))
            if e>=0:x0+=xs;e-=2*dy
            e+=2*dx;y0+=ys
    return pts

# ---- the interpreter (the engine's `stamps` routine does exactly this) ----
def run(script,lib):
    out=bytearray(8192); i=0; last=None
    def put(y,c,v): out[row_offset(y)+c]=v
    def line(x,y,n,adx,ady,f):
        xs=-1 if f&1 else 1; ys=-1 if f&32 else 1
        e=(2*ady-adx) if f&2 else (2*adx-ady)
        for _ in range(n):
            a=row_offset(y)+x//7
            if f&16: out[a]|=128   # (the art's palette follows any blue pixel)
            if not((f&4 and x&1) or (f&8 and not x&1)): out[a]|=1<<(x%7)
            if f&2:
                if e>=0:y+=ys;e-=2*adx
                e+=2*ady;x+=xs
            else:
                if e>=0:x+=xs;e-=2*ady
                e+=2*adx;y+=ys
    while True:
        op=script[i]
        if op==0:
            assert i<len(script)
            return bytes(out)
        if op==1:
            row,col,n=script[i+1:i+4]; g=script[i+4:i+4+n]
            for r in range(5):
                for k,gl in enumerate(g):put(row+r,col+k,FONTROWS[r][gl])
            i+=4+n
        elif op==2:
            x=script[i+1]*7+script[i+2]; y,n=script[i+3],script[i+4]
            adx=script[i+5]|script[i+6]<<8; ady,f=script[i+7],script[i+8]
            last=[x,y,n,adx,ady,f]; line(*last)
            i+=9
        elif op==3:
            row,col,ln,p=script[i+1:i+5]; pat=script[i+5:i+5+p]
            for k in range(ln):put(row,col+k,pat[k%p])
            i+=5+p
        elif op==4:
            row,col,w,h=script[i+1:i+5]; pat=script[i+5:i+5+w]
            for r in range(h):
                for k in range(w):put(row+r,col+k,pat[k])
            i+=5+w
        elif op==5:
            sid,row,col=script[i+1:i+4]; s=lib[sid]; h=s[0]; j=1
            r=0
            while r<h:
                off,ln=s[j],s[j+1]
                for k in range(ln&127):put(row+r,col+off+k,s[j+2+k])
                j+=2+(ln&127)
                if not ln&128:r+=1
            i+=4
        elif op==6:
            count,dx=script[i+1],script[i+2]
            for _ in range(count):
                last[0]+=dx; line(*last)
            i+=3
        else:raise ValueError(op)

FONTROWS=[[_fb(ch,r) for ch in GLYPHS] for r in range(5)]

def compile_room(target,name='SECURITY',lines=()):
    script=bytearray(); lib=[]
    # 1. HUD text from the resident font.
    t=CLOCKS[name]
    for row,col,text in ((169,1,name),(169,39-len(t),t)):
        script+=bytes([1,row,col,len(text)])+bytes(GLYPHS.index(ch) for ch in text)
    ctl='WASD/ARROWS WALK   SPACE PROBE'; col=(40-len(ctl))//2
    script+=bytes([1,186,col,len(ctl)])+bytes(GLYPHS.index(ch) for ch in ctl)
    # 2. Long lines, ORed in.
    for (x0,y0,x1,y1,flags,*rep_) in lines:
        pts=[p for p in bres(x0,y0,x1,y1) if 0<=p[0]<280]
        assert pts[0]==(x0,y0)
        adx,ady=abs(x1-x0),abs(y1-y0)
        f=flags|(1 if x1<x0 else 0)|(2 if adx>ady else 0)|(32 if y1<y0 else 0)
        script+=bytes([2,x0//7,x0%7,y0,len(pts),adx&255,adx>>8,ady,f])
        if rep_:
            assert 0<rep_[1]<128 and all(0<=x0+k*rep_[1] and x0+k*rep_[1]+adx<280 for k in range(rep_[0]+1))
            script+=bytes([6,rep_[0],rep_[1]])
    T=[list(target[row_offset(y):row_offset(y)+40]) for y in range(192)]
    def wrong_set():
        S=run(bytes(script)+b'\0',lib)
        return {(y,c) for y in range(192) for c in range(40) if S[row_offset(y)+c]!=T[y][c]}
    W=wrong_set()
    # 3. Blocks: the same w bytes repeated down h rows (frames, walls, posts).
    def try_blocks():
        best=None
        for (y,c) in W:
            for w in range(1,9):
                if c+w>40:break
                pat=T[y][c:c+w]
                h=1
                while y+h<192 and T[y+h][c:c+w]==pat:h+=1
                cov=sum(1 for r in range(h) for k in range(w) if (y+r,c+k) in W)
                gain=cov-(5+w)
                if best is None or gain>best[0]:best=(gain,y,c,w,h,pat)
        return best
    # 4. Pattern rows: a repeating p-byte pattern along a row.
    def try_rows():
        best=None
        for (y,c) in W:
            for p in range(1,13):
                pat=T[y][c:c+p]
                if len(pat)<p:break
                ln=p
                while c+ln<40 and T[y][c+ln]==pat[ln%p]:ln+=1
                cov=sum(1 for k in range(ln) if (y,c+k) in W)
                gain=cov-(5+p)
                if best is None or gain>best[0]:best=(gain,y,c,ln,p,pat)
        return best
    while W:
        b=try_blocks(); r=try_rows()
        if max(b[0],r[0])<=1:break
        if b[0]>=r[0]:
            _,y,c,w,h,pat=b; script+=bytes([4,y,c,w,h])+bytes(pat)
            W-={(y+rr,c+k) for rr in range(h) for k in range(w)}
        else:
            _,y,c,ln,p,pat=r; script+=bytes([3,y,c,ln,p])+bytes(pat)
            W-={(y,c+k) for k in range(ln)}
    # 5. Stamps for what is left: clusters of nearby wrong bytes, row spans.
    left=sorted(W); S=set(left); seen=set(); comps=[]
    for pt in left:
        if pt in seen:continue
        q=[pt];seen.add(pt);comp=[]
        while q:
            a=q.pop();comp.append(a)
            for dy in (-1,0,1):
                for dx in (-2,-1,0,1,2):
                    nb=(a[0]+dy,a[1]+dx)
                    if nb in S and nb not in seen:seen.add(nb);q.append(nb)
        comps.append(comp)
    index={}
    for comp in comps:
        y0=min(p[0] for p in comp);y1=max(p[0] for p in comp);x0=min(p[1] for p in comp)
        data=bytearray([y1-y0+1])
        for y in range(y0,y1+1):
            cs=sorted(c for (yy,c) in comp if yy==y)
            if not cs:data+=b'\0\0';continue
            spans=[[cs[0],cs[0]]]
            for c in cs[1:]:
                if c-spans[-1][1]<=2:spans[-1][1]=c   # a short gap is cheaper kept
                else:spans.append([c,c])
            for k,(a,b_) in enumerate(spans):
                more=128 if k<len(spans)-1 else 0
                data+=bytes([a-x0,(b_-a+1)|more])+bytes(T[y][a:b_+1])
        data=bytes(data)
        if data not in index:index[data]=len(lib);lib.append(data)
        script+=bytes([5,index[data],y0,x0])
    script+=b'\0'
    assert run(bytes(script),lib)==bytes(target),'stamp room differs from the art'
    return bytes(script),lib

# The room's long strokes, drawn as lines (same order and colours as the art):
# floor perspective (blue), the patrol lane's 22 hazard stripes (white), the
# east door's slanted edges and the desk's front corner.
LINES=[(140+(x-140)//5,81,x,FLOOR+1,4|16) for x in (-210,-58,85,225,370,520)]
LINES+=[(12,124,16,118,0,21,12),(271,96,252,102,0),(252,150,271,156,0),(96,70,104,78,0)]

STAMPBASE=0x1000   # header: stamp count, address lows, address highs, script

def security():
    from gen_security import room
    return compile_room(room(False),lines=LINES)

def place(areas,script,lib):
    """Put a variant into memory areas [(image, free flags, base address)]:
    its header and script at the first area's start if that is an aux track
    ($1000), else first-fit; stamps (largest first) first-fit across the areas
    in order. Returns the header address."""
    n=len(lib); assert n<128
    size=1+2*n+len(script)
    def fit(ln,only=None):
        for img,fr,base in (areas if only is None else [only]):
            k=0
            while k+ln<=len(img):
                if all(fr[k:k+ln]):
                    for j in range(k,k+ln):fr[j]=False
                    return img,base+k
                k+=1
        raise AssertionError('stamp data does not fit')
    img0,fr0,base0=areas[0]
    if base0==STAMPBASE:
        assert all(fr0[:size]),'stamp script does not fit at $1000'
        for k in range(size):fr0[k]=False
        hdr=STAMPBASE;himg=img0
    else:
        himg,hdr=fit(size,areas[0])
    addr=[0]*n
    for sid in sorted(range(n),key=lambda k:-len(lib[k])):
        img,a=fit(len(lib[sid]))
        base=next(b for i,_,b in areas if i is img)
        img[a-base:a-base+len(lib[sid])]=lib[sid]; addr[sid]=a
    hb=next(b for i,_,b in areas if i is himg)
    himg[hdr-hb:hdr-hb+size]=bytes([n])+bytes(a&255 for a in addr)+bytes(a>>8 for a in addr)+script
    return hdr

def read_back(hdr,mem):
    """Script and library of the variant whose header is at `hdr`; mem(addr)
    returns the memory from addr on (aux track at $1000 or the pool)."""
    h=mem(hdr); n=h[0]; lo=h[1:1+n]; hi=h[1+n:1+2*n]
    return h[1+2*n:],[mem(l|k<<8) for l,k in zip(lo,hi)]

def from_aux(aux,base=0x1000,pool=b'',poolbase=0xD000):
    """Read the script and library of the aux-home variant back out."""
    def mem(a):
        return aux[a-base:] if base<=a<base+len(aux) else pool[a-poolbase:]
    return read_back(STAMPBASE,mem)

# The lab: its floor rays are the same blue lines as the security room's.
def lab():
    from gen_lab import room
    return compile_room(room(),'THE LAB',LINES[:6])

# The dark and lit power rooms: no long lines (its floor rays are dotted).
def power(on):
    from gen_power_room import room
    return compile_room(room(on),'POWER ROOM')

if __name__=='__main__':
    s,lib=security()
    print('security: script %d bytes, %d stamps %d bytes (+%d table)'%(len(s),len(lib),sum(map(len,lib)),1+2*len(lib)))
