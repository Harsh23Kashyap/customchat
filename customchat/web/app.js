(() => {
"use strict";
const $ = (s) => document.querySelector(s);
const el = (tag, props = {}, ...kids) => {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (k === "class") e.className = v; else if (k === "text") e.textContent = v;
    else if (k.startsWith("on")) e.addEventListener(k.slice(2), v); else e.setAttribute(k, v);
  }
  for (const c of kids.flat()) if (c != null) e.append(c.nodeType ? c : document.createTextNode(c));
  return e;
};
const ICON = {
  clip: "M21 11.5l-8.6 8.6a5 5 0 01-7-7l9-9a3.3 3.3 0 014.7 4.7l-9 9a1.7 1.7 0 01-2.4-2.4l8.3-8.3",
  pin: "M12 17v5M9 3h6l-1 7 3 3v2H7v-2l3-3z",
  trash: "M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3",
  edit: "M4 20h4L19 9l-4-4L4 16z",
  down: "M12 4v12M6 12l6 6 6-6",
  tray: "M12 3v11M7 10l5 5 5-5M5 20h14",
  topic: "M12 5v14M5 12h14",
  send: "M12 19V5M5 12l7-7 7 7",
  stop: "M7 7h10v10H7z",
  mic: "M12 15a3 3 0 003-3V6a3 3 0 00-6 0v6a3 3 0 003 3zM6 11a6 6 0 0012 0M12 17v4",
  temp: "M12 3a9 9 0 100 18 9 9 0 000-18zM12 7v5l3 2",
  user: "M12 12a4 4 0 100-8 4 4 0 000 8zM4 21a8 8 0 0116 0",
  up: "M12 20V8M6 12l6-6 6 6",
  menu: "M4 7h16M4 12h16M4 17h16",
  close: "M6 6l12 12M18 6L6 18",
};
const svg = (n) => { const e = document.createElementNS("http://www.w3.org/2000/svg", "svg"); e.setAttribute("viewBox", "0 0 24 24"); e.setAttribute("width", "18"); e.setAttribute("height", "18"); e.setAttribute("fill", "none"); e.setAttribute("stroke", "currentColor"); e.setAttribute("stroke-width", "2"); e.setAttribute("stroke-linecap", "round"); e.setAttribute("stroke-linejoin", "round"); const p = document.createElementNS("http://www.w3.org/2000/svg", "path"); p.setAttribute("d", ICON[n]); e.append(p); return e; };
const S = { scope: null, suggestions: null, cfg: null, chat: null, topic: null, newTopic: false, tab: "chats", sources: new Set(), turns: [], ratings: {}, temp: false, useProfile: localStorage.getItem("cc_profile_on") === "1", busy: false, token: localStorage.getItem("cc_token") || "" };

const TV = (k) => ((window.CCTheme && window.CCTheme.value) || {})[k] || "";
const PREVIEW = !!window.__ccPreview;
function avatar(kind) {
  const e = TV(kind === "bot" ? "emoji_bot" : "emoji_you"), a = S.cfg.app;
  return el("div", { class: "av " + kind + (e ? " emo" : ""), text: e || (kind === "bot" ? (TV("txt_title") || a.title || "AI").replace(/[^A-Za-z]/g, "").slice(0, 2) : "You") });
}
async function api(path, body) {
  const h = { "Content-Type": "application/json" };
  if (S.token) h.Authorization = "Bearer " + S.token;
  const r = await fetch(path, body === undefined ? { headers: h } : { method: "POST", headers: h, body: JSON.stringify(body) });
  const d = await r.json().catch(() => ({}));
  if (r.status === 401 && S.cfg && S.cfg.auth === "accounts" && !path.startsWith("/api/account/")) { location.reload(); return new Promise(() => {}); }
  if (r.status === 401 && S.cfg && S.cfg.auth === "token") {
    const t = prompt("Access token"); if (t) { S.token = t; localStorage.setItem("cc_token", t); return api(path, body); }
  }
  if (!r.ok) throw new Error(d.error || "Request failed");
  return d;
}
function centerToast(t) { const m = document.querySelector(".main"); if (m) { const r = m.getBoundingClientRect(); t.style.left = (r.left + r.width / 2) + "px"; } return t; }
function toast(msg) { document.querySelectorAll(".toast").forEach((x) => x.remove()); const t = el("div", { class: "toast", role: "status", "aria-live": "polite", text: msg }); document.body.append(t); centerToast(t); setTimeout(() => t.classList.add("out"), 2000); setTimeout(() => t.remove(), 2250); }

function inline(parent, text, evidence) {
  // safe inline markdown: **bold**, `code`, and [n] citations. Everything is text nodes.
  let afterCite = false;
  text.split(/(\*\*[^*]+\*\*|`[^`]+`|\[\d+\])/).forEach((p) => {
    let m; const wasCite = afterCite; afterCite = false;
    if ((m = p.match(/^\[(\d+)\]$/)) && evidence.some((e) => e.n === +m[1])) { parent.append(el("button", { class: "cite", title: "Show source " + m[1], onclick: () => showSources(evidence, +m[1]) }, "[" + m[1] + "]")); afterCite = true; }
    else if (/^\*\*[^*]+\*\*$/.test(p)) parent.append(el("strong", { text: p.slice(2, -2) }));
    else if (/^`[^`]+`$/.test(p)) parent.append(el("code", { text: p.slice(1, -1) }));
    else if (p) parent.append(document.createTextNode((wasCite && /^[.,;:!?)]/.test(p) ? "\u2060" : "") + p));
  });
}
function renderAnswer(text, evidence) {
  const box = el("div", { class: "a" });
  let list = null;
  text.split(/\n/).forEach((line) => {
    const li = line.match(/^\s*(?:[-*]|\d+[.)])\s+(.*)/), h = line.match(/^#{1,3}\s+(.*)/);
    if (li) { if (!list) { list = el("ul"); box.append(list); } const x = el("li"); inline(x, li[1], evidence); list.append(x); return; }
    list = null;
    if (!line.trim()) return;
    const p = el(h ? "h4" : "p"); inline(p, h ? h[1] : line, evidence); box.append(p);
  });
  return box;
}

