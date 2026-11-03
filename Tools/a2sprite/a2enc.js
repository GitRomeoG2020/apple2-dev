// ==== a2enc: Apple II encoders (shared by a2sprite.html and node tests) ====
var A2 = (function(){
  // Sprite model: {wb, h, px:[h][wb*7] 0/1, pal:[h][wb] 0/1}
  function newSprite(wb,h){var s={wb:wb,h:h,px:[],pal:[]};for(var y=0;y<h;y++){s.px.push(new Array(wb*7).fill(0));s.pal.push(new Array(wb).fill(0));}return s;}
  function resize(s,wb,h){var n=newSprite(wb,h);for(var y=0;y<Math.min(h,s.h);y++){for(var x=0;x<Math.min(wb*7,s.wb*7);x++)n.px[y][x]=s.px[y][x];for(var b=0;b<Math.min(wb,s.wb);b++)n.pal[y][b]=s.pal[y][b];}return n;}
  // bit0 = leftmost pixel of the byte, bit7 = palette
  function rowBytes(s,y){var o=[];for(var b=0;b<s.wb;b++){var v=s.pal[y][b]<<7;for(var i=0;i<7;i++)if(s.px[y][b*7+i])v|=1<<i;o.push(v);}return o;}
  function spriteBytes(s){var o=[];for(var y=0;y<s.h;y++)o.push(rowBytes(s,y));return o;}
  // AND-mask: clear sprite pixels; where a sprite byte has pixels its palette replaces the screen's (bit7=0), else keep (bit7=1)
  function maskRow(r){return r.map(function(v){var bits=v&0x7f;return bits?(~bits&0x7f):0xff;});}
  // Pre-shift a byte row right by s pixels (0..6) into wb+1 bytes. Bits carry across bytes;
  // each output byte takes the palette of the source byte that contributes most of its set pixels.
  function shiftRow(r,s){var n=r.length,out=[];for(var j=0;j<=n;j++){var v=0;for(var i=0;i<7;i++){var src=j*7+i-s;if(src<0)continue;var sb=Math.floor(src/7),si=src%7;if(sb<n&&(r[sb]>>si)&1)v|=1<<i;}
    // palette: source byte contributing the most set bits; if none, the source of output pixel 0
    var cnt={};for(var i2=0;i2<7;i2++){var sr2=j*7+i2-s;if(sr2<0)continue;var sb2=Math.floor(sr2/7);if(sb2<n&&(r[sb2]>>(sr2%7))&1)cnt[sb2]=(cnt[sb2]||0)+1;}
    var p0=j*7-s,pb=p0<0?0:Math.min(Math.floor(p0/7),n-1),best=-1;for(var k in cnt)if(cnt[k]>best){best=cnt[k];pb=+k;}
    v|=(r[pb]&0x80);out.push(v);}return out;}
  function hex(v){return '$'+(v<16?'0':'')+v.toString(16).toUpperCase();}
  function asmRows(lbl,rows,comment){var t='';if(comment)t+='; '+comment+'\n';t+=lbl+':\n';rows.forEach(function(r,i){t+='        .byte '+r.map(hex).join(',')+'   ; row '+i+'\n';});return t;}
  function exportSpriteAsm(s,name,opt){opt=opt||{};var rows=spriteBytes(s);var t='; a2sprite export: '+name+'\n; size: '+s.wb+' bytes ('+(s.wb*7)+' px) x '+s.h+' rows, '+(s.wb*s.h)+' bytes\n; byte layout: bit0 = leftmost pixel, bit7 = palette (0=violet/green, 1=blue/orange)\n';
    t+=name.toUpperCase()+'_W = '+s.wb+'\n'+name.toUpperCase()+'_H = '+s.h+'\n\n';
    t+=asmRows(name,rows);
    if(opt.mask)t+='\n'+asmRows(name+'_mask',rows.map(maskRow),'AND mask: screen = (screen AND mask) OR sprite');
    if(opt.shifts){t+='\n; 7 pre-shifted copies, '+(s.wb+1)+' bytes per row\n'+name.toUpperCase()+'_SW = '+(s.wb+1)+'\n';
      for(var k=0;k<7;k++){var sr=rows.map(function(r){return shiftRow(r,k);});t+='\n'+asmRows(name+'_s'+k,sr,'shift '+k);if(opt.mask)t+=asmRows(name+'_s'+k+'_mask',sr.map(maskRow));}
      t+='\n'+name+'_shift_lo: .byte '+[0,1,2,3,4,5,6].map(function(k){return '<'+name+'_s'+k;}).join(',')+'\n'+name+'_shift_hi: .byte '+[0,1,2,3,4,5,6].map(function(k){return '>'+name+'_s'+k;}).join(',')+'\n';}
    return t;}
  function exportSpriteBin(s,opt){opt=opt||{};var rows=spriteBytes(s),o=[];rows.forEach(function(r){o.push.apply(o,r);});if(opt.mask)rows.forEach(function(r){o.push.apply(o,maskRow(r));});
    if(opt.shifts)for(var k=0;k<7;k++){var sr=rows.map(function(r){return shiftRow(r,k);});sr.forEach(function(r){o.push.apply(o,r);});if(opt.mask)sr.forEach(function(r){o.push.apply(o,maskRow(r));});}return o;}
  // NTSC artifact color approximation for one row of bytes, starting at screen byte column col0 (parity matters).
  // returns array of color ids: 0 black,1 white,2 violet,3 green,4 blue,5 orange
  function artifactRow(bytes,col0){col0=col0||0;var bits=[],pal=[];bytes.forEach(function(v){for(var i=0;i<7;i++){bits.push((v>>i)&1);pal.push(v>>7);}});var o=[];
    for(var x=0;x<bits.length;x++){var on=bits[x],l=x>0&&bits[x-1],r=x<bits.length-1&&bits[x+1];var sx=col0*7+x;
      if(on){if(l||r)o.push(1);else o.push(pal[x]?((sx&1)?5:4):((sx&1)?3:2));}
      else{if(l&&r)o.push(1);else if(l||r){/* half-lit: fringe of neighbor color */var nx=l?x-1:x+1;o.push(0);}else o.push(0);}}return o;}
  // Paint helper for color mode: color 0..5 at pixel x (pairs aligned to even screen columns). Returns conflict flag.
  function paintColor(s,x,y,c){var x0=x&~1,conflict=false;var set=function(px,v){if(px>=0&&px<s.wb*7)s.px[y][px]=v;};
    var pp=function(px,p){if(px<0||px>=s.wb*7)return;var b=Math.floor(px/7);if(s.pal[y][b]!==p){for(var i=0;i<7;i++)if(s.px[y][b*7+i]&&b*7+i!==x0&&b*7+i!==x0+1){conflict=true;break;}s.pal[y][b]=p;}};
    if(c===0){set(x0,0);set(x0+1,0);}else if(c===1){set(x0,1);set(x0+1,1);}
    else{var p=(c===4||c===5)?1:0;var odd=(c===3||c===5);var px=odd?x0+1:x0;set(x0,0);set(x0+1,0);set(px,1);pp(px,p);}
    return conflict;}

  // ===== Applesoft shape tables =====
  // vector code: bit2 = plot, bits0-1 dir: 0 up,1 right,2 down,3 left. Plot happens at current point, then move.
  var DIRS=[[0,-1],[1,0],[0,1],[-1,0]];
  function packVectors(v){var out=[],i=0;
    while(i<v.length){var A=v[i];
      if(i+1<v.length){var B=v[i+1];var C=(i+2<v.length&&v[i+2]<4&&v[i+2]!==0)?v[i+2]:-1;
        if(B!==0){if(C>0){out.push(A|B<<3|C<<6);i+=3;}else{out.push(A|B<<3);i+=2;}continue;}
        if(C>0){out.push(A|C<<6);i+=3;continue;}}
      if(A!==0){out.push(A);i+=1;continue;}
      // lone "move up, no plot": encode as up, right(no plot), left(no plot) => net up
      out.push(0x00|1<<3|3<<6);i+=1;}
    out.push(0);return out;}
  function buildTable(shapes){var n=shapes.length,bodies=shapes.map(packVectors),t=[n,0],off=2+2*n;bodies.forEach(function(b){t.push(off&255,off>>8);off+=b.length;});bodies.forEach(function(b){t.push.apply(t,b);});return t;}
  // Decode / simulate DRAW at scale 1, rot 0 -> list of plotted points relative to origin
  function simulate(table,num){var off=table[2*num]|table[2*num+1]<<8,x=0,y=0,pts=[];
    function ex(c){if(c&4)pts.push([x,y]);x+=DIRS[c&3][0];y+=DIRS[c&3][1];}
    for(var p=off;;p++){var b=table[p];if(b===0||b===undefined)break;ex(b&7);var r=b>>3;if(!r)continue;ex(r&7);r>>=3;if(!r)continue;ex(r&3);}return pts;}
  // Convert pixel set (array of [x,y]) to vectors, starting from origin (ox,oy)
  function pixelsToVectors(pts,ox,oy){var left=pts.map(function(p){return [p[0],p[1]];}),v=[],cx=ox,cy=oy;
    function stepToward(tx,ty){if(tx>cx)return 1;if(tx<cx)return 3;if(ty>cy)return 2;if(ty<cy)return 0;return 1;}
    function mv(d){cx+=DIRS[d][0];cy+=DIRS[d][1];}
    function nearest(){var bi=0,bd=1e9;for(var i=0;i<left.length;i++){var d=Math.abs(left[i][0]-cx)+Math.abs(left[i][1]-cy);if(d<bd){bd=d;bi=i;}}return left.splice(bi,1)[0];}
    var tgt=left.length?nearest():null;
    while(tgt){while(cx!==tgt[0]||cy!==tgt[1]){var d=stepToward(tgt[0],tgt[1]);v.push(d);mv(d);}
      var nxt=left.length?nearest():null;var d2=nxt?stepToward(nxt[0],nxt[1]):1;v.push(4|d2);mv(d2);tgt=nxt;}
    return v;}
  function vecToText(v){var n='URDL';return v.map(function(c){return (c&4?'':'m')+n[c&3];}).join(' ');}
  function textToVec(t){return t.trim().split(/[\s,]+/).filter(Boolean).map(function(w){var m=/^(m?)([URDL])$/i.exec(w);if(!m)throw new Error('bad step: '+w);return (m[1]?0:4)|'URDL'.indexOf(m[2].toUpperCase());});}
  function tableAsm(t,name,shapes){var s='; Applesoft shape table: '+name+', '+shapes+' shape(s), '+t.length+' bytes\n'+name+':\n';for(var i=0;i<t.length;i+=12)s+='        .byte '+t.slice(i,i+12).map(hex).join(',')+'\n';return s;}
  function basicLoader(t,addr,n){addr=addr||24576;var lines=[],ln=10,d=t.slice();
    lines.push(ln+' REM SHAPE TABLE LOADER ('+t.length+' BYTES AT '+addr+')');ln+=10;
    lines.push(ln+' FOR I = 0 TO '+(t.length-1)+': READ B: POKE '+addr+' + I,B: NEXT');ln+=10;
    lines.push(ln+' POKE 232,'+(addr&255)+': POKE 233,'+(addr>>8));ln+=10;
    lines.push(ln+' HGR : HCOLOR= 3: SCALE= 1: ROT= 0');ln+=10;
    lines.push(ln+' DRAW 1 AT 140,96');ln+=10;
    lines.push(ln+' REM XDRAW 1 AT 140,96 ERASES IT AGAIN (XOR)');ln+=10;
    lines.push(ln+' END');ln=1000;
    for(var i=0;i<d.length;i+=16){lines.push(ln+' DATA '+d.slice(i,i+16).join(','));ln+=10;}
    return lines.join('\n')+'\n';}
  // HGR screen helpers
  function hgrAddr(y){return 0x2000+(y&7)*0x400+((y>>3)&7)*0x80+(y>>6)*0x28;}
  function decodeHgr(mem){var rows=[];for(var y=0;y<192;y++){var a=hgrAddr(y)-0x2000,r=[];for(var b=0;b<40;b++){var v=mem[a+b];for(var i=0;i<7;i++)r.push((v>>i)&1);}rows.push(r);}return rows;}
  return {newSprite:newSprite,resize:resize,rowBytes:rowBytes,spriteBytes:spriteBytes,maskRow:maskRow,shiftRow:shiftRow,exportSpriteAsm:exportSpriteAsm,exportSpriteBin:exportSpriteBin,artifactRow:artifactRow,paintColor:paintColor,
    packVectors:packVectors,buildTable:buildTable,simulate:simulate,pixelsToVectors:pixelsToVectors,vecToText:vecToText,textToVec:textToVec,tableAsm:tableAsm,basicLoader:basicLoader,hgrAddr:hgrAddr,decodeHgr:decodeHgr,hex:hex};
})();
if(typeof module!=='undefined')module.exports=A2;
