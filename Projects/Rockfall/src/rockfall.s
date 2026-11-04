; ROCKFALL - dodge the falling rocks.  Apple II+/IIe, 48K, 6502, ca65.
; Self-booting: the stage-2 loader in src/boot.s (track 0, $0800) reads
; tracks 1+ to $6000 and jumps here with X = slot*16.
; Graphics are double-buffered on HGR pages 1 ($2000) and 2 ($4000) in
; full-screen hi-res (no mixed text: text page 2 at $0800 holds the
; resident loader). Score/speed/hi are drawn with a tiny hi-res font.
        .setcpu "6502"

; ---- hardware ----
KBD     = $C000
KBDSTRB = $C010
SPKR    = $C030
TXTCLR  = $C050
TXTSET  = $C051
MIXCLR  = $C052
MIXSET  = $C053
LOWSCR  = $C054
HISCR   = $C055
HIRES   = $C057
WAIT    = $FCA8          ; monitor delay routine (A = length)
MACHID  = $FBB3          ; $06 on IIe/IIc

; ---- game constants ----
NROCKS  = 5
PLAYY   = 140            ; top row of ship (field is rows 0-151, landscape 152-183, status 186-190)
; ---- rock sizes -- tweak here (tables rsize_* in RODATA) ----
; 0 small pebble 1x6 bytes x rows, 1.5x SPEED, +3;  1 medium rock 2x8, 1x SPEED, +5;
; 2 large boulder 3x14, 0.5x SPEED, 2 hits, +15.  Rocks vanish when their bottom would reach LANDY.
RSIZE   = $D0            ; NROCKS bytes each
RHP     = $D8            ; hits left
RSUB    = $E0            ; half-row speed remainder
MAXLG   = 2              ; at most this many boulders at once
SV_RSP  = $1AD0          ; per page: sprite drawn (0 pebble, 1 rock, 2 boulder, 3 cracked)
PXMAX   = 132            ; ship x in 2-pixel units (pixel x = 2*px)
HOLDNEW = 16             ; II+ (no key-down flag): frames a fresh arrow press moves
HOLDREP = 6              ; II+: frames per auto-repeat of the same arrow (~150 ms)
; frame pacing: after rendering, fdelay waits FDBASE ~100-cycle units minus the drawing cost of
; what is on screen (rcost per rock size, FLYCOST for a flyer), so the frame time stays the same
; whatever the rock mix. FDBASE: 5 medium rocks pace like the old game (~26.2k cycles/frame).
FDBASE  = 126
FLYCOST = 32

; ---- zero page ----
SRC     = $50            ; blit source ptr
DST     = $52            ; blit dest ptr
BW      = $54            ; blit width in bytes
BH      = $55            ; blit height
BCOL    = $56
BY      = $57
STR     = $58            ; string ptr
SEED    = $5A
TMP     = $5B
PX      = $5C            ; ship x (2px units)
OLDPX   = $5D
DIR     = $5E            ; 0 none, 1 left, 2 right
HOLD    = $5F            ; II+ key hold timer
ISIIE   = $60
SPEED   = $61
DODGE   = $62            ; rocks dodged since last speed-up
SCORE   = $63            ; 2 bytes BCD, $63=lo $64=hi
HISCORE = $65            ; 2 bytes BCD
DEAD    = $67
PER     = $68            ; sound period
DURL    = $69
DURH    = $6A
RCOL    = $70            ; NROCKS bytes each
RY      = $78
RWAIT   = $80
RON     = $88
FRAME   = $90            ; frame counter (star timing)
NSTARS  = 36
STARMAXY= 151            ; stars live in rows 0-151 (landscape strip starts at LANDY)
SCOL    = $1800          ; star tables (RAM below HGR page 1)
SMSK    = $1830
SY      = $1860
; per-page copies of what was last drawn on each HGR page (index page*64+i)
SV_SC   = $1900
SV_SM   = $1980
SV_SY   = $1A00
SV_RON  = $1A80          ; rocks: page*8+i
SV_RCOL = $1A90
SV_RY   = $1AA0
SV_PX   = $1AB0          ; ship: page
SV_LON  = $1AB2          ; laser: page
SV_LC   = $1AB4
SV_LM1  = $1AB6
SV_LM2  = $1AB8
SV_LY   = $1ABA
SV_VAL  = $1ABC          ; page holds a drawn frame
; more zero page
PGEOR   = $91            ; $00 = page 1, $60 = page 2 (hgrhi EOR)
BACK    = $92            ; page being drawn (0/1); other one is shown
FIRE    = $93            ; fire key pressed
LON     = $94            ; laser bolt active
LC      = $95            ; bolt byte column
LM1     = $96            ; bolt mask in LC
LM2     = $97            ; bolt mask in LC+1
LY      = $98            ; bolt top row
LX2     = $99            ; bolt x in 2-pixel units
VALID   = $9A
CNT     = $9B
OFS     = $9C
PR      = $9D            ; plot row / col / mask
PC      = $9E
PM      = $9F
DC      = $A0            ; xlaser params
DM1     = $A1
DM2     = $A2
DLY     = $A3
LLEN    = 12             ; bolt length (rows) = rows moved per frame
SROW    = 186            ; status line (hi-res font) top row
LANDY   = 152            ; landscape strip top row (LANDH rows, from land.inc)
LANDN   = $B2            ; current landscape 0..NLAND-1 (cycles each level)

; ---- bonus flyer (comet / satellite) -- tweak here ----
; One at a time, rows FMINY..FMINY+31, FLYSPD 2-px units per frame (~4 px/frame, ~2 s to cross).
; FX = screen x/2 + 14 (0 = fully off the left edge, FXEND = fully off the right edge).
; Next one FTMIN + 0..510 frames (~10-23 s at ~40 fps) after the last one spawned.
; Hit: comet 50, satellite 100 points; burst then the points shown for PTLEN frames.
FLYSPD  = 2
FXEND   = 154
FMINY   = 8
FTMIN   = 400
PTLEN   = 40
PTBURST = 32             ; PT >= PTBURST: explosion burst, below: points
FON     = $B3            ; flyer active
FX      = $B4
FY      = $B5            ; top row
FDIR    = $B6            ; 0 = moving right, 1 = left
FTYPE   = $B7            ; 0 comet, 1 satellite
FTL     = $B8            ; frames until the next flyer (16 bit)
FTH     = $B9
PK      = $BA            ; popup kind: 0 none, 1 burst, 2 points
PCL     = $BB            ; popup byte column
PY      = $BC            ; popup row
PV      = $BD            ; popup value: 0 = 50, 1 = 100
PT      = $BE            ; popup timer
BEXT    = $BF            ; clipped blit: sign extension of BCOL
CCOL    = $C0
FS      = $C1            ; sprite: 0 comet right, 1 comet left, 2/3 satellite (beacon on/off)
DPV     = $C2
SV_FON  = $1AC0          ; per-page copies (index page)
SV_FS   = $1AC2
SV_FX   = $1AC4
SV_FY   = $1AC6
SV_PK   = $1AC8
SV_PC   = $1ACA
SV_PY   = $1ACC
SV_PV   = $1ACE

; ---- title / attract mode -- tweak here ----
; Art view (hi-res page 1, mixed: text rows 20-23) for ARTT ticks, then the text score view
; for SCORET ticks, repeat. One tick = WAIT TICKW (~11 ms) + animation.
ARTT    = 1300           ; art view ticks, ~15 s
SCORET  = 450            ; ~5 s
TICKW   = $40
TCL     = $C3            ; ticks left in this view
TCH     = $C4
MON     = $C5            ; streaking meteor active
MCOL    = $C6
MROW    = $C7
MSTEP   = $C8
MTIM    = $C9            ; ticks until the next streak
MSUB    = $CA
RLEEND  = $CC            ; RLE decoder: stop row
RLEPG   = $CD            ; RLE decoder: 0 = page 1 only, else both pages
TVIEW   = $CE            ; 0 = art view, 1 = score view (for tests)

; ---- laser heat (Parsec-style overheat) -- tweak here ----
; HEAT rises by HEATSHOT per shot and falls by 1 every HEATCOOL frames (every
; frame while overheated). Reaching HEATMAX = OVERHEAT: the laser is locked
; until HEAT is back to HEATOK. ~40 fps: 1 shot per ~0.9 s never heats up;
; holding fire overheats on the 5th shot, then ~1.6 s lockout.
HEATMAX = 63
HEATSHOT= 18
HEATCOOL= 2              ; power of 2
HEATOK  = 0
BARCOL  = 31             ; heat bar: byte cols 31-38 (56 px), caps at 30/39
HEAT    = $A4
OVH     = $A5            ; 1 = overheated (laser locked)
LASTBAR = $A6            ; last bar fill drawn (px), $FF = redraw

