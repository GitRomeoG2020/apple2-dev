# a2sprite - Apple II sprite & shape editor

Double-click `a2sprite.html` (Edge/Chrome/Firefox, works offline, no install). Put it in
`C:\Users\rjguerrero\Projects\AppleII\Tools\`.

## Hi-res sprites tab
- Width is in bytes (7 pixels each), height in rows. Green grid lines = byte boundaries; an orange
  corner = that byte's palette (high) bit is set.
- **Color** mode paints 2-pixel color cells: violet/green set palette 0, blue/orange set palette 1,
  white = both pixels, black = clear. A warning shows if that changes the palette of a byte that already
  had pixels of the other color group (one palette bit per byte is an Apple II hardware limit).
  Colors assume the sprite is drawn at an **even** screen byte column (odd columns swap violet/green and blue/orange).
- **Raw bits**: left-click sets a pixel, right-click clears. **Palette bit**: click a byte to toggle bit 7.
- Previews: NTSC artifact color approximation (adjacent pixels = white) and monochrome.
- Export (ca65): `.byte` rows (bit0 = leftmost pixel), `NAME_W/NAME_H` constants, optional AND
  mask (`screen = (screen AND mask) OR sprite`), optional 7 pre-shifted copies (`name_s0..name_s6`,
  width+1 bytes each, with `name_shift_lo/hi` pointer tables). Download as `.s` or raw `.bin`
  (order: data, mask, then s0 [mask0], s1 ...).
- Import PNG: dark pixels = off, light gray = white, colored pixels map to the nearest artifact color.

## Applesoft shape tables tab
- Each shape is either **Pixels → vectors** (paint pixels, the path is generated) or **Manual path**
  (arrow keys/buttons, Space toggles pen; text form `U R D L` = plot then move, `mU mR mD mL` = move only).
- Shift+click sets the origin (red square), which is the `DRAW n AT x,y` point.
- The preview is decoded from the actual encoded bytes. Export as ca65 `.byte`, Applesoft loader
  (POKEs the table, sets pointer at 232/233, `HGR:HCOLOR=3:SCALE=1:ROT=0:DRAW 1 AT 140,96`), or `.bin`.
  To BLOAD the .bin instead: `BLOAD SHAPES,A$6000 : POKE 232,0 : POKE 233,96`.

## Projects
Save/Load project writes all sprites and shapes to a JSON file.

## Developer notes
Encoders live in `a2enc.js`; `template.html` + `build.sh` produce the single-file `a2sprite.html`.
`node tests/unit.js` runs encoder tests; `python3 tests/emu_test.py` verifies in the bobbin-ai emulator.
