#!/usr/bin/env python3
"""gen_title.py: the Rockfall hi-res title art -> src/title.inc (+ build/title.png preview).

280x160 (mixed mode: text rows 20-23 below hold the prompts). Drawn back to front:
starfield, curved planet limb with a glowing atmosphere, flaming meteors with fire trails falling
diagonally (one smashing into the logo), the chunky cratered 'ROCKFALL' logo with a white bevel
on orange rock, and a small ship.  Uses gen_land's colour canvas (k w v g b o), encoder and RLE.
Also emits: the twinkle star list (row, col, mask) and the animated streak sprite."""
import math, os, random
import gen_land as G
W, H = 280, 160
D = os.path.dirname(os.path.abspath(__file__)) + '/..'
FONT = {
 'R': ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
 'O': [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
 'C': [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
 'K': ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
 'F': ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
 'A': [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
 'L': ["#....", "#....", "#....", "#....", "#....", "#....", "#####"]}
LOGO_X, LOGO_Y, CW, CH = 23, 44, 5, 6           # cell size in px; logo = 47x7 cells = 235x42 px
STREAK = """
##.#.................
...####.#............
........######.#.....
..............#######
...............######
................####..
"""

def meteor(c, hx, hy, r, length, dx=2.0, dy=1.0, seed=0):
    rnd = random.Random(seed); n = math.hypot(dx, dy); ux, uy = -dx / n, -dy / n     # trail points up-left
    for t in range(length):
        f = t / length; w = max(0.5, r * (1 - f) + 0.5)
        for s in range(-int(w) - 1, int(w) + 2):
            if abs(s) > w: continue
            x = int(hx + ux * t - uy * s); y = int(hy + uy * t + ux * s)
            p = (1 - f) ** 1.3
            if rnd.random() < p: c.set(x, y, 'w' if (f < 0.12 and abs(s) < w * 0.5) else 'o')
    for y in range(-r, r + 1):
        for x in range(-r - 1, r + 2):
            if (x / (r + 0.6)) ** 2 + (y / (r + 0.3)) ** 2 <= 1: c.set(hx + x, hy + y, 'w')
    if r >= 4:                                                   # craters on the rock
        c.set(hx - 1, hy - 1, 'k'); c.set(hx + 2, hy + 1, 'k'); c.set(hx + 1, hy + 1, 'k')

def planet(c):
    cx, cy, R = 140, 160 + 520, 560
    for y in range(110, H):
        for x in range(W):
            d = math.hypot(x - cx, y - cy)
            if d < R:
                band = math.sin(x / 23.0 + y / 3.5) + 0.6 * math.sin(x / 9.0 - y / 2.0)
                c.set(x, y, 'w' if (band > 1.15 and d < R - 2) else 'b')
            elif d < R + 2: c.set(x, y, 'w')                      # bright limb
            elif d < R + 7 and (x + y) % 2 == 0 and random.Random(x * 997 + y).random() < 1 - (d - R - 2) / 5:
                c.set(x, y, 'b')                                  # glowing atmosphere, fading out

def logo(c):
    word = 'ROCKFALL'; cells = set()
    for i, ch in enumerate(word):
        for ry, row in enumerate(FONT[ch]):
            for rx, v in enumerate(row):
                if v == '#': cells.add((i * 6 + rx, ry))
    for (gx, gy) in cells:
        x0, y0 = LOGO_X + gx * CW, LOGO_Y + gy * CH
        ext = 3 if (gx + 1, gy) not in cells else 0                                # bold: thicker strokes
        c.rect(x0, y0, x0 + CW + ext, y0 + CH, 'o')
        if (gx, gy - 1) not in cells: c.rect(x0, y0, x0 + CW + ext, y0 + 2, 'w')          # bevel: lit top
        if (gx - 1, gy) not in cells: c.rect(x0, y0, x0 + 2, y0 + CH, 'w')          # and left
        if (gx, gy + 1) not in cells: c.rect(x0, y0 + CH - 1, x0 + CW + ext, y0 + CH, 'k') # shadowed bottom edge
    rnd = random.Random(3)
    for k in range(26):                                                              # craters in the rock
        gx, gy = rnd.choice(sorted(cells)); x = LOGO_X + gx * CW + 2; y = LOGO_Y + gy * CH + 3
        if c.p[y][x] == 'o':
            c.set(x, y, 'k'); c.set(x + 1, y, 'k'); c.set(x, y - 1, 'w'); c.set(x + 1, y - 1, 'w')

SHIP = """
...ww...
..wwww..
.wwwwww.
wwwwwwww
ww.ww.ww
"""

def draw():
    c = G.Canvas(H); rnd = random.Random(42); stars = []
    planet(c)
    for i in range(90):
        x, y = rnd.randrange(0, W - 1), rnd.randrange(0, 118)
        if LOGO_Y - 4 <= y < LOGO_Y + 46 and LOGO_X - 4 <= x < LOGO_X + 240: continue
        if i % 3: c.set(x, y, 'w'); c.set(x + 1, y, 'w'); stars.append((x, y, 2))
        else: c.set(x, y, 'vg'[x % 2]); stars.append((x, y, 1))
    meteor(c, 70, 22, 4, 60, seed=1)
    meteor(c, 238, 14, 3, 45, seed=2)
    meteor(c, 196, 98, 6, 95, seed=3)        # crashing past the logo
    meteor(c, 34, 112, 3, 35, seed=4)
    meteor(c, 150, 6, 2, 30, seed=5)
    meteor(c, 262, 104, 4, 55, seed=6)
    logo(c)
    meteor(c, 120, 40, 3, 50, seed=7)        # one in front of the logo, hitting the 'K'
    c.ascii(136, 100, SHIP)
    return c, stars

def main():
    c, stars = draw(); rows = G.encode(c); flat = [v for r in rows for v in r]; z = G.rle(flat)
    assert G.unrle(z) == flat
    tw = []
    for (x, y, n) in stars:
        if c.p[y][x] not in 'wvg': continue
        b = x // 7; m = sum(1 << ((x + i) % 7) for i in range(n) if (x + i) // 7 == b)
        if m: tw.append((y, b, m))
    tw = tw[:32]
    st = [l for l in STREAK.strip('\n').split('\n')]
    sb = []
    for l in st:
        for b in range(3): sb.append(sum(1 << i for i in range(7) if l[b * 7 + i] == '#'))
    o = ['; generated by tools/gen_title.py -- do not edit', 'TITLEH = %d' % H, 'NTWINK = %d' % len(tw),
         '; title art: %d bytes raw -> %d RLE' % (len(flat), len(z)), 'titleart:']
    for i in range(0, len(z), 16): o.append('        .byte ' + ','.join('$%02X' % v for v in z[i:i + 16]))
    o.append('twrow:  .byte ' + ','.join(str(t[0]) for t in tw))
    o.append('twcol:  .byte ' + ','.join(str(t[1]) for t in tw))
    o.append('twmsk:  .byte ' + ','.join('$%02X' % t[2] for t in tw))
    o.append('streak: .byte ' + ','.join('$%02X' % v for v in sb))
    open(D + '/src/title.inc', 'w').write('\n'.join(o) + '\n')
    os.makedirs(D + '/build', exist_ok=True); G.render_png(rows, D + '/build/title.png')
    print('title art: %d bytes raw -> %d RLE; %d twinkle stars' % (len(flat), len(z), len(tw)))

if __name__ == '__main__': main()