function highlight(node, text, terms) {
  if (!terms.length) { node.textContent = text; return node; }
  const re = new RegExp("(" + terms.map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|") + ")", "gi");
  text.split(re).forEach((p, i) => node.append(i % 2 ? el("mark", { text: p }) : document.createTextNode(p)));
  return node;
}
function sendIcon(name, label) {
  const send = $("#send"); send.replaceChildren(name === "send" && TV("emoji_send") ? document.createTextNode(TV("emoji_send")) : svg(name)); send.setAttribute("aria-label", label);
  if (motionAllowed() && send.animate) send.animate([{opacity:.5,transform:"scale(.95)"},{opacity:1,transform:"scale(1)"}],{duration:150,easing:"ease-out"});
}
function motionAllowed() { return document.documentElement.dataset.motion !== "none" && !matchMedia("(prefers-reduced-motion: reduce)").matches; }
let sourceExit;
function closeSources() {
  const pane = $("#sources");
  if (!motionAllowed() || !pane.animate) { $("#app").classList.remove("src"); return; }
  sourceExit = pane.animate([{opacity:1, transform:"translateX(0)"}, {opacity:0, transform:"translateX(12px)"}], {duration:160, easing:"ease-in"});
  sourceExit.onfinish = () => { $("#app").classList.remove("src"); sourceExit = null; };
}
function showSources(evidence, hl) {
  const terms = [...new Set(((S.turns[S.turns.length - 1] || {}).standalone || "").toLowerCase().match(/[a-z0-9]{4,}/g) || [])].slice(0, 8);
  const pane = $("#sources");
  if (sourceExit) { sourceExit.onfinish = null; sourceExit.cancel(); sourceExit = null; }
  const opening = !$("#app").classList.contains("src"); pane.replaceChildren();
  $("#app").classList.add("src");
  const types = [...new Set(evidence.map((e) => e.source))];
  const filters = el("div", { class: "filters" });
  const list = el("div");
  const draw = (only) => {
    list.replaceChildren(...evidence.filter((e) => !only || e.source === only).map((e) => el("div", { class: "src" + (e.n === hl ? " hl" : "") },
      el("b", { text: e.n + ". " + e.title }),
      el("small", { text: [e.authors.slice(0, 3).join(", "), e.year, e.venue, e.document, e.page ? "page " + e.page : e.section, e.version ? "version " + e.version.slice(0, 12) : "", e.ocr ? "OCR text, check original" : ""].filter(Boolean).join(" · ") }),
      highlight(el("p"), e.text, terms),
      e.url ? el("a", { href: e.url, target: "_blank", rel: "noopener noreferrer", text: "Open source" }) : null)));
  };
  if (types.length > 1) types.forEach((t) => filters.append(el("button", { class: "chip", onclick: (ev) => {
    const on = ev.target.classList.toggle("on"); filters.querySelectorAll(".chip").forEach((c) => c !== ev.target && c.classList.remove("on")); draw(on ? t : null);
  } }, (S.cfg.sources.find((s) => s.id === t) || {}).label || t)));
  pane.append(el("button", { class: "icon", style: "float:right", "aria-label": "Close", onclick: closeSources }, svg("close")),
    el("h3", { text: "Sources" }), el("div", { class: "sub", text: evidence.length + " used for this answer" }), filters, list);
  draw(null);
  if (opening && motionAllowed() && pane.animate) pane.animate([{opacity:0, transform:"translateX(16px)"}, {opacity:1, transform:"translateX(0)"}], {duration:240, easing:"cubic-bezier(.2,.8,.2,1)"});
  const selected = list.querySelector(".hl");
  if (selected) {
    selected.scrollIntoView({block:"nearest", behavior:motionAllowed() ? "smooth" : "auto"});
    if (motionAllowed() && selected.animate) selected.animate([{opacity:.7, transform:"translateY(2px)"},{opacity:1, transform:"none"}],{duration:180,easing:"ease-out"});
  }
}

function turnView(t, prev) {
  const nodes = [];
  if (prev && prev.chat !== t.chat) nodes.push(el("div", { class: "divider", text: "Earlier chat" }));
  nodes.push(el("div", { class: "row u" }, avatar("you"), el("div", { class: "bubble ub", text: t.question })));
  const bub = el("div", { class: "bubble bb" + (t.evidence.length ? "" : " none") }, renderAnswer(t.answer, t.evidence));
  if (!t.evidence.length) {
    const ill = document.createElementNS("http://www.w3.org/2000/svg", "svg"); ill.setAttribute("viewBox", "0 0 96 96"); ill.setAttribute("class", "nf-ill"); ill.setAttribute("aria-hidden", "true");
    ill.innerHTML = '<g fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M26 14h30l14 14v50H26z"/><path d="M56 14v15h14"/><path d="M36 42h24M36 52h18" opacity=".5"/><circle cx="58" cy="62" r="13" class="nf-lens"/><path d="m67 71 12 12"/></g>';
    bub.prepend(el("div", { class: "nf-h", text: "No evidence found" }));
    bub.prepend(ill);
    const tip = (txt, fn) => el("button", { class: "tip", onclick: fn }, el("span", { text: txt }), el("span", { class: "go", "aria-hidden": "true", text: "\u203a" }));
    bub.append(el("div", { class: "nf-tips" }, tip("Try a different question", () => { $("#q").focus(); }), tip("Use words from your documents", () => { $("#q").focus(); }), tip("See which documents this chat uses", () => { location.href = "/settings.html"; })));
  }
  const srcLabel = (e) => (S.cfg.sources.find((x) => x.id === e.source) || {}).label || e.source || "";
  const srcs = !t.evidence.length ? null : (el("div", { class: "srcs" }, el("div", { class: "srcs-h", text: "Sources" }), t.evidence.slice(0, 5).map((e) => el("button", { class: "s", title: e.title, onclick: () => showSources(t.evidence, e.n) }, el("span", { class: "n", text: "[" + e.n + "]" }), el("span", { class: "sx" }, el("span", { class: "st", text: e.title }), el("span", { class: "sm", text: [srcLabel(e), e.year, e.page ? "page " + e.page : e.section, e.ocr ? "OCR text, check original" : ""].filter(Boolean).join(" \u00b7 ") })), el("span", { class: "go", "aria-hidden": "true", text: "\u203a" })))));
  nodes.push(el("div", { class: "row" }, avatar("bot"), bub));
  const meta = el("div", { class: "meta" });
  const weak = (t.ledger || []).filter((l) => !l.supported || (l.overlap !== undefined && l.overlap < 0.35));
  if (t.evidence.length && weak.length) meta.append(el("button", { class: "chip warn", title: "Sentences without a valid citation or with little overlap with the cited text. Click to see them.", onclick: () => alert("Check these sentences:\n\n" + weak.map((l) => "- " + l.claim).join("\n")) }, weak.length + " to check"));
  if (t.seconds !== undefined) meta.append(el("span", { "data-more": "1", class: "chip", title: "Time to answer" }, t.seconds < 1 ? "<1s" : t.seconds + "s"));
  if (t.standalone && t.standalone !== t.question) meta.append(el("span", { class: "chip", title: "Understood as" }, "Understood as: " + t.standalone));
  if (t.scope) meta.append(el("span", {class:"chip scope-used", text:"Scoped: " + (t.scope.document || t.scope.source)}));
  meta.append(el("button", { "data-more": "1", class: "chip", title: "How this answer was built", onclick: () => contextDialog(t) }, "Context"));
  if (t.evidence.length) meta.append(el("button", { class: "chip copy", onclick: (ev) => { const b = ev.currentTarget; navigator.clipboard.writeText(t.answer).then(() => { toast("Copied"); b.textContent = "Copied"; b.classList.add("done"); setTimeout(() => { b.textContent = "Copy"; b.classList.remove("done"); }, 1600); }); } }, "Copy"));
  if (t.evidence.length) {
    for (const v of [1, -1]) meta.append(el("button", { class: "chip" + (S.ratings[t.id] === v ? " on" : "") + (S.pop === t.id + ":" + v ? " pop" : ""), "aria-pressed": String(S.ratings[t.id] === v), onclick: async () => { const r = S.ratings[t.id] === v ? 0 : v; try { if (r) S.pop = t.id + ":" + v; await api("/api/rate", { turn: t.id, rating: r }); if (r) S.ratings[t.id] = r; else delete S.ratings[t.id]; drawThread(); } catch (e) { toast(e.message); } } }, v > 0 ? "Helpful" : "Not helpful"));
    meta.append(el("button", { "data-more": "1", class: "chip", onclick: () => download("/api/bibtex?turn=" + t.id, "references.bib") }, "BibTeX"));
    meta.append(el("button", { "data-more": "1", class: "chip", onclick: () => download("/api/pdf?turn=" + t.id, "answer.pdf") }, "PDF"));
    for (const s of ["quick", "deep"]) if (S.cfg.styles.includes(s)) meta.append(el("button", { "data-more": "1", class: "chip", onclick: () => regen(t.id, s) }, s === "quick" ? "Shorter" : "Deeper"));
  }
  if (srcs) bub.append(srcs);
  bub.append(meta);
  if (t.followups && t.followups.length) {
    const f = el("div", { class: "meta fu" });
    t.followups.forEach((x) => f.append(el("button", { class: "chip", onclick: () => { $("#q").value = x; send(); } }, x)));
    nodes.push(el("div", { class: "fu-label", text: "Related" }), f);
  }
  meta.append(el("button", { "data-more": "1", class: "chip", onclick: () => branchQuestion(t) }, "Edit + branch"));
  meta.append(el("button", { "data-more": "1", class: "chip del", title: "Delete this answer", onclick: async () => {
    await api("/api/delete-turn", { turn: t.id }); S.turns = S.turns.filter((x) => x.id !== t.id); drawThread();
    const u = el("div", { class: "toast", onclick: async () => { await api("/api/restore-turn", { turn: t.id }); S.turns = await api("/api/turns?chat=" + S.chat); drawThread(); u.remove(); } }, "Answer deleted. Click to undo"); centerToast(u);
    document.body.append(u); setTimeout(() => u.remove(), 6000); } }, "Delete"));
  const more = [...meta.querySelectorAll("[data-more]")];
  if (more.length) { const d = el("details", { class: "more" }, el("summary", { class: "chip", title: "More actions" }, t.evidence.length ? "More" : "Details")); const box = el("div", { class: "more-box" }); more.forEach((b) => box.append(b)); d.append(box); meta.append(d); }
  return nodes;
}
async function branchQuestion(t) {
  if (S.busy) return toast("Wait for the current answer or stop it first");
  const question = prompt("Edit this question. A new branch keeps earlier context and leaves the original unchanged.", t.question);
  if (question == null || !question.trim()) return;
  if (S.temp) return toast("Edit + branch needs a saved chat. Temporary chats stay unsaved.");
  try {
    const result = await api("/api/branch", {turn:t.id, question});
    await openChat(result.chat);
    $("#q").value = result.question; autosize(); rdy(); $("#q").focus();
    const notice = el("div", {class:"branch-notice"}, "New branch. Original unchanged. ", el("button", {class:"chip", onclick:()=>{$("#q").value="";autosize();rdy();openChat(result.original_chat)}}, "Open original"));
    $("#thread .wrap").prepend(notice);
    toast("Branch ready. Review and send your edited question.");
  } catch(e) { toast(e.message); }
}
async function download(path, name) {
  const h = S.token ? { Authorization: "Bearer " + S.token } : {};
  const r = await fetch(path, { headers: h }); if (!r.ok) return toast("Download failed");
  const a = el("a", { href: URL.createObjectURL(await r.blob()), download: name }); a.click();
}