; ---- levels -- tweak here ----
; A speed-up step happens every 15 rocks dodged (SPEED itself caps at 5, but
; steps keep counting). Every LEVELSPD steps = next level: brief banner.
LEVELSPD= 3
LEVEL   = $A7            ; current level, BCD (1..99)
SPDUPS  = $A8            ; speed-up steps since this level began
LVLUP   = $A9            ; 1 = show the level banner after this frame
SMODE   = $AA            ; star colour: 0 white, 1 violet, 2 green (cycles)
BROW    = 74             ; banner top row (10 rows: 3x5 font doubled)
BANCOL  = 16             ; banner first byte column

; ---- high-score table: one 256-byte page, ready to be written to a disk
; sector later with wrsect ($080B). 5 entries x 8 bytes, best first:
;   +0..2 initials (high-bit ASCII), +3 score lo (BCD), +4 score hi, +5 level (BCD), +6..7 0
; +$28 "RF" + version byte 1 (validates a table loaded from disk); rest 0.
HS      = $1B00
HSN     = 5
HSMAGIC = HS+$28
TROW    = $AB            ; text row of the table header
HILITE  = $AC            ; entry to show in inverse ($FF none)
RANK    = $AD            ; game-over rank 0-4, $FF = didn't qualify
LPOS    = $AE            ; initials entry: letter 0-2
JOYOK   = $AF            ; joystick seen centred at entry start
ENTER   = $B0            ; 1 while entering initials
SAVERR  = $B1            ; last save: 0 ok/none, 1 write protected, 2 disk error
WRSECT  = $080B          ; loader: write page A to track X, phys sector Y
HSTRK   = 0              ; high scores on disk: track 0, physical sector 15
HSSECT  = 15
BUTN0   = $C061
PREAD   = $FB1E          ; monitor paddle read: X = paddle, Y = 0-255

        .segment "CODE"
boot:   lda $C088,x              ; X = slot*16 from the loader: motor off
        cld
        ldx #$FF
        txs
        jsr hsvalid              ; loader read the saved table to $1B00
        bcc @hk
        ldx #0                   ; invalid: defaults, rest of page 0
@hs:    lda #0
        cpx #hsdef_end-hsdef
        bcs @hz
        lda hsdef,x
@hz:    sta HS,x
        inx
        bne @hs
@hk:    lda #$FF
        sta HILITE
        jsr sethi
        lda #$A5
        sta SEED
        lda #0
        sta ISIIE
        lda MACHID
        cmp #$06
        bne title
        inc ISIIE

; ================= title screen (attract mode) =================
title:  lda #0
        sta MON
        sta RLEPG                ; title art -> HGR page 1 only
        lda #<titleart
        sta SRC
        lda #>titleart
        sta SRC+1
        lda #0
        sta PR
        lda #TITLEH
        sta RLEEND
        jsr drawrle
        lda #60
        sta MTIM
        jsr artview
        bit KBDSTRB
        jsr intro                ; play tune over the art
@art:   jsr artview
        lda #<ARTT
        sta TCL
        lda #>ARTT
        sta TCH
@al:    jsr tick
        bcs @go
        jsr animate
        jsr tdec
        bne @al
        jsr mclear
        jsr scoreview
        lda #<SCORET
        sta TCL
        lda #>SCORET
        sta TCH
@sl:    jsr tick
        bcs @go
        jsr tdec
        bne @sl
        jmp @art
@go:    bit KBDSTRB
        jmp newgame

; one tick: wait, stir the RNG; C=1 if a key is waiting
tick:   inc SEED
        bne @s
        inc SEED
@s:     lda #TICKW
        jsr WAIT
        lda KBD
        asl
        rts
; TC-- ; Z=1 when it reaches 0
tdec:   lda TCL
        bne @l
        dec TCH
@l:     dec TCL
        lda TCL
        ora TCH
        rts

; hi-res art (page 1) + 4-line text window: tagline, controls, best score, flashing prompt
artview:
        lda #0
        sta TVIEW
        sta PGEOR
        jsr clrtext
        jsr setstr2
        .addr s_twist
        ldx #20
        ldy #2
        jsr print
        jsr setstr2
        .addr s_ctl
        ldx #21
        ldy #3
        jsr print
        jsr setstr2
        .addr s_best
        ldx #22
        ldy #13
        jsr print
        ldx #22                  ; initials + score of #1
        lda textlo,x
        sta DST
        lda texthi,x
        sta DST+1
        ldy #19
        ldx #0
@i:     lda HS,x
        sta (DST),y
        iny
        inx
        cpx #3
        bne @i
        iny
        lda HS+4
        jsr bcd2
        lda HS+3
        jsr bcd2
        jsr setstr2
        .addr s_press
        ldx #23
        ldy #9
        jsr print
        ldx #23                  ; prompt flashes
        lda textlo,x
        sta DST
        lda texthi,x
        sta DST+1
        ldy #39
@f:     lda (DST),y
        cmp #$A0
        beq @n
        and #$3F
        ora #$40
        sta (DST),y
@n:     dey
        bpl @f
        sta LOWSCR
        sta HIRES
        sta MIXSET
        sta TXTCLR
        rts

; the old title text screen: name, controls, prompt and the high-score table
scoreview:
        lda #1
        sta TVIEW
        sta TXTSET
        sta LOWSCR
        jsr clrtext
        jsr setstr2
        .addr s_title
        ldx #4
        ldy #12
        jsr print
        jsr setstr2
        .addr s_sub
        ldx #7
        ldy #7
        jsr print
        jsr setstr2
        .addr s_keys
        ldx #10
        ldy #6
        jsr print
        jsr setstr2
        .addr s_fire
        ldx #11
        ldy #11
        jsr print
        jsr setstr2
        .addr s_press
        ldx #14
        ldy #9
        jsr print
        lda #16
        sta TROW
        jmp drawtable

; art-view animation: twinkling stars, a meteor streak now and then (XOR on page 1)
animate:
        jsr rand                 ; twinkle: toggle one star every ~4 ticks
        and #3
        bne @m
        jsr rand
        and #31
        cmp #NTWINK
        bcs @m
        tax
        lda twrow,x
        sta PR
        lda twcol,x
        sta PC
        lda twmsk,x
        sta PM
        jsr plot
@m:     lda MON
        bne @run
        dec MTIM
        bne @r
        lda #1                   ; launch a streak
        sta MON
        jsr rand
        and #15
        sta MCOL
        jsr rand
        and #15
        adc #2
        sta MROW
        lda #22
        sta MSTEP
        lda #0
        sta MSUB
        jmp xstreak
@run:   inc MSUB
        lda MSUB
        and #1
        bne @r
        jsr xstreak              ; erase, move, redraw
        inc MCOL
        inc MROW
        inc MROW
        dec MSTEP
        beq @end
        jmp xstreak
@end:   lda #0
        sta MON
        jsr rand
        and #127
        adc #140
        sta MTIM
@r:     rts
; erase a streak left on screen (before leaving the art view)
mclear: lda MON
        beq @r
        lda #0
        sta MON
        lda #60
        sta MTIM
        jmp xstreak
@r:     rts
xstreak:
        lda #<streak
        sta SRC
        lda #>streak
        sta SRC+1
        lda MCOL
        sta BCOL
        lda MROW
        sta BY
        lda #3
        sta BW
        lda #6
        sta BH
        jmp blit

; ================= new game =================
newgame:
        lda #0
        sta SV_VAL               ; nothing drawn on either page yet
        sta SV_VAL+1
        sta DST
        lda #$20                 ; clear both HGR pages
        ldx #$40
        jsr clrmem
        jsr clrtext
        sta TXTCLR
        sta MIXCLR
        sta LOWSCR
        sta HIRES
        lda #1
        sta BACK                 ; draw page 2 first while page 1 shows
        lda #0
        sta LON
        sta FIRE
        sta HEAT
        sta OVH
        lda #$FF
        sta LASTBAR
        lda #0                   ; landscape 1 on both pages
        sta LANDN
        jsr drawland
        lda #0
        sta SCORE
        sta SCORE+1
        sta DODGE
        sta DIR
        sta HOLD
        sta DEAD
        sta SPDUPS
        sta LVLUP
        sta SMODE
        lda #1
        sta SPEED
        sta LEVEL
        ldx #NROCKS-1
@ri:    lda #0
        sta RON,x
        txa
        asl
        asl
        asl
        asl                      ; stagger: 16 frames apart
        clc
        adc #1
        sta RWAIT,x
        dex
        bpl @ri
        jsr initstars
        lda #0
        sta FON
        sta PK
        sta PT
        jsr settimer
        lda #66
        sta PX
        ldy #1                   ; status labels, both pages
        lda #<s_hstat
        sta STR
        lda #>s_hstat
        sta STR+1
        jsr hstr
        jsr status
        jsr heatbar

; ================= main loop =================
loop:   jsr input
        jsr moveship
        jsr rocks
        jsr heatcool
        jsr flyer
        jsr laser
        jsr stars
        jsr collide
        jsr render
        jsr flip
        jsr heatbar
        lda DEAD
        bne gameover
        lda LVLUP
        beq @nolv
        jsr banner
