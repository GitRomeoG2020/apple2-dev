; G-Bot: After Hours -- first playable workshop. Plain NMOS 6502 / 48K.
; HGR pages $2000/$4000, immutable room $8000, masked frames $A000.
; Only the offscreen page's old 7x44 rectangle is restored, then composited.
; All horizontal positions are even: artifact-color parity never reverses.
        .setcpu "6502"
SRC=$50
DST=$52
BG=$54
FP=$56
MP=$58
DP=$5A
SL=$5C
SH=$5E
ROW=$60
COL=$61
CM=$62
CD=$63
RAW=$64
BITS=$65
PHASE=$66
OX=$67
OY=$68
TMPX=$69
TMPY=$6A
PAGEHI=$6B
PX=$70
PY=$71
DIR=$72                       ; 0 south, 1 west, 2 east, 3 north
BURST=$73                     ; bounded four-tick walk per keyboard event
WALK=$74
CLOCK=$75
PAGE=$76                      ; page currently being prepared: 0=$2000, 1=$4000
FRAME=$77
XB=$78
SHIFT=$79
OLDX=$7A                      ; two pairs x-byte,y (one per HGR page)
OLDY=$7B
PROBE=$7E
READY=$7F
MOVING=$80
TICKS=$81                     ; 16-bit completed-frame counter, test visibility
MASKBUF=$1200                 ; 308 shifted opacity bytes (not inverse masks)
DATABUF=$1000                 ; 308 shifted pixels
PHASEBUF=$1400                ; 44 phase bytes

        .export entry, main, code_end
        .segment "CODE"
entry:  cld
        sei
        ldx $2B
        lda $C088,x            ; motor off. No subsequent disk I/O, ever.
        bit $C051              ; hide setup in text mode
        lda #0
        ldx #$32
@state: sta $50,x
        dex
        bpl @state
        lda #126
        sta PX
        lda #104
        sta PY
        sta OLDY
        sta OLDY+2
        lda #18
        sta OLDX
        sta OLDX+2
        ; Copy all 8K, including HGR holes, into both display pages.
        lda #$80
        sta SRC+1
        lda #$20
        sta DST+1
        lda #0
        sta SRC
        sta DST
        ldx #32
@page:  ldy #0
@copy:  lda (SRC),y
        sta (DST),y
        iny
        bne @copy
        inc SRC+1
        inc DST+1
        dex
        bne @page
        lda #$80
        sta SRC+1
        lda #$40
        sta DST+1
        ldx #32
@page2: ldy #0
@copy2: lda (SRC),y
        sta (DST),y
        iny
        bne @copy2
        inc SRC+1
        inc DST+1
        dex
        bne @page2
        ; Render both initial images before showing graphics.
        jsr prepare
        jsr render
        inc PAGE
        jsr render
        lda #0
        sta PAGE
        bit $C010
        bit $C054
        bit $C057
        bit $C052              ; full HGR; instructions are native HGR pixels
        bit $C050
        lda #$A5
        sta READY
main:   lda PAGE
        eor #1
        sta PAGE
        jsr keyboard
        jsr update
        jsr prepare
        jsr render
        ldx PAGE
        lda $C054,x            ; publish only the completed page
        inc CLOCK
        inc TICKS
        bne :+
        inc TICKS+1
:       lda #32
        jsr $FCA8              ; small fixed throttle; no IIe-only VBL dependency
        jmp main

keyboard:
        lda $C000
        bpl @done
        bit $C010
        and #$7F
        cmp #$20
        beq @probe
        and #$DF               ; accepts lower-case WASD on IIe
        ldx #0
        cmp #'S'
        beq @walk
        cmp #$0A
        beq @walk
        inx
        cmp #'A'
        beq @walk
        cmp #$08
        beq @walk
        inx
        cmp #'D'
        beq @walk
        cmp #$15
        beq @walk
        inx
        cmp #'W'
        beq @walk
        cmp #$0B
        bne @done
@walk:  stx DIR
        lda #4
        sta BURST
        lda #0
        sta PROBE
        rts
@probe: lda #8
        sta PROBE
        lda #0
        sta BURST
        sta DIR
@done:  rts

update: lda #0
        sta MOVING
        lda PROBE
        beq @move
        dec PROBE
        rts
@move:  lda BURST
        beq @done
        dec BURST
        lda PX
        sta TMPX
        lda PY
        sta TMPY
        ldx DIR
        lda PX
        clc
        adc dx,x
        sta PX
        lda PY
        clc
        adc dy,x
        sta PY
        ; Footprint vs. room walls, then two pieces of solid furniture.
        lda PX
        cmp #14
        bcc @blocked
        cmp #225
        bcs @blocked
        lda PY
        cmp #48
        bcc @blocked
        cmp #115
        bcs @blocked
        lda PX
        cmp #86
        bcs @right
        lda PY
        cmp #64
        bcc @blocked           ; left bench front is y=106
@right: lda PX
        cmp #192
        bcc @allowed
        lda PY
        cmp #70
        bcc @blocked           ; terminal front is y=112
@allowed:
        inc WALK
        lda #1
        sta MOVING
@done:  rts
@blocked:
        lda TMPX
        sta PX
        lda TMPY
        sta PY
        lda #0
        sta BURST
        rts

; Pick an expressive pose and construct the 7-byte-wide shifted sprite.
prepare:
        ldx DIR
        lda baseframe,x
        sta FRAME
        lda PROBE
        beq @walk
        lda #13
        bne @set
@walk:  lda MOVING
        beq @idle
        lda WALK
        lsr a
        and #1
        clc
        adc FRAME
        adc #1
        bne @set
