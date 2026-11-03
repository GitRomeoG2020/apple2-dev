const A=require('../a2enc.js'),fs=require('fs');let fail=0;
function eq(n,a,b){const ok=JSON.stringify(a)===JSON.stringify(b);if(!ok)fail++;console.log((ok?'PASS ':'FAIL ')+n+(ok?'':' got '+JSON.stringify(a)+' want '+JSON.stringify(b)));}
// (1) preshift: single pixel walks across
for(let s=0;s<7;s++)eq('1px shift '+s,A.shiftRow([0x01],s),[1<<s,0]);
eq('carry: bit6 shift1 -> next byte bit0',A.shiftRow([0x40],1),[0,1]);
eq('full byte shift 3',A.shiftRow([0x7f],3),[0x78,0x07]);
eq('palette kept',A.shiftRow([0xff],2),[0xfc,0x83]);
eq('2-byte carry',A.shiftRow([0x81,0x7f],3),[0x88,0x78,0x07]);
// generic check: bitstream equality for random rows
for(let t=0;t<200;t++){const n=1+(t%4),r=[...Array(n)].map(()=>Math.random()*256|0);for(let s=0;s<7;s++){const o=A.shiftRow(r,s);
  const bi=[];r.forEach(v=>{for(let i=0;i<7;i++)bi.push((v>>i)&1)});const bo=[];o.forEach(v=>{for(let i=0;i<7;i++)bo.push((v>>i)&1)});
  const want=Array(s).fill(0).concat(bi);while(want.length<bo.length)want.push(0);if(JSON.stringify(want)!==JSON.stringify(bo)){fail++;console.log('FAIL random',r,s);}}}
console.log('random bitstream preshift checks done (1400)');
eq('mask',A.maskRow([0x83,0x00]),[0x7c,0xff]);
// shape packing rules
eq('square table',A.buildTable([A.textToVec('R R R R D D D D L L L L U U U U')]),[1,0,4,0,45,45,54,54,63,63,36,36,0]);
eq('lone move-up',A.packVectors([0]),[0xC8,0]);
eq('mU mU',A.packVectors([0,0]),[0xC8,0xC8,0]);
eq('up,up,mR uses C',A.packVectors([0,0,1]),[0x40,0]);
// random path round-trip: no zero bytes inside, simulated plots equal intended
for(let t=0;t<300;t++){const v=[...Array(1+t%40)].map(()=>Math.random()*8|0);const tb=A.buildTable([v]);const body=tb.slice(4);
  if(body.indexOf(0)!==body.length-1){fail++;console.log('FAIL zero inside',v);}
  let x=0,y=0;const want=[];v.forEach(c=>{if(c&4)want.push([x,y]);x+=[0,1,0,-1][c&3];y+=[-1,0,1,0][c&3];});
  if(JSON.stringify(A.simulate(tb,1))!==JSON.stringify(want)){fail++;console.log('FAIL roundtrip',v);}}
console.log('random shape roundtrip checks done (300)');
// pixels->vectors covers exactly the pixel set
const px=[[2,2],[3,2],[4,2],[2,5],[9,9]];const vt=A.buildTable([A.pixelsToVectors(px,0,0)]);
eq('pixels->vectors',A.simulate(vt,1).map(p=>p+'').sort(),px.map(p=>p+'').sort());
// artifacts for emulator tests
const sq=A.textToVec('R R R R R R R R D D D D D D D D L L L L L L L L U U U U U U U U');
const arrow=A.pixelsToVectors([[0,0],[1,1],[2,2],[3,3],[4,4],[3,5],[2,6],[1,7],[0,8],[0,1],[0,2],[0,3],[0,4],[0,5],[0,6],[0,7]],0,4);
fs.writeFileSync(__dirname+'/shapes.bin',Buffer.from(A.buildTable([sq,arrow])));
fs.writeFileSync(__dirname+'/loader.bas',A.basicLoader(A.buildTable([sq,arrow]),24576));
console.log(fail?fail+' FAILURES':'ALL UNIT TESTS PASS');process.exit(fail?1:0);
