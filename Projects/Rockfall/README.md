# ROCKFALL (Apple II hi-res, 6502 assembly)

Dodge the falling rocks. Self-booting disk, no DOS. Apple IIe or II+, 48K.

Controls: Left/Right arrows or J / L to move, Space or A to fire the laser.
On a IIe the ship stops when you let go of the key; on a II+ it glides a few frames.
Game over: any key plays again, Esc goes back to the title.
Laser heat: every shot heats the laser (HEAT bar, bottom right). Fire slowly and it stays cool; hold fire and it
overheats on the 5th shot: a warning buzz, the label turns to HOT, the bar blinks, and the laser is locked for ~1.2 s
until it has cooled all the way down.
Score: +1 per rock dodged, +5 per rock shot. Speed goes up every 15 rocks (max 5).
Levels: every LEVELSPD=3 speed-up steps (steps keep counting after SPEED caps at 5) is a new level: a
brief LEVEL N banner (~1.5 s, rising chime), then play continues. HUD shows LV. New stars change colour per
level (white, violet, green, repeating). Constants/variables at the top of rockfall.s; tests/level_test.py.
High scores: top 5 (initials, score, level) on the title screen and after game over; HUD HI = #1. A qualifying
score asks for initials: type A-Z, or cycle with arrows/joystick; RETURN, space or button 0 confirms each letter.
Table lives in its own page at $1B00 (5 x 8 bytes + "RF",1 at $1B28) so it can later go to a disk sector.

## Files
- src/rockfall.s    game source (ca65)
- src/font.s       tiny 3x5 hi-res font for the status line, made by tools/gen_font.py
- src/sprites.s     ship (7 pre-shifted copies) + rock data, made by tools/gen_sprites.js
- src/boot.s       stage-2 loader (track 0): reads the game from tracks 1-6 to $6000
- src/rockfall.cfg  linker config: loader at $0800 (track 0), game at $6000-$BFFF (max 24K)
- tests/loader_test.py pads the game image with a pattern to 20-24K, boots it and checks RAM byte for byte
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
- Boot (two stages, no DOS):
  1. Byte $0800 = $03 tells the Disk II boot ROM to load physical sectors 0-2 of track 0
     (src/boot.s) to $0800-$0AFF; it jumps to $0801 with X = slot*16.
  2. The loader shows LOADING... (one * per track), then reads tracks 1..N with its own
     6+2 GCR read code (DOS 3.3 style, cycle-safe read loops, 4+4 address field, data
     checksum), taking sectors in whatever order they pass under the head, and stepping
     the head with the four phase magnets (~19 ms per half-track, then settle). Then
     JMP $6000 with X = slot*16. Byte $0804 = N (number of game tracks) is filled in by
     the disk builders from the image size.
  - Disk layout: build/rockfall.bin = 4K track-0 image + game image; 256-byte chunk i goes to
    track i/16, PHYSICAL sector i%16 (mkdisk.py and build.ps1 then map physical to
    DOS-order slots in the .dsk). Both builders produce byte-identical disks.
  - The loader stays resident at $0800-$0CFF (text page 2, unused) with a jump table for
    the game: $0805 seek (A = track), $0808 rdsect, $080B wrsect (placeholder for saving
    high scores later: needs prenibblize + a 32-cycle write loop via $C08F/$C08D).
- Graphics: full-screen hi-res, double-buffered on HGR page 1 ($2000) and page 2 ($4000).
  Each frame is drawn on the hidden page, then $C054/$C055 flips it into view, so there is no flicker.
  For every page the game remembers what it last drew there (ship, rocks, bolt, stars at $1900-$1ABF);
  next time it XOR-erases exactly that and draws the new state. The field is rows 0-159; SCORE / SPD / HI / HEAT
  are drawn on both pages at rows 172-176 with a small hi-res font (mixed text mode is off during play,
  because text page 2 at $0800 holds the resident loader). The game-over screen switches to page 1
  with the 4 text lines (text page 1 at $0400 is free). Sprites use XOR, so drawing the same thing again erases it. Rocks sit on byte columns. The ship
  uses pre-shifted copies so it moves 2 px at a time.
- Stars: 36 small white dots (2 pixels each) fall behind the rocks. Half of them move 1 row
  every 2 frames and half every 4, which gives a parallax look. A star that reaches row 156
  comes back at the top in a new random spot. Stars are XORed like everything else, so a rock
  or the ship passing over one never leaves a mark. They don't count for collisions. Star
  tables sit in RAM at $1800-$18FF, below the HGR pages.
- Laser: one bolt at a time, 12 rows long, flying up 12 rows per frame from the ship's nose.
  A rock is hit if it overlaps the bolt's rows and the bolt's x is inside the rock. Hit = rock
  gone (it respawns at the top later), +5 points, and a crackle.
- Heat (Parsec-style): constants at the top of rockfall.s. HEATSHOT=18 per shot, HEATMAX=63,
  cools 1 per HEATCOOL=2 frames (~20/s at ~40 fps), every frame while overheated. Reaching 63 locks the
  laser until heat is back to HEATOK=0. Firing while locked only clicks. The bar (byte cols 31-38,
  56 px = HEAT*7/8, even widths) is written straight to both pages, only when it changes.
- Collision: a bounding box in 2-pixel units.
- Sound: the $C030 speaker with timed loops. There's an intro tune on the title and a noise
  burst plus falling sweep on a crash, a falling-pitch pew when you fire, a crackle on a hit, and a
  ~31 ms two-tone buzz (1 kHz / 600 Hz) on overheat. tools/render_sfx.py renders all three to a WAV preview.
- Memory: text page 1 $0400-$07FF (title/game over), loader $0800-$0AFF + buffers $0B00-$0C6F,
  tables $1800-$1ABF, HGR $2000-$5FFF, game code+data $6000-$6DDE (3.5K of 24K: up to $BFFF).
