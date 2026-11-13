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
ACTLOADED=$9E                 ; whose aux track is at $1000-$1FFF (room 0-3):
                              ; that room's message bank and actor frames
ACTX=$9F                      ; current room's actor: byte column, top row,
ACTY=$A0                      ;   height, frame index, visible
ACTH=$A1
ACTSHOW=$A2
ACTVIS=$A3
GOLDY=$A4                     ; actor top row last drawn on page 0 / page 1
SCSPOT=$A6                    ; scientist: spot 0-2, phase timer, phase
SCTIMER=$A7
SCPHASE=$A8                   ; 0 gone, 1 flickering in, 2 here, 3 flickering out
CONSOLE=$A9                   ; lab console: 0 drifting, 1 diagnosed, 2 tuning, 3 in phase
TUNESTEP=$AA                  ; tuning: phase 0-2, cursor 0-14
TUNEPOS=$AB
TALK=$AC                      ; the scientist is talking: she holds still, G-Bot listens
LOCKOUT=$AD                   ; frames after a door during which keys are dropped
LOCK_FRAMES=4
ROOMTRK=$AE                   ; transition: the new room's first track
SLOT=$2B                      ; boot loader: drive slot * 16
CURPH=$3C                     ; boot loader: head position (half-tracks)
SFIRST=$4A                    ; boot loader: sector range for LOADONE
SEND=$4B
SPUN=$4C                      ; boot loader: motor already running
RAWHI=$4E                     ; boot loader: 8K raw-nibble area (hidden page)
MASKBUF=$1200                 ; 308 shifted opacity bytes (not inverse masks)
DATABUF=$1000                 ; 308 shifted pixels
PHASEBUF=$1400                ; 44 phase bytes
GUARDART=$1800                ; actor frames (guard or scientist) from the aux track
LINEBUF=$1140                 ; 40 glyph numbers: the status line being drawn
BANK=$1440                    ; this room's messages, from its aux track
LOADROOM=$0805                ; resident boot-loader entry: A=track, Y=page
LOADONE=$0808                 ; same, sectors SFIRST..SEND-1 of one track
MOTOROFF=$080B                ; the motor runs across one door's reads
WORKSHOP_TRACK=3
WORKAUX_TRACK=7               ; each room's aux track sits beside its room
POWER_TRACK=8
POWERLIT_TRACK=10
POWERAUX_TRACK=12
STAMP_ROOM=2                  ; security: drawn from stamps on its aux track
GUARD_TRACK=13                ; (its aux track: bank, guard frames, stamps)
LAB_TRACK=14
SCI_TRACK=16
STAMPLIB=$1000                ; stamp count, address lows, highs, then the script
DOOR_X0=110                   ; workshop/power doorway column (PX), inclusive
DOOR_X1=134
GY=93                         ; guard top row; feet on y=122
GXMIN=2
GXMAX=30
GSTEP=3                       ; ticks per one-byte guard step
SPAWNX=224                    ; security-room entry checkpoint
SPAWNY=104

        .export entry, main, code_end, transition, stamps, st_next
        .segment "CODE"
entry:  cld
        sei
        ldx $2B
        lda $C088,x            ; motor off; only room changes read the disk
        bit $C051              ; hide setup in text mode
        lda #0
        ldx #$5D
@state: sta $50,x
        dex
        bpl @state
        lda #GXMIN
        sta GX
        ; ACTLOADED=0: boot read the workshop's aux track (its message bank)
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
        lda LOCKOUT            ; just through a door: drop anything typed
        beq :+
        dec LOCKOUT
        lda $C000              ; (read, then clear: drops a key however it
        bit $C010              ; was latched, even by a lazy emulator queue)
        rts
:       lda $C000
        bmi :+
        rts
:
        bit $C010
        ldy ROOM
        ldx jobx,y
        ldy REPAIR,x
        cpy #2
        bne :+
        rts                    ; a repair/fit in progress ignores keys
:       and #$7F
        ldy ROOM
        cpy #3
        bne :+
        jsr labkeys            ; console tuning / dialogue; C=1 key used
        bcs @done
        ldy ROOM               ; (labkeys keeps A and X otherwise)
        ldx jobx,y
:        cmp #$1B
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

