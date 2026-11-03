# Apple II MAME test runner

Files: `Scripts\runner.lua` (MAME Lua), `Scripts\Run-Apple2.ps1` (PowerShell wrapper).
Results go to `Projects\<Project>\build\results.txt` (config written to `build\runner_cfg.lua`).

## Examples (run from `C:\Users\rjguerrero\Projects\AppleII\Scripts`)

```powershell
# Type in a BASIC program, RUN it, dump $0300-$030F and the text screen
.\Run-Apple2.ps1 -Project BeginnerTesting -Basic hello.bas -Dump '0300-030F'

# Assemble src\store.s at $6000, load it, CALL 24576, stop as soon as $0303 = $42
.\Run-Apple2.ps1 -Project BeginnerTesting -Asm store.s -LoadAddr 6000 -Call -WaitPeek '0303=42' -Dump '0300-0303,6000-601F'

# Fast, no window or sound
.\Run-Apple2.ps1 -Basic hello.bas -Dump '0300-0303' -Headless

# Save a PNG into build\ (needs a window, not -Headless)
.\Run-Apple2.ps1 -Basic hello.bas -Screenshot

# Use the IIc
.\Run-Apple2.ps1 -Basic hello.bas -Machine apple2c
```

If PowerShell blocks the script: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` (once),
or `Unblock-File .\Run-Apple2.ps1`.

## Parameters
| Param | Meaning |
|---|---|
| -Project | folder under Projects (default BeginnerTesting) |
| -Basic | BASIC file in src\ — typed line by line after `NEW`, then `RUN` |
| -Asm | ca65 source in src\ — built with `cl65 -t none --start-addr` to build\<name>.bin (+ .lst) |
| -Bin | raw binary in build\ to poke into memory |
| -LoadAddr | hex load address (default 6000) |
| -Call | type `CALL <addr>` after loading |
| -Dump | hex ranges, e.g. `'0300-030F,6000-60FF'` |
| -BootFrames | frames to wait before acting (default 120 = 2 s) |
| -Frames | frames to run after typing ends (default 300 = 5 s) |
| -WaitPeek | `'addr=value'` (hex) stop early when memory matches |
| -MaxFrames | hard timeout (default 3600 = 60 s) |
| -Machine | apple2e (default), apple2c, ... |
| -Screenshot | PNG snapshot into build\ |
| -Headless | `-video none -sound none -nothrottle` |
| -NoScreen | skip the text-screen capture |

## Results file contains
stop reason, registers (PC A X Y SP P + flags), hex/ASCII dumps, the 40x24 text screen
(page 1, high-bit stripped), and any `ERROR [...]` lines caught by pcall.

## Using runner.lua directly
```powershell
cd ..\MAME
$env:A2RUN_CFG = '..\Scripts\runner_cfg.lua'   # a Lua file that returns a table of options
.\mame.exe apple2e -sl6 '""' -window -skip_gameinfo -autoboot_script ..\Scripts\runner.lua
```
Env overrides: A2RUN_BASIC, A2RUN_BIN, A2RUN_LOADADDR, A2RUN_CALL, A2RUN_DUMP, A2RUN_FRAMES,
A2RUN_BOOTFRAMES, A2RUN_WAITPEEK, A2RUN_SNAPSHOT, A2RUN_OUT.

## Notes
- `-sl6 ""` leaves the disk card out so the IIe boots straight to `]`.
- Binary loading writes through the CPU's address space, so it's fine for main RAM ($0800-$BFFF);
  don't load over $C000+ or into aux/language-card RAM this way.
- `-WaitPeek` only starts checking after typing is done.
