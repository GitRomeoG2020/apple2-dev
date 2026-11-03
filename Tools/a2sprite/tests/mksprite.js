const A=require('../a2enc.js');const s=A.newSprite(2,7);
[[0,1,1,1,1,1,0],[1,0,0,0,0,0,1],[1,0,1,0,1,0,1],[1,0,0,0,0,0,1],[1,0,1,1,1,0,1],[1,0,0,0,0,0,1],[0,1,1,1,1,1,0]].forEach((r,y)=>r.forEach((v,x)=>s.px[y][x+5]=v));
let t=A.exportSpriteAsm(s,'face',{mask:true,shifts:true});
t+=`
; blit face_s3 (3 bytes wide x 7 rows) to HGR page 1 at row Y0, byte column COL using (screen AND mask) OR data
Y0=40
COL=10
ptr=$06
src=$08
msk=$FA
        .segment "CODE"
blit:   ldx #0
@row:   lda rowlo,x
        sta ptr
        lda rowhi,x
        sta ptr+1
        ldy #0
@col:   stx $FC
        txa
        asl
        adc $FC         ; x*3
        sta $FD
        tya
        clc
        adc $FD
        sta $FE
        ldx $FE
        lda (ptr),y
        and face_s3_mask,x
        ora face_s3,x
        sta (ptr),y
        ldx $FC
        iny
        cpy #3
        bne @col
        inx
        cpx #7
        bne @row
        rts
`;
let lo=[],hi=[];for(let y=40;y<47;y++){const a=A.hgrAddr(y)+10;lo.push(a&255);hi.push(a>>8);}
t+='rowlo: .byte '+lo.map(A.hex).join(',')+'\nrowhi: .byte '+hi.map(A.hex).join(',')+'\n';
// put code first: move blit to start by using a jump stub
t='        .segment "CODE"\n        jmp blit\n'+t;
require('fs').writeFileSync(__dirname+'/blit.s',t);
