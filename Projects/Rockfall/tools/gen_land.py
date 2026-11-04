#!/usr/bin/env python3
"""gen_land.py: build the Rockfall landscape strips -> src/land.inc (+ PNG previews in build/).

Each landscape is W=280 x H=32 pixels drawn at hi-res rows LANDY..LANDY+31, defined as a
colour grid: k black, w white, v violet, g green (palette 0), b blue, o orange (palette 1).
Pixel x is the absolute screen x, so colour parity is exact: violet/blue light even x,
green/orange odd x, white lights both.  Each 7-pixel byte gets palette 1 if it has more
blue/orange than violet/green pixels.

Add a landscape: write a function f(c) that paints into canvas c (c.set(x,y,ch), helpers
below, or c.ascii(...) to stamp ASCII art) and append (NAME, f) to LANDS.  To use art from
the a2sprite editor: export a 40-byte-wide x 32-row sprite as raw .bin (no mask/shifts) and
add ('NAME', 'raw:path/to/file.bin') -- the bytes are used as-is.

Compression (decoded by drawland in rockfall.s), a stream of 1280 bytes in screen order:
  ctl $00-$7F: ctl+1 literal bytes follow;  ctl $80-$FF: next byte repeated (ctl&$7F)+3 times.
"""
import math, os, sys
W, H = 280, 32
D = os.path.dirname(os.path.abspath(__file__)) + '/..'

class Canvas:
    def __init__(s, h=H): s.h = h; s.p = [['k'] * W for _ in range(h)]
    def set(s, x, y, ch):
        if 0 <= x < W and 0 <= y < s.h: s.p[y][x] = ch
    def col(s, x, top, ch, bot=None):        # fill column x rows top..bot-1
        for y in range(max(0, int(top)), s.h if bot is None else bot): s.set(x, y, ch)
    def rect(s, x0, y0, x1, y1, ch):
        for y in range(y0, y1):
            for x in range(x0, x1): s.set(x, y, ch)
    def ascii(s, x0, y0, art, sx=1, sy=1):   # ' ' / '.' = transparent; other chars = colour codes
        for j, line in enumerate(art.strip('\n').split('\n')):
            for i, ch in enumerate(line):
                if ch not in ' .':
                    for dy in range(sy):
                        for dx in range(sx): s.set(x0 + i * sx + dx, y0 + j * sy + dy, ch)

def wave(x, *terms):                        # sum of sines: (amplitude, period px, phase)
    return sum(a * math.sin(2 * math.pi * x / p + ph) for a, p, ph in terms)

# ---------------- landscapes ----------------
def mountains(c):
    for x in range(W):
        far = 16 + wave(x, (7, 97, 0.3), (4, 41, 1.0), (2, 17, 2.0))      # height in rows
        near = 8 + wave(x, (3, 71, 2.2), (2, 29, 0.4))
        top = H - far
        c.col(x, top, 'v')
        if far > 19: c.col(x, top, "w", int(top + (far - 19) * 1.2 + 1))  # snow caps
        c.col(x, H - near, 'g')
    c.rect(0, H - 2, W, H, 'g')

