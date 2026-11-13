; G-Bot: After Hours -- four rooms: workshop, power room, security room, lab.
; Plain NMOS 6502 / 48K. HGR pages $2000/$4000, canonical room $8000,
; G-Bot's masked frames $A000, actor frames $1800: the guard (track 13, read
; at boot) or the lab's flickering scientist (track 16), loaded per room.
; Only ONE 8K room fits at $8000: room changes stream the next background from
; disk through the resident boot loader. Tracks: 3-4 workshop, 7-8 dark power
; room, 9-10 lit power room, 11-12 security room, 14-15 lab.
; Every frame: restore both sprites' old rectangles on the offscreen page, sync
; diagnostics, then composite back-to-front (by feet depth) and flip.
; All G-Bot x positions are even: artifact-color parity never reverses.
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
REPAIR=$83                    ; workbench job: 0 faulted 1 inspected 2 working 3 done
NEAR=$84                      ; 0 nothing; 1 bench/panel/desk; 2 power-room locker
MESSAGE=$85
LASTMSG=$86
REPAIRTIME=$87
FEEDBACK=$88
UIROW=$89
ROOM=$8A                      ; 0 workshop, 1 power room, 2 security room
TRANSIT=$8B                   ; set when G-Bot walks into an open doorway
PANEL=$8C                     ; breaker job, same states as REPAIR
FUSE=$8D                      ; 0 in the locker, 1 carried, 2 fitted
NOJOB=$8E                     ; security room has no job: always 0
GX=$8F                        ; guard byte column (moves whole bytes)
GDIR=$90                      ; 0 rolling east, 1 west
GTICK=$91
GSTATE=$92                    ; 0 never seen, 1 rebooting, 2 patrolling
GTIMER=$93
GANIM=$94
GSHOW=$95                     ; guard frame drawn this tick (pose*2+parity)
GOLD=$96                      ; guard column last drawn on page 0 / page 1
NEXTROOM=$98
NX=$99
NY=$9A
NDIR=$9B
POWERUP=$9C
LABOPEN=$9D                   ; security desk probed: lab door unlocked
ACTLOADED=$9E                 ; whose frames are at $1800: 2 guard, 3 scientist
ACTX=$9F                      ; current room's actor: byte column, top row,
ACTY=$A0                      ;   height, frame index, visible
ACTH=$A1
ACTSHOW=$A2
ACTVIS=$A3
GOLDY=$A4                     ; actor top row last drawn on page 0 / page 1
SCSPOT=$A6                    ; scientist: spot 0-2, phase timer, phase
SCTIMER=$A7
SCPHASE=$A8                   ; 0 gone, 1 flickering in, 2 here, 3 flickering out
MASKBUF=$1200                 ; 308 shifted opacity bytes (not inverse masks)
DATABUF=$1000                 ; 308 shifted pixels
PHASEBUF=$1400                ; 44 phase bytes
GUARDART=$1800                ; 6 x 270-byte guard frames from track 13
LOADROOM=$0805                ; resident boot-loader entry: A=track, Y=page
LOADONE=$0808                 ; same, one track (4K)
WORKSHOP_TRACK=3
POWER_TRACK=7
POWERLIT_TRACK=9
SECURITY_TRACK=11
GUARD_TRACK=13
LAB_TRACK=14
SCI_TRACK=16
DOOR_X0=110                   ; workshop/power doorway column (PX), inclusive
DOOR_X1=134
GY=93                         ; guard top row; feet on y=122
GXMIN=2
GXMAX=30
GSTEP=3                       ; ticks per one-byte guard step
SPAWNX=224                    ; security-room entry checkpoint
SPAWNY=104

        .export entry, main, code_end
        .segment "CODE"
entry:  cld
        sei
        ldx $2B
        lda $C088,x            ; motor off; only room changes read the disk
        bit $C051              ; hide setup in text mode
        lda #0
        ldx #$58
