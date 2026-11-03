; ROCKFALL - dodge the falling rocks.  Apple II+/IIe, 48K, 6502, ca65.
; Self-booting: byte $0800 tells the Disk II boot ROM how many track-0
; sectors to load ($0800-$17FF); the ROM then jumps to $0801.
        .setcpu "6502"

; ---- hardware ----
KBD     = $C000
KBDSTRB = $C010
SPKR    = $C030
TXTCLR  = $C050
TXTSET  = $C051
MIXSET  = $C053
LOWSCR  = $C054
HIRES   = $C057
WAIT    = $FCA8          ; monitor delay routine (A = length)
MACHID  = $FBB3          ; $06 on IIe/IIc

; ---- game constants ----
NROCKS  = 5
PLAYY   = 148            ; top row of ship (field is rows 0-159, text below)
ROCKMAXY= 152            ; rock top row limit (rows y..y+7 must be < 160)
PXMAX   = 132            ; ship x in 2-pixel units (pixel x = 2*px)
FRAMEDLY= $44            ; WAIT value per frame (~13 ms)

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
        .addr s_press
        ldx #13
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
        jsr clrhgr
        jsr clrtext
        sta TXTCLR
        sta MIXSET
        sta LOWSCR
        sta HIRES
        ; ground line at row 158-159
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
        jsr drawship
        jsr status

; ================= main loop =================
loop:   jsr input
        jsr moveship
        jsr rocks
        jsr stars
        jsr collide
        lda DEAD
        bne gameover
        lda #FRAMEDLY
        jsr WAIT
        jmp loop

gameover:
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
        cmp #$95 & $DF           ; right arrow ($95 -> $95 & $DF = $95)
        beq @r
        cmp #$CC                 ; L
        beq @r
        cmp #$A0 & $DF           ; space stops
        bne @rts2
        lda #0
        sta DIR
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
        sta OLDPX
        ldx DIR
        cpx #1
        bne @right
        cmp #0
        beq @done
        dec PX
        jmp @redraw
@right: cmp #PXMAX
        bcs @done
        inc PX
@redraw:
        lda PX
        pha
        lda OLDPX
        sta PX
        jsr drawship             ; XOR erase at old
        pla
        sta PX
        jsr drawship             ; draw at new
@done:  rts

drawship:
        ldx PX
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

; X = rock index
drawrock:
        lda #<rock
        sta SRC
        lda #>rock
        sta SRC+1
        lda RCOL,x
        sta BCOL
        lda RY,x
        sta BY
        lda #2
        sta BW
        lda #8
        sta BH
        stx TMP
        jsr blit
        ldx TMP
        rts

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
        jsr drawrock
        jmp @next
@move:  jsr drawrock             ; erase
        lda RY,x
        clc
        adc SPEED
        sta RY,x
        cmp #ROCKMAXY+1
        bcs @gone
        jsr drawrock
        jmp @next
@gone:  lda #0
        sta RON,x
        jsr rand
        and #31
        clc
        adc #1
        sta RWAIT,x
        jsr addscore
@next:  dex
        bpl @lp
        rts

addscore:
        txa
        pha
        sed
        lda SCORE
        clc
        adc #1
        sta SCORE
        lda SCORE+1
        adc #0
        sta SCORE+1
        cld
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
@s:     jsr status
        pla
        tax
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
; Each star is a 2-pixel white dot (two adjacent bits of one byte), XORed
; onto the screen like every other sprite, so overlaps always cancel out.
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
        jsr xstar
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

; XOR star X onto the screen (keeps X)
xstar:  ldy SY,x
        lda hgrlo,y
        sta DST
        lda hgrhi,y
        sta DST+1
        ldy SCOL,x
        lda (DST),y
        eor SMSK,x
        sta (DST),y
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
@mv:    jsr xstar                ; erase
        inc SY,x
        lda SY,x
        cmp #STARMAXY+1
        bcc @dr
        lda #0
        sta SY,x
        jsr newstar
@dr:    jsr xstar                ; draw
@nx:    dex
        bpl @lp
@done:  rts

; ================= graphics =================
; XOR blit: SRC data, BW bytes wide, BH rows, at byte col BCOL, row BY
blit:   ldx BY
@row:   lda hgrlo,x
        clc
        adc BCOL
        sta DST
        lda hgrhi,x
        adc #0
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

; solid line across row X
hline:  lda hgrlo,x
        sta DST
        lda hgrhi,x
        sta DST+1
        ldy #39
        lda #$7F
@l:     sta (DST),y
        dey
        bpl @l
        rts

clrhgr: lda #0
        sta DST
        ldx #$20
        stx DST+1
        tay
@l:     sta (DST),y
        iny
        bne @l
        inc DST+1
        dex
        bne @l
        rts

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

status: jsr setstr2
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
        jsr prbcd
        rts

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
s_press:  .byte "PRESS ANY KEY TO START",0
s_hi:     .byte "HI SCORE",0
s_status: .byte "SCORE 0000   SPEED 00   HI 0000",0
s_over:   .byte "*** G A M E   O V E R ***",0
s_again:  .byte "ANY KEY: PLAY AGAIN   ESC: TITLE",0

starmask: .byte $03,$06,$0C,$18,$30,$60

; ship position tables: index = x in 2-pixel units
pdiv7:  .repeat PXMAX+1, I
        .byte (I*2)/7
        .endrep
pmod7:  .repeat PXMAX+1, I
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

        .include "sprites.s"