@nolv:
        jsr fdelay
        jmp loop

gameover:
        jsr render               ; same final frame on the other page too
        jsr flip
        jsr crash
        lda #0
        sta SAVERR
        jsr hsinsert             ; RANK, HILITE; table updated (initials AAA)
        jsr sethi
        jsr status
        ; show page 1 with the text window (text page 1 at $0400 is free)
        jsr clrtext
        jsr tstatus
        jsr setstr2
        .addr s_over
        ldx #22
        ldy #8
        jsr print
        jsr setstr2
        .addr s_again
        ldx #23
        ldy #4
        jsr print
        sta LOWSCR
        sta MIXSET
        ; short pause so a held key doesn't skip the screen
        ldx #10
@p:     lda #$FF
        jsr WAIT
        dex
        bne @p
        lda ISIIE                ; IIe: wait (max ~2 s) until a key held from play is
        beq @fl                  ; released, so its auto-repeat can't hit the initials
        ldx #12
@up:    lda KBDSTRB
        bpl @fl
        lda #$FF
        jsr WAIT
        dex
        bne @up
@fl:    bit KBDSTRB
        lda RANK
        bmi @tb
        jsr initials
        jsr hssave
@tb:    lda #0
        sta ENTER
        jsr goscreen
@k:     inc SEED
        lda KBD
        bpl @k
        bit KBDSTRB
        cmp #$9B                 ; ESC -> title
        bne @ng
        jmp title
@ng:    jmp newgame

; ================= high scores =================
; C=0 if the page at HS is a valid table ("RF", version 1, EOR $00-$2B = 0)
hsvalid:lda HS+$28
        cmp #'R'
        bne @no
        lda HS+$29
        cmp #'F'
        bne @no
        lda HS+$2A
        cmp #1
        bne @no
        lda #0
        ldx #$2B
@x:     eor HS,x
        dex
        bpl @x
        cmp #0
        bne @no
        clc
        rts
@no:    sec
        rts

; write the table to disk (new check byte first); SAVERR = 0 / 1 WP / 2 error
hssave: lda #0
        ldx #$2A
@x:     eor HS,x
        dex
        bpl @x
        sta HS+$2B
        jsr setstr2
        .addr s_saving
        ldx #19
        ldy #15
        jsr print
        lda #>HS
        ldx #HSTRK
        ldy #HSSECT
        jsr WRSECT
        bcs @e
        lda #0
@e:     sta SAVERR
        rts

; HISCORE (HUD) = top entry
sethi:  lda HS+3
        sta HISCORE
        lda HS+4
        sta HISCORE+1
        rts

; find SCORE's rank (first entry it beats), insert it there with level and
; initials "AAA". RANK = HILITE = rank or $FF.
hsinsert:
        ldx #0
        ldy #0
@c:     lda SCORE+1
        cmp HS+4,y
        bcc @nx
        bne @got
        lda SCORE
        cmp HS+3,y
        beq @nx
        bcs @got
@nx:    tya
        clc
        adc #8
        tay
        inx
        cpx #HSN
        bne @c
        ldx #$FF
        stx RANK
        stx HILITE
        rts
@got:   stx RANK
        stx HILITE
        sty TMP                  ; entry offset
        ldx #HSN*8-9             ; move entries rank..3 down one slot
@mv:    cpx TMP
        bcc @w
        lda HS,x
        sta HS+8,x
        dex
        bpl @mv
@w:     ldy TMP
        lda #$C1
        sta HS,y
        sta HS+1,y
        sta HS+2,y
        lda SCORE
        sta HS+3,y
        lda SCORE+1
        sta HS+4,y
        lda LEVEL
        sta HS+5,y
        lda #0
        sta HS+6,y
        sta HS+7,y
        rts

; table at text row TROW: header, then rows TROW+2.. "1. AAA  0250  LV03"
; (cols 11-28); entry HILITE in inverse; while ENTER, letter LPOS flashes.
drawtable:
        jsr setstr2
        .addr s_hshdr
        ldx TROW
        ldy #14
        jsr print
        lda #0
        sta CNT
@e:     lda CNT
        clc
        adc TROW
        adc #2
        tax                      ; text row
        lda CNT
        asl
        asl
        asl
        sta OFS                  ; entry offset
        lda textlo,x
        sta DST
        lda texthi,x
        sta DST+1
        ldy #11
        lda CNT
        clc
        adc #$B1                 ; '1'..'5'
        sta (DST),y
        iny
        lda #$AE                 ; '.'
        sta (DST),y
        ldy #14
        ldx OFS
@i:     lda HS,x
        sta (DST),y
        inx
        iny
        cpy #17
        bne @i
        ldy #19
        lda HS+1,x               ; x = OFS+3: score hi
        jsr bcd2
        lda HS,x
        jsr bcd2
        ldy #25
        lda #$CC                 ; 'L'
        sta (DST),y
        iny
        lda #$D6                 ; 'V'
        sta (DST),y
        iny
        lda HS+2,x               ; level
        jsr bcd2
        lda CNT
        cmp HILITE
        bne @nh
        ldy #10                  ; inverse bar, cols 10-29
@inv:   lda (DST),y
        and #$3F
        sta (DST),y
        iny
        cpy #30
        bne @inv
        lda ENTER
        beq @nh
        lda LPOS
        clc
        adc #14
        tay
        lda (DST),y
        ora #$40                 ; flashing
        sta (DST),y
@nh:    inc CNT
        lda CNT
        cmp #HSN
        beq @x
        jmp @e
@x:     rts
; BCD A -> 2 digits at (DST),y
bcd2:   pha
        lsr
        lsr
        lsr
        lsr
        ora #$B0
        sta (DST),y
        iny
        pla
        and #$0F
        ora #$B0
        sta (DST),y
        iny
        rts

; full text screen after game over: table (+ entry prompt while ENTER)
goscreen:
        jsr clrtext
        sta TXTSET
        sta LOWSCR
        jsr setstr2
        .addr s_over
        ldx #1
        ldy #8
        jsr print
        lda #5
        sta TROW
        jsr drawtable
        jsr tstatus
        lda ENTER
        beq @a
        jsr setstr2
        .addr s_new
        ldx #3
        ldy #4
        jsr print
        jsr setstr2
        .addr s_ihelp1
        ldx #14
        ldy #3
        jsr print
        jsr setstr2
        .addr s_ihelp2
        ldx #15
        ldy #3
        jsr print
        rts
@a:     lda SAVERR
        beq @a2
        cmp #1
        bne @a1
        jsr setstr2
        .addr s_wprot
        jmp @a3
@a1:    jsr setstr2
        .addr s_derr
@a3:    ldx #19
        ldy #4
        jsr print
@a2:    jsr setstr2
        .addr s_again
        ldx #23
        ldy #4
        jmp print

; initials entry for entry RANK: keys A-Z type a letter; left/down and
; right/up (or joystick left/right) cycle; RETURN, space or button 0 confirm.
initials:
        lda #1
        sta ENTER
        lda #0
        sta LPOS
        sta JOYOK
        ldx #0
        jsr PREAD                ; no joystick reads 255: ignore the stick
        cpy #48
        bcc @rd
        cpy #208
        bcs @rd
        inc JOYOK
@rd:    jsr goscreen
@in:    inc SEED
        lda KBD
        bmi @key
        lda BUTN0
        bmi @btn
        lda JOYOK
        beq @in
        ldx #0
        jsr PREAD
        cpy #48
        bcc @prev
        cpy #208
        bcs @next
        bcc @in
@btn:   lda BUTN0                ; wait for release
        bmi @btn
        bpl @ok
@key:   bit KBDSTRB
        and #$DF
        cmp #$C1
        bcc @ctl
        cmp #$DB
        bcs @ctl
        jsr letptr
        sta HS,y
        jmp @ok
@ctl:   cmp #$8D                 ; RETURN
        beq @ok
        cmp #$80                 ; space
        beq @ok
        cmp #$88                 ; left
        beq @prev
        cmp #$8A                 ; down
        beq @prev
        cmp #$95                 ; right
        beq @next
        cmp #$8B                 ; up
        beq @next
        bne @in
@prev:  jsr letptr
        lda HS,y
        sec
        sbc #1
        cmp #$C1
        bcs @st
        lda #$DA
        bne @st
@next:  jsr letptr
        lda HS,y
        clc
        adc #1
        cmp #$DB
        bcc @st
        lda #$C1
@st:    sta HS,y
        jsr goscreen
        lda JOYOK                ; stick auto-repeat ~0.3 s
        beq @in
        lda #$FF
        jsr WAIT
        lda #$FF
        jsr WAIT
        jmp @in
@ok:    inc LPOS
        lda LPOS
        cmp #3
        bcs @done
        jmp @rd
