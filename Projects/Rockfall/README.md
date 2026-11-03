# ROCKFALL (Apple II hi-res, 6502 assembly)

Dodge the falling rocks. Self-booting disk, no DOS. Apple IIe or II+, 48K.

Controls: Left/Right arrows or J / L to move, Space to stop.
Game over: any key plays again, Esc goes back to the title.
Score = rocks dodged. Speed goes up every 15 rocks (max 5).

## Files
- src/rockfall.s    game source (ca65)
- src/sprites.s     ship (7 pre-shifted copies) + rock data, made by tools/gen_sprites.js
- src/rockfall.cfg  linker config: the game sits at $0800-$17FF (track 0)
- build.ps1         Windows build (+ -Run to launch MAME)
- disk/rockfall.dsk bootable 140K disk image
- tools/            gen_sprites.js (node, only to change the art), mkdisk.py, a2enc.js
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
- Graphics: HGR page 1 in mixed mode. The field is rows 0-159, and the score is in the 4 text lines.
  Sprites use XOR, so drawing the same thing again erases it. Rocks sit on byte columns. The ship
  uses pre-shifted copies so it moves 2 px at a time.
- Stars: 36 small white dots (2 pixels each) fall behind the rocks. Half of them move 1 row
  every 2 frames and half every 4, which gives a parallax look. A star that reaches row 156
  comes back at the top in a new random spot. Stars are XORed like everything else, so a rock
  or the ship passing over one never leaves a mark. They don't count for collisions. Star
  tables sit in RAM at $1800-$18FF, outside the 4K disk image.
- Collision: a bounding box in 2-pixel units.
- Sound: the $C030 speaker with timed loops. There's an intro tune on the title and a noise
  burst plus falling sweep on a crash.