@state: sta $50,x
        dex
        bpl @state
        lda #GXMIN
        sta GX
        lda #2                 ; boot read the guard's frames
        sta ACTLOADED
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
        lda #$FF
        sta LASTMSG
        jsr interaction
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
        lda TRANSIT
        beq :+
        jsr transition
        jmp main               ; both pages already complete
:       jsr actors
        jsr interaction
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
        bmi :+
        rts
:
        bit $C010
        ldy ROOM
        ldx jobx,y
        ldy REPAIR,x
        cpy #2
        beq @done              ; a repair/fit in progress ignores keys
        and #$7F
        cmp #$1B
        beq @cancel
        cmp #$20
        beq @probe
        and #$DF               ; accepts lower-case WASD on IIe
        cmp #'R'
        beq @repair
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
        sta FEEDBACK
        rts
@cancel:
        lda REPAIR,x
        cmp #1
        bne @done
        lda #0
        sta REPAIR,x
        rts
@repair:
        lda REPAIR,x
        cmp #1
        bne @done
        lda NEAR
        cmp #1
        bne @done
        lda #2
        sta REPAIR,x
        lda #24
        sta REPAIRTIME
        sta PROBE
        lda #0
        sta BURST
        sta DIR
        rts
@probe: lda PROBE
        bne @done
        jsr probe_contact
        lda #8
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
        bne :+
        rts
:       dec BURST
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
        ; Footprint vs. room walls, then each room's solid furniture.
        lda PX
        cmp #14
        bcc @blocked
        cmp #225
        bcs @blocked
        lda PY
        cmp #48
        bcc @blocked
        cmp #121               ; front edge: feet at row 163
        bcs @blocked
        lda ROOM
        beq @work
        cmp #1
        beq @power
        cmp #3
        bne @desk
        lda PY                 ; lab: time-chamber dais, front y=100
        cmp #58
        bcs @allowed
        lda PX
        cmp #64
        bcc @allowed
        cmp #175
        bcs @allowed
        bcc @blocked
@desk:  lda PX                 ; security desk: front y=96, right x=100
        cmp #82
        bcs @allowed
        lda PY
        cmp #54
        bcc @blocked
        bcs @allowed
@power: lda PX                 ; generator: front y=112, left x=184
        cmp #150
        bcc @allowed
        lda PY
        cmp #70
        bcc @blocked
        bcs @allowed
@work:  lda PX
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
        ; fall through: walking into a wall may mean walking into a door

; Doors. A = message when sealed; otherwise queue the transition.
doors:  lda ROOM
        bne :+
        jmp @workshop
:       cmp #1
        bne :+
        jmp @power
:       cmp #3
        bne @security
        lda DIR                ; lab: doorway at the bottom, back to security
        bne @no1
        lda PY
        cmp #120
        bne @no1
        jsr incolumn
        bcc @no1
        lda #0
        sta NDIR
        lda #2
        ldx PX
        ldy #48
        jmp @go
@no1:   rts
@security:
        lda DIR
        cmp #3
        bne @east
        lda PY                 ; north: the lab door, released from the desk
        cmp #48
        bne @no1
        jsr incolumn
        bcc @no1
        lda LABOPEN
        bne :+
        lda #29                ; LAB DOOR LOCKED - TRY THE DESK
        jmp @sealed
:       lda #3
        sta NDIR
        ldx PX
        ldy #120
        jmp @go
@east:  lda DIR                ; east door, front half of right wall
        cmp #2
        bne @no0
        lda PX
        cmp #224
        bne @no0
        lda PY
        cmp #94
        bcc @no0
        lda #2
        sta NDIR
        lda #1
        ldx #14
        ldy #90
        bne @go
@no0:   rts
@power: lda DIR
        cmp #1
        beq @west
        cmp #0
        bne @no
        lda PY                 ; south: the lit doorway back to the workshop
        cmp #120
        bne @no
        lda PX
        cmp #DOOR_X0
        bcc @no
        cmp #DOOR_X1+1
        bcs @no
        lda #0
        sta NDIR
        ldx PX
        ldy #48
        bne @go
