#!/usr/bin/env python3
"""Original playable workshop and 42x44 G-Bot frames. Pillow is ART-ONLY.
Checked-in native binaries let ca65 builds run without Python/Pillow on Windows.
Sprite rows: 6 opaque bytes, 6 pixel bytes, one shared phase byte.
Every x in the engine is even, preserving artifact color parity when shifting.
"""
from pathlib import Path
import math
from PIL import Image, ImageDraw
from gen_concept import Paint, K,V,G,B,O,T,encode,decode,row_offset,FONT
ROOT=Path(__file__).resolve().parents[1]
FONT.update({
 'C':['01111','10000','10000','10000','01111'],
 'D':['11110','10001','10001','10001','11110'],
 'F':['11111','10000','11110','10000','10000'],
 'H':['10001','10001','11111','10001','10001'],
 'L':['10000','10000','10000','10000','11111'],
 'M':['10001','11011','10101','10001','10001'],
 'N':['10001','11001','10101','10011','10001'],
 'U':['10001','10001','10001','10001','01110'],
 'W':['10001','10001','10101','11011','10001'],
 'K':['10001','10010','11100','10010','10001'],
 'V':['10001','10001','10001','01010','00100'],
 'Y':['10001','01010','00100','00100','00100'],
 '+':['000','010','111','010','000'],
 ':':['0','1','0','1','0'],
 '/':['00001','00010','00100','01000','10000'],
})
SW,SH=42,44
CLEAR=6
# Every room's front edge. The rows below it hold the HUD, baked into each
# room's art: a one-row strip (room name and that room's clock, 169-173), the
# engine's status line (177-181) and the controls (186-190).
FLOOR=164
CLOCKS={'WORKSHOP':'12:15','POWER ROOM':'9:41','SECURITY':'2:53','THE LAB':'6:02','SUBSTATION':'11:59','WING B':'3:07'}

def clock_hands(p,cx,cy,name,rh,rm,c=T):
    """Short hour hand, long minute hand (2 px wide so they stay white),
    showing CLOCKS[name]."""
    h,m=map(int,CLOCKS[name].split(':'))
    for a,r in (((h%12+m/60)*30,rh),(m*6,rm)):
        a=math.radians(a)
        p.line([(cx,cy),(cx+round(r*math.sin(a)),cy-round(r*math.cos(a)))],c,2)

CONTROLS='WASD/ARROWS SPACE:PROBE T:TASK'   # the baked controls line
def finish(p,name):
    """Native room bytes plus the baked HUD: strip and controls line."""
    data=bytearray(encode(p.im))
    t=CLOCKS[name]
    strip=' '+name+' '*(38-len(name)-len(t))+t+' '
    for top,text in ((169,strip),(186,CONTROLS)):
        for row,values in enumerate(message_pixels(text)):
            data[row_offset(top+row):row_offset(top+row)+40]=values
    return bytes(data)

