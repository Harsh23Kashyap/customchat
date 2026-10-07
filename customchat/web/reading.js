(() => {
"use strict";
const key="cc_reading";
function load(){try{return JSON.parse(localStorage.getItem(key)||"{}")}catch(_){return {}}}
function apply(v){
 const width=[600,720,900].includes(+v.width)?+v.width:720;
 const size=[15,17,19,21].includes(+v.size)?+v.size:17;
 document.documentElement.style.setProperty("--reading-width",width+"px");
 document.documentElement.style.setProperty("--reading-size",size+"px");
 return {width,size};
}
apply(load());
document.addEventListener("DOMContentLoaded",()=>{
 const button=document.getElementById("readingBtn");if(!button)return;
 button.onclick=()=>{
  if(document.getElementById("readingDialog"))return;
  const dialog=document.createElement("dialog");dialog.id="readingDialog";dialog.className="reading-dialog";dialog.setAttribute("aria-labelledby","readingTitle");
  const header=document.createElement("header");header.className="reading-head";
  const badge=document.createElement("span");badge.className="reading-badge";badge.textContent="Aa";
  const title=document.createElement("div");const heading=document.createElement("h2");heading.id="readingTitle";heading.textContent="Make room to read";
  const subtitle=document.createElement("p");subtitle.textContent="Your view. Your pace.";title.append(heading,subtitle);header.append(badge,title);dialog.append(header);
  const value=apply(load());const preview=document.createElement("div");preview.className="reading-preview";
  const caption=document.createElement("span");caption.textContent="LIVE PREVIEW";preview.append(caption);
  const sample=document.createElement("p");sample.textContent="A little space makes a long answer easier to follow.";preview.append(sample);
  function sync(){sample.style.fontSize=value.size+"px";preview.dataset.width=value.width;}
  for(const [name,label,options] of [["width","Answer width",[[600,"Narrow"],[720,"Standard"],[900,"Wide"]]],["size","Answer text",[[15,"Small"],[17,"Default"],[19,"Large"],[21,"Largest"]]]]){
   const group=document.createElement("fieldset");group.className="reading-options";const legend=document.createElement("legend");legend.textContent=label;group.append(legend);
   for(const [n,text] of options){const item=document.createElement("label");const input=document.createElement("input");input.type="radio";input.name="reading-"+name;input.value=n;input.checked=n===value[name];input.setAttribute("aria-label",label+": "+text);const span=document.createElement("span");span.textContent=text;
    input.onchange=()=>{if(input.checked){value[name]=+input.value;apply(value);localStorage.setItem(key,JSON.stringify(value));sync()}};item.append(input,span);group.append(item)}
   dialog.append(group);
  }
  sync();dialog.append(preview);
  const note=document.createElement("p");note.className="reading-note";note.textContent="Saved on this browser. Scroll up during an answer to hold your place.";dialog.append(note);
  const footer=document.createElement("footer");const close=document.createElement("button");close.className="reading-done";close.textContent="Done";close.onclick=()=>dialog.close();footer.append(close);dialog.append(footer);
  dialog.addEventListener("close",()=>{dialog.remove();button.focus()});document.body.append(dialog);dialog.showModal();
 };
});
})();