@west:  lda PX                 ; west: security door, needs power
        cmp #14
        bne @no
        lda PY
        cmp #76
        bcc @no
        cmp #105
        bcs @no
        lda PANEL
        cmp #3
        beq :+
        lda #21                ; SECURITY DOOR SEALED - NO POWER
        bne @sealed
:       lda #1
        sta NDIR
        lda #2
        ldx #SPAWNX
        ldy #SPAWNY
        bne @go
@workshop:
        lda DIR                ; rear door, walking north
        cmp #3
        bne @no
        lda PY
        cmp #48
        bne @no
        lda PX
        cmp #DOOR_X0
        bcc @no
        cmp #DOOR_X1+1
        bcs @no
        lda REPAIR
        cmp #3
        beq :+
        lda #12                ; DOOR SEALED - FIX WORKBENCH FIRST
        bne @sealed
:       lda #3
        sta NDIR
        lda #1
        ldx PX
        ldy #120
@go:    sta NEXTROOM
        stx NX
        sty NY
        inc TRANSIT
@no:    rts
@sealed:sta MESSAGE
        lda #64
        sta FEEDBACK
        rts

incolumn:                      ; C=1 when PX is in the shared doorway column
        lda PX
        cmp #DOOR_X0
        bcc :+
        cmp #DOOR_X1+1
        bcs :++
        sec
:       rts
:       clc
        rts

; Room change (or reload of the lit power room). Entry/exit: PAGE is the
; displayed page. Only the workshop door gets the slide-open beat.
transition:
        lda PAGE
        eor #1
        sta PAGE               ; main had already flipped to the hidden page
        lda #0
        sta TRANSIT
        sta BURST
        sta PROBE
        sta FEEDBACK
        sta MOVING
        lda ROOM
        bne @nodoor
        jsr open_door
        jsr show_room
        ldx #3
@beat:  lda #$FF               ; a short beat in the open doorway
        jsr $FCA8
        dex
        bne @beat
@nodoor:lda NEXTROOM
        sta ROOM
        lda NX
        sta PX
        lda NY
        sta PY
        lda NDIR
        sta DIR
        ldx ROOM
        lda roomtrack,x
        cpx #1
        bne @load
        ldy PANEL
        cpy #3
        bne @load
        lda #POWERLIT_TRACK
@load:  ldy #>room
        jsr LOADROOM
        ldx ROOM               ; this room's actor frames at $1800, if needed
        cpx #2
        bcc @noactor
        cpx ACTLOADED
        beq @noactor
        stx ACTLOADED
        lda actortrack-2,x
        ldy #$10
        jsr LOADONE
@noactor:
        lda POWERUP
        beq :+
        lda #0
        sta POWERUP
        lda #18                ; POWER RESTORED - WEST DOOR OPEN
        sta MESSAGE
        lda #96
        sta FEEDBACK
:       lda ROOM
        cmp #2
        bne :+
        lda GSTATE
        bne :+
        lda #1                 ; first visit: the guard is still booting
        sta GSTATE
        lda #40
        sta GTIMER
:       lda ROOM
        cmp #3
        bne :+
        lda #0                 ; lab: the scientist is out of sync for a moment
        sta SCPHASE
        lda #20
        sta SCTIMER
:       jsr actor_show
        lda #$FF
        sta LASTMSG
        jsr interaction        ; status line, and repair patches if workshop
        jmp show_room

actors: lda ROOM
        cmp #2
        bne :+
        jmp guard
:       cmp #3
        beq scientist
        rts
actor_show:
        lda ROOM
        cmp #2
        bne :+
        jmp guard_show
:       cmp #3
        beq sci_show
        rts