; Lab console keys. In: A = key (7-bit). Out: C=1 when used up.
labkeys:
        ldy TALK
        bne @used              ; she is talking: G-Bot listens
        ldy CONSOLE
        cpy #2
        beq @tune
        cpy #1
        bne @pass
        cmp #$1B
        beq @cancel
        pha
        and #$DF
        cmp #'R'
        bne @notr
        pla
        lda #2                 ; R: start tuning, phase 1
        sta CONSOLE
        lda #0
        sta TUNESTEP
        sta FEEDBACK
        sta BURST
        lda #TUNE_START
        sta TUNEPOS
@used:  sec
        rts
@notr:  pla
@pass:  clc
        rts
@cancel:lda #0
        sta CONSOLE
        lda #48                ; TUNING CANCELLED. DRIFT CONTINUES.
        ldx #48
        bne @say
@tune:  cmp #$1B
        beq @cancel
        and #$DF
        cmp #'A'
        beq @left
        cmp #$08
        beq @left
        cmp #'D'
        beq @right
        cmp #$15
        beq @right
        cmp #'R'
        bne @used              ; other keys do nothing while tuning
        ldx TUNESTEP
        lda TUNEPOS
        cmp tunetarget,x
        beq @hit
        lda #47                ; OUT OF PHASE - KEEP TUNING
        ldx #24
        bne @say
@hit:   inx
        stx TUNESTEP
        cpx #3
        beq @solved
        lda #TUNE_START
        sta TUNEPOS
        lda #46                ; LOCKED! NEXT PHASE...
        ldx #20
        bne @say
@solved:lda #3                 ; in phase: she can hold still long enough to talk
        sta CONSOLE
        lda #1
        sta TALK
        lda #2
        sta SCSPOT
        sta SCPHASE
        lda #FIRST_DIALOG
        ldx #DIALOG_TIME
@say:   sta MESSAGE
        stx FEEDBACK
        sec
        rts
@left:  lda TUNEPOS
        beq @used
        dec TUNEPOS
        bpl @moved
@right: lda TUNEPOS
        cmp #TUNE_LAST
        beq @used
        inc TUNEPOS
@moved: lda #0
        sta FEEDBACK
        sec
        rts

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
        ldx NEXTROOM
        cpx ROOM
        beq @nodoor            ; (the fuse fit reloads the same room)
        ldy SLOT               ; start the drive now: it spins up while the
        lda $C08A,y            ; status line and chirp go out
        lda $C089,y
        lda $C08E,y            ; (read mode; the loader never writes)
        lda entermsg,x         ; ENTERING <ROOM>... from the current bank,
        sta MESSAGE            ; on both pages at once, before any disk read
        jsr draw_status
        jsr copy_status
        jsr door_sound
        lda ROOM
        bne @spin
        jsr open_door          ; workshop: the rear door slides open (shown on
        jsr show_one           ; one page; no pause in the doorway)
        jmp @spun
@spin:  lda #$90               ; rest of the ~90 ms spin-up (~54 ms)
        jsr $FCA8
@spun:  lda #1
        sta SPUN               ; the loader need not wait again
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
@load:  sta ROOMTRK
        lda PAGE               ; the loader's raw nibbles go to the hidden page
        eor #1
        tax
        lda pagehigh,x
        sta RAWHI
        ldx ROOM
        cpx #STAMP_ROOM        ; a stamp-built room: one aux track, then draw
        bne @full
        stx ACTLOADED
        jsr load_aux
        jsr MOTOROFF
        jsr stamps
        jmp @drawn
@full:  ldx ROOM               ; this room's messages and actor frames too?
        cpx ACTLOADED
        beq @bgonly
        stx ACTLOADED
        lda CURPH              ; nearest first: every aux track lies above
        lsr a                  ; its room, so coming down from higher
        cmp ROOMTRK            ; tracks read the aux track first
        bcc @bgfirst
        jsr load_aux
@bgonly:jsr load_bg
        jmp @loaded
@bgfirst:
        jsr load_bg
        jsr load_aux
@loaded:jsr MOTOROFF
@drawn: lda POWERUP
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
        jsr show_room
        lda $C000
        bit $C010              ; keys pressed during the load are discarded,
        lda #LOCK_FRAMES       ; and a few frames more after arrival
        sta LOCKOUT
        rts
load_bg:lda ROOMTRK
        ldy #>room
        jmp LOADROOM
