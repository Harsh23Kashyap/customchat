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
  const dialog=document.createElement("dialog");dialog.id="readingDialog";dialog.className="reading-dialog";
  const heading=document.createElement("h2");heading.textContent="Reading preferences";dialog.append(heading);
  const value=apply(load());
  for(const [name,title,options] of [["width","Answer width",[[600,"Narrow"],[720,"Standard"],[900,"Wide"]]],["size","Answer text",[[15,"15px"],[17,"17px"],[19,"19px"],[21,"21px"]]]]){
   const label=document.createElement("label");label.textContent=title+" ";const select=document.createElement("select");select.setAttribute("aria-label",title);
   for(const [n,text] of options){const option=document.createElement("option");option.value=n;option.textContent=text;option.selected=n===value[name];select.append(option)}
   select.onchange=()=>{value[name]=+select.value;apply(value);localStorage.setItem(key,JSON.stringify(value))};label.append(select);dialog.append(label);
  }
  const note=document.createElement("p");note.textContent="Saved on this browser. Scroll up while an answer streams to hold your place; use the down arrow to follow it again.";dialog.append(note);
  const close=document.createElement("button");close.textContent="Done";close.onclick=()=>dialog.close();dialog.append(close);
  dialog.addEventListener("close",()=>{dialog.remove();button.focus()});document.body.append(dialog);dialog.showModal();
 };
});
})();