; The flickering scientist: harmless. Gone, flickers in, stays ~3 s, flickers
; out, then turns up at the next spot. Ghost frames draw alternate rows only.
scientist:
        dec SCTIMER
        bne sci_show
        ldx SCPHASE
        inx
        cpx #4
        bcc @set
        ldx #0
        ldy SCSPOT
        iny
        cpy #3
        bcc :+
        ldy #0
:       sty SCSPOT
@set:   stx SCPHASE
        lda phasetime,x
        sta SCTIMER
sci_show:
        ldx SCSPOT
        lda spotx,x
        sta ACTX
        lda spoty,x
        sta ACTY
        lda #40
        sta ACTH
        ldy SCPHASE
        lda phasevis,y
        sta ACTVIS
        lda #0
        cpy #2
        beq :+
        lda SCTIMER            ; flickering: alternate solid and ghost
        and #1
        asl a
:       clc
        adc #6                 ; scientist frames follow the guard's six
        sta ACTSHOW
        lda ACTX
        and #1
        ora ACTSHOW
        sta ACTSHOW
        rts

; Security guard: dormant until first seen, ~3 s reboot, then a steady
; byte-stepped patrol along the hazard lane. Touch = back to the checkpoint.
guard:  lda ROOM
        cmp #2
        beq :+
        rts
:       lda GSTATE
        cmp #2
        beq @patrol
        cmp #1
        bne guard_show
        dec GTIMER
        bne guard_show
        lda #2
        sta GSTATE
        bne guard_show
@patrol:
        inc GTICK
        lda GTICK
        cmp #GSTEP
        bcc @touch
        lda #0
        sta GTICK
        lda GANIM
        eor #1
        sta GANIM
        lda GDIR
        bne @left
        inc GX
        lda GX
        cmp #GXMAX
        bcc @touch
        lda #1
        sta GDIR
        bne @touch
@left:  dec GX
        lda GX
        cmp #GXMIN+1
        bcs @touch
        lda #0
        sta GDIR
@touch: lda PY                 ; same depth: G-Bot feet within 13 rows of y=122
        cmp #66
        bcc guard_show
        cmp #93
        bcs guard_show
        lda GX                 ; guard body x = GX*7+2 .. GX*7+25
        asl a
        asl a
        asl a
        sec
        sbc GX
        sta TMPX
        clc
        adc #20                ; PX+6 < TMPX+26 ?
        cmp PX
        beq guard_show
        bcc guard_show
        lda TMPX               ; TMPX+2 < PX+36 ?
        sec
        sbc PX
        bcc @hit
        cmp #34
        bcs guard_show
@hit:   lda #SPAWNX            ; zapped back to the room's entry checkpoint
        sta PX
        lda #SPAWNY
        sta PY
        lda #1
        sta DIR
        lda #0
        sta BURST
        sta PROBE
        lda #24                ; GUARD: WORK ORDER NOT RECOGNIZED
        sta MESSAGE
        lda #64
        sta FEEDBACK
guard_show:
        lda GX
        and #1
        sta GSHOW
        lda GSTATE
        cmp #2
        bne :+
        lda GANIM
        asl a
        adc #2
        adc GSHOW
        sta GSHOW
:       lda GSHOW
        sta ACTSHOW
        lda GX
        sta ACTX
        lda #GY
        sta ACTY
        lda #30
        sta ACTH
        lda #1
        sta ACTVIS
        rts

probe_contact:
        lda ROOM
        bne :+
        jmp @workshop
:       cmp #1
        beq @power
        cmp #3
        beq @lab
        ldx #28                ; NOTHING TO PROBE HERE
        lda NEAR
        beq @say
        lda #1
        sta LABOPEN            ; the desk's door release: lab unlocked
        ldx #27                ; MONITORS: EVERY CAMERA SHOWS NOBODY
        bne @say
@lab:   ldx NEAR
        lda labprobe,x
        tax
        bne @say
@power: lda NEAR
        bne @thing
        ldx #11                ; TOO DARK - NOTHING TO PROBE HERE
        lda PANEL
        cmp #3
        bne @say
        ldx #28
        bne @say
