const assert=require('node:assert/strict');
const B=require('../customchat/web/brand.js');
let n=0;
for(const c of ['#000000','#ffffff','#ff0000','#00ff00','#0000ff','#dddddd','#ccaa00','#000080'])for(const dark of [true,false]){
 const p=B.palette(c,dark);
 for(const k of ['ink','muted','brand','accent','danger'])for(const bg of ['bg','surface','sidebar','bot','you']){assert(B.contrast(p[k],p[bg])>=4.5);n++}
}
assert.equal(B.seed(new Uint8ClampedArray([255,255,255,0])),'#173f35');
assert.equal(B.seed(new Uint8ClampedArray([180,40,20,255,255,255,255,255])),'#b42814');
console.log(n+' contrast pairs and transparent/white seed fallback passed');