load_aux:
        ldx ROOM
        lda auxfirst,x         ; sectors 0-3 are scratch (or stamps); read to auxend-1
        sta SFIRST
        lda auxend,x
        sta SEND
        lda auxtrack,x
        ldy #$10
        jmp LOADONE
; ---- stamps: draw a stamp-built room into $8000 from its aux track's script
; (format: tools/gen_stamps.py). Runs once at the door, before the scratch
; area at $1000-$143F (which holds the script) is used again.
SP=SRC                         ; script pointer
LE=BG                          ; line: error (16-bit)
D1=MP                          ; 2*ady
D2=DP                          ; 2*adx
LCOL=SL                        ; line start column, bit, row; pixel count
LBIT=SL+1
LY=SH
LN=SH+1
YV=ROW                         ; current row / column / counters
CV=COL
CNTV=CM
IDXV=CD
LF=RAW                         ; line flags
BITV=BITS                      ; current bit, x parity
PARV=PHASE
LADY=OX
LADX=OY                        ; (2 bytes: OY, TMPX)
TMPV=TMPY
STBUF=$0C00                    ; 40 bytes the loader no longer uses (not $1140:
                               ; the script itself lives in that scratch area)
HIV=SHIFT                      ; (render scratch) palette bit for this line
SKIPV=XB                       ; (render scratch) parity not drawn
stamps: lda #0
        tay
@clr:
.repeat 32,PG
        sta room+PG*256,y
.endrepeat
        iny
        bne @clr
        lda STAMPLIB           ; script = STAMPLIB + 1 + 2 * count
        asl a
        adc #<(STAMPLIB+1)
        sta SP
        lda #>(STAMPLIB+1)
        adc #0
        sta SP+1
st_next:ldy #0
        lda (SP),y
        bne :+
        rts
:       asl a
        tax
        lda st_ops-2,x
        sta FP
        lda st_ops-1,x
        sta FP+1
        jmp (FP)
st_ops: .word st_text,st_line,st_row,st_block,st_stamp,st_repeat
st_adv: clc                    ; SP += A
        adc SP
        sta SP
        bcc :+
        inc SP+1
:       jmp st_next
st_rowptr:                     ; DST = row X of the canonical room, + CV
        lda rowlo,x            ; (row starts + 39 never cross a page)
        clc
        adc CV
        sta DST
        lda rowhi,x
        ora #$80
        sta DST+1
        rts
st_params:                     ; YV, CV, CNTV, IDXV = script bytes 1-4;
        ldy #1                 ; FP = the script + 5
        lda (SP),y
        sta YV
        iny
        lda (SP),y
        sta CV
        iny
        lda (SP),y
        sta CNTV
        iny
        lda (SP),y
        sta IDXV
        lda SP
        clc
        adc #5
        sta FP
        lda SP+1
        adc #0
        sta FP+1
        rts
st_text:jsr st_params          ; row, col, n; glyphs from script byte 4
        lda CNTV               ; copy the glyphs out to STBUF
        clc
        adc #4
        sta TMPV
        ldy #4
:       lda (SP),y
        sta STBUF-4,y
        iny
        cpy TMPV
        bne :-
        lda #0
        sta IDXV               ; glyph row 0-4
@r:     lda YV
        clc
        adc IDXV
        tax
        jsr st_rowptr
        ldx IDXV
        lda fontlo,x
        sta FP
        lda fonthi,x
        sta FP+1
        ldx #0
@k:     ldy STBUF,x
        lda (FP),y
        pha
        txa
        tay
        pla
        sta (DST),y
        inx
        cpx CNTV
        bne @k
        inc IDXV
        lda IDXV
        cmp #5
        bne @r
        lda CNTV
        clc
        adc #4
        jmp st_adv
st_row: jsr st_params          ; row, col, len, period, pattern
        ldy #0
:       lda (FP),y             ; pattern -> STBUF
        sta STBUF,y
        iny
        cpy IDXV
        bne :-
        ldx YV
        jsr st_rowptr
        ldx #0
        ldy #0
@k:     lda STBUF,x
        sta (DST),y
        iny
        inx
        cpx IDXV
        bne :+
        ldx #0
:       cpy CNTV
        bne @k
        lda IDXV
        clc
        adc #5
        jmp st_adv
st_block:jsr st_params         ; row, col, width, height, bytes
@r:     ldx YV
        jsr st_rowptr
        ldy CNTV
        dey
