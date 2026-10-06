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
const NOTE = (m) => { const n = $("#msg"); if (n) { n.textContent = m; n.className = "msg"; } };
let stages = [], real = false;

function diagram() {
  const box = el("div", { class: "pipe", role: "list", "aria-label": "Order of steps for each question" });
  const order = ["question_check", "standalone", "queries", "relevance", "answer", "faithfulness", "followups"];
  const names = { question_check: "Check question", standalone: "Make standalone", queries: "Write searches", relevance: "Keep relevant", answer: "Write answer", faithfulness: "Check support", followups: "Suggest follow-ups" };
  order.forEach((k, i) => {
    const s = stages.find((x) => x.key === k); const on = !s || !s.optional || s.on;
    if (i) box.append(el("span", { class: "arrow", "aria-hidden": "true", text: "\u203A" }));
    box.append(el("a", { href: "#st-" + k, role: "listitem", class: "step" + (on ? "" : " off"), text: names[k] + (on ? "" : " (off)") }));
  });
  return box;
}

function stageCard(s) {
  const area = el("textarea", { rows: "6", maxlength: "6000", "aria-label": s.label + " prompt", spellcheck: "false" });
  area.value = s.text || s.default;
  const brief = el("input", { placeholder: "Describe your topic in a sentence (optional)", "aria-label": "About your topic" });
  const st = el("span", { class: "testres", role: "status" });
  const sw = s.optional ? el("label", { class: "check sw" }, el("input", { type: "checkbox", id: "on-" + s.key }), " Use this step") : null;
  if (sw) { $("input", sw).checked = !!s.on; $("input", sw).addEventListener("change", async (e) => { try { await api("/api/prompts/save", { key: s.key, on: e.target.checked }); s.on = e.target.checked; const sm = $("summary small", $("#st-" + s.key)); if (sm) sm.textContent = s.on ? "On" : "Off"; redrawDiagram(); st.textContent = e.target.checked ? "On." : "Off."; } catch (x) { st.textContent = x.message; e.target.checked = !e.target.checked; } }); }
  const save = el("button", { type: "button", class: "go blue", text: "Save", onclick: async () => { try { const txt = area.value.trim() === s.default.trim() ? "" : area.value; const r = await api("/api/prompts/save", { key: s.key, text: txt }); s.text = txt; st.textContent = "Saved. New questions use it."; } catch (x) { st.textContent = x.message; } } });
  const reset = el("button", { type: "button", class: "go ghost", text: "Use default", onclick: async () => { try { await api("/api/prompts/reset", { key: s.key }); s.text = ""; area.value = s.default; st.textContent = "Back to the default."; } catch (x) { st.textContent = x.message; } } });
  const gen = el("button", { type: "button", class: "go ghost", text: "Write it with AI", onclick: async () => { gen.disabled = true; st.textContent = "Writing..."; try { const r = await api("/api/prompts/generate", { key: s.key, brief: brief.value, current: area.value }); area.value = r.prompt; st.textContent = (r.model_used ? "Written by your model. " : "Built-in template used (no model connected). ") + "Read it, then press Save."; if (r.rationale && r.rationale.length) why.textContent = r.rationale.join(" "); } catch (x) { st.textContent = x.message; } gen.disabled = false; } });
  const why = el("p", { class: "h" });
  return el("details", { class: "stage", id: "st-" + s.key }, el("summary", {}, el("b", { text: s.label }), el("small", { text: s.optional ? (s.on ? "On" : "Off") : "Always on" })), el("div", { class: "sbody" }, el("p", { class: "h", text: s.help }), sw, area, el("div", { class: "keyrow" }, brief, gen), why, el("div", { class: "keyrow" }, save, reset, st)));
}
let dg;
function redrawDiagram() { if (dg) { const n = diagram(); dg.replaceWith(n); dg = n; } }

