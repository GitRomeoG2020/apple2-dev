# G-Bot: After Hours

![The console is back in phase and the scientist can finally hold still long enough to talk to G-Bot, captured from the Apple IIe emulator's actual HGR page](screenshots/lab_talk_enhanced.png)

**Sixth playable milestone: the first story beat.** Fix the workshop, find the
fuse, light the power room, slip past the security room's guard bot, unlock the
lab, and tune the time chamber's drifting console back into phase, so the
flickering scientist can finally hold still long enough to talk to G-Bot.
Four connected rooms.
The official title is **G-Bot: After Hours**; the stable project folder remains
`Projects/GBotAdventure`.

## What's playable

- **Every room is stamp-built, and the game runs from the language card.**
  No room is an 8 KB picture on disk any more. At each door the engine draws
  the next room into `$8000` from a **room script and a stamp library**: text in
  the resident status font, Pillow-exact lines (floor perspective, hazard
  stripes), repeating byte rows, blocks and stamps. Each one rebuilds the old
  art **byte for byte**, so gameplay is unchanged. Code and tables now live in
  the 16 KB language card, and bank 1 holds a shared **stamp pool**. As a
  result a door reads **one 4 KB track** (or less), every door takes
  **0.72–0.98 s** (it was 0.98–1.32 s), fitting the fuse lights the power room
  with no disk read at all, the disk uses tracks 0–10 (24 free), and about
  **13 KB of RAM** is free (it was 421 bytes). The game needs 64 KB now: a IIe,
  or a II+ with a language card.

- **Doors answer at once.** The moment G-Bot steps into a doorway, the status
  line reads **ENTERING POWER ROOM...** (or **ENTERING WORKSHOP... / SECURITY... /
  THE LAB...**) on both display pages, and a short rising chirp plays, all
  within about 20 ms and before the disk is touched. Keys pressed while the next room loads
  are thrown away, and so is anything typed in the first four frames after
  arrival. Mashing a key during the load can no longer walk him back out of
  the door. A room change now takes **1.15–1.32 s**; it used to take 1.75–2.78 s.

- **A slim HUD.** The big in-game title band is gone. A one-row strip under each
  room names it and shows its clock: **WORKSHOP 12:15**, **POWER ROOM 9:41**
  (stopped when the power went), **SECURITY 2:53**, **THE LAB 6:02**. No two
  rooms agree. The rooms got the space back: every floor is 7 rows deeper, and
  G-Bot can walk that much further toward the front.
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
  visibly empty). One small white glint in the old locker gives the fuse away.
- **The fuse.** Probing the locker finds it: **FOUND A FUSE!** A little fuse icon
  appears at the right end of the status line while G-Bot carries it.
- **Fitting it** works like the workbench: Space at the panel offers
  **R TO FIT / ESC CANCEL**; R fits it during a short, bounded pause. The lights
  come on: a **lit power room** with solid outlines, the bulb glowing, breakers set
  and green, the fuse seated, the generator's gauge needle up and the west
  security door unlocked. It stays lit for the rest of the session.
- **The SECURITY ROOM**, through that west door (sealed until the power is back):
  a monitor wall of camera feeds, the security desk with phone and mug, ceiling
  cameras, evidence lockers, a wall clock that doesn't agree with the workshop's,
  and a striped patrol lane across the floor.
- **One guard bot.** It is still rebooting when G-Bot first walks in, then rolls
  steadily back and forth along the lane. Touching it sends G-Bot back to the
  room's entry door (**GUARD: WORK ORDER NOT RECOGNIZED**). There are no lives, damage or
  game over. You can cross the lane safely by timing it.
- **The lab door.** A new door in the security room's back wall, marked **LAB**,
  with an orange lock lamp. Walking into it says
  **LAB DOOR LOCKED - TRY THE DESK**. Probing the security desk releases it:
  the lamp turns green and the desk's line runs on with
  **...AND THE LAB DOOR CLICKS OPEN**.
