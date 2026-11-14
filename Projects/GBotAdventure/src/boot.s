; G-Bot: After Hours -- read-only Disk II loader, derived from the workshop's
; Rockfall loader. NO write routine, score sector or game-specific persistence.
; The boot ROM loads T0 physical sectors 0..4 at $0800; the one-time boot code
; at $0C00 reads the code tracks to $6000 and moves them into the language
; card (bank 2), the stamp pool into bank 1, then the workshop, G-Bot's frames
; and the workshop aux track.
; The loader stays resident: the game calls LOADROOM ($0805) to stream one 8K
; room background (two whole tracks) into $8000 on a room transition, and
; LOADONE ($0808) for an aux track. Track numbers: layout.inc.
        .setcpu "6502"
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
LASTT=$48                        ; first track NOT to read
NREAD=$49
SFIRST=$4A                       ; sectors SFIRST..SEND-1 of each track are read
SEND=$4B
SPUN=$4C                         ; non-zero while the motor is already running
STEP=$4D                         ; seek acceleration index
RAWHI=$4E                        ; 8K raw-nibble area (a hidden HGR page)
DONE=$0D60
SH=$0E00                         ; decode tables built at boot: v<<2, and the
T0=$0E40                         ; three bit-reversed 2-bit fields of v
T1=$0E80
T2=$0EC0
GAME=$6000                       ; tracks 1-3 land here, then move to the
LCGAME=$D000                     ; language card ($D000-$FFFF, bank 2)
        .include "layout.inc"
        .export wait
        .segment "BOOT"
        .byte 5                  ; the boot ROM loads physical sectors 0-4
        jmp start
ntracks:.byte CODE_TRACKS        ; $0804: code tracks in the boot load
        jmp loadroom             ; $0805: LOADROOM entry used by the game
        jmp loadone              ; $0808: LOADONE, a single track (sectors SFIRST..SEND-1)
        jmp motoroff             ; $080B: MOTOROFF, after a door's last read
; NMI, RESET and IRQ/BRK vectors (LC RAM is mapped while the game runs)
vectors:.word vnmi,vreset,virq
; NMI, RESET and IRQ/BRK land here with LC RAM mapped: map the ROM back in
; (read ROM, write RAM bank 2) and continue through the ROM's own vector.
vnmi:   bit $C082
        jmp ($FFFA)
vreset: bit $C082
        jmp ($FFFC)
virq:   bit $C082
        jmp ($FFFE)


; readtracks: read tracks TRK..LASTT-1 (sectors SFIRST..SEND-1) into pages
; PAGE0.. (16 per track). Each track is read in about one revolution: sectors
; are stored as raw 6-bit values (RAWHI+s pages, then 86-byte secondaries at
; RAWHI+$10 + 86s) as they pass, and decoded together afterwards. (Decoding
; each sector before the next would miss the one right behind it, needing
; two revolutions.)
readtracks:
@track: lda TRK
        jsr seek
        ldy #15
@clear: lda #1                   ; sectors outside SFIRST..SEND-1 count as done
        cpy SFIRST
        bcc @set
        cpy SEND
        bcs @set
        lda #0
@set:   sta DONE,y
        dey
        bpl @clear
        lda SEND
        sec
        sbc SFIRST
        sta LEFT
@sector:jsr rdsect
        bcs @sector
        dec LEFT
        bne @sector
        jsr decode
        lda PAGE0
        clc
        adc #16
        sta PAGE0
        inc TRK
        lda TRK
        cmp LASTT
        bcc @track
        rts

; loadroom: A = first track, Y = destination page. Reads two whole tracks
; (8K); loadone reads sectors SFIRST..SEND-1 of one track to pages Y+sector.
; Read-only: motor on, drive 1, read mode. The motor keeps running between
; the reads of one door (one spin-up wait); MOTOROFF stops it afterwards.
loadroom:
        ldx #0
        stx SFIRST
        ldx #16
        stx SEND
        ldx #2
        bne loadn
loadone:ldx #1
loadn:  stx NREAD
        sta TRK
        sty PAGE0
        clc
        adc NREAD
        sta LASTT
        ldx SLOT
        lda $C089,x              ; motor on
        lda $C08A,x              ; drive 1
        lda $C08E,x              ; read mode (never write mode)
        lda SPUN
        bne @spun
        inc SPUN
        lda #$C0                 ; ~90 ms spin-up; bad reads simply retry
        jsr wait
@spun:  jmp readtracks
motoroff:
        ldx SLOT
        lda $C088,x              ; motor off
        lda #0
        sta SPUN
        rts

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
        tya                      ; aim rddata at this sector's raw buffers
        clc
        adc RAWHI
        sta n1op+2
        lda n2lo,y
        sec
        sbc #$AA                 ; rddata indexes secondaries with Y=$AA..$FF
        sta n2op+1
        lda n2hi,y
        sbc #0
        clc
        adc RAWHI
        sta n2op+2
        jsr rddata
        bcs @err
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
rd_s1:    dey
        beq rd_bad
rd_s2:    lda $C08C,x
        bpl rd_s2
rd_s3:    eor #$D5
        bne rd_s1
        nop
rd_s4:    lda $C08C,x
        bpl rd_s4
        cmp #$AA
        bne rd_s3
        nop
rd_s5:    lda $C08C,x
        bpl rd_s5
        cmp #$AD
        bne rd_s3
        ldy #$AA                 ; 86 secondaries, stored in arrival order
        lda #0
rd_n1:    sty IDX
rd_n2:    ldy $C08C,x
        bpl rd_n2
        eor dnib-$96,y
        ldy IDX
n2op:   sta $FFFF,y
        iny
        bne rd_n1
rd_n3:    sty IDX
rd_n4:    ldy $C08C,x
        bpl rd_n4
        eor dnib-$96,y
        ldy IDX
