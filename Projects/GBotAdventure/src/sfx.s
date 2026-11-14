; Speaker sound effects (included in the LCHI segment, $E000+ language card).
;
; The main loop ends every frame with a fixed ~3,000-cycle throttle. sfx_frame
; spends exactly that slot: silent, it is the old WAIT; with an effect playing
; it is one 3 ms tone "unit" of the current note, so the frame rate does not
; change. An effect is a list of notes (half-period P, units F), P=0 a rest,
; F=0 the end. Longer jingles (sfx_jingle) play their whole list at once and
; are used only where the game is already paused (a repair finishing, the fuse
; reload, the scientist starting to talk).
;
; Pitch: one click every P passes of a 27-cycle loop: ~18,500/P Hz.
SFX_BUZZ=1
SFX_CHIME=2
SFX_WARBLE=3
SFX_CLICK=4
SFX_GUARD=5
SFX_CHORD=6
SFX_OPEN=7
SFX_CRACKLE=8
SFX_ONLINE=9
SFX_RISE=10
SFX_HUM=11
UNIT_PASSES=110                ; 110 x 27 cycles ~ the 3,005-cycle throttle
CRACKLE_GAP=160                ; frames (~12 s) between scientist crackles

; Per-frame slot (replaces "lda #32 / jsr wait").
sfx_frame:
        lda CRACKT
        beq :+
        dec CRACKT
:       lda SFXLEFT
        bne @play
        lda SOUNDOFF           ; idle: a soft footstep tick every 8th frame
        bne @wait              ; while walking
        lda MOVING
        beq @wait
        lda CLOCK
        and #7
        bne @wait
        lda $C030
        nop
        nop
        lda $C030
        lda #2
        jsr spk_add
@wait:  lda #32
        jmp wait
@play:  jsr sfx_unit
        dec SFXLEFT
        bne :+
        jmp sfx_note
:       rts

; Start effect A in the slot. One already playing keeps going and this one
; follows it (latest wins). Off: nothing.
sfx_start:
        ldx SOUNDOFF
        bne @rts
        ldx SFXLEFT
        beq sfx_begin
        sta SFXNEXT
@rts:   rts
sfx_begin:
        sta SFXLAST
        tax
        lda sfxlo-1,x
        sta SFXPTR
        lda sfxhi-1,x
        sta SFXPTR+1
; Load the next note; at the end, start the queued effect, if any.
sfx_note:
        ldy #1
        lda (SFXPTR),y
        sta SFXLEFT
        beq @end
        dey
        lda (SFXPTR),y
        sta SFXPER
        sta TCNT
        lda SFXPTR
        clc
        adc #2
        sta SFXPTR
        bcc :+
        inc SFXPTR+1
:       rts
@end:   lda SFXNEXT
        beq :-
        ldx #0
        stx SFXNEXT
        beq sfx_begin

; Play effect A to the end now (only at a pause). Counts in JINGLES. Keeps X, Y.
sfx_jingle:
        sta TOGV
        lda SOUNDOFF
        bne @off
        txa
        pha
        tya
        pha
        inc JINGLES
        lda #0
        sta SFXNEXT
        lda TOGV
        jsr sfx_begin
@unit:  lda SFXLEFT
        beq @done
        jsr sfx_unit
        dec SFXLEFT
        bne @unit
        jsr sfx_note
        jmp @unit
@done:  pla
        tay
        pla
        tax
@off:   rts

; A status message first shows: its sound, if it has one (msgsfx, generated).
msg_sfx:
        cmp SFXMSG
        beq @rts
        sta SFXMSG
        cmp #MSG_COUNT         ; (the tuning meter lines are $80+)
        bcs @rts
        tax
        lda msgsfx,x
        beq @rts
        bpl sfx_start
        and #$7F
        jmp sfx_jingle
@rts:   rts

