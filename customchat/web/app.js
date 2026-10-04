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
const S = { cfg: null, chat: null, topic: null, newTopic: false, tab: "chats", sources: new Set(), turns: [], busy: false, token: localStorage.getItem("cc_token") || "" };

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

function showSources(evidence, hl) {
  const pane = $("#sources"); pane.replaceChildren();
  $("#app").classList.add("src");
  const types = [...new Set(evidence.map((e) => e.source))];
  const filters = el("div", { class: "filters" });
  const list = el("div");
  const draw = (only) => {
    list.replaceChildren(...evidence.filter((e) => !only || e.source === only).map((e) => el("div", { class: "src" + (e.n === hl ? " hl" : "") },
      el("b", { text: e.n + ". " + e.title }),
      el("small", { text: [e.authors.slice(0, 3).join(", "), e.year, e.venue].filter(Boolean).join(" · ") }),
      el("p", { text: e.text }),
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
  const unsupported = (t.ledger || []).filter((l) => !l.supported).length;
  if (t.evidence.length && unsupported) meta.append(el("span", { class: "chip warn", title: "Sentences without a valid citation" }, unsupported + " uncited"));
  if (t.standalone && t.standalone !== t.question) meta.append(el("span", { class: "chip", title: "Understood as" }, "Understood as: " + t.standalone));
  if (t.evidence.length) {
    meta.append(el("button", { class: "chip", onclick: () => navigator.clipboard.writeText(t.answer).then(() => toast("Copied")) }, "Copy"));
    meta.append(el("button", { class: "chip", onclick: () => download("/api/bibtex?turn=" + t.id, "references.bib") }, "BibTeX"));
    meta.append(el("button", { class: "chip", onclick: () => download("/api/pdf?turn=" + t.id, "answer.pdf") }, "PDF"));
    for (const s of ["quick", "deep"]) if (S.cfg.styles.includes(s)) meta.append(el("button", { class: "chip", onclick: () => regen(t.id, s) }, s === "quick" ? "Shorter" : "Deeper"));
  }
  nodes.push(meta);
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

async function loadList() {
  const list = $("#list"); list.replaceChildren();
  try {
    if (S.tab === "chats") {
      const rows = await api("/api/chats?q=" + encodeURIComponent($("#search").value));
      if (!rows.length) list.append(el("div", { class: "empty", text: "No chats yet." }));
      rows.forEach((c) => list.append(el("div", { class: "item" + (c.id === S.chat ? " on" : ""), onclick: () => openChat(c.id) },
        el("span", { class: "t", text: (c.pinned ? "📌 " : "") + c.title }),
        el("span", { class: "acts" },
          el("button", { title: c.pinned ? "Unpin" : "Pin", onclick: async (e) => { e.stopPropagation(); await api("/api/pin", { chat: c.id, pinned: !c.pinned }); loadList(); } }, "📌"),
          el("button", { title: "Rename", onclick: async (e) => { e.stopPropagation(); const t = prompt("Rename chat", c.title); if (t) { await api("/api/rename", { chat: c.id, title: t }); loadList(); } } }, "✎"),
          el("button", { title: "Delete", onclick: async (e) => { e.stopPropagation(); await api("/api/delete", { chat: c.id }); if (S.chat === c.id) newChat(); loadList(); const u = el("div", { class: "toast", onclick: async () => { await api("/api/restore", { chat: c.id }); loadList(); u.remove(); } }, "Deleted. Click to undo"); document.body.append(u); setTimeout(() => u.remove(), 6000); } }, "🗑")))));
    } else {
      const rows = await api("/api/topics");
      if (!rows.length) list.append(el("div", { class: "empty", text: "Conversations appear after your first question." }));
      rows.forEach((t) => list.append(el("div", { class: "item" + (t.id === S.topic ? " on" : ""), onclick: () => openTopic(t.id) },
        el("span", { class: "t" }, t.title, el("span", { class: "sub", text: t.turns + " question" + (t.turns === 1 ? "" : "s") })),
        el("span", { class: "acts" }, el("button", { title: "Rename", onclick: async (e) => { e.stopPropagation(); const n = prompt("Rename conversation", t.title); if (n) { await api("/api/rename-topic", { topic: t.id, title: n }); loadList(); } } }, "✎")))));
    }
  } catch (e) { list.append(el("div", { class: "empty", text: e.message })); }
}

async function openChat(id) {
  S.chat = id; S.newTopic = false;
  S.turns = await api("/api/turns?chat=" + id);
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

async function send() {
  const q = $("#q").value.trim(); if (!q || S.busy) return;
  S.busy = true; $("#send").disabled = true; $("#q").value = ""; autosize();
  const w = $("#thread .wrap") || $("#thread");
  w.querySelector(".hero")?.remove();
  w.append(el("div", { class: "q", text: q }), el("div", { class: "think", id: "think" }, el("span", { class: "dot" }), el("span", { class: "dot" }), el("span", { class: "dot" })));
  $("#thread").scrollTop = $("#thread").scrollHeight;
  try {
    const r = await api("/api/ask", { chat: S.chat, question: q, style: $("#style").value, topic: S.topic, new_topic: S.newTopic, sources: [...S.sources].length ? [...S.sources] : null });
    S.chat = r.chat; S.topic = r.topic; S.newTopic = false;
    S.turns.push({ ...r, id: r.id });
    if (Object.keys(r.source_errors || {}).length) toast("Some sources were unavailable: " + Object.keys(r.source_errors).join(", "));
  } catch (e) { toast(e.message); S.turns = S.turns.slice(); }
  S.busy = false; $("#send").disabled = false; drawThread(); loadList();
  if (S.turns.length === 1) $("#chatTitle").textContent = q.slice(0, 60);
}
async function regen(turn, style) {
  try { const r = await api("/api/regenerate", { turn, style }); S.turns.push(r); drawThread(); } catch (e) { toast(e.message); }
}
const autosize = () => { const q = $("#q"); q.style.height = "auto"; q.style.height = Math.min(q.scrollHeight, 160) + "px"; };

async function init() {
  S.cfg = await api("/api/config");
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
  $("#send").addEventListener("click", send); $("#newChat").addEventListener("click", newChat);
  $("#menu").addEventListener("click", () => $("#app").classList.toggle("menu-open"));
  $("#search").addEventListener("input", () => S.tab === "chats" && loadList());
  document.querySelectorAll(".tab").forEach((b) => b.addEventListener("click", () => { document.querySelectorAll(".tab").forEach((x) => x.classList.toggle("on", x === b)); S.tab = b.dataset.tab; loadList(); }));
  document.addEventListener("keydown", (e) => { if ((e.metaKey || e.ctrlKey) && e.key === "k") { e.preventDefault(); $("#search").focus(); } });
  drawThread(); loadList();
}
init().catch((e) => { document.body.textContent = "Could not start: " + e.message; });
})();