function scopeChip() {
 const p=$("#scopeChip");p.replaceChildren();
 if (S.scope) p.append(el("span",{text:"Only " + (S.scope.document || S.scope.source)}),el("button",{class:"chip",onclick:()=>{S.scope=null;scopeChip()}},"Clear"));
}
async function scopeDialog() {
 try {
  const rows=await api("/api/scopes");const dialog=el("dialog",{class:"reading-dialog scope-dialog"});
  dialog.append(el("header",{class:"reading-head"},el("h2",{text:"Choose source scope"})));
  const options=el("div",{class:"scope-options"});
  for (const row of rows) {
   const choose=(document)=>{S.scope={source:row.source,...(document?{document}:{})};scopeChip();dialog.close()};
   options.append(el("button",{class:"chip",onclick:()=>choose()},"Collection: "+row.label));
   row.documents.forEach(doc=>options.append(el("button",{class:"chip",onclick:()=>choose(doc)},doc)));
  }
  if (!rows.length) options.append(el("p",{text:"No configured sources"}));
  dialog.append(options,el("footer",{},el("button",{class:"reading-done",onclick:()=>dialog.close()},"Done")));
  dialog.addEventListener("close",()=>{dialog.remove();$("#scopeBtn").focus()});document.body.append(dialog);dialog.showModal();
 } catch(e){toast(e.message)}
}
async function loadSuggestions() {
  if (PREVIEW) return;
  try { S.suggestions = await api("/api/suggestions", {temporary: S.temp}); if (!S.turns.length) drawThread(); }
  catch (_) { /* Configured examples remain usable if budget/provider is unavailable. */ }
}
function recentQuestions() {
  if (S.temp || !S.suggestions || !S.suggestions.recent.length) return null;
  return el("div", {class:"recent-questions"}, el("p", {class:"fu-label",text:"Your recent questions"}),
    el("div",{class:"ex"}, S.suggestions.recent.map(x=>el("button",{onclick:()=>{$("#q").value=x;send();}},x))));
}
function heroView() {
  const a = S.cfg.app;
  const he = TV("emoji_hero") || TV("emoji_bot"), exs = TV("txt_examples") ? TV("txt_examples").split("\n").map((x) => x.trim()).filter(Boolean).slice(0, 8) : (S.suggestions ? S.suggestions.questions : a.examples);
  return el("div", { class: "hero" + (PREVIEW ? " mini" : "") }, TV("logo") ? el("img", { class: "hero-logo", src: TV("logo"), alt: "" }) : el("div", { class: "av bot" + (he ? " emo" : ""), text: he || (TV("txt_title") || a.title || "AI").replace(/[^A-Za-z]/g, "").slice(0, 2) }), el("div", {}, el("h1", { text: TV("txt_title") || a.title }), el("p", { text: TV("txt_tagline") || a.tagline }),
    el("div", { class: "ex" }, exs.map((x) => el("button", { onclick: () => { $("#q").value = x; send(); } }, x)))));
}
function chartCard() {
  const parts = [["Whole grains", 46, "var(--brand)"], ["Fruit and veg", 31, "var(--lime)"], ["Beans and lentils", 23, "var(--mut)"]];
  let off = 0; const C = 2 * Math.PI * 15.9155;
  const ring = parts.map(([n, v, c]) => { const e = '<circle r="15.9155" cx="21" cy="21" fill="none" stroke="' + c + '" stroke-width="6" stroke-dasharray="' + (v * C / 100) + ' ' + C + '" stroke-dashoffset="' + (-off * C / 100) + '" transform="rotate(-90 21 21)"></circle>'; off += v; return e; }).join("");
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg"); svg.setAttribute("viewBox", "0 0 42 42"); svg.setAttribute("class", "donut"); svg.setAttribute("role", "img"); svg.setAttribute("aria-label", "Sample day: fiber by food group"); svg.innerHTML = ring;
  return el("div", { class: "chartcard" }, el("b", { text: "Sample day: fiber by food group" }), el("div", { class: "chartrow" }, svg, el("ul", {}, parts.map(([n, v, c]) => el("li", {}, el("i", { style: "background:" + c }), n + " " + v + "%")))));
}
function rdy() { const q = $("#q"), s = $("#send"); if (!q || !s || S.busy) return; const on = !!q.value.trim(); if (on && !s.classList.contains("on")) { s.classList.add("ready"); setTimeout(() => s.classList.remove("ready"), 200); } s.classList.toggle("on", on); }
function drawThread() {
  const th = $("#thread"), priorScroll = th.scrollTop, keep = th.scrollHeight - th.scrollTop - th.clientHeight > 100; th.replaceChildren();
  const w = el("div", { class: "wrap" });
  if (!S.turns.length) {
    const a = S.cfg.app;
    const he = TV("emoji_hero") || TV("emoji_bot"), exs = TV("txt_examples") ? TV("txt_examples").split("\n").map((x) => x.trim()).filter(Boolean).slice(0, 8) : (S.suggestions ? S.suggestions.questions : a.examples);
    w.append(heroView()); const recent = recentQuestions(); if (recent) w.append(recent);
  } else { if (PREVIEW) w.append(heroView()); S.turns.forEach((t, i) => w.append(...turnView(t, S.turns[i - 1]))); if (PREVIEW) w.append(chartCard()); }
  { const rows = [...w.querySelectorAll(".row")], same = th.dataset.chat === String(S.chat), prev = same ? +th.dataset.n || 0 : 0; rows.forEach((r, i) => { if (i >= prev) r.classList.add("fresh"); }); th.dataset.chat = String(S.chat); th.dataset.n = rows.length; }
  th.append(w); th.scrollTop = PREVIEW ? 0 : (keep ? priorScroll : th.scrollHeight);
  $("#pills").replaceChildren();
}

