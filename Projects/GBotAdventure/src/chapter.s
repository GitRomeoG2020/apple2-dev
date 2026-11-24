; The second minute, and the scientist's notes (track 13, read at boot to
; $6000; main RAM the game does not otherwise use). The chapter bank first
; (the story bank links on to it), then the code and the room patches.
;
; Waking the guard jolts security's monitor wall into snow. Probing the desk
; finds a loose cable: R reconnects it (the workshop's repair, and its
; jingle), the guard can see again, and the chamber recharges. The chamber
; then charges G-Bot with a second minute (MINUTE 3). In wing B it wakes the
; coffee machine (MINUTE 4): the frozen drop falls, the machine grumbles, and
; hands over the first page of the scientist's notebook (PAGES).
; A rerun resets the night (MINUTE 0, the drop frozen again); repairs and the
; page stay with G-Bot, and the coffee remembers him.
MSG_EMPTY=$B0
MSG_NOSIGNAL=$B1
MSG_SECOND=$B2
MSG_CAMSUP=$B5
MSG_AGAIN2=$B6
MSG_GRUMPY=$B7
MSG_ALLSTATIC=$B8
MSG_RECONNECT=$B9
MSG_SEEAGAIN=$BB
MSG_PLIP=$C0
MSG_GOTPAGE=$C5
MSG_BREWING=$CC
MSG_FROZENAGAIN=$CD
MSG_PLIPAGAIN=$CE
MSG_KEPTPAGE=$D1
        .segment "CHAPTER"
chapbank:
        .incbin "../art/chapter-bank.bin"
.assert chapbank = $6000, lderror, "the story bank links to the chapter bank at $6000"

; ---- message plumbing for the chapter's ids ($B0 up)
; X = message: A = the line it runs on into (0 none), flags from A. The page
; changes hands as GOT A NOTEBOOK PAGE! shows.
chain_of:
        cpx #CH_FIRST
        bcs @ch
        lda chain,x
        rts
@ch:    lda chchain-CH_FIRST,x
        cmp #MSG_GOTPAGE
        bne :+
        ldy #1
        sty PAGES
:       cmp #0
        rts
ch_sfx:                        ; A = message >= MSG_COUNT: its sound, if any
        cmp #CH_FIRST
        bcc @rts
        tax
        lda chsfx-CH_FIRST,x
        beq @rts
        bpl :+
        and #$7F
        jmp sfx_jingle
:       jmp sfx_start
@rts:   rts

; ---- patch X (src/chapter_art.inc) over the canonical room; Y=1: on both
; pages too, except where a sprite covers the old background (G-Bot stays in
; front; the next frames redraw him over the new bytes).
patch:  sty PALL
        lda patlo,x
        sta SRC
        lda pathi,x
        sta SRC+1
        lda patrow,x
        sta PROW
        lda path,x
        sta PLEFT
        lda patw,x
        sta PW
        lda patcol,x
        sta PCOL
@row:   ldx PROW
        lda rowlo,x
        clc
        adc PCOL               ; (row bases end at $D0: no carry)
        sta BG
        sta DST
        sta MP
        lda rowhi,x
        ora #$80
        sta BG+1
        and #$1F
        ora #$20
        sta DST+1
        eor #$60
        sta MP+1
        ldy #0
@b:     lda (BG),y
        sta PCOLD
        lda (SRC),y
        sta (BG),y
        ldx PALL
        beq @next
        tax
        lda (DST),y
        cmp PCOLD
        bne :+
        txa
        sta (DST),y
:       lda (MP),y
        cmp PCOLD
        bne @next
        txa
        sta (MP),y
@next:  iny
        cpy PW
        bne @b
        tya
        clc
        adc SRC
        sta SRC
        bcc :+
        inc SRC+1
:       inc PROW
        dec PLEFT
        bne @row
        rts

; ---- arriving: security's snow, wing B's awake machine (into $8000 only;
; the door then shows the room)
chapter_arrive:
        ldy #0
        lda ROOM
        cmp #2
        bne @wing
        lda GSTATE
        cmp #3
        bne @rts
        lda CAMJOB
        cmp #3
        beq @rts
        ldx #PATCH_STATIC
        jmp patch
@wing:  cmp #WINGROOM
        bne @rts
        lda MINUTE
        cmp #4
        bne @rts
        ldx #PATCH_AWAKE
        jmp patch
@rts:   rts

; ---- security: the guard wakes, his monitors go to snow (unless fixed)
cams_static:
        lda CAMJOB
        cmp #3
        beq :+
        ldx #PATCH_STATIC
        ldy #1
        jmp patch
:       rts
; the reconnect finished (interaction, CAMJOB now 3): the feeds come back
cams_fixed:
        ldx #PATCH_FEEDS
        ldy #1
        jsr patch
        lda #MSG_SEEAGAIN      ; GUARD: I CAN SEE! THANKS, G-BOT. (runs on)
        sta MESSAGE
        lda #96
        sta FEEDBACK
        rts
; Space at the desk: C=1 when the snowed-in monitors take it (inspected:
; the context line offers R)
desk_probe:
        lda GSTATE
        cmp #3
        bne @no
        lda CAMJOB
        cmp #3
        beq @no
        lda #1
        sta CAMJOB
        lda #0
        sta FEEDBACK
        sec
        rts