@k:     lda (FP),y
        sta (DST),y
        dey
        bpl @k
        inc YV
        dec IDXV
        bne @r
        lda CNTV
        clc
        adc #5
        jmp st_adv
st_stamp:                      ; id, row, col
        ldy #1
        lda (SP),y
        tax                    ; id
        iny
        lda (SP),y
        sta YV
        iny
        lda (SP),y
        sta TMPV               ; stamp's left column
        inx                    ; lo[id] is at STAMPLIB+1+id (page $10)
        lda STAMPLIB&$FF00,x
        sta FP
        txa
        clc
        adc STAMPLIB           ; + count -> hi[id]
        tax
        lda STAMPLIB&$FF00,x
        sta FP+1
        ldy #0
        lda (FP),y
        sta CNTV               ; rows
        iny
@span:  lda (FP),y             ; column offset
        clc
        adc TMPV
        sta CV
        iny
        lda (FP),y
        sta IDXV               ; length (+$80: another span on this row)
        iny
        tya                    ; FP -> the span's bytes
        clc
        adc FP
        sta FP
        bcc :+
        inc FP+1
:       ldx YV
        jsr st_rowptr
        lda IDXV
        and #$7F
        tay
        beq @done
        dey
@copy:  lda (FP),y
        sta (DST),y
        dey
        bpl @copy
@done:  lda IDXV
        and #$7F
        tay                    ; next span starts right after these bytes
        lda IDXV
        bmi @span
        inc YV
        dec CNTV
        bne @span
        lda #4
        jmp st_adv
st_repeat:                     ; count, dx: the last line again, dx pixels on
        ldy #1
        lda (SP),y
        sta IDXV               ; (st_draw counts pixels in CNTV)
@again: ldy #2
        lda (SP),y
        tax
@step:  inc LBIT
        lda LBIT
        cmp #7
        bne :+
        lda #0
        sta LBIT
        inc LCOL
:       dex
        bne @step
        jsr st_draw
        dec IDXV
        bne @again
        lda #3
        jmp st_adv
st_line:ldy #1                 ; col, bit, y, n, adx (2), ady, flags
        lda (SP),y
        sta LCOL
        iny
        lda (SP),y
        sta LBIT
        iny
        lda (SP),y
        sta LY
        iny
        lda (SP),y
        sta LN
        iny
        lda (SP),y
        sta LADX
        iny
        lda (SP),y
        sta LADX+1
        iny
        lda (SP),y
        sta LADY
        iny
        lda (SP),y
        sta LF
        jsr st_draw
        lda #9
        jmp st_adv
; Bresenham as Pillow draws it. Per pixel: OR the palette bit (blue lines)
; and, if this x parity is drawn, the pixel's bit.
st_draw:lda LADY               ; D1 = 2*ady, D2 = 2*adx
        asl a
        sta D1
        lda #0
        rol a
        sta D1+1
        lda LADX
        asl a
        sta D2
        lda LADX+1
        rol a
        sta D2+1
        lda LF                 ; e = x-major ? 2ady-adx : 2adx-ady
        and #2
        beq @ym
        sec
        lda D1
        sbc LADX
        sta LE
        lda D1+1
        sbc LADX+1
        sta LE+1
        jmp @go
@ym:    sec
        lda D2
        sbc LADY
        sta LE
        lda D2+1
        sbc #0
        sta LE+1
@go:    lda LF                 ; HIV: palette bit to OR in
        and #$10
        asl a
        asl a
        asl a
        sta HIV
        ldx #$FF               ; SKIPV: the parity that is not drawn
        lda LF
        and #4
        beq :+
        ldx #1                 ; even pixels only
:       lda LF
        and #8
        beq :+
        ldx #0                 ; odd pixels only
:       stx SKIPV
        lda LBIT
        sta BITV
        clc
        adc LCOL
        and #1
        sta PARV               ; x parity (x = 7*col + bit)
        lda LY
        sta YV
        lda LN
        sta CNTV
        lda #0
        sta CV
        ldx YV
        jsr st_rowptr          ; DST = row start; Y is the column
        ldy LCOL
@pix:   lda (DST),y
        ora HIV
        ldx PARV
        cpx SKIPV
        beq :+
        ldx BITV
        ora st_bit,x