- **THE LAB**: a time-chamber ring humming on its dais, a bank of consoles, a lab
  clock showing yet another time (about 6:02), a dropped clipboard page and cup,
  and a robot **parking bay** with "G-BOT" over a dotted outline exactly his
  shape, a charging arm and a CHARGE lamp.
- **The flickering scientist.** A masked, double-buffered sprite in a lab coat with a
  clipboard. She is never quite in sync: she flickers in (alternate scanlines only),
  stays about three seconds, flickers out, and turns up somewhere else a few
  seconds later. She is harmless and never moves G-Bot.
- **The console puzzle.** Probing the lab consoles finds the fault:
  **CONSOLE: LOOP 4,817. PHASE DRIFT!** Press **R** to tune. A meter on the
  status line shows the phase (1/3, 2/3, 3/3), a target **|** and G-Bot's cursor
  **O**. Line them up with **A/D** (or the arrows). The cursor becomes a **\***
  when it's on target. Then lock it with **R**. A wrong lock just says **OUT OF PHASE - KEEP TUNING**. **Esc** cancels at any point.
- **The conversation.** With all three phases locked, the scientist stabilizes
  next to the consoles, solid and still, and finally talks to him. Mid-warning,
  she slips out of phase again. The console stays in phase for the rest of the
  session, and probing it again gives a short reminder of what she said.
- **Probe everything.** The chamber, the bay, the consoles and the scientist each
  give a short clue, and some lines run on into a second one. The bay recognizes
  G-Bot. See the walkthrough below.
- Every door works both ways, and the repair, fuse, power and lab-door states are
  kept as G-Bot moves between all four rooms.
- The original robot size, readable face, walking, blink and probe pose remain intact.

This is a **four-room prototype**, not the finished adventure. There is no
combat, lives, saves or story choice in this build yet. The scientist has said
her piece: what G-Bot does about full power is the next chapter.

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
| Space | Extend probe; inspect the workbench, locker, breaker panel, security desk, or anything in the lab |
| R | Reconnect the loose lead / fit the fuse / start tuning and lock a phase at the lab console |
| A / D (while tuning) | Move the phase cursor left / right (G-Bot stays put) |
| Escape | Cancel inspection or tuning (walking away from an inspection also cancels) |
| M | Sound effects on / off (shows **SOUND ON** / **SOUND OFF** briefly; S is taken by walking) |

### Sound

Short speaker effects (sound starts **on**; **M** toggles it, and off silences
everything, the door chirp included). Most play inside the main loop's existing
~3,000-cycle end-of-frame throttle: one ~3 ms tone burst per frame in place of
the old idle wait, so the frame rate does not change. The few longer jingles
play only where the game already pauses.

