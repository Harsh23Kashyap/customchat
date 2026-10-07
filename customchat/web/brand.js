/* Local-only palette extraction. No image or pixels leave the browser. */
(function(root){
  const rgb=h=>[1,3,5].map(i=>parseInt(h.slice(i,i+2),16));
  const hex=c=>'#'+c.map(v=>Math.max(0,Math.min(255,Math.round(v))).toString(16).padStart(2,'0')).join('');
  const mix=(a,b,t)=>hex(rgb(a).map((v,i)=>v*(1-t)+rgb(b)[i]*t));
  const lum=h=>rgb(h).map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4}).reduce((s,v,i)=>s+v*[.2126,.7152,.0722][i],0);
  const contrast=(a,b)=>(Math.max(lum(a),lum(b))+.05)/(Math.min(lum(a),lum(b))+.05);
  function safe(c,backs,target=4.5){
    if(backs.every(b=>contrast(c,b)>=target))return c;
    const end=lum(backs[0])>.4?'#000000':'#ffffff';
    for(let i=1;i<=100;i++){const x=mix(c,end,i/100);if(backs.every(b=>contrast(x,b)>=target))return x;}
    return end;
  }
  function seed(pixels){
    const bins=new Map();
    for(let i=0;i<pixels.length;i+=4){if(pixels[i+3]<128)continue;const c=[pixels[i],pixels[i+1],pixels[i+2]];const saturation=(Math.max(...c)-Math.min(...c))/255;const brightness=c.reduce((a,b)=>a+b,0)/3;if(brightness>245||brightness<10)continue;
      const key=c.map(v=>Math.round(v/24)*24).join(',');const b=bins.get(key)||{n:0,c:[0,0,0],sat:0};b.n++;b.c=b.c.map((v,j)=>v+c[j]);b.sat+=saturation;bins.set(key,b);
    }
    const best=[...bins.values()].sort((a,b)=>b.n*(.15+b.sat/b.n)-a.n*(.15+a.sat/a.n))[0];
    return best?hex(best.c.map(v=>v/best.n)):'#173f35';
  }
  function palette(color,dark){
    const bg=mix(color,dark?'#000000':'#ffffff',dark?.94:.97),surface=mix(color,dark?'#000000':'#ffffff',dark?.89:.99),sidebar=mix(color,dark?'#000000':'#ffffff',dark?.85:.94),bot=mix(color,dark?'#000000':'#ffffff',dark?.82:.94),you=mix(color,dark?'#000000':'#ffffff',dark?.72:.88);
    const backs=[bg,surface,sidebar,bot,you];
    return {bg,surface,sidebar,bot,you,brand:safe(color,backs),accent:safe(color,backs),ink:safe(dark?'#f8f8f8':'#17231f',backs),muted:safe(dark?'#a9b7b0':'#63736c',backs),line:mix(color,dark?'#000000':'#ffffff',dark?.65:.78),danger:safe('#b23a3a',backs)};
  }
  const api={seed,palette,contrast,safe};root.CCBrand=api;if(typeof module!=='undefined')module.exports=api;
})(typeof window!=='undefined'?window:globalThis);
