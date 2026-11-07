# G-Bot Adventure

**Working title — not final.** An optional naming idea is **G-Bot: After Hours**.
The stable workshop folder is `Projects/GBotAdventure` regardless of the eventual title.

## Status

Planning/scaffold only. **No gameplay, build script, executable, bootable disk, or
artwork has been implemented yet.** Everything below describes a proposed direction,
not existing features; details remain open to collaboration.

## Proposed concept

An original, fixed-room repair adventure with exploration and bursts of danger.
Room-to-room transitions take inspiration from Berzerk and Castle Wolfenstein,
with original assets and design rather than copied characters, rooms, or mechanics.
Bringing broken equipment back online could open routes—and wake security systems
that were better left switched off.

The proposed protagonist is a curious maintenance robot, not a combat tank:
- A squat, battered cream-colored body inspired by an Apple II.
- A green screen face with expressive pixel eyes and a chest disk-drive light.
- Chunky feet, one grabber hand, and a repair/zap probe on the other arm.
- A larger, readable sprite with walking animation and a visibly extending repair probe.

Fixed rooms are intended to leave more room for character and environment detail
without requiring scrolling. Sprite dimensions, graphics techniques, controls,
and memory budgets are still to be worked out in the prototype.

## Proposed first prototype

Start with three connected rooms to test the repair/explore loop before building
an entire facility:
1. **Workshop/tutorial:** a quiet space to learn movement and a simple repair.
2. **Dark power room:** restore power and discover what it changes elsewhere.
3. **Security room:** react to systems awakened by restored power, introducing danger.

The first milestone would be readable movement, room transitions, and one repair
with a visible consequence—not a complete game. None of this is implemented yet.

## Intended technical direction

- Apple II+/IIe, 48 KB RAM; 6502 assembly using the workshop's ca65/ld65 toolchain.
- Follow the existing native Windows PowerShell build workflow with the workshop's
  cc65, AppleCommander/JRE, and MAME setup; no WSL or new major tool installation planned.
- Two disks are acceptable later if the world needs them, but are not a requirement
  or an established disk layout. Prototype scope and memory usage come first.

There are deliberately no build/run commands yet: no buildable program or disk
exists for this project. Rockfall remains separate and unchanged.

## Folder layout

- `src/` — reserved for future assembly source and project assets.
- `disk/` — reserved for future distributable disk images.
- `tests/` — reserved for future checks and emulator tests.
- `tools/` — reserved for future project-specific helpers; reuse workshop tools where practical.
- `build/` — future generated intermediates; ignored by the workshop `.gitignore`
  and created locally/by a future build, not tracked in Git.

The empty tracked directories use `.gitkeep` only to preserve the scaffold.
See the [workshop README](../../README.md) for shared tools and repository layout.