function dayLabel(ts) {
  const d = new Date(ts * 1000), n = new Date(), day = 86400000, start = new Date(n.getFullYear(), n.getMonth(), n.getDate()).getTime();
  if (d.getTime() >= start) return "Today"; if (d.getTime() >= start - day) return "Yesterday"; if (d.getTime() >= start - 7 * day) return "This week"; return "Earlier";
}
async function loadList() {
  const seq = (loadList.seq = (loadList.seq || 0) + 1); const list = $("#list"); list.replaceChildren();
  try {
    if (S.tab === "chats") {
      const rows = await api("/api/chats?q=" + encodeURIComponent($("#search").value)); if (seq !== loadList.seq) return;
      if (!rows.length) list.append(el("div", { class: "empty", text: "No chats yet." }));
      let lastGroup = "";
      const cnt = {}; rows.forEach((c) => { cnt[c.title] = (cnt[c.title] || 0) + 1; });
      rows.forEach((c) => { const g = c.pinned ? "Pinned" : dayLabel(c.created); if (g !== lastGroup) { list.append(el("div", { class: "group", text: g })); lastGroup = g; } list.append(el("div", { class: "item" + (c.id === S.chat ? " on" : ""), title: c.title, onclick: () => openChat(c.id) },
        el("span", { class: "t", text: c.title }), cnt[c.title] > 1 ? el("span", { class: "tm", text: new Date(c.created * 1000).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" }) }) : null, c.pinned ? el("span", { class: "pinned", title: "Pinned" }, svg("pin")) : null,
        el("span", { class: "acts" },
          el("button", { class: c.pinned ? "is-pinned" : "", title: c.pinned ? "Unpin" : "Pin", "aria-label": (c.pinned ? "Unpin " : "Pin ") + c.title, "aria-pressed": c.pinned ? "true" : "false", onclick: async (e) => { e.stopPropagation(); await api("/api/pin", { chat: c.id, pinned: !c.pinned }); loadList(); } }, svg("pin")),
          el("button", { title: "Rename", "aria-label": "Rename " + c.title, onclick: async (e) => { e.stopPropagation(); const t = prompt("Rename chat", c.title); if (t) { await api("/api/rename", { chat: c.id, title: t }); loadList(); } } }, svg("edit")),
          el("button", { title: "Delete", "aria-label": "Delete " + c.title, onclick: async (e) => { e.stopPropagation(); const wasOpen = S.chat === c.id; await api("/api/delete", { chat: c.id }); if (wasOpen) newChat(); loadList(); const u = el("div", { class: "toast", onclick: async () => { await api("/api/restore", { chat: c.id }); loadList(); u.remove(); if (wasOpen) openChat(c.id); } }, "Chat deleted. Undo"); document.body.append(u); centerToast(u); setTimeout(() => u.remove(), 6000); } }, svg("trash"))))); });
    } else {
      const rows = await api("/api/topics"); if (seq !== loadList.seq) return;
      if (!rows.length) list.append(el("div", { class: "empty", text: "Conversations appear after your first question." }));
      rows.forEach((t) => list.append(el("div", { class: "item" + (t.id === S.topic ? " on" : ""), onclick: () => openTopic(t.id) },
        el("span", { class: "t" }, t.title, el("span", { class: "sub", text: (t.summary ? t.summary.slice(0, 70) : t.turns + " question" + (t.turns === 1 ? "" : "s")) })),
        el("span", { class: "acts" }, el("button", { title: "Rename", "aria-label": "Rename " + c.title, onclick: async (e) => { e.stopPropagation(); const n = prompt("Rename conversation", t.title); if (n) { await api("/api/rename-topic", { topic: t.id, title: n }); loadList(); } } }, svg("edit"))))));
    }
  } catch (e) { list.append(el("div", { class: "empty", text: e.message })); }
}

async function openChat(id) {
  setTemp(false);
  S.chat = id; S.newTopic = false;
  S.turns = await api("/api/turns?chat=" + id);
  try { S.ratings = await api("/api/ratings?chat=" + id); } catch (e) { S.ratings = {}; }
  S.topic = S.turns.length ? S.turns[S.turns.length - 1].topic : null;
  $("#chatTitle").textContent = (await api("/api/chats")).find((c) => c.id === id)?.title || "Chat";
  document.title = $("#chatTitle").textContent + " - " + S.cfg.app.title;
  $("#app").classList.remove("menu-open", "src"); drawThread(); loadList();
}
async function openTopic(id) {
  S.topic = id; S.newTopic = false;
  if (!S.chat) S.chat = (await api("/api/chats", {})).id;
  S.turns = await api("/api/topic-turns?topic=" + id);
  $("#chatTitle").textContent = "Conversation"; $("#app").classList.remove("menu-open"); drawThread();
}
function newChat() { setTemp(false); loadSuggestions(); S.chat = null; S.topic = null; S.newTopic = false; S.turns = []; $("#chatTitle").textContent = "New chat"; $("#app").classList.remove("src", "menu-open"); drawThread(); loadList(); $("#q").focus(); }

let aborter = null;
async function stream(body, onEvent) {
  aborter = new AbortController();
  const h = { "Content-Type": "application/json" };
  if (S.token) h.Authorization = "Bearer " + S.token;
  const r = await fetch("/api/ask-stream", { method: "POST", headers: h, body: JSON.stringify(body), signal: aborter.signal });
  if (!r.ok) { const d = await r.json().catch(() => ({})); throw new Error(d.error || ("The app returned an error (HTTP " + r.status + ")")); }
  const reader = r.body.getReader(), dec = new TextDecoder(); let buf = "";
  for (;;) {
    const { value, done } = await reader.read(); if (done) break;
    buf += dec.decode(value, { stream: true });
    let i; while ((i = buf.indexOf("\n")) >= 0) { const line = buf.slice(0, i).trim(); buf = buf.slice(i + 1); if (line) { let ev; try { ev = JSON.parse(line); } catch (e) { continue; } onEvent(ev); } }
  }
}
async function send() {
  const q = $("#q").value.trim(); if (!q || S.busy) return;
  const status = $("#pipelineStatus"); status.hidden = false; status.textContent = "Waiting for the app";
  S.busy = true; sendIcon("stop", "Stop"); $("#q").value = ""; autosize(); S.lastQ = q;
  const w = $("#thread .wrap") || $("#thread");
  w.querySelector(".hero")?.remove();
  const live = el("div", { class: "a", id: "live" });
  w.append(el("div", { class: "q", text: q }), el("div", { class: "think", id: "think" }, el("span", { class: "dot" }), el("span", { class: "dot" }), el("span", { class: "dot" }), el("span", { class: "tm", id: "thinkTm", text: "0.0s" })), live);
  const t0 = Date.now(), tick = setInterval(() => { const e = $("#thinkTm"); if (e) e.textContent = ((Date.now() - t0) / 1000).toFixed(1) + "s"; else clearInterval(tick); }, 100);
  const th = $("#thread"); th.scrollTop = th.scrollHeight;
  let text = "", result = null, err = null;
  try {
    await stream({ scope: S.scope, chat: S.temp ? null : S.chat, question: q, style: $("#style").value, topic: S.topic, new_topic: S.newTopic, sources: S.sources.size ? [...S.sources] : null, temporary: S.temp, history: S.temp ? S.turns.slice(-6).map((t) => ({ question: t.question, answer: t.answer })) : undefined, use_profile: S.useProfile && !S.temp }, (ev) => {
      if (ev.type === "progress") { status.textContent = ev.data.label; }
      else if (ev.type === "token") {
        const thinking = $("#think");
        if (thinking) {
          if (motionAllowed() && thinking.animate) {
            thinking.removeAttribute("id"); thinking.style.overflow = "hidden";
            const fade = thinking.animate([{opacity:1,height:thinking.getBoundingClientRect().height+"px",padding:"4px 0"},{opacity:0,height:"0px",padding:"0px"}],{duration:120,easing:"ease-out"}); fade.onfinish = () => thinking.remove();
            live.classList.add("answer-arrive");
          } else thinking.remove();
        }
        text += ev.data; const sp = document.createElement("span"); sp.className = "tk"; sp.textContent = ev.data; const follow = th.scrollHeight - th.scrollTop - th.clientHeight < 100; live.append(sp); if (follow) th.scrollTop = th.scrollHeight; }
      else if (ev.type === "done") result = ev.data;
      else if (ev.type === "error") err = ev.data;
    });
  } catch (e) { err = e.name === "AbortError" ? "Stopped" : (e instanceof TypeError ? "Could not reach the app. Is it still running?" : e.message); }
  if (!result && !err) err = text ? "The answer was cut short" : "No answer came back";
  if (result) {
    if (!S.temp) { S.chat = result.chat; S.topic = result.topic; S.newTopic = false; }
    S.turns.push(result);
    if (Object.keys(result.source_errors || {}).length) toast("Some sources were unavailable: " + Object.keys(result.source_errors).join(", "));
    if (S.turns.length === 1 && !S.temp) $("#chatTitle").textContent = q.slice(0, 60);
  } else {
    const u = el("div", { class: "toast", onclick: () => { u.remove(); $("#q").value = q; send(); } }, (err || "Something went wrong").replace(/[.?!]+$/, "") + ". Click to retry"); centerToast(u);
    document.body.append(u); setTimeout(() => u.remove(), 7000);
  }
  status.textContent = result ? "Answer ready" : (err || "Reply interrupted"); setTimeout(() => { if (!S.busy) status.hidden = true; }, 2500);
  S.busy = false; applyIcons(); sendIcon("send", "Send"); drawThread(); loadList(); $("#q").focus();
  if (!result) {
    // keep what the user typed, and any text that did arrive, instead of losing both
    if (text && err !== "Stopped") { const w2 = $("#thread .wrap") || $("#thread"); w2.querySelector(".hero")?.remove(); w2.append(el("div", { class: "q", text: q }), el("div", { class: "a" }, text + "\n\n(Cut short. Click the notice to ask again.)")); }
    else if (!$("#q").value) { $("#q").value = q; autosize(); }
  }
}
async function uploadDialog() {
  const link = prompt("Paste a web page link to add it as a source, or press Cancel to choose files");
  if (link && link.trim()) { try { const r = await api("/api/load-url", { url: link.trim() }); toast("Added: " + r.name); } catch (e) { toast(e.message); } return; }
  const inp = el("input", { type: "file", accept: ".txt,.md,.csv,.json,.pdf,application/pdf", multiple: "" });
  inp.addEventListener("change", async () => {
    let n = 0;
    for (const f of inp.files) {
      if (/\.pdf$/i.test(f.name)) {
        if (f.size > 8e6) { toast(f.name + " is over 8 MB"); continue; }
        try {
          const bytes = new Uint8Array(await f.arrayBuffer()); let bin = ""; for (let i = 0; i < bytes.length; i += 8192) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 8192));
          await api("/api/upload-pdf", { name: f.name, data: btoa(bin) }); n++;
        } catch (e) { toast(f.name + ": " + e.message); }
        continue;
      }
      if (f.size > 150000) { toast(f.name + " is over 150 KB"); continue; }
      try { await api("/api/uploads", { name: f.name, text: await f.text() }); n++; } catch (e) { toast(e.message); }
    }
    if (n) toast(n + " file" + (n > 1 ? "s" : "") + " added. Questions can now use them.");
  });
  inp.click();
}
function contextDialog(t) {
  const m = el("div", { class: "modal-back", onclick: (e) => e.target === m && m.remove() }, el("div", { class: "modal", role: "dialog", "aria-label": "Answer context" },
    el("h2", { text: "How this answer was built" }),
    el("p", { text: "You asked: " + t.question }),
    el("p", { text: "Understood as: " + (t.standalone || t.question) }),
    el("p", { text: (t.evidence || []).length + " source" + ((t.evidence || []).length === 1 ? "" : "s") + " used" + (t.seconds !== undefined ? ", answered in " + (t.seconds < 1 ? "under 1s" : t.seconds + "s") : "") + "." }),
    el("div", { class: "modal-act" }, el("button", { class: "btn-out", onclick: () => m.remove() }, "Close"))));
  document.body.append(m);
}
async function regen(turn, style) {
  try { const r = await api("/api/regenerate", { turn, style }); S.turns.push(r); drawThread(); } catch (e) { toast(e.message); }
}
const autosize = () => { const q = $("#q"); q.style.height = "auto"; q.style.height = Math.min(q.scrollHeight, 160) + "px"; };

