# G-Bot: After Hours

![G-Bot arrives in the dark power room, captured from the Apple IIe emulator's actual HGR page](screenshots/power_arrive_enhanced.png)

**Third playable milestone: the repaired workshop door opens into the DARK POWER ROOM.**
The official title is **G-Bot: After Hours**; the stable project folder remains
`Projects/GBotAdventure`.

## What's playable

- An original, fixed workshop in true Apple II color HGR: a tool board, oscilloscope,
  parts bench, terminal, cables and a service mat in a slightly elevated view.
- A **42 × 44-pixel masked G-Bot**, including his arms and chunky boots. His large
  green CRT face, sloped cream/white enclosure, chest drive, belly keys, grabber,
  repair probe and bent aerial carry over from the original portrait.
- Four-direction walking with alternating weighted feet and a small body bob.
  Sideward glances, rear service vents, and a front-facing idle blink give him
  character. The chest activity light briefly dims with the idle blink.
- Solid room edges, bench and terminal; clean background restoration over floor
  seams, cables and furniture. No sprite trails or XOR drawing.
- A visibly faulted **left workbench terminal**, an orange service socket on the
  bench front, contextual diagnostics and a small inspect/reconnect interaction.
- Restoring the connection boots the terminal's green waveform, energizes the
  ceiling conduit/task light and changes the rear door indicator from orange to
  green. Power stays on for this session.
- **The rear door.** Before the repair, walking into it reports
  **DOOR SEALED - FIX WORKBENCH FIRST**. Afterwards, walking north into it slides
  the door open and G-Bot steps through into the second room.
- **The DARK POWER ROOM**: an original, almost-black HGR room made of sparse, dim,
  dotted outlines G-Bot can barely make out: pipe runs, a dead bulb, a locker, a
  big dead generator with its gauge needle on zero, and a feed cable to a
  **breaker panel**. The only light is a warm wedge spilling through the doorway
  behind him, the panel's orange standby lamp and two sleeping controller LEDs.
- Probing the breaker panel reports **NO POWER - FIND FUSE** (its fuse holder is
  visibly empty). That is a hint of the next goal, not a puzzle yet.
- Walking south through the lit doorway returns to the workshop, in front of the
  rear door, with the repair (lights, terminal, green indicator) kept.
- The original robot size, readable face, walking, blink and probe pose remain intact.

This is a **two-room prototype**, not the finished adventure. There are no
enemies, combat, lives, checkpoints, saves or story reveals in this build. Those
belong to later collaboration; the underlying mystery and twists are not finalized.

## Play the included disk

The self-booting [disk/gbot-after-hours.dsk](disk/gbot-after-hours.dsk) needs no build
step. Target: **Apple II+ or IIe, 48 KB, Disk II**, stock NMOS 6502 instructions.

Close MAME before pulling disk updates. With the usual two PowerShell tabs:

**Tab 1**, already at the main `AppleII` folder:
```powershell
git pull
```

**Tab 2**, already inside `MAME`:
```powershell
.\mame.exe apple2e -flop1 ..\Projects\GBotAdventure\disk\gbot-after-hours.dsk -window
```

For II+, use `apple2p` instead of `apple2e`. In AppleWin, insert this `.dsk` in
Drive 1 and boot an Apple II+/IIe with at least 48 KB. The disk is a raw boot disk,
not a DOS filesystem. The program never writes to it. Keep the disk in drive 1
while playing: each room change reads that room from the disk.

### Controls

| Key | Action |
| --- | --- |
| W / Up | Walk toward the back wall |
| A / Left | Walk left |
| S / Down | Walk toward the front |
| D / Right | Walk right |
| Space | Extend probe; inspect the left workbench / breaker panel when in range |
| R | Reconnect the loose lead after inspection |
| Escape | Cancel inspection (walking away also cancels) |

The Apple II keyboard reports **key events, not independent held-key states**.
A tap starts a short, bounded four-tick walk (up to eight pixels); the robot then
stops unless another direction event arrives. IIe autorepeat continues walking
after its initial delay. On an original II+, hold **REPT with W/A/S/D** to repeat,
or tap to walk. II+ keyboards don't have all four arrow keys. This prototype
supports one direction at a time, not simultaneous/diagonal movement, and does
not latch the last key into endless motion. Blocked walks stop at the obstacle.

### Your first repair

1. Walk **left**, then **up to the front of the left workbench**. The orange socket
   is on its right apron, below the small terminal. The footer changes to
   **WORKBENCH: SPACE TO INSPECT** when you are close enough.
2. Tap **Space**. G-Bot finds a loose lead; the footer offers **R RECONNECT / ESC CANCEL**.
3. Press **R** to reconnect it. Watch **RECONNECTING** and his probe for a short,
   bounded pause, then **WORKSHOP ONLINE** and the room's powered-up details.
4. Walk normally again. Probing the same terminal reports that it is already online.

From the untouched starting position, eleven taps of **A** and five taps of **W**
reach a valid service position. There is no required facing direction. Space away
from the socket reports **NO CONTACT** rather than silently pretending to repair.
Repeating/holding Space cannot confirm the repair; **R** is a deliberate second
step. This is an introductory diagnosis/action, not yet a circuit-routing puzzle.
Repair progress briefly holds G-Bot in place and ignores other keys; it always
finishes. Resetting/rebooting starts with the fault again. No disk data is saved.

![Fault diagnosed at the workbench](screenshots/workshop_fault_enhanced.png)

![Workshop restored after the first repair](screenshots/workshop_restored_enhanced.png)

### Into the dark power room

1. After the repair, walk to the **middle of the back wall** and keep walking
   **up** into the rear door (its indicator is green). From the starting spot,
   he is already lined up: just keep tapping or holding **W**. The door slides open, there is
   a short pause while the room loads from disk (about 1½-2½ seconds), and G-Bot
   arrives at the lit doorway at the bottom of the power room, facing in.
2. Walk **left and up** to the breaker panel on the back wall (top left). The
   footer changes to **BREAKER PANEL: SPACE TO PROBE**. Tap **Space**:
   **NO POWER - FIND FUSE**. Space elsewhere reports that it is too dark.
   The generator on the right is solid.
3. To go back, walk to the **middle of the bottom edge** (the lit doorway) and keep
   walking **down**. G-Bot returns to the workshop facing out of the rear door, with
   power still on. You can go back and forth as often as you like.

![Probing the dead breaker panel](screenshots/power_panel_enhanced.png)

![Back in the workshop, repair kept](screenshots/workshop_return_enhanced.png)

## Build

Uses the workshop's existing **ca65 / ld65** installation. No WSL, Java,
AppleCommander, Python or Pillow is required for the native Windows build:

```powershell
.\Projects\GBotAdventure\build.ps1
# Or build and launch:
.\Projects\GBotAdventure\build.ps1 -Run
```

Tools are resolved under `Tools\cc65\bin`, with MAME under `MAME\mame.exe`.
The build only uses this project's files. It does not rebuild or modify Rockfall.

On the development box / Linux:

```sh
python3 Projects/GBotAdventure/tools/build.py
# Optional explicit tool directory:
python3 Projects/GBotAdventure/tools/build.py --cc65 /path/to/cc65/bin
```

The Python build uses only the standard library and the checked-in native art.
Both build routes use the same linker layout and DOS-order sector mapping.

### Art regeneration (optional)

With Python 3 and Pillow installed:

```powershell
python Projects/GBotAdventure/tools/gen_workshop.py
python Projects/GBotAdventure/tools/gen_power_room.py
python Projects/GBotAdventure/tools/gen_concept.py
```

`gen_workshop.py` authors the separate, **robot-free background** and 14 masked
animation frames, plus `src/interaction.inc` (diagnostic pixels and visual patch
lookup tables, and every status-line message). `gen_power_room.py` authors the
dark power room (`art/power-room.hgr`). `gen_concept.py` regenerates the original portrait without
changing it. Neither imports Rockfall or uses external artwork/fonts. Build again
after regenerating workshop art. The checked-in `.hgr` and sprite `.bin` are
required native build inputs, not modern images loaded by the game.

## Graphics / memory notes

- Full-screen **280 × 192 HGR**, with the room above row 160 and native HGR title
  and controls below. No text-page switching or IIe-only video features.
- `$0800–$0A00`: read-only bootloader, **kept resident** as the room loader
  (`LOADROOM` entry at `$0805`); `$0C00–$0D6F`: disk decoding scratch.
  No high-score sector, write routine or Rockfall runtime is carried over.
- `$1000–$1133`: shifted sprite pixels; `$1200–$1333`: opacity;
  `$1400–$142B`: row palette phases; `$50–$8B`: engine zero-page state/scratch
  (`$8A` current room); `$26`, `$2B`, `$3C–$48`: loader zero page.
- `$2000–$3FFF` and `$4000–$5FFF`: alternating HGR display pages.
- `$6000–$7A7F`: engine, lookup tables and 13 status messages (including
  alignment padding). `$7A80–$7FFF` remains available: 1,408 bytes.
- `$8000–$9FFF`: the **current** room's canonical native background (8,192 bytes;
  repair/status changes update it in RAM).