def city(c):
    import random
    r = random.Random(7); x = 0
    while x < W:
        w = r.choice([14, 18, 22, 28]); h = r.randint(9, 27)
        c.rect(x, H - h, x + w - 2, H, 'b')
        for wy in range(H - h + 3, H - 3, 4):                              # lit windows
            for wx in range(x + 3, x + w - 4, 4):
                if r.random() < 0.6: c.rect(wx, wy, wx + 2, wy + 2, 'o')
        if h > 22 and r.random() < 0.7: c.rect(x + w // 2 - 2, H - h - 4, x + w // 2, H - h, 'w')   # antenna
        x += w
    c.rect(0, H - 2, W, H, 'w')

LANDER = """
..wwww..
.ww..ww.
wwwwwwww
.w....w.
w......w
"""
def moon(c):
    for x in range(W):
        back = 13 + wave(x, (6, 53, 1.7), (3, 23, 0.2))                   # distant blue ridges
        c.col(x, H - back, 'b')
        ground = 7 + wave(x, (2, 89, 0.9), (1, 31, 2.5))
        c.col(x, H - ground, 'w')
    for cx, cy, rx, ry in ((40, 28, 14, 3), (120, 29, 9, 2), (200, 27, 18, 3), (255, 30, 7, 1)):
        for y in range(cy - ry, cy + ry + 1):
            for x in range(cx - rx, cx + rx + 1):
                d = ((x - cx) / rx) ** 2 + ((y - cy) / max(ry, 1)) ** 2
                if d <= 1: c.set(x, y, 'k' if d < 0.55 else 'b')
    c.ascii(150, H - 7 - 7, LANDER, sx=2)                                  # a lunar lander

def desert(c):
    for x in range(W):
        c.col(x, H - (6 + wave(x, (2, 61, 0.0), (1.5, 37, 1.3))), 'o')
    for px, base in ((70, 30), (150, 22), (225, 14)):                     # pyramids: lit / shaded faces
        for y in range(base):
            yy = H - 4 - y
            half = base - y
            c.rect(px - half, yy, px, yy + 1, 'w')
            c.rect(px, yy, px + half, yy + 1, 'o')
    c.rect(0, H - 2, W, H, 'o')

LANDS = [('MOUNTAINS', mountains), ('CITY', city), ('MOON', moon), ('DESERT', desert)]

# ---------------- encoding ----------------
def encode(c):
    rows = []
    for y in range(len(c.p)):
        row = []
        for b in range(40):
            px = [c.p[y][b * 7 + i] for i in range(7)]
            pal = 1 if sum(ch in 'bo' for ch in px) > sum(ch in 'vg' for ch in px) else 0
            v = pal << 7
            for i, ch in enumerate(px):
                x = b * 7 + i
                if ch == 'w' or (ch in 'vb' and x % 2 == 0) or (ch in 'go' and x % 2 == 1): v |= 1 << i
            row.append(v)
        rows.append(row)
    return rows

def rle(data):
    out, i, lit = [], 0, []
    def flush():
        while lit:
            n = lit[:128]; del lit[:128]; out.append(len(n) - 1); out.extend(n)
    while i < len(data):
        j = i
        while j < len(data) and data[j] == data[i] and j - i < 130: j += 1
        if j - i >= 3: flush(); out += [0x80 + j - i - 3, data[i]]; i = j
        else: lit.append(data[i]); i += 1
    flush(); return bytes(out)

def unrle(z):
    out, i = [], 0
    while i < len(z):
        c = z[i]; i += 1
        if c & 0x80: out += [z[i]] * ((c & 0x7F) + 3); i += 1
        else: out += list(z[i:i + c + 1]); i += c + 1
    return out

def render_png(rows, path):
    from PIL import Image
    im = Image.new('RGB', (W, len(rows))); px = im.load()
    for y, row in enumerate(rows):
        bits = [(v >> i) & 1 for v in row for i in range(7)]; hb = [v >> 7 for v in row for i in range(7)]
        for x in range(W):
            if not bits[x]: continue
            if (x > 0 and bits[x - 1]) or (x < W - 1 and bits[x + 1]): col = (255, 255, 255)
            elif hb[x]: col = (20, 207, 253) if x % 2 == 0 else (255, 106, 60)
            else: col = (255, 68, 253) if x % 2 == 0 else (20, 245, 60)
            px[x, y] = col
    im.resize((W * 2, len(rows) * 4 if len(rows) < 64 else len(rows) * 2), Image.NEAREST).save(path)

def build():
    out = ['; generated by tools/gen_land.py -- do not edit', 'NLAND = %d' % len(LANDS), 'LANDH = %d' % H, '']
    total = 0; names = []
    for k, (name, f) in enumerate(LANDS):
        if isinstance(f, str) and f.startswith('raw:'):
            raw = open(os.path.join(D, f[4:]), 'rb').read(); assert len(raw) == 40 * H, 'raw landscape must be 40x%d bytes' % H
            rows = [list(raw[y * 40:y * 40 + 40]) for y in range(H)]
        else:
            c = Canvas(); f(c); rows = encode(c)
        flat = [v for r in rows for v in r]; z = rle(flat); assert unrle(z) == flat
        total += len(z); names.append((name, len(z)))
        out.append('; %d: %s  (%d bytes raw -> %d RLE)' % (k, name, len(flat), len(z)))
        out.append('land%d:' % k)
        for i in range(0, len(z), 16): out.append('        .byte ' + ','.join('$%02X' % v for v in z[i:i + 16]))
        os.makedirs(D + '/build', exist_ok=True)
        try: render_png(rows, D + '/build/land%d_%s.png' % (k, name.lower()))
        except ImportError: pass
    out.append('landlo: .byte ' + ','.join('<land%d' % k for k in range(len(LANDS))))
    out.append('landhi: .byte ' + ','.join('>land%d' % k for k in range(len(LANDS))))
    out.append('; total %d bytes' % total)
    open(D + '/src/land.inc', 'w').write('\n'.join(out) + '\n')
    for n, s in names: print('%-10s %5d bytes (raw 1280)' % (n, s))
    print('total      %5d bytes' % total)

if __name__ == '__main__': build()