async function init() {
  S.cfg = await api("/api/config");
  if (S.cfg.auth === "accounts" && !PREVIEW) await accountGate();
  { const h = S.cfg.app.accent.replace("#", ""), v = [0, 2, 4].map((i) => parseInt(h.substr(i, 2), 16) / 255).map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
    const L = 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]; document.documentElement.style.setProperty("--on-accent", L > 0.5 ? "#000" : "#fff"); }
  const a = S.cfg.app; document.title = a.title;
  $("#brand").textContent = a.title; $("#sideTitle").textContent = "Conversations"; $("#noteName").textContent = a.title; $("#noteText").textContent = a.footer; $("#tempPill").addEventListener("click", () => $("#tempBtn").click()); $("#themeBtn").addEventListener("click", () => { const dark = document.documentElement.dataset.theme === "dark"; localStorage.setItem("cc_mode", dark ? "light" : "dark"); CCTheme.apply(CCTheme.value); });
  $("#modelBadge").textContent = S.cfg.provider.type + (S.cfg.provider.model ? " · " + S.cfg.provider.model : "");
  S.cfg.styles.forEach((s) => $("#style").append(el("option", { value: s === "standard" ? s : s, ...(s === "standard" ? { selected: "" } : {}) }, s[0].toUpperCase() + s.slice(1))));
  if (S.cfg.sources.length > 1) {
    const f = el("div", { class: "pills" });
    S.cfg.sources.forEach((s) => f.append(el("button", { class: "pill", onclick: (e) => { S.sources.has(s.id) ? S.sources.delete(s.id) : S.sources.add(s.id); e.target.style.opacity = S.sources.has(s.id) || !S.sources.size ? 1 : .45; [...f.children].forEach((c, i) => c.style.opacity = !S.sources.size || S.sources.has(S.cfg.sources[i].id) ? 1 : .45); } }, s.label)));
    $(".composer").prepend(f);
  }
  $("#scopeBtn").onclick=scopeDialog;
  $("#hint").textContent = "Answers cite their sources. Check important facts.";
  $("#q").addEventListener("input", autosize);
  $("#q").addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } });
  $("#exportChat").addEventListener("click", () => S.chat && S.turns.length ? download("/api/export?chat=" + S.chat, "chat.md") : toast("Nothing to export yet"));
  $("#q").addEventListener("input", rdy); $("#send").addEventListener("click", () => (S.busy ? aborter && aborter.abort() : send())); $("#newChat").addEventListener("click", newChat);
  $("#menu").addEventListener("click", () => $("#app").classList.toggle("menu-open"));
  $("#search").addEventListener("input", () => S.tab === "chats" && loadList());
  document.querySelectorAll(".tab").forEach((b) => b.addEventListener("click", () => { document.querySelectorAll(".tab").forEach((x) => x.classList.toggle("on", x === b)); S.tab = b.dataset.tab; loadList(); }));
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") $("#app").classList.remove("src", "menu-open"); });
  const th = $("#thread"), jump = $("#jump");
  th.addEventListener("scroll", () => jump.classList.toggle("show", th.scrollHeight - th.scrollTop - th.clientHeight > 240));
  jump.addEventListener("click", () => th.scrollTo({ top: th.scrollHeight, behavior: "smooth" }));
  $("#menu").replaceChildren(svg("menu")); $("#upload").replaceChildren(svg("clip")); $("#exportChat").replaceChildren(svg("tray")); $("#newTopic").replaceChildren(svg("topic")); $("#newTopic").onclick = () => { S.newTopic = true; S.topic = null; toast("Next question starts a new conversation"); }; $("#send").replaceChildren(svg("send")); $("#jump").replaceChildren(svg("down"));
  $("#upload").addEventListener("click", uploadDialog);
  document.addEventListener("keydown", (e) => { if ((e.metaKey || e.ctrlKey) && e.key === "k") { e.preventDefault(); $("#search").focus(); } });
  $("#tempBtn").replaceChildren(svg("temp")); $("#profileBtn").replaceChildren(svg("user")); $("#prevQ").replaceChildren(svg("up")); $("#nextQ").replaceChildren(svg("down"));
  $("#tempBtn").addEventListener("click", toggleTemp); $("#profileBtn").addEventListener("click", profileDialog);
  $("#prevQ").addEventListener("click", () => jumpQ(-1)); $("#nextQ").addEventListener("click", () => jumpQ(1));
  setupMic(); setupSimilar(); setupResizer();
  document.addEventListener("keydown", (e) => { const t = e.target.tagName; if (["INPUT", "TEXTAREA", "SELECT"].includes(t) || e.metaKey || e.ctrlKey || e.altKey) return; if (e.key === "j") jumpQ(1); else if (e.key === "k") jumpQ(-1); });
  applyWording(); applyIcons();
  if (PREVIEW) { previewMode(); return; }
  drawThread(); loadList(); loadSuggestions(); tour();
}
init().catch((e) => { document.body.textContent = "Could not start: " + e.message; });

