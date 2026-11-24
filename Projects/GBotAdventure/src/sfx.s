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
SFX_CUTOFF=12                  ; "IT RUNS AGAIN-": the reveal, cut off mid-note
SFX_MOTIF0=13                  ; room motifs 13-17 (workshop, power, security, lab, substation)
SFX_SURGE=18                   ; full power: the rising surge and a big chord
SFX_ZAP=19                     ; a strobe crackle
SFX_REWIND=20                  ; waking in the workshop again: a sad trombone
SFX_UNSTICK=21                 ; the trickle lead: tick... tock... chime
SFX_HOOK=22                    ; TO BE CONTINUED
SFX_TICK=23                    ; a carried minute: tick... tock
SFX_MOTIFW=24                  ; wing B's motif (room_tune maps room 5 to it)
SFX_PLIP=25                    ; the coffee drop lands (chapter.s)
; Note half-periods: ~18,500 / f passes.
NC4=71
NE4=56
NG4=47
NA4=42
NB4=37
NC5=35
ND5=32
NE5=28
NFS5=25
NG5=24
NGS5=22
NA5=21
NC6=18
NE6=14
NG6=12
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
        cmp #MSG_COUNT         ; (the tuning meter lines are $80+; the
        bcc :+                 ;  chapter's $B0 up have their own table)
        jmp ch_sfx
:
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
        .byte <fx_open,<fx_crackle,<fx_online,<fx_rise,<fx_hum,<fx_cutoff
        .byte <tune_workshop,<tune_power,<tune_security,<tune_lab,<tune_sub
        .byte <fx_surge,<fx_zap,<fx_rewind,<fx_unstick,<fx_hook,<fx_tick,<tune_wingb,<fx_plip
sfxhi:  .byte >fx_buzz,>fx_chime,>fx_warble,>fx_click,>fx_guard,>fx_chord
        .byte >fx_open,>fx_crackle,>fx_online,>fx_rise,>fx_hum,>fx_cutoff
        .byte >tune_workshop,>tune_power,>tune_security,>tune_lab,>tune_sub
        .byte >fx_surge,>fx_zap,>fx_rewind,>fx_unstick,>fx_hook,>fx_tick,>tune_wingb,>fx_plip
; Notes: half-period, units (~3 ms each; in the slot one unit per frame).
fx_buzz:    .byte 24,1, 30,1, 24,1, 30,1, 0,0
fx_chime:   .byte 7,1, 5,1, 4,1, 4,1, 0,0
fx_warble:  .byte 11,1, 7,1, 11,1, 7,1, 11,1, 0,0
fx_click:   .byte 40,1, 0,0
fx_guard:   .byte 12,2, 0,1, 18,2, 0,1, 12,1, 0,0
fx_chord:   .byte 13,1, 10,1, 8,1, 6,2, 0,0
; Lab door unlocked (blocking, ~0.4 s: the whole room holds for it).
fx_open:    .byte 60,6, 0,10, NE5,18, NG5,18, NC6,18, NE6,60, 0,0
fx_crackle: .byte 3,1, 0,1, 8,1, 2,1, 0,0
; Console in phase: power hum, then a fanfare (~1.1 s; dialogue starts).
fx_online:  .byte NC4,30, NG4,30, 0,10
            .byte NC5,24, 0,6, NC5,12, 0,4, NC5,12, 0,4, NG5,60, 0,10
            .byte NE5,30, 0,4, NG5,30, 0,4, NC6,110, 0,0
; Workbench repaired: "fixed it!" (~0.7 s, G-Bot is still holding).
fx_rise:    .byte NG5,20, 0,4, NC6,20, 0,4, NE6,30, 0,8
            .byte NC6,16, 0,4, NE6,30, 0,4, NG6,100, 0,0
fx_hum:     .byte 70,6, 60,6, 35,6, 0,0
; "IT RUNS AGAIN-": a slow climb that is cut off mid-note by a crackle.
fx_cutoff:  .byte NA4,40, 0,6, NC5,40, 0,6, NE5,40, 0,6, NA5,40, 0,6
            .byte NC6,60, 3,2, 0,1, 8,1, 2,2, 0,0
