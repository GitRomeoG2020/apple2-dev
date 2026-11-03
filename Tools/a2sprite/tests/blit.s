        .segment "CODE"
        jmp blit
; a2sprite export: face
; size: 2 bytes (14 px) x 7 rows, 14 bytes
; byte layout: bit0 = leftmost pixel, bit7 = palette (0=violet/green, 1=blue/orange)
FACE_W = 2
FACE_H = 7

face:
        .byte $40,$0F   ; row 0
        .byte $20,$10   ; row 1
        .byte $20,$15   ; row 2
        .byte $20,$10   ; row 3
        .byte $20,$17   ; row 4
        .byte $20,$10   ; row 5
        .byte $40,$0F   ; row 6

; AND mask: screen = (screen AND mask) OR sprite
face_mask:
        .byte $3F,$70   ; row 0
        .byte $5F,$6F   ; row 1
        .byte $5F,$6A   ; row 2
        .byte $5F,$6F   ; row 3
        .byte $5F,$68   ; row 4
        .byte $5F,$6F   ; row 5
        .byte $3F,$70   ; row 6

; 7 pre-shifted copies, 3 bytes per row
FACE_SW = 3

; shift 0
face_s0:
        .byte $40,$0F,$00   ; row 0
        .byte $20,$10,$00   ; row 1
        .byte $20,$15,$00   ; row 2
        .byte $20,$10,$00   ; row 3
        .byte $20,$17,$00   ; row 4
        .byte $20,$10,$00   ; row 5
        .byte $40,$0F,$00   ; row 6
face_s0_mask:
        .byte $3F,$70,$FF   ; row 0
        .byte $5F,$6F,$FF   ; row 1
        .byte $5F,$6A,$FF   ; row 2
        .byte $5F,$6F,$FF   ; row 3
        .byte $5F,$68,$FF   ; row 4
        .byte $5F,$6F,$FF   ; row 5
        .byte $3F,$70,$FF   ; row 6

; shift 1
face_s1:
        .byte $00,$1F,$00   ; row 0
        .byte $40,$20,$00   ; row 1
        .byte $40,$2A,$00   ; row 2
        .byte $40,$20,$00   ; row 3
        .byte $40,$2E,$00   ; row 4
        .byte $40,$20,$00   ; row 5
        .byte $00,$1F,$00   ; row 6
face_s1_mask:
        .byte $FF,$60,$FF   ; row 0
        .byte $3F,$5F,$FF   ; row 1
        .byte $3F,$55,$FF   ; row 2
        .byte $3F,$5F,$FF   ; row 3
        .byte $3F,$51,$FF   ; row 4
        .byte $3F,$5F,$FF   ; row 5
        .byte $FF,$60,$FF   ; row 6

; shift 2
face_s2:
        .byte $00,$3E,$00   ; row 0
        .byte $00,$41,$00   ; row 1
        .byte $00,$55,$00   ; row 2
        .byte $00,$41,$00   ; row 3
        .byte $00,$5D,$00   ; row 4
        .byte $00,$41,$00   ; row 5
        .byte $00,$3E,$00   ; row 6
face_s2_mask:
        .byte $FF,$41,$FF   ; row 0
        .byte $FF,$3E,$FF   ; row 1
        .byte $FF,$2A,$FF   ; row 2
        .byte $FF,$3E,$FF   ; row 3
        .byte $FF,$22,$FF   ; row 4
        .byte $FF,$3E,$FF   ; row 5
        .byte $FF,$41,$FF   ; row 6

; shift 3
face_s3:
        .byte $00,$7C,$00   ; row 0
        .byte $00,$02,$01   ; row 1
        .byte $00,$2A,$01   ; row 2
        .byte $00,$02,$01   ; row 3
        .byte $00,$3A,$01   ; row 4
        .byte $00,$02,$01   ; row 5
        .byte $00,$7C,$00   ; row 6