n1op:   sta $FF00,y
        iny
        bne rd_n3
rd_n5:    ldy $C08C,x
        bpl rd_n5
        cmp dnib-$96,y
        bne rd_bad
rd_n6:    lda $C08C,x
        bpl rd_n6
        cmp #$DE
        bne rd_bad
        clc
        rts
rd_bad:   sec
        rts

; ---- decode: raw sectors SFIRST..SEND-1 -> pages PAGE0+s (DOS 3.3 6+2:
; byte p*86+i = primary<<2 | bit-reversed field p of secondary 85-i).
decode: ldx SFIRST
@sec:   cpx SEND
        bcs @done
        stx IDX
        txa
        clc
        adc RAWHI
        sta @n1+2
        txa
        clc
        adc PAGE0
        sta @dst+2
        lda n2lo,x
        sta @n2+1
        lda n2hi,x
        clc
        adc RAWHI
        sta @n2+2
        ldy #2
@part:  lda partoff,y
        sta @n1+1
        sta @dst+1
        lda parttab,y
        sta @t+1
        lda partend,y
        sta @end+1
        sty CNT
        ldx #0
@byte:
@n2:    ldy $FFFF,x
@t:     lda T0,y
@n1:    ldy $FF00,x
        ora SH,y
@dst:   sta $FF00,x
        inx
@end:   cpx #86
        bne @byte
        ldy CNT
        dey
        bpl @part
        ldx IDX
        inx
        bne @sec
@done:  ldx SLOT
        rts
partoff:.byte 0,86,172
partend:.byte 86,86,84
parttab:.byte <T0,<T1,<T2
rev2:   .byte 0,2,1,3
n2lo:
.repeat 16,S
        .byte <($1000+S*86)
.endrepeat
n2hi:
.repeat 16,S
        .byte >($1000+S*86)
.endrepeat

; ---- seek: move head to track A by phase stepping (2 phases per track).
; Like DOS: energise the current phase first, then for each half-track step
; turn the next phase on, wait ~19 ms, turn the previous phase off; finally
; settle ~19 ms and release the last phase. Like DOS the steps accelerate:
; ~19 ms for the first half-track, then 11, 7.5, 6 and ~5.4 ms each.
seek:   asl a
        sta TMP                  ; target half-track
        lda #0
        sta STEP
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
        ldy STEP
        lda steptime,y
        jsr wait
        cpy #4
        bcs :+
        inc STEP
:
        pla
        jsr phoff                ; previous phase off
        jmp @s0
@done:  lda #$56                 ; settle
        jsr wait
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

; wait: the monitor's WAIT ($FCA8) byte for byte, so delays are unchanged
; while the ROM is switched out. Its branches must not cross a page.
wait:   sec
@w2:    pha
@w3:    sbc #1
        bne @w3
        pla
        sbc #1
        bne @w2
        rts
.assert >wait = >(*-1), error, "wait crosses a page: its timing would change"
steptime: .byte $56,$40,$34,$2E,$2C   ; WAIT values per half-track step

        .segment "BOOT2"         ; $0C00: run once at boot (later the stamp
                                 ; interpreter's text buffer)
start:  cld
        sei                      ; (no IRQ source; the vectors change below)
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
        sta SFIRST
        sta SPUN
        lda #16
        sta SEND
        lda #$20                 ; raw nibbles go to HGR page 1 while booting
        sta RAWHI
        ldx #63
@tab:   txa
        asl a
        asl a
        sta SH,x
        txa
        and #3
        tay
        lda rev2,y
        sta T0,x
        txa
        lsr a
        lsr a
        and #3
        tay
        lda rev2,y
        sta T1,x
        txa
        lsr a
        lsr a
        lsr a
        lsr a
        tay
        lda rev2,y
        sta T2,x
        dex
        bpl @tab
        lda #1                   ; code and tables: tracks 1-3 -> $6000-$8FFF
        ldx #CODE_TRACKS
        ldy #>GAME
        jsr bootread
        ; Language card: read and write RAM, bank 2 (two reads of $C083), for
        ; good. The game's 12K of code and tables move from $6000 to $D000;
        ; $6000-$7FFF is free from here on. Nothing calls the ROM after this:
        ; WAIT has a RAM copy below, and the vectors bounce to the ROM's own.
        bit $C083
        bit $C083
        ldy #0
        ldx #CODE_TRACKS*16
@lc:    lda GAME,y
@lcd:   sta LCGAME,y
        iny
        bne @lc
        inc @lc+2
        inc @lcd+2
        dex
        bne @lc
        ldx #5
@vec:   lda vectors,x
        sta $FFFA,x
        dex
        bpl @vec
        lda #POOL_TRACK          ; the stamp pool -> $6000, then LC bank 1
        ldx #1
        ldy #>GAME
        jsr bootread
        bit $C08B                ; read and write RAM, bank 1
        bit $C08B
        ldy #0
        ldx #16
@pool:  lda GAME,y
@poold: sta LCGAME,y
        iny
        bne @pool
        inc @pool+2
        inc @poold+2
        dex
        bne @pool
        bit $C083                ; bank 2 (the game's code) for good
        bit $C083
        lda #WORKSHOP_TRACK      ; workshop room and G-Bot's frames -> $8000-$BFFF
        ldx #4
        ldy #$80
        jsr bootread
        lda #WORKAUX_TRACK       ; workshop aux track (messages) -> $1000-$1FFF
        ldx #1
        ldy #$10
        jsr bootread
        ldx SLOT
        jmp LCGAME
bootread:                        ; A = first track, X = tracks, Y = first page
        sta TRK
        sty PAGE0
        stx LASTT
        clc
        adc LASTT
        sta LASTT
        jmp readtracks
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