; Room motifs (~0.4-0.5 s), earnest and a little playful.
tune_workshop:                 ; tinkering: up the C chord and a hop
            .byte NC5,26, 0,4, NE5,26, 0,4, NG5,26, 0,4, NE5,18, 0,4, NC6,36, 0,0
tune_power: .byte NG4,28, 0,4, NB4,28, 0,4, ND5,28, 0,4, NG5,50, 0,0   ; warming up
tune_security:                 ; tiptoe past the guard
            .byte NE5,14, 0,14, NE5,14, 0,10, NG5,24, 0,8, NE5,14, 0,6, ND5,40, 0,0
tune_lab:   .byte NC5,24, 0,3, ND5,24, 0,3, NE5,24, 0,3, NFS5,24, 0,3, NGS5,42, 0,0 ; wonder

; A door: maybe a motif for the room being entered. Always on the first-ever
; entry, otherwise 1 in 2; half the time the room's own motif, otherwise any
; of the four. Played (whole, before the read) in place of the door chirp and
; the motor spin-up wait. Sets TUNED when one played. Off: none (the room
; still counts as visited).
room_tune:
        lda #0
        sta TUNED
        lda WAKE               ; waking from a rerun: the rewind, not a motif
        beq :+
        lda SOUNDOFF
        bne @rts
        lda #SFX_REWIND
        jsr sfx_jingle
        inc TUNED
@rts:   rts
:
        lda SEED               ; 8-bit LFSR (x^8+x^4+x^3+x^2+1), mixed with the
        bne :+                 ; frame counter: the player's timing decides
        lda #$5A
:       asl a
        bcc :+
        eor #$1D
:       sta SEED
        eor TICKS
        sta TUNERND
        ldx NEXTROOM
        lda roombit,x
        bit VISITED
        php
        ora VISITED
        sta VISITED
        plp
        beq @play              ; first time in: always
        lda TUNERND
        bpl @play              ; 1 in 2: none
        rts
@play:  lda TUNERND
        and #$40
        beq :+                 ; the room's own...
        lda TUNERND
        and #3                 ; ...or any of the four
        tax
:       lda motifof,x          ; (wing B's own motif sits after the story sounds)
; Play motif A (0-4, or 11 for wing B) now. Off: nothing.
play_motif:
        ldx SOUNDOFF
        bne @rts
        sta TUNELAST
        inc TUNES
        inc TUNED
        clc
        adc #SFX_MOTIF0
        jmp sfx_jingle
@rts:   rts
roombit:    .byte 1,2,4,8,16,32
motifof:    .byte 0,1,2,3,4,SFX_MOTIFW-SFX_MOTIF0
tune_sub:   .byte NG4,20, 0,4, NG4,20, 0,4, NC5,20, 0,4, NB4,20, 0,4, NG4,46, 0,0  ; the big switch hums
; Full power: a whine climbing to a big chord (~0.45 s).
fx_surge:   .byte 60,2, 54,2, 48,2, 42,2, 37,2, 32,2, 28,2, 24,2, 21,2, 18,2, 15,2, 13,2, 11,2, 9,2
            .byte NC5,12, NE5,12, NG5,12, NC6,60, 0,0
fx_zap:     .byte 3,1, 9,1, 2,1, 6,1, 0,0
; Waking in the workshop again: wah, wah, wah, waaah (~0.6 s).
fx_rewind:  .byte NA4,36, 0,6, 44,36, 0,6, NG4,36, 0,6, 50,24, 52,6, 50,6, 52,6, 50,6, 52,6, 50,20, 0,0
; The trickle lead: the ring ticks once, then a little chime of hope (~0.6 s).
fx_unstick: .byte 3,2, 0,40, 4,2, 0,40, NC6,20, NE6,20, NG6,60, 0,0
; TO BE CONTINUED: a hopeful, unfinished phrase (~0.8 s).
fx_hook:    .byte NC5,24, 0,4, NE5,24, 0,4, NG5,24, 0,4, NA5,40, 0,8, NG5,24, 0,4, ND5,90, 0,0
; A carried minute: tick... tock (~0.25 s).
fx_tick:    .byte 3,2, 0,30, 5,2, 0,30, 0,0
; Wing B: the archive, stopped mid-sip (~0.5 s).
tune_wingb: .byte NE5,26, 0,4, NE5,26, 0,4, ND5,26, 0,4, NC5,26, 0,10, NG4,40, 0,0