@no:    clc
        rts
sec_context:                   ; A = the security room's status line
        lda #23                ; SECURITY UNIT REBOOTING...
        ldx GSTATE
        cpx #1
        beq @rts
        lda NEAR
        bne @desk
        lda CAMJOB             ; walking away cancels the inspection
        cmp #1
        bne :+
        lda #0
        sta CAMJOB
:       lda GSTATE
        cmp #3
        bne @asleep
        lda #MSG_OFFDUTY       ; GUARD: OFF DUTY. WING B IS OPEN.
        ldx CAMJOB
        cpx #3
        beq @rts
        lda #MSG_ALLSTATIC     ; GUARD: MY MONITORS! ALL STATIC!
        rts
@asleep:lda #MSG_STUCKTOO      ; G-BOT: THE GUARD... IS STUCK TOO.
        ldx MINUTE
        cpx #1
        beq @rts
        lda #22                ; SECURITY ROOM - MIND THE GUARD BOT
@rts:   rts
@desk:  lda #26                ; SECURITY DESK: SPACE TO PROBE
        ldx CAMJOB
        cpx #1
        bne @rts
        lda #MSG_RECONNECT     ; MONITORS: STATIC! R RECONNECT / ESC
        rts

; ---- the lab: the chamber (lead in) and the console, minutes two on
chamber_line:                  ; A = the chamber's line
        lda MINUTE
        cmp #2
        beq @two
        lda #MSG_CHARGED       ; CHAMBER: ONE MINUTE CARRIED. GO! (1 or 3)
        bcc @rts
        ldx MINUTE
        cpx #3
        beq @rts
        lda #MSG_SOON          ; CHAMBER: RECHARGING. NEXT MINUTE SOON
@rts:   rts
@two:   lda CAMJOB
        cmp #3
        beq :+
        lda #MSG_EMPTY         ; CHAMBER: EMPTY. FIX SOMETHING NEARBY. (runs on)
        rts
:       lda #3                 ; recharged: the second minute
        sta MINUTE
        lda #$FF
        sta LASTMSG            ; (the HUD clock is back)
        lda #MSG_SECOND        ; CHAMBER: CHARGED! A SECOND MINUTE. (runs on)
        rts
ch_console:                    ; X = the console's line once a minute is spent
        ldx #MSG_GRUMPY        ; CONSOLE: 6:05! SOMEONE IS GRUMPY.
        lda MINUTE
        cmp #4
        beq @rts
        ldx #MSG_AGAIN2        ; CONSOLE: 6:04 AND TICKING. AGAIN!
        cmp #3
        beq @rts
        ldx #MSG_CAMSUP        ; CONSOLE: CAMERAS UP. CHAMBER CHARGED.
        lda CAMJOB
        cmp #3
        beq @rts
        ldx #MSG_WOKE          ; CONSOLE: 6:04! SOMETHING WOKE UP. (runs on)
@rts:   rts

; ---- wing B: Space at the coffee machine or the loop log
wing_probe:
        ldx #28                ; NOTHING TO PROBE HERE
        lda NEAR
        beq @say
        ldx #MSG_LOG           ; LOOP LOG: 4,817 TALLY MARKS. NEAT. (runs on)
        cmp #2
        beq @say
        lda MINUTE
        cmp #3
        beq coffee_wakes
        cmp #4
        bne @frozen
        ldx #MSG_BREWING       ; COFFEE: BREWING. GO FIND HER PAGES.
        lda PAGES
        bne @say
        ldx #MSG_GOTPAGE-1     ; (walked off before the page: it again)
        bne @say
@frozen:ldx #MSG_COFFEE        ; A DROP OF COFFEE, FROZEN IN MIDAIR. (runs on)
        lda PAGES
        beq @say
        ldx #MSG_FROZENAGAIN   ; G-BOT: FROZEN AGAIN. I KEPT THE PAGE. (runs on)
@say:   stx MESSAGE
        lda #96
        sta FEEDBACK
        rts
; The second minute: the drop falls (a pause by nature), the machine wakes.
coffee_wakes:
        lda #4
        sta MINUTE             ; spent (the lab clock will say 6:05)
        ldx #MSG_PLIP          ; ...PLIP! THE DROP FINALLY LANDS. (runs on)
        lda PAGES
        beq :+
        ldx #MSG_PLIPAGAIN     ; ...PLIP! THE DROP LANDS. AGAIN. (it knows him)
:       stx MESSAGE
        stx LASTMSG
        txa
        jsr draw_status        ; the line, and the HUD clock clears
        jsr copy_status
        ldx #PATCH_DROP1
        jsr @frame
        ldx #PATCH_DROP2
        jsr @frame
        ldx #PATCH_AWAKE
        ldy #1
        jsr patch
        lda #SFX_PLIP
        jsr sfx_jingle
        lda #96
        sta FEEDBACK
        rts
@frame: ldy #1
        jsr patch
        lda #$C0               ; (~95 ms)
        jmp wait

fx_plip:    .byte NG6,4, NE6,4, 0,4, NC6,10, 0,0

        .include "chapter_msgs.inc"
        .include "chapter_art.inc"
chapter_end:
.assert chapter_end <= $7000, lderror, "the chapter track holds 4K"
