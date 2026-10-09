(() => {
"use strict";
const $ = (s) => document.querySelector(s);
const NAMES = { mock: "Demo", ollama: "Ollama", openai: "OpenAI", claude: "Claude", gemini: "Gemini", openai_compatible: "Other", minimax: "MiniMax", mimo: "Xiaomi MiMo", deepseek: "DeepSeek", groq: "Groq", openrouter: "OpenRouter", mistral: "Mistral" };
let autoTimer = 0, testBlocked = false, cur = {}, canEdit = false, theme = null, saved = null, meta = null, editMode = "light";
const token = localStorage.getItem("cc_token") || "";
async function api(path, body) {
  const h = { "Content-Type": "application/json" }; if (token) h.Authorization = "Bearer " + token;
  const r = await fetch(path, body === undefined ? { headers: h } : { method: "POST", headers: h, body: JSON.stringify(body) });
  const d = await r.json().catch(() => ({})); if (!r.ok) throw new Error(d.error || "Request failed"); return d;
}
const say = (t, err) => { const m = $("#msg"); m.textContent = t; m.className = "msg" + (err ? " err" : ""); };
const el = (tag, props = {}, ...kids) => { const e = document.createElement(tag); for (const [k, v] of Object.entries(props)) { if (v === undefined || v === null) continue; if (k === "class") e.className = v; else if (k === "text") e.textContent = v; else if (k.startsWith("on")) e.addEventListener(k.slice(2), v); else e.setAttribute(k, v); } for (const c of kids.flat()) if (c != null) e.append(c.nodeType ? c : document.createTextNode(c)); return e; };

/* ---------- model section (unchanged behaviour) ---------- */
function draw() {
  $("#model").value = cur.model || ""; $("#base").value = cur.base_url || ""; $("#temp").value = cur.temperature; $("#topk").value = cur.top_k; $("#rewrite").checked = !!cur.query_rewrite;
  $("#tv").textContent = (+cur.temperature).toFixed(2); $("#kv").textContent = cur.top_k; sliderVisuals();
  document.querySelectorAll("#seg button").forEach((b) => b.setAttribute("aria-checked", String(b.dataset.p === cur.provider)));
  buildChips();
  provExtras();
  for (const id of ["model", "apikey", "keysave", "keyclear", "modelPick", "refreshModels", "testconn", "base", "temp", "topk", "rewrite", "apply", "load", "saveLook", "resetAll", "imp", "exportApp", "checkDocs", "saveBudget"]) $("#" + id).disabled = !canEdit; $("#testconn").disabled = !canEdit || testBlocked;
}
const read = () => ({ provider: cur.provider, model: chosenModel(), base_url: $("#base").value.trim(), temperature: +$("#temp").value, top_k: +$("#topk").value, query_rewrite: $("#rewrite").checked });
/* ---------- key, model picker, connection test ---------- */
let keyInfo = {}, modelNote = "";
const OTHER = "__other__";
async function provExtras() {
  const p = cur.provider, k = keyInfo[p] || { needed: false, has: true };
  $("#keybox").hidden = p === "mock" || p === "ollama"; { const bl = $("#base").closest("label"); if (bl) bl.hidden = !(p === "ollama" || p === "openai_compatible"); }
  $("#keyh").textContent = p === "openai_compatible" ? "Only if your server asks for one. Stored on this computer only, never shown again." : "Stored on this computer only, never shown again.";
  $("#apikey").placeholder = k.has ? "Saved key available. Enter only to replace it." : "Paste a key to save privately";
  const ks = $("#keystate"); ks.className = "keystate" + (k.has ? " ok" : "");
  ks.textContent = k.has ? (k.source === "env" ? "Key found in an environment variable." : "A key is saved.") : (k.needed ? "Not filled (no API key saved)." : "No key needed.");
  { const tc = $("#testconn"), blocked = !!(k.needed && !k.has); testBlocked = blocked; tc.disabled = blocked || !canEdit; tc.title = blocked ? "Save a key first, then test it" : ""; if (blocked) $("#testres").textContent = "Save a key first, then test."; else if ($("#testres").textContent === "Save a key first, then test.") $("#testres").textContent = ""; }
  $("#keyclear").hidden = k.source !== "saved"; $("#apikey").value = "";
  ollamaPanel();
  await loadModels(false);
}
async function loadModels(force) {
  const sel = $("#modelPick"), p = cur.provider; sel.replaceChildren();
  let list = [];
  try { const r = await api("/api/provider/models", { provider: p, base_url: $("#base").value.trim() }); list = r.models || []; modelNote = r.note || ""; } catch (e) { modelNote = e.message; }
  const m = cur.model || "";
  for (const n of list) sel.append(el("option", { value: n, text: n }));
  sel.append(el("option", { value: OTHER, text: list.length ? "Other (type a name)" : "Type a name" }));
  sel.value = list.includes(m) ? m : OTHER;
  const demo = p === "mock"; sel.hidden = demo; $("#refreshModels").hidden = demo; { const ml = document.querySelector("label[for=modelPick]"); if (ml) ml.hidden = demo; } { const kr = sel.closest(".keyrow"); if (kr) kr.hidden = demo; } const typed = !demo && sel.value === OTHER; $("#model").hidden = !typed; if (typed) $("#model").value = m;
  $("#modelh").textContent = demo ? "The demo answers without a model." : list.length ? list.length + (list.length === 1 ? " model found." : " models found.") : (modelNote || "Type the model name your provider uses.");
}
function sliderVisuals(){
  const t=document.getElementById("temperatureViz"), d=document.getElementById("sourcesViz");
  if(t)t.style.setProperty("--heat",Math.max(0,Math.min(1,+$("#temp").value/2)));
  if(d){const n=Math.min(5,Math.max(1,Math.ceil(+$("#topk").value/4)));d.replaceChildren(...Array.from({length:n},(_,i)=>el("i",{style:"--layer:"+i})));}
}
function pickChanged() { const v = $("#modelPick").value; const typed = v === OTHER; $("#model").hidden = !typed; if (!typed) { $("#model").value = v; cur.model = v; } }
const chosenModel = () => ($("#modelPick").value === OTHER ? $("#model").value.trim() : $("#modelPick").value);
const BRAND = { openai: ["#10a37f", "O"], claude: ["#d97757", "C"], gemini: ["#4285f4", "G"], ollama: ["#2b2b2b", "Ol"], deepseek: ["#4d6bfe", "D"], groq: ["#f55036", "Gq"], mistral: ["#fa520f", "M"], minimax: ["#e0245e", "Mx"], mimo: ["#ff6900", "Mi"], openrouter: ["#6467f2", "Or"], mock: ["#8a94a3", "\u2022"], openai_compatible: ["#5b6b7f", "+"] };
const TOP = ["openai", "claude", "gemini", "deepseek", "ollama"];
let chipsMore = false, chipList = [];
const LOGOS = ["openai", "claude", "gemini", "deepseek", "ollama", "groq", "mistral", "openrouter", "minimax", "mimo"];
function mark(p) { if (LOGOS.includes(p)) { const img=el("img", { class: "plogo", src: "/logos/" + p + ".svg", alt: "", width: "20", height: "20" }); img.addEventListener("error",()=>{const b=BRAND[p] || ["#667",p[0]];img.replaceWith(el("span",{class:"pm",style:"background:"+b[0],"aria-hidden":"true",text:b[1]}))},{once:true});return img; } const b = BRAND[p] || ["#667", (NAMES[p] || p)[0]]; return el("span", { class: "pm", style: "background:" + b[0], "aria-hidden": "true", text: b[1] }); }
function buildChips(list) {
  if (list) chipList = list; const seg = $("#seg"); seg.replaceChildren();
  const top = TOP.filter((p) => chipList.includes(p)), rest = chipList.filter((p) => !top.includes(p));
  // Keep the active provider visible without reopening a collapsed list.
  if (!top.includes(cur.provider) && chipList.includes(cur.provider)) top.push(cur.provider);
  const extra = rest.filter(p => !top.includes(p));
  for (const p of top.concat(chipsMore ? extra : [])) { const b = el("button", { type: "button", "data-p": p, role: "radio", "aria-checked": String(p === cur.provider) }, mark(p), NAMES[p] || p); b.addEventListener("click", () => { if (canEdit) { cur = { ...read(), provider: p, model: "" };$("#testres").textContent="";$("#testres").className="testres"; draw(); pvFollow(); } }); seg.append(b); }
  if (extra.length) { const m = el("button", { type: "button", class: "chipmore", "aria-expanded": String(chipsMore) }, chipsMore ? "Show fewer" : "Load more"); m.addEventListener("click", () => { chipsMore = !chipsMore; buildChips(); }); seg.append(m); }
}
/* ---------- local model suggestions (Ollama) ---------- */
let hwView = "simple";
/* Cloud picks, checked against the providers' own model pages on 5 Oct 2026:
   developers.openai.com/api/docs/models and ai.google.dev/gemini-api/docs/models */
const CLOUD_PICKS = [
  { p: "openai", id: "gpt-6.1-sol", name: "GPT-6.1 Sol", why: "Near-Astra performance at a lower cost, for complex coding, computer use and professional work." },
  { p: "gemini", id: "gemini-3.8-flash", name: "Gemini 3.8 Flash", why: "Google's most intelligent Flash model." },
]; const testLog = [];
async function ollamaPanel() {
  const box = $("#ollamabox"); if (activeSec !== "model") return; box.hidden = false; box.dataset.loaded = "1";
  box.replaceChildren(el("div", { class: "h", text: "Looking at this computer..." }));
  let r; try { r = await api("/api/hardware?base_url=" + encodeURIComponent($("#base").value.trim())); } catch (e) { box.dataset.loaded="";box.replaceChildren(el("b",{text:"Suggested local models"}),el("div",{class:"h",text:e.message}),el("button",{type:"button",class:"mini",text:"Retry local suggestions",onclick:ollamaPanel})); return; }
  const hw = r.hardware, rec = r.recommendation, det = hwView === "tech";
  const tabs = el("div", { class: "seg mini", role: "radiogroup", "aria-label": "Detail level" });
  for (const [v, t] of [["simple", "Simple"], ["tech", "Details"]]) tabs.append(el("button", { type: "button", role: "radio", "aria-checked": String(hwView === v), onclick: () => { hwView = v; ollamaPanel(); } }, t));
  const head = el("div", { class: "ohead" }, el("b", { text: "Suggested local models" }), tabs);
  const cards = el("div", { class: "ocards" });
  if (!rec.picks.length) cards.append(el("div", { class: "h", text: rec.note || "No suggestion available." }));
  rec.picks.forEach((p) => {
    const c = el("div", { class: "ocard fit-" + p.fit }, el("div", { class: "otag", text: p.label }), el("b", { text: p.name }), el("div", { class: "h", text: p.note }),
      el("div", { class: "fitchip " + p.fit }, el("i"), p.fit_why));
    if (det) c.append(el("div",{class:"model-metrics"},el("div",{class:"metric-head"},el("span",{text:"Memory budget"}),el("b",{text:p.uses_pct+"%"})),el("div",{class:"budget-track",role:"img","aria-label":p.uses_pct+"% of memory budget used, 85% fit limit"},el("i",{style:"width:"+Math.max(0,Math.min(100,p.uses_pct))+"%"}),el("span",{style:"left:85%"})),el("div",{class:"metric-foot"},el("b",{text:p.needs_gb+" GB needed"}),el("span",{text:rec.budget_gb+" GB budget"})),el("div",{class:"metric-row"},el("span",{},"↓ Download",el("b",{text:p.download_gb+" GB"})),el("span",{class:"speed",text:"Speed: "+p.speed})),el("small",{class:"model-tag",text:p.tag})));
    c.append(el("div", { class: "oact" }, modelAction(p.tag, p.installed)));
    cards.append(c);
  });
  box.replaceChildren(head, cards);
  if (canEdit) { $("#sec-model .ollama-setup")?.remove();const setup=el("section",{class:"ollama-setup"});$("#sec-model").prepend(setup);drawOllamaSetup(setup); }
  if (r.others && r.others.length) {
    const d = el("details", { class: "grp" }, el("summary", { text: "See other models" }), el("div", { class: "oother" }, r.others.map((o) => el("div", { class: "orow" }, el("span", { class: "fitdot " + o.fit }), el("span", { class: "oname", text: o.name }), el("span", { class: "h", text: o.why })))));
    box.append(d);
  }
  if (det) {
    const total=hw.gpu && hw.vram_gb ? hw.vram_gb : hw.ram_gb, pct=Math.max(0,Math.min(100,rec.budget_gb/Math.max(.1,total)*100));
    const graph=el("section",{class:"memory-graph","aria-label":"Model memory budget"},el("h3",{text:"Model memory budget"}),el("div",{class:"memory-label"},el("b",{text:total+" GB "+(hw.apple_silicon?"shared memory":hw.gpu?"GPU memory":"RAM")}),el("span",{text:hw.os+" · "+hw.cores+" CPU cores"})),el("div",{class:"memory-total",role:"img","aria-label":rec.budget_gb+" GB model budget, "+Math.max(0,total-rec.budget_gb).toFixed(1)+" GB reserve"},el("div",{class:"memory-available",style:"width:"+pct+"%;padding:"+(pct===0?0:4)+"px",text:pct>=20?rec.budget_gb+" GB model budget":""}),el("div",{class:"memory-reserve",style:"width:"+(100-pct)+"%",text:Math.max(0,total-rec.budget_gb).toFixed(1)+" GB reserve"})),el("small",{text:rec.budget_why}),el("h4",{text:"Safe fit inside that budget"}),el("div",{class:"memory-fit",role:"img","aria-label":"85% safe fit ceiling"},el("i",{style:"width:"+(rec.budget_gb>0?85:0)+"%"})),el("div",{class:"memory-label"},el("b",{text:rec.limit_gb+" GB fit ceiling"}),el("span",{text:rec.budget_gb+" GB budget"})),el("div",{class:"memory-thresholds"},el("span",{text:"Comfortable ≤60%"}),el("span",{text:"Fits ≤85%"}),el("span",{text:"Doesn't fit >85%"})),el("small",{text:"Includes about 1.5 GB for conversation overhead. Estimates, not measured free RAM."}),el("p",{text:"Ollama: "+(r.ollama_running?"running · "+(r.installed||[]).length+" models installed":"not reachable")}),el("small",{text:hw.os+" "+hw.arch}));
    if (rec.budget_gb === 0) graph.prepend(el("p",{text:"No safe model memory budget detected. Use a hosted provider or a larger computer."}));
    box.append(graph);
  }
  else box.append(el("div", { class: "h", text: "Rough estimate from " + hw.ram_gb + " GB of memory" + (hw.gpu ? " and your " + hw.gpu : "") + ". Choose Details to see the math." }));
  if (rec.note && rec.picks.length) box.append(el("div", { class: "h", text: rec.note }));
}
function modelAction(tag, installed) {
  const wrap = el("div", { class: "mact" });
  const use = () => { cur = {...read(),provider:"ollama",model:tag,base_url:cur.provider==="ollama"?$("#base").value.trim():"http://localhost:11434"};draw();loadModels(true).then(() => { const pick=$("#modelPick");pick.value=[...pick.options].some(o=>o.value===tag)?tag:OTHER;$("#model").value=tag;pickChanged();pvFollow(); }); };
  if (installed) { wrap.append(el("span", { class: "okt", text: "Installed" }), el("button", { type: "button", class: "mini", onclick: use }, "Use this model")); return wrap; }
  const bar = el("div", { class: "pbar", hidden: "" }, el("i")), msg = el("span", { class: "h" });
  const btn = el("button", { type: "button", class: "mini dl", disabled: canEdit ? undefined : "" }, "Download");
  let pullId="";const cancel=el("button",{type:"button",class:"mini",text:"Cancel download",hidden:"",onclick:async()=>{cancel.disabled=true;msg.textContent="Cancelling...";try{await api("/api/ollama/pull/cancel",{id:pullId})}catch(e){cancel.disabled=false;msg.textContent=e.message}}});
  btn.addEventListener("click", async () => {
    btn.disabled = true; bar.hidden = false; msg.textContent = "Starting...";
    try {
      const plan=await api('/api/ollama/pull/review',{model:tag,base_url:$("#base").value.trim()});
      const reviewText='Download '+plan.model+'?\n\nApproximate download: '+(plan.download_gb_estimate??'unknown')+' GB. Free disk: '+plan.free_disk_gb+' GB. Memory estimate: '+(plan.memory_need_gb_estimate??'unknown')+' GB; fit: '+plan.fit+'.\n'+plan.location_note+'\n'+plan.notice;
      if(!window.confirm(reviewText)){btn.disabled=false;bar.hidden=true;msg.textContent='Download not started.';return}
      const { id } = await api('/api/ollama/pull/execute',{ticket:plan.ticket,confirmed:true});
      pullId=id;cancel.hidden=false;cancel.disabled=false;
      for (;;) {
        await new Promise((r) => setTimeout(r, 700));
        const st = await api("/api/ollama/pull?id=" + id);
        bar.firstChild.style.width = st.pct + "%"; msg.textContent = st.error || (st.done ? "Done" : (st.status || "Downloading") + " " + st.pct + "%");
        if(st.cancelled&&st.done){cancel.hidden=true;bar.hidden=true;btn.disabled=false;btn.textContent="Retry download";msg.textContent="Cancelled. Retry rechecks the model; Ollama decides whether partial files can be reused.";break}
        if (st.error) { cancel.hidden=true; btn.disabled = false; btn.textContent = "Try again"; bar.hidden = true; msg.className = "h bad"; break; }
        if (st.done) { cancel.hidden=true;wrap.replaceChildren(el("span", { class: "okt", text: "Installed" }), el("button", { type: "button", class: "mini", onclick: use }, "Use this model")); use(); break; }
      }
    } catch (e) { cancel.hidden=true; btn.disabled = false; bar.hidden = true; msg.textContent = e.message; msg.className = "h bad"; }
  });
  wrap.append(btn, cancel, bar, msg); return wrap;
}
function syncDeleteLook(){const name=$("#states").value,btn=$("#del");btn.disabled=!name||!canEdit;btn.textContent=name?'Delete "'+name+'"':'Choose a saved look to delete';}
async function states() {
  const data = await api("/api/states"), s=data.states; const sel = $("#states"); sel.replaceChildren();
  sel.append(el("option", { value: "", text: "Current look (not a named snapshot)" })); s.forEach((n) => sel.append(el("option", { value: n, text: n })));sel.value=data.current||"";syncDeleteLook();
}

/* ---------- look: every setting, with a plain explanation ---------- */
const C = (k, label, help) => ({ key: k, label, help, type: "color", colors: true });
const SECTIONS = [
  { id: "wording", icon: "Aa", tone: "green", title: "Wording", sub: "The words people read", help: "Leave a box empty to keep the default text from the app file.", fields: [
    { key: "logo_watermark", label: "Subtle logo watermark", help: "Optional background mark. It does not cover chat text and can be turned off.", type: "toggle" },
    { key: "logo", label: "Logo", help: "Optional. Choose a picture; it blends into the page.", type: "logo" },
    { key: "txt_title", label: "App name", help: "Shown in the top bar, the welcome screen and the browser tab.", type: "text", ph: "Blank uses the app default" },
    { key: "txt_tagline", label: "Welcome line", help: "The sentence under the name on an empty chat.", type: "text", ph: "Blank uses the app default" },
    { key: "txt_examples", label: "Example questions", help: "One per line (up to 8). They appear as buttons on an empty chat.", type: "area" },
    { key: "txt_placeholder", label: "Question box hint", help: "The grey text inside the question box.", type: "text", ph: "Ask a question" },
    { key: "txt_hint", label: "Small line under the box (left)", help: "A short reminder under the question box.", type: "text" },
    { key: "txt_disclaimer", label: "Small line under the box (right)", help: "For example a disclaimer.", type: "text" },
    { key: "txt_sidebar", label: "Sidebar heading", help: "The title above your chat list.", type: "text", ph: "Conversations" },
    { key: "txt_footer", label: "Sidebar footer note", help: "Text at the bottom of the sidebar.", type: "text" } ] },
  { id: "colors", icon: "\u25D0", tone: "blue", title: "Colors", sub: "Every color, for light and dark", help: "Pick which set you are editing with the Light / Dark switch. The mode setting decides which set people see.", modeTabs: true, fields: [
    { key: "mode", label: "Which set to show", help: "Light, dark, or follow the person's device. Visitors can still flip it with the sun/moon button.", type: "select" },
    C("brand", "Main color", "Titles, your messages, buttons and links."),
    C("accent", "Accent color", "The send button and small highlights."),
    C("bg", "Page background", "Behind everything."),
    C("surface", "Cards and chat area", "The big panel the chat sits on."),
    C("ink", "Text", "Main reading color."),
    C("muted", "Soft text", "Captions and hints."),
    C("line", "Lines", "Borders and dividers."),
    C("sidebar", "Sidebar", "Background of the chat list."),
    C("bot", "Assistant message", "Background of the answers."),
    C("you", "Your avatar", "Background behind your initial."),
    C("danger", "Warning color", "Errors and delete.") ] },
  { id: "background", icon: "\u25A6", tone: "purple", title: "Background", sub: "The page behind the chat", help: "Pick a style, then optionally lay a pattern over it.", fields: [
    { key: "bg_style", label: "Background style", help: "Plain color is the default. Image needs an https link.", type: "select" },
    { key: "bg_color2", label: "Gradient second color", help: "Used by the gradient style.", type: "color" },
    { key: "bg_angle", label: "Gradient angle", help: "Direction of the gradient in degrees.", type: "range", unit: "\u00B0" },
    { key: "bg_image", label: "Image link", help: "https link to a picture, shown softly behind everything.", type: "text", ph: "https://..." },
    { key: "pattern", label: "Pattern", help: "A repeating texture over the background.", type: "select" },
    { key: "pattern_color", label: "Pattern color", help: "Leave on automatic to use the text color.", type: "color", clearable: true },
    { key: "pattern_opacity", label: "Pattern strength", help: "How visible the pattern is.", type: "range", unit: "%" },
    { key: "pattern_size", label: "Pattern size", help: "Spacing of the pattern in pixels.", type: "range", unit: "px" } ] },
  { id: "fonts", icon: "T", tone: "green", title: "Fonts", sub: "How words look", help: "Fonts load from Google Fonts. Offline, the fallback is a similar system font.", fields: [
    { key: "font", label: "Body font", help: "Used for messages and buttons.", type: "select", fonts: true },
    { key: "heading_font", label: "Heading font", help: "Used for titles and the welcome name.", type: "select", fonts: true },
    { key: "custom_font", label: "Custom Google font name", help: "Type a family name exactly as on fonts.google.com, then choose Custom above.", type: "text", ph: "e.g. Merriweather" },
    { key: "font_size", label: "Text size", help: "Makes all text larger or smaller.", type: "range", unit: "%" },
    { key: "line_height", label: "Line spacing", help: "Space between lines of text.", type: "range", unit: "%" } ] },
  { id: "shape", icon: "\u25A2", tone: "blue", title: "Shape and spacing", sub: "Corners, shadows, message style", help: "Small changes here make the whole app feel different.", fields: [
    { key: "radius", label: "Corner roundness", help: "0 is sharp. 100 is the default. Up to 160 is rounder.", type: "range", unit: "%" },
    { key: "density", label: "Spacing", help: "Compact fits more on screen. Roomy is airy.", type: "select" },
    { key: "shadow", label: "Shadow", help: "Depth of the main panel.", type: "select" },
    { key: "bubble", label: "Message style", help: "Soft: filled bubbles. Flat: no bubble for answers. Outline: thin borders.", type: "select" } ] },
  { id: "emoji", icon: "\u263A", tone: "purple", title: "Emojis and icons", sub: "Avatars and buttons", help: "Choose an emoji. Use app default to reset.", fields: [
    { key: "emoji_bot", label: "Assistant avatar", help: "Next to every answer.", type: "emoji", ph: "Optional" },
    { key: "emoji_you", label: "Your avatar", help: "Next to your messages.", type: "emoji", ph: "Optional" },
    { key: "emoji_hero", label: "Welcome emoji", help: "On an empty chat. Falls back to the assistant avatar.", type: "emoji", ph: "Optional" },
    { key: "emoji_send", label: "Send button", help: "Replaces the arrow.", type: "emoji", ph: "Optional" },
    { key: "emoji_attach", label: "Attach button", help: "Replaces the paperclip.", type: "emoji", ph: "Optional" },
    { key: "emoji_temp", label: "Temporary chat button", help: "Replaces the clock icon.", type: "emoji", ph: "Optional" } ] },
  { id: "motion", icon: "\u21BB", tone: "green", title: "Motion", sub: "Animations and speed", help: "Turn animation down if it feels busy. Visitors whose device asks for less motion always get none.", fields: [
    { key: "motion", label: "Amount of motion", help: "Full: all effects. Subtle: quick and quiet. Calm: no decorative motion, stable reading. None: nothing moves. Your device's reduced-motion setting always overrides Full.", type: "select" },
    { key: "entrance", label: "New message effect", help: "How messages appear.", type: "select" },
    { key: "speed", label: "Animation speed", help: "100 is normal. Higher is faster.", type: "range", unit: "%" },
    { key: "hover_lift", label: "Lift items on hover", help: "Buttons and chips rise slightly under the mouse.", type: "toggle" } ] },
  { id: "layout", icon: "\u25EB", tone: "blue", title: "Layout", sub: "Where things sit", help: "Arrange the screen to suit how you work.", fields: [
    { key: "sidebar", label: "Sidebar position", help: "Left, right, or hidden until you press the menu button.", type: "select" },
    { key: "sidebar_width", label: "Sidebar width", help: "In pixels. You can also drag its edge in the chat.", type: "range", unit: "px" },
    { key: "chat_width", label: "Chat width", help: "How wide the conversation column is.", type: "select" },
    { key: "avatars", label: "Avatars", help: "Show or hide the small pictures next to messages.", type: "select" },
    { key: "you_align", label: "Your messages", help: "On the right like a phone, or on the left like a document.", type: "select" },
    { key: "composer", label: "Question box", help: "Inline: attached to the bottom bar. Floating: a card over the chat.", type: "select" },
    { key: "toolbar", label: "Top bar", help: "Hide it for a cleaner look. The Configuration page stays at /settings.html.", type: "select" },
    { key: "sources_panel", label: "Sources side panel", help: "The panel that opens when you click a source.", type: "toggle" } ] },
];
const LABELS = { mode: { light: "Light", dark: "Dark", auto: "Match the device" }, bg_style: { soft: "Soft glow (legacy)", solid: "Plain color", gradient: "Two-color gradient", image: "Image" },
  pattern: { none: "None", dots: "Dots", grid: "Grid", lines: "Lines", diagonal: "Diagonal", checker: "Checker", waves: "Waves", plus: "Plus signs" }, motion: { full: "Full", subtle: "Subtle", calm: "Calm", none: "None" },
  entrance: { fade: "Fade in", slide: "Slide up", pop: "Pop", none: "None" }, bubble: { soft: "Soft bubbles", flat: "Flat", outline: "Outline" }, density: { compact: "Compact", cozy: "Cozy", roomy: "Roomy" },
  sidebar: { left: "Left", right: "Right", hidden: "Hidden" }, chat_width: { narrow: "Narrow", normal: "Normal", wide: "Wide", full: "Full width" }, avatars: { show: "Show", hide: "Hide" },
  you_align: { right: "Right", left: "Left" }, shadow: { none: "None", soft: "Soft", strong: "Strong" }, composer: { inline: "Inline", floating: "Floating" }, toolbar: { show: "Show", hide: "Hide" } };
const FONTNAMES = { "dm-sans": "DM Sans", inter: "Inter", system: "System default", georgia: "Georgia", fraunces: "Fraunces", playfair: "Playfair Display", lora: "Lora", "space-grotesk": "Space Grotesk", nunito: "Nunito", poppins: "Poppins", jetbrains: "JetBrains Mono", mono: "System monospace", custom: "Custom (type a name below)" };

const PRESETS = {
  Forest: { font: "dm-sans", heading_font: "fraunces" },
  Ocean: { light: { brand: "#0b3d66", accent: "#7fd1f5", bg: "#eef6fb", surface: "#ffffff", ink: "#0f2231", muted: "#5b7285", line: "#d3e2ed", sidebar: "#e1eef7", bot: "#eef5fa", you: "#cfe3f1" }, dark: { brand: "#7fc4f0", accent: "#7fd1f5", bg: "#0a1620", surface: "#0f1f2c", ink: "#e6f1f8", muted: "#8aa4b6", line: "#1e3446", sidebar: "#12263a", bot: "#142a3b", you: "#22425a" }, font: "inter", heading_font: "inter", bg_style: "gradient", bg_color2: "#d8ecf8", radius: 120 },
  Sunset: { light: { brand: "#7a2e1d", accent: "#ffb86b", bg: "#fff4ea", surface: "#fffaf5", ink: "#2b1810", muted: "#8a6a5c", line: "#f0d9c8", sidebar: "#fbe6d3", bot: "#fbeee2", you: "#f5d3b5" }, font: "poppins", heading_font: "playfair", bg_style: "gradient", bg_color2: "#ffd9c2", bg_angle: 135, radius: 140, pattern: "dots", pattern_opacity: 10 },
  Mono: { light: { brand: "#111111", accent: "#e5e5e5", bg: "#f4f4f4", surface: "#ffffff", ink: "#111111", muted: "#6b6b6b", line: "#dddddd", sidebar: "#eeeeee", bot: "#f3f3f3", you: "#e2e2e2", danger: "#aa2222" }, font: "jetbrains", heading_font: "jetbrains", bg_style: "solid", radius: 30, bubble: "outline", shadow: "none", pattern: "grid", pattern_opacity: 6 },
  Midnight: { mode: "dark", dark: { brand: "#b8a6ff", accent: "#ff8fd8", bg: "#0b0b17", surface: "#12122a", ink: "#ececff", muted: "#9a9ac4", line: "#27274a", sidebar: "#0f0f22", bot: "#181838", you: "#2a2a58" }, font: "space-grotesk", heading_font: "space-grotesk", bg_style: "gradient", bg_color2: "#1a1040", radius: 130, shadow: "strong", pattern: "dots", pattern_opacity: 14 },
  Paper: { light: { brand: "#3b2f23", accent: "#e0c48a", bg: "#f6efe0", surface: "#fbf7ec", ink: "#2a2118", muted: "#7d6e5c", line: "#e2d6bd", sidebar: "#eee3cc", bot: "#f1e8d3", you: "#e4d5b4" }, font: "lora", heading_font: "playfair", bg_style: "solid", radius: 40, bubble: "flat", shadow: "soft", pattern: "lines", pattern_size: 28, pattern_opacity: 8 },
};
const MORE_PRESETS = {
  Lavender: { light: { brand: "#4b3f8f", accent: "#cbbcff", bg: "#f6f3fc", surface: "#fdfcff", ink: "#221c3a", muted: "#6f688f", line: "#e2dcf2", sidebar: "#ece7f8", bot: "#f1edfa", you: "#ddd4f3" }, font: "nunito", heading_font: "fraunces", bg_style: "solid", radius: 60, bubble: "flat", shadow: "soft" },
  Slate: { light: { brand: "#2f3e4e", accent: "#9fb6c9", bg: "#f2f4f6", surface: "#ffffff", ink: "#182430", muted: "#66737f", line: "#d9dfe5", sidebar: "#e7ebef", bot: "#eef1f4", you: "#d5dde5" }, font: "inter", heading_font: "inter", bg_style: "solid", radius: 30, bubble: "flat", shadow: "none" },
  Terracotta: { light: { brand: "#9c4a2f", accent: "#e8b79a", bg: "#faf1ea", surface: "#fffaf6", ink: "#33201a", muted: "#8a6c60", line: "#ecd6c8", sidebar: "#f3e0d3", bot: "#f7e9de", you: "#ecc9b3" }, font: "lora", heading_font: "fraunces", bg_style: "solid", radius: 50, bubble: "flat", shadow: "soft" },
  Matcha: { light: { brand: "#4a5d23", accent: "#c9dc8a", bg: "#f4f6ea", surface: "#fbfcf5", ink: "#222a12", muted: "#6c7656", line: "#dde3c6", sidebar: "#e9eed6", bot: "#eff2df", you: "#d8e2b5" }, font: "dm-sans", heading_font: "playfair", bg_style: "solid", radius: 70, bubble: "flat", shadow: "soft" },
  Rose: { light: { brand: "#8a2f4d", accent: "#f2b5c8", bg: "#fcf2f5", surface: "#fffafb", ink: "#33161f", muted: "#8d6874", line: "#f0d6de", sidebar: "#f8e4ea", bot: "#f9e9ee", you: "#f0c9d5" }, font: "poppins", heading_font: "playfair", bg_style: "solid", radius: 80, bubble: "flat", shadow: "soft" },
  Nord: { mode: "dark", dark: { brand: "#88c0d0", accent: "#a3be8c", bg: "#20262f", surface: "#2a313c", ink: "#e5e9f0", muted: "#9aa5b8", line: "#3b4252", sidebar: "#252b35", bot: "#303846", you: "#3b4658" }, font: "inter", heading_font: "inter", bg_style: "solid", radius: 40, bubble: "flat", shadow: "none" },
  Ink: { mode: "dark", dark: { brand: "#f2f2f2", accent: "#d4af37", bg: "#0c0c0c", surface: "#151515", ink: "#f2f2f2", muted: "#a0a0a0", line: "#2a2a2a", sidebar: "#111111", bot: "#1b1b1b", you: "#2a2a2a" }, font: "lora", heading_font: "playfair", bg_style: "solid", radius: 20, bubble: "flat", shadow: "none" },
  Sand: { light: { brand: "#6b5a3e", accent: "#d9c7a0", bg: "#f7f3ea", surface: "#fdfbf6", ink: "#2b2619", muted: "#847a66", line: "#e6dfcc", sidebar: "#efe9d9", bot: "#f3eee0", you: "#e3d9bd" }, font: "georgia", heading_font: "georgia", bg_style: "solid", radius: 30, bubble: "flat", shadow: "none" }
};
/* How each tab is organised: [group title, [keys], collapsed-by-default] */
const GROUPS = {
  wording: [["Basics", ["logo", "logo_watermark", "txt_title", "txt_tagline"]], ["More wording", ["txt_examples", "txt_placeholder", "txt_hint", "txt_disclaimer", "txt_sidebar", "txt_footer"], true]],
  colors: [["Mode", ["mode"]], ["Colors", ["brand", "bg"]], ["More colors", ["accent", "surface", "sidebar", "ink", "muted", "line", "bot", "you", "danger"], true]],
  background: [["Style", ["bg_style", "bg_color2"]], ["More background options", ["bg_angle", "bg_image", "pattern", "pattern_color", "pattern_opacity", "pattern_size"], true]],
  fonts: [["Fonts", ["font", "heading_font"]], ["More font options", ["custom_font", "font_size", "line_height"], true]],
  shape: [["Shape", ["radius", "density"]], ["More shape options", ["shadow", "bubble"], true]],
  emoji: [["Icons (optional)", ["emoji_bot", "emoji_you", "emoji_send", "emoji_hero", "emoji_attach", "emoji_temp"], true]],
  motion: [["Motion", ["motion"]], ["More motion options", ["entrance", "speed", "hover_lift"], true]],
  layout: [["Layout", ["sidebar", "chat_width"]], ["More layout options", ["sidebar_width", "avatars", "you_align", "composer", "toolbar", "sources_panel"], true]]
};
const clone = (o) => JSON.parse(JSON.stringify(o));
const effectiveWording = () => {const a=window.CCLoadedApp?.app||{};return {txt_title:a.title,txt_tagline:a.tagline,txt_examples:(a.examples||[]).join("\n"),txt_footer:a.footer,txt_placeholder:"Ask a question",txt_hint:"Answers cite their sources. Check important facts.",txt_disclaimer:"Not a substitute for professional advice.",txt_sidebar:"Conversations"};};
const get = (f) => (f.colors ? theme[editMode][f.key] : theme[f.key] || effectiveWording()[f.key] || theme[f.key]);
const setv = (f, v) => { const empty=document.getElementById("f-"+f.key)?.closest(".field")?.querySelector(".empty-field");if(empty)empty.hidden=!!v; if (f.colors) theme[editMode][f.key] = v; else theme[f.key] = v; changed(); };
let sendTimer = 0;
function pushPreview() {
  const t = clone(theme); const m = $("#pvmode .seg button[aria-checked=true], #pvmode button[aria-checked=true]"); t.mode = m ? m.dataset.m : t.mode;
  const frame=$("#pv");const reduced=matchMedia("(prefers-reduced-motion:reduce)").matches||["calm","none"].includes(t.motion);
  if(!reduced){frame.classList.add("preview-changing");setTimeout(()=>frame.classList.remove("preview-changing"),160)}
  const w = $("#pv").contentWindow; if (w) w.postMessage({ ccTheme: t }, location.origin);
  const w2 = $("#pv").contentWindow; if (w2 && w2.CCTheme) { /* same-origin: also apply the wording/emoji source */ w2.CCTheme.apply(t); }
}
function updateVis() {
  if (!theme) return; const st = theme.bg_style, pt = theme.pattern;
  const show = { bg_color2: st === "gradient", bg_angle: st === "gradient", bg_image: st === "image", pattern_color: !!pt && pt !== "none", pattern_opacity: !!pt && pt !== "none", pattern_size: !!pt && pt !== "none" };
  document.querySelectorAll("[data-k]").forEach((e) => { if (e.dataset.k in show) e.hidden = !show[e.dataset.k]; });
}
function changed() {
  updateVis();syncPreset();
  clearTimeout(sendTimer); sendTimer = setTimeout(pushPreview, 40); pvExtra(); setTimeout(pvExtra, 350);
  const dirty = JSON.stringify(theme) !== JSON.stringify(saved);
  $("#dirty").textContent = dirty ? "Saving..." : "All changes saved"; $("#dirty").className = dirty ? "dirty" : ""; $("#savebar").classList.toggle("clean", !dirty);
  clearTimeout(autoTimer); if (dirty && canEdit) autoTimer = setTimeout(async () => { const snap = clone(theme); try { await api("/api/theme", { theme: snap }); saved = clone(snap); const d = $("#dirty"); if (JSON.stringify(theme) === JSON.stringify(saved)) { d.textContent = "All changes saved"; d.className = ""; $("#savebar").classList.add("clean"); say("Saved. The chat now uses it."); } } catch (e) { say(e.message, true); } }, 1500);
}
/* Logo: everything happens in the browser. The picture is shrunk, its plain background can be removed,
   and its edges are feathered so it melts into the page instead of sitting in a hard box. */
function logoControl(f, current) {
  let orig = null; const st = { feather: 25, strip: false };
  const prev = el("img", { class: "logoprev", alt: "Result", hidden: current ? undefined : "" }); if (current) prev.src = current;
  const before = el("img", { class: "logoprev", alt: "Original", hidden: "" }), onpage = el("div", { class: "logopage", hidden: current ? undefined : "" }), pgimg = el("img", { alt: "" }), pgname = el("span");
  onpage.append(pgimg, pgname); if (current) pgimg.src = current;
  const paintPage = () => { const c = theme.light || {}; onpage.style.background = c.bg || "#f8f4e9"; onpage.style.color = c.ink || "#222"; pgname.textContent = theme.txt_title || "Your app"; };
  paintPage();
  const stage = el("div", { class: "logostage", hidden: current ? undefined : "" }, el("figure", {}, before, el("figcaption", { text: "Original" })), el("figure", {}, prev, el("figcaption", { text: "After blending" })), el("figure", {}, onpage, el("figcaption", { text: "In your app" })));
  const file = el("input", { type: "file", accept: ".png,.jpg,.jpeg,.webp,.gif,image/*", id: "f-logo-file", "aria-label": "Choose a logo picture" }); file.style.cssText = "position:absolute;width:1px;height:1px;opacity:0;pointer-events:none"; const fileBtn = el("label", { class: "go ghost filebtn", for: "f-logo-file" }, "Choose a picture");
  const fe = el("input", { type: "range", min: "0", max: "50", value: "25", "aria-label": "Edge softness", disabled: "" });
  const rb = el("input", { type: "checkbox", disabled: "" });
  const note = el("div", { class: "h", text: current ? "Choose a new picture to adjust it." : "PNG, JPG, WebP or GIF. Stays on this computer." });
  const rm = el("button", { type: "button", class: "mini", hidden: current ? undefined : "" }, "Remove");
  function render() {
    if (!orig) return; const max = 256, k = Math.min(1, max / Math.max(orig.width, orig.height));
    const w = Math.max(8, Math.round(orig.width * k)), h = Math.max(8, Math.round(orig.height * k));
    const c = document.createElement("canvas"); c.width = w; c.height = h; const x = c.getContext("2d", { willReadFrequently: true }); x.drawImage(orig, 0, 0, w, h);
    const im = x.getImageData(0, 0, w, h), d = im.data;
    const corner = [[0, 0], [w - 1, 0], [0, h - 1], [w - 1, h - 1]].map(([cx, cy]) => { const i = (cy * w + cx) * 4; return [d[i], d[i + 1], d[i + 2]]; });
    const bg = [0, 1, 2].map((j) => corner.reduce((a, c2) => a + c2[j], 0) / 4);
    const edge = (st.feather / 100) * Math.min(w, h) / 2 || 0;
    for (let yy = 0; yy < h; yy++) for (let xx = 0; xx < w; xx++) {
      const i = (yy * w + xx) * 4; let a = d[i + 3] / 255;
      if (st.strip) { const dist = Math.hypot(d[i] - bg[0], d[i + 1] - bg[1], d[i + 2] - bg[2]); const t = Math.min(1, Math.max(0, (dist - 28) / 52)); a *= t * t * (3 - 2 * t); }
      if (edge > 0) { const e = Math.min(xx, yy, w - 1 - xx, h - 1 - yy); const t = Math.min(1, e / edge); a *= t * t * (3 - 2 * t); }
      d[i + 3] = Math.round(a * 255);
    }
    x.putImageData(im, 0, 0); let url = c.toDataURL("image/png");
    if (url.length > 280000) { c.width = 128; c.height = Math.round(128 * h / w); const y = c.getContext("2d"); y.drawImage(orig, 0, 0, c.width, c.height); url = c.toDataURL("image/png"); }
    prev.src = url; prev.hidden = false; pgimg.src = url; onpage.hidden = false; paintPage(); rm.hidden = false; setv(f, url);
  }
  file.addEventListener("change", () => {
    const fl = file.files[0]; if (!fl) return;file.value="";if(fl.size>20000000){note.textContent="That picture is over 20 MB. Choose a smaller one.";say(note.textContent,true);return}note.textContent="Reading "+fl.name+"...";
    const im = new Image();
    im.onload = () => { orig = im; before.src = im.src; before.hidden = false; stage.hidden = false; fe.disabled = rb.disabled = false; note.textContent = "Soft edges and background removal run on this computer."; try{render();derive.disabled=false;note.textContent="Added "+fl.name+". Preview updated.";say(note.textContent)}catch(error){note.textContent="Could not process this picture: "+error.message;say(note.textContent,true)}; /* keep the object URL while the Original tile shows it */ };
    im.onerror=()=>{note.textContent="Could not decode "+fl.name+". Export it as PNG or JPG and try again.";say(note.textContent,true)};
    const reader=new FileReader();reader.onload=()=>{im.src=reader.result};reader.onerror=()=>{note.textContent="Cannot read "+fl.name+". Download it from iCloud locally, then try again.";say(note.textContent,true)};reader.readAsDataURL(fl);
  });
  fe.addEventListener("input", () => { st.feather = +fe.value; render(); });
  rb.addEventListener("change", () => { st.strip = rb.checked; render(); });
  rm.addEventListener("click", () => { orig = null; prev.classList.add("leave"); setTimeout(() => { prev.hidden = true; prev.classList.remove("leave"); }, 180); before.hidden = true; onpage.hidden = true; rm.hidden = true; fe.disabled = rb.disabled = true; file.value = ""; setv(f, ""); });
  const derive = el("button", {type:"button",class:"go ghost",disabled:current ? undefined : ""}, "Build colors from logo");
  derive.addEventListener("click", () => {
    if (!prev.src || !window.CCBrand) return;
    const image = new Image(); image.onload = () => {
      const canvas = document.createElement("canvas"); canvas.width = canvas.height = 64;
      const ctx = canvas.getContext("2d", {willReadFrequently:true}); ctx.drawImage(image,0,0,64,64);
      const seed = CCBrand.seed(ctx.getImageData(0,0,64,64).data);
      theme.light = CCBrand.palette(seed,false); theme.dark = CCBrand.palette(seed,true);
      changed(); paintPage();
      say("Light and dark palettes are ready in the preview. Text contrast is at least 4.5:1 on generated surfaces. Colors remain editable. Save look to keep them.");
    }; image.src = prev.src;
  });
  file.addEventListener("change", () => { derive.disabled = false; });
  rm.addEventListener("click", () => { derive.disabled = true; theme.logo_watermark = false; changed(); });
  const box = el("div", { class: "logobox" });
  const take = (fl) => { if (!fl || !/^image\//.test(fl.type)) { say("Drop a PNG, JPG, WebP or GIF picture.", true); return; } const dt = new DataTransfer(); dt.items.add(fl); file.files = dt.files; file.dispatchEvent(new Event("change")); };
  let depth = 0; const over = (on) => box.classList.toggle("dragover", on);
  box.addEventListener("dragenter", (e) => { e.preventDefault(); depth++; over(true); });
  box.addEventListener("dragover", (e) => { e.preventDefault(); e.dataTransfer.dropEffect = "copy"; });
  box.addEventListener("dragleave", () => { if (--depth <= 0) { depth = 0; over(false); } });
  box.addEventListener("drop", (e) => { e.preventDefault(); depth = 0; over(false); take(e.dataTransfer.files[0]); });
  box.append(stage, el("div", { class: "logoctl" }, fileBtn, el("span", { class: "h dropnote", text: "or drag a picture here" }), file, el("label", { class: "check" }, rb, "Remove plain background"), el("label", { class: "h" }, "Edge softness", fe), derive, el("span", {class:"h",text:"Replaces both palettes in the preview. Save look to keep; edit Colors for overrides. Logo also becomes the favicon."}), note, rm));
  return box;
}
const EMOJI_GROUPS={
 "Smileys":[["😀","grin happy"],["😃","smile"],["😄","laugh"],["😁","beaming"],["😂","joy tears"],["🥹","happy tears"],["😊","blush"],["😍","heart eyes love"],["🥰","love"],["😎","cool"],["🤓","nerd"],["🤔","thinking"],["🫡","salute"],["🤗","hug"],["🥳","party"],["🤯","mind blown"],["😴","sleep"],["😭","cry"],["😮","wow"],["😌","relief"]],
 "People":[["👋","wave hello"],["👍","thumbs up yes"],["👎","thumbs down no"],["👏","clap"],["🙌","celebrate"],["🙏","thanks please"],["💪","strong"],["🤝","handshake"],["🧑‍💻","developer"],["🧑‍🚀","astronaut"],["🕺","dance"],["🤖","robot assistant"]],
 "Nature":[["🐶","dog"],["🐱","cat"],["🦊","fox"],["🐼","panda"],["🐸","frog"],["🦋","butterfly"],["🌱","seedling plant"],["🌻","sunflower"],["🌈","rainbow"],["☀️","sun"],["🌙","moon"],["⭐","star"]],
 "Food":[["☕","coffee"],["🍵","tea"],["🍕","pizza"],["🍔","burger"],["🍎","apple"],["🥑","avocado"],["🍪","cookie"],["🎂","cake"]],
 "Objects":[["🚀","rocket launch"],["🎉","tada party"],["🎊","confetti"],["🔥","fire"],["💡","idea bulb"],["📚","books"],["📄","document"],["📎","attachment paperclip"],["💬","chat"],["🔍","search"],["🎯","target"],["⚡","lightning"],["✨","sparkles"],["🏆","trophy"]],
 "Symbols":[["❤️","heart love"],["💚","green heart"],["💛","yellow heart"],["💜","purple heart"],["✅","check done"],["❌","cross no"],["➕","plus"],["➡️","arrow right send"],["⬆️","arrow up send"],["♾️","infinity"]]
};
function emojiControl(f,id,v){
 const tile=el("button",{id,type:"button",class:"emoji-tile",disabled:canEdit?undefined:"","aria-label":"Choose "+f.label.toLowerCase()}),choose=el("button",{type:"button",class:"mini",text:"Choose emoji",disabled:canEdit?undefined:""}),box=el("div",{class:"emoji-control"},tile,choose);tile.value=v||"";
 const paint=()=>{tile.replaceChildren(theme[f.key]?CCEmoji.node(theme[f.key],theme[f.key+"_animated"],"",["calm","none"].includes(theme.motion)):document.createTextNode("+"));};paint();
 const open=()=>{
  const dialog=el("dialog",{class:"emoji-dialog","aria-label":"Choose "+f.label.toLowerCase()}),search=el("input",{type:"search",placeholder:"Search emoji","aria-label":"Search emoji"}),tabs=el("div",{class:"emoji-tabs"}),grid=el("div",{class:"emoji-grid"}),close=el("button",{type:"button",class:"mini",text:"Close"}),clear=el("button",{type:"button",class:"mini",text:"Use app default"});let group="Animated";
  const draw=()=>{const q=search.value.trim().toLowerCase();grid.replaceChildren();const pairs=group==="Animated"?Object.entries(CCEmoji.assets).map(([e,a])=>[e,a.name.toLowerCase()]):EMOJI_GROUPS[group];for(const [e,n] of pairs.filter(([e,n])=>!q||n.includes(q)||e===q)){const animated=group==="Animated",b=el("button",{type:"button",class:"emoji-option",title:n,"aria-label":n,onclick:()=>{tile.value=e;theme[f.key+"_animated"]=animated;setv(f,e);paint();dialog.close();choose.focus()}});b.append(CCEmoji.node(e,animated,n,["calm","none"].includes(theme.motion)));grid.append(b)}if(!grid.children.length)grid.append(el("small",{text:"No matching emoji"}));tabs.querySelectorAll("button").forEach(b=>b.setAttribute("aria-pressed",String(b.textContent===group)))};
  for(const name of ["Animated",...Object.keys(EMOJI_GROUPS)])tabs.append(el("button",{type:"button",class:"mini",text:name,onclick:()=>{group=name;search.value="";draw()}}));search.addEventListener("input",draw);close.addEventListener("click",()=>dialog.close());clear.addEventListener("click",()=>{tile.value="";theme[f.key+"_animated"]=false;setv(f,"");paint();dialog.close();choose.focus()});dialog.addEventListener("close",()=>dialog.remove());dialog.append(el("div",{class:"emoji-head"},el("b",{text:"Choose an emoji"}),close),search,tabs,grid,el("small",{class:"h",text:"Noto Emoji by Google Fonts. Static icons are bundled for offline use; animated icons use CC BY 4.0 assets. Motion stops with Calm, None or reduced motion."}),clear);document.body.append(dialog);draw();dialog.showModal();search.focus();
 };choose.addEventListener("click",open);tile.addEventListener("click",open);return box;
}

function compactHelp(){
 document.querySelectorAll('.field>.h,.tile>.help,.logoctl>.h').forEach(help=>{
  if(help.dataset.compact||help.textContent.length<110)return;help.dataset.compact='1';const text=help.textContent;
  const btn=el('button',{type:'button',class:'info-tip','aria-label':'More information','aria-expanded':'false',text:'i'}),tip=el('div',{class:'info-pop',role:'tooltip',text,hidden:''}),host=help.closest('.field'),label=host?host.querySelector('.flabel'):(help.previousElementSibling?.querySelector('#budgetSpend')?help.previousElementSibling:help.parentElement.querySelector('.head b'));
  help.replaceChildren(tip);if(label?.querySelector('input')){const title=el('span',{class:'label-title'});while(label.firstChild&&label.firstChild.nodeType===3)title.append(label.firstChild);title.append(btn);label.prepend(title)}else (label||help).append(btn);help.classList.add('compact-help');
  const show=()=>{tip.hidden=false;btn.setAttribute('aria-expanded','true')},hide=()=>{tip.hidden=true;btn.setAttribute('aria-expanded','false')};let pinned=false;btn.addEventListener('click',()=>{pinned=!pinned;pinned?show():hide()});btn.addEventListener('mouseenter',show);btn.addEventListener('mouseleave',()=>{if(!pinned)hide()});btn.addEventListener('focus',show);btn.addEventListener('blur',()=>{pinned=false;hide()});btn.addEventListener('keydown',e=>{if(e.key==='Escape')hide()});
 });
}

function control(f) {
  const id = "f-" + (f.colors && f.key==="sidebar" ? "color-sidebar" : f.key); let input;
  if(f.key === "bg_image"){
    const marker=el("small",{class:"h empty-field",text:"(not filled)",hidden:get(f)?"":undefined}),syncMarker=()=>{marker.hidden=!!link.value.trim()};const link=el("input",{id,type:"text",value:get(f)||"",placeholder:"https://… or choose a picture","aria-label":f.label}),file=el("input",{type:"file",accept:"image/png,image/jpeg,image/webp","aria-label":"Background picture",disabled:canEdit?undefined:""});link.addEventListener("input",()=>{setv(f,link.value);if(!link.value.trim())file.value="";syncMarker()});file.addEventListener("change",()=>{const chosen=file.files[0];if(!chosen)return;if(chosen.size>4000000){say("Choose a background picture under 4 MB.",true);return}const im=new Image(),url=URL.createObjectURL(chosen);im.onload=()=>{const c=document.createElement("canvas"),scale=Math.min(1,1000/im.width,1000/im.height);c.width=Math.round(im.width*scale);c.height=Math.round(im.height*scale);c.getContext("2d").drawImage(im,0,0,c.width,c.height);const data=c.toDataURL("image/jpeg",.75);if(data.length>600000){say("Picture is too detailed. Choose a smaller one.",true)}else{link.value=data;theme.bg_style="image";setv(f,data);syncMarker();say("Background picture added.")}URL.revokeObjectURL(url)};im.onerror=()=>{say("That picture could not be read.",true);URL.revokeObjectURL(url)};im.src=url});return el("div",{class:"field"},el("div",{class:"flabel",text:"Background picture"}),el("div",{class:"h",text:"Choose a local picture or paste an HTTPS image link."}),link,file,marker);
  }
  const v = get(f);
  if (f.type === "color") {
    const swatch = el("input", { type: "color", id, value: v || "#888888", "aria-label": f.label }), hex = el("input", { type: "text", class: "hex", value: v || "", maxlength: "7", "aria-label": f.label + " hex code", placeholder: "automatic" });
    swatch.addEventListener("input", () => { hex.value = swatch.value; setv(f, swatch.value); });
    hex.addEventListener("input", () => { if (/^#[0-9a-fA-F]{6}$/.test(hex.value)) { swatch.value = hex.value; setv(f, hex.value.toLowerCase()); } else if (f.clearable && hex.value === "") setv(f, ""); });
    input = el("div", { class: "colorrow" }, swatch, hex); if (f.clearable) input.append(el("button", { type: "button", class: "mini", onclick: () => { hex.value = ""; setv(f, ""); } }, "Auto"));
  } else if (f.type === "logo") {
    input = logoControl(f, v);
  } else if (f.type === "emoji") {
    input=emojiControl(f,id,v);
  } else if (f.type === "select") {
    input = el("select", { id }); if (f.fonts) input.dataset.fonts = "1"; const opts = f.fonts ? Object.keys(meta.fonts).concat("custom") : meta.enums[f.key];
    opts.forEach((o) => input.append(el("option", { value: o, text: f.fonts ? FONTNAMES[o] || o : (LABELS[f.key] || {})[o] || o })));
    input.value = v; input.addEventListener("change", () => { setv(f, input.value); if (f.key === "mode" && input.value !== "auto") { editMode = input.value; setPvMode(editMode); drawLook(); } });
  } else if (f.type === "range") {
    const [lo, hi] = meta.ranges[f.key], out = el("output", { text: v + (f.unit || "") });
    input = el("div", { class: "rangerow" }, el("input", { type: "range", id, min: lo, max: hi, value: v, "aria-label": f.label }), out, el("small", { class: "rng", text: lo + (f.unit || "") + " to " + hi + (f.unit || "") }));
    input.firstChild.addEventListener("input", (e) => { out.textContent = e.target.value + (f.unit || ""); setv(f, +e.target.value); });
  } else if (f.type === "toggle") {
    input = el("label", { class: "check" }, el("input", { type: "checkbox", id }), "On"); input.firstChild.checked = !!v; input.firstChild.addEventListener("change", (e) => setv(f, e.target.checked));
  } else if (f.type === "area") {
    input = el("textarea", { id, rows: "4", placeholder: f.ph || "(not filled)" }); input.value = v || ""; input.addEventListener("input", () => setv(f, input.value));
  } else {
    input = el("input", { type: "text", id, placeholder: f.ph || "(not filled)", maxlength: f.type === "emoji" ? "8" : "300", class: f.type === "emoji" ? "emoji" : "" }); input.value = v || ""; input.addEventListener("input", () => setv(f, input.value)); input.addEventListener("blur", () => { const t = input.value.trim(); if (t !== input.value) { input.value = t; setv(f, t); } });
  }
  if (!canEdit) { if (input.matches("input,select,textarea,button")) input.disabled=true; input.querySelectorAll("input,select,textarea,button").forEach((x)=>x.disabled=true); }
  if (!canEdit && input.tagName === "SELECT") input.disabled = true;
  const field=el("div", { class: "field" }, el("label", { for: id, class: "flabel" }, f.label), el("span", { class: "h", text: f.help }), input);
  if(f.key.startsWith("txt_")&&!theme[f.key]&&v)field.append(el("small",{class:"h value-source",text:"Using app default; no saved override."}));
  if (["text","area","emoji","logo"].includes(f.type) && !v) field.append(el("small",{class:"h empty-field",text:"(not filled)"}));
  if(["motion","entrance","speed","hover_lift"].includes(f.key)){
    const play=()=>{pushPreview();setTimeout(()=>{const w=$("#pv").contentWindow;if(w?.ccPreviewMotion)w.ccPreviewMotion(theme)},60)};input.addEventListener("change",play);input.addEventListener("input",play);
  }
  return field;
}
async function saveSection(s) {
  try {
    const base = clone(saved);
    for (const f of s.fields) { if (f.colors) { base.light[f.key] = theme.light[f.key]; base.dark[f.key] = theme.dark[f.key]; } else {base[f.key] = theme[f.key];if(f.type==="emoji")base[f.key+"_animated"]=theme[f.key+"_animated"];} }
    saved = clone((await api("/api/theme", { theme: base })).theme); changed(); say(s.title + " saved. Other sections keep their last saved values.");
  } catch (e) { say(e.message, true); }
}
/* the preview follows the section being edited */
let activeSec = "presets";

function lum(h) { const m = /^#?([0-9a-f]{6})$/i.exec(h || ""); if (!m) return null; const v = [0, 2, 4].map((i) => { const c = parseInt(m[1].substr(i, 2), 16) / 255; return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); }); return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]; }
function ratio(a, b) { const x = lum(a), y = lum(b); if (x == null || y == null) return null; const hi = Math.max(x, y), lo = Math.min(x, y); return (hi + 0.05) / (lo + 0.05); }
function pvExtra() {
  const host = $("#pvextra"); if (!host) return;
  const sec = activeSec; host.hidden = !(sec === "colors" || sec === "fonts"); if (host.hidden) { return; }
  if (sec === "colors") {
    const c = (theme && theme[editMode]) || {};
    const pairs = [["Text on page", c.ink, c.bg], ["Text on cards", c.ink, c.surface], ["Soft text on page", c.muted, c.bg], ["Your bubble", c.ink, c.you], ["Reply bubble", c.ink, c.bot], ["Title color on page", c.brand, c.bg]];
    host.replaceChildren(el("b", { text: "Colors and readability" }), el("div", { class: "crgrid" }, ...pairs.map(([n, a, b]) => { const r = ratio(a, b), cls = r == null ? "" : r >= 4.5 ? "green" : r >= 3 ? "blue" : "red";
      return el("div", { class: "cc", title: n + (cls === "green" ? ": easy to read" : cls === "blue" ? ": large text only" : ": too low") }, el("span", { class: "crs", style: "background:" + (b || "#fff") + ";color:" + (a || "#000") }, "Aa"), el("span", { text: n }), el("span", { class: "rt " + cls, text: r == null ? "n/a" : r.toFixed(1) })); })),
      el("div", { class: "h", text: "Contrast ratio. 4.5 or more is easy to read (green), 3 to 4.5 only for large text (blue), below 3 is too low (red)." }));
  } else {
    let fam = {}; try { const d = $("#pv").contentDocument, h = d.querySelector(".hero h1, .hero b, h1") || d.body; fam = { body: getComputedStyle(d.body).fontFamily, head: getComputedStyle(h).fontFamily }; } catch (e) { fam = { body: "inherit", head: "inherit" }; }
    host.replaceChildren(el("b", { text: "Font sample" }), el("div", { class: "fs-h", style: "font-family:" + fam.head, text: "How can I help today?" }), el("div", { class: "fs-b", style: "font-family:" + fam.body, text: "A good answer explains itself, then shows where it came from. 0123456789" }), el("div", { class: "h", text: "Headline font above, answer font below." }));
  }
}
function pvFollow() {
  // Keep all settings in one continuous document. Navigation only updates preview.
  window.CCPipelineFocus?.(activeSec);
  const m = activeSec === "model", card = $("#pvmodel"), fr = $("#pv"), cap = $("#pvcap");
  const names = { presets: "Whole look", wording: "Wording", colors: "Colors", background: "Background", fonts: "Fonts", shape: "Shape and spacing", emoji: "Icons", motion: "Motion", layout: "Layout", model: "Model" };
  if (cap) cap.textContent = "Showing: " + (names[activeSec] || "Chat");
  if (card.hidden === m) { (m ? card : fr).hidden = false; (m ? fr : card).hidden = true; (m ? card : fr).animate([{ opacity: 0, transform: "translateY(4px)" }, { opacity: 1, transform: "none" }], { duration: 180, easing: "ease-out" }); }
  { const pn = document.querySelector(".pvnote:not(#pvcap)"), ph = document.querySelector(".pvhead b"), pm = $("#pvmode"); if (pn) pn.hidden = m; if (ph) ph.textContent = m ? "Model status" : "Live preview"; if (pm) pm.hidden = m; }
  if (m) {
    const k = keyInfo[cur.provider] || {}, r = $("#testres"), st = r && r.classList.contains("ok") ? "ok" : (r && r.classList.contains("bad") ? "bad" : "");
    const keyTxt = k.source === "saved" ? "Key saved on this computer" : (k.source === "env" ? "Key from environment variable" : (k.needed === false ? "No key needed" : "No key yet"));
    card.replaceChildren(
      el("div", { class: "pvm-top" }, mark(cur.provider), el("div", {}, el("b", { text: NAMES[cur.provider] || cur.provider }), el("div", { class: "pvm-row", text: chosenModel() || (cur.provider === "mock" ? "Built-in demo, no model needed" : "No model chosen yet") }))),
      el("div", { class: "pvm-row", text: keyTxt }),
      el("div", { class: "pvm-badge " + st, text: st === "ok" ? "Connected" : (st === "bad" ? "Not working" : "Not tested yet") }),
      el("div", { class: "pvm-row " + st, text: (r && r.textContent) || "Press Test connection to check the key and model." }));

  }
  pvExtra();
  { let cp = $("#pvcloud"); if (!cp) { cp = el("div", { id: "pvcloud", class: "pvcloud" }); card.after(cp); }
    cp.hidden = !m;
    if (m) cp.replaceChildren(el("b", { text: "Suggested cloud models" }), ...CLOUD_PICKS.map((c) => el("div", { class: "cpick" }, mark(c.p), el("div", { class: "cpt" }, el("b", { text: c.name }), el("span", { class: "h", text: c.why })),
      cur.provider === c.p && chosenModel() === c.id ? el("span", { class: "okt", text: "In use" }) : el("button", { type: "button", class: "mini", disabled: canEdit ? undefined : "", onclick: () => { cur = { ...read(), provider: c.p, model: c.id }; draw(); const tr = $("#testres"); if (tr) { tr.textContent = ""; tr.className = ""; } loadModels(false).then(() => { const pk = $("#modelPick"); pk.value = [...pk.options].some((o) => o.value === c.id) ? c.id : OTHER; if (pk.value === OTHER) { $("#model").hidden = false; $("#model").value = c.id; } cur.model = c.id; pvFollow(); }); } }, "Use"))),
      el("div", { class: "h" }, "Taken from ", el("a", { href: "https://developers.openai.com/api/docs/models", target: "_blank", rel: "noopener" }, "OpenAI"), " and ", el("a", { href: "https://ai.google.dev/gemini-api/docs/models", target: "_blank", rel: "noopener" }, "Google"), " model pages on 5 Oct 2026. Names change, so use Refresh list after adding a key.")); }
  { const box = $("#ollamabox"); if (box) { const cpn = $("#pvcloud"); if (box.previousElementSibling !== cpn) cpn.after(box); box.hidden = !m; if (m && !box.dataset.loaded) ollamaPanel(); }
    let hist = $("#pvhist"); if (!hist) { hist = el("div", { id: "pvhist", class: "pvhist" }); card.parentNode.append(hist); }
    hist.hidden = !(m && testLog.length); hist.replaceChildren(el("b", { text: "Recent tests" }), ...testLog.map((x) => el("div", { class: "pvh-row" }, el("span", { class: "fitdot " + (x.ok ? "green" : "red") }), el("span", { text: x.p + (x.ok ? " worked" : " failed"),title:x.detail || "" }), el("span", { class: "h", text: x.t })))); }
}
function pvPop() { const f = document.getElementById("pv"); if (!f || matchMedia("(prefers-reduced-motion:reduce)").matches || ["calm","none"].includes(theme.motion)) return; f.animate([{ opacity: .55, transform: "scale(.985)" }, { opacity: 1, transform: "scale(1)" }], { duration: 220, easing: "ease-out" }); }
function syncColorEditor(sec) {
  sec.querySelectorAll('[data-m]').forEach(b=>b.setAttribute('aria-checked',String(b.dataset.m===editMode)));
  const spec=SECTIONS.find(s=>s.id==='colors');
  for(const f of spec.fields.filter(f=>f.colors)){
    const swatch=sec.querySelector('#f-'+(f.colors&&f.key==='sidebar'?'color-sidebar':f.key));if(!swatch)continue;
    const value=get(f)||'';swatch.value=value||'#888888';const hex=swatch.closest('.colorrow')?.querySelector('.hex');if(hex)hex.value=value;
  }
}
function drawLook() {
  const root = $("#look"),extra=new Map([...root.querySelectorAll("section.tile")].map(sec=>[sec.id,[...sec.querySelectorAll(":scope > .workspace-fields")]])); root.replaceChildren();
  for (const s of SECTIONS) {
    const sec = el("section", { class: "tile", id: "sec-" + s.id });
    const head = el("div", { class: "head" }, el("span", { class: "ic " + s.tone, text: s.icon }), el("div", {}, el("b", { text: s.title }), el("small", { text: s.sub })), el("button", { type: "button", class: "mini reset", title: "Put this group back to the defaults", disabled: canEdit ? undefined : "", onclick: () => resetGroup(s) }, "Reset group"));
    sec.append(head, el("div", { class: "help", text: s.help }));
    if (s.modeTabs) {
      const tabs = el("div", { class: "seg mini", role: "radiogroup", "aria-label": "Color set being edited" });
      for (const m of ["light", "dark"]) tabs.append(el("button", { type: "button", "data-m": m, role: "radio", "aria-checked": String(editMode === m), onclick: () => { editMode = m; setPvMode(m); syncColorEditor(sec); pushPreview(); } }, "Editing: " + (m === "light" ? "Light" : "Dark")));
      sec.append(tabs);
    }
    const byKey = Object.fromEntries(s.fields.map((f) => [f.key, f])); const gs = GROUPS[s.id];
    if (!gs) { const grid = el("div", { class: "fields" }); s.fields.forEach((f) => grid.append(control(f))); sec.append(grid); }
    else {
      const used = new Set();
      for (const [title, keys, collapsed] of gs) {
        const fs = keys.map((k) => byKey[k]).filter(Boolean); if (!fs.length) continue; fs.forEach((f) => used.add(f.key));
        const grid = el("div", { class: "fields" + (fs.every((f) => f.type === "color") ? " colorlist" : "") }); fs.forEach((f) => { const c = control(f); if (c && c.dataset) c.dataset.k = f.key; grid.append(c); });
        if (collapsed) { const d = el("details", { class: "grp" }, el("summary", { text: title }), grid); sec.append(d); }
        else sec.append(el("div", { class: "grp" }, el("h4", { text: title }), grid));
      }
      const rest = s.fields.filter((f) => !used.has(f.key)); if (rest.length) { const g = el("div", { class: "fields" }); rest.forEach((f) => g.append(control(f))); sec.append(el("details", { class: "grp" }, el("summary", { text: "More options" }), g)); }
    }
    sec.append(el("div", { class: "secfoot" }, el("button", { type: "button", class: "go blue", disabled: canEdit ? undefined : "", onclick: () => saveSection(s) }, "Save " + s.title.toLowerCase()), el("button", { type: "button", class: "go ghost", disabled: canEdit ? undefined : "", onclick: () => resetGroup(s) }, "Reset to default")));
    for(const panel of extra.get(sec.id)||[])sec.append(panel);
    root.append(sec);
  }
  buildMenu();
}
function resetGroup(s) { const d = meta.default; for (const f of s.fields) { if (f.colors) theme[editMode][f.key] = d[editMode][f.key]; else theme[f.key] = d[f.key]; } drawLook(); changed(); try { window.ccPulse && window.ccPulse(document.getElementById("sec-" + s.id)); } catch (e) {} }
function setPvMode(m) { document.querySelectorAll("#pvmode button").forEach((b) => b.setAttribute("aria-checked", String(b.dataset.m === m))); }
function buildMenu() {
  const m = $("#menu"); m.replaceChildren();
  const groups=[["config","Configuration",[["model","Model and key"],["search","Sources and APIs"],["prompts","Prompts"],["code","Code helpers"]]],["frontend","Frontend",[["presets","Presets and states"],...SECTIONS.map(s=>[s.id,s.title])]], ["manage","App management",[["freshness","Document freshness"],["budget","Budget"],["portable","Portable app"],["finish","Setup and workspace"]]]];
  groups.forEach(([id,title,items])=>{const group=el("div",{class:"nav-group","data-group":id});group.append(el("b",{class:"nav-label",text:title}));items.forEach(([id,t])=>group.append(el("a",{href:"#sec-"+id,text:t})));m.append(group);});
  m.querySelector("a").classList.add("on");
  let navHoldUntil=0;
  m.addEventListener("click",e=>{const a=e.target.closest("a");if(!a)return;e.preventDefault();activeSec=a.hash.replace("#sec-","");navHoldUntil=Date.now()+1200;pvFollow();history.replaceState(null,"",a.hash);requestAnimationFrame(()=>document.querySelector(a.hash)?.scrollIntoView({block:"start",behavior:"instant"}));m.querySelectorAll("a").forEach(x=>x.classList.toggle("on",x===a))});
  const col=$("#col");const order=["finish","model","search","prompts","code","presets","look","freshness","budget","portable"];
  order.forEach(id=>{const sec=id==="look"?$("#look"):$("#sec-"+id);if(sec)col.insertBefore(sec,$("#msg"));});
  const io = new IntersectionObserver((es) => { for (const e of es) if (e.isIntersecting && Date.now()>navHoldUntil) { activeSec = e.target.id.replace("sec-", ""); pvFollow(); document.querySelectorAll("#menu a").forEach((a) => a.classList.toggle("on", a.getAttribute("href") === "#" + e.target.id)); } }, { rootMargin: "-20% 0px -70% 0px" });
  const watch = () => document.querySelectorAll("section.tile[id^=sec-]").forEach((n) => io.observe(n)); watch(); setTimeout(watch, 800); setTimeout(watch, 2500);
}
function presetTheme(p){const t=Object.assign(clone(meta.default),clone(p));t.light=Object.assign(clone(meta.default.light),p.light||{});t.dark=Object.assign(clone(meta.default.dark),p.dark||{});return t;}
function lookSignature(t){const n=clone(t);for(const k of Object.keys(n))if(k.startsWith("txt_")||k.startsWith("logo"))delete n[k];return JSON.stringify(Object.fromEntries(Object.entries(n).sort()));}
function syncPreset(){if(!theme||!meta)return;const name=Object.entries({...PRESETS,...MORE_PRESETS}).find(([n,p])=>lookSignature(presetTheme(p))===lookSignature(theme))?.[0];document.querySelectorAll("#presets [data-preset]").forEach(b=>{const on=b.dataset.preset===name;b.setAttribute("aria-pressed",String(on));b.classList.toggle("selected",on)});let note=$("#presetCurrent");if(!note){note=el("p",{id:"presetCurrent",class:"h",role:"status"});$("#presets").before(note)}note.textContent=name?"Current preset: "+name:"Current look: Custom";}
function buildPresets() {
  const box = $("#presets"); box.replaceChildren();
  let showMore = Object.entries({...PRESETS,...MORE_PRESETS}).slice(4).some(([n,p])=>lookSignature(presetTheme(p))===lookSignature(theme));
  const draw = () => { box.replaceChildren();
  const all = showMore ? Object.assign({}, PRESETS, MORE_PRESETS) : Object.fromEntries(Object.entries(PRESETS).slice(0, 4));
  for (const [name, p] of Object.entries(all)) {
    const t = presetTheme(p);
    const c = t.mode === "dark" ? t.dark : t.light;
    const b = el("button", { type: "button", class: "preset", "data-preset":name,"aria-pressed":"false", title: "Apply the " + name + " look", disabled: canEdit ? undefined : "" }, el("span", { class: "sw", style: `background:linear-gradient(135deg,${c.bg} 0 50%,${c.brand} 50% 75%,${c.accent} 75%)` }), el("span", { class: "pn" }, el("span", { text: name }), el("small", { text: (FONTNAMES[t.font] || t.font) + (t.heading_font && t.heading_font !== t.font ? " + " + (FONTNAMES[t.heading_font] || t.heading_font) : "") })));
    b.addEventListener("click", () => { const scroll=scrollY; const keep = ["txt_title", "txt_tagline", "txt_examples", "txt_placeholder", "txt_hint", "txt_disclaimer", "txt_sidebar", "txt_footer"]; for (const k of keep) t[k] = theme[k]; theme = t; editMode = theme.mode === "dark" ? "dark" : "light"; setPvMode(editMode); drawLook(); pvPop(); changed();window.scrollTo({top:scroll,behavior:"instant"});requestAnimationFrame(()=>window.scrollTo({top:scroll,behavior:"instant"})); say("Preset \u201c" + name + "\u201d applied to the preview. Press Save look to keep it."); });
    box.append(b);
  }
  const more = el("button", { type: "button", class: "preset more", "aria-expanded": showMore ? "true" : "false" }, showMore ? "Show fewer" : "Load more");
  more.addEventListener("click", () => { showMore = !showMore; draw();syncPreset(); });
  box.append(more); };
  draw();syncPreset();
}
async function init() {
  const c = await api("/api/config"); window.CCLoadedApp = c; $("#lead").textContent = "Editing " + c.app.title + ". " + (c.app.tagline || "") + " Keys stay on this computer."; $("#h").textContent = c.app.title + " configuration"; document.title = c.app.title + " configuration";
  const overview = el("details", {class:"loaded-app",id:"loadedApp"}, el("summary", {text:"Loaded Nerd: " + c.app.title}), el("p", {text:c.app.tagline || ""}), el("small", {text:"Sources: " + c.sources.map(x=>x.label || x.id).join(", ")}));
  $("#lead").after(overview);
  const sourceOverview = el("div", {class:"loaded-source-overview"}, el("b", {text:"This Nerd's configured sources"}), ...c.sources.map(x=>el("p", {text:(x.label || x.id) + " · " + (x.type || "") })), el("small", {text:"Sources in the loaded app file are already active. The controls below add optional web searches; they do not replace your Nerd's connector."}));
  const search = $("#sec-search"); if (search) search.prepend(sourceOverview);
  const d = await api("/api/settings"); cur = d.settings; canEdit = d.can_edit; try { keyInfo = (await api("/api/provider/status")).keys; } catch (e) { keyInfo = {}; }
  const th = await api("/api/theme"); theme = th.theme; meta = th.meta; saved = clone(theme); canEdit = canEdit && th.can_edit !== false;
  const seg = $("#seg");
  buildChips(d.providers);
  draw(); await states(); buildPresets(); drawLook(); compactHelp();
  document.querySelectorAll("#pvmode button").forEach((b) => b.addEventListener("click", () => { setPvMode(b.dataset.m); pushPreview(); }));
  $("#pv").addEventListener("load", () => { setPvMode(theme.mode === "dark" ? "dark" : "light"); setTimeout(pushPreview, 250); });
  if (!canEdit) say("View only. Open this page on the computer running the app, or sign in as the admin, to change anything.");
  $("#temp").addEventListener("input", () => {$("#tv").textContent = (+$("#temp").value).toFixed(2);sliderVisuals()});
  $("#topk").addEventListener("input", () => {$("#kv").textContent = $("#topk").value;sliderVisuals()});
  $("#modelPick").addEventListener("change", pickChanged);
  $("#refreshModels").addEventListener("click", () => loadModels(true));
  $("#keysave").addEventListener("click", async () => { const v = $("#apikey").value.trim(); if (!v) { say("Paste a key first.", true); return; } try { const r = await api("/api/provider/key", { provider: cur.provider, key: v }); keyInfo[cur.provider] = r.key; $("#apikey").value = ""; await provExtras(); say("Key saved on this computer."); } catch (e) { say(e.message, true); } });
  $("#keyclear").addEventListener("click", async () => { try { const r = await api("/api/provider/key", { provider: cur.provider, clear: true }); keyInfo[cur.provider] = r.key; await provExtras(); say("Key removed."); } catch (e) { say(e.message, true); } });
  $("#testconn").addEventListener("click", async () => { const t=$("#testres"),provider=cur.provider,model=chosenModel(),base=$("#base").value.trim();t.className="testres busy";t.textContent="Testing...";let ok=false,message="";try{const r=await api("/api/provider/test",{provider,model,base_url:base});ok=r.ok;message=r.message}catch(e){message=e.message}testLog.unshift({p:NAMES[provider]||provider,ok,detail:message,t:new Date().toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"})});testLog.length=Math.min(testLog.length,5);if(cur.provider===provider){t.className="testres "+(ok?"ok":"bad");t.textContent=(ok?"Passed. ":"Failed. ")+message}pvFollow(); });
  $("#apply").addEventListener("click", async () => { try { cur = (await api("/api/settings", { settings: read() })).settings; draw(); localStorage.setItem("cc_config_changed", String(Date.now())); say("Applied. New questions use these settings."); } catch (e) { say(e.message, true); } });
  $("#save").addEventListener("click", async () => { try { const n = (await api("/api/states/save", { name: $("#sname").value })).name; await states(); say("Saved as \u201c" + n + "\u201d."); } catch (e) { say(e.message, true); } });
  $("#states").addEventListener("change",syncDeleteLook);
  $("#load").addEventListener("click", async () => { const n = $("#states").value; if (!n) return say("Choose a saved state first", true); try { cur = (await api("/api/states/load", { name: n })).settings; draw(); localStorage.setItem("cc_config_changed", String(Date.now())); say("Loaded \u201c" + n + "\u201d."); } catch (e) { say(e.message, true); } });
  $("#del").addEventListener("click", async () => { const n = $("#states").value; if (!n) return say("Choose a saved look first", true); if (!confirm("Delete the saved look \"" + n + "\"?")) return; await api("/api/states/delete", { name: n }); await states(); say("Deleted."); });
  $("#saveLook").addEventListener("click", async () => { try { theme = (await api("/api/theme", { theme })).theme; saved = clone(theme); drawLook(); changed(); say("Look saved. The chat now uses it for everyone."); } catch (e) { say(e.message, true); } });
  $("#resetAll").addEventListener("click", () => { if (!confirm("Reset only the look to the default? Prompts, sources, keys and helper drafts stay unchanged.")) return; theme = clone(meta.default); drawLook(); changed(); });
  $("#exp").addEventListener("click", () => { const a = el("a", { href: URL.createObjectURL(new Blob([JSON.stringify(theme, null, 1)], { type: "application/json" })), download: "customchat-look.json" }); document.body.append(a); a.click(); a.remove(); });
  $("#imp").addEventListener("change", async (e) => { const f = e.target.files[0]; if (!f) return; try { const j = JSON.parse(await f.text()); const t = Object.assign(clone(meta.default), j); t.light = Object.assign(clone(meta.default.light), j.light || {}); t.dark = Object.assign(clone(meta.default.dark), j.dark || {}); theme = t; drawLook(); changed(); say("Look imported into the preview. Press Save look to keep it."); } catch (x) { say("That file is not a CustomChat look file", true); } e.target.value = ""; });
}
// App export is separate from the saved-look JSON export.
document.getElementById("exportApp").addEventListener("click", async function () {
  if (!canEdit) return;
  const status = document.getElementById("exportStatus");
  try {
    const checks=await api("/api/app-export-check");
    const text="Export readiness (offline checks only):\n\n"+checks.readiness.rows.filter(r=>["setup","warning","blocked"].includes(r.kind)).map(r=>r.item+": "+r.message).join("\n")+"\n\nNot included: "+checks.excluded.join(", ")+".\n\nIncluded documents need your review before sharing. Download bundle?";
    if (!confirm(text)) return;
  } catch(e) { status.textContent=e.message;return; }
  this.disabled = true; status.textContent = "Preparing app export...";
  try {
    // Flush the current look so the ZIP matches the configuration on screen.
    clearTimeout(autoTimer);
    const snap = clone(theme); await api("/api/theme", { theme: snap }); saved = clone(snap);
    const headers = {};
    if (token) headers.Authorization = "Bearer " + token;
    const response = await fetch("/api/app-export", { headers });
    if (!response.ok) { const error = await response.json(); throw new Error(error.error || "Export failed"); }
    const blob = await response.blob(), url = URL.createObjectURL(blob), a = document.createElement("a");
    a.href = url; a.download = "customchat-app.zip"; a.click(); setTimeout(() => URL.revokeObjectURL(url), 60000);
    status.textContent = "App ZIP downloaded. Review the included documents before sharing.";
  } catch (error) { status.textContent = error.message; }
  finally { this.disabled = !canEdit; }
});

async function docsFreshness(force) {
  const box = $("#docsFreshness");
  box.textContent = "Checking local documents...";
  try {
    const result = await api("/api/docs-freshness", force ? {} : undefined);
    box.replaceChildren();
    if (!result.sources.length) box.textContent = "No local document folders configured.";
    for (const source of result.sources) {
      const checked = source.checked_at ? new Date(source.checked_at * 1000).toLocaleString() : "not checked";
      const line=el("div",{class:"status-card"},el("b",{text:source.label}),
        el("div",{class:"status-stats"},el("span",{text:source.documents+" "+(source.documents===1?"document":"documents")}),el("span",{text:source.chunks+" "+(source.chunks===1?"passage":"passages")})),
        el("small",{text:"Last checked: "+checked}));
      if(source.error)line.append(el("p",{class:"bad",text:source.error}));
      else line.append(el("details",{},el("summary",{text:"Index details"}),el("small",{text:"Version "+source.revision.slice(0,12)+" · Checks on questions, at most every "+source.refresh_interval+" seconds"})));
      box.append(line);
    }
  } catch (error) { box.textContent = error.message; }
}
$("#checkDocs").addEventListener("click", async function () {
  if (!canEdit) return; this.disabled = true;
  try { await docsFreshness(true); } finally { this.disabled = !canEdit; }
});

function budgetVisuals(){
 for(const [id,icon] of [["budgetQuestions","?"] ,["budgetUser","♙"],["budgetCalls","✦"],["budgetSpend","$"]]){
  const input=document.getElementById(id);if(!input)continue;const label=input.closest("label");
  let v=label.querySelector(".budget-viz");if(!v){v=el("span",{class:"budget-viz","aria-hidden":"true"});label.append(v)}
  const count=id==="budgetSpend" ? (input.value===""?0:1) : Math.min(5,Math.max(0,Math.ceil(Math.log10(1+Math.max(0,+input.value))*2)));
  v.replaceChildren(...Array.from({length:count},()=>el("i",{text:icon})),el("small",{text:id==="budgetSpend"?(input.value===""?"No dollar cap":"Non-Demo answers blocked"):(+input.value===0?"No daily limit":input.value+" per day")}));
  if(!matchMedia("(prefers-reduced-motion:reduce)").matches&&! ["calm","none"].includes(theme.motion))v.animate([{transform:"translateY(2px)",opacity:.6},{transform:"translateY(0)",opacity:1}],{duration:160});
 }
}
for(const id of ["budgetQuestions","budgetUser","budgetCalls","budgetSpend"])document.getElementById(id)?.addEventListener("input",budgetVisuals);
async function loadBudget() {
  const data = await api("/api/budget"), limits = data.limits;
  $("#budgetQuestions").value = limits.daily_questions;
  $("#budgetUser").value = limits.user_daily_questions;
  $("#budgetCalls").value = limits.daily_model_calls;
  $("#budgetSpend").value = limits.spend_cap_usd === null ? "" : limits.spend_cap_usd; budgetVisuals();
  const q=data.used.question||0,m=data.used.model||0;
  $("#budgetStatus").replaceChildren(el("div",{class:"status-card"},el("b",{text:"Today's usage"}),
    el("div",{class:"status-stats"},el("span",{text:q+" "+(q===1?"question":"questions")}),el("span",{text:m+" "+(m===1?"model call":"model calls")})),
    el("small",{text:"Usage day: "+data.day+" · Resets at midnight UTC"}),el("details",{},el("summary",{text:"How dollar limits work"}),el("p",{text:data.spend_note}))));
}
$("#saveBudget").addEventListener("click", async function () {
  if (!canEdit) return; this.disabled = true;
  try {
    await api("/api/budget", { budget: { daily_questions: Number($("#budgetQuestions").value),
      user_daily_questions: Number($("#budgetUser").value), daily_model_calls: Number($("#budgetCalls").value),
      spend_cap_usd: $("#budgetSpend").value === "" ? null : Number($("#budgetSpend").value) } });
    await loadBudget();
  } catch (error) { $("#budgetStatus").textContent = error.message; }
  finally { this.disabled = !canEdit; }
});

let helpQueued=false;new MutationObserver(()=>{if(helpQueued)return;helpQueued=true;queueMicrotask(()=>{helpQueued=false;compactHelp()})}).observe(document.getElementById("look"),{childList:true,subtree:true});
$("#configGuide").addEventListener("click", () => CCTour.config(true));

async function drawOllamaSetup(host) {
  host.dataset.poll='';
  host.replaceChildren(el('div',{class:'h',text:'Checking local Ollama...'}));
  try {
    const st=await api('/api/ollama/setup');
    const titles={running:'Ollama is running',stopped:'Ollama is installed but stopped',not_detected:'Ollama not detected'};
    host.replaceChildren(el('h3',{text:'Set up Ollama'}),el('div',{class:'setup-status'},el('b',{text:titles[st.state]}),el('p',{class:'h',text:'On the computer running CustomChat, not this phone.'})));
    const recheck=el('button',{type:'button',class:'mini',text:'Recheck',onclick:()=>drawOllamaSetup(host)});
    host.append(el('div',{class:'setup-row'},el('span',{text:'Computer'}),el('b',{text:st.system+' · '+st.arch})),el('div',{class:'setup-row'},el('span',{text:'Installer'}),el('b',{text:'Official Ollama'})));
    if(st.state==='running'){host.append(el('p',{text:'Choose a model separately below.'}),recheck);return;}
    const detail=el('details',{class:'setup-details'},el('summary',{text:'Installation details'}),el('p',{class:'h',text:st.disk_free_gb+' GB free disk. A connection error alone does not mean Ollama is missing. If installed elsewhere, start it and recheck.'}),el('p',{class:'h',text:'Review before installing. OS prompts stay on your computer. Models download separately.'}));
    if(!st.supported){host.append(el('a',{href:'https://ollama.com',target:'_blank',rel:'noopener',text:'Official Ollama site'}),recheck);return;}
    const action=st.state==='stopped'?'start':'install';
    host.append(el('button',{type:'button',class:'mini',text:action==='start'?'Review start':'Review installation',onclick:async()=>{
      try {
        const plan=await api('/api/ollama/setup/prepare',{action});
        host.replaceChildren(el('h3',{text:action==='start'?'Start local Ollama':'Install Ollama?'}),el('p',{class:'h',text:'On this '+plan.system+' computer. '+plan.disk_free_gb+' GB free.'}));const more=el('details',{class:'setup-details'},el('summary',{text:'What changes'}),el('p',{class:'h',text:plan.changes}),el('p',{class:'h',text:plan.instructions}));host.append(more);
        if(action==='install')host.append(el('a',{href:plan.source,target:'_blank',rel:'noopener',text:'Official installer source'}),el('p',{class:'h',text:'No model download included. Installer size unknown; limit 2 GB.'}));
        const consent=el('input',{type:'checkbox'}),label=el('label',{class:'setup-consent'},consent,' I approve '+(action==='install'?'installing Ollama':'starting Ollama')+' on this computer.');
        const go=el('button',{type:'button',class:'mini',text:action==='install'?'Install Ollama':'Start Ollama',disabled:''});consent.onchange=()=>go.disabled=!consent.checked;
        go.onclick=async()=>{go.disabled=true;try{const {id}=await api('/api/ollama/setup/execute',{ticket:plan.ticket,confirmed:consent.checked});await pollOllamaSetup(host,id);}catch(e){host.append(el('p',{class:'testres bad',text:e.message}));}};
        host.append(label,go,el('button',{type:'button',class:'mini',text:'Not now',onclick:()=>drawOllamaSetup(host)}));
      }catch(e){host.append(el('p',{class:'testres bad',text:e.message}));}
    }}),recheck,detail);
  }catch(e){host.replaceChildren(el('p',{class:'h',text:e.message}));}
}
async function pollOllamaSetup(host,id){
  host.dataset.poll=id;
  for(let i=0;i<310 && host.isConnected && host.dataset.poll===id;i++){
    const st=await api('/api/ollama/setup/status?id='+encodeURIComponent(id));
    host.replaceChildren(el('h3',{text:st.state==='ready'?'Ollama is ready':'Ollama setup'}),el('p',{text:st.message}));
    if(st.downloaded_bytes)host.append(el('p',{class:'h',text:(st.downloaded_bytes/1048576).toFixed(1)+' MB downloaded'+(st.total_bytes?' of '+(st.total_bytes/1048576).toFixed(1)+' MB':' · total size unknown')}));
    if(st.sha256){const d=el('details',{},el('summary',{text:'Downloaded installer fingerprint'}),el('small',{text:st.sha256}));host.append(d);}
    if(st.page)host.append(el('a',{href:st.page,target:'_blank',rel:'noopener',text:'Official installation instructions'}));
    host.append(el('button',{type:'button',class:'mini',text:'Recheck local service',onclick:()=>drawOllamaSetup(host)}));
    if(['ready','failed','needs_manual','cancelled'].includes(st.state)){if(st.state!=='ready')host.append(el('button',{type:'button',class:'mini',text:'Retry after fresh review',onclick:()=>drawOllamaSetup(host)}));return;}
    host.append(el('button',{type:'button',class:'mini',text:'Cancel setup work',onclick:async()=>{await api('/api/ollama/setup/cancel',{id})}}));
    await new Promise(r=>setTimeout(r,2000));
  }
}

init().then(() => { CCTour.config(); if (canEdit) { docsFreshness(false); loadBudget().catch((e) => { $("#budgetStatus").textContent = e.message; }); } updateVis(); setTimeout(updateVis, 500); }).catch((e) => say(e.message, true));
})();


(function () { const upd = () => document.querySelectorAll("input[type=range]").forEach((r) => { const mn = +r.min || 0, mx = +r.max || 100; r.style.setProperty("--p", ((+r.value - mn) / (mx - mn) * 100) + "%"); }); document.addEventListener("input", upd); setInterval(upd, 400); upd(); })();

(function () {
  const mk = () => {
    const f = document.getElementById("f-font"), h = document.getElementById("f-heading_font");
    if (f && !document.getElementById("typeprev")) { const host = f.closest(".field") || f.parentElement; const d = document.createElement("div"); d.id = "typeprev"; d.className = "typeprev"; d.innerHTML = '<span class="tp-h">Heading sample</span><span class="tp-b">The quick brown fox jumps over the lazy dog.</span>'; host.parentElement.insertBefore(d, host.nextSibling); }
    const tp = document.getElementById("typeprev"); if (tp) { const sf = (sel) => { const o = sel && sel.options[sel.selectedIndex]; return o && o.value && !["system", "custom"].includes(o.value) ? '"' + o.textContent + '", sans-serif' : ""; }; const bf = sf(f), hf = sf(h); tp.querySelector(".tp-b").style.fontFamily = bf; tp.querySelector(".tp-h").style.fontFamily = hf || bf; }
    const sb = document.getElementById("f-sidebar"), cw = document.getElementById("f-chat_width");
    if (sb && !document.getElementById("layprev")) { const host = sb.closest(".field") || sb.parentElement; const d = document.createElement("div"); d.id = "layprev"; d.className = "layprev"; d.innerHTML = '<i class="lp-s"></i><i class="lp-c"></i>'; host.parentElement.insertBefore(d, host); }
    const lp = document.getElementById("layprev"); if (lp && sb) { lp.dataset.side = sb.value; lp.dataset.w = cw ? cw.value : ""; }
  };
  setInterval(mk, 500);
})();

document.addEventListener("click", (e) => { if (e.target && e.target.id === "resetLink") { const r = document.getElementById("resetAll"); if (r) r.click(); } });


// Keep the settings preview in place while properties update.
(function(){var m=document.querySelector('.menu');if(m){var on=function(){m.classList.toggle('end',m.scrollLeft+m.clientWidth>=m.scrollWidth-4)};m.addEventListener('scroll',on,{passive:true});on()}

})();