@done:  rts
; Y = RANK*8+LPOS (keeps A)
letptr: pha
        lda RANK
        asl
        asl
        asl
        adc LPOS
        tay
        pla
        rts

; ================= input =================
input:  lda KBD
        bmi @key
        lda ISIIE
        beq @plus
        lda KBDSTRB              ; IIe: bit 7 = a key is still held
        bmi @rts
        lda #0
        sta DIR
@rts:   rts
@plus:  lda HOLD                 ; II+: keep moving a few frames
        beq @stop
        dec HOLD
        rts
@stop:  sta DIR
        rts
@key:   bit KBDSTRB
        and #$DF                 ; fold lower case to upper
        cmp #$88                 ; left arrow
        beq @l
        cmp #$CA                 ; J
        beq @l
        cmp #$95                 ; right arrow
        beq @r
        cmp #$CC                 ; L
        beq @r
        cmp #$A0 & $DF           ; space fires
        beq @f
        cmp #$C1                 ; A fires
        bne @rts2
@f:     lda #1
        sta FIRE
@rts2:  rts
@l:     lda #1
        bne @set
@r:     lda #2
@set:   ldx #HOLDNEW             ; II+: new direction moves HOLDNEW frames,
        cmp DIR                  ; a repeat of the same key (host/MAME key
        bne @h                   ; repeat) only HOLDREP, so release stops fast
        ldx #HOLDREP
@h:     sta DIR
        stx HOLD
        rts

moveship:
        lda DIR
        beq @done
        lda PX
        ldx DIR
        cpx #1
        bne @right
        cmp #0
        beq @done
        dec PX
        rts
@right: cmp #PXMAX
        bcs @done
        inc PX
@done:  rts

; A = ship x (2px units); XOR onto page PGEOR
drawship:
        tax
        ldy pmod7,x
        lda ship_shift_lo,y
        sta SRC
        lda ship_shift_hi,y
        sta SRC+1
        lda pdiv7,x
        sta BCOL
        lda #PLAYY
        sta BY
        lda #3
        sta BW
        lda #8
        sta BH
        jmp blit

; XOR rock sprite A (0 pebble, 1 rock, 2 boulder, 3 cracked boulder) at BCOL/BY
drawrock:
        tay
        lda rsprlo,y
        sta SRC
        lda rsprhi,y
        sta SRC+1
        lda rspw,y
        sta BW
        lda rsph,y
        sta BH
        jmp blit

; frame pacing (see FDBASE)
fdelay: lda #FDBASE
        ldx #NROCKS-1
@r:     ldy RON,x
        beq @n
        ldy RSIZE,x
        sec
        sbc rcost,y
        bcc @z
@n:     dex
        bpl @r
        ldy FON
        beq @w
        sec
        sbc #FLYCOST
        bcc @z
@w:     tax
        beq @z
@o:     ldy #19                  ; ~100 cycles
@d:     dey
        bne @d
        dex
        bne @o
@z:     rts

; pick a size for a new rock (keeps X): odds by level, at most MAXLG boulders
pksize: lda LEVEL
        cmp #4
        bcc @b
        lda #4
@b:     tay
        dey                      ; bucket 0-3
        jsr rand
        and #15
        cmp rsmall,y
        bcc @sm
        cmp rlarge,y
        bcs @lg
@md:    lda #1
        rts
@sm:    lda #0
        rts
@lg:    stx TMP
        lda #0
        sta CNT
        ldx #NROCKS-1
@c:     lda RON,x
        beq @c2
        lda RSIZE,x
        cmp #2
        bne @c2
        inc CNT
@c2:    dex
        bpl @c
        ldx TMP
        lda CNT
        cmp #MAXLG
        bcs @md
        lda #2
        rts

rocks:  ldx #NROCKS-1
@lp:    lda RON,x
        bne @move
        dec RWAIT,x
        bne @next
        jsr pksize
        sta RSIZE,x
        tay
        lda rhp0,y
        sta RHP,x
        lda #0
        sta RSUB,x
        jsr rand                 ; random byte column that fits
@m:     cmp rncol,y
        bcc @ok
        sbc rncol,y
        jmp @m
@ok:    sta RCOL,x
        lda #0
        sta RY,x
        lda #1
        sta RON,x
        jmp @next
@move:  ldy RSIZE,x              ; speed in half-rows: 3/2/1 x SPEED
        lda SPEED
        cpy #2
        beq @v
        asl
        cpy #1
        beq @v
        adc SPEED
@v:     clc
        adc RSUB,x
        pha
        and #1
        sta RSUB,x
        pla
        lsr
        clc
        adc RY,x
        sta RY,x
        cmp rmaxy1,y             ; bottom would reach the landscape: gone, dodged
        bcc @next
        jsr killrock
        jsr addscore
@next:  dex
        bpl @lp
        rts

; rock X off; respawn later (keeps X)
killrock:
        lda #0
        sta RON,x
        jsr rand
        and #31
        clc
        adc #1
        sta RWAIT,x
        rts

addscore:                        ; +1 for a dodged rock
        inc DODGE
        lda DODGE
        cmp #15                  ; speed up every 15 rocks dodged
        bcc @s
        lda #0
        sta DODGE
        lda SPEED
        cmp #5
        bcs @st
        inc SPEED
@st:    inc SPDUPS               ; count the step even when SPEED is capped
        lda SPDUPS
        cmp #LEVELSPD
        bcc @s
        lda #0
        sta SPDUPS
        lda LEVEL
        cmp #$99
        beq @s
        sed
        clc
        adc #1
        cld
        sta LEVEL
        inc LVLUP                ; main loop shows the banner
        inc LANDN                ; next landscape (drawn during the banner)
        lda LANDN
        cmp #NLAND
        bcc @ln
        lda #0
        sta LANDN
@ln:
        inc SMODE                ; next star colour (new stars as they respawn)
        lda SMODE
        cmp #3
        bcc @s
        lda #0
        sta SMODE
@s:     lda #1
; add BCD A to score, redraw status (keeps X)
addpts: sed
        clc
        adc SCORE
        sta SCORE
        lda SCORE+1
        adc #0
        sta SCORE+1
        cld
        txa
        pha
        jsr status
        pla
        tax
        rts

; ================= laser =================
laser:  lda LON
        beq @idle
        lda LY                   ; bolt flies up LLEN rows per frame
        sec
        sbc #LLEN
        bcc @off
        sta LY
        jmp hits
@off:   lda #0
        sta LON
@idle:  lda FIRE
        beq @rts
        lda #0
        sta FIRE
        lda OVH
        beq @cool
        bit SPKR                 ; locked: just a soft click
        rts
@cool:  lda HEAT
        clc
        adc #HEATSHOT
        cmp #HEATMAX
        bcc @hs
        lda #HEATMAX
        inc OVH
@hs:    sta HEAT
        lda PX                   ; nose = pixels 2*PX+6, 2*PX+7
        clc
        adc #3
        sta LX2
        tax
        lda pdiv7,x
        sta LC
        ldy pmod7,x
        lda lmask1,y
        sta LM1
        lda lmask2,y
        sta LM2
        lda #PLAYY-LLEN
        sta LY
        lda #1
        sta LON
        jsr pew
        lda OVH
        beq @h
        jsr ovhsnd
        jsr hotlbl
@h:     jmp hits
@rts:   rts

; cool the laser once per frame (called before laser)
heatcool:
        lda HEAT
        beq @z
        lda OVH
        bne @dec                 ; locked: cool every frame
        lda FRAME
        and #HEATCOOL-1
        bne @r
@dec:   dec HEAT
        lda HEAT
        cmp #HEATOK+1
        bcs @r
@z:     lda OVH
        beq @r
        lda #0
        sta OVH
        sta HEAT
        ; fall through: label back to HEAT
        lda #<s_heat
        ldx #>s_heat
        bne lbl
@r:     rts
hotlbl: lda #<s_hot
        ldx #>s_hot
lbl:    sta STR
        stx STR+1
        ldy #26
        jmp hstr

; heat bar, both pages, rows SROW..SROW+4: caps + fill of HEAT*7/8 px.
; Blinks (empty every other 8 frames) while overheated. Only redraws on change.
heatbar:
        lda HEAT
        lsr
        lsr
        lsr
        sta TMP
        lda HEAT
        sec
        sbc TMP                  ; 0..56 px
        and #$FE                 ; even widths: clean white, no color fringe
        ldx OVH
        beq @v
        lda FRAME
        and #8
        beq @v0
        lda #0
        beq @v
@v0:    lda #56
@v:     cmp LASTBAR
        beq @rts
        sta LASTBAR
        lda #SROW
        sta PR
@row:   ldy PR
        lda hgrlo,y
        sta DST
        lda hgrhi,y
        sta DST+1
        lda LASTBAR
        sta CNT                  ; px left to fill
        ldy #BARCOL
@b:     lda CNT
        cmp #7
        bcc @part
        sbc #7
        sta CNT
        lda #$7F
        bne @put
