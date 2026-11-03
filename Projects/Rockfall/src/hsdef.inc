; generated layout - high-score table defaults (44 bytes). Shared by rockfall.s (fallback) and
; boot.s (track 0 physical sector 15 on the disk = saved table).
;   5 entries x 8: initials (hi-ASCII), score lo, score hi (BCD), level (BCD), 0, 0
;   +$28 "RF", +$2A version 1, +$2B check byte: EOR of bytes $00-$2B must be 0
        .byte $C1,$B2,$C4,$50,$02,$04,$00,$00
        .byte $D2,$CF,$CD,$50,$01,$03,$00,$00
        .byte $C7,$D2,$CB,$00,$01,$02,$00,$00
        .byte $C8,$C7,$D2,$50,$00,$02,$00,$00
        .byte $D3,$D0,$CB,$25,$00,$01,$00,$00
        .byte $52,$46,$01,$C8
