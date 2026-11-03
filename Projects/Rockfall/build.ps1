# Build Rockfall on Windows PowerShell.  Run from Projects\Rockfall:   .\build.ps1
# Optional:  .\build.ps1 -Run     (also launches MAME with the disk)
param([switch]$Run, [string]$Machine = 'apple2e')
$ErrorActionPreference = 'Stop'
$proj = $PSScriptRoot
$root = Resolve-Path (Join-Path $proj '..\..')          # ...\AppleII
$cc65 = Join-Path $root 'Tools\cc65\bin'
$mame = Join-Path $root 'MAME\mame.exe'
New-Item -ItemType Directory -Force -Path "$proj\build","$proj\disk" | Out-Null

Push-Location "$proj\src"
try {
  & "$cc65\ca65.exe" rockfall.s -o ..\build\rockfall.o -l ..\build\rockfall.lst
  if ($LASTEXITCODE) { throw 'ca65 failed' }
  & "$cc65\ca65.exe" boot.s -o ..\build\boot.o -l ..\build\boot.lst
  if ($LASTEXITCODE) { throw 'ca65 failed' }
  & "$cc65\ld65.exe" -C rockfall.cfg ..\build\boot.o ..\build\rockfall.o -o ..\build\rockfall.bin -m ..\build\rockfall.map
  if ($LASTEXITCODE) { throw 'ld65 failed' }
} finally { Pop-Location }

# Make a 140K DOS-order .dsk (self-booting, no DOS). Same layout as tools/mkdisk.py:
# Track 0 physical sector 15 (from the loader image, src/hsdef.inc) is the saved high-score table:
# rebuilding resets it to the defaults.
# rockfall.bin = 4K track-0 loader + game; 256-byte chunk i -> track i/16, physical sector i%16.
$bin = [IO.File]::ReadAllBytes("$proj\build\rockfall.bin")
$game = $bin.Length - 4096
if ($game -le 0 -or $game -gt 24576) { throw "game is $game bytes; must be 1..24576 (`$6000-`$BFFF)" }
$bin[4] = [byte][Math]::Floor(($game + 4095) / 4096)     # loader: number of game tracks
$img = New-Object byte[] 143360
$p2l = 0,7,14,6,13,5,12,4,11,3,10,2,9,1,8,15        # physical -> logical sector
for ($i = 0; $i -lt $bin.Length; $i += 256) {
  $n = [Math]::Min(256, $bin.Length - $i)
  $o = [int]([Math]::Floor($i / 4096) * 4096 + $p2l[[int][Math]::Floor($i / 256) % 16] * 256)
  [Array]::Copy($bin, $i, $img, $o, $n)
}
$dsk = "$proj\disk\rockfall.dsk"
[IO.File]::WriteAllBytes($dsk, $img)
Write-Host "Built $dsk ($game bytes of game)"

if ($Run) {
  Push-Location (Split-Path $mame)
  try { & $mame $Machine -flop1 $dsk -window } finally { Pop-Location }
}