@part:  tax
        lda #0
        sta CNT
        lda fill7,x
        ldx PR                   ; top/bottom rows: outline
        cpx #SROW
        beq @edge
        cpx #SROW+4
        bne @put
@edge:  lda #$7F
@put:   sta (DST),y
        tax
        lda DST+1
        eor #$60
        sta DST+1
        txa
        sta (DST),y
        lda DST+1
        eor #$60
        sta DST+1
        iny
        cpy #BARCOL+8
        bne @b
        lda #$40                 ; end caps
        ldy #BARCOL-1
        jsr @cap
        lda #$01
        ldy #BARCOL+8
        jsr @cap
        inc PR
        lda PR
        cmp #SROW+5
        bne @row
@rts:   rts
@cap:   sta (DST),y
        tax
        lda DST+1
        eor #$60
        sta DST+1
        txa
        sta (DST),y
        lda DST+1
        eor #$60
        sta DST+1
        rts

; bolt vs rocks: rows overlap and bolt x inside the rock's 7 units
hits:   jsr flyhit
        bcc @go
        rts
@go:    ldx #NROCKS-1
@lp:    lda RON,x
        beq @nx
        ldy RSIZE,x
        lda RY,x
        clc
        adc rsph,y
        cmp LY                   ; rock bottom (RY+h-1) >= bolt top
        bcc @nx
        beq @nx
        lda LY
        clc
        adc #LLEN-1
        cmp RY,x                 ; bolt bottom >= rock top
        bcc @nx
        sty TMP
        ldy RCOL,x
        lda LX2
        sec
        sbc rockx2,y
        bcc @nx
        ldy TMP
        cmp rhitw,y              ; bolt inside the sprite's width
        bcs @nx
        lda #0                   ; hit!
        sta LON
        dec RHP,x
        beq @kill
        jmp crackle              ; boulder: cracked, needs one more
@kill:  jsr killrock
        cpy #2
        beq @big
        lda rpts,y
        pha
        jsr crackle
        pla
        jmp addpts
@big:   lda RCOL,x               ; boulder: burst + "15" popup, big boom
        cmp #37
        bcc @c
        lda #36
@c:     sta PCL
        lda RY,x
        clc
        adc #3
        sta PY
        lda #2
        sta PV
        lda #PTLEN
        sta PT
        lda #1
        sta PK
        jsr bigboom
        lda #$15
        jmp addpts
@nx:    dex
        bpl @lp
        rts

; boulder explosion: two crackles and a low thud (~35 ms; keeps X)
bigboom:
        jsr crackle
        jsr crackle
        txa
        pha
        lda #<SPKR
        sta tog
        lda #220
        sta PER
        lda #14
        sta DURL
        lda #0
        sta DURH
        jsr tone
        pla
        tax
        rts

; bounding boxes in 2-pixel units / rows, per size
collide:
        ldx #NROCKS-1
@lp:    lda RON,x
        beq @next
        ldy RSIZE,x
        sty TMP
        lda RY,x
        clc
        adc rsph,y               ; RY+h > PLAYY: bottom reaches the ship
        cmp #PLAYY+1
        bcc @next
        lda RY,x
        cmp #PLAYY+8             ; top above the ship's bottom
        bcs @next
        ldy RCOL,x
        lda rockx2,y
        sta CNT                  ; rock left
        lda PX
        clc
        adc #6
        sec
        sbc CNT                  ; PX+6 > left
        bcc @next
        beq @next
        ldy TMP
        lda CNT
        clc
        adc rcolw,y              ; PX < left + w
        cmp PX
        bcc @next
        beq @next
        lda #1
        sta DEAD
        rts
@next:  dex
        bpl @lp
        rts

; ================= bonus flyer =================
flyer:  lda PT                   ; popup: burst, then points, then gone
        beq @f
        dec PT
        bne @pk
        lda #0
        sta PK
        beq @f
@pk:    lda PT
        cmp #PTBURST
        lda #1
        bcs @k
        lda #2
@k:     sta PK
@f:     lda FON
        bne @mv
        lda FTL                  ; count down to the next one
        bne @d
        lda FTH
        beq @spawn
        dec FTH
@d:     dec FTL
        rts
@spawn: jsr rand
        and #1
        sta FTYPE
        jsr rand
        and #1
        sta FDIR
        jsr rand
        and #31
        cmp #25
        bcc @y
        sbc #16
@y:     clc
        adc #FMINY               ; rows 8..32 (+7 tall)
        sta FY
        lda #0
        ldx FDIR
        beq @x
        lda #FXEND
@x:     sta FX
        lda #1
        sta FON
        jsr settimer
        jmp @spr
@mv:    lda FDIR
        bne @lt
        lda FX
        clc
        adc #FLYSPD
        sta FX
        cmp #FXEND
        bcc @spr
        bcs @off
@lt:    lda FX
        sec
        sbc #FLYSPD
        sta FX
        beq @off
        bcs @spr
@off:   lda #0                   ; left the screen
        sta FON
        rts
@spr:   lda FTYPE
        beq @c
        lda FRAME                ; satellite beacon blinks every 8 frames
        lsr
        lsr
        lsr
        and #1
        ora #2
        bne @s
@c:     lda FDIR
@s:     sta FS
        rts

; frames until the next flyer: FTMIN + 2*rand
settimer:
        jsr rand
        sta FTL
        lda #0
        sta FTH
        asl FTL
        rol FTH
        lda FTL
        clc
        adc #<FTMIN
        sta FTL
        lda FTH
        adc #>FTMIN
        sta FTH
        rts

; bolt vs flyer; C=1 if hit (flyer gone, bonus scored)
flyhit: lda FON
        beq @no
        lda FY
        clc
        adc #FLYH-1
        cmp LY                   ; flyer bottom >= bolt top
        bcc @no
        lda LY
        clc
        adc #LLEN-1
        cmp FY                   ; bolt bottom >= flyer top
        bcc @no
        lda LX2                  ; bolt x - flyer left, 2-px units
        clc
        adc #14
        sec
        sbc FX
        bcc @no
        cmp #11
        bcs @no
        lda #0
        sta FON
        sta LON
        lda FY
        sta PY
        ldx FX
        lda pdiv7,x
        sec
        sbc #4
        bpl @c0
        lda #0
@c0:    cmp #37
        bcc @c1
        lda #36
@c1:    sta PCL
        lda FTYPE
        sta PV
        lda #PTLEN
        sta PT
        lda #1
        sta PK
        jsr bonus
        lda #$50
        jsr addpts
        lda PV
        beq @y
        lda #$50
        jsr addpts
@y:     sec
        rts
@no:    clc
        rts

; XOR flyer sprite A (FS) at FX = X, row Y on page PGEOR, clipped at both edges
drawfly:
        sty BY
        asl
        asl
        asl
        sta TMP
        lda pmod7,x
        clc
        adc TMP
        tay
        lda flyspr_lo,y
        sta SRC
        lda flyspr_hi,y
        sta SRC+1
        lda pdiv7,x
        sec
        sbc #4
        sta BCOL
        lda #FLYW
        sta BW
        lda #FLYH
        sta BH
; XOR blit like blit, but BCOL may be negative/past 39: off-screen bytes skipped
fblit:  lda #0
        ldx BCOL
        bpl @p
        lda #$FF
@p:     sta BEXT
        ldx BY
@row:   lda hgrlo,x
        clc
        adc BCOL
        sta DST
        lda hgrhi,x
        eor PGEOR
        adc BEXT
        sta DST+1
        lda BCOL
        sta CCOL
        ldy #0
@b:     lda CCOL
        cmp #40
        bcs @s
        lda (DST),y
        eor (SRC),y
        sta (DST),y
@s:     inc CCOL
        iny
        cpy BW
        bne @b
        lda SRC
        clc
        adc BW
        sta SRC
        bcc @nc
        inc SRC+1
@nc:    inx
        dec BH
        bne @row
        rts

; XOR popup kind A (1 burst, 2 points DPV) at byte col X, row Y on page PGEOR
drawpop:
        sty BY
        stx BCOL
        cmp #1
        bne @dig
        lda #<burst
        sta SRC
        lda #>burst
        sta SRC+1
        lda #3
        sta BW
        lda #7
        sta BH
        jmp blit
@dig:   iny
        sty PR
        stx PC
        lda DPV
        beq @50
        cmp #2
        beq @15
        lda #1
        jsr xglyph
        lda #0
        jsr xglyph
        lda #0
        jmp xglyph
@15:    lda #1
        jsr xglyph
        lda #5
        jmp xglyph
@50:    lda #5
        jsr xglyph
        lda #0
; XOR status-font glyph A at col PC, rows PR..PR+4, page PGEOR; PC++
xglyph: sta TMP
        asl
        asl
        adc TMP
        tax
        lda PR
        sta DLY
