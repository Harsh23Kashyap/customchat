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
const STEPS = ["Open the key page and sign in, or create an account.", "Choose the button to create a new API key and name it CustomChat.", "Copy the key right away. Some sites show it only once.", "Paste it into the key box here and press Save. Never send it to anyone or save it in a file."];
const MODEL_GUIDES = {
  openai: { name: "OpenAI", url: "https://platform.openai.com/api-keys", help: "https://help.openai.com/en/articles/4936850", note: "API use is billed separately from a ChatGPT subscription. Check the billing page for your limits.", steps: STEPS },
  claude: { name: "Claude", url: "https://console.anthropic.com/settings/keys", help: "https://platform.claude.com/docs/en/get-api-key", note: "Keys live in the Claude Console under Settings, then API keys.", steps: STEPS },
  gemini: { name: "Gemini", url: "https://aistudio.google.com/app/apikey", help: "https://ai.google.dev/gemini-api/docs/api-key", note: "There is a free usage tier for the Gemini API. Its limits are listed on Google's billing page.", steps: STEPS },
  groq: { name: "Groq", url: "https://console.groq.com/keys", help: "https://console.groq.com/docs/quickstart", note: "The keys page has a Create API Key button.", steps: STEPS },
  mistral: { name: "Mistral", url: "https://docs.mistral.ai/getting-started/quickstarts/studio/activate-and-generate-api-key", help: "https://docs.mistral.ai/getting-started/quickstarts/studio/activate-and-generate-api-key", note: "Mistral's guide says free mode has API access on by default with no credit card.", steps: ["Open Mistral's guide and follow its steps to open Studio and create a key.", "Copy the key right away.", "Paste it into the key box here and press Save."] },
  minimax: { name: "MiniMax", url: "https://platform.minimax.io/docs/guides/quickstart-preparation", help: "https://platform.minimax.io/docs/guides/quickstart-preparation", note: "Register, then create a key as described on that page.", steps: ["Open MiniMax's guide, register or sign in, and create an API key.", "Copy the key right away.", "Paste it into the key box here and press Save."] },
  mimo: { name: "Xiaomi MiMo", url: "https://platform.xiaomimimo.com/console/api-keys", help: "https://mimo.mi.com/docs/en-US/quick-start/faq/api-integration", note: "After login, apply for a key in the console.", steps: ["Open the console page and sign in.", "Apply for a new API key.", "Copy it and paste it into the key box here."] },
  deepseek: { name: "DeepSeek", url: "https://api-docs.deepseek.com/", help: "https://api-docs.deepseek.com/", note: "DeepSeek's docs say to create an API key first. I could not confirm the exact key page, so follow its docs.", steps: null },
  openrouter: { name: "OpenRouter", url: "https://openrouter.ai/collections/free-models", help: "https://openrouter.ai/collections/free-models", note: "OpenRouter lists models with $0 prices. I could not confirm the key steps, so follow its site.", steps: null }
};
const NAME2ID = { OpenAI: "openai", Claude: "claude", Gemini: "gemini", Groq: "groq", Mistral: "mistral", MiniMax: "minimax", "Xiaomi MiMo": "mimo", DeepSeek: "deepseek", OpenRouter: "openrouter" };
const SEARCH = [
  { id: "tavily", name: "Tavily", pro: "Made for AI apps. Returns short, clean snippets.", free: "Free plan: 1,000 credits a month (Tavily docs).", url: "https://app.tavily.com/", docs: "https://docs.tavily.com/documentation/quickstart" },
  { id: "exa", name: "Exa", pro: "Finds pages by meaning, good for papers and documentation.", free: "New accounts get $20 in credits, plus $10 a month on the free tier (Exa pricing).", url: "https://dashboard.exa.ai/api-keys", docs: "https://exa.ai/docs/reference/pricing" },
  { id: "firecrawl", name: "Firecrawl", pro: "Searches and can read whole pages.", free: "Free plan: 500 searches or 1,000 pages, no card (Firecrawl pricing).", url: "https://www.firecrawl.dev/app", docs: "https://docs.firecrawl.dev/billing" },
  { id: "parallel", name: "Parallel", pro: "Takes a plain-language goal and returns focused excerpts.", free: "Paid by use: about $5 per 1,000 searches, $1 in turbo mode. A free tier is not confirmed.", url: "https://platform.parallel.ai/", docs: "https://docs.parallel.ai/getting-started/pricing" }
];