:       sta (DST),y
        lda LF
        and #2
        beq @ymaj
        lda LE+1               ; x-major: if e>=0 { y+=ys; e-=2adx }
        bmi :+
        jsr st_ystep
        sec
        lda LE
        sbc D2
        sta LE
        lda LE+1
        sbc D2+1
        sta LE+1
:       clc
        lda LE
        adc D1
        sta LE
        lda LE+1
        adc D1+1
        sta LE+1
        jsr st_xstep
        jmp @nextpix
@ymaj:  lda LE+1               ; y-major: if e>=0 { x+=xs; e-=2ady }
        bmi :+
        jsr st_xstep
        sec
        lda LE
        sbc D1
        sta LE
        lda LE+1
        sbc D1+1
        sta LE+1
:       clc
        lda LE
        adc D2
        sta LE
        lda LE+1
        adc D2+1
        sta LE+1
        jsr st_ystep
@nextpix:
        dec CNTV
        bne @pix
        rts
st_ystep:                      ; (keeps Y, the column)
        lda LF
        and #$20
        bne :+
        inc YV
        bne @ptr
:       dec YV
@ptr:   ldx YV
        lda rowlo,x
        sta DST
        lda rowhi,x
        ora #$80
        sta DST+1
        rts
st_xstep:                      ; Y is the column
        lda PARV
        eor #1
        sta PARV
        lda LF
        and #1
        bne @left
        inc BITV
        lda BITV
        cmp #7
        bne :+
        lda #0
        sta BITV
        iny
:       rts
@left:  dec BITV
        bpl :+
        lda #6
        sta BITV
        dey
:       rts
st_bit: .byte 1,2,4,8,16,32,64
; A rising chirp on the speaker, ~22 ms: the door opens.
door_sound:
        ldy #$60
@tone:  lda $C030
        tya
        tax
@wait:  dex
        bne @wait
        dey
        cpy #$18
        bne @tone
        rts
; Status rows 177-181 of the canonical room -> both HGR pages.
copy_status:
        ldx #177
@row:   lda rowlo,x
        sta BG
        sta DST
        sta SRC
        lda rowhi,x
        ora #$80
        sta BG+1
        and #$1F
        ora #$20
        sta DST+1
        eor #$60
        sta SRC+1
        ldy #39
@copy:  lda (BG),y
        sta (DST),y
        sta (SRC),y
        dey
        bpl @copy
        inx
        cpx #182
        bne @row
        rts

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
        lda TALK
        bne sci_show
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
        cpx #4
        bne :+
        ldx #58                ; CONSOLE: IN PHASE. NO FULL POWER!
        lda CONSOLE
        cmp #3
        beq @say
        lda #1                 ; diagnosed: PHASE DRIFT, offer R to tune
        sta CONSOLE
        ldx #41
        lda #48
        stx MESSAGE
        sta FEEDBACK
        rts
:       lda labprobe,x
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
        ldx #96
        cmp #FIRST_DIALOG      ; dialogue lines are a little quicker
        bcc @long
        ldx #DIALOG_TIME
@long:  stx FEEDBACK
        cmp #RELEASE_LINE
        bne :+
        lda #0                 ; mid-word, she slips out of phase again
        sta TALK
        lda #3
        sta SCPHASE
        lda #6
        sta SCTIMER
:       lda MESSAGE
        jmp @message
@context:
        lda ROOM
        beq @workroom
        cmp #1
        beq @powerroom
        cmp #3
        bne :+
        jmp @labroom
:       lda #23                ; SECURITY UNIT REBOOTING...
        ldx GSTATE
        cpx #1
        beq @msg_far
        lda #26                ; SECURITY DESK: SPACE TO PROBE
        ldx NEAR
        bne @msg_far
        lda #22                ; SECURITY ROOM - MIND THE GUARD BOT
@msg_far:
        jmp @message
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
@labroom:
        lda CONSOLE
        cmp #2
        bne @lr1
        lda TUNESTEP           ; the tuning meter: $80 + phase*16 + cursor
        asl a
        asl a
        asl a
        asl a
        ora TUNEPOS
        ora #$80
        bne @message
@lr1:   cmp #1
        bne @lr2
        lda NEAR
        cmp #4
        bne @lrc
        lda #44                ; PHASE DRIFT: R TO TUNE / ESC CANCEL
        bne @message
@lrc:   lda #0                 ; walking away cancels the diagnosis
        sta CONSOLE