def room(online=False):
    p=Paint()
    # Back wall: a deep, quiet workshop rather than a busy neon maze.
    p.line([(6,3),(273,3),(273,FLOOR-5)],B,2)
    p.line([(6,3),(6,FLOOR-4)],B,2)
    p.line([(9,7),(269,7)],T)
    for y in (34,70):
        p.line([(9,y),(271,y)],B)
    for x in (63,139,211):
        p.line([(x,9),(x,69)],B)
    p.line([(9,75),(271,75)],O)
    p.line([(9,80),(271,80)],B)
    # Ceiling conduit and small warm task light.
    p.line([(11,14),(96,14),(96,23)],B,2)
    p.line([(11,13),(94,13)],T)
    p.poly([(86,23),(103,23),(110,28),(79,28)],O)
    p.line([(83,29),(106,29)],T,2)
    # Pegboard tools: open wrench, screwdriver, pliers.
    p.rect((17,37,82,58),K)
    for y in (38,44,50,56):
        for x in range(19,82,8): p.dot(x,y,O)
    p.line([(28,40),(28,51)],T,2)
    p.line([(24,37),(24,40),(28,43),(32,40),(32,37)],T)
    p.rect((44,39,47,45),O); p.line([(45,46),(45,54)],T)
    p.line([(60,38),(64,43),(61,53)],T)
    p.line([(68,38),(64,43),(68,53)],O)
    # Left bench, small oscilloscope, parts tray and sturdy drawers.
    p.poly([(13,66),(84,66),(96,75),(13,75)],O)
    p.line([(13,66),(83,66),(95,74)],T)
    p.rect((14,77,87,81),B)
    p.rect((18,82,66,101),K)
    for y in (83,92):
        p.rect((19,y,65,y+7),B)
        p.line([(21,y),(63,y)],O)
        p.rect((39,y+3,46,y+3),K)
    p.line([(83,81),(83,103)],B,3)
    p.line([(18,101),(66,101)],B)
    p.rect((23,50,52,65),K)
    p.line([(23,65),(23,50),(49,50),(53,54),(53,65)],T)
    p.rect((27,54,45,62),B); p.rect((29,55,43,60),K)
    if online:
        p.line([(29,59),(32,59),(34,56),(36,60),(38,57),(41,58)],G)
    else:
        p.line([(30,55),(40,60)],O); p.line([(30,60),(40,55)],O)
    p.rect((48,55,50,56),O); p.rect((48,60,50,61),T)
    p.poly([(61,69),(76,69),(82,73),(63,73)],G)
    for x in (65,71,77): p.line([(x,69),(x+2,72)],K)
    # Front-facing service socket: probe reaches it from the bench's apron.
    p.rect((70,86,79,96),K)
    p.line([(71,87),(78,87),(78,95),(71,95),(71,87)],G if online else O)
    p.line([(74,89),(74,93)],T)
    if online:
        p.line([(12,13),(76,13)],G,2)
        p.line([(83,30),(106,30)],T,2)
    # Rear door -- decoration only in this first, single-room milestone.
    p.rect((113,28,172,74),K)
    p.line([(113,74),(113,28),(172,28),(172,74)],B,2)
    p.line([(117,72),(117,32),(168,32),(168,72)],V)
    p.line([(142,33),(142,71)],B)
    p.rect((159,51,162,54),G if online else O)
    p.rect((130,20,156,24),K)
    p.text(132,20,'01',O)
    # Clock, sleeping terminal, fan vents and cable loops.
    p.ellipse((183,18,205,34),B); p.ellipse((186,20,202,32),K)
    clock_hands(p,194,26,'WORKSHOP',3,5)
    p.rect((225,40,263,109),K)
    p.line([(225,109),(225,40),(263,40),(263,109)],B,2)
    p.line([(229,44),(259,44),(259,105)],V)
    p.rect((232,49,252,64),B); p.rect((235,52,249,61),K)
    p.line([(237,58),(244,58)],G)
    for y in (71,75,79): p.line([(233,y),(253,y)],B)
    p.rect((233,87,236,89),O)
    p.line([(241,88),(252,88)],B)
    p.line([(233,99),(253,99)],B)
    p.line([(223,53),(215,53),(215,86),(221,93)],B)
    # Floor perspective, subtle seams. Movable sprite covers these cleanly.
    for x in (-210,-58,85,225,370,520):
        p.line([(140+(x-140)//5,81),(x,FLOOR+1)],B)
    for y in (93,113,137,FLOOR): p.line([(9,y),(271,y)],B)
    p.line([(8,FLOOR),(272,FLOOR)],O)
    # Rubber service mat, spare screws, coiled cable. None block movement.
    p.poly([(112,113),(170,113),(183,148),(99,148)],K)
    p.line([(112,113),(170,113),(183,148),(99,148),(112,113)],V)
    for y in (120,127,134,141): p.line([(110,y),(172,y)],B)
    p.line([(49,104),(50,111),(68,115),(80,120),(77,127),(61,129),(59,135),(74,139)],O)
    p.rect((26,142,31,144),B); p.line([(28,141),(29,141)],T)
    p.line([(208,144),(216,143),(220,146)],O)
    return finish(p,'WORKSHOP')

# Three logical columns, each emitted as a pair of lit HGR bits: real white,
# not alternating artifact colors. One seven-pixel byte per character.
REPAIR_FONT={
 'A':['010','101','111','101','101'], 'B':['110','101','110','101','110'],
 'C':['011','100','100','100','011'], 'D':['110','101','101','101','110'],
 'E':['111','100','110','100','111'], 'F':['111','100','110','100','100'],
 'G':['011','100','101','101','011'], 'H':['101','101','111','101','101'],
 'I':['111','010','010','010','111'], 'J':['001','001','001','101','010'],
 'K':['101','101','110','101','101'], 'L':['100','100','100','100','111'],
 'M':['101','111','111','101','101'], 'N':['101','111','111','111','101'],
 'O':['010','101','101','101','010'], 'P':['110','101','110','100','100'],
 'Q':['010','101','101','111','011'], 'R':['110','101','110','101','101'],
 'S':['011','100','010','001','110'], 'T':['111','010','010','010','010'],
 'U':['101','101','101','101','111'], 'V':['101','101','101','101','010'],
 'W':['101','101','111','111','101'], 'X':['101','101','010','101','101'],
 'Y':['101','101','010','010','010'], 'Z':['111','001','010','100','111'],
 ' ':['000']*5, '-':['000','000','111','000','000'],
 '/':['001','001','010','100','100'], ':':['000','010','000','010','000'],
 '.':['000','000','000','000','010'], '!':['010','010','010','000','010'],
 ',':['000','000','000','010','100'],
 '0':['111','101','101','101','111'], '1':['010','110','010','010','111'],
 '2':['111','001','111','100','111'], '3':['111','001','011','001','111'],
 '4':['101','101','111','001','001'], '5':['111','100','111','001','111'],
 '6':['111','100','111','101','111'], '7':['111','001','010','010','010'],
 '8':['111','101','111','101','111'], '9':['111','101','111','001','111'],
 '?':['111','001','010','000','010'], "'":['010','010','000','000','000'],
 '|':['010','010','010','010','010'], '*':['000','101','010','101','000'],
}
# Glyph numbers as the engine stores them (space is glyph 0).
GLYPHS=sorted(REPAIR_FONT,key=lambda ch:(ch!=' ',ch))
# Status line text, indexed by MESSAGE ($85). 0-7 workshop, 8-12 power room/door.
MESSAGES=[
    'WORKBENCH OFFLINE - CHECK LEFT BENCH',
    'WORKBENCH: SPACE TO INSPECT',
    'LOOSE LEAD: R RECONNECT / ESC CANCEL',
    'RECONNECTING... HOLD TIGHT LITTLE BOT',
    'WORKSHOP ONLINE - NICE WORK G-BOT',
    'NO CONTACT - TRY LEFT BENCH SOCKET',
    'TERMINAL ONLINE - ALL SET HERE',
    'MOVE CLOSER TO LEFT BENCH SOCKET',
    'DARK POWER ROOM - EYES ADJUSTING...',
    'BREAKER PANEL: SPACE TO PROBE',
    'NO POWER - FIND FUSE',
    'TOO DARK - NOTHING TO PROBE HERE',
    'DOOR SEALED - FIX WORKBENCH FIRST',
    'OLD LOCKER: SPACE TO PROBE',             # 13
    'FOUND A FUSE! TAKE IT TO THE PANEL',     # 14
    'LOCKER IS EMPTY NOW',                    # 15
    'FUSE FITS: R TO FIT / ESC CANCEL',       # 16
    'FITTING FUSE... STAND CLEAR',            # 17
    'POWER RESTORED - WEST DOOR OPEN',        # 18
    'POWER ROOM ONLINE - WEST DOOR OPEN',     # 19
    'PANEL ONLINE - ALL BREAKERS SET',        # 20
    'SECURITY DOOR SEALED - NO POWER',        # 21
    'SECURITY ROOM - MIND THE GUARD BOT',     # 22
    'SECURITY UNIT REBOOTING...',             # 23
    'GUARD: WORK ORDER NOT RECOGNIZED',       # 24
    'SECURITY DESK: SPACE TO PROBE',          # 25 (spare prompt)
    'SECURITY DESK: SPACE TO PROBE',          # 26
    'MONITORS: EVERY CAMERA SHOWS NOBODY',    # 27
    'NOTHING TO PROBE HERE',                  # 28
    'LAB DOOR LOCKED - TRY THE DESK',         # 29
    '...AND THE LAB DOOR CLICKS OPEN',        # 30
    'THE LAB: SOMETHING IS STILL RUNNING',    # 31
    'TIME CHAMBER: SPACE TO PROBE',           # 32
    'CHAMBER: LOOP ACTIVE. DO NOT DISTURB',   # 33
    'PARKING BAY: WELCOME BACK, G-BOT',       # 34
    'BAY: G-BOT. LAST SERVICE: TONIGHT.',     # 35
    '...AND TONIGHT. AND TONIGHT.',           # 36
    'SCIENTIST! SPACE TO SAY HELLO',          # 37
    'SCIENTIST: ...BEFORE THE MORNING SHI-',  # 38
    '...AND SHE FLICKERED OUT MID-WORD',      # 39
    'CONSOLES: SPACE TO PROBE',               # 40
    'CONSOLE: LOOP 4,817. PHASE DRIFT!',      # 41
    'LAB CLOCK SAYS 6:02. NOBODY AGREES.',    # 42
    '...THE RING HUMS. IT KNOWS YOU.',        # 43
    # The time-chamber console: diagnose, tune three phases, then she talks.
    'PHASE DRIFT: R TO TUNE / ESC CANCEL',    # 44 prompt
    'PHASE 1/3 ...............  R LOCK',      # 45 meter template (engine fills it)
    'LOCKED! NEXT PHASE...',                  # 46
    'OUT OF PHASE - KEEP TUNING',             # 47
    'TUNING CANCELLED. DRIFT CONTINUES.',     # 48
    'SCIENTIST: YOU CAN SEE ME? G-BOT!',      # 49 dialogue
    'THE EXPERIMENT WORKED. TOO WELL.',       # 50
    'WE ARE STUCK IN ONE NIGHT.',             # 51
    'OVER AND OVER. THE COFFEE NEVER ENDS.',  # 52
    'YOU WERE PARKED IN THE CHAMBER...',      # 53
    '...SO TIME SLID RIGHT OFF YOU!',         # 54
    "DON'T RESTORE FULL POWER -",             # 55
    'IT RUNS AGAIN-',                         # 56 (she flickers out)
    '...FLICKERED OUT. CONSOLE STAYS ON.',    # 57
    'CONSOLE: IN PHASE. NO FULL POWER!',      # 58 re-probe reminder
    'ENTERING WORKSHOP...',                   # 59 door status (shown before
    'ENTERING POWER ROOM...',                 # 60  the disk read, from the
    'ENTERING SECURITY...',                   # 61  bank of the room being
    'ENTERING THE LAB...',                    # 62  left)
    'SOUND ON',                               # 63 M toggles sound
    'SOUND OFF',                              # 64
    # Twist two: full power reruns the experiment. The substation and the choice.
    'ENTERING SUBSTATION...',                 # 65 door status (power room bank)
    'SUBSTATION SEALED - NEEDS LAB OK',       # 66 east door before the console
    'CONSOLE: SUBSTATION UNSEALED. HMM.',     # 67 after her reveal
    'SUBSTATION: THE BIG SWITCH',             # 68 arrival / context
    'MAIN BREAKER: SPACE TO PROBE',           # 69
    'RESTORE FULL POWER?  Y YES / N NO',      # 70 the choice
    'FULL POWER! HERE WE GO AGAIN-',          # 71 restore: the rerun
    'G-BOT REBOOTING... 12:15 AGAIN',         # 72 restore: the wake "door" line
    'G-BOT: ...THAT WAS A BAD IDEA. AGAIN.',  # 73 waking in the workshop
    'G-BOT: ...STILL A BAD IDEA. AGAIN.',     # 74 (second loop on)
    'G-BOT: NO. SHE SAID NO FULL POWER.',     # 75 refuse
    '...BUT THIS TRICKLE LEAD MIGHT HELP.',   # 76
    'NEW TASK: TRICKLE LEAD TO THE CHAMBER',  # 77
    'BREAKER STAYS OFF. SHE WAS RIGHT.',      # 78 substation after refusing
    'CONSOLE: LOOP 4,818. PHASE DRIFT!',      # 79 diagnose, one loop later
    'CONSOLE: LOOP 4,8??. YOU AGAIN?!',       # 80 diagnose, loops later
    'SCIENTIST: G-BOT! WAIT. AGAIN?',         # 81 dialogue after a restore
    "YOU DID IT AGAIN, DIDN'T YOU?",          # 82
    'FULL POWER JUST RERUNS THE NIGHT.',      # 83 (then 55, 56: cut off again)
    'SCIENTIST: AGAIN?! STOP FLIPPING IT!',   # 84 dialogue after two or more
    'TRICKLE LEAD IN. THE RING TICKS ONCE.',  # 85 refuse path: at the chamber
    'LAB CLOCK: 6:02... 6:03! IT MOVED!',     # 86
    'SCIENTIST: YOU LISTENED! ONE MINUTE!',   # 87
    'ONLY YOU CAN CARRY TIME, G-BOT.',        # 88
    "G-BOT: I'M... TICKING?",                 # 89 he carries a minute now
    'CONSOLE: BREAKER OFF. GOOD BOT.',        # 90 console after refusing
    'CHAMBER: RECHARGING. NEXT MINUTE SOON',  # 91 chamber once the minute is spent
    'CHAMBER: SPACE TO PLUG IN THE LEAD',     # 92 carrying the lead
    'CONSOLE: LOOP HOLDS. 6:03 AND TICKING',  # 93 console after the lead
    'G-BOT: ...HAVE I DONE THIS BEFORE?',     # 94 deja vu at the breaker, first loop
    'G-BOT: ...I HAVE DONE THIS BEFORE.',     # 95 deja vu after a rerun
    '...THE SUBSTATION: EAST OF POWER ROOM',  # 96 the nudge after her warning
    'SUBSTATION OPEN: EAST OF POWER ROOM',    # 97 console reminder until the choice
    'SCIENTIST: TAKE IT TO SOMETHING STUCK',  # 98 carrying time
    'NEW TASK: UNSTICK SOMETHING FROZEN',     # 99
    'CHAMBER: ONE MINUTE CARRIED. GO!',       # 100 chamber while he carries it
    'CONSOLE: 6:04! SOMETHING WOKE UP.',      # 101 console once it is spent
    'G-BOT: THE GUARD... IS STUCK TOO.',      # 102 security, carrying the minute
    'GUARD: BEEP? WHERE DID THE NIGHT GO?',   # 103 the guard remembers
    'GUARD: G-BOT! YOU KEEP PASSING ME!',     # 104
    'GUARD: WING B CODE IS 6-0-4. GO ON.',    # 105
    'THE MINUTE IS SPENT. WING B UNSEALED.',  # 106
    'WING B SEALED - GUARD HAS THE CODE',     # 107 security west door
    'GUARD: OFF DUTY. WING B IS OPEN.',       # 108 security once he is awake
    'ENTERING WING B...',                     # 109
    'GUARD: ...HAVE WE MET? REBOOTING.',      # 110 after a rerun, faintly
    'WING B: THE ARCHIVE, STOPPED AT 3:07',   # 111 wing B
    'COFFEE MACHINE: SPACE TO PROBE',         # 112
    'LOOP LOG: SPACE TO PROBE',               # 113
    'A DROP OF COFFEE, FROZEN IN MIDAIR.',    # 114
    'G-BOT: THAT WILL TAKE ANOTHER MINUTE.',  # 115
    '...MAYBE THE CHAMBER HAS ONE MORE?',     # 116 the hint (runs on: 0xDB, or 0xDC with the desk fixed)
    'LOOP LOG: 4,817 TALLY MARKS. NEAT.',     # 117
    "LAST ENTRY: DON'T FLIP THE BREAKER.",    # 118
]
# The second minute (and the scientist's notes): ids $B0 up, past the tuning
# meter's $80-$AF. Their texts live in the chapter bank ($6000, track 13: the
# story bank links on to it), their chains and sounds in src/chapter_msgs.inc.
CH_FIRST=0xB0
CHAPTER={
 0xB0:'CHAMBER: EMPTY. FIX SOMETHING NEARBY.',  # chamber, first minute spent
 0xB1:'CONSOLE: SECURITY MONITORS: NO SIGNAL',  # ...the console knows what
 0xB2:'CHAMBER: CHARGED! A SECOND MINUTE.',     # cameras fixed: minute two
 0xB3:'G-BOT: TICKING AGAIN. COFFEE TIME?',
 0xB4:'NEW TASK: WAKE THE COFFEE MACHINE',
 0xB5:'CONSOLE: CAMERAS UP. CHAMBER CHARGED.',  # console, cameras fixed
 0xB6:'CONSOLE: 6:04 AND TICKING. AGAIN!',      # console, carrying minute two
 0xB7:'CONSOLE: 6:05! SOMEONE IS GRUMPY.',      # console, minute two spent
 0xB8:'GUARD: MY MONITORS! ALL STATIC!',        # security once he is awake
 0xB9:'MONITORS: STATIC! R RECONNECT / ESC',    # the desk, inspected
 0xBA:'RECONNECTING CAMERAS... HOLD STILL',     # the repair
 0xBB:'GUARD: I CAN SEE! THANKS, G-BOT.',       # fixed
 0xBC:'GUARD: CAMERA 4... A FLOATING DROP?',
 0xBD:'...FAR AWAY, THE CHAMBER RECHARGES.',
 0xC0:'...PLIP! THE DROP FINALLY LANDS.',       # wing B: minute two wakes the coffee
 0xC1:'COFFEE: FINALLY! 4,817 NIGHTS OF DRIP',
 0xC2:'COFFEE: SHE ALWAYS SAID ONE MORE CUP.',
 0xC3:'COFFEE: THEN 11:59:59. THEN NOTHING.',
 0xC4:'COFFEE: SHE LEFT THIS IN MY FILTER.',
 0xC5:'GOT A NOTEBOOK PAGE!',                   # (the HUD shows a page)
 0xC6:'PAGE: 11:59:59. FULL POWER. A LOOP.',
 0xC7:'PAGE: NOT A FLOOD. A TRICKLE ENDS IT.',
 0xC8:'PAGE: I HID THE REST. ROOM BY ROOM.',
 0xC9:'COFFEE: NOW SHOO. MY CUP IS COOLING.',
 0xCA:'NEW TASK: FIND THE OTHER PAGES',
 0xCB:'TO BE CONTINUED: HER MISSING NOTES',     # the hook
 0xCC:'COFFEE: BREWING. GO FIND HER PAGES.',    # the coffee, awake, again
 0xCD:'G-BOT: FROZEN AGAIN. I KEPT THE PAGE.',  # after a rerun (the page stays)
 0xCE:'...PLIP! THE DROP LANDS. AGAIN.',        # waking it again, a loop later
 0xCF:'COFFEE: YOU AGAIN?! YOU GOT THE PAGE.',
 0xD0:'COFFEE: ANOTHER NIGHT. SHOO.',
 0xD1:'G-BOT: BAD IDEA. BUT I KEPT THE PAGE.',  # waking from a rerun, page kept
 # G-Bot thinks out loud: after each milestone, a nudge toward the next one.
 0xD2:'G-BOT: THE BACK DOOR CLICKED. NORTH!',   # workbench fixed
 0xD3:'G-BOT: THAT OLD LOCKER... A GLINT?',     # dead panel
 0xD4:'G-BOT: WEST DOOR. SECURITY. GULP.',      # power restored
 0xD5:'G-BOT: SNEAK BEHIND HIM TO THE DESK.',   # caught by the guard
 0xD6:'G-BOT: BUT SHE SAID NO FULL POWER...',   # after her warning: the N path
 0xD7:'G-BOT: NEXT TIME I LISTEN TO HER. N.',   # waking from a rerun
 0xD8:'G-BOT: THE LAB CHAMBER! PLUG THIS IN.',  # took the trickle lead
 0xD9:'G-BOT: THE GUARD IS STUCK. BUMP HIM!',   # carrying the minute
 0xDA:'G-BOT: HIS MONITORS DIED. HIS DESK?',    # the guard woke
 0xDB:"G-BOT: FIRST, FIX THE GUARD'S DESK.",   # coffee, no minute, desk unfixed
 0xDC:'G-BOT: THE LAB CHAMBER MUST BE READY!',   # coffee, no minute, desk fixed
 0xDD:"G-BOT: THE GUARD'S DESK. LOOSE CABLE?",   # empty chamber / console
 0xDE:'G-BOT: BACK TO THE LAB CHAMBER, THEN.',   # cameras fixed
 0xDF:"G-BOT: WING B. SECURITY'S WEST DOOR.",    # second minute
 # T: the current goal (one per progress state; some run on to a second line)
 0xE0:'GOAL: FIX THE WORKBENCH. LEFT BENCH.',
 0xE1:'GOAL: FIND A FUSE. POWER ROOM, NORTH.',
 0xE2:'GOAL: FIT THE FUSE IN THE PANEL',
 0xE3:'GOAL: GET TO THE DESK IN SECURITY',
 0xE4:'G-BOT: WEST DOOR. WAIT FOR THE GUARD.',
 0xE5:'GOAL: THE LAB, NORTH IN SECURITY',
 0xE6:'G-BOT: PROBE THE CONSOLES. TUNE THEM.',
 0xE7:'GOAL: THE SUBSTATION, EAST OF POWER',
 0xE8:'G-BOT: SHE SAID NO FULL POWER. SO: N.',
 0xE9:'GOAL: PUT THE LEAD IN THE LAB CHAMBER',
 0xEA:'GOAL: TAKE THE MINUTE TO THE GUARD',
 0xEB:'G-BOT: IN SECURITY. JUST BUMP HIM.',
 0xEC:"GOAL: FIX THE GUARD'S DESK MONITORS",
 0xED:'G-BOT: SPACE AT HIS DESK, THEN R.',
 0xEE:'GOAL: LAB CHAMBER. ONE MORE MINUTE',
 0xEF:'GOAL: WAKE THE COFFEE IN WING B',
 0xF0:"G-BOT: THAT'S SECURITY'S WEST DOOR.",
 0xF1:'GOAL: THE COFFEE HAS A PAGE FOR ME',
 0xF2:'GOAL: FIND THE OTHER NOTEBOOK PAGES',
 0xF3:'G-BOT: ...ON THE NEXT DISK, I GUESS.',
}
# T's goal per progress state, in task_goal's order (src/chapter.s)
GOALS=(0xE0,0xE1,0xE2,0xE3,0xE5,0xE7,0xE9,0xEA,0xEC,0xEE,0xEF,0xF1,0xF2)
CH_CHAIN={0xB0:0xB1,0xB2:0xB3,0xB3:0xB4,0xBB:0xBC,0xBC:0xBD,0xC0:0xC1,0xC1:0xC2,0xC2:0xC3,
          0xC3:0xC4,0xC4:0xC5,0xC5:0xC6,0xC6:0xC7,0xC7:0xC8,0xC8:0xC9,0xC9:0xCA,0xCA:0xCB,
          0xCD:115,0xCE:0xCF,0xCF:0xD0,
          0xB1:0xDD,0xBD:0xDE,0xB4:0xDF,0xD1:0xD7,
          0xE3:0xE4,0xE5:0xE6,0xE7:0xE8,0xE9:None,0xEA:0xEB,0xEC:0xED,0xEF:0xF0,0xF2:0xF3}
CH_CHAIN={k:v for k,v in CH_CHAIN.items() if v}
class _Messages(list):
    """MESSAGES[i]: ids 0-118 as listed, the chapter's from $B0."""
    def __getitem__(self,i):
        if isinstance(i,int) and i>=CH_FIRST:return CHAPTER[i]
        return list.__getitem__(self,i)
MESSAGES=_Messages(MESSAGES)
# Which room's disk bank carries each message (status lines are per room).
# 'story': the shared story bank in language-card RAM (every room's bank
# links on to it): the twist-two lines, shown from any room.
MSG_ROOMS={0:list(range(0,8))+[12,60,63,64],1:list(range(8,22))+[59,61,63,64],
           2:list(range(22,31))+[60,62,63,64],3:[28]+list(range(31,59))+[61,63,64],
           4:[28,60,63,64],5:[28,61,63,64]+list(range(111,119)),'story':list(range(65,111)),
           'chapter':sorted(CHAPTER)}
SOUND_MSG=63
# Speaker effect a message plays when it first shows (src/sfx.s ids):
# 1 buzz, 2 chime, 6 lock chord; +128 = a blocking stinger: 7 lab door
# unlocked, 9 console online fanfare, 12 the reveal cut off at IT RUNS AGAIN-.
SFX_BUZZ,SFX_CHIME,SFX_CHORD,SFX_OPEN,SFX_ONLINE,SFX_CUTOFF=1,2,6,128+7,128+9,128+12
SFX_UNSTICK,SFX_HOOK=128+21,128+22     # the trickle lead ticks the ring; to be continued
SFX_TICK=128+23                        # a carried minute ticks
MSG_SFX={5:SFX_BUZZ,7:SFX_BUZZ,10:SFX_BUZZ,11:SFX_BUZZ,12:SFX_BUZZ,15:SFX_BUZZ,
         21:SFX_BUZZ,24:SFX_BUZZ,28:SFX_BUZZ,29:SFX_BUZZ,47:SFX_BUZZ,48:SFX_BUZZ,
         14:SFX_CHIME,46:SFX_CHORD,30:SFX_OPEN,49:SFX_ONLINE,56:SFX_CUTOFF,
         66:SFX_BUZZ,81:SFX_ONLINE,84:SFX_ONLINE,85:SFX_UNSTICK,89:SFX_TICK,103:SFX_TICK,106:SFX_OPEN,107:SFX_BUZZ,116:SFX_CHIME}
CH_SFX={0xB0:SFX_BUZZ,0xB2:SFX_TICK,0xB8:SFX_BUZZ,0xBD:SFX_CHIME,0xC5:SFX_CHIME,0xCA:SFX_HOOK}
# Door status line by destination room (workshop, power, security, lab).
ENTER_MSG=(59,60,61,62,65,109)
METER=45; FIRST_DIALOG=49; RELEASE_LINE=56; DIALOG_TIME=56
TUNE_TARGETS=(11,2,9); TUNE_START=7; TUNE_CELLS=15
# A probe line that runs on: when its feedback time ends, the next one shows.
CHAIN={10:0xD3,18:0xD4,24:0xD5,96:0xD6,73:0xD7,74:0xD7,77:0xD8,99:0xD9,106:0xDA,116:0xDB,101:0xB1,89:98,98:99,103:104,104:105,105:106,114:115,115:116,117:118,57:67,67:96,97:42,75:76,76:77,81:82,82:83,83:55,84:83,85:86,86:87,87:88,88:89,27:30,33:43,35:36,38:39,58:97,49:50,50:51,51:52,52:53,53:54,54:55,55:56,56:57}

def meter_text(step,pos):
    """The tuning meter the engine builds from template 45: phase number,
    target '|', cursor 'O' (or '*' when it sits on the target)."""
    t=list(MESSAGES[METER].center(40)); first=t.index('.')
    t[t.index('1')]=str(step+1)
    target=TUNE_TARGETS[step]; t[first+target]='|'
    t[first+pos]='*' if pos==target else 'O'
    return ''.join(t)
def message_pixels(text):
    if isinstance(text,int):text=meter_text((text>>4)&7,text&15)
    assert len(text)<=40
    text=text.center(40)
    return [bytes(sum((3<<(x*2)) for x,v in enumerate(REPAIR_FONT[ch][y]) if v=='1') for ch in text) for y in range(5)]

def fuse_icon():
    """Two status-line bytes (columns 38-39, rows 177-181): a carried fuse."""
    from gen_concept import Paint as _P
    p=_P()
    p.rect((266,177,267,181),T); p.rect((278,177,279,181),T)
    p.rect((268,178,277,180),O); p.line([(270,179),(275,179)],T)
    data=encode(p.im)
    return [bytes(data[row_offset(177+r)+38:row_offset(177+r)+40]) for r in range(5)]

def clock_icon():
    """Two status-line bytes (columns 38-39, rows 177-181): a carried minute."""
    from gen_concept import Paint as _P
    p=_P()
    p.line([(268,177),(277,177),(277,181),(268,181),(268,177)],T)
    p.line([(272,178),(272,179),(275,179)],T)
    data=encode(p.im)
    return [bytes(data[row_offset(177+r)+38:row_offset(177+r)+40]) for r in range(5)]

def page_icon():
    """Two status-line bytes (columns 38-39, rows 177-181): a notebook page."""
    from gen_concept import Paint as _P
    p=_P()
    p.line([(268,177),(274,177),(276,179),(276,181),(268,181),(268,177)],T)
    p.line([(270,179),(273,179)],T)
    data=encode(p.im)
    return [bytes(data[row_offset(177+r)+38:row_offset(177+r)+40]) for r in range(5)]

def status_rows(index,carrying=False):
    """Exact five status rows the engine draws: message plus optional fuse icon."""
    rows=[bytearray(r) for r in message_pixels(index if 128<=index<CH_FIRST else MESSAGES[index])]
    if carrying:
        for r,icon in zip(rows,{'clock':clock_icon,'page':page_icon}.get(carrying,fuse_icon)()): r[38:40]=icon
    return [bytes(r) for r in rows]

def interaction_art():
    offline,online=room(),room(True)
    changed=[i for i,(a,b) in enumerate(zip(offline,online)) if a!=b]
    assert 0<len(changed)<=128, "6502 patch loop uses a signed decrement"
    messages=MESSAGES
    assert all(i in sum(MSG_ROOMS.values(),[]) for i in range(len(messages))), 'every message in a bank'
    arrays={
        'patchlo':[i&255 for i in changed],
        'patchhi':[i>>8 for i in changed],
        'patch_off':[offline[i] for i in changed],
        'patch_on':[online[i] for i in changed],
    }
    lines=['; Generated by tools/gen_workshop.py; do not hand edit.',f'PATCH_COUNT={len(changed)}']
    for name,values in arrays.items():
        lines += [name+':','.byte '+','.join(str(v) for v in values)]
    # Messages are 40 glyph indices; the engine looks up one byte per row.
    glyphs=GLYPHS
    # The message texts themselves live in per-room disk banks (gen_banks.py).
    for i,text in enumerate(messages):
        assert len(text)<=37 and text.center(40)[38:]=='  ', 'columns 38-39 hold the fuse icon'
    t=MESSAGES[METER].center(40)
    lines += [f'METER={METER}',f'METER_STEP={t.index("1")}',f'METER_CELL0={t.index(".")}',
              f'GLYPH_1={glyphs.index("1")}',f'GLYPH_0={glyphs.index("0")}',f'GLYPH_BAR={glyphs.index("|")}',
              f'GLYPH_O={glyphs.index("O")}',f'GLYPH_STAR={glyphs.index("*")}',
              'entermsg:','.byte '+','.join(str(v) for v in ENTER_MSG),
              f'FIRST_DIALOG={FIRST_DIALOG}',f'RELEASE_LINE={RELEASE_LINE}',f'DIALOG_TIME={DIALOG_TIME}',
              f'TUNE_START={TUNE_START}',f'TUNE_LAST={TUNE_CELLS-1}',
              'tunetarget:','.byte '+','.join(map(str,TUNE_TARGETS))]
    for step in range(3):
        for pos in range(TUNE_CELLS):
            assert len(meter_text(step,pos).strip())<=37 and meter_text(step,pos)[38:]=='  '
    lines += ['fontlo:','.byte '+','.join(f'<fontrow{r}' for r in range(5)),
              'fonthi:','.byte '+','.join(f'>fontrow{r}' for r in range(5))]
    for r in range(5):
        lines += [f'fontrow{r}:','.byte '+','.join(str(message_pixels(ch)[r][19]) for ch in glyphs)]
    lines += [f'SOUND_MSG={SOUND_MSG}',f'MSG_COUNT={len(messages)}','msgsfx:','.byte '+','.join(str(MSG_SFX.get(i,0)) for i in range(len(messages)))]
    lines += ['chain:','.byte '+','.join(str(CHAIN.get(i,0)) for i in range(len(messages)))]
    # HUD icons (fuse or lead, minute, page): after the page-aligned tables.
    icon=fuse_icon()+clock_icon()+page_icon()
    (ROOT/'src/icons.inc').write_text('\n'.join(['; Generated by tools/gen_workshop.py; do not hand edit.',
        'iconl:','.byte '+','.join(str(r[0]) for r in icon),'iconr:','.byte '+','.join(str(r[1]) for r in icon)])+'\n')
    # The chapter's messages: chains and sounds for ids $B0 up (chapter code).
    assert CH_FIRST>=0x80+0x30 and max(CHAPTER)<0xFE, 'chapter ids clear of the meter and the bank markers'
    for i,text in CHAPTER.items():
        assert len(text)<=37 and all(ch in GLYPHS for ch in text), (hex(i),text)
    n=max(CHAPTER)+1-CH_FIRST
    ch=['; Generated by tools/gen_workshop.py; do not hand edit.',f'CH_FIRST={CH_FIRST}',f'CH_LAST={max(CHAPTER)}',
        'chsfx:','.byte '+','.join(str(CH_SFX.get(CH_FIRST+i,0)) for i in range(n)),
        'chchain:','.byte '+','.join(str(CH_CHAIN.get(CH_FIRST+i,0)) for i in range(n)),
        'goals:','.byte '+','.join(str(g) for g in GOALS)]
    (ROOT/'src/chapter_msgs.inc').write_text('\n'.join(ch)+'\n')
    # Self-check: glyph lookup reproduces message_pixels exactly.
    for text in messages:
        rows=message_pixels(text)
        for r in range(5):
            assert bytes(message_pixels(ch)[r][19] for ch in text.center(40))==rows[r]
    (ROOT/'src/interaction.inc').write_text('\n'.join(lines)+'\n')
    print('Repair visual patch:',len(changed),'bytes; font',5*len(glyphs),'bytes; messages are in the disk banks')

def robot(direction=0,pose=0,blink=False,probe=False):
    im=Image.new('L',(SW,SH),CLEAR); d=ImageDraw.Draw(im)
    def r(b,c): d.rectangle(b,fill=c)
    def l(points,c,w=1): d.line(points,fill=c,width=w)
    def poly(points,c): d.polygon(points,fill=c)
    # Stable black silhouette includes the soles; body bob gives foot weight.
    bob=1 if pose==2 else 0
    # Ankle bellows and broad, staggered boots.
    for x,dy in ((10+(-1 if pose==1 else 1 if pose==2 else 0),-1 if pose==1 else 0),
                 (24+(1 if pose==1 else -1 if pose==2 else 0),-1 if pose==2 else 0)):
        r((x,33,x+7,39),K); r((x+2,34,x+5,39),B)
        l([(x+1,35),(x+6,35)],T); l([(x+1,37),(x+6,37)],T)
        poly([(x,38+dy),(x+7,38+dy),(x+10,41+dy),(x+10,43+dy),(x-2,43+dy),(x-2,41+dy)],K)
        poly([(x+1,39+dy),(x+6,39+dy),(x+8,41+dy),(x-1,41+dy)],T)
        l([(x-1,42+dy),(x+8,42+dy)],O)
        l([(x-1,43+dy),(x+9,43+dy)],T)
    # Grabber arm and probe: silhouette, elbow pin, metal upper edge.
    l([(10,26+bob),(6,29+bob),(4,25+bob)],K,5)
    l([(10,26+bob),(6,29+bob),(4,25+bob)],O,2)
    l([(7,28+bob),(8,28+bob)],T,2)
    l([(3,26+bob),(1,23+bob),(1,21+bob)],K,3)
    l([(3,25+bob),(1,23+bob),(1,21+bob)],T)
    l([(4,25+bob),(6,23+bob),(6,21+bob)],T)
    end=40 if probe else 37
    l([(31,26+bob),(34,29+bob),(end,26+bob)],K,5)
    l([(31,25+bob),(34,28+bob),(end,25+bob)],O,2)
    l([(34,28+bob),(end,25+bob)],T)
    if probe: l([(38,24+bob),(41,23+bob)],B)
    # Familiar sloped cream computer body, recessed drive, keyboard-like belly.
    poly([(11,21+bob),(28,21+bob),(33,25+bob),(32,34+bob),(10,34+bob),(8,29+bob)],K)
    poly([(12,22+bob),(27,22+bob),(30,25+bob),(11,25+bob)],T)
    r((10,26+bob,29,32+bob),T)
    r((30,26+bob,31,32+bob),O)
    r((13,26+bob,27,29+bob),K)
    l([(14,27+bob),(25,27+bob)],B)
    r((21,26+bob,23,27+bob),T)
    r((26,28+bob,27,29+bob),K if blink else O)
    l([(13,31+bob),(27,31+bob)],K)
    for x in (14,18,22,26): r((x,31+bob,x+1,31+bob),T)
    l([(11,33+bob),(28,33+bob)],O)
    # Neck and big CRT head: face occupies 20x11 pixels, never shrunk to a dot.
    r((17,19+bob,25,23+bob),K); l([(18,21+bob),(24,21+bob)],T)
    poly([(9,4+bob),(13,2+bob),(29,2+bob),(34,6+bob),(34,18+bob),(31,22+bob),(9,21+bob),(6,18+bob),(6,7+bob)],K)
    poly([(10,4+bob),(14,3+bob),(28,3+bob),(31,5+bob),(11,5+bob)],T)
    poly([(9,6+bob),(30,6+bob),(32,8+bob),(31,19+bob),(28,21+bob),(10,20+bob),(8,18+bob),(8,8+bob)],T)
    l([(33,7+bob),(33,17+bob),(31,20+bob)],G)
    r((10,8+bob,29,18+bob),K)
    l([(10,18+bob),(12,19+bob),(28,19+bob)],G)
    if direction==3:
        # Rear vents and service-label LED; this is an actual directional pose.
        for y in (10,13,16): l([(13,y+bob),(26,y+bob)],T)
        r((27,16+bob,28,17+bob),G)
    else:
        glance=-2 if direction==1 else 2 if direction==2 else 0
        if blink:
            l([(12,13+bob),(17,13+bob)],G)
            l([(23,13+bob),(28,13+bob)],G)
        else:
            l([(12,9+bob),(16,9+bob)],G)
            l([(24,10+bob),(28,10+bob)],G)
            r((12,11+bob,17,15+bob),G); r((23,11+bob,28,15+bob),G)
            r((14+glance//2,11+bob,15+glance//2,14+bob),K)
            r((25+glance//2,11+bob,26+glance//2,14+bob),K)
        l([(17,16+bob),(19,18+bob),(23,18+bob),(25,16+bob)],G)
        l([(11,8+bob),(13,8+bob)],T)
    # A small scuff and the crooked aerial from the portrait.
    l([(26,4+bob),(28,4+bob)],K)
    l([(26,2+bob),(28,0),(30,0)],T)
    r((30,0,31,1),G)
    out=bytearray()
    for y in range(SH):
        phase=128 if y>=23 else 0
        mask=[]; data=[]
        for b in range(6):
            m=v=0
            for i in range(7):
                x=b*7+i; c=im.getpixel((x,y))
                if c!=CLEAR: m|=1<<i
                if c==T or (c in (V,B) and x%2==0) or (c in (G,O) and x%2==1): v|=1<<i
            mask.append(m); data.append(v)
        out.extend(mask+data+[phase])
    return bytes(out)

def main():
    (ROOT/'build').mkdir(exist_ok=True)
    interaction_art()
    data=room(); (ROOT/'art/workshop-room.hgr').write_bytes(data)
    frames=[robot(d,p) for d in range(4) for p in range(3)]
    frames += [robot(blink=True),robot(probe=True)]
    assert all(len(f)==44*13 for f in frames)
    assert data==room(), 'Workshop generation must be deterministic'
    used={row_offset(y)+b for y in range(192) for b in range(40)}
    assert all(data[i]==0 for i in set(range(8192))-used), 'Nonzero HGR holes'
    for frame in frames:
        for off in range(0,len(frame),13):
            row=frame[off:off+13]
            assert row[12] in (0,128) and all(v<128 for v in row[:12])
            assert all((v&~m)==0 for m,v in zip(row[:6],row[6:12])), 'Pixels outside opacity'
    (ROOT/'art/gbot-sprites.bin').write_bytes(b''.join(frames))
    # Preview composited native bytes at even x; exact same source format as engine.
    screen=bytearray(data); x0,y0=126,104
    f=frames[0]
    for y in range(44):
        m=f[y*13:y*13+6]; v=f[y*13+6:y*13+12]; phase=f[y*13+12]
        for b in range(6):
            at=row_offset(y0+y)+x0//7+b
            screen[at]=((screen[at]&(~m[b]&127))|v[b]|phase) if m[b] else screen[at]
    decode(screen).crop((0,0,280,166)).resize((1120,640),Image.Resampling.NEAREST).save(ROOT/'build/workshop-design.png')
    print('Workshop: 8192 bytes; 14 masked 42x44 frames:',len(b''.join(frames)),'bytes')
if __name__=='__main__':main()