@thing: cmp #2
        beq @locker
        ldx #20                ; PANEL ONLINE - ALL BREAKERS SET
        lda PANEL
        cmp #3
        beq @say
        ldx #10                ; NO POWER - FIND FUSE
        lda FUSE
        cmp #1
        bne @say
        lda #1                 ; carrying the fuse: offer R to fit it
        sta PANEL
        lda #0
        sta FEEDBACK
        rts
@locker:ldx #15                ; LOCKER IS EMPTY NOW
        lda FUSE
        bne @say
        lda #1
        sta FUSE
        lda #$FF
        sta LASTMSG            ; redraw the status line with the fuse icon
        ldx #14                ; FOUND A FUSE! TAKE IT TO THE PANEL
@say:   stx MESSAGE
        lda #96
        sta FEEDBACK
        rts
@workshop:
        lda NEAR
        bne @contact
        lda #5
        bne @feedback
@contact:
        lda REPAIR
        cmp #3
        beq @online
        lda #1
        sta REPAIR
        lda #0
        sta FEEDBACK
        rts
@online:
        lda #6
@feedback:
        sta MESSAGE
        lda #48
        sta FEEDBACK
        rts

interaction:
        lda #0
        sta NEAR
        lda ROOM
        beq @workshop
        cmp #1
        beq @prange
        cmp #3
        bne @srange
        jsr labnear
        jmp @range_done
@srange:lda PX                 ; security desk apron
        cmp #76
        bcs @range_done
        lda PY
        cmp #64
        bcs @range_done
        inc NEAR
        bne @range_done
@prange:lda PY                 ; power room: back-wall panel and locker
        cmp #60
        bcs @range_done
        lda PX
        cmp #30
        bcc @range_done
        cmp #73
        bcc @panel
        cmp #100
        bcc @range_done
        cmp #141
        bcs @range_done
        lda #2
        sta NEAR
        bne @range_done
@panel: inc NEAR
        bne @range_done
@workshop:
        lda PX
        cmp #14
        bcc @range_done
        cmp #65
        bcs @range_done
        lda PY
        cmp #64
        bcc @range_done
        cmp #85
        bcs @range_done
        inc NEAR
@range_done:
        ldy ROOM
        ldx jobx,y
        lda REPAIR,x
        cmp #2
        bne @not_busy
        dec REPAIRTIME
        bne @busy
        lda #3
        sta REPAIR,x
        lda #0
        sta PROBE
        sta FEEDBACK
        lda ROOM
        cmp #1
        bne @not_busy
        lda #2                 ; fuse fitted: reload the room, now lit
        sta FUSE
        lda #1
        sta NEXTROOM
        sta POWERUP
        sta TRANSIT
        lda PX
        sta NX
        lda PY
        sta NY
        lda DIR
        sta NDIR
        jmp @not_busy
@busy:  ldx ROOM
        lda busymsg,x
        jmp @message
@not_busy:
        lda FEEDBACK
        beq @context
        dec FEEDBACK
        bne :+
        ldx MESSAGE            ; a probe line that runs on into the next one
        lda chain,x
        beq :+
        sta MESSAGE
        lda #96
        sta FEEDBACK
:       lda MESSAGE
        jmp @message
@context:
        lda ROOM
        beq @workroom
        cmp #1
        beq @powerroom
        cmp #3
        bne :+
        ldx NEAR
        lda labctx,x
        jmp @message
:       lda #23                ; SECURITY UNIT REBOOTING...
        ldx GSTATE
        cpx #1
        beq @message
        lda #26                ; SECURITY DESK: SPACE TO PROBE
        ldx NEAR
        bne @message
        lda #22                ; SECURITY ROOM - MIND THE GUARD BOT
        bne @message
@powerroom:
        lda PANEL
        cmp #1
        bne @pr2
        lda NEAR
        cmp #1
        bne @cancel
        lda #16                ; FUSE FITS: R TO FIT / ESC CANCEL
        bne @message