| Effect | Trigger | Length |
| --- | --- | --- |
| Scanning warble | Space (probe) | 5 frames (~3 ms each) |
| Low buzz | a failed or not-applicable action: NO CONTACT, MOVE CLOSER, NO POWER, TOO DARK, sealed doors, empty locker, NOTHING TO PROBE, lab door locked, guard catch, OUT OF PHASE, tuning cancelled | 4 frames |
| Chime | FOUND A FUSE! | 4 frames |
| Click | each A/D tuning step; sound back on | 1 frame |
| Robotic beep | the guard rebooting (first entry to security) | 7 frames |
| Chord | LOCKED! NEXT PHASE... | 5 frames |
| Electric crackle | the scientist flickering in (at most every ~12 s) | 4 frames |
| Footstep tick | every 8th frame while walking (2 clicks) | a few cycles |
| "Fixed it!" tune | the workbench repair completing (G-Bot is still holding) | ~0.7 s, blocking |
| Power-on hum | the fuse fitted (inside the room's reload) | ~54 ms, blocking |
| Hum + fanfare | the console coming into phase as she starts to talk | ~1.1 s, blocking |
| Unlock stinger | ...AND THE LAB DOOR CLICKS OPEN (the whole room, guard included, holds for it) | ~0.4 s, blocking |
| Cut-off reveal | IT RUNS AGAIN- : a slow climb cut off mid-note by a crackle | ~0.75 s, blocking |
| Door chirp | every door with no room tune | ~22 ms, during the door |
| Room motif | entering a room: see below | ~0.45 s, during the door |

**Room tunes.** Entering a room may play one of four short motifs: the
workshop's tinkering hop up the C chord, the power room's warming-up climb,
security's tiptoe past the guard, and the lab's whole-tone wonder. The
first-ever entry to a room always plays one (the workshop's plays at boot);
after that it's a coin flip, and a played motif is the room's own half the
time, otherwise any of the four. The coin is an 8-bit LFSR mixed with the frame
counter, so the player's pace decides. The motif plays during the door, after
the ENTERING line and before the disk read, in place of the chirp and the
drive's spin-up wait, which it outlasts. That makes a door with a motif about
0.4 s longer (up to 0.46 s from the workshop, whose door animation already
covers the spin-up); a door without one costs what it did before. Walking is
untouched. M off: no motifs.

The effects engine is `src/sfx.s`; which message plays which sound is
generated (`MSG_SFX` in `tools/gen_workshop.py`).

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

### The fuse and the lights

1. In the dark power room, walk to the **middle of the back wall**, to the old
   locker with the tiny glint (from the doorway, just keep walking **up**). The
   footer reads **OLD LOCKER: SPACE TO PROBE**. Tap **Space**: **FOUND A FUSE!**
   The fuse icon appears at the end of the status line.
2. Walk **left** along the back wall to the breaker panel. Tap **Space**:
   **FUSE FITS: R TO FIT / ESC CANCEL**. Press **R**. After **FITTING FUSE...**
   the room reloads lit: **POWER RESTORED - WEST DOOR OPEN**.

![The fuse found: status-line icon](screenshots/power_fuse_enhanced.png)

![The power room with the lights back on](screenshots/power_lit_enhanced.png)

### The security room and its guard

1. Walk to the **left wall, lower half** (the door marked **SEC**, lamp green
   now) and keep walking **left**. Before the fuse is fitted it says
   **SECURITY DOOR SEALED - NO POWER**.
2. G-Bot arrives at the security room's **east door** (bottom right): the room's
   checkpoint. The guard is booting for about three seconds, then patrols the
   striped lane, one step at a time, end to end (a round trip takes ~12 s).
3. G-Bot is only caught when he is **on the lane** (roughly the middle band of
   the floor) and overlaps the guard. The back wall strip and the front strip are
   safe. Wait until the guard rolls away, then cross. If it touches him he's sent
   back to the east door; nothing else is lost.
4. Visit the **security desk** (back left; the desk itself is solid). Its footer
   reads **SECURITY DESK: SPACE TO PROBE**. Space shows what the monitors see.
5. Leave by walking **right** into the east door from the front strip. You arrive
   at the power room's west door. Every door can be used again in either direction.

![Caught: back to the checkpoint](screenshots/security_caught_enhanced.png)

![At the security desk](screenshots/security_desk_enhanced.png)

### The lab

1. The **LAB** door is in the middle of the security room's back wall, with a
   small lamp to its right. Before you probe the desk, walking into it says
   **LAB DOOR LOCKED - TRY THE DESK**.
2. Probe the **security desk**. After the monitors line, the footer adds
   **...AND THE LAB DOOR CLICKS OPEN** and the lamp turns green.
3. From the desk, walk **right** along the back strip, which is safe from the guard,
   to the door's middle. Then keep walking **up**. The lab loads from disk, and
   G-Bot arrives at its bottom doorway: **THE LAB: SOMETHING IS STILL RUNNING**.
4. Look around and probe:
   - **Consoles** (back left): **CONSOLE: LOOP 4,817. PHASE DRIFT!** See the next
     section.
   - **Time chamber** (walk up to the front of the dais; the dais is solid):
     **CHAMBER: LOOP ACTIVE. DO NOT DISTURB** then **...THE RING HUMS. IT KNOWS YOU.**
   - **Parking bay** (back right): just standing there gives
     **PARKING BAY: WELCOME BACK, G-BOT**. Probe it for
     **BAY: G-BOT. LAST SERVICE: TONIGHT.** then **...AND TONIGHT. AND TONIGHT.**
   - **The scientist**: walk close while she is visible:
     **SCIENTIST! SPACE TO SAY HELLO**. Probe for
     **SCIENTIST: ...BEFORE THE MORNING SHI-**. When she flickers away, it adds
     **...AND SHE FLICKERED OUT MID-WORD**.
5. To leave, walk to the **middle of the bottom edge** and keep walking **down**.
   You arrive back at the security room's lab door, on the guard-free back strip.

### The console puzzle and the scientist

1. Stand at the **consoles** (back left; from the doorway, walk left, then up).
   Tap **Space**: **CONSOLE: LOOP 4,817. PHASE DRIFT!**, then the footer offers
   **PHASE DRIFT: R TO TUNE / ESC CANCEL**.
2. Press **R**. The status line becomes the tuning meter, for example
   `PHASE 1/3 ...|.O.......  R LOCK`. The **|** is the target; **O** is your
   cursor. A/D (or Left/Right) move the cursor; G-Bot stays put. When it sits on
   the target it turns into a **\***. Press **R** to lock: **LOCKED! NEXT PHASE...**
   Locking off target says **OUT OF PHASE - KEEP TUNING** and lets you try again.
   **Esc** cancels: **TUNING CANCELLED. DRIFT CONTINUES.** (probe to start over).
3. Lock all three phases. The scientist steadies beside the consoles and talks.
   Each line stays about four seconds; G-Bot listens, so keys are ignored:
   - **SCIENTIST: YOU CAN SEE ME? G-BOT!**
   - **THE EXPERIMENT WORKED. TOO WELL.**
   - **WE ARE STUCK IN ONE NIGHT.**
   - **OVER AND OVER. THE COFFEE NEVER ENDS.**
   - **YOU WERE PARKED IN THE CHAMBER...**
   - **...SO TIME SLID RIGHT OFF YOU!**
   - **DON'T RESTORE FULL POWER -**
   - **IT RUNS AGAIN-**. Mid-word, she flickers out.
   - **...FLICKERED OUT. CONSOLE STAYS ON.**
4. The console stays in phase from then on, even after leaving the lab. Probing
   it again gives **CONSOLE: IN PHASE. NO FULL POWER!** then
   **LAB CLOCK SAYS 6:02. NOBODY AGREES.** Afterwards the scientist goes back
   to flickering around the lab.

![The tuning meter: phase 1 of 3](screenshots/lab_tuning_enhanced.png)

![Cursor on target](screenshots/lab_phase_aligned_enhanced.png)

![Her warning](screenshots/lab_warning_enhanced.png)

![The scientist, solid for a moment](screenshots/lab_scientist_enhanced.png)

![Flickering out of sync (ghost frame)](screenshots/lab_flicker_enhanced.png)

![The parking bay recognizes G-Bot](screenshots/lab_bay_enhanced.png)

![Probing the time chamber](screenshots/lab_chamber_enhanced.png)

![The lab door unlocked from the desk](screenshots/security_labdoor_open_enhanced.png)

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
python Projects/GBotAdventure/tools/gen_security.py
python Projects/GBotAdventure/tools/gen_lab.py
python Projects/GBotAdventure/tools/gen_concept.py
```

`gen_workshop.py` authors the separate, **robot-free background** and 14 masked
animation frames, plus `src/interaction.inc` (diagnostic pixels and visual patch
lookup tables, and every status-line message). `gen_power_room.py` authors the
dark and lit power rooms (`art/power-room.hgr`, `art/power-room-lit.hgr`).
`gen_security.py` authors the security room and the guard's six masked frames
(`art/security-room.hgr`, `art/guard-sprites.bin`), plus `src/security.inc`
(the lab-door lamp bytes). The room generators are still the source art for
every room: `gen_stamps.py` compiles each room (the workshop as it boots, the
dark and lit power room, security, the lab) into a stamp library and a room
script, checking the result byte for byte, and `gen_banks.py` packs them onto
the rooms' aux tracks and into the stamp pool (`art/stamp-pool.bin`), and writes
`src/auxend.inc` (each variant's script address and aux sectors).
`gen_lab.py` authors the lab and the scientist's four
frames (`art/lab-room.hgr`, `art/scientist-sprites.bin`: solid and ghost, each
for even and odd columns). `gen_concept.py` regenerates the original portrait without
changing it. Neither imports Rockfall or uses external artwork/fonts. Build again
after regenerating workshop art. The checked-in `.hgr` and sprite `.bin` are
required native build inputs, not modern images loaded by the game.

## Graphics / memory notes

- Full-screen **280 × 192 HGR**. The room fills rows 0–164. Below it there is
  no title band any more, just three slim native HGR text rows:
  - a **room strip** at rows 169–173: the room's name on the left and its clock
    time on the right;
  - the engine's **status line** at rows 177–181;
  - the **controls** at rows 186–190.

  The strip and the controls are baked into each room's background on disk, so
  they cost no RAM. No text-page switching or IIe-only video features.
- `$0800–$0A8F`: read-only bootloader, **kept resident** as the room loader
  (`LOADROOM` at `$0805` reads two tracks, `LOADONE` at `$0808` sectors
  `SFIRST..SEND-1` of one, `MOTOROFF` at `$080B`), with a cycle-exact RAM copy
  of the monitor's `WAIT` and the interrupt-vector stubs; `$0B96–$0BFF` the
  nibble table; `$0C00–$0CFA` the one-time boot code (the boot ROM loads
  sectors 0–4), afterwards the interpreter's text buffer (`$0C00–$0C27`);
  `$0D60–$0D6F` sector flags, `$0E00–$0EFF` decode tables built at boot. Raw
  sector data goes to the **hidden** HGR page during a read (to HGR page 1
  while booting). No high-score sector, write routine or Rockfall runtime.
- `$1000–$1133`: shifted sprite pixels; `$1200–$1333`: opacity;
  `$1400–$142B`: row palette phases (all three rebuilt every frame).
  `$1140–$1167`: the status line being drawn (40 glyph numbers).
- **Per-room aux track** at `$1000–$1FFF`. Every room has one 4 KB track, and a
  door reads only that track (workshop 7, read at boot; power room 8;
  security 9; lab 10):
  - `$1000`: the room's **stamp count, stamp address table and room script**,
    in the per-frame scratch area: the room is drawn right after the read,
    before that area is reused;
  - `$1440` holds that room's **message bank**: id, length, glyphs. Entries
    can continue after the actor frames; `$FF` ends the bank;
  - `$1800` holds the room's actor frames: the guard's 6 (1,620 bytes) or the
    scientist's 4 (1,440 bytes);
  - the stamps fill every gap left (largest first), and any that do not fit go
    into the stamp pool.

  The engine finds a message by scanning the bank and centers it into the line
  buffer. The banks: workshop 341 bytes (10 messages), power room 487 (16),
  security 331 (11), lab 965 (30, including the dialogue and the tuning meter
  template). The four **ENTERING ...** lines sit in the bank of each room that
  has a door to that room, so the bank being left always has the line it
  needs. A door reads the aux sectors that hold data: all of them for a stamp
  room (workshop 0–9, power room 0–11, security 0–15, lab 0–14), only the bank
  (4–6) for the lit power room.
- **Stamp rooms** (script bytes / stamps / stamp bytes / total):

  | Room | Script | Stamps | Stamp bytes | Total | Where |
  | --- | --- | --- | --- | --- | --- |
  | workshop | 649 | 35 | 1,429 | 2,149 | aux 7 |
  | power room, dark | 866 | 91 | 1,378 | 2,427 | aux 8 |
  | power room, lit | 798 | 49 | 1,245 | 2,142 | pool |
  | security | 734 | 31 | 1,253 | 2,050 | aux 9 |
  | lab | 573 | 31 | 2,088 | 2,724 | aux 10 + pool |

  All five pictures take 11,492 bytes, against 40,960 as full art. The
  interpreter (`stamps`) draws a room in about 0.3 s; it maps language-card
  bank 1 while it draws, so it and everything it reads (fonts, row tables) sit
  at `$E000` or above. The workshop's online look and the security lab-door
  lamp are still patched on in RAM, as before.
- `$50–$A8`: engine zero-page state/scratch (`$8A` room, `$8C` panel,
  `$8D` fuse, `$8F–$97` guard, `$9D` lab door, `$9E` which actor is loaded,
  `$9F–$A5` the current actor, `$A6–$A8` scientist, `$A9` console state,
  `$AA–$AB` tuning phase/cursor, `$AC` talking, `$AD` door input lockout,
  `$AE` door scratch); `$26`, `$2B`, `$3C–$4E`: loader zero page.
- `$2000–$3FFF` and `$4000–$5FFF`: alternating HGR display pages.
- **Language card (16 KB at `$D000–$FFFF`).** The boot reads the 12 KB of
  engine code and tables (tracks 1–3) to `$6000`, switches the card to *read
  and write RAM, bank 2* (two reads of `$C083`) and copies them up to
  `$D000–$FFFF`, where the game runs from then on. It then reads the stamp pool
  (track 4) to `$6000` and copies it into **bank 1** (`$C08B`). The card stays
  mapped (bank 2) for the whole game, so the ROM is switched out for good and
  **nothing calls it**: the monitor's `WAIT` has a cycle-exact RAM copy in the
  loader (`wait`), and the NMI/RESET/IRQ vectors at `$FFFA–$FFFF` point into
  the loader, which maps the ROM back in (`$C082`) and continues through the
  ROM's own vector (the game runs with interrupts off). Only the stamp
  interpreter switches to bank 1, and back, while it draws a room.
  - bank 2 `$D000–$DEBF`: engine code (free to `$DFFF`: **320 bytes**);
  - `$E000–$EC7F`: lookup tables and the 47-glyph status font;
  - `$EC80–$EFF3`: the stamp interpreter;
  - `$EFF4–$F29A`: sound effects, tunes and their tables (679 bytes);
  - `$F29B–$FFF9`: **free, 3,423 bytes**;
  - bank 1 `$D000–$DFFF`: the stamp pool (lit power room, the lab's overflow;
    **428 bytes** free).

  Both the IIe and a II+ need 64 KB (a II+ with a 16K language card in slot
  0); Bobbin emulates the card on both.
- `$8000–$9FFF`: the **current** room's canonical native background (8,192 bytes;
  repair/status changes update it in RAM).
- `$A000–$BF47`: 14 original 42 × 44 frames (8,008 bytes).
  `$BF48–$BFFF`: 184 spare bytes.
- **`$6000–$7FFF` (8,192 bytes) is free main RAM.** Free RAM in all: **12,547
  bytes** (8,192 at `$6000`, 320 + 3,423 in the language card, 428 in
  the pool, 184 at `$BF48`). Before the language card the code area had 421
  bytes free.
- Disk: track 0 boot; **1–3 code and tables, 4 stamp pool, 5–6 G-Bot's frames,
  7 workshop aux, 8 power aux, 9 security aux, 10 lab aux** (`src/layout.inc`).
  The complete disk is 143,360 bytes; **tracks 11–34 are free** (24 tracks).
  It needs a 64 KB machine (language card); no auxiliary RAM or expansion
  sound hardware.

**Door timing.** Measured per door in Bobbin (`tests/door_timing.py`; the IIe
and II+ give the same numbers):

| Door | First version | Full art (fast loader) | Stamp rooms | With a room tune |
| --- | --- | --- | --- | --- |
| workshop → power room (dark) | 2.78 s | 1.17 s | **0.80 s** | ~1.26 s (first entry: always) |
| power room (dark) → workshop | 2.20 s | 1.27 s | **0.86 s** | ~1.24 s |
| workshop → power room (lit) | 2.78 s | 1.31–1.32 s | **0.78 s** | 1.24 s |
| power room → security | 1.77 s | 0.98 s | **0.98 s** | 1.36 s |
| security → lab | 1.75 s | 1.26 s | **0.91 s** | 1.29 s |
| lab → security | 1.95 s | 1.00 s | **0.98 s** | 1.37 s |
| security → power room (lit) | 1.93 s | 1.19 s | **0.72 s** | 1.09 s |
| power room (lit) → workshop | 2.20 s | 1.26 s | **0.85 s** | 1.23 s |
| fitting the fuse (dark → lit) | | reads 2 tracks | **no disk read** |  |

A room tune plays during the door in place of the chirp and the spin-up wait;
`tests/tune_test.py` measures doors with and without one (a tune may add at
most 0.5 s; doors without one must match the table).

Where the time went:
- the half-second pause in the workshop doorway is gone; the door slides open
  on one page only;
- the drive motor starts as the door triggers, so it spins up while the
  status line and chirp go out, and it runs once per door instead of once per read;
- seeks accelerate like DOS 3.3: 19, 11, 7.5, 6, then about 5.4 ms per
  half-track;
- each track is read in about **one revolution instead of two**. Sectors are
  stored raw as they pass and decoded together afterwards with lookup tables.
  Decoding each one before the next used to miss the sector right behind it;
- a door reads one aux track (bank, actor frames, room script and stamps)
  instead of two 8K room tracks plus the aux sectors; drawing the room from
  stamps costs about 0.3 s of that time;
- the room is copied to a page with an unrolled loop (about 9 cycles a byte,
  down from 16).

**Why rooms are drawn from stamps.** Each HGR background is a full 8 KB and
only one fits beside the two display pages and the sprites. The first versions
streamed each room's two tracks into `$8000` at the door. With the engine in
the language card, there is room for an interpreter, so each room is now a
script of a few hundred bytes plus its stamps, read with the aux track the door
needs anyway (or kept in the bank-1 pool). The room generators remain the
source art, and the build and tests check every room byte for byte against
it. Leaving the power room redraws the pristine workshop; the repair patches
and status line are then re-applied from RAM state, so nothing is lost.
Fitting the fuse redraws the power room lit from the pool, and every later
visit picks lit or dark from the panel state. The disk is only ever read.

## Validation / screenshots

[IIe screenshot, native 280 × 192](screenshots/workshop_idle_enhanced-280.png) ·
[Walking pose](screenshots/workshop_walking_enhanced.png) ·
[Probe gesture](screenshots/workshop_probe_enhanced.png) ·
[II+ workshop](screenshots/workshop_idle_plus.png) ·
[Power room arrival, native 280 × 192](screenshots/power_arrive_enhanced-280.png) ·
[II+ power room](screenshots/power_arrive_plus.png) ·
[Locker prompt](screenshots/power_locker_enhanced.png) ·
[Security room arrival, guard rebooting](screenshots/security_arrive_enhanced.png) ·
[II+ security room](screenshots/security_patrol_plus.png) ·
[Lab arrival, native 280 × 192](screenshots/lab_arrive_enhanced-280.png) ·
[II+ lab with the scientist](screenshots/lab_scientist_plus.png) ·
[Lab consoles](screenshots/lab_consoles_enhanced.png) ·
[Lab door locked](screenshots/security_labdoor_locked_enhanced.png)

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
into it afterwards draws the power room byte-for-byte from its stamps; all
four power-room walls (including the closed bottom edge beside the doorway), the
generator front and side; the far probe, walking to the breaker panel with real
controls, its prompt and **NO POWER - FIND FUSE**; that standing in the doorway
doesn't leave; and that walking out restores the workshop with the repair kept.
A second round trip follows. Both pages are rebuilt and compared after every
transition, so leftover robots or trails from the previous room would fail.

This milestone's tests cover the sealed security door; the panel without a fuse
(and R doing nothing); walking to the locker, the fuse pickup, the HUD icon and the
empty locker afterwards; Escape, Space repeat and R at the panel; the fit and the
lit room redrawn from the pool with no disk read; the lit room still lit after a trip to the
workshop; the security door opening at its checkpoint; the guard rebooting,
waking, and patrolling one byte at a time to both ends while the checkpoint stays
safe; a touch sending G-Bot back; a timed crossing with real controls to the desk;
the desk probe and solidity; and round trips through all three rooms.

The lab milestone adds: the lab door sealed before the desk (message and orange
lamp bytes); the desk unlocking it (green lamp, run-on line); walking into the lab
drawn from its stamps with the scientist's frames streamed to `$1800` from its aux track (10);
250 frames of the flicker cycle (gone, flickering in, solid, flickering out) with
both solid and ghost frames seen at more than one spot and G-Bot never moved; the
consoles, chamber, bay and scientist prompts and probes, every run-on line, and
the empty-floor probe; the dais blocking from the front and side; leaving the lab
with the guard's frames re-streamed and the guard and door state kept; and a full
round trip lab → security → power → workshop → power → security → lab with every
state kept (24 transitions in the whole run). The independent compositor draws
the guard and the scientist (including ghost frames) with the same depth ordering,
so every frame checks both sprites on both pages, and every flicker frame proves
there are no trails. The console milestone adds:
- the workshop bank read at boot;
- after every room change, a check that the room's whole aux track (message
  bank and actor frames) is in RAM, with all four banks seen;
- every message compared through the existing exact status-line oracle;
- the console probe, prompt, Esc cancel, walking away, and R starting the
  tuning meter;
- A/D moving the cursor (not G-Bot), the cursor stopping at the right end, the
  lock-on star, a wrong lock, all three locks;
- the whole conversation in order, with the scientist solid and still and G-Bot
  ignoring keys until she slips out of phase;
- the console staying in phase, the reminder, and the state surviving a full
  round trip through every room.

The door change adds checks on every room change in the run, all six door
directions:
- the test stops at the loader's entry (`$0805`/`$0808`), before any disk
  read, and checks that both pages' status rows match **ENTERING <ROOM>...**
  pixel for pixel. It saves a screenshot the first time each door is used;
- it types **S** while the room is loading. Unflushed, that key would turn
  G-Bot round at the arrival doorway and walk him straight back out. It
  types **A** in the first frame after arrival;
- it checks that the input lockout is armed and that G-Bot has not moved
  after it ends;
- it checks the aux sectors each door reads, and that no door takes more than
  1.7 million cycles.

The stamp rooms add, for each of the five pictures (the workshop at boot, the
dark power room, the lit one after the fuse, security, the lab): the script
and stamps read back from the disk images rebuild the old art byte for byte,
and the engine's own `$8000` equals the old art (status line aside). Each
saves an old | new | red-difference sheet,
`screenshots/<room>_stamps_vs_art_<machine>.png`. The whole run also keeps
comparing both pages and `$8000` against the old art in every frame.

The IIe run checked **3,072 frames** (175 checks), the II+ run **3,066** (174),
with both full pages compared each time. The HUD-strip change moved every
room's front edge from G-Bot row 114 to 120, and the walk paths in the tests
were adjusted to match: arrivals through the bottom doorways, the south walls,
and the walks to the breaker panel and the locker. Frame-cost checks
combine Bobbin's completed video-frame count and partial-frame cycle count.

```sh
# Build first, then (each run is bounded by the caller):
timeout 2400 python3 Projects/GBotAdventure/tests/workshop_test.py enhanced
timeout 2400 python3 Projects/GBotAdventure/tests/workshop_test.py plus
```

These tests run on Bobbin's IIe and II+ models. Native Windows PowerShell,
MAME, AppleWin and physical hardware have not been run in this Linux environment;
their launch/build instructions follow the workshop's existing native layout.

## Original portrait and future direction

![The original G-Bot character concept, preserved unchanged](art/gbot-workshop.png)

[Native full-screen portrait](art/gbot-workshop.hgr) ·
[280 × 192 portrait](art/gbot-workshop-280.png)

G-Bot is a curious repair robot, not a combat tank. The wider idea remains a
room-to-room repair adventure: the workshop, power room, security room and lab
now exist, with repairs that affect other rooms and gradually reveal the facility's
story. Room checkpoints rather than limited lives are the direction already used
for the guard. Two disks remain an option **if the world earns them**, not a
requirement to fill space.
