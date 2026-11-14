; Disk layout: tracks of everything read after the boot track. It must match
; the order of the memory areas in gbot.cfg (tools/build.py checks it).
CODE_TRACKS=3                 ; tracks 1-3: code and tables (-> $6000, then LC)
POOL_TRACK=4                  ; stamp pool (boot): -> LC bank 1 $D000-$DFFF
WORKSHOP_TRACK=5              ; 5-6 workshop room (boot), 7-8 G-Bot's frames
WORKAUX_TRACK=9               ; workshop aux (boot): messages
POWERAUX_TRACK=10             ; power aux: messages, dark room stamps
GUARD_TRACK=11                ; security aux: messages, guard frames, stamps
SCI_TRACK=12                  ; lab aux: messages, scientist frames, stamps
FREE_TRACK=13                 ; 13-34 free