@cancel:lda #0                 ; walking away cancels, the fuse stays carried
        sta PANEL
@pr2:   lda NEAR
        cmp #1
        bne @pr3
        lda #9                 ; BREAKER PANEL: SPACE TO PROBE
        bne @message
@pr3:   cmp #2
        bne @pr4
        lda FUSE
        bne @pr4
        lda #13                ; OLD LOCKER: SPACE TO PROBE
        bne @message
@pr4:   lda #8                 ; DARK POWER ROOM - EYES ADJUSTING...
        ldx PANEL
        cpx #3
        bne @message
        lda #19                ; POWER ROOM ONLINE - WEST DOOR OPEN
        bne @message
@workroom:
        lda REPAIR
        cmp #3
        beq @ready
        lda NEAR
        beq @away
        lda REPAIR
        cmp #1
        beq @loose
        lda #1
        bne @message
@loose: lda #2
        bne @message
@away:  lda #0
        sta REPAIR              ; walking away cancels inspection, not repair
        beq @message
@ready: lda #4
@message:
        sta MESSAGE
        cmp LASTMSG
        beq @patch
        sta LASTMSG
        tax
        lda messagelo,x
        sta SRC
        lda messagehi,x
        sta SRC+1
        lda #0
        sta UIROW
@textrow:                      ; 40 glyphs -> one native byte per glyph row
        lda UIROW
        clc
        adc #177
        tax
        lda rowlo,x
        sta BG
        lda rowhi,x
        ora #$80
        sta BG+1
        ldx UIROW
        lda fontlo,x
        sta FP
        lda fonthi,x
        sta FP+1
        ldy #39
@letter:lda (SRC),y
        sty COL
        tay
        lda (FP),y
        ldy COL
        sta (BG),y
        dey
        bpl @letter
        lda FUSE               ; HUD: a carried fuse in columns 38-39
        cmp #1
        bne @noicon
        ldx UIROW
        ldy #38
        lda iconl,x
        sta (BG),y
        iny
        lda iconr,x
        sta (BG),y
@noicon:inc UIROW
        lda UIROW
        cmp #5
        bne @textrow
@patch:
        ; Mutable canonical background is the sole restoration source.
        lda ROOM
        beq :++
        cmp #2
        beq :+
        rts
:       jmp secpatch           ; security: the lab-door lock lamp
:       ldx #PATCH_COUNT-1
@byte:  lda patchlo,x
        sta BG
        lda patchhi,x
        ora #$80
        sta BG+1
        lda REPAIR
        cmp #3
        beq @on
        lda patch_off,x
        jmp @store
@on:    lda patch_on,x
@store: ldy #0
        sta (BG),y
        dex
        bpl @byte
        rts

open_door:
        ldx #33
@row:   lda rowlo,x
        clc
        adc #17
        sta BG
        lda rowhi,x
        ora #$80
        sta BG+1
        lda #0
        ldy #6
@byte:  sta (BG),y
        dey
        bpl @byte
        inx
        cpx #72
        bne @row
        rts

; Rebuild both pages from the canonical room, hidden page first.
show_room:
        lda PAGE
        eor #1
        sta PAGE
        jsr fill_page
        jsr prepare
        jsr render
        ldx PAGE
        lda $C054,x
        lda PAGE
        eor #1
        sta PAGE
        jsr fill_page
        jsr render
        ldx PAGE
        lda $C054,x
        rts
fill_page:
        ldx PAGE
        lda pagehigh,x
        sta DST+1
        lda #>room
        sta SRC+1
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
        rts

; Small repair: inspect the fault, explicitly reconnect with R, watch it boot.
; A different confirmation key means held/repeating Space cannot solve it.
secpatch:
        ldx #SECPATCH_COUNT-1
