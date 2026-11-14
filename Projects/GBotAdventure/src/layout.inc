; Disk layout: tracks of everything read after the boot track. It must match
; the order of the memory areas in gbot.cfg (tools/build.py checks it).
CODE_TRACKS=3                 ; tracks 1-3: code and tables (-> $6000, then LC)
WORKSHOP_TRACK=4              ; 4-5 workshop room (boot), 6-7 G-Bot's frames
WORKAUX_TRACK=8               ; workshop aux (boot): messages
POWERLIT_TRACK=9              ; 9-10 lit power room
POWERAUX_TRACK=11             ; power aux: messages, dark room stamps
GUARD_TRACK=12                ; security aux: messages, guard frames, stamps
LAB_TRACK=13                  ; 13-14 lab
SCI_TRACK=15                  ; lab aux: messages, scientist frames
FREE_TRACK=16                 ; 16-34 free
