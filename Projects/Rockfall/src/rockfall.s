; ROCKFALL - dodge the falling rocks.  Apple II+/IIe, 48K, 6502, ca65.
; Self-booting: byte $0800 tells the Disk II boot ROM how many track-0
; sectors to load ($0800-$17FF); the ROM then jumps to $0801.
; Graphics are double-buffered on HGR pages 1 ($2000) and 2 ($4000) in
; full-screen hi-res (no mixed text, because text page 2 at $0800 is where
; this code lives). Score/speed/hi are drawn with a tiny hi-res font.
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
PLAYY   = 148            ; top row of ship (field is rows 0-159, status below)
ROCKMAXY= 152            ; rock top row limit (rows y..y+7 must be < 160)
PXMAX   = 132            ; ship x in 2-pixel units (pixel x = 2*px)
FRAMEDLY= $2F            ; WAIT value per frame (~6 ms; rendering takes the rest)

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
STARMAXY= 156            ; stars live in rows 0-156 (ground is 158-159)
SCOL    = $1800          ; star tables (RAM above the 4K game image)
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
SROW    = 172            ; status line (hi-res font) top row

        .segment "CODE"
        .byte $10                ; boot ROM: load 16 sectors of track 0
boot:   lda $C088,x              ; X = slot*16 from boot ROM: motor off
        cld
        ldx #$FF
        txs
        lda #0
        sta HISCORE
        sta HISCORE+1
        lda #$A5
        sta SEED
        lda #0
        sta ISIIE
        lda MACHID
        cmp #$06
        bne title
        inc ISIIE

; ================= title screen =================
title:  sta TXTSET
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
        ldy #8
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
        jsr setstr2
        .addr s_hi
        ldx #18
        ldy #13
        jsr print
        ldx #18
        ldy #23
        lda HISCORE+1
        jsr prbcd
        lda HISCORE
        jsr prbcd
        bit KBDSTRB
        jsr intro                ; play tune
@wait:  inc SEED                 ; seed RNG from time until key
        bne @w2
        inc SEED
@w2:    lda KBD
        bpl @wait
        bit KBDSTRB

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
        ; ground line at row 158-159, on both pages
        ldx #158
        jsr hline
        ldx #159
        jsr hline
        lda #0
        sta SCORE
        sta SCORE+1
        sta DODGE
        sta DIR
        sta HOLD
        sta DEAD
        lda #1
        sta SPEED
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
        lda #66
        sta PX
        ldy #1                   ; status labels, both pages
        lda #<s_hstat
        sta STR
        lda #>s_hstat
        sta STR+1
        jsr hstr
        jsr status

; ================= main loop =================
loop:   jsr input
        jsr moveship
        jsr rocks
        jsr laser
        jsr stars
        jsr collide
        jsr render
        jsr flip
        lda DEAD
        bne gameover
        lda #FRAMEDLY
        jsr WAIT
        jmp loop

gameover:
        jsr render               ; same final frame on the other page too
        jsr flip
        jsr crash
        ; update high score
        lda SCORE+1
        cmp HISCORE+1
        bcc @nohi
        bne @hi
        lda SCORE
        cmp HISCORE
        bcc @nohi
@hi:    lda SCORE
        sta HISCORE
        lda SCORE+1
        sta HISCORE+1
@nohi:  jsr status
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
        bit KBDSTRB
@k:     inc SEED
        lda KBD
        bpl @k
        bit KBDSTRB
        cmp #$9B                 ; ESC -> title
        bne @ng
        jmp title
@ng:    jmp newgame

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
@set:   sta DIR
        lda #12
        sta HOLD
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

; XOR a rock at BCOL/BY
drawrock:
        lda #<rock
        sta SRC
        lda #>rock
        sta SRC+1
        lda #2
        sta BW
        lda #8
        sta BH
        jmp blit

