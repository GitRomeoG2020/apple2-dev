; G-Bot: After Hours -- read-only Disk II loader, derived from the workshop's
; Rockfall loader. NO write routine, score sector or game-specific persistence.
; ROM loads T0 physical sectors 0..3 at $0800. Tracks 1..6 -> $6000..$BFFF.
        .setcpu "6502"
WAIT=$FCA8
SLOT=$2B
CURPH=$3C
TRK=$3D
BUF=$3E
IDX=$26
HVOL=$40
HTRK=$41
HSEC=$42
TMP=$44
LEFT=$45
PAGE0=$46
CNT=$47
DONE=$0D60
NBUF1=$0C00
NBUF2=$0D00
GAME=$6000
        .segment "BOOT"
        .byte 4
        jmp start
ntracks:.byte 6
start:  cld
        stx SLOT
        jsr $FC58
        ldy #0
@msg:   lda msg,y
        beq @go
        ora #$80
        sta $05A8+7,y
        iny
        bne @msg
@go:    bit $C051
        bit $C054
        ldx SLOT
        lda $C08E,x
        lda #0
        sta CURPH
        lda #>GAME
        sta PAGE0
        lda #1
        sta TRK
@track: lda TRK
        jsr seek
        ldy #15
        lda #0
@clear: sta DONE,y
        dey
        bpl @clear
        lda #16
        sta LEFT
@sector:jsr rdsect
        bcs @sector
        dec LEFT
        bne @sector
        lda PAGE0
        clc
        adc #16
        sta PAGE0
        inc TRK
        lda TRK
        sec
        sbc #1
        cmp ntracks
        bcc @track
        ldx SLOT
        jmp GAME

; rdsect: read the next sector that passes under the head on track TRK.
; If its DONE flag is clear, decode it to page PAGE0+sector, set DONE, C=0.
; C=1 on any error, wrong track (re-seeks), or already-done sector.
rdsect: ldx SLOT
        jsr rdadr
        bcs @err
        lda HTRK
        cmp TRK
        beq @ok
        asl                      ; wrong track: trust header, re-seek
        sta CURPH
        lda TRK
        jsr seek
        sec
        rts
@ok:    ldy HSEC
        cpy #16
        bcs @err
        lda DONE,y
        bne @err
        jsr rddata
        bcs @err
        ldy HSEC
        tya
        clc
        adc PAGE0
        sta BUF+1
        lda #0
        sta BUF
        jsr postnib
        ldy HSEC
        lda #1
        sta DONE,y
        clc
        rts
@err:   sec
        rts


; ---- rdadr: find D5 AA 96, read vol/trk/sec/chk (4+4). C=1 on bad checksum/timeout.
rdadr:  lda #0
        sta CNT
        ldy #0
@r1:    iny
        bne @r2
        inc CNT
        beq @bad                 ; ~65k nibbles: no disk / no sync
@r2:    lda $C08C,x
        bpl @r2
@r3:    cmp #$D5
        bne @r1
@r4:    lda $C08C,x
        bpl @r4
        cmp #$AA
        bne @r3
@r5:    lda $C08C,x
        bpl @r5
        cmp #$96
        bne @r3
        ldy #0
@r6:    lda $C08C,x
        bpl @r6
        sec                      ; 4+4: (odd<<1 | 1) & even
        rol a
        sta TMP
@r7:    lda $C08C,x
        bpl @r7
        and TMP
        sta HVOL,y
        iny
        cpy #4
        bne @r6
        lda HVOL
        eor HTRK
        eor HSEC
        eor HVOL+3
        bne @bad
        clc
        rts
@bad:   sec
        rts

; ---- rddata: D5 AA AD within 32 nibbles, 342 data nibbles + checksum (DOS 3.3
; timing: inner loops <= 26 cycles per 32-cycle nibble; tables page-aligned).
rddata: ldy #$20
@s1:    dey
        beq @bad
@s2:    lda $C08C,x
        bpl @s2
@s3:    eor #$D5
        bne @s1
        nop
@s4:    lda $C08C,x
        bpl @s4
        cmp #$AA
        bne @s3
        nop
@s5:    lda $C08C,x
        bpl @s5
        cmp #$AD
        bne @s3
        ldy #$56
        lda #0
@n1:    dey
        sty IDX
@n2:    ldy $C08C,x
        bpl @n2
        eor dnib-$96,y
        ldy IDX
        sta NBUF2,y
        bne @n1
@n3:    sty IDX
@n4:    ldy $C08C,x
        bpl @n4
        eor dnib-$96,y
        ldy IDX
        sta NBUF1,y
        iny
        bne @n3
@n5:    ldy $C08C,x
        bpl @n5
        cmp dnib-$96,y
        bne @bad
@n6:    lda $C08C,x
        bpl @n6
        cmp #$DE
        bne @bad
        clc
        rts
@bad:   sec
        rts

; ---- postnib: NBUF1/NBUF2 -> (BUF) (DOS 3.3 order)
postnib:ldy #0
@p1:    ldx #$56
@p2:    dex
        bmi @p1
        lda NBUF1,y
        lsr NBUF2,x
        rol a
        lsr NBUF2,x
        rol a
        sta (BUF),y
        iny
        bne @p2
        ldx SLOT
        rts

; ---- seek: move head to track A by phase stepping (2 phases per track).
; Like DOS: energise the current phase first, then for each half-track step
; turn the next phase on, wait ~19 ms, turn the previous phase off; finally
; settle ~19 ms and release the last phase.  (Conservative but simple; DOS
; accelerates with a table, we just use a fixed delay.)
seek:   asl a
        sta TMP                  ; target half-track
        jsr phon                 ; hold current position
@s0:    lda CURPH
        cmp TMP
        beq @done
        pha                      ; previous phase
        bcc @up
        dec CURPH
        bcs @step
@up:    inc CURPH
@step:  jsr phon                 ; next phase on
        lda #$56                 ; ~19 ms
        jsr WAIT
        pla
        jsr phoff                ; previous phase off
        jmp @s0
@done:  lda #$56                 ; settle
        jsr WAIT
        lda CURPH
        jsr phoff
        ldx SLOT
        rts
phon:   lda CURPH
        jsr phx
        lda $C081,x
        rts
phoff:  jsr phx
        lda $C080,x
        rts
phx:    and #3
        asl a
        ora SLOT
        tax
        rts

msg: .byte "G-BOT: AFTER HOURS / LOADING",0

        .segment "DNIB"          ; at $0B96: 6+2 nibble -> 6-bit value
dnib:
        .byte $00,$01,$00,$00,$02,$03,$00,$04,$05,$06,$00,$00,$00,$00,$00,$00
        .byte $07,$08,$00,$00,$00,$09,$0A,$0B,$0C,$0D,$00,$00,$0E,$0F,$10,$11
        .byte $12,$13,$00,$14,$15,$16,$17,$18,$19,$1A,$00,$00,$00,$00,$00,$00
        .byte $00,$00,$00,$00,$00,$1B,$00,$1C,$1D,$1E,$00,$00,$00,$1F,$00,$00
        .byte $20,$21,$00,$22,$23,$24,$25,$26,$27,$28,$00,$00,$00,$00,$00,$29
        .byte $2A,$2B,$00,$2C,$2D,$2E,$2F,$30,$31,$32,$00,$00,$33,$34,$35,$36
        .byte $37,$38,$00,$39,$3A,$3B,$3C,$3D,$3E,$3F
