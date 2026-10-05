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
  send: "M12 19V5M5 12l7-7 7 7",
  stop: "M7 7h10v10H7z",
};
const svg = (n) => { const e = document.createElementNS("http://www.w3.org/2000/svg", "svg"); e.setAttribute("viewBox", "0 0 24 24"); e.setAttribute("width", "18"); e.setAttribute("height", "18"); e.setAttribute("fill", "none"); e.setAttribute("stroke", "currentColor"); e.setAttribute("stroke-width", "2"); e.setAttribute("stroke-linecap", "round"); e.setAttribute("stroke-linejoin", "round"); const p = document.createElementNS("http://www.w3.org/2000/svg", "path"); p.setAttribute("d", ICON[n]); e.append(p); return e; };
const S = { cfg: null, chat: null, topic: null, newTopic: false, tab: "chats", sources: new Set(), turns: [], ratings: {}, busy: false, token: localStorage.getItem("cc_token") || "" };

async function api(path, body) {
  const h = { "Content-Type": "application/json" };
  if (S.token) h.Authorization = "Bearer " + S.token;
  const r = await fetch(path, body === undefined ? { headers: h } : { method: "POST", headers: h, body: JSON.stringify(body) });
  const d = await r.json().catch(() => ({}));
  if (r.status === 401 && S.cfg && S.cfg.auth === "token") {
    const t = prompt("Access token"); if (t) { S.token = t; localStorage.setItem("cc_token", t); return api(path, body); }
  }
  if (!r.ok) throw new Error(d.error || "Request failed");
  return d;
}
function toast(msg) { const t = el("div", { class: "toast", text: msg }); document.body.append(t); setTimeout(() => t.remove(), 2200); }