- `$A000–$BF47`: 14 original 42 × 44 frames (8,008 bytes).
  `$BF48–$BFFF`: 184 spare bytes. Total current layout slack: **1,592 bytes**.
- Disk: track 0 boot; tracks 1–6 the fixed 24 KB boot load (the workshop room is
  tracks 3–4); tracks **7–8 the power room**. The complete disk is 143,360 bytes.
  No language card, auxiliary RAM or expansion sound hardware is needed.

**Why rooms load from disk.** Each HGR background is a full 8 KB and only one fits
beside the two display pages, engine and sprites. Rather than compress rooms (and
squeeze a decompressor plus a compressed workshop into the 1.4 KB left), a room
change re-uses the boot loader, which is already resident: it spins up the drive,
reads the next room's two tracks straight into `$8000`, and turns the motor off.
Leaving the power room reloads the pristine workshop from tracks 3–4; the repair
patches and status line are then re-applied from RAM state, so nothing is lost.
This scales to more rooms (two tracks each) and keeps the art uncompressed and
exact. The cost is a short pause at each door (measured below). The disk is
only ever read.

Before drawing, only the **offscreen page's previous 7-byte × 44-line rectangle**
is restored from the canonical room. The diagnostic strip and 52 changed visual
bytes are then synchronized to that offscreen page before the next robot is drawn. The next sprite is shifted in software and
mask-composited, then the completed page is selected. Every horizontal position
is even, preserving artifact color parity at all seven byte alignments. At an
opaque edge, the sprite selects that byte's palette phase; the underlying room
bytes are restored exactly when it moves away. The two display pages normally
show successive animation states, not identical frames.

