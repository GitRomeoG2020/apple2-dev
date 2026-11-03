; store.s - writes 'A' 'B' 'C' to $0300-$0302, then $42 to $0303 as a "done" flag
; Build: cl65 -t none --start-addr $6000 -o store.bin store.s  (Run-Apple2.ps1 -Asm does this)
start:  ldx #0
loop:   txa
        clc
        adc #$C1            ; 'A' with high bit set
        sta $0300,x
        inx
        cpx #3
        bne loop
        lda #$42
        sta $0303           ; done flag
        rts                 ; back to BASIC