document.addEventListener("keydown", (e) => {
  const t = e.target.tagName;
  if (t === "INPUT" || t === "TEXTAREA" || t === "SELECT" || e.metaKey || e.ctrlKey || e.altKey) return;
  if (e.key === "/") { e.preventDefault(); const s = document.getElementById("search"); if (s) s.focus(); }
  else if (e.key === "n") { e.preventDefault(); const b = document.getElementById("newChat"); if (b) b.click(); }
  else if (e.key === "?") { const u = document.createElement("div"); u.className = "toast"; u.textContent = "Shortcuts: / search, n new chat, Enter send, Shift+Enter new line, Esc close"; document.body.append(u); setTimeout(() => u.remove(), 5000); }
});
document.addEventListener("click", (e) => {
  const app = document.getElementById("app");
  if (app && app.classList.contains("menu-open") && !e.target.closest(".side") && !e.target.closest(".toast") && !e.target.closest("#menu")) app.classList.remove("menu-open");
});

// ---- temporary chat, profile, mic, similar questions, question navigation, resizer, tour ----
function setTemp(on) {
  S.temp = on; document.body.classList.toggle("temp", on);
  const b = $("#tempBtn"); if (b) b.setAttribute("aria-pressed", String(on)); $("#tempPill").setAttribute("aria-pressed", String(on));
}
function toggleTemp() {
  if (S.temp) { newChat(); return; }
  S.chat = null; S.topic = null; S.turns = []; setTemp(true);
  $("#chatTitle").textContent = "Temporary chat"; drawThread();
  const t = $("#thread .hero"); if (t) { t.querySelector("h1").textContent = "Temporary chat"; t.querySelector("p").textContent = "Nothing here is saved, and your profile and uploads are not used. Closing the chat clears it."; }
  $("#q").focus();
}
async function profileDialog() {
  let cur = ""; try { cur = (await api("/api/profile")).text; } catch (e) { /* ignore */ }
  const ta = el("textarea", { rows: "6", placeholder: "Optional background the answers can take into account, for example your goals or constraints. Kept on this server, never treated as evidence.", maxlength: "3000" }); ta.value = cur;
  const on = el("input", { type: "checkbox", id: "useProfile" }); on.checked = S.useProfile;
  const close = () => back.remove();
  const save = async () => { try { await api("/api/profile", { text: ta.value }); S.useProfile = on.checked && !!ta.value.trim(); localStorage.setItem("cc_profile_on", S.useProfile ? "1" : "0"); toast("Profile saved"); close(); drawThread(); } catch (e) { toast(e.message); } };
  const back = el("div", { class: "modal-back", onclick: (e) => e.target === back && close() },
    el("div", { class: "modal", role: "dialog", "aria-modal": "true", "aria-label": "My profile" },
      el("h2", { text: "My profile" }), ta,
      el("label", { class: "chk" }, on, " Use my profile in saved chats (not in temporary chats)"),
      el("div", { class: "modal-act" }, el("button", { class: "chip", onclick: close }, "Cancel"), el("button", { class: "chip on", onclick: save }, "Save"))));
  document.body.append(back); ta.focus();
}
function setupMic() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition; const m = $("#mic");
  if (!SR || !m) return;
  m.hidden = false; m.replaceChildren(svg("mic"));
  let rec = null;
  m.addEventListener("click", () => {
    if (rec) { rec.stop(); return; }
    rec = new SR(); rec.lang = (S.cfg.app.language || "en"); rec.interimResults = true; rec.continuous = false;
    const base = $("#q").value; m.classList.add("rec"); m.setAttribute("aria-label", "Stop dictation");
    rec.onresult = (e) => { let t = ""; for (const r of e.results) t += r[0].transcript; $("#q").value = (base ? base + " " : "") + t; autosize(); };
    rec.onerror = (e) => { if (e.error !== "aborted") toast("Dictation: " + e.error); };
    rec.onend = () => { rec = null; m.classList.remove("rec"); m.setAttribute("aria-label", "Dictate"); $("#q").focus(); };
    try { rec.start(); } catch (e) { rec = null; m.classList.remove("rec"); }
  });
}
let simTimer = null;
function setupSimilar() {
  $("#q").addEventListener("input", () => {
    clearTimeout(simTimer);
    const q = $("#q").value.trim(), box = $("#similar");
    if (S.temp || q.split(/\s+/).length < 3) { box.replaceChildren(); return; }
    simTimer = setTimeout(async () => {
      try {
        const r = await api("/api/similar?q=" + encodeURIComponent(q));
        box.replaceChildren(...r.map((x) => el("button", { class: "pill", title: "Open the chat where you asked this", onclick: () => { box.replaceChildren(); openChat(x.chat); } }, "Asked before: " + x.question.slice(0, 60))));
      } catch (e) { /* ignore */ }
    }, 500);
  });
}
function jumpQ(dir) {
  const qs = [...document.querySelectorAll("#thread .q")]; if (!qs.length) return;
  const th = $("#thread"), top = th.getBoundingClientRect().top + 8;
  const idx = qs.findIndex((n) => n.getBoundingClientRect().top > top + 4);
  let target = dir > 0 ? qs[idx === -1 ? qs.length - 1 : idx] : qs[(idx === -1 ? qs.length : idx) - 2] || qs[0];
  if (dir < 0 && idx === -1) target = qs[Math.max(0, qs.length - 2)];
  target.scrollIntoView({ behavior: "smooth", block: "start" });
}
function setupResizer() {
  const r = $("#resizer"), app = $("#app"); if (!r) return;
  const saved = parseInt(localStorage.getItem("cc_side") || "0", 10); if (saved) document.documentElement.style.setProperty("--side-w", saved + "px");
  r.addEventListener("pointerdown", (e) => {
    e.preventDefault(); r.setPointerCapture(e.pointerId);
    const move = (ev) => { const w = Math.min(460, Math.max(220, ev.clientX)); document.documentElement.style.setProperty("--side-w", w + "px"); localStorage.setItem("cc_side", String(w)); };
    const up = () => { r.removeEventListener("pointermove", move); r.removeEventListener("pointerup", up); };
    r.addEventListener("pointermove", move); r.addEventListener("pointerup", up);
  });
  r.addEventListener("dblclick", () => { document.documentElement.style.removeProperty("--side-w"); localStorage.removeItem("cc_side"); });
}
async function accountGate() {
  const post = (p, b) => api("/api/account/" + p, b);
  let me = await api("/api/account/me");
  while (!me.user) {
    me = await new Promise((resolve) => {
      let mode = "in";
      const back = el("div", { class: "modal-back" }), err = el("div", { class: "auth-err", role: "alert" });
      const email = el("input", { type: "email", placeholder: "Email", autocomplete: "email", "aria-label": "Email" });
      const name = el("input", { type: "text", placeholder: "Your name (optional)", autocomplete: "name", "aria-label": "Name" });
      const pw = el("input", { type: "password", placeholder: "Password (8+ characters)", autocomplete: "current-password", "aria-label": "Password" });
      const go = el("button", { class: "chip on" }, "Sign in"), sw = el("button", { class: "linkbtn", type: "button" });
      const draw = () => {
        name.hidden = mode === "in"; go.textContent = mode === "in" ? "Sign in" : "Create account";
        sw.textContent = mode === "in" ? "New here? Create an account" : "Have an account? Sign in"; sw.hidden = mode === "in" && !me.signup;
        pw.autocomplete = mode === "in" ? "current-password" : "new-password"; err.textContent = "";
      };
      const submit = async () => {
        go.disabled = true;
        try { resolve(await post(mode === "in" ? "login" : "signup", { email: email.value, name: name.value, password: pw.value }).then(() => post("me"))); back.remove(); }
        catch (e) { err.textContent = e.message; go.disabled = false; }
      };
      go.addEventListener("click", submit); pw.addEventListener("keydown", (e) => e.key === "Enter" && submit());
      sw.addEventListener("click", () => { mode = mode === "in" ? "up" : "in"; draw(); });
      back.append(el("form", { class: "modal auth", onsubmit: (e) => e.preventDefault(), role: "dialog", "aria-modal": "true", "aria-label": "Sign in" },
        el("h2", { text: S.cfg.app.title }), el("p", { class: "mut", text: "Sign in to keep your chats private to you." }), email, name, pw, err, el("div", { class: "modal-act" }, sw, go)));
      document.body.append(back); draw(); email.focus();
    });
  }
  S.user = me.user;
  const tb = $(".toolbar"), menu = el("div", { class: "acct-menu", hidden: "" });
  const btn = el("button", { class: "acct-btn", "aria-haspopup": "true", "aria-label": "Account" }, el("span", { class: "acct-dot", text: (me.user.name || "?")[0].toUpperCase() }), el("span", { text: me.user.name }));
  const item = (t, f) => el("button", { class: "acct-item", onclick: () => { menu.hidden = true; f(); } }, t);
  menu.append(el("div", { class: "acct-mail mut", text: me.user.email }),
    item("Change password", () => {
      const o = el("input", { type: "password", placeholder: "Current password", autocomplete: "current-password" }), n = el("input", { type: "password", placeholder: "New password (8+ characters)", autocomplete: "new-password" });
      const e = el("div", { class: "auth-err", role: "alert" }), back = el("div", { class: "modal-back" });
      const save = el("button", { class: "chip on", onclick: async () => { try { await post("password", { old: o.value, new: n.value }); back.remove(); toast("Password changed. Other devices were signed out."); } catch (x) { e.textContent = x.message; } } }, "Save");
      back.append(el("div", { class: "modal auth", role: "dialog", "aria-modal": "true", "aria-label": "Change password" }, el("h2", { text: "Change password" }), o, n, e, el("div", { class: "modal-act" }, el("button", { class: "chip", onclick: () => back.remove() }, "Cancel"), save)));
      document.body.append(back); o.focus();
    }),
    item("Sign out", async () => { await post("logout", {}); location.reload(); }));
  btn.addEventListener("click", (e) => { e.stopPropagation(); menu.hidden = !menu.hidden; });
  document.addEventListener("click", () => (menu.hidden = true));
  tb.insertBefore(el("div", { class: "acct" }, btn, menu), $("#themeBtn"));
}
function applyWording() {
  const a = S.cfg.app;
  { const b = $("#brand"); b.textContent = TV("txt_title") || a.title; const lg = TV("logo"); if (lg) { const im = document.createElement("img"); im.className = "tb-logo"; im.alt = ""; im.src = lg; b.prepend(im); } } document.title = TV("txt_title") || a.title;
  $("#noteName").textContent = TV("txt_title") || a.title; $("#noteText").textContent = TV("txt_footer") || a.footer;
  $("#q").placeholder = TV("txt_placeholder") || "Ask a question"; $("#hint").textContent = TV("txt_hint") || "Answers cite their sources. Check important facts.";
  const d = document.querySelector(".cmeta span:last-child"); if (d) d.textContent = TV("txt_disclaimer") || "Not a substitute for professional advice.";
  $("#sideTitle").textContent = TV("txt_sidebar") || "Chats";
}
function applyIcons() {
  for (const [id, key, name] of [["#send", "emoji_send", "send"], ["#upload", "emoji_attach", "clip"], ["#tempBtn", "emoji_temp", "temp"]]) {
    const b = $(id); if (!b) continue; const e = TV(key); if (id === "#send" && S.busy) continue; b.replaceChildren(e ? document.createTextNode(e) : svg(name));
  }
}
function pvBottom() { const t = $("#thread"); if (t) { t.style.scrollBehavior = "auto"; t.scrollTop = t.scrollHeight; } }
function previewMode() {
  document.documentElement.classList.add("preview");
  S.turns = [
    { id: "p1", chat: "p", question: "How much fiber should an adult eat each day?", answer: "What we know: adults are advised to eat about 14 g of fiber per 1,000 kcal, which works out to roughly 25 g a day for women and 38 g for men [1].\n\nWhat we don't know: the supplied sources do not say how much benefit or risk comes with eating more or less than that [1].\n\nWhat to ask a dietitian: how much fiber suits you, and which foods are the best way to reach it.", evidence: [{ n: 1, title: "Health Implications of Dietary Fiber (Academy of Nutrition and Dietetics, 2015)", text: "" }], ledger: [], seconds: 4 },
    { id: "p2", chat: "p", question: "Which foods contain iron?", answer: "Iron is found in meat, fish, beans, lentils and fortified cereals [1]. Iron from plants is absorbed less well than iron from meat, and vitamin C eaten at the same meal helps [2].", evidence: [{ n: 1, title: "Iron fact sheet for consumers", text: "" }, { n: 2, title: "Iron absorption and diet", text: "" }], ledger: [], seconds: 3 },
  ];
  S.chat = "p"; drawThread(); pvBottom(); $("#chatTitle").textContent = "Fiber and iron";
  const list = $("#list"); list.replaceChildren(...["Fiber and iron", "Protein needs", "Hydration"].map((t, i) => el("div", { class: "item" + (i ? "" : " on") }, el("span", { text: t }))));
  window.addEventListener("message", (e) => { if (e.origin === location.origin && e.data && e.data.ccTheme) { applyWording(); applyIcons(); drawThread(); pvBottom(); $("#chatTitle").textContent = "Fiber and iron"; } });
}
function tour() {
  if (localStorage.getItem("cc_tour")) return;
  const steps = [["Ask anything", "Answers are written from your sources and every claim links to the evidence."], ["Follow-ups just work", "Ask 'what about its cost?' and it remembers what you were discussing."], ["Temporary chat and profile", "Use the clock button for a chat that saves nothing. The person button holds optional background for your saved chats."]];
  let i = 0;
  const back = el("div", { class: "modal-back" });
  const draw = () => {
    const [h, p] = steps[i];
    back.replaceChildren(el("div", { class: "modal", role: "dialog", "aria-modal": "true", "aria-label": "Quick tour" },
      el("div", { class: "mut", text: (i + 1) + " of " + steps.length }), el("h2", { text: h }), el("p", { text: p }),
      el("div", { class: "modal-act" }, el("button", { class: "chip", onclick: done }, "Skip"), el("button", { class: "chip on", onclick: () => (++i < steps.length ? draw() : done()) }, i + 1 < steps.length ? "Next" : "Done"))));
  };
  const done = () => { localStorage.setItem("cc_tour", "1"); back.remove(); $("#q").focus(); };
  document.body.append(back); draw();
}
})();

document.getElementById("sideClose")?.addEventListener("click", () => document.getElementById("app").classList.remove("menu-open"));
(() => { const c = document.querySelector(".composer"); if (!c) return; const set = () => document.documentElement.style.setProperty("--composer-h", Math.ceil(c.getBoundingClientRect().height + (window.innerHeight - c.getBoundingClientRect().bottom)) + "px"); set(); window.addEventListener("resize", set); if (window.ResizeObserver) new ResizeObserver(set).observe(c); })();

(function () { const q = document.getElementById("q"), sb = document.getElementById("send"); if (!q || !sb) return; const upd = () => sb.classList.toggle("idle", !q.value.trim() && sb.getAttribute("aria-label") === "Send"); q.addEventListener("input", upd); setInterval(upd, 400); upd(); })();

// if saving is not possible (disk full, read-only folder) the server keeps answering; say so once
try { fetch("/api/health").then((r) => r.json()).then((h) => { if (h && h.degraded && typeof toast === "function") toast(h.degraded); }).catch(() => {}); } catch (e) { /* notice only */ }