@r:     ldy DLY
        lda hgrlo,y
        sta DST
        lda hgrhi,y
        eor PGEOR
        sta DST+1
        ldy PC
        lda (DST),y
        eor font,x
        sta (DST),y
        inx
        inc DLY
        lda DLY
        sec
        sbc PR
        cmp #5
        bne @r
        inc PC
        rts

; ================= starfield =================
; Each star is a 2-pixel white dot (two adjacent bits of one byte).
; Even-numbered stars fall 1 row every 2 frames, odd ones every 4 (parallax).
initstars:
        ldx #NSTARS-1
@lp:    jsr newstar
        jsr rand
@m:     cmp #STARMAXY+1
        bcc @ok
        sbc #STARMAXY+1
        bcs @m
@ok:    sta SY,x
        dex
        bpl @lp
        rts

; random column + bit pair for star X (keeps X)
newstar:
        jsr rand
@m:     cmp #40
        bcc @ok
        sbc #40
        bcs @m
@ok:    sta SCOL,x
        lda SMODE
        bne @col
        jsr rand
        and #7
        cmp #6
        bcc @k
        sbc #3                   ; 6,7 -> 3,4
@k:     tay
        lda starmask,y
        sta SMSK,x
        rts
; coloured star: one pixel; screen x = 7*col+bit, x even = violet, odd = green
@col:   jsr rand
        and #7
        cmp #7
        bcc @b
        lda #3
@b:     sta TMP                  ; bit 0-6
        lda SCOL,x
        eor TMP
        eor SMODE                ; want (col^bit)&1 == SMODE-1
        and #1
        bne @set
        lda TMP
        cmp #6
        bcc @up
        dec TMP
        bcs @set
@up:    inc TMP
@set:   ldy TMP
        lda bitmask,y
        sta SMSK,x
        rts

stars:  inc FRAME
        lda FRAME
        and #1
        bne @done                ; nothing on odd frames
        ldx #NSTARS-1
@lp:    txa
        lsr
        bcc @mv                  ; even star: every 2nd frame
        lda FRAME
        and #2
        bne @nx                  ; odd star: every 4th frame
@mv:    inc SY,x
        lda SY,x
        cmp #STARMAXY+1
        bcc @nx
        lda #0
        sta SY,x
        jsr newstar
@nx:    dex
        bpl @lp
@done:  rts

; ================= double buffering =================
; render: on back page, XOR-erase what was drawn there last time (saved per
; page), XOR-draw the current state, and save it for that page.
render: ldx BACK
        lda pgeor,x
        sta PGEOR
        lda SV_VAL,x
        sta VALID
        txa
        asl
        asl
        asl
        sta OFS                  ; rocks: page*8
        ; --- ship ---
        lda VALID
        beq @s1
        lda SV_PX,x
        jsr drawship
@s1:    ldx BACK
        lda PX
        sta SV_PX,x
        jsr drawship
        ; --- laser bolt ---
        ldx BACK
        lda VALID
        beq @l1
        lda SV_LON,x
        beq @l1
        lda SV_LC,x
        sta DC
        lda SV_LM1,x
        sta DM1
        lda SV_LM2,x
        sta DM2
        lda SV_LY,x
        sta DLY
        jsr xlaser
@l1:    ldx BACK
        lda LON
        sta SV_LON,x
        beq @l2
        lda LC
        sta SV_LC,x
        sta DC
        lda LM1
        sta SV_LM1,x
        sta DM1
        lda LM2
        sta SV_LM2,x
        sta DM2
        lda LY
        sta SV_LY,x
        sta DLY
        jsr xlaser
@l2:    ; --- rocks ---
        lda #NROCKS-1
        sta CNT
@rk:    lda CNT
        clc
        adc OFS
        tay
        lda VALID
        beq @r1
        lda SV_RON,y
        beq @r1
        lda SV_RCOL,y
        sta BCOL
        lda SV_RY,y
        sta BY
        lda SV_RSP,y
        jsr drawrock
@r1:    lda CNT
        tax
        clc
        adc OFS
        tay
        lda RON,x
        sta SV_RON,y
        beq @r2
        lda RCOL,x
        sta SV_RCOL,y
        sta BCOL
        lda RY,x
        sta SV_RY,y
        sta BY
        lda RSIZE,x              ; sprite: size, cracked boulder = 3
        cmp #2
        bne @id
        lda #4
        sec
        sbc RHP,x
@id:    sta SV_RSP,y
        jsr drawrock
@r2:    dec CNT
        bpl @rk
        ; --- bonus flyer ---
        ldx BACK
        lda VALID
        beq @fa
        lda SV_FON,x
        beq @fa
        ldy SV_FY,x
        lda SV_FS,x
        pha
        lda SV_FX,x
        tax
        pla
        jsr drawfly
@fa:    ldx BACK
        lda FON
        sta SV_FON,x
        beq @fb
        lda FS
        sta SV_FS,x
        lda FX
        sta SV_FX,x
        lda FY
        sta SV_FY,x
        ldy FY
        ldx FX
        lda FS
        jsr drawfly
@fb:    ; --- hit popup ---
        ldx BACK
        lda VALID
        beq @pa
        lda SV_PK,x
        beq @pa
        lda SV_PV,x
        sta DPV
        lda SV_PK,x
        pha
        ldy SV_PY,x
        lda SV_PC,x
        tax
        pla
        jsr drawpop
@pa:    ldx BACK
        lda PK
        sta SV_PK,x
        beq @pb
        lda PV
        sta SV_PV,x
        sta DPV
        lda PCL
        sta SV_PC,x
        lda PY
        sta SV_PY,x
        ldy PY
        ldx PCL
        lda PK
        jsr drawpop
@pb:
        ; --- stars ---
        lda BACK
        asl
        asl
        asl
        asl
        asl
        asl
        sta OFS                  ; stars: page*64
        lda #NSTARS-1
        sta CNT
@st:    lda CNT
        clc
        adc OFS
        tay
        lda VALID
        beq @t1
        lda SV_SY,y
        sta PR
        lda SV_SC,y
        sta PC
        lda SV_SM,y
        sta PM
        jsr plot
@t1:    lda CNT
        tax
        clc
        adc OFS
        tay
        lda SY,x
        sta SV_SY,y
        sta PR
        lda SCOL,x
        sta SV_SC,y
        sta PC
        lda SMSK,x
        sta SV_SM,y
        sta PM
        jsr plot
        dec CNT
        bpl @st
        ldx BACK
        lda #1
        sta SV_VAL,x
        rts

; show the page just drawn, draw the other one next
flip:   lda BACK
        bne @p2
        sta LOWSCR
        inc BACK
        rts
@p2:    sta HISCR
        lda #0
        sta BACK
        rts

; XOR mask PM at row PR, col PC
plot:   ldy PR
        lda hgrlo,y
        sta DST
        lda hgrhi,y
        eor PGEOR
        sta DST+1
        ldy PC
        lda (DST),y
        eor PM
        sta (DST),y
        rts

; XOR the laser bolt DC/DM1/DM2, rows DLY..DLY+LLEN-1
xlaser: ldx DLY
        lda #LLEN
        sta BH
@r:     lda hgrlo,x
        sta DST
        lda hgrhi,x
        eor PGEOR
        sta DST+1
        ldy DC
        lda (DST),y
        eor DM1
        sta (DST),y
        lda DM2
        beq @n
        iny
        eor (DST),y
        sta (DST),y
@n:     inx
        dec BH
        bne @r
        rts

; ================= graphics =================
; XOR blit: SRC data, BW bytes wide, BH rows, at byte col BCOL, row BY
blit:   ldx BY
@row:   lda hgrlo,x
        clc
        adc BCOL
        sta DST
        lda hgrhi,x
        adc #0
        eor PGEOR
        sta DST+1
        ldy #0
@b:     lda (DST),y
        eor (SRC),y
        sta (DST),y
        iny
        cpy BW
        bne @b
        lda SRC
        clc
        adc BW
        sta SRC
        bcc @nc
        inc SRC+1
@nc:    inx
        dec BH
        bne @row
        rts

; solid line across row X on both pages
hline:  lda hgrlo,x
        sta DST
        lda hgrhi,x
        sta DST+1
        ldy #39
        lda #$7F
@l:     sta (DST),y
        dey
        bpl @l
        lda DST+1
        eor #$60
        sta DST+1
        ldy #39
        lda #$7F
@l2:    sta (DST),y
        dey
        bpl @l2
        rts

; zero X pages starting at page A (DST lo must be 0)
clrmem: sta DST+1
        lda #0
        tay
@l:     sta (DST),y
        iny
        bne @l
        inc DST+1
        dex
        bne @l
        rts

; ---- hi-res status font (3x5, pixels doubled -> white) ----
; glyph A at byte col Y, both pages; advances Y
hchar:  sty PC
        sta TMP
        asl
        asl
        adc TMP                  ; *5
        tax
        lda #SROW
        sta PR
