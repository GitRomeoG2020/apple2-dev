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
  & "$cc65\ld65.exe" -C rockfall.cfg ..\build\rockfall.o -o ..\build\rockfall.bin -m ..\build\rockfall.map
  if ($LASTEXITCODE) { throw 'ld65 failed' }
} finally { Pop-Location }

# Make a 140K DOS-order .dsk with the game on track 0 (self-booting, no DOS needed).
$bin = [IO.File]::ReadAllBytes("$proj\build\rockfall.bin")
if ($bin.Length -gt 4096) { throw "game is $($bin.Length) bytes; must fit in 4096 (track 0)" }
$img = New-Object byte[] 143360
$p2l = 0,7,14,6,13,5,12,4,11,3,10,2,9,1,8,15        # physical -> logical sector
for ($p = 0; $p -lt 16; $p++) {
  $n = [Math]::Min(256, [Math]::Max(0, $bin.Length - $p*256))
  if ($n -gt 0) { [Array]::Copy($bin, $p*256, $img, $p2l[$p]*256, $n) }
}
$dsk = "$proj\disk\rockfall.dsk"
[IO.File]::WriteAllBytes($dsk, $img)
Write-Host "Built $dsk ($($bin.Length) bytes of game)"

if ($Run) {
  Push-Location (Split-Path $mame)
  try { & $mame $Machine -flop1 $dsk -window } finally { Pop-Location }
}