@byte:  lda secpatchlo,x
        sta BG
        lda secpatchhi,x
        ora #$80
        sta BG+1
        lda LABOPEN
        beq @off
        lda secpatch_on,x
        jmp @store
@off:   lda secpatch_off,x
@store: ldy #0
        sta (BG),y
        dex
        bpl @byte
        rts

; Lab: what is G-Bot standing near? 3 the (visible) scientist, 1 the chamber,
; 2 the parking bay, 4 the consoles.
labnear:
        lda ACTVIS
        beq @fixed
        lda PY                 ; feet within 17 rows of hers?
        clc
        adc #4
        sec
        sbc ACTY
        bcs :+
        eor #$FF
        adc #1
:       cmp #18
        bcs @fixed
        lda ACTX
        asl a
        asl a
        asl a
        sec
        sbc ACTX
        sta TMPX
        clc
        adc #30
        cmp PX
        beq @fixed
        bcc @fixed
        lda TMPX
        sec
        sbc PX
        bcc @sci
        cmp #44
        bcs @fixed
@sci:   lda #3
        sta NEAR
        rts
@fixed: lda PX
        cmp #60
        bcs @nc
        lda PY
        cmp #62
        bcs @none
        lda #4
        sta NEAR
        rts
@nc:    cmp #180
        bcc @nb
        lda PY
        cmp #72
        bcs @none
        lda #2
        sta NEAR
        rts
@nb:    cmp #80
        bcc @none
        cmp #161
        bcs @none
        lda PY
        cmp #67
        bcs @none
        lda #1
        sta NEAR
@none:  rts

; Called AFTER old robot restoration and BEFORE new robot compositing.
; Each page receives the current diagnostics/visual state independently.
draw_diagnostics:
        lda #177
        sta UIROW
        lda #0
        sta OX
@row:   ldx UIROW
        jsr row_pointers
        ldy #39
@copy:  lda (BG),y
        sta (DST),y
        dey
        bpl @copy
        inc UIROW
        lda UIROW
        cmp #182
        bne @row
        ldx #PATCH_COUNT-1
@patch: lda patchlo,x
        sta BG
        sta DST
        lda patchhi,x
        ora #$80
        sta BG+1
        lda patchhi,x
        ora PAGEHI
        sta DST+1
        ldy #0
        lda (BG),y
        sta (DST),y
        dex
        bpl @patch
        ldx #SECPATCH_COUNT-1
@sp:    lda secpatchlo,x
        sta BG
        sta DST
        lda secpatchhi,x
        ora #$80
        sta BG+1
        lda secpatchhi,x
        ora PAGEHI
        sta DST+1
        ldy #0
        lda (BG),y
        sta (DST),y
        dex
        bpl @sp
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

; Restore both old rectangles first, then draw back-to-front by feet depth,
; so overlapping sprites composite correctly with no trails on either page.
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
        lda ROOM
        cmp #2
        bcc @diag
        ldx PAGE
        lda GOLD,x
        sta OX
        lda GOLDY,x
        sta OY
        lda #0
        sta ROW
@grest: lda OY
        clc
        adc ROW
        tax
        jsr row_pointers
        ldy #3
@gcopy: lda (BG),y
        sta (DST),y
        dey
        bpl @gcopy
        inc ROW
        lda ROW
        cmp ACTH
        bne @grest
@diag:  jsr draw_diagnostics
        ldx PAGE
        txa
        asl a
        tax
        lda XB
        sta OLDX,x
        lda PY
        sta OLDY,x
        lda ROOM
        cmp #2
        bcs :+
        jmp blit_gbot
:       ldx PAGE
        lda ACTX
        sta GOLD,x
        lda ACTY
        sta GOLDY,x
        lda ACTVIS
        bne :+
        jmp blit_gbot
:       lda ACTY               ; G-Bot's feet at or below the actor's: in front
        clc
        adc ACTH
        sec
        sbc #44
        sta TMPY
        lda PY
        cmp TMPY
        bcs @front
        jsr blit_gbot
        jmp blit_guard