Measured game ticks average approximately **69,060 cycles (~14.5 updates/second
at 1 MHz)** on both Bobbin models, including repair/status synchronization. The
worst sampled normal tick was **73,478 cycles**; the reconnect lasts about 1.7 seconds.
A room change (door beat, disk spin-up, seek, two-track read, both pages rebuilt)
took at most **2.35 million cycles (~2.3 s)** in Bobbin's Disk II emulation.

There is no IIe-only vertical-blank wait: the II+ uses the same bounded software
loop. Page selection is not beam-synchronized, so a CRT can show a slight transition
tear, but no partially erased sprite is deliberately displayed.

## Validation / screenshots

[IIe screenshot, native 280 × 192](screenshots/workshop_idle_enhanced-280.png) ·
[Walking pose](screenshots/workshop_walking_enhanced.png) ·
[Probe gesture](screenshots/workshop_probe_enhanced.png) ·
[II+ workshop](screenshots/workshop_idle_plus.png) ·
[Power room arrival, native 280 × 192](screenshots/power_arrive_enhanced-280.png) ·
[II+ power room](screenshots/power_arrive_plus.png)

Screenshots are decoded **from actual Bobbin HGR RAM after booting this disk**,
not the generator's concept preview. Enlargements use nearest-neighbor pixels.
The renderer uses a discrete artifact-color approximation (adjacent lit bits white;
isolated bits colored by parity and byte phase), not an analog NTSC/CRT simulation.
Real monitors and emulator filter settings will look a little different.

`tests/workshop_test.py` boots a disposable disk in Bobbin through a PTY and its
JSON control socket. It checks WASD and Apple arrow codes, four facings/foot poses,
all seven horizontal byte alignments, all four walls, both furniture fronts and
sides, the probe, idle blink and no stuck movement. Every sampled frame compares
**both entire 8 KB display pages** against an independent software compositor,
including old-background restoration and HGR holes. It independently reconstructs
faulted/online room bytes and each diagnostic, verifies the canonical buffer, and
checks far probes, reaching the service position through real movement, inspection,
Space repeat, cancel/walk-away, explicit R confirmation, bounded progress, online
visuals on both pages, idempotent re-probing and movement afterward. It also checks
unchanged source sprites, resident loader preservation and an unchanged disk.

The room tests check that the door is sealed before the repair; that walking
into it afterwards streams in the power room byte-for-byte from tracks 7–8; all
four power-room walls (including the closed bottom edge beside the doorway), the
generator front and side; the far probe, walking to the breaker panel with real
controls, its prompt and **NO POWER - FIND FUSE**; that standing in the doorway
doesn't leave; and that walking out restores the workshop with the repair kept.
A second round trip follows. Both pages are rebuilt and compared after every
transition, so leftover robots or trails from the previous room would fail.
The IIe run checked **931 frames**, the II+ run **925**, with both full pages
compared each time. Frame-cost checks
combine Bobbin's completed video-frame count and partial-frame cycle count.

```sh
# Build first, then (each run is bounded by the caller):
timeout 600 python3 Projects/GBotAdventure/tests/workshop_test.py enhanced
timeout 600 python3 Projects/GBotAdventure/tests/workshop_test.py plus
```

These tests run on Bobbin's IIe and II+ models. Native Windows PowerShell,
MAME, AppleWin and physical hardware have not been run in this Linux environment;
their launch/build instructions follow the workshop's existing native layout.

## Original portrait and future direction

![The original G-Bot character concept, preserved unchanged](art/gbot-workshop.png)

[Native full-screen portrait](art/gbot-workshop.hgr) ·
[280 × 192 portrait](art/gbot-workshop-280.png)

G-Bot is a curious repair robot, not a combat tank. The wider idea remains a
room-to-room repair adventure: the workshop and dark power room now exist; finding
the missing fuse and a security room are potential next steps, with repairs that affect other rooms and gradually
reveal the facility's story. Room checkpoints rather than limited lives are the
current direction. Two disks remain an option **if the world earns them**, not a
requirement to fill space.
