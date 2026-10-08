/* Shared local walkthrough. It never edits settings or contacts a model. */
(() => {
  'use strict';
  const node=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text)n.textContent=text;return n;};
  const stored=k=>{try{return localStorage.getItem(k)}catch{return null}};
  const mark=k=>{try{localStorage.setItem(k,'1')}catch{}};
  async function show({key,title,steps,replay=false,onClose}) {
    if(!replay){try{const r=await fetch("/api/guide-seen"),d=await r.json();if(d[key])return}catch{}}
    if(document.querySelector('.cc-tour')||(!replay&&stored(key)))return;
    mark(key);fetch('/api/guide-seen',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key})}).catch(()=>{});
    const before=document.activeElement,scroll=window.scrollY;
    const dialog=node('dialog','cc-tour');dialog.setAttribute('aria-label',title);
    const glow=node('div','cc-tour-focus');glow.setAttribute('aria-hidden','true');document.body.append(glow);
    let i=0,target=null;
    const motion=()=>!matchMedia('(prefers-reduced-motion: reduce)').matches;
    function locate(){
      if(!target){glow.hidden=true;dialog.dataset.edge='none';dialog.style.left='16px';dialog.style.top='16px';return}
      const r=target.getBoundingClientRect(),top=Math.max(8,r.top),bottom=Math.min(innerHeight-8,r.bottom),left=Math.max(8,r.left),right=Math.min(innerWidth-8,r.right);
      glow.hidden=bottom<=top||right<=left;Object.assign(glow.style,{top:top+'px',left:left+'px',width:Math.max(0,right-left)+'px',height:Math.max(0,bottom-top)+'px'});
      const w=dialog.offsetWidth,h=dialog.offsetHeight,gap=20,pad=16;let x,y,edge;
      if(innerWidth>760 && innerWidth-r.right>=w+gap+pad){x=r.right+gap;y=Math.max(pad,Math.min(innerHeight-h-pad,r.top+6));edge='left'}
      else if(innerWidth>760 && r.left>=w+gap+pad){x=r.left-w-gap;y=Math.max(pad,Math.min(innerHeight-h-pad,r.top+6));edge='right'}
      else if(innerHeight-r.bottom>=h+gap+pad){x=Math.max(pad,Math.min(innerWidth-w-pad,r.left));y=r.bottom+gap;edge='top'}
      else if(r.top>=h+gap+pad){x=Math.max(pad,Math.min(innerWidth-w-pad,r.left));y=r.top-h-gap;edge='bottom'}
      else{x=Math.max(pad,(innerWidth-w)/2);y=Math.max(pad,innerHeight-h-pad);edge='top'}
      dialog.dataset.edge=edge;Object.assign(dialog.style,{left:x+'px',top:y+'px',bottom:'auto',right:'auto'});
    }
    function end(){mark(key);dialog.close();dialog.remove();glow.remove();window.removeEventListener('resize',locate);window.removeEventListener('scroll',locate);window.scrollTo({top:scroll,behavior:'instant'});if(before?.isConnected)before.focus({preventScroll:true});onClose?.();}
    function draw(){
      const s=steps[i];target=document.querySelector(s.target||'');
      if(target&&getComputedStyle(target).display==='none')target=document.querySelector('#cfgmode');
      target?.scrollIntoView({block:'start',behavior:'instant'});
      const header=node('header','cc-tour-head'),count=node('span','cc-tour-count',`${i+1} / ${steps.length}`),skip=node('button','cc-tour-skip','Skip');skip.type='button';skip.onclick=end;
      header.append(node('span','cc-tour-label',title),count,skip);
      const scene=node('div','cc-tour-scene');scene.setAttribute('aria-hidden','true');scene.dataset.kind=s.kind||'tabs';
      const rail=node('div','cc-tour-rail');(s.tabs||['Ask','Sources','Answer']).forEach((t,j)=>{const chip=node('span','cc-tour-tab'+(j===0?' active':''),t);chip.style.setProperty('--n',j);rail.append(chip)});
      const sample=node('div','cc-tour-sample');sample.append(node('span','cc-tour-orb',s.icon||'✦'),node('div','cc-tour-lines'));for(let j=0;j<3;j++)sample.lastChild.append(node('i'));
      scene.append(rail,sample);
      const content=node('div','cc-tour-content');const h=node('h2','',s.title);h.id='cc-tour-title';dialog.setAttribute('aria-labelledby',h.id);content.append(h,node('p','',s.text));
      const progress=node('div','cc-tour-progress');progress.setAttribute('aria-label',`Step ${i+1} of ${steps.length}`);steps.forEach((_,j)=>progress.append(node('i',j<=i?'done':'')));
      const footer=node('footer','cc-tour-actions'),back=node('button','cc-tour-back','Back'),next=node('button','cc-tour-next',i===steps.length-1?'Done':'Next');back.type=next.type='button';back.disabled=i===0;back.onclick=()=>{i--;draw()};next.onclick=()=>{if(i===steps.length-1)end();else{i++;draw()}};footer.append(back,next);
      dialog.replaceChildren(header,content,progress,footer);locate();requestAnimationFrame(locate);
      if(motion())dialog.animate([{opacity:.5,transform:'translateY(10px)'},{opacity:1,transform:'none'}],{duration:240,easing:'ease-out'});
      next.focus({preventScroll:true});
    }
    dialog.addEventListener('cancel',e=>{e.preventDefault();end()});
    dialog.addEventListener('keydown',e=>{if(e.key==='ArrowRight'){e.preventDefault();dialog.querySelector('.cc-tour-next').click()}else if(e.key==='ArrowLeft'&&i){e.preventDefault();i--;draw()}});
    window.addEventListener('resize',locate);window.addEventListener('scroll',locate,{passive:true});document.body.append(dialog);dialog.showModal();draw();
  }
  const configSteps=[
    {title:'Your setup, one place',text:'Simple keeps everyday settings close. Advanced adds fine design controls. The sidebar groups Configuration, Frontend and App management.',target:'#cfgmode',tabs:['Simple','Advanced','Sections'],icon:'⚙'},
    {title:'Choose who answers',text:'Model and key selects your provider and model. Demo is offline and free. Save a key only for a provider that needs one, then use Test connection.',target:'#seg',tabs:['Model','Key','Test'],icon:'✦'},
    {title:'Choose what to search',text:'Sources and APIs controls live web search and its provider keys. Local documents remain your evidence. Presets give you ready-made configurations to start from.',target:'#sec-search',tabs:['Sources','APIs','Presets'],icon:'⌕'},
    {title:'Make the words yours',text:'Wording changes the title, welcome text and logo. Fonts changes body and heading type. Empty text keeps the app default.',target:'#sec-wording',tabs:['Wording','Logo','Fonts'],icon:'Aa'},
    {title:'Give it your look',text:'Colors edits light and dark palettes. Background sets the page behind the chat. Shape and spacing controls corners, shadows and message style. Fine controls live in Advanced.',target:'#sec-colors',tabs:['Colors','Background','Shape'],icon:'◐'},
    {title:'Bring the details to life',text:'Emojis and icons sets avatars and buttons. Motion controls animation and speed. Layout arranges the chat and sidebar. Reduced-motion device preferences are always respected.',target:'#sec-emoji',tabs:['Emojis','Motion','Layout'],icon:'☺'},
    {title:'Keep your app in good shape',text:'Presets and states saves reusable looks. Document freshness checks local files. Budget limits usage. Portable app exports setup and configured documents, not keys or private chats.',target:'#sec-freshness',tabs:['Freshness','Budget','Portable'],icon:'↗'},
    {title:'Preview, then start chatting',text:'Live preview shows your changes without sending a message. All set? checks the current model, web and look. Open your chat when ready. Replay this guide any time from Guide.',target:'#sec-finish',tabs:['Preview','All set?','Chat'],icon:'✓'}
  ];
  const chatSteps=[
    {title:'Ask from your sources',text:'Add documents or a web link, then ask a question. Answers use the retrieved sources; check citations for important facts.',target:'#q',tabs:['Ask','Retrieve','Cite'],icon:'⌕'},
    {title:'Keep the conversation going',text:'Follow-ups use bounded context from this conversation. Start a new conversation for a fresh subject. History is not unlimited recall.',target:'#newTopic',tabs:['Question','Follow-up','Context'],icon:'↻'},
    {title:'Choose what stays with you',text:'Temporary chat saves no conversation. My profile adds optional background to saved chats. Configuration controls the model, sources and look.',target:'#profileBtn',tabs:['Temporary','Profile','Configure'],icon:'☺'}
  ];
  window.CCTour={chat:(replay=false,onClose)=>show({key:'cc_tour',title:'Quick tour',steps:chatSteps,replay,onClose}),config:(replay=false)=>show({key:'cc_cfg_tour_v1',title:'Configuration guide',steps:configSteps,replay})};
})();
