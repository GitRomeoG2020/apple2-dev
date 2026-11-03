# ROCKFALL (Apple II hi-res, 6502 assembly)

Dodge the falling rocks. Self-booting disk, no DOS. Apple IIe or II+, 48K.

Controls: Left/Right arrows or J / L to move, Space or A to fire the laser.
On a IIe the ship stops when you let go of the key; on a II+ it glides a few frames.
Game over: any key plays again, Esc goes back to the title.
Score: +1 per rock dodged, +5 per rock shot. Speed goes up every 15 rocks (max 5).

## Files
- src/rockfall.s    game source (ca65)
- src/font.s       tiny 3x5 hi-res font for the status line, made by tools/gen_font.py
- src/sprites.s     ship (7 pre-shifted copies) + rock data, made by tools/gen_sprites.js
- src/rockfall.cfg  linker config: the game sits at $0800-$17FF (track 0)
- build.ps1         Windows build (+ -Run to launch MAME)
- disk/rockfall.dsk bootable 140K disk image
- tools/            gen_sprites.js (node, only to change the art), gen_font.py, mkdisk.py, a2enc.js
- tests/emu_test.py bobbin-ai test (boots disk, presses keys, checks memory; rebuilds the screen from game state
  and compares it byte-for-byte, so any leftover pixels show up)

## Build and run (PowerShell, from Projects\Rockfall)
    Unblock-File .\build.ps1
    .\build.ps1          # build only
    .\build.ps1 -Run     # build, then start MAME
Or by hand, from the MAME folder:
    .\mame.exe apple2e -flop1 ..\Projects\Rockfall\disk\rockfall.dsk -window
(`apple2p` for a II+.)

## How it works
- Boot: byte $0800 = $10 tells the Disk II boot ROM to load all 16 sectors of track 0
  into $0800-$17FF, then it jumps to $0801. The image builders put physical sector p in its
  DOS-order slot.
- Graphics: full-screen hi-res, double-buffered on HGR page 1 ($2000) and page 2 ($4000).
  Each frame is drawn on the hidden page, then $C054/$C055 flips it into view, so there is no flicker.
  For every page the game remembers what it last drew there (ship, rocks, bolt, stars at $1900-$1ABF);
  next time it XOR-erases exactly that and draws the new state. The field is rows 0-159; SCORE / SPEED / HI
  are drawn on both pages at rows 172-176 with a small hi-res font (mixed text mode is off during play,
  because text page 2 lives at $0800, where the game code is). The game-over screen switches to page 1
  with the 4 text lines (text page 1 at $0400 is free). Sprites use XOR, so drawing the same thing again erases it. Rocks sit on byte columns. The ship
  uses pre-shifted copies so it moves 2 px at a time.
- Stars: 36 small white dots (2 pixels each) fall behind the rocks. Half of them move 1 row
  every 2 frames and half every 4, which gives a parallax look. A star that reaches row 156
  comes back at the top in a new random spot. Stars are XORed like everything else, so a rock
  or the ship passing over one never leaves a mark. They don't count for collisions. Star
  tables sit in RAM at $1800-$18FF, outside the 4K disk image.
- Laser: one bolt at a time, 12 rows long, flying up 12 rows per frame from the ship's nose.
  A rock is hit if it overlaps the bolt's rows and the bolt's x is inside the rock. Hit = rock
  gone (it respawns at the top later), +5 points, and a ~4 ms zap.
- Collision: a bounding box in 2-pixel units.
- Sound: the $C030 speaker with timed loops. There's an intro tune on the title and a noise
  burst plus falling sweep on a crash, and a short zap when you fire.
- Memory: code+data $0800-$1471 (about 3.2K of the 4K track), tables $1800-$1ABF, HGR $2000-$5FFF.
