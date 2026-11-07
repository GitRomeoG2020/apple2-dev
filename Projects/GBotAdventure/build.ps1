# Native Windows build. From AppleII: .\Projects\GBotAdventure\build.ps1 [-Run]
# Uses the existing workshop cc65 tools; no Python, Pillow, WSL or Java required.
param([switch]$Run, [string]$Machine = 'apple2e')
$ErrorActionPreference = 'Stop'
$proj = $PSScriptRoot
$root = Resolve-Path (Join-Path $proj '..\..')
$cc65 = Join-Path $root 'Tools\cc65\bin'
$mame = Join-Path $root 'MAME\mame.exe'
New-Item -ItemType Directory -Force -Path "$proj\build","$proj\disk" | Out-Null
Push-Location "$proj\src"
try {
  foreach ($name in @('boot','gbot')) {
    & "$cc65\ca65.exe" "$name.s" -o "..\build\$name.o" -l "..\build\$name.lst"
    if ($LASTEXITCODE) { throw "ca65 failed: $name" }
  }
  & "$cc65\ld65.exe" -C gbot.cfg ..\build\boot.o ..\build\gbot.o -o ..\build\gbot.bin -m ..\build\gbot.map -Ln ..\build\gbot.lbl
  if ($LASTEXITCODE) { throw 'ld65 failed' }
} finally { Pop-Location }
# Same physical-sector mapping as tools/build.py. This disk has no DOS filesystem.
$bin = [IO.File]::ReadAllBytes("$proj\build\gbot.bin")
$game = $bin.Length - 4096
if ($game -le 0 -or $game -gt 24576) { throw "Load image is $game bytes; expected 1..24576" }
$bin[4] = [byte][Math]::Floor(($game + 4095) / 4096)
$img = New-Object byte[] 143360
$p2l = 0,7,14,6,13,5,12,4,11,3,10,2,9,1,8,15
for ($i = 0; $i -lt $bin.Length; $i += 256) {
  $n = [Math]::Min(256, $bin.Length - $i)
  $o = [int]([Math]::Floor($i / 4096) * 4096 + $p2l[[int][Math]::Floor($i / 256) % 16] * 256)
  [Array]::Copy($bin, $i, $img, $o, $n)
}
$dsk = "$proj\disk\gbot-after-hours.dsk"
[IO.File]::WriteAllBytes($dsk, $img)
Write-Host "Built $dsk (24576-byte 48K load; read-only 140K disk)"
if ($Run) {
  Push-Location (Split-Path $mame)
  try { & $mame $Machine -flop1 $dsk -window } finally { Pop-Location }
}