function svgSteps() {
  const s = 'http://www.w3.org/2000/svg';
  const w = document.createElementNS(s, "svg"); w.setAttribute("viewBox", "0 0 300 60"); w.setAttribute("class", "gsvg"); w.setAttribute("role", "img"); w.setAttribute("aria-label", "Open the site, create a key, paste it here");
  w.innerHTML = '<g fill="none" stroke="#5d7388" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="8" y="12" width="52" height="36" rx="6"/><path d="M8 22h52"/><circle cx="14" cy="17" r="1.2"/><path d="M70 30h18m-5-5 5 5-5 5"/><circle cx="118" cy="26" r="9"/><path d="M127 30h24m-6 0v8m-7-8v6"/><path d="M168 30h18m-5-5 5 5-5 5"/><rect x="198" y="16" width="92" height="28" rx="14"/><path d="M212 30h4m6 0h4m6 0h4m6 0h4"/></g><g fill="#5d7388" font-size="9" font-family="DM Sans,sans-serif"><text x="10" y="58">Open</text><text x="100" y="58">Create key</text><text x="224" y="58">Paste</text></g>';
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
  host.replaceChildren(el("div", { class: "pvhead" }, el("b", { text: "Try a prompt" })), el("p", { class: "h", text: "Pick a step, give it a sample question and passages, and see what your model answers. Nothing is saved." }));
  const sel = el("select", { "aria-label": "Step to try" });
  const keys = [["answer", "Answer"], ["queries", "Search queries"], ["standalone", "Standalone question"], ["relevance", "Relevance filter"], ["faithfulness", "Support check"], ["followups", "Follow-ups"], ["question_check", "Question check"], ["summary", "Summary"]];
  keys.forEach(([k, t]) => sel.append(el("option", { value: k, text: t })));
  const q = el("input", { placeholder: "Sample question", "aria-label": "Sample question", value: "What does the refund policy say?" });
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
  host.replaceChildren(el("div", { class: "pvhead" }, el("b", { text: "Live search keys" })), el("p", { class: "h", text: "Optional. A search key lets the code helper look up an API's documentation, and lets answers include live web results. Keys stay on this computer and are never shown again." }));
  host.append(el("details", { class: "stage", open: "" }, el("summary", {}, el("b", { text: "Why add a search key?" }), el("small", { text: "Optional" })), el("div", { class: "sbody why" },
    el("p", { text: "Without one, answers come only from your own files and the sources you set up. A search key lets the chat look things up on the live web too." }),
    el("b", { text: "It helps in two places" }),
    el("ul", {}, el("li", { text: "Answers: recent facts, news and anything your files do not cover are added as extra sources, with clear web labels in the citations." }), el("li", { text: "Code helper: it can read an API's documentation first, so the connector it writes matches how that API really behaves." })),
    el("b", { text: "In technical terms" }),
    el("p", { class: "h", text: "The key authenticates calls to the provider's search endpoint. Results are normalized to title, text and link, deduplicated and ranked with your other evidence. If the service fails or runs out of credits, answers fall back to your local sources. Free tiers have monthly limits. You can leave this off." }))));
  let src = { on: false, provider: "" };
  try { const d = await api("/api/websearch/status"); keyStatus = Object.fromEntries(d.providers.map((p) => [p.id, p.has_key])); src = d.source || src; } catch (e) { }
  const sst = el("small", { class: "h", role: "status" });
  const psel = el("select", { "aria-label": "Search provider for answers" }); SEARCH.forEach((p) => psel.append(el("option", { value: p.id, text: p.name + (keyStatus[p.id] ? "" : " (no key)") }))); psel.value = src.provider || (SEARCH.find((p) => keyStatus[p.id]) || SEARCH[0]).id;
  const tog = el("input", { type: "checkbox", id: "websrc" }); tog.checked = !!src.on;
  const push = async () => { try { const r = await api("/api/websearch/source", { on: tog.checked, provider: psel.value }); sst.textContent = r.on ? "On. Answers now also use live results from " + psel.value + ". If it fails, local sources still answer." : "Off."; } catch (e) { tog.checked = false; sst.textContent = e.message; } };
  tog.addEventListener("change", push); psel.addEventListener("change", () => { if (tog.checked) push(); });
  host.append(el("div", { class: "gcard" }, el("label", { class: "check sw" }, tog, " Add live web results to answers"), psel, sst));
  for (const p of SEARCH) {
    const st = el("span", { class: "testres", role: "status" }); const key = el("input", { type: "password", placeholder: keyStatus[p.id] ? "Key saved" : "Paste key", autocomplete: "off", "aria-label": p.name + " key" });
    const save = el("button", { type: "button", class: "go blue", text: "Save", onclick: async () => { try { const r = await api("/api/websearch/key", { id: p.id, key: key.value }); key.value = ""; key.placeholder = r.has_key ? "Key saved" : "Paste key"; st.textContent = "Saved."; } catch (e) { st.textContent = e.message; } } });
    const test = el("button", { type: "button", class: "go ghost", text: "Test", onclick: async () => { st.textContent = "Testing..."; try { const r = await api("/api/websearch/test", { id: p.id, query: "NASA open APIs" }); st.textContent = r.ok ? "Works: " + r.items.length + " results" + (r.items[0] ? ". First: " + r.items[0].title.slice(0, 60) : "") : r.error; } catch (e) { st.textContent = e.message; } } });
    const clear = el("button", { type: "button", class: "go ghost", text: "Remove", onclick: async () => { await api("/api/websearch/key", { id: p.id, clear: true }); key.placeholder = "Paste key"; st.textContent = "Removed."; } });
    host.append(el("details", { class: "stage" }, el("summary", {}, el("b", { text: p.name }), el("small", { text: keyStatus[p.id] ? "Key saved" : "No key" })), el("div", { class: "sbody" }, el("p", { text: p.pro }), el("p", { class: "h", text: p.free }), el("div", { class: "keyrow" }, key, save, test, clear), st, stepsBlock({ url: p.url, help: p.docs, steps: STEPS }))));
  }
  host.append(el("p", { class: "h", text: "The code helper's research option uses the provider chosen above, or the first one that has a key." }));
}

function boot() {
  if (!$("#pvbox") || !$("#sec-prompts")) return setTimeout(boot, 200);
  modelGuide();
  const ctx = ctxBox();
  const state = { which: "" };
  const apply = async (w) => {
    if (w === state.which) return; state.which = w;
    if (w) document.querySelectorAll("#menu a").forEach((a) => a.classList.toggle("on", a.getAttribute("href") === "#sec-" + w));
    $("#pvbox").hidden = w === "prompts" || w === "code"; ctx.hidden = !(w === "prompts" || w === "code");
    if (w === "prompts") promptsPanel(ctx); else if (w === "code") await codePanel(ctx);
  };
  const ids = ["sec-prompts", "sec-code"];
  const io = new IntersectionObserver((es) => { for (const e of es) { if (e.isIntersecting) apply(e.target.id.replace("sec-", "")); else if (state.which === e.target.id.replace("sec-", "")) apply(""); } }, { rootMargin: "-25% 0px -60% 0px" });
  ids.forEach((i) => io.observe($("#" + i)));
}
boot();
})();