function codeCard(kind, title, help, ph) {
  const brief = el("textarea", { rows: "3", "aria-label": title + " description", placeholder: ph });
  const host = el("div", { class: "cmhost" });
  const ed = window.CCEditor ? window.CCEditor.create(host, { doc: "" }) : null;
  const fallback = ed ? null : el("textarea", { rows: "12", class: "code", spellcheck: "false", "aria-label": title + " code" });
  const code = { get value() { return ed ? ed.get() : fallback.value; }, set value(v) { if (ed) ed.set(v); else fallback.value = v; } };
  if (ed) { let free = false; host.addEventListener("keydown", (e) => { if (e.key === "Escape") { free = true; return; } if (e.key === "Tab" && free) { e.stopImmediatePropagation(); free = false; return; } free = false; }, true); }
  if (ed) { host.dataset.ph = "The code appears here after you press Write the code."; const sync = () => host.classList.toggle("filled", !!ed.get()); new MutationObserver(sync).observe(host, { childList: true, subtree: true, characterData: true }); sync(); }
  const out = el("div", { class: "review", role: "status", "aria-live": "polite" });
  async function review() { try { const r = await api("/api/codegen/review", { kind, code: code.value }); out.className = "review " + (r.ok ? "ok" : "bad"); if (ed) { host._marks = r.marks || []; ed.mark(host._marks); } out.replaceChildren(el("b", { text: r.ok ? "Safety check passed" : "Needs changes" }), ...(r.problems || []).map((p) => el("div", { text: p }))); } catch (x) { out.textContent = x.message; } }
  const gen = el("button", { type: "button", class: "go blue", text: "Write the code", onclick: async () => { if (!brief.value.trim()) { out.className = "review bad"; out.textContent = "Describe what it should do first."; return; } gen.disabled = true; out.className = "review"; out.textContent = "Writing..."; try { const r = await api("/api/codegen", { kind, brief: brief.value, sample }); sample = ""; code.value = r.code || ""; await review(); if (!r.model_used) out.append(el("div", { class: "h", text: "No model is connected, so this is a starting template to edit." })); } catch (x) { out.className = "review bad"; out.textContent = x.message; } gen.disabled = false; } });
  let sample = "";
  const tq = el("input", { placeholder: "Sample question to try", "aria-label": "Sample question", value: kind === "search" ? "vitamin D and sleep" : "Can you tell me about vitamin D?" });
  const tres = el("div", { class: "review", role: "status", "aria-live": "polite" });
  const tryBtn = el("button", { type: "button", class: "go ghost", text: "Try it", title: "Runs this code once, in a separate limited process, with your sample question", onclick: async () => {
    tryBtn.disabled = true; out.className = "review"; out.textContent = ""; if (ed) ed.mark([]); tres.className = "review"; tres.textContent = "Running once..."; try { const r = await api("/api/codegen/test", { kind, code: code.value, query: tq.value }); tres.className = "review " + (r.ok ? "ok" : "bad");
      const rows = [el("b", { text: r.ok ? "Worked" + (kind === "search" ? ": " + r.count + " result" + (r.count === 1 ? "" : "s") + " in " + r.seconds + "s" : ": " + (r.result || "")) : r.error || (r.empty ? "It ran but returned no results. Try another sample question, or show a raw response and rewrite the parsing." : "Needs changes")})];
      (r.problems || []).forEach((x) => rows.push(el("div", { text: x }))); (r.items || []).forEach((it) => rows.push(el("div", { class: "item", text: (it.title || "(no title)") + (it.year ? " (" + it.year + ")" : "") + ": " + (it.text || "").slice(0, 110) })));
      if (r.ok && (r.items || []).length) { const norm = JSON.stringify(r.items, null, 2); const parts = [el("div", { class: "h", text: "Normalized: what the chat receives from your code" }), el("pre", { class: "code", text: norm.slice(0, 4000) })]; if (raw.value.trim()) parts.unshift(el("div", { class: "h", text: "Raw: what the API sent (the box above)" }), el("pre", { class: "code", text: raw.value.slice(0, 1500) })); rows.push(el("details", { class: "stage inner" }, el("summary", {}, el("b", { text: "Compare raw and normalized" })), el("div", { class: "sbody" }, ...parts))); }
      tres.replaceChildren(...rows); } catch (x) { tres.className = "review bad"; tres.textContent = x.message; } tryBtn.disabled = false; } });
  const url = el("input", { placeholder: "https://api.example.org/search?q={query}", "aria-label": "API address for a sample response" });
  const raw = el("textarea", { rows: "5", class: "code", "aria-label": "Raw response", placeholder: "A raw response from the API appears here. You can also paste one.", spellcheck: "false" });
  const show = el("button", { type: "button", class: "go ghost", text: "Show raw response", onclick: async () => { try { const r = await api("/api/codegen/sample", { url: url.value, query: tq.value }); raw.value = r.body; tres.className = "review"; tres.textContent = "Got HTTP " + r.status + " (" + (r.type || "unknown type") + "). Now press Rewrite parsing."; } catch (x) { tres.className = "review bad"; tres.textContent = x.message; } } });
  const rewrite = el("button", { type: "button", class: "go blue", text: "Rewrite parsing from this response", onclick: () => { sample = raw.value; gen.click(); } });
  const live = kind === "search" ? el("details", { class: "stage inner" }, el("summary", {}, el("b", { text: "Match a real response" }), el("small", { text: "Optional" })), el("div", { class: "sbody" }, el("p", { class: "h", text: "Fetch one real response so the parsing fits it." }), el("div", { class: "keyrow" }, url, show), raw, rewrite)) : null;
  const copy = el("button", { type: "button", class: "go ghost", text: "Copy", onclick: () => { navigator.clipboard && navigator.clipboard.writeText(code.value); out.textContent = "Copied."; } });
  const chk = el("button", { type: "button", class: "go ghost", text: "Check again", onclick: review });
  return el("div", { class: "sub" }, el("b", { text: title }), el("small", { text: help }), brief, live, el("div", { class: "keyrow tight" }, gen, chk, copy), ed ? host : fallback, ed ? el("small", { class: "h", text: "Tab indents. Press Esc, then Tab, to move on to the next control." }) : null, out, el("div", { class: "keyrow" }, tq, tryBtn), tres);
}

