"""Expected-screen model of the bonus flyer + hit popup on one HGR page, from the per-page
copies the game keeps (SV_* at $1AC0, i.e. offset 0x2C0 into a peek of $1800)."""
import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))+'/../tools'); import gen_flyer
def apply(e,sv,pg,FONT):
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
    return e