@front: jsr blit_guard
        jmp blit_gbot

; Masked composite over whatever the page already holds (restored room or
; the other sprite). Fully transparent bytes are left untouched.
blit_gbot:
        lda XB
        sta OX
        lda PY
        sta OY
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
        beq @next
        eor #$FF
        and (DST),y
        and #$7F
        ora (DP),y
        ora PHASE
        sta (DST),y
@next:  dey
        bpl @pixel
        jsr advance_buffers
        inc ROW
        lda ROW
        cmp #44
        bne @blit
        rts

; Actor (guard or scientist): 4 bytes wide, byte-aligned (no shifting),
; parity-matched frame, ACTH rows from ACTY.
blit_guard:
        lda ACTX
        sta OX
        ldx ACTSHOW
        lda actframelo,x
        sta FP
        lda actframehi,x
        sta FP+1
        lda #0
        sta ROW
@row:   lda ACTY
        clc
        adc ROW
        tax
        jsr row_pointers
        ldy #8
        lda (FP),y
        sta PHASE
        ldy #3
@px:    lda (FP),y
        beq @next
        eor #$FF
        and (DST),y
        and #$7F
        sta BITS
        iny
        iny
        iny
        iny
        lda (FP),y
        ora BITS
        ora PHASE
        dey
        dey
        dey
        dey
        sta (DST),y
@next:  dey
        bpl @px
        clc
        lda FP
        adc #9
        sta FP
        bcc :+
        inc FP+1
:       inc ROW
        lda ROW
        cmp ACTH
        bne @row
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
        .include "interaction.inc"
        .include "security.inc"
jobx: .byte 0,PANEL-REPAIR,NOJOB-REPAIR,NOJOB-REPAIR
busymsg: .byte 3,17,3,3
roomtrack: .byte WORKSHOP_TRACK,POWER_TRACK,SECURITY_TRACK,LAB_TRACK
actortrack: .byte GUARD_TRACK,SCI_TRACK
labprobe: .byte 28,33,35,38,41    ; by NEAR: nothing, chamber, bay, scientist, consoles
labctx: .byte 31,32,34,37,40
phasetime: .byte 28,6,40,6
phasevis: .byte 0,1,1,1
spotx: .byte 4,25,9               ; scientist spots (byte column, top row)
spoty: .byte 92,100,60
actframelo:                       ; 6 guard frames (270 bytes), 4 scientist (360)
.repeat 6,I
 .byte <(GUARDART+I*270)
.endrepeat
.repeat 4,I
 .byte <(GUARDART+I*360)
.endrepeat
actframehi:
.repeat 6,I
 .byte >(GUARDART+I*270)
.endrepeat
.repeat 4,I
 .byte >(GUARDART+I*360)
.endrepeat
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
        .segment "POWERROOM"   ; disk tracks 7-8 only; streamed into $8000
power_room: .incbin "../art/power-room.hgr"
        .segment "POWERLIT"    ; tracks 9-10
power_lit: .incbin "../art/power-room-lit.hgr"
        .segment "SECURITYROOM" ; tracks 11-12
security_room: .incbin "../art/security-room.hgr"
        .segment "GUARDART"    ; track 13, read to $1000-$1FFF at boot
guard_frames: .incbin "../art/guard-sprites.bin"
guard_end:
.assert guard_frames = GUARDART, lderror, "Guard art must sit at $1800"
.assert guard_end <= $2000, lderror, "Guard art overflows into HGR page 1"
        .segment "LABROOM"     ; tracks 14-15
lab_room: .incbin "../art/lab-room.hgr"
        .segment "SCIART"      ; track 16, read to $1000-$1FFF on entering the lab
sci_frames: .incbin "../art/scientist-sprites.bin"
sci_end:
.assert sci_frames = GUARDART, lderror, "Scientist art must sit at $1800"
.assert sci_end <= $2000, lderror, "Scientist art overflows into HGR page 1"