@r:     ldy PR
        lda hgrlo,y
        sta DST
        lda hgrhi,y
        sta DST+1
        ldy PC
        lda font,x
        sta (DST),y
        lda DST+1
        eor #$60
        sta DST+1
        lda font,x
        sta (DST),y
        inx
        inc PR
        lda PR
        cmp #SROW+5
        bne @r
        ldy PC
        iny
        rts

; glyph string STR ($FF-terminated) at col Y
hstr:   lda #0
        sta CNT
@l:     sty TMP+0
        ldy CNT
        lda (STR),y
        cmp #$FF
        beq @d
        ldy TMP
        jsr hchar
        inc CNT
        bne @l
@d:     rts

; BCD A at col Y (hi-res); advances Y by 2
hbcd:   pha
        lsr
        lsr
        lsr
        lsr
        jsr hchar
        pla
        and #$0F
        jmp hchar

status: ldy #4
        lda SCORE+1
        jsr hbcd
        lda SCORE
        jsr hbcd
        ldy #12
        lda SPEED
        jsr hchar
        ldy #16
        lda LEVEL
        jsr hbcd
        ldy #22
        lda HISCORE+1
        jsr hbcd
        lda HISCORE
        jmp hbcd

; ---- level banner: "LEVEL N" XOR-drawn big (2x tall) on both pages ----
banner: jsr bdraw
        jsr drawland             ; new scenery on both pages while the game is paused
        lda #<SPKR               ; rising 3-note chime
        sta tog
        ldy #2
@n:     lda chper,y
        sta PER
        lda chlen,y
        sta DURL
        lda #0
        sta DURH
        tya
        pha
        jsr tone
        pla
        tay
        dey
        bpl @n
        ldx #8                   ; ~1.5 s total
@w:     lda #$FF
        jsr WAIT
        dex
        bne @w
        jsr bdraw                ; XOR again = erased
        bit KBDSTRB
        lda #0
        sta LVLUP
        sta DIR
        sta FIRE
        rts
bdraw:  lda #<s_level
        sta STR
        lda #>s_level
        sta STR+1
        ldy #BANCOL
        lda #0
        sta CNT
@l:     sty DLY
        ldy CNT
        lda (STR),y
        cmp #$FF
        beq @d
        ldy DLY
        jsr bchar
        inc CNT
        bne @l
@d:     ldy DLY
        lda LEVEL
        cmp #$10
        bcc @lo                  ; no leading zero
        lsr
        lsr
        lsr
        lsr
        jsr bchar
        lda LEVEL
@lo:    and #$0F
; glyph A at byte col Y, rows BROW..BROW+9, XOR on both pages; advances Y
bchar:  sty PC
        sta TMP
        asl
        asl
        adc TMP                  ; *5
        tax
        lda #BROW
        sta PR
@r:     ldy PR
        lda hgrlo,y
        sta DST
        lda hgrhi,y
        sta DST+1
        ldy PC
        lda (DST),y
        eor font,x
        sta (DST),y
        lda DST+1
        eor #$60
        sta DST+1
        lda (DST),y
        eor font,x
        sta (DST),y
        inc PR
        lda PR
        and #1                   ; BROW even: next glyph row every 2 rows
        bne @r
        inx
        lda PR
        cmp #BROW+10
        bne @r
        ldy PC
        iny
        rts

; ---- landscape LANDN -> rows LANDY..LANDY+LANDH-1, both pages (RLE, see tools/gen_land.py)
drawland:
        ldx LANDN
        lda landlo,x
        sta SRC
        lda landhi,x
        sta SRC+1
        lda #LANDY
        sta PR
        lda #LANDY+LANDH
        sta RLEEND
        lda #1
        sta RLEPG
; RLE stream at SRC -> rows PR..RLEEND-1 (page 1, or both if RLEPG)
drawrle:
        lda #0
        sta PC
@c:     jsr getb
        tax
        bmi @run
        sta BW                   ; ctl+1 literals
        inc BW
@lit:   jsr getb
        jsr putb
        dec BW
        bne @lit
        beq @chk
@run:   and #$7F
        clc
        adc #3
        sta BW
        jsr getb
        sta TMP
@r:     lda TMP
        jsr putb
        dec BW
        bne @r
@chk:   lda PR
        cmp RLEEND
        bcc @c
        rts
getb:   ldy #0
        lda (SRC),y
        inc SRC
        bne @x
        inc SRC+1
@x:     rts
putb:   pha
        ldy PR
        lda hgrlo,y
        sta DST
        lda hgrhi,y
        sta DST+1
        ldy PC
        pla
        sta (DST),y
        ldx RLEPG
        beq @one
        pha
        lda DST+1
        eor #$60
        sta DST+1
        pla
        sta (DST),y
@one:   inc PC
        lda PC
        cmp #40
        bcc @x
        lda #0
        sta PC
        inc PR
@x:     rts

; ================= text =================
clrtext:
        ldx #23
@r:     lda textlo,x
        sta DST
        lda texthi,x
        sta DST+1
        ldy #39
        lda #$A0
@c:     sta (DST),y
        dey
        bpl @c
        dex
        bpl @r
        rts

; setstr2: JSR setstr2 / .addr string  -> sets STR
setstr2:
        pla
        sta DST
        pla
        sta DST+1
        ldy #1
        lda (DST),y
        sta STR
        iny
        lda (DST),y
        sta STR+1
        lda DST
        clc
        adc #2
        tax
        lda DST+1
        adc #0
        pha
        txa
        pha
        rts

; print zero-terminated STR at text row X, col Y
print:  lda textlo,x
        sta DST
        lda texthi,x
        sta DST+1
        tya
        clc
        adc DST
        sta DST
        ldy #0
@l:     lda (STR),y
        beq @d
        ora #$80
        sta (DST),y
        iny
        bne @l
@d:     rts

; print BCD byte A at row X col Y; advances Y by 2
prbcd:  pha
        lda textlo,x
        sta DST
        lda texthi,x
        sta DST+1
        pla
        pha
        lsr
        lsr
        lsr
        lsr
        ora #$B0
        sta (DST),y
        iny
        pla
        and #$0F
        ora #$B0
        sta (DST),y
        iny
        rts

; text-page status line (game over screen)
tstatus:
        jsr setstr2
        .addr s_status
        ldx #21
        ldy #1
        jsr print
        ldx #21
        ldy #7
        lda SCORE+1
        jsr prbcd
        lda SCORE
        jsr prbcd
        ldy #19
        lda SPEED
        jsr prbcd
        ldy #29
        lda LEVEL
        jsr prbcd
        ldy #36
        lda HISCORE+1
        jsr prbcd
        lda HISCORE
        jmp prbcd

; ================= misc =================
rand:   lda SEED
        asl
        bcc @n
        eor #$1D
@n:     bne @z
        lda #$5A                 ; never let seed stick at 0
@z:     sta SEED
        rts

; ================= sound =================
; tone: PER = half-period delay, DURL/H = number of half-cycles
tone:
tonelp: lda SPKR
tog = tonelp + 1                 ; operand low byte (self-modified for rests)
        ldx PER
@d:     dex
        bne @d
        lda DURL
        bne @n
        dec DURH
@n:     dec DURL
        lda DURL
        ora DURH
        bne tonelp
        rts

intro:  ldy #0
@nt:    lda tune,y
        beq @end
        ldx #<SPKR
        cmp #1
        bne @s2
        ldx #<KBD                ; rest: read keyboard instead of speaker
        lda #200
@s2:    sta PER
        txa
        sta tog
        lda tune+1,y
        sta DURL
        lda tune+2,y
        sta DURH
        tya
        pha
        jsr tone
        pla
        tay
        iny
        iny
        iny
        jmp @nt
@end:   lda #<SPKR
        sta tog
        rts

; ---------------------------------------------------------------
; pew: laser fire sound, descending sweep ~3.5 kHz -> ~700 Hz, ~28 ms.
; All timing at 1.023 MHz.  One half-period (speaker toggle to toggle):
;   bit SPKR 4 + ldx 3 + delay (5*X-1) + frac/step update 22 = 5*X+28 cyc
;   X=23  -> 143 cyc -> 3577 Hz;   X=140 -> 728 cyc -> 703 Hz
; X (PER) grows by 1.80 (1 + 204/256) every half-period: 65 half-periods,
; total ~28,700 cycles = ~28 ms (exact model: tools/render_sfx.py).
PEWHI   = 23
PEWLO   = 140
pew:    lda #PEWHI
        sta PER
        lda #0
        sta DURL                 ; fractional part of PER
@hp:    bit SPKR                 ; 4
        ldx PER                  ; 3
@d:     dex                      ; 2 \ 5*X-1
        bne @d                   ; 3 /
        lda DURL                 ; 3
        clc                      ; 2
        adc #204                 ; 2
        sta DURL                 ; 3
        lda PER                  ; 3
        adc #1                   ; 2
        sta PER                  ; 3
        cmp #PEWLO               ; 2
        bcc @hp                  ; 3 (2 on exit)
        rts