rocks:  ldx #NROCKS-1
@lp:    lda RON,x
        bne @move
        dec RWAIT,x
        bne @next
        jsr rand                 ; spawn at random byte column 0-38
@m:     cmp #39
        bcc @ok
        sbc #39
        jmp @m
@ok:    sta RCOL,x
        lda #0
        sta RY,x
        lda #1
        sta RON,x
        jmp @next
@move:  lda RY,x
        clc
        adc SPEED
        sta RY,x
        cmp #ROCKMAXY+1
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
        bcs @s
        inc SPEED
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
        jmp hits
@rts:   rts

; bolt vs rocks: rows overlap and bolt x inside the rock's 7 units
hits:   ldx #NROCKS-1
@lp:    lda RON,x
        beq @nx
        lda RY,x
        clc
        adc #7
        cmp LY                   ; rock bottom >= bolt top
        bcc @nx
        lda LY
        clc
        adc #LLEN-1
        cmp RY,x                 ; bolt bottom >= rock top
        bcc @nx
        ldy RCOL,x
        lda LX2
        sec
        sbc rockx2,y
        bcc @nx
        cmp #7
        bcs @nx
        jsr killrock             ; hit!
        jsr crackle
        lda #0
        sta LON
        lda #5
        jmp addpts
@nx:    dex
        bpl @lp
        rts

; bounding-box collision in 2-pixel units
collide:
        ldx #NROCKS-1
@lp:    lda RON,x
        beq @next
        lda RY,x
        cmp #PLAYY-7             ; rock bottom (y+7) >= PLAYY ?
        bcc @next
        cmp #PLAYY+8             ; rock top < PLAYY+8 ?
        bcs @next
        ldy RCOL,x
        lda PX
        sec
        sbc rockx2,y             ; dx = ship - rock
        bcs @pos
        eor #$FF
        adc #1
@pos:   cmp #6                   ; |dx| < 6 units (12 px) -> hit
        bcs @next
        lda #1
        sta DEAD
        rts
@next:  dex
        bpl @lp
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
        jsr rand
        and #7
        cmp #6
        bcc @k
        sbc #3                   ; 6,7 -> 3,4
@k:     tay
        lda starmask,y
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
        jsr drawrock
@r2:    dec CNT
        bpl @rk
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

status: ldy #7
        lda SCORE+1
        jsr hbcd
        lda SCORE
        jsr hbcd
        ldy #20
        lda SPEED
        jsr hbcd
        ldy #28
        lda HISCORE+1
        jsr hbcd
        lda HISCORE
        jmp hbcd

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
        ldy #20
        lda SPEED
        jsr prbcd
        ldy #28
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
s_sub:    .byte "DODGE THE FALLING ROCKS!",0
s_keys:   .byte "ARROWS OR J / L TO MOVE",0
s_fire:   .byte "SPACE OR A TO FIRE",0
s_press:  .byte "PRESS ANY KEY TO START",0
s_hi:     .byte "HI SCORE",0
s_status: .byte "SCORE 0000   SPEED 00   HI 0000",0
s_over:   .byte "*** G A M E   O V E R ***",0
s_again:  .byte "ANY KEY: PLAY AGAIN   ESC: TITLE",0

starmask: .byte $03,$06,$0C,$18,$30,$60
pgeor:    .byte $00,$60
lmask1:   .byte $03,$06,$0C,$18,$30,$60,$40
lmask2:   .byte $00,$00,$00,$00,$00,$00,$01
; status labels as font glyph indices (0-9 digits, $11 blank)
s_hstat:  .byte 5,10,0,16,12,17,0,0,0,0,17,17,17,5,15,12,12,11,17,0,0,17,17,17,13,14,17,0,0,0,0,$FF

; ship position tables: index = x in 2-pixel units
pdiv7:  .repeat PXMAX+4, I
        .byte (I*2)/7
        .endrep
pmod7:  .repeat PXMAX+4, I
        .byte (I*2) .mod 7
        .endrep
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
