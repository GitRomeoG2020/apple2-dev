; Disk layout: tracks of everything read after the boot track. It must match
; the order of the memory areas in gbot.cfg (tools/build.py checks it).
CODE_TRACKS=3                 ; tracks 1-3: code and tables (-> $6000, then LC)
POOL_TRACK=4                  ; stamp pool (boot): -> LC bank 1 $D000-$DFFF
SPRITE_TRACK=5                ; 5-6 G-Bot's frames (boot) -> $A000
WORKAUX_TRACK=7               ; workshop aux (boot): messages, stamps
POWERAUX_TRACK=8              ; power aux: messages, dark room stamps
GUARD_TRACK=9                 ; security aux: messages, guard frames, stamps
SCI_TRACK=10                  ; lab aux: messages, scientist frames, stamps
SUB_TRACK=11                  ; substation aux: messages, stamps
WINGB_TRACK=12                ; wing B aux: messages, stamps
CHAPTER_TRACK=13              ; 13-14 the chapter: code, messages, hints, patches (boot -> $6000)
FREE_TRACK=15                 ; 15-34 free