function inline(parent, text, evidence) {
  // safe inline markdown: **bold**, `code`, and [n] citations. Everything is text nodes.
  text.split(/(\*\*[^*]+\*\*|`[^`]+`|\[\d+\])/).forEach((p) => {
    let m;
    if ((m = p.match(/^\[(\d+)\]$/)) && evidence.some((e) => e.n === +m[1])) parent.append(el("button", { class: "cite", title: "Show source " + m[1], onclick: () => showSources(evidence, +m[1]) }, "[" + m[1] + "]"));
    else if (/^\*\*[^*]+\*\*$/.test(p)) parent.append(el("strong", { text: p.slice(2, -2) }));
    else if (/^`[^`]+`$/.test(p)) parent.append(el("code", { text: p.slice(1, -1) }));
    else if (p) parent.append(document.createTextNode(p));
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
function showSources(evidence, hl) {
  const terms = [...new Set(((S.turns[S.turns.length - 1] || {}).standalone || "").toLowerCase().match(/[a-z0-9]{4,}/g) || [])].slice(0, 8);
  const pane = $("#sources"); pane.replaceChildren();
  $("#app").classList.add("src");
  const types = [...new Set(evidence.map((e) => e.source))];
  const filters = el("div", { class: "filters" });
  const list = el("div");
  const draw = (only) => {
    list.replaceChildren(...evidence.filter((e) => !only || e.source === only).map((e) => el("div", { class: "src" + (e.n === hl ? " hl" : "") },
      el("b", { text: e.n + ". " + e.title }),
      el("small", { text: [e.authors.slice(0, 3).join(", "), e.year, e.venue].filter(Boolean).join(" · ") }),
      highlight(el("p"), e.text, terms),
      e.url ? el("a", { href: e.url, target: "_blank", rel: "noopener noreferrer", text: "Open source" }) : null)));
  };
  if (types.length > 1) types.forEach((t) => filters.append(el("button", { class: "chip", onclick: (ev) => {
    const on = ev.target.classList.toggle("on"); filters.querySelectorAll(".chip").forEach((c) => c !== ev.target && c.classList.remove("on")); draw(on ? t : null);
  } }, (S.cfg.sources.find((s) => s.id === t) || {}).label || t)));
  pane.append(el("button", { class: "icon", style: "float:right", "aria-label": "Close", onclick: () => $("#app").classList.remove("src") }, "✕"),
    el("h3", { text: "Sources" }), el("div", { class: "sub", text: evidence.length + " used for this answer" }), filters, list);
  draw(null);
  if (hl) setTimeout(() => list.querySelector(".hl")?.scrollIntoView({ block: "center" }), 50);
}

function turnView(t, prev) {
  const nodes = [];
  if (prev && prev.chat !== t.chat) nodes.push(el("div", { class: "divider", text: "Earlier chat" }));
  nodes.push(el("div", { class: "q", text: t.question }));
  nodes.push(renderAnswer(t.answer, t.evidence));
  const meta = el("div", { class: "meta" });
  if (t.evidence.length) meta.append(el("button", { class: "chip", onclick: () => showSources(t.evidence) }, t.evidence.length + " sources"));
  const weak = (t.ledger || []).filter((l) => !l.supported || (l.overlap !== undefined && l.overlap < 0.35));
  if (t.evidence.length && weak.length) meta.append(el("button", { class: "chip warn", title: "Sentences without a valid citation or with little overlap with the cited text. Click to see them.", onclick: () => alert("Check these sentences:\n\n" + weak.map((l) => "- " + l.claim).join("\n")) }, weak.length + " to check"));
  if (t.seconds !== undefined) meta.append(el("span", { class: "chip", title: "Time to answer" }, t.seconds < 1 ? "<1s" : t.seconds + "s"));
  if (t.standalone && t.standalone !== t.question) meta.append(el("span", { class: "chip", title: "Understood as" }, "Understood as: " + t.standalone));
  if (t.evidence.length) {
    meta.append(el("button", { class: "chip", onclick: () => navigator.clipboard.writeText(t.answer).then(() => toast("Copied")) }, "Copy"));
    for (const v of [1, -1]) meta.append(el("button", { class: "chip" + (S.ratings[t.id] === v ? " on" : ""), "aria-pressed": String(S.ratings[t.id] === v), onclick: async () => { const r = S.ratings[t.id] === v ? 0 : v; try { await api("/api/rate", { turn: t.id, rating: r }); if (r) S.ratings[t.id] = r; else delete S.ratings[t.id]; drawThread(); } catch (e) { toast(e.message); } } }, v > 0 ? "Helpful" : "Not helpful"));
    meta.append(el("button", { class: "chip", onclick: () => download("/api/bibtex?turn=" + t.id, "references.bib") }, "BibTeX"));
    meta.append(el("button", { class: "chip", onclick: () => download("/api/pdf?turn=" + t.id, "answer.pdf") }, "PDF"));
    for (const s of ["quick", "deep"]) if (S.cfg.styles.includes(s)) meta.append(el("button", { class: "chip", onclick: () => regen(t.id, s) }, s === "quick" ? "Shorter" : "Deeper"));
  }
  nodes.push(meta);
  if (t.followups && t.followups.length) {
    const f = el("div", { class: "meta fu" });
    t.followups.forEach((x) => f.append(el("button", { class: "chip", onclick: () => { $("#q").value = x; send(); } }, x)));
    nodes.push(el("div", { class: "fu-label", text: "Related" }), f);
  }
  nodes.push(el("button", { class: "chip del", title: "Delete this answer", onclick: async () => {
    await api("/api/delete-turn", { turn: t.id }); S.turns = S.turns.filter((x) => x.id !== t.id); drawThread();
    const u = el("div", { class: "toast", onclick: async () => { await api("/api/restore-turn", { turn: t.id }); S.turns = await api("/api/turns?chat=" + S.chat); drawThread(); u.remove(); } }, "Answer deleted. Click to undo");
    document.body.append(u); setTimeout(() => u.remove(), 6000); } }, "Delete"));
  return nodes;
}
async function download(path, name) {
  const h = S.token ? { Authorization: "Bearer " + S.token } : {};
  const r = await fetch(path, { headers: h }); if (!r.ok) return toast("Download failed");
  const a = el("a", { href: URL.createObjectURL(await r.blob()), download: name }); a.click();
}

function drawThread() {
  const th = $("#thread"); th.replaceChildren();
  const w = el("div", { class: "wrap" });
  if (!S.turns.length) {
    const a = S.cfg.app;
    w.append(el("div", { class: "hero" }, el("h1", { text: a.title }), el("p", { text: a.tagline }),
      el("div", { class: "ex" }, a.examples.map((x) => el("button", { onclick: () => { $("#q").value = x; send(); } }, x)))));
  } else S.turns.forEach((t, i) => w.append(...turnView(t, S.turns[i - 1])));
  th.append(w); th.scrollTop = th.scrollHeight;
  $("#pills").replaceChildren(...(S.turns.length ? [el("button", { class: "pill", title: "Start a new conversation topic in this chat", onclick: () => { S.newTopic = true; S.topic = null; toast("Next question starts a new conversation"); } }, "New conversation")] : []));
}

function dayLabel(ts) {
  const d = new Date(ts * 1000), n = new Date(), day = 86400000, start = new Date(n.getFullYear(), n.getMonth(), n.getDate()).getTime();
  if (d.getTime() >= start) return "Today"; if (d.getTime() >= start - day) return "Yesterday"; if (d.getTime() >= start - 7 * day) return "This week"; return "Earlier";
}
async function loadList() {
  const list = $("#list"); list.replaceChildren();
  try {
    if (S.tab === "chats") {
      const rows = await api("/api/chats?q=" + encodeURIComponent($("#search").value));
      if (!rows.length) list.append(el("div", { class: "empty", text: "No chats yet." }));
      let lastGroup = "";
      rows.forEach((c) => { const g = c.pinned ? "Pinned" : dayLabel(c.created); if (g !== lastGroup) { list.append(el("div", { class: "group", text: g })); lastGroup = g; } list.append(el("div", { class: "item" + (c.id === S.chat ? " on" : ""), onclick: () => openChat(c.id) },
        el("span", { class: "t", text: c.title }), c.pinned ? el("span", { class: "pinned", title: "Pinned" }, svg("pin")) : null,
        el("span", { class: "acts" },
          el("button", { title: c.pinned ? "Unpin" : "Pin", onclick: async (e) => { e.stopPropagation(); await api("/api/pin", { chat: c.id, pinned: !c.pinned }); loadList(); } }, svg("pin")),
          el("button", { title: "Rename", onclick: async (e) => { e.stopPropagation(); const t = prompt("Rename chat", c.title); if (t) { await api("/api/rename", { chat: c.id, title: t }); loadList(); } } }, svg("edit")),
          el("button", { title: "Delete", onclick: async (e) => { e.stopPropagation(); await api("/api/delete", { chat: c.id }); if (S.chat === c.id) newChat(); loadList(); const u = el("div", { class: "toast", onclick: async () => { await api("/api/restore", { chat: c.id }); loadList(); u.remove(); } }, "Deleted. Click to undo"); document.body.append(u); setTimeout(() => u.remove(), 6000); } }, svg("trash"))))); });
    } else {
      const rows = await api("/api/topics");
      if (!rows.length) list.append(el("div", { class: "empty", text: "Conversations appear after your first question." }));
      rows.forEach((t) => list.append(el("div", { class: "item" + (t.id === S.topic ? " on" : ""), onclick: () => openTopic(t.id) },
        el("span", { class: "t" }, t.title, el("span", { class: "sub", text: (t.summary ? t.summary.slice(0, 70) : t.turns + " question" + (t.turns === 1 ? "" : "s")) })),
        el("span", { class: "acts" }, el("button", { title: "Rename", onclick: async (e) => { e.stopPropagation(); const n = prompt("Rename conversation", t.title); if (n) { await api("/api/rename-topic", { topic: t.id, title: n }); loadList(); } } }, svg("edit"))))));
    }
  } catch (e) { list.append(el("div", { class: "empty", text: e.message })); }
}

async function openChat(id) {
  S.chat = id; S.newTopic = false;
  S.turns = await api("/api/turns?chat=" + id);
  try { S.ratings = await api("/api/ratings?chat=" + id); } catch (e) { S.ratings = {}; }
  S.topic = S.turns.length ? S.turns[S.turns.length - 1].topic : null;
  $("#chatTitle").textContent = (await api("/api/chats")).find((c) => c.id === id)?.title || "Chat";
  $("#app").classList.remove("menu-open", "src"); drawThread(); loadList();
}
async function openTopic(id) {
  S.topic = id; S.newTopic = false;
  if (!S.chat) S.chat = (await api("/api/chats", {})).id;
  S.turns = await api("/api/topic-turns?topic=" + id);
  $("#chatTitle").textContent = "Conversation"; $("#app").classList.remove("menu-open"); drawThread();
}
function newChat() { S.chat = null; S.topic = null; S.newTopic = false; S.turns = []; $("#chatTitle").textContent = "New chat"; $("#app").classList.remove("src"); drawThread(); $("#q").focus(); }

let aborter = null;
async function stream(body, onEvent) {
  aborter = new AbortController();
  const h = { "Content-Type": "application/json" };
  if (S.token) h.Authorization = "Bearer " + S.token;
  const r = await fetch("/api/ask-stream", { method: "POST", headers: h, body: JSON.stringify(body), signal: aborter.signal });
  if (!r.ok) { const d = await r.json().catch(() => ({})); throw new Error(d.error || "Request failed"); }
  const reader = r.body.getReader(), dec = new TextDecoder(); let buf = "";
  for (;;) {
    const { value, done } = await reader.read(); if (done) break;
    buf += dec.decode(value, { stream: true });
    let i; while ((i = buf.indexOf("\n")) >= 0) { const line = buf.slice(0, i).trim(); buf = buf.slice(i + 1); if (line) onEvent(JSON.parse(line)); }
  }
}
async function send() {
  const q = $("#q").value.trim(); if (!q || S.busy) return;
  S.busy = true; $("#send").replaceChildren(svg("stop")); $("#send").setAttribute("aria-label", "Stop"); $("#q").value = ""; autosize(); S.lastQ = q;
  const w = $("#thread .wrap") || $("#thread");
  w.querySelector(".hero")?.remove();
  const live = el("div", { class: "a", id: "live" });
  w.append(el("div", { class: "q", text: q }), el("div", { class: "think", id: "think" }, el("span", { class: "dot" }), el("span", { class: "dot" }), el("span", { class: "dot" })), live);
  const th = $("#thread"); th.scrollTop = th.scrollHeight;
  let text = "", result = null, err = null;
  try {
    await stream({ chat: S.chat, question: q, style: $("#style").value, topic: S.topic, new_topic: S.newTopic, sources: S.sources.size ? [...S.sources] : null }, (ev) => {
      if (ev.type === "token") { $("#think")?.remove(); text += ev.data; live.textContent = text; th.scrollTop = th.scrollHeight; }
      else if (ev.type === "done") result = ev.data;
      else if (ev.type === "error") err = ev.data;
    });
  } catch (e) { err = e.name === "AbortError" ? "Stopped" : e.message; }
  if (result) {
    S.chat = result.chat; S.topic = result.topic; S.newTopic = false; S.turns.push(result);
    if (Object.keys(result.source_errors || {}).length) toast("Some sources were unavailable: " + Object.keys(result.source_errors).join(", "));
    if (S.turns.length === 1) $("#chatTitle").textContent = q.slice(0, 60);
  } else {
    const u = el("div", { class: "toast", onclick: () => { u.remove(); $("#q").value = q; send(); } }, (err || "Something went wrong") + ". Click to retry");
    document.body.append(u); setTimeout(() => u.remove(), 7000);
  }
  S.busy = false; $("#send").replaceChildren(svg("send")); $("#send").setAttribute("aria-label", "Send"); drawThread(); loadList(); $("#q").focus();
}
async function uploadDialog() {
  const inp = el("input", { type: "file", accept: ".txt,.md,.csv,.json", multiple: "" });
  inp.addEventListener("change", async () => {
    let n = 0;
    for (const f of inp.files) {
      if (f.size > 150000) { toast(f.name + " is over 150 KB"); continue; }
      try { await api("/api/uploads", { name: f.name, text: await f.text() }); n++; } catch (e) { toast(e.message); }
    }
    if (n) toast(n + " file" + (n > 1 ? "s" : "") + " added. Questions can now use them.");
  });
  inp.click();
}
async function regen(turn, style) {
  try { const r = await api("/api/regenerate", { turn, style }); S.turns.push(r); drawThread(); } catch (e) { toast(e.message); }
}
const autosize = () => { const q = $("#q"); q.style.height = "auto"; q.style.height = Math.min(q.scrollHeight, 160) + "px"; };

async function init() {
  S.cfg = await api("/api/config");
  { const h = S.cfg.app.accent.replace("#", ""), v = [0, 2, 4].map((i) => parseInt(h.substr(i, 2), 16) / 255).map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
    const L = 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]; document.documentElement.style.setProperty("--on-accent", L > 0.5 ? "#000" : "#fff"); }
  const a = S.cfg.app; document.title = a.title;
  $("#brand").textContent = a.title; $("#foot").textContent = a.footer;
  $("#modelBadge").textContent = S.cfg.provider.type + (S.cfg.provider.model ? " · " + S.cfg.provider.model : "");
  S.cfg.styles.forEach((s) => $("#style").append(el("option", { value: s === "standard" ? s : s, ...(s === "standard" ? { selected: "" } : {}) }, s[0].toUpperCase() + s.slice(1))));
  if (S.cfg.sources.length > 1) {
    const f = el("div", { class: "pills" });
    S.cfg.sources.forEach((s) => f.append(el("button", { class: "pill", onclick: (e) => { S.sources.has(s.id) ? S.sources.delete(s.id) : S.sources.add(s.id); e.target.style.opacity = S.sources.has(s.id) || !S.sources.size ? 1 : .45; [...f.children].forEach((c, i) => c.style.opacity = !S.sources.size || S.sources.has(S.cfg.sources[i].id) ? 1 : .45); } }, s.label)));
    $(".composer").prepend(f);
  }
  $("#hint").textContent = "Answers cite their sources. Check important facts.";
  $("#q").addEventListener("input", autosize);
  $("#q").addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } });
  $("#exportChat").addEventListener("click", () => S.chat && S.turns.length ? download("/api/export?chat=" + S.chat, "chat.md") : toast("Nothing to export yet"));
  $("#send").addEventListener("click", () => (S.busy ? aborter && aborter.abort() : send())); $("#newChat").addEventListener("click", newChat);
  $("#menu").addEventListener("click", () => $("#app").classList.toggle("menu-open"));
  $("#search").addEventListener("input", () => S.tab === "chats" && loadList());
  document.querySelectorAll(".tab").forEach((b) => b.addEventListener("click", () => { document.querySelectorAll(".tab").forEach((x) => x.classList.toggle("on", x === b)); S.tab = b.dataset.tab; loadList(); }));
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") $("#app").classList.remove("src", "menu-open"); });
  const th = $("#thread"), jump = $("#jump");
  th.addEventListener("scroll", () => jump.classList.toggle("show", th.scrollHeight - th.scrollTop - th.clientHeight > 240));
  jump.addEventListener("click", () => th.scrollTo({ top: th.scrollHeight, behavior: "smooth" }));
  $("#upload").replaceChildren(svg("clip")); $("#exportChat").replaceChildren(svg("down")); $("#send").replaceChildren(svg("send")); $("#jump").replaceChildren(svg("down"));
  $("#upload").addEventListener("click", uploadDialog);
  document.addEventListener("keydown", (e) => { if ((e.metaKey || e.ctrlKey) && e.key === "k") { e.preventDefault(); $("#search").focus(); } });
  drawThread(); loadList();
}
init().catch((e) => { document.body.textContent = "Could not start: " + e.message; });
})();

document.addEventListener("keydown", (e) => {
  const t = e.target.tagName;
  if (t === "INPUT" || t === "TEXTAREA" || t === "SELECT" || e.metaKey || e.ctrlKey || e.altKey) return;
  if (e.key === "/") { e.preventDefault(); const s = document.getElementById("search"); if (s) s.focus(); }
  else if (e.key === "n") { e.preventDefault(); const b = document.getElementById("newChat"); if (b) b.click(); }
  else if (e.key === "?") { const u = document.createElement("div"); u.className = "toast"; u.textContent = "Shortcuts: / search, n new chat, Enter send, Shift+Enter new line, Esc close"; document.body.append(u); setTimeout(() => u.remove(), 5000); }
});