@lr2:   ldx NEAR
        lda labctx,x
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
        jsr draw_status
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

; Status text: message A from this room's disk bank (or the tuning meter for
; A >= $80) as 40 centred glyph numbers in LINEBUF.
fetch:  sta COL
        ldy #39
        lda #0
@clr:   sta LINEBUF,y
        dey
        bpl @clr
        lda COL
        bmi meter
        lda #<BANK
        sta SRC
        lda #>BANK
        sta SRC+1
@scan:  ldy #0
        lda (SRC),y
        cmp COL
        beq @found
        cmp #$FF
        beq @none
        cmp #$FE
        beq @jump
        iny
        lda (SRC),y            ; skip id, length, text
        clc
        adc #2
        adc SRC
        sta SRC
        bcc @scan
        inc SRC+1
        bne @scan
@jump:  iny
        lda (SRC),y
        tax
        iny
        lda (SRC),y
        sta SRC+1
        stx SRC
        jmp @scan
@found: iny
        lda (SRC),y
        sta TMPX
        lda #40
        sec
        sbc TMPX
        lsr a
        tax
        ldy #2
@copy:  lda (SRC),y
        sta LINEBUF,x
        inx
        iny
        dec TMPX
        bne @copy
@none:  rts
meter:  lda #METER
        jsr fetch
        lda TUNESTEP
        clc
        adc #GLYPH_1
        sta LINEBUF+METER_STEP
        ldx TUNESTEP
        lda tunetarget,x
        tax
        lda #GLYPH_BAR
        sta LINEBUF+METER_CELL0,x
        ldy #GLYPH_O
        cpx TUNEPOS
        bne :+
        ldy #GLYPH_STAR
:       ldx TUNEPOS
        tya
        sta LINEBUF+METER_CELL0,x
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
; Render status line A (message id or meter) into the canonical room's rows 177-181.
draw_status:
        jsr fetch
        lda #<LINEBUF
        sta SRC
        lda #>LINEBUF
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
        rts

show_room:
        jsr show_one
        lda PAGE
        eor #1
        sta PAGE
        jsr fill_page
        jsr render
        ldx PAGE
        lda $C054,x
        rts
show_one:                      ; draw the hidden page whole and show it
        lda PAGE
        eor #1
        sta PAGE
        jsr fill_page
        jsr prepare
        jsr render
        ldx PAGE
        lda $C054,x
        rts
fill_page:                     ; canonical room -> PAGE: 32 pages per pass
        lda PAGE               ; of Y, unrolled (~9 cycles a byte)
        beq :+
        jmp @p2
:       ldy #0
@c1:
.repeat 32,PG
        lda room+PG*256,y
        sta $2000+PG*256,y
.endrepeat
        iny
        beq :+
        jmp @c1
:       rts
@p2:    ldy #0
@c2:
.repeat 32,PG
        lda room+PG*256,y
        sta $4000+PG*256,y
.endrepeat
        iny
        beq :+
        jmp @c2
:       rts

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
        .include "auxend.inc"
        .include "security.inc"
jobx: .byte 0,PANEL-REPAIR,NOJOB-REPAIR,NOJOB-REPAIR
busymsg: .byte 3,17,3,3
roomtrack: .byte WORKSHOP_TRACK,POWER_TRACK,0,LAB_TRACK
auxtrack: .byte WORKAUX_TRACK,POWERAUX_TRACK,GUARD_TRACK,SCI_TRACK
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
        .segment "POWERROOM"   ; disk tracks 8-9; streamed into $8000
power_room: .incbin "../art/power-room.hgr"
        .segment "POWERLIT"    ; tracks 10-11
power_lit: .incbin "../art/power-room-lit.hgr"
        .segment "SECAUX"      ; track 13: security messages, guard frames and
                               ; the stamp library + script its room is drawn from
        .incbin "../art/aux-security.bin"
        .segment "LABROOM"     ; tracks 14-15
lab_room: .incbin "../art/lab-room.hgr"
        .segment "LABAUX"      ; track 18: lab messages + scientist frames
        .incbin "../art/aux-lab.bin"
        .segment "WORKAUX"     ; track 7: workshop messages (read at boot)
        .incbin "../art/aux-workshop.bin"
        .segment "POWERAUX"    ; track 12: power room messages
        .incbin "../art/aux-power.bin"