face_s3_mask:
        .byte $FF,$03,$FF   ; row 0
        .byte $FF,$7D,$7E   ; row 1
        .byte $FF,$55,$7E   ; row 2
        .byte $FF,$7D,$7E   ; row 3
        .byte $FF,$45,$7E   ; row 4
        .byte $FF,$7D,$7E   ; row 5
        .byte $FF,$03,$FF   ; row 6

; shift 4
face_s4:
        .byte $00,$78,$01   ; row 0
        .byte $00,$04,$02   ; row 1
        .byte $00,$54,$02   ; row 2
        .byte $00,$04,$02   ; row 3
        .byte $00,$74,$02   ; row 4
        .byte $00,$04,$02   ; row 5
        .byte $00,$78,$01   ; row 6
face_s4_mask:
        .byte $FF,$07,$7E   ; row 0
        .byte $FF,$7B,$7D   ; row 1
        .byte $FF,$2B,$7D   ; row 2
        .byte $FF,$7B,$7D   ; row 3
        .byte $FF,$0B,$7D   ; row 4
        .byte $FF,$7B,$7D   ; row 5
        .byte $FF,$07,$7E   ; row 6

; shift 5
face_s5:
        .byte $00,$70,$03   ; row 0
        .byte $00,$08,$04   ; row 1
        .byte $00,$28,$05   ; row 2
        .byte $00,$08,$04   ; row 3
        .byte $00,$68,$05   ; row 4
        .byte $00,$08,$04   ; row 5
        .byte $00,$70,$03   ; row 6
face_s5_mask:
        .byte $FF,$0F,$7C   ; row 0
        .byte $FF,$77,$7B   ; row 1
        .byte $FF,$57,$7A   ; row 2
        .byte $FF,$77,$7B   ; row 3
        .byte $FF,$17,$7A   ; row 4
        .byte $FF,$77,$7B   ; row 5
        .byte $FF,$0F,$7C   ; row 6

; shift 6
face_s6:
        .byte $00,$60,$07   ; row 0
        .byte $00,$10,$08   ; row 1
        .byte $00,$50,$0A   ; row 2
        .byte $00,$10,$08   ; row 3
        .byte $00,$50,$0B   ; row 4
        .byte $00,$10,$08   ; row 5
        .byte $00,$60,$07   ; row 6
face_s6_mask:
        .byte $FF,$1F,$78   ; row 0
        .byte $FF,$6F,$77   ; row 1
        .byte $FF,$2F,$75   ; row 2
        .byte $FF,$6F,$77   ; row 3
        .byte $FF,$2F,$74   ; row 4
        .byte $FF,$6F,$77   ; row 5
        .byte $FF,$1F,$78   ; row 6

face_shift_lo: .byte <face_s0,<face_s1,<face_s2,<face_s3,<face_s4,<face_s5,<face_s6
face_shift_hi: .byte >face_s0,>face_s1,>face_s2,>face_s3,>face_s4,>face_s5,>face_s6

; blit face_s3 (3 bytes wide x 7 rows) to HGR page 1 at row Y0, byte column COL using (screen AND mask) OR data
Y0=40
COL=10
ptr=$06
src=$08
msk=$FA
        .segment "CODE"
blit:   ldx #0
@row:   lda rowlo,x
        sta ptr
        lda rowhi,x
        sta ptr+1
        ldy #0
@col:   stx $FC
        txa
        asl
        adc $FC         ; x*3
        sta $FD
        tya
        clc
        adc $FD
        sta $FE
        ldx $FE
        lda (ptr),y
        and face_s3_mask,x
        ora face_s3,x
        sta (ptr),y
        ldx $FC
        iny
        cpy #3
        bne @col
        inx
        cpx #7
        bne @row
        rts
rowlo: .byte $8A,$8A,$8A,$8A,$8A,$8A,$8A
rowhi: .byte $22,$26,$2A,$2E,$32,$36,$3A