function build(col) {
  const prompts = el("section", { class: "tile", id: "sec-prompts" }, el("div", { class: "head" }, el("span", { class: "ic purple", text: "\u2630" }), el("div", {}, el("b", { text: "Prompts" }), el("small", { text: "The instructions behind each step of an answer" }))),
    el("div", { class: "help", text: "Each question passes through these steps. Open one to edit it." }));
  dg = diagram(); prompts.append(dg);
  stages.forEach((s) => prompts.append(stageCard(s)));
  if (!real) prompts.append(el("p", { class: "h", text: "Optional steps need a real model." }));
  const code = el("section", { class: "tile", id: "sec-code" }, el("div", { class: "head" }, el("span", { class: "ic green", text: "</>" }), el("div", {}, el("b", { text: "Code helpers" }), el("small", { text: "Describe it, read the code, then use it yourself" }))),
    el("div", { class: "help", text: "These write small Python helpers. Code is checked, then shown. It runs only when you press Try it." }),
    codeCard("search", "Search connector", "Pulls passages from your own API or website.", "Example: search my clinic's JSON API at https://example.org/api, using the q parameter, and return title, text and link."),
    codeCard("clean_query", "Query cleaning", "Tidies a question before it is searched.", "Example: remove filler words, keep drug names and numbers, and lowercase everything."));
  const m = $("#sec-model"); const anchor = $("#look");
  col.insertBefore(prompts, anchor); col.insertBefore(code, anchor);
  const menu = $("#menu"); const go = () => { if (!menu.children.length) return setTimeout(go, 150); for (const [id, t] of [["prompts", "Prompts"], ["code", "Code helpers"]]) menu.append(el("a", { href: "#sec-" + id, text: t })); }; go();
}
async function init() {
  try { const d = await api("/api/prompts"); stages = d.stages; real = d.real_model; } catch (e) { return; }
  build($("#col"));
}
init();
})();
