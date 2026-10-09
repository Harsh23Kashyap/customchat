/* Keys stay in the private workspace store, not YAML, DOM hydration or exports. */
(async () => {
 let section;for(let i=0;i<100;i++){section=document.getElementById('sec-search');if(section?.querySelector('.source-key-card'))break;await new Promise(r=>setTimeout(r,80))}if(!section)return;
 const headers={'Content-Type':'application/json'},token=localStorage.getItem('cc_token');if(token)headers.Authorization='Bearer '+token;
 async function api(body){const r=await fetch('/api/source-credentials',body?{method:'POST',headers,body:JSON.stringify(body)}:{headers});const d=await r.json();if(!r.ok)throw Error(d.error||'Cannot save source key');return d}
 const el=(tag,text)=>{const n=document.createElement(tag);if(text)n.textContent=text;return n};
 try {
  const d=await api();if(!d.credentials.length)return;
  for(let i=0;i<100&&!section.querySelector('.source-key-card');i++)await new Promise(r=>setTimeout(r,80));
  const box=el('section');box.className='native-source-keys';box.append(el('h3','Custom source credentials'),el('p','Keys stay private in this workspace. Save does not contact the service. Presence is not a validity check.'));
  for(const item of d.credentials){const card=el('div');card.className='source-key-card';const label=el('label',item.label+' · '+item.env);const input=el('input');input.type='password';input.autocomplete='off';input.placeholder='Paste API key';input.setAttribute('aria-label',item.label+' API key');label.append(input);card.append(el('small','Sends this header only to '+item.url.split('?')[0]+' when you run a source query.')); const status=el('small',item.has_key?'Key saved or supplied by host (not validated)':'Not filled (API key)');status.setAttribute('role','status');const row=el('div');row.className='keyrow';
   for(const clear of [false,true]){const button=el('button',clear?'Remove key':'Save key');button.type='button';button.className='go ghost';button.onclick=async()=>{button.disabled=true;try{const result=await api({source:item.source,env:item.env,...(clear?{clear:true}:{key:input.value})});input.value='';const current=result.credentials.find(x=>x.source===item.source&&x.env===item.env);status.textContent=current?.has_key?'Key saved or supplied by host (not validated)':'Not filled (API key)'}catch(e){status.textContent=e.message}finally{button.disabled=false}};row.append(button)}card.append(label,row,status);box.append(card)}
  section.prepend(box);
  new MutationObserver(()=>{if(!section.contains(box))section.prepend(box)}).observe(section,{childList:true});
 }catch(e){const warning=el('p',e.message);warning.setAttribute('role','status');section.prepend(warning)}
})();
