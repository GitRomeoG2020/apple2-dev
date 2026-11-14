; Twist two: restoring full power reruns the experiment (LCHI, $E000+).
;
; The substation (room 4) sits behind the power room's east door, which the
; lab unseals once the console is back in phase. Its MAIN BREAKER asks
; RESTORE FULL POWER? Y/N:
;   Y  the experiment reruns: surge, strobe, white-out, black; the loop resets
;      and G-Bot wakes in the workshop at 12:15 with LOOPS one higher. The
;      machines remember him (workbench, fuse, lab door stay fixed); the console
;      drifts again and the guard reboots. Later lines remark on the loops.
;   N  he leaves it off and takes the trickle lead off its hook: the new task is
;      the time chamber, where it unsticks one minute (TO BE CONTINUED).
STORYBANK=$F800                ; shared story messages (tools/gen_banks.py STORY)
SUBROOM=4
ENTER_SUB_MSG=65
MSG_SEALED_SUB=66
MSG_SUB=68
MSG_BREAKER=69
MSG_CHOICE=70
MSG_RERUN=71
MSG_REBOOT=72
MSG_BADIDEA=73
MSG_STILLBAD=74
MSG_REFUSE=75
MSG_OFF_RIGHT=78
MSG_DRIFT1=79
MSG_DRIFTN=80
MSG_AGAIN1=81
MSG_AGAINN=84
MSG_PLUGGED=85
MSG_GOODBOT=90
MSG_SOON=91
MSG_PLUGHINT=92
MSG_TICKING=93
MSG_DEJA1=94
MSG_DEJAN=95
HESITATE=14                    ; deja-vu ticks before the prompt (~0.8 s)

; ---- rooms 3 and 4 have their own keys. In: A = key. Out: C=1 used, else A, X kept.
roomkeys:
        ldy ROOM
        cpy #SUBROOM
        beq subkeys
        jmp labkeys
subkeys:
        ldy CHOICE
        bne :+
        clc
        rts
:       pha
        and #$DF
        cmp #'Y'
        beq @yes
        cmp #'N'
        beq @no
        cmp #$1B
        beq @cancel
        pla                    ; anything else (walking away cancels)
        clc
        rts
@cancel:pla
        lda #0
        sta CHOICE
        sec
        rts
@no:    pla
        jsr refuse
        sec
        rts
@yes:   pla
        jsr restore
        sec
        rts

; ---- substation geometry: the breaker cabinet (x 102-176, plinth front y=100)
sub_solid:                     ; C=1: PX/PY blocked
        lda PY
        cmp #56
        bcs @free
        lda PX
        cmp #70
        bcc @free
        cmp #176
        bcs @free
        sec
        rts
@free:  clc
        rts
sub_near:                      ; the breaker apron: NEAR=1
        lda PY
        cmp #64
        bcs :+
        lda PX
        cmp #64
        bcc :+
        cmp #182
        bcs :+
        inc NEAR
:       rts
sub_doors:                     ; west: back to the power room's east door
        lda DIR
        cmp #1
        bne @no
        lda PX
        cmp #14
        bne @no
        lda PY
        cmp #76
        bcc @no
        cmp #105
        bcs @no
        lda #1
        sta NDIR
        ldx #224
        ldy #104
        jmp door_go
@no:    rts
power_east:                    ; the power room's east door (front half)
        lda PX
        cmp #224
        bne @no
        lda PY
        cmp #94
        bcc @no
        lda CONSOLE
        cmp #3
        beq :+
        lda #MSG_SEALED_SUB    ; SUBSTATION SEALED - NEEDS LAB OK
        jmp door_sealed
:       lda #2
        sta NDIR
        lda #SUBROOM
        ldx #14
        ldy #90
        jmp door_go
@no:    rts

