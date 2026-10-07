(() => {
"use strict";
const $ = (s, r = document) => r.querySelector(s);
const token = localStorage.getItem("cc_token") || "";
async function api(path, body) {
  const h = { "Content-Type": "application/json" }; if (token) h.Authorization = "Bearer " + token;
  const r = await fetch(path, body === undefined ? { headers: h } : { method: "POST", headers: h, body: JSON.stringify(body) });
  const d = await r.json().catch(() => ({})); if (!r.ok) throw new Error(d.error || "Request failed"); return d;
}
const el = (t, p = {}, ...k) => { const e = document.createElement(t); for (const [a, v] of Object.entries(p)) { if (v == null) continue; if (a === "class") e.className = v; else if (a === "text") e.textContent = v; else if (a.startsWith("on")) e.addEventListener(a.slice(2), v); else e.setAttribute(a, v); } e.append(...k.filter((x) => x != null)); return e; };
const link = (href, text) => el("a", { href, target: "_blank", rel: "noopener noreferrer", text });

/* Key guides. Every link and claim below was read from the provider's own pages on 5 Oct 2026. Steps are only written where the official page confirms them. */
const STEPS = ["Sign in on the key page.", "Create a key.", "Copy it and paste it here."];
const MODEL_GUIDES = {
  openai: { name: "OpenAI", url: "https://platform.openai.com/api-keys", help: "https://help.openai.com/en/articles/4936850", note: "Billed separately from ChatGPT.", steps: STEPS },
  claude: { name: "Claude", url: "https://console.anthropic.com/settings/keys", help: "https://platform.claude.com/docs/en/get-api-key", note: "Settings, then API keys.", steps: STEPS },
  gemini: { name: "Gemini", url: "https://aistudio.google.com/app/apikey", help: "https://ai.google.dev/gemini-api/docs/api-key", note: "Has a free usage tier.", steps: STEPS },
  groq: { name: "Groq", url: "https://console.groq.com/keys", help: "https://console.groq.com/docs/quickstart", note: "", steps: STEPS },
  mistral: { name: "Mistral", url: "https://docs.mistral.ai/getting-started/quickstarts/studio/activate-and-generate-api-key", help: "https://docs.mistral.ai/getting-started/quickstarts/studio/activate-and-generate-api-key", note: "Free mode needs no card.", steps: ["Follow Mistral's guide.", "Copy the key.", "Paste it here."] },
  minimax: { name: "MiniMax", url: "https://platform.minimax.io/docs/guides/quickstart-preparation", help: "https://platform.minimax.io/docs/guides/quickstart-preparation", note: "", steps: ["Register or sign in.", "Create a key.", "Copy it and paste it here."] },
  mimo: { name: "Xiaomi MiMo", url: "https://platform.xiaomimimo.com/console/api-keys", help: "https://mimo.mi.com/docs/en-US/quick-start/faq/api-integration", note: "", steps: ["Sign in to the console.", "Apply for a key.", "Copy it and paste it here."] },
  deepseek: { name: "DeepSeek", url: "https://api-docs.deepseek.com/", help: "https://api-docs.deepseek.com/", note: "Follow DeepSeek's docs to create a key.", steps: null },
  openrouter: { name: "OpenRouter", url: "https://openrouter.ai/collections/free-models", help: "https://openrouter.ai/collections/free-models", note: "Follow OpenRouter's site to create a key.", steps: null }
};
const NAME2ID = { OpenAI: "openai", Claude: "claude", Gemini: "gemini", Groq: "groq", Mistral: "mistral", MiniMax: "minimax", "Xiaomi MiMo": "mimo", DeepSeek: "deepseek", OpenRouter: "openrouter" };
const SEARCH = [
  { id: "tavily", name: "Tavily", pro: "Short, clean snippets.", free: "Free: 1,000 credits a month.", url: "https://app.tavily.com/", docs: "https://docs.tavily.com/documentation/quickstart" },
  { id: "exa", name: "Exa", pro: "Finds pages by meaning.", free: "Free: $20 on signup, $10 a month.", url: "https://dashboard.exa.ai/api-keys", docs: "https://exa.ai/docs/reference/pricing" },
  { id: "firecrawl", name: "Firecrawl", pro: "Also reads whole pages.", free: "Free: 500 searches, no card.", url: "https://www.firecrawl.dev/app", docs: "https://docs.firecrawl.dev/billing" },
  { id: "parallel", name: "Parallel", pro: "Focused excerpts.", free: "Paid by use, about $5 per 1,000 searches. Free tier not confirmed.", url: "https://platform.parallel.ai/", docs: "https://docs.parallel.ai/getting-started/pricing" }
];

function whySvg() {
  const w = document.createElementNS("http://www.w3.org/2000/svg", "svg"); w.setAttribute("viewBox", "0 0 320 96"); w.setAttribute("class", "gsvg"); w.setAttribute("role", "img"); w.setAttribute("aria-label", "Your files and the live web both feed the answer");
  w.innerHTML = '<g fill="none" stroke="#66786f" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="30" width="56" height="36" rx="18"/><path d="M62 42l30-18m-6-1l6-1 1 6"/><path d="M62 54l30 18m-6 1l6 1 1-6"/><rect x="96" y="8" width="84" height="30" rx="8"/><rect x="96" y="58" width="84" height="30" rx="8"/><path d="M180 23l34 20m-6-1l6 1-1 6"/><path d="M180 73l34-20m-6 1l6-1-1-6"/><rect x="216" y="28" width="98" height="40" rx="10"/><path d="M228 44h74m-74 10h50"/></g><g fill="#66786f" font-size="11.5" font-family="DM Sans,sans-serif"><text x="14" y="52">Ask</text><text x="106" y="27">Your files</text><text x="106" y="77">Live web</text><text x="226" y="21">Answer + sources</text></g>';
  return w;
}
function svgSteps() {
  const s = 'http://www.w3.org/2000/svg';
  const w = document.createElementNS(s, "svg"); w.setAttribute("viewBox", "0 0 300 60"); w.setAttribute("class", "gsvg"); w.setAttribute("role", "img"); w.setAttribute("aria-label", "Open the site, create a key, paste it here");
  w.innerHTML = '<g fill="none" stroke="#66786f" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="8" y="12" width="52" height="36" rx="6"/><path d="M8 22h52"/><circle cx="14" cy="17" r="1.2"/><path d="M70 30h18m-5-5 5 5-5 5"/><circle cx="118" cy="26" r="9"/><path d="M127 30h24m-6 0v8m-7-8v6"/><path d="M168 30h18m-5-5 5 5-5 5"/><rect x="198" y="16" width="92" height="28" rx="14"/><path d="M212 30h4m6 0h4m6 0h4m6 0h4"/></g><g fill="#66786f" font-size="10.5" font-family="DM Sans,sans-serif"><text x="10" y="58">Open</text><text x="100" y="58">Create key</text><text x="224" y="58">Paste</text></g>';
  return w;
}
function stepsBlock(g) {
  const box = el("div", { class: "gbody" });
  box.append(svgSteps());
  if (g.note) box.append(el("p", { class: "h", text: g.note }));
  if (g.steps) box.append(el("ol", { class: "gsteps" }, ...g.steps.map((t) => el("li", { text: t }))));
  box.append(el("div", { class: "keyrow" }, link(g.url, "Open the key page"), g.help && g.help !== g.url ? link(g.help, "Official guide") : null));
  return box;
}

/* ---- Model tab: guide in the right panel ---- */
function modelGuide() {
  const box = el("div", { class: "gcard", id: "guidebox", hidden: "" });
  $("#pvbox").append(box);
  const draw = () => {
    const b = $("#seg button[aria-checked=true]"); const name = b ? b.textContent.trim() : ""; const id = NAME2ID[name]; const g = MODEL_GUIDES[id];
    const on = !$("#pvmodel").hidden && !!g; box.hidden = !on; if (!on) return;
    box.replaceChildren(el("b", { text: "How to get your " + g.name + " key" }), stepsBlock(g));
  };
  new MutationObserver(draw).observe($("#seg"), { subtree: true, attributes: true, attributeFilter: ["aria-checked"], childList: true });
  new MutationObserver(draw).observe($("#pvmodel"), { attributes: true, attributeFilter: ["hidden"] });
  draw();
}

/* ---- Prompts and Code tabs: replace the chat preview ---- */
function ctxBox() {
  const aside = el("aside", { class: "preview ctx", id: "ctxbox", hidden: "", "aria-label": "Helper panel" });
  $("#pvbox").after(aside); return aside;
}
const diffLines = (a, b) => { const A = a.split("\n"), B = b.split("\n"), sa = new Set(A), sb = new Set(B); return [...A.filter((x) => !sb.has(x)).map((x) => ["-", x]), ...B.filter((x) => !sa.has(x)).map((x) => ["+", x])]; };

function promptsPanel(host) {
  host.replaceChildren(el("div", { class: "pvhead" }, el("b", { text: "Try a prompt" })), el("p", { class: "h", text: "Run a step on a sample. Nothing is saved." }));
  const sel = el("select", { "aria-label": "Step to try" });
  const keys = [["answer", "Answer"], ["queries", "Search queries"], ["standalone", "Standalone question"], ["relevance", "Relevance filter"], ["faithfulness", "Support check"], ["followups", "Follow-ups"], ["question_check", "Question check"], ["summary", "Summary"]];
  keys.forEach(([k, t]) => sel.append(el("option", { value: k, text: t })));
  const q = el("input", { placeholder: "Sample question", "aria-label": "Sample question", value: "What are the main points in this document?" });
  const ps = el("textarea", { rows: "4", placeholder: "Sample passages (optional), one per line", "aria-label": "Sample passages" });
  const out = el("div", { class: "review", role: "status", "aria-live": "polite" });
  const stat = el("small", { class: "h" }); const diff = el("div", { class: "diff" });
  const area = () => $("#st-" + sel.value + " textarea");
  const info = () => { const a = area(); if (!a) return; const t = a.value; stat.textContent = t.length + " characters, about " + Math.ceil(t.length / 4) + " tokens"; const d = $("#st-" + sel.value + " textarea").dataset.def; };
  const defOf = async () => { const d = await api("/api/prompts"); return (d.stages.find((s) => s.key === sel.value) || {}).default || ""; };
  const show = async () => { info(); try { const def = await defOf(); const a = area(); const lines = a ? diffLines(def, a.value) : []; diff.replaceChildren(el("b", { text: "Change from the default" }), ...(lines.length ? lines.slice(0, 40).map(([m, x]) => el("div", { class: "dl " + (m === "+" ? "add" : "del"), text: m + " " + x })) : [el("div", { class: "h", text: "Same as the default." })])); } catch (e) { } };
  sel.addEventListener("change", show);
  document.addEventListener("input", (e) => { if (e.target.closest && e.target.closest(".stage")) show(); });
  const run = el("button", { type: "button", class: "go blue", text: "Run on sample", onclick: async () => { run.disabled = true; out.className = "review"; out.textContent = "Running..."; try { const r = await api("/api/prompts/test", { key: sel.value, text: area().value, question: q.value, passages: ps.value }); out.className = "review " + (r.ok ? "ok" : "bad"); out.textContent = r.ok ? r.output : r.error; } catch (e) { out.className = "review bad"; out.textContent = e.message; } run.disabled = false; } });
  host.append(sel, q, ps, run, out, stat, diff);
  const order = ["question_check", "standalone", "queries", "relevance", "answer", "faithfulness", "followups"]; show();
}

let keyStatus = {};
async function codePanel(host) {
  let state;
  try {state=await api("/api/websearch/status")}catch(e){host.textContent=e.message;return}
  const selected=new Set(state.source.providers||[]), libraries=new Set(state.catalog||[]);
  keyStatus=Object.fromEntries(state.providers.map(p=>[p.id,p.has_key]));
  let webOn=!!state.source.on;
  const notice=el("p",{class:"h",role:"status"});
  const persistWeb=async()=>{try{await api("/api/websearch/source",{on:webOn,providers:[...selected]})}catch(e){notice.textContent=e.message}};
  const persistLibraries=async()=>{try{await api("/api/catalog",{types:[...libraries]})}catch(e){notice.textContent=e.message}};
  host.replaceChildren(el("div",{class:"head"},el("div",{},el("b",{text:"Sources and search keys"}),el("small",{text:"Your documents work without extra keys."}))),
    el("p",{class:"h",text:"Turn a service on, then add its key here. Missing keys pause that service, not your other sources. Keys are saved privately on this server."}));
  const webToggle=el("input",{type:"checkbox","aria-label":"Add live web results"});webToggle.checked=webOn;
  webToggle.addEventListener("change",()=>{webOn=webToggle.checked;if(!selected.size){notice.textContent="Choose a service below first.";webOn=false;webToggle.checked=false;return}persistWeb()});
  host.append(el("label",{class:"check sw"},webToggle," Add live web results to answers"),notice,el("h3",{text:"Web search"}));
  function service(id,name,library,keyfree,url){
    const set=library?libraries:selected;
    let has=keyfree||(library?!!(state.catalog_keys||{})[id]:!!keyStatus[id]);
    const cb=el("input",{type:"checkbox","aria-label":"Enable "+name});cb.checked=set.has(id);
    const badge=el("span",{class:"source-key-badge"});const status=el("small",{class:"h",role:"status"});
    const card=el("section",{class:"source-key-card"});
    const input=el("input",{type:"password",autocomplete:"off",spellcheck:"false","aria-label":name+" API key",placeholder:"Paste "+name+" API key"});
    const keyrow=el("div",{class:"keyrow source-inline-key"});const help=el("small",{class:"h"});
    const refresh=()=>{badge.textContent=keyfree?"Key-free":has?"Key saved":"Key needed";status.textContent=!cb.checked?"Off. Turn on to set up.":has?"Ready to use.":"Selected. Paused until a key is saved.";keyrow.hidden=help.hidden=keyfree||!cb.checked;help.textContent=has?"A key is saved. Leave blank to keep it, or paste a replacement.":"Needs a key before it can search. No requests sent until saved.";remove.hidden=!has||keyfree;};
    const endpoint=library?"/api/catalog/key":"/api/websearch/key";
    const save=el("button",{type:"button",class:"go blue",text:"Save key",onclick:async()=>{if(!input.value.trim()){status.textContent="Paste a key first. Existing key kept.";return}try{const r=await api(endpoint,{id,key:input.value});input.value="";has=r.has_key;refresh()}catch(e){status.textContent=e.message}}});
    const remove=el("button",{type:"button",class:"go ghost",text:"Remove key",onclick:async()=>{try{const r=await api(endpoint,{id,clear:true});has=r.has_key;refresh()}catch(e){status.textContent=e.message}}});
    keyrow.append(input,save,remove);
    cb.addEventListener("change",()=>{cb.checked?set.add(id):set.delete(id);refresh();library?persistLibraries():persistWeb()});
    card.append(el("div",{class:"source-key-top"},el("label",{class:"check sw"},cb,el("b",{text:name})),badge),status,keyrow,help);refresh();host.append(card);
  }
  const loaded=window.CCLoadedApp || await api("/api/config");
  host.prepend(el("div", {class:"loaded-source-overview"}, el("b", {text:"This Nerd's configured sources"}), ...loaded.sources.map(s=>el("p", {text:s.label + " · " + s.type})),el("small", {text:"Already active from the loaded Nerd. The controls below add optional searches."})));
  SEARCH.forEach(p=>service(p.id,p.name,false,false,p.url));
  host.append(el("h3",{text:"Reference libraries"}));
  [["pubmed","PubMed"],["arxiv","arXiv"],["wikipedia","Wikipedia"],["crossref","Crossref"],["openalex","OpenAlex"]].forEach(([id,name])=>service(id,name,true,id!=="openalex","https://openalex.org/settings/api"));
  host.append(el("p",{class:"h",text:"Key-free libraries work without adding a secret. OpenAlex uses its own API key; check its pricing before enabling requests."}));
}

function boot() {
  if (!$("#pvbox") || !$("#menu a")) return setTimeout(boot, 200);
  modelGuide();
  const host=el("section",{class:"tile",id:"sec-search"});
  $("#sec-model").after(host);codePanel(host);

  const io=new IntersectionObserver(es=>{for(const e of es)if(e.isIntersecting){$("#pvbox").hidden=false;document.querySelectorAll("#menu a").forEach(a=>a.classList.toggle("on",a.getAttribute("href")==="#sec-search"));}},{rootMargin:"-20% 0px -70% 0px"});io.observe(host);
}
boot();
})();
