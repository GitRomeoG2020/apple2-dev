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
# Boot track, code tracks, then rooms and aux tracks up to FREE_TRACK (src/layout.inc).
$layout = Get-Content "$proj\src\layout.inc" -Raw
$free = [int]([regex]::Match($layout, '(?m)^FREE_TRACK=(\d+)').Groups[1].Value)
if ($bin.Length -ne 4096 * $free) { throw "Image is $($bin.Length) bytes; expected $(4096 * $free)" }
if ($bin[0] -ne 5 -or $bin[4] -ne 3) { throw 'Boot must load sectors 0-4 and code tracks 1-3' }
$img = New-Object byte[] 143360
$p2l = 0,7,14,6,13,5,12,4,11,3,10,2,9,1,8,15
for ($i = 0; $i -lt $bin.Length; $i += 256) {
  $n = [Math]::Min(256, $bin.Length - $i)
  $o = [int]([Math]::Floor($i / 4096) * 4096 + $p2l[[int][Math]::Floor($i / 256) % 16] * 256)
  [Array]::Copy($bin, $i, $img, $o, $n)
}
$dsk = "$proj\disk\gbot-after-hours.dsk"
[IO.File]::WriteAllBytes($dsk, $img)
Write-Host "Built $dsk (boot load + disk-streamed rooms; read-only 140K disk)"
if ($Run) {
  Push-Location (Split-Path $mame)
  try { & $mame $Machine -flop1 $dsk -window } finally { Pop-Location }
}