; ---- substation status line (A = message)
sub_context:
        lda HESIT              ; the deja vu has passed: now the question
        beq @ask
        lda #0
        sta HESIT
        lda BURST              ; (unless he walked off mid-glitch)
        bne @ask
        lda NEAR
        beq @ask
        sta CHOICE
@ask:   lda CHOICE
        beq @plain
        lda NEAR
        bne :+
        sta CHOICE             ; walking away cancels the choice
        beq @plain
:       lda #MSG_CHOICE        ; RESTORE FULL POWER?  Y YES / N NO
        rts
@plain: lda NEAR
        beq :+
        lda #MSG_BREAKER       ; MAIN BREAKER: SPACE TO PROBE
        rts
:       lda #MSG_SUB
        ldx REFUSED
        beq :+
        lda #MSG_OFF_RIGHT     ; BREAKER STAYS OFF. SHE WAS RIGHT.
:       rts
sub_probe:
        lda NEAR
        beq :+
        ldx LOOPS              ; first probe in this loop: deja vu
        inx
        cpx DEJA
        beq @ask
        stx DEJA
        lda #1
        sta HESIT
        lda #MSG_DEJA1         ; G-BOT: ...HAVE I DONE THIS BEFORE?
        ldx LOOPS
        beq @say
        lda #MSG_DEJAN         ; G-BOT: ...I HAVE DONE THIS BEFORE.
@say:   sta MESSAGE
        lda #HESITATE+2
        sta FEEDBACK
        lda #SFX_CRACKLE       ; a little time glitch
        jmp sfx_start
@ask:   lda #1
        sta CHOICE             ; the prompt
        lda #0
        sta FEEDBACK
        rts
:       ldx #28                ; NOTHING TO PROBE HERE
        stx MESSAGE
        lda #96
        sta FEEDBACK
        rts

; ---- N: he leaves it off, and takes the trickle lead
refuse: lda #0
        sta CHOICE
        lda #1
        sta REFUSED
        ldx #MSG_OFF_RIGHT
        lda LEAD
        bne :+
        lda #1
        sta LEAD
        lda #$FF
        sta LASTMSG            ; the HUD shows what he carries
        ldx #MSG_REFUSE        ; G-BOT: NO. SHE SAID NO FULL POWER. (runs on)
:       stx MESSAGE
        lda #96
        sta FEEDBACK
        lda #SFX_CHIME
        jmp sfx_start

; ---- Y: the experiment reruns. Blocking (a pause by nature): the surge, a
; strobe between the screen and its negative, a white-out, black, then the
; loop resets and the next "door" wakes G-Bot in the workshop.
restore:
        lda #0
        sta CHOICE
        lda #MSG_RERUN         ; FULL POWER! HERE WE GO AGAIN-
        sta MESSAGE
        sta LASTMSG
        jsr draw_status
        jsr copy_status
        lda #SFX_SURGE
        jsr sfx_jingle
        ldx PAGE               ; the hidden page becomes the negative
        jsr invert_page
        lda #4
        sta TMPY
strobe:ldx PAGE
        lda $C054,x            ; negative on screen