; crackle: laser HIT sound, ~10 ms noise burst, distinct from the pew.
; Delays come from this routine's own code bytes (deterministic "noise").
; Per toggle: lda abs,y 4 + and 2 + tax 2 + inx 2 + (5*X-1) + bit 4
;   + iny 2 + cpy 2 + bne 3 = 5*X+20, X=1..32 -> 25..180 cyc.
; 96 toggles ~ 10 ms (max 17.3k cyc = 17 ms).  Preserves X.
CRKN    = 96
crackle:
        txa
        pha
        ldy #0
@c:     lda pew,y                ; 4 (5 if page cross)
        and #$1F                 ; 2
        tax                      ; 2
        inx                      ; 2
@d:     dex                      ; 2 \ 5*X-1
        bne @d                   ; 3 /
        bit SPKR                 ; 4
        iny                      ; 2
        cpy #CRKN                ; 2
        bne @c                   ; 3
        pla
        tax
        rts

; bonus: fast rising arpeggio C6-E6-G6-C7-E7-G7-C8 + C7-G7-C8 trill, ~130 ms
bonus:  lda #<SPKR
        sta tog
        ldy #0
@n:     lda bnper,y
        beq @x
        sta PER
        lda bnlen,y
        sta DURL
        lda #0
        sta DURH
        tya
        pha
        jsr tone
        pla
        tay
        iny
        bne @n
@x:     rts

; overheat warning: two-tone buzz hi/lo/hi/lo, ~1 kHz / ~600 Hz, ~32 ms
OVHHI   = 96
OVHLO   = 165
ovhsnd: lda #<SPKR
        sta tog
        lda #3
        sta CNT
@t:     lda CNT
        and #1
        tax
        lda ovhper,x
        sta PER
        lda ovhlen,x
        sta DURL
        lda #0
        sta DURH
        jsr tone
        dec CNT
        bpl @t
        rts

crash:  lda #<SPKR
        sta tog
        ; noise burst
        lda #0
        sta DURH
        ldy #0
@nz:    jsr rand
        lsr
        lsr
        tax
@nd:    dex
        bne @nd
        lda SPKR
        iny
        bne @nz
        inc DURH
        lda DURH
        cmp #3
        bne @nz
        ; falling sweep
        lda #60
        sta PER
@sw:    lda #12
        sta DURL
        lda #0
        sta DURH
        jsr tone
        inc PER
        inc PER
        lda PER
        cmp #240
        bcc @sw
        rts

; ================= data =================
        .segment "RODATA"
.macro NOTE f, ms
        .byte (500000/f-15)/5
        .word ms*f/500
.endmacro
.macro REST ms
        .byte 1
        .word ms                  ; ~1 ms per half-cycle at PER=200
.endmacro
tune:   NOTE 523,110
        NOTE 659,110
        NOTE 784,110
        NOTE 1047,220
        REST 60
        NOTE 784,110
        NOTE 1047,330
        REST 120
        NOTE 880,110
        NOTE 784,110
        NOTE 659,110
        NOTE 523,330
        .byte 0

s_title:  .byte "R O C K F A L L",0
s_sub:    .byte "DODGE THE FALLING METEORS!",0
s_twist:  .byte "THEY'RE NOT ROCKS. THEY'RE METEORS!",0
s_ctl:    .byte "ARROWS OR J/L MOVE   SPACE OR A FIRE",0
s_best:   .byte "BEST:",0
s_keys:   .byte "ARROWS OR J / L TO MOVE",0
s_fire:   .byte "SPACE OR A TO FIRE",0
s_press:  .byte "PRESS ANY KEY TO START",0
s_hshdr:  .byte "HIGH SCORES",0
s_saving: .byte "SAVING...",0
s_wprot:  .byte "DISK WRITE PROTECTED - NOT SAVED",0
s_derr:   .byte "DISK ERROR - SCORES NOT SAVED",0
s_new:    .byte "NEW HIGH SCORE! ENTER YOUR INITIALS",0
s_ihelp1: .byte "A-Z: TYPE  ARROWS/STICK: CHANGE",0
s_ihelp2: .byte "RETURN/SPACE/BUTTON: OK",0
hsdef:
        .include "hsdef.inc"
hsdef_end:
s_status: .byte "SCORE 0000  SPEED 00  LEVEL 00  HI 0000",0
s_over:   .byte "*** G A M E   O V E R ***",0
s_again:  .byte "ANY KEY: PLAY AGAIN   ESC: TITLE",0

starmask: .byte $03,$06,$0C,$18,$30,$60
pgeor:    .byte $00,$60
lmask1:   .byte $03,$06,$0C,$18,$30,$60,$40
lmask2:   .byte $00,$00,$00,$00,$00,$00,$01
; status labels as font glyph indices (0-9, C10 D11 E12 H13 I14 P15 R16 blank17 S18 O19 A20 T21 L22 V23)
; "SC 0000 SPD0 LV00 HI 0000 " (cols 1-25), runs on into s_heat (cols 26-29)
s_hstat:  .byte 18,10,17,0,0,0,0,17,18,15,11,0,17,22,23,0,0,17,13,14,17,0,0,0,0
s_heat:   .byte 13,12,20,21,$FF            ; HEAT
s_hot:    .byte 13,19,21,17,$FF            ; HOT
s_level:  .byte 22,12,23,12,22,17,$FF    ; "LEVEL "
bitmask:  .byte $01,$02,$04,$08,$10,$20,$40
fill7:    .byte $00,$01,$03,$07,$0F,$1F,$3F
ovhper:   .byte OVHLO,OVHHI
chper:    .byte 60,80,100                 ; chime (played last to first)
chlen:    .byte 90,70,60
.macro BN f,ms
        .byte (500000/f-15)/5
.endmacro
.macro BL f,ms
        .byte ms*f/500
.endmacro
bnper:  BN 1047,15
        BN 1319,15
        BN 1568,15
        BN 2093,15
        BN 2637,15
        BN 3136,15
        BN 4186,15
        BN 2093,10
        BN 3136,10
        BN 4186,20
        .byte 0
bnlen:  BL 1047,15
        BL 1319,15
        BL 1568,15
        BL 2093,15
        BL 2637,15
        BL 3136,15
        BL 4186,15
        BL 2093,10
        BL 3136,10
        BL 4186,20
ovhlen:   .byte 10,14                      ; half-cycles: lo ~8.5 ms, hi ~7.3 ms

; ship position tables: index = x in 2-pixel units
pdiv7:  .repeat 160, I
        .byte (I*2)/7
        .endrep
pmod7:  .repeat 160, I
        .byte (I*2) .mod 7
        .endrep
; ---- rock sizes: 0 pebble, 1 rock, 2 boulder (3 = cracked boulder sprite) ----
rsprlo: .byte <pebble,<rock,<boulder,<boulder_cracked
rsprhi: .byte >pebble,>rock,>boulder,>boulder_cracked
rspw:   .byte PEBBLE_W,ROCK_W,BOULDER_W,BOULDER_W
rsph:   .byte PEBBLE_H,ROCK_H,BOULDER_H,BOULDER_H
rmaxy1: .byte LANDY-PEBBLE_H+1,LANDY-ROCK_H+1,LANDY-BOULDER_H+1   ; RY >= this: gone
rncol:  .byte 41-PEBBLE_W,41-ROCK_W,41-BOULDER_W                 ; spawn columns
rhp0:   .byte 1,1,2                                               ; laser hits needed
rpts:   .byte $03,$05,$15                                         ; points (BCD)
rhitw:  .byte 3,7,11                                              ; laser hit width, 2-px units
rcolw:  .byte 2,6,9                                               ; ship collision: PX < left+w
rcost:  .byte 8,14,31                                             ; erase+draw cost, ~100-cycle units
; spawn odds per level bucket (L1, L2, L3, L4+), out of 16: pebble if r < rsmall, boulder if r >= rlarge
rsmall: .byte 3,4,5,5
rlarge: .byte 15,14,14,13
; rock left edge in 2-pixel units per byte column
rockx2: .repeat 40, I
        .byte (I*7)/2
        .endrep
hgrlo:  .repeat 192, YY
        .byte <($2000 + (YY .mod 8)*$400 + ((YY/8) .mod 8)*$80 + (YY/64)*$28)
        .endrep
hgrhi:  .repeat 192, YY
        .byte >($2000 + (YY .mod 8)*$400 + ((YY/8) .mod 8)*$80 + (YY/64)*$28)
        .endrep
textlo: .repeat 24, R
        .byte <($400 + (R .mod 8)*$80 + (R/8)*$28)
        .endrep
texthi: .repeat 24, R
        .byte >($400 + (R .mod 8)*$80 + (R/8)*$28)
        .endrep

        .include "font.s"
        .include "sprites.s"
        .include "land.inc"
        .include "flyer.inc"
        .include "title.inc"
