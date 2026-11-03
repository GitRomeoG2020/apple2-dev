; ROCKFALL stage-2 boot loader ("RWTS-lite").  Lives on track 0, $0800-$0AFF.
; The Disk II boot ROM reads physical sectors 0..(byte $0800)-1 of track 0
; to $0800.. and jumps to $0801 with X = slot*16 and the drive motor on.
; We then read whole tracks 1..NTRACKS (6+2 GCR, our own read routine) to
; $6000.. and jump to $6000 (the game) with X = slot*16.
; Disk layout (written by tools/mkdisk.py / build.ps1): the file
; build/rockfall.bin is laid out in PHYSICAL sector order: 256-byte chunk i
; -> track i/16, physical sector i%16.  So track t, physical sector s holds
; game page $60 + (t-1)*16 + s.  NTRACKS (byte $0804) is patched in by the
; disk builder from the image size.
; Entry points kept resident for the game (e.g. a future high-score save):
;   $0805 JMP seek    (A = track)        $0808 JMP rdsect (reads any sector of
;   current track into page (PAGES),hdr in HSEC)  $080B JMP wrsect (TODO: write).
; Loader RAM: $0800-$0AFF code/tables, $0B00-$0C55 nibble buffers.
        .setcpu "6502"
WAIT    = $FCA8
HOME    = $FC58
SLOT    = $2B            ; slot*16 (boot ROM also keeps it here)
CURPH   = $3C            ; current half-track (phase position*1)
TRK     = $3D
BUF     = $3E            ; ptr for postnibblize
IDX     = $26
HVOL    = $40            ; header: vol,trk,sec,chk at $40-$43
HTRK    = $41
HSEC    = $42
TMP     = $44
LEFT    = $45            ; sectors still needed on this track
PAGE0   = $46            ; dest page for sector 0 of this track
CNT     = $47
DONE    = $0C60          ; 16 flags
NBUF1   = $0B00          ; 256 x 6-bit
NBUF2   = $0C00          ; 86 x 2-bit
GAME    = $6000

        .segment "BOOT"
        .byte 3                  ; boot ROM: load physical sectors 0-2
        jmp start                ; $0801
ntracks:.byte 0                  ; $0804 patched by disk builder
        jmp seek                 ; $0805
        jmp rdsect               ; $0808
        jmp wrsect               ; $080B (placeholder)
start:  cld
        stx SLOT
        jsr HOME
        ldy #0
@m:     lda msg,y
        beq @m2
        ora #$80
        sta $05A8+15,y           ; text row 11
        iny
        bne @m
@m2:    bit $C051                ; text mode, page 1
        bit $C054
        ldx SLOT
        lda $C08E,x              ; read mode
        lda #0
        sta CURPH                ; boot ROM left the head on track 0 (phase 0)
        lda #>GAME
        sta PAGE0
        lda #1
        sta TRK
@trk:   lda TRK
        jsr seek
        ldy #15
        lda #0
@c:     sta DONE,y
        dey
        bpl @c
        lda #16
        sta LEFT
@sec:   jsr rdsect
        bcs @sec                 ; error / already have it -> next one
        dec LEFT
        bne @sec
        lda PAGE0
        clc
        adc #16
        sta PAGE0
        ldy TRK                  ; progress: one * per track
        lda #$AA
        sta $05A8+25,y
        inc TRK
        lda TRK
        sec
        sbc #1
        cmp ntracks
        bcc @trk
        ldx SLOT
        jmp GAME                 ; game turns the motor off

; ---- rdsect: read the next sector that passes under the head on track TRK.
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

wrsect: sec                      ; TODO: write 6+2 (prenibble, Q7H, 32-cycle loop)
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

msg:    .byte "LOADING...",0

        .segment "DNIB"          ; at $0A96: 6+2 nibble -> 6-bit value
dnib:
        .byte $00,$01,$00,$00,$02,$03,$00,$04,$05,$06,$00,$00,$00,$00,$00,$00
        .byte $07,$08,$00,$00,$00,$09,$0A,$0B,$0C,$0D,$00,$00,$0E,$0F,$10,$11
        .byte $12,$13,$00,$14,$15,$16,$17,$18,$19,$1A,$00,$00,$00,$00,$00,$00
        .byte $00,$00,$00,$00,$00,$1B,$00,$1C,$1D,$1E,$00,$00,$00,$1F,$00,$00
        .byte $20,$21,$00,$22,$23,$24,$25,$26,$27,$28,$00,$00,$00,$00,$00,$29
        .byte $2A,$2B,$00,$2C,$2D,$2E,$2F,$30,$31,$32,$00,$00,$33,$34,$35,$36
        .byte $37,$38,$00,$39,$3A,$3B,$3C,$3D,$3E,$3F