; The scientist flickers in: a crackle, at most every CRACKLE_GAP frames.
sfx_crackle:
        lda CRACKT
        bne @rts
        lda #CRACKLE_GAP
        sta CRACKT
        txa
        pha
        lda #SFX_CRACKLE
        jsr sfx_start
        pla
        tax
@rts:   rts

; M: sound on/off. In: A = key. Out: C=1 (and the key used) when it was M;
; otherwise C=0 and A kept.
sound_key:
        pha
        and #$5F               ; M or m
        cmp #'M'
        beq :+
        pla
        clc
        rts
:       pla
        lda SOUNDOFF
        eor #1
        sta SOUNDOFF
        lda #0
        sta SFXLEFT            ; off silences anything playing
        sta SFXNEXT
        lda #SFX_CLICK         ; (on: a click to confirm)
        jsr sfx_start
        ldy ROOM               ; SOUND ON/OFF on the status line, unless a
        ldx jobx,y             ; repair, the tuning meter or dialogue owns it
        lda REPAIR,x
        cmp #2
        beq @quiet
        lda TALK
        bne @quiet
        lda ROOM
        cmp #3
        bne :+
        lda CONSOLE
        cmp #2
        beq @quiet
:       lda #SOUND_MSG
        clc
        adc SOUNDOFF
        sta MESSAGE
        lda #30
        sta FEEDBACK
@quiet: sec
        rts

; SPKCNT += A
spk_add:
        clc
        adc SPKCNT
        sta SPKCNT
        bcc :+
        inc SPKCNT+1
:       rts

; One ~3,000-cycle unit of SFXPER (0: the plain throttle wait). Both loop
; paths take 27 cycles so the pitch is steady.
sfx_unit:
        ldx SFXPER
        bne :+
        lda #32
        jmp wait
:       lda #0
        sta TOGV
        ldy #UNIT_PASSES
sfx_pass:
        dec TCNT               ; 5
        bne sfx_skip           ; 2 / 3
        lda $C030              ; 4  click
        inc TOGV               ; 5
        stx TCNT               ; 3
        jmp sfx_next           ; 3  = 22
sfx_skip:
        nop                    ; 8 + 14 = 22
        nop
        nop
        nop
        nop
        nop
        nop
sfx_next:
        dey                    ; 2
        bne sfx_pass           ; 3  = 27
        lda TOGV
        jmp spk_add
.assert >sfx_pass = >sfx_next, error, "sfx loop branch crosses a page"
.assert >sfx_skip = >(sfx_pass+4), error, "sfx loop branch crosses a page"

sfxlo:  .byte <fx_buzz,<fx_chime,<fx_warble,<fx_click,<fx_guard,<fx_chord
        .byte <fx_open,<fx_crackle,<fx_online,<fx_rise,<fx_hum
sfxhi:  .byte >fx_buzz,>fx_chime,>fx_warble,>fx_click,>fx_guard,>fx_chord
        .byte >fx_open,>fx_crackle,>fx_online,>fx_rise,>fx_hum
; Notes: half-period, units (~3 ms each; in the slot one unit per frame).
fx_buzz:    .byte 24,1, 30,1, 24,1, 30,1, 0,0
fx_chime:   .byte 7,1, 5,1, 4,1, 4,1, 0,0
fx_warble:  .byte 11,1, 7,1, 11,1, 7,1, 11,1, 0,0
fx_click:   .byte 40,1, 0,0
fx_guard:   .byte 12,2, 0,1, 18,2, 0,1, 12,1, 0,0
fx_chord:   .byte 13,1, 10,1, 8,1, 6,2, 0,0
fx_open:    .byte 16,2, 12,2, 9,2, 6,3, 0,0
fx_crackle: .byte 3,1, 0,1, 8,1, 2,1, 0,0
fx_online:  .byte 60,8, 30,4, 13,2, 10,2, 8,2, 6,5, 0,0
fx_rise:    .byte 17,4, 13,4, 11,4, 8,8, 0,0
fx_hum:     .byte 70,6, 60,6, 35,6, 0,0
