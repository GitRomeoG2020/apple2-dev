"""Expected-screen model of the bonus flyer + hit popup on one HGR page, from the per-page
copies the game keeps (SV_* at $1AC0, i.e. offset 0x2C0 into a peek of $1800)."""
import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))+'/../tools'); import gen_flyer,re
def _caps():
    t=open(os.path.dirname(os.path.abspath(__file__))+'/../src/sprites.s').read()
    out=[]
    for n in ('shield0','shield1','cool0','cool1','spread0','spread1','oneup0','oneup1'):
        body=t.split('cap_'+n+':')[1].split('\n\n')[0]
        out.append([int(v,16) for v in re.findall(r'\$([0-9A-F]{2})',body)])
    return out
CAPS=_caps()
def apply(e,sv,pg,FONT):
    """flyer, popup + power-ups (shield bubble, spread side bolts, capsule). The caller's ship model must
    skip the plain ship when shield(sv,pg) is set."""
    H=len(e)
    def x(row,col,v):
        if 0<=col<40 and 0<=row<H: e[row][col]^=v
    if sv[0x2C0+pg]:
        fs,fx,fy=sv[0x2C2+pg],sv[0x2C4+pg],sv[0x2C6+pg]
        d=gen_flyer.sprite(fs,(2*fx)%7); col=(2*fx)//7-4
        for r in range(7):
            for b in range(4): x(fy+r,col+b,d[r*4+b])
    pk=sv[0x2C8+pg]
    if pk:
        pc,py,pv=sv[0x2CA+pg],sv[0x2CC+pg],sv[0x2CE+pg]
        if pk==1:
            for r in range(7):
                for b in range(3): x(py+r,pc+b,gen_flyer.BURST_BYTES[r*3+b])
        else:
            for i,g in enumerate({0:[5,0],1:[1,0,0],2:[1,5]}[pv]):
                for r in range(5): x(py+1+r,pc+i,FONT[g*5+r])
    if sv[0x2E0+pg]:                       # shield bubble (flyer sprite 4, 10 rows) at FX=PX+12
        fx=sv[0x2B0+pg]+12; d=gen_flyer.sprite(4,(2*fx)%7); col=(2*fx)//7-4
        for r in range(10):
            for b in range(4): x(138+r,col+b,d[r*4+b])
    ly=sv[0x2F2+pg]
    for i in range(2):                     # spread side bolts
        j=pg*2+i
        if sv[0x2E2+j]:
            for r in range(12):
                x(ly+r,sv[0x2E6+j],sv[0x2EA+j])
                if sv[0x2EE+j]: x(ly+r,sv[0x2E6+j]+1,sv[0x2EE+j])
    if sv[0x2F4+pg]:                       # capsule
        d=CAPS[sv[0x2FA+pg]]; c,y=sv[0x2F6+pg],sv[0x2F8+pg]
        for r in range(9):
            for b in range(2): x(y+r,c+b,d[r*2+b])
    return e
def shield(sv,pg): return sv[0x2E0+pg]