flash_shot:                    ; (tests photograph the flash here)
        lda #SFX_ZAP
        jsr sfx_jingle
        lda #$90               ; (~54 ms each way)
        jsr wait
        lda PAGE
        eor #1
        tax
        lda $C054,x            ; and back
        lda #$90
        jsr wait
        dec TMPY
        bne strobe
        lda #$7F               ; white-out on the hidden page
        ldx PAGE
        jsr fill_hgr
        ldx PAGE
        lda $C054,x
        lda #SFX_CHORD
        jsr sfx_jingle
        lda #$C0
        jsr wait
        lda PAGE               ; and black on the other, shown last (so PAGE's
        eor #1                 ; partner is on screen, as main expects)
        tax
        lda #0
        jsr fill_hgr
        lda PAGE
        eor #1
        tax
        lda $C054,x
        ; The loop resets. What the machines remember stays.
        lda LOOPS
        cmp #$FF
        beq :+
        inc LOOPS
:       lda #0
        sta CONSOLE            ; the console drifts again
        sta TUNESTEP
        sta TALK
        sta GSTATE             ; the guard will reboot
        sta LEAD               ; the lead is back on its hook
        sta REFUSED
        sta SCPHASE
        sta FEEDBACK
        sta BURST
        sta PROBE
        lda #1
        sta WAKE
        lda #0                 ; wake in the workshop, at the bench-side spawn
        sta NDIR
        ldx #126
        ldy #104
        jmp door_go

; X = page (0/1): every byte's pixels inverted (palette bit kept)
invert_page:
        lda pagehigh,x
        sta DST+1
        ldy #0
        sty DST
        ldx #32
@l:     lda (DST),y
        eor #$7F
        sta (DST),y
        iny
        bne @l
        inc DST+1
        dex
        bne @l
        rts
; A = byte, X = page (0/1): fill it
fill_hgr:
        pha
        lda pagehigh,x
        sta DST+1
        ldy #0
        sty DST
        ldx #32
        pla
@l:     sta (DST),y
        iny
        bne @l
        inc DST+1
        dex
        bne @l
        rts

; ---- the wake door: its status line, and G-Bot's verdict on arrival
door_msg:                      ; X = next room: A = the door's status line
        lda WAKE
        beq :+
        lda #MSG_REBOOT        ; G-BOT REBOOTING... 12:15 AGAIN
        rts
:       lda entermsg,x
        rts
story_arrive:
        lda WAKE
        beq @rts
        lda #0
        sta WAKE
        lda #MSG_BADIDEA       ; (the rewind played at the door; the punchline)
        ldx LOOPS
        cpx #2
        bcc :+
        lda #MSG_STILLBAD
:       sta MESSAGE
        lda #128
        sta FEEDBACK
@rts:   rts

; ---- lines that remember the choice
first_line:                    ; A = her first line after the console locks
        lda #FIRST_DIALOG
        ldx LOOPS
        beq :+
        lda #MSG_AGAIN1
        dex
        beq :+
        lda #MSG_AGAINN
:       rts
drift_line:                    ; X = the console's diagnosis
        ldx #41
        lda LOOPS
        beq :+
        ldx #MSG_DRIFT1
        cmp #1
        beq :+
        ldx #MSG_DRIFTN
:       rts
console_line:                  ; X = the console once in phase
        ldx #58
        lda LEAD
        cmp #2
        bne :+
        ldx #MSG_TICKING
        rts
:       lda REFUSED
        beq :+
        ldx #MSG_GOODBOT
:       rts
lab_probe:                     ; X = NEAR (not the consoles): A = message
        cpx #1
        bne @table
        lda LEAD
        cmp #1
        bne :+
        lda #2                 ; the trickle lead goes into the chamber
        sta LEAD
        lda #$FF
        sta LASTMSG
        lda #MSG_PLUGGED       ; TRICKLE LEAD IN. THE RING TICKS ONCE. (runs on)
        rts
:       cmp #2
        bne @table
        lda #MSG_SOON
        rts
@table: lda labprobe,x
        rts
lab_context:                   ; X = NEAR: A = message
        cpx #1
        bne :+
        lda LEAD
        cmp #1
        bne :+
        lda #MSG_PLUGHINT      ; CHAMBER: SPACE TO PLUG IN THE LEAD
        rts
:       lda labctx,x
        rts
carrying:                      ; Z=1: the HUD shows a carried fuse or lead
        lda FUSE
        cmp #1
        beq :+
        lda LEAD
        cmp #1
:       rts

; G-Bot's pose by PROBE ticks left while he hesitates (index 0..HESITATE):
; the probe goes up (13), stalls and stutters with the eyes flickering
; (blink 12 / idle 0), then he just stands there, wondering.
hesitframe:
        .byte 0,0,0, 12,0,12,13,12,0,12,0, 13,13,13,13