@idle:  lda DIR
        bne @chosen
        lda CLOCK
        and #127
        cmp #124
        bcc @chosen
        lda #12
@set:   sta FRAME
@chosen:
        ldx FRAME
        lda framelo,x
        sta FP
        lda framehi,x
        sta FP+1
        lda PX
        ldx #0
@div7:  cmp #7
        bcc @rem
        sec
        sbc #7
        inx
        bne @div7
@rem:   sta SHIFT
        stx XB
        tax
        lda shiftlo,x
        sta SL
        sta SH
        lda shiftpage,x
        sta SL+1
        clc
        adc #>carry_table->left_table
        sta SH+1
        lda #<MASKBUF
        sta MP
        lda #>MASKBUF
        sta MP+1
        lda #<DATABUF
        sta DP
        lda #>DATABUF
        sta DP+1
        lda #0
        sta ROW
@row:   ldy #12
        lda (FP),y
        ldx ROW
        sta PHASEBUF,x
        lda #0
        sta CM
        sta CD
        sta COL
@byte:  ldy COL
        lda (FP),y
        sta RAW
        tay
        lda (SL),y
        ora CM
        sta BITS
        lda (SH),y
        sta CM
        ldy COL
        lda BITS
        sta (MP),y
        tya
        clc
        adc #6
        tay
        lda (FP),y
        tay
        lda (SL),y
        ora CD
        sta BITS
        lda (SH),y
        sta CD
        ldy COL
        lda BITS
        sta (DP),y
        inc COL
        lda COL
        cmp #6
        bne @byte
        ldy #6
        lda CM
        sta (MP),y
        lda CD
        sta (DP),y
        clc
        lda FP
        adc #13
        sta FP
        bcc :+
        inc FP+1
:       jsr advance_buffers
        inc ROW
        lda ROW
        cmp #44
        bne @row
        rts

; Both restore and blit use row lookup tables, never redraw room furniture.
render: ldx PAGE
        lda pagehigh,x
        sta PAGEHI
        txa
        asl a
        tax
        lda OLDX,x
        sta OX
        lda OLDY,x
        sta OY
        lda #0
        sta ROW
@restore:
        lda OY
        clc
        adc ROW
        tax
        jsr row_pointers
        ldy #6
@copy:  lda (BG),y
        sta (DST),y
        dey
        bpl @copy
        inc ROW
        lda ROW
        cmp #44
        bne @restore
        lda XB
        sta OX
        lda PY
        sta OY
        ldx PAGE
        txa
        asl a
        tax
        lda OX
        sta OLDX,x
        lda OY
        sta OLDY,x
        lda #<MASKBUF
        sta MP
        lda #>MASKBUF
        sta MP+1
        lda #<DATABUF
        sta DP
        lda #>DATABUF
        sta DP+1
        lda #0
        sta ROW
@blit:  lda OY
        clc
        adc ROW
        tax
        jsr row_pointers
        ldx ROW
        lda PHASEBUF,x
        sta PHASE
        ldy #6
@pixel: lda (MP),y
        beq @transparent       ; fully transparent byte preserves palette bit
        eor #$FF
        and (BG),y
        and #$7F
        ora (DP),y
        ora PHASE
        sta (DST),y
        jmp @next
@transparent:
        lda (BG),y             ; spill column can differ from last dirty rect
        sta (DST),y
@next:  dey
        bpl @pixel
        jsr advance_buffers
        inc ROW
        lda ROW
        cmp #44
        bne @blit
        rts

row_pointers:
        lda rowlo,x
        clc
        adc OX
        sta BG
        sta DST
        lda rowhi,x
        adc #0
        ora #$80
        sta BG+1
        lda rowhi,x            ; 40-column rows never cross a page with OX<=32
        ora PAGEHI
        sta DST+1
        rts
advance_buffers:
        clc
        lda MP
        adc #7
        sta MP
        bcc :+
        inc MP+1
:       clc
        lda DP
        adc #7
        sta DP
        bcc :+
        inc DP+1
:       rts

        .segment "RODATA"
dx: .byte 0,254,2,0
dy: .byte 2,0,0,254
baseframe: .byte 0,3,6,9
pagehigh: .byte $20,$40
framelo:
.repeat 14,I
 .byte <(sprite_frames+I*572)
.endrepeat
framehi:
.repeat 14,I
 .byte >(sprite_frames+I*572)
.endrepeat
rowlo:
.repeat 192,YY
 .byte <(((YY&7)*$400)+(((YY>>3)&7)*$80)+(YY/64)*40)
.endrepeat
rowhi:
.repeat 192,YY
 .byte >(((YY&7)*$400)+(((YY>>3)&7)*$80)+(YY/64)*40)
.endrepeat
shiftlo:
.repeat 7,S
 .byte <(left_table+S*128)
.endrepeat
shiftpage:
.repeat 7,S
 .byte >(left_table+S*128)
.endrepeat
.align 256
left_table:
.repeat 7,S
 .repeat 128,V
  .byte (V<<S)&127
 .endrepeat
.endrepeat
; Keep the carry table at an integer number of pages after the left table.
.align 256
carry_table:
.repeat 7,S
 .repeat 128,V
  .byte (V<<S)>>7
 .endrepeat
.endrepeat
code_end:
.assert code_end <= $8000, lderror, "Code/table overflow into room"
        .segment "BACKGROUND"
room: .incbin "../art/workshop-room.hgr"
        .segment "SPRITES"
sprite_frames: .incbin "../art/gbot-sprites.bin"
sprites_end:
.assert sprites_end <= $C000, lderror, "Sprites overflow 48K RAM"
