(() => {
"use strict";
const $ = (s) => document.querySelector(s);
const NAMES = { mock: "Demo", ollama: "Ollama", openai: "OpenAI", claude: "Claude", gemini: "Gemini", openai_compatible: "Other", minimax: "MiniMax", mimo: "Xiaomi MiMo", deepseek: "DeepSeek", groq: "Groq", openrouter: "OpenRouter", mistral: "Mistral" };
let cur = {}, canEdit = false, theme = null, saved = null, meta = null, editMode = "light";
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
  $("#tv").textContent = (+cur.temperature).toFixed(2); $("#kv").textContent = cur.top_k;
  document.querySelectorAll("#seg button").forEach((b) => b.setAttribute("aria-checked", String(b.dataset.p === cur.provider)));
  buildChips();
  provExtras();
  for (const id of ["model", "apikey", "keysave", "keyclear", "modelPick", "refreshModels", "testconn", "base", "temp", "topk", "rewrite", "apply", "load", "saveLook", "resetAll", "imp"]) $("#" + id).disabled = !canEdit;
}
const read = () => ({ provider: cur.provider, model: chosenModel(), base_url: $("#base").value.trim(), temperature: +$("#temp").value, top_k: +$("#topk").value, query_rewrite: $("#rewrite").checked });
/* ---------- key, model picker, connection test ---------- */
let keyInfo = {}, modelNote = "";
const OTHER = "__other__";
async function provExtras() {
  const p = cur.provider, k = keyInfo[p] || { needed: false, has: true };
  $("#keybox").hidden = p === "mock" || p === "ollama";
  $("#keyh").textContent = p === "openai_compatible" ? "Only if your server asks for one. Stored on this computer only, never shown again." : "Stored on this computer only, never shown again.";
  const ks = $("#keystate"); ks.className = "keystate" + (k.has ? " ok" : "");
  ks.textContent = k.has ? (k.source === "env" ? "Key found in an environment variable." : "A key is saved.") : (k.needed ? "No key yet." : "");
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
  const typed = sel.value === OTHER; $("#model").hidden = !typed; if (typed) $("#model").value = m;
  $("#modelh").textContent = list.length ? list.length + " models found." : (modelNote || "Type the model name your provider uses.");
}
function pickChanged() { const v = $("#modelPick").value; const typed = v === OTHER; $("#model").hidden = !typed; if (!typed) { $("#model").value = v; cur.model = v; } }
const chosenModel = () => ($("#modelPick").value === OTHER ? $("#model").value.trim() : $("#modelPick").value);
const BRAND = { openai: ["#10a37f", "O"], claude: ["#d97757", "C"], gemini: ["#4285f4", "G"], ollama: ["#2b2b2b", "Ol"], deepseek: ["#4d6bfe", "D"], groq: ["#f55036", "Gq"], mistral: ["#fa520f", "M"], minimax: ["#e0245e", "Mx"], mimo: ["#ff6900", "Mi"], openrouter: ["#6467f2", "Or"], mock: ["#8a94a3", "\u2022"], openai_compatible: ["#5b6b7f", "+"] };
const TOP = ["openai", "claude", "gemini", "deepseek", "ollama"];
let chipsMore = false, chipList = [];
function mark(p) { const b = BRAND[p] || ["#667", (NAMES[p] || p)[0]]; return el("span", { class: "pm", style: "background:" + (p === "gemini" ? "linear-gradient(135deg,#4285f4,#9b72cb 60%,#d96570)" : b[0]), "aria-hidden": "true", text: b[1] }); }
function buildChips(list) {
  if (list) chipList = list; const seg = $("#seg"); seg.replaceChildren();
  const top = TOP.filter((p) => chipList.includes(p)), rest = chipList.filter((p) => !top.includes(p));
  if (rest.includes(cur.provider)) chipsMore = true;
  for (const p of top.concat(chipsMore ? rest : [])) { const b = el("button", { type: "button", "data-p": p, role: "radio", "aria-checked": String(p === cur.provider) }, mark(p), NAMES[p] || p); b.addEventListener("click", () => { if (canEdit) { cur = { ...read(), provider: p, model: "" }; draw(); } }); seg.append(b); }
  if (rest.length) { const m = el("button", { type: "button", class: "chipmore" }, chipsMore ? "Show fewer" : "Load more"); m.addEventListener("click", () => { chipsMore = !chipsMore; buildChips(); }); seg.append(m); }
}
/* ---------- local model suggestions (Ollama) ---------- */
let hwView = "simple";
async function ollamaPanel() {
  const box = $("#ollamabox"); box.hidden = cur.provider !== "ollama"; if (box.hidden) return;
  box.replaceChildren(el("div", { class: "h", text: "Looking at this computer..." }));
  let r; try { r = await api("/api/hardware?base_url=" + encodeURIComponent($("#base").value.trim())); } catch (e) { box.replaceChildren(el("div", { class: "h", text: e.message })); return; }
  const hw = r.hardware, rec = r.recommendation;
  const tabs = el("div", { class: "seg mini", role: "radiogroup", "aria-label": "View" });
  for (const [v, t] of [["simple", "Simple"], ["tech", "Technical"]]) tabs.append(el("button", { type: "button", role: "radio", "aria-checked": String(hwView === v), onclick: () => { hwView = v; ollamaPanel(); } }, t));
  const head = el("div", { class: "ohead" }, el("b", { text: "Best models for this computer" }), tabs);
  const cards = el("div", { class: "ocards" });
  if (!rec.picks.length) cards.append(el("div", { class: "h", text: rec.note || "No suggestion available." }));
  rec.picks.forEach((p, i) => {
    const c = el("div", { class: "ocard" }, el("div", { class: "otag", text: p.label }), el("b", { text: p.name }), el("div", { class: "h", text: p.note }),
      el("div", { class: "ometa", text: "About " + p.download_gb + " GB download. Speed: " + p.speed + "." }));
    if (hwView === "tech") c.append(el("div", { class: "otech", text: p.tag + " | needs about " + p.needs_gb + " GB (" + p.uses_pct + "% of the " + rec.budget_gb + " GB budget) | " + p.params_b + "B parameters, 4-bit" }));
    const act = el("div", { class: "oact" });
    if (p.installed) act.append(el("span", { class: "ok", text: "Installed" }), el("button", { type: "button", class: "mini", onclick: () => { cur.model = p.tag; loadModels(true).then(() => { $("#modelPick").value = p.tag; pickChanged(); }); } }, "Use this model"));
    else act.append(el("code", { text: p.pull }), el("button", { type: "button", class: "mini", onclick: () => { navigator.clipboard && navigator.clipboard.writeText(p.pull); say("Copied. Run it in a terminal, then press Refresh list."); } }, "Copy command"));
    c.append(act); cards.append(c);
  });
  box.replaceChildren(head, cards);
  if (hwView === "tech") box.append(el("pre", { class: "otechbox", text: ["Computer: " + hw.os + " " + hw.arch + ", " + hw.cores + " CPU cores, " + hw.ram_gb + " GB RAM", "GPU: " + (hw.gpu ? hw.gpu + " (" + hw.vram_gb + " GB video memory)" : (hw.apple_silicon ? "Apple Silicon (shared memory)" : "none found")), "Ollama: " + (r.ollama_running ? "running, " + (r.installed || []).length + " models installed" : "not reachable at the Base URL"), "", "Memory budget: " + rec.budget_gb + " GB. " + rec.budget_why, "A model must fit in 85% of that (" + rec.limit_gb + " GB), counting its file size plus about 1.5 GB for the conversation.", "Picks: largest that fits, largest using at most 60%, largest using at most 30%."].join("\n") }));
  else box.append(el("div", { class: "h", text: "Based on " + hw.ram_gb + " GB of memory" + (hw.gpu ? " and your " + hw.gpu : "") + ". Switch to Technical to see the math." }));
  if (rec.note && rec.picks.length) box.append(el("div", { class: "h", text: rec.note }));
}
async function states() {
  const s = (await api("/api/states")).states; const sel = $("#states"); sel.replaceChildren();
  sel.append(el("option", { value: "", text: "Select a state..." })); s.forEach((n) => sel.append(el("option", { value: n, text: n })));
}

/* ---------- look: every setting, with a plain explanation ---------- */
const C = (k, label, help) => ({ key: k, label, help, type: "color", colors: true });
const SECTIONS = [
  { id: "wording", icon: "Aa", tone: "green", title: "Wording", sub: "The words people read", help: "Leave a box empty to keep the default text from the app file.", fields: [
    { key: "txt_title", label: "App name", help: "Shown in the top bar, the welcome screen and the browser tab.", type: "text", ph: "Docs Chat" },
    { key: "txt_tagline", label: "Welcome line", help: "The sentence under the name on an empty chat.", type: "text" },
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
  { id: "fonts", icon: "T", tone: "green", title: "Fonts and text size", sub: "How words look", help: "Fonts load from Google Fonts. Offline, the fallback is a similar system font.", fields: [
    { key: "font", label: "Body font", help: "Used for messages and buttons.", type: "select", fonts: true },
    { key: "heading_font", label: "Heading font", help: "Used for titles and the welcome name.", type: "select", fonts: true },
    { key: "custom_font", label: "Custom Google font name", help: "Type a family name exactly as on fonts.google.com, then choose Custom above.", type: "text", ph: "e.g. Merriweather" },
    { key: "font_size", label: "Text size", help: "Makes all text larger or smaller.", type: "range", unit: "%" },
    { key: "line_height", label: "Line spacing", help: "Space between lines of text.", type: "range", unit: "%" } ] },
  { id: "shape", icon: "\u25A2", tone: "blue", title: "Shape and spacing", sub: "Corners, shadows, message style", help: "Small changes here make the whole app feel different.", fields: [
    { key: "radius", label: "Corner roundness", help: "0 is sharp corners. 100 is the default. Higher is rounder.", type: "range", unit: "%" },
    { key: "density", label: "Spacing", help: "Compact fits more on screen. Roomy is airy.", type: "select" },
    { key: "shadow", label: "Shadow", help: "Depth of the main panel.", type: "select" },
    { key: "bubble", label: "Message style", help: "Soft: filled bubbles. Flat: no bubble for answers. Outline: thin borders.", type: "select" } ] },
  { id: "emoji", icon: "\u263A", tone: "purple", title: "Emojis and icons", sub: "Avatars and buttons", help: "Type or paste one emoji. Leave empty for the default icon.", fields: [
    { key: "emoji_bot", label: "Assistant avatar", help: "Next to every answer.", type: "emoji", ph: "Optional" },
    { key: "emoji_you", label: "Your avatar", help: "Next to your messages.", type: "emoji", ph: "Optional" },
    { key: "emoji_hero", label: "Welcome emoji", help: "On an empty chat. Falls back to the assistant avatar.", type: "emoji", ph: "Optional" },
    { key: "emoji_send", label: "Send button", help: "Replaces the arrow.", type: "emoji", ph: "Optional" },
    { key: "emoji_attach", label: "Attach button", help: "Replaces the paperclip.", type: "emoji", ph: "Optional" },
    { key: "emoji_temp", label: "Temporary chat button", help: "Replaces the clock icon.", type: "emoji", ph: "Optional" } ] },
  { id: "motion", icon: "\u21BB", tone: "green", title: "Motion", sub: "Animations and speed", help: "Turn animation down if it feels busy. People who ask their device for less motion always get none.", fields: [
    { key: "motion", label: "Amount of motion", help: "Full: all effects. Subtle: quick and quiet. None: nothing moves.", type: "select" },
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
  pattern: { none: "None", dots: "Dots", grid: "Grid", lines: "Lines", diagonal: "Diagonal", checker: "Checker", waves: "Waves", plus: "Plus signs" }, motion: { full: "Full", subtle: "Subtle", none: "None" },
  entrance: { fade: "Fade in", slide: "Slide up", pop: "Pop", none: "None" }, bubble: { soft: "Soft bubbles", flat: "Flat", outline: "Outline" }, density: { compact: "Compact", cozy: "Cozy", roomy: "Roomy" },
  sidebar: { left: "Left", right: "Right", hidden: "Hidden" }, chat_width: { narrow: "Narrow", normal: "Normal", wide: "Wide", full: "Full width" }, avatars: { show: "Show", hide: "Hide" },
  you_align: { right: "Right", left: "Left" }, shadow: { none: "None", soft: "Soft", strong: "Strong" }, composer: { inline: "Inline", floating: "Floating" }, toolbar: { show: "Show", hide: "Hide" } };
const FONTNAMES = { "dm-sans": "DM Sans", inter: "Inter", system: "System default", georgia: "Georgia", fraunces: "Fraunces", playfair: "Playfair Display", lora: "Lora", "space-grotesk": "Space Grotesk", nunito: "Nunito", poppins: "Poppins", jetbrains: "JetBrains Mono", mono: "System monospace", custom: "Custom (type a name below)" };

const PRESETS = {
  Forest: {},
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
  wording: [["Basics", ["txt_title", "txt_tagline"]], ["Empty chat", ["txt_examples"]], ["Question box", ["txt_placeholder"]], ["Small print and sidebar", ["txt_hint", "txt_disclaimer", "txt_sidebar", "txt_footer"], true]],
  colors: [["Mode", ["mode"]], ["Brand", ["brand", "accent"]], ["Surfaces", ["bg", "surface", "sidebar"]], ["Text and lines", ["ink", "muted", "line"]], ["Messages and alerts", ["bot", "you", "danger"], true]],
  background: [["Style", ["bg_style", "bg_color2", "bg_angle", "bg_image"]], ["Pattern", ["pattern", "pattern_color", "pattern_opacity", "pattern_size"], true]],
  fonts: [["Fonts", ["font", "heading_font", "custom_font"]], ["Size", ["font_size", "line_height"]]],
  emoji: [["Main icons", ["emoji_bot", "emoji_you", "emoji_send"]], ["Other icons", ["emoji_hero", "emoji_attach", "emoji_temp"], true]],
  layout: [["Sizes", ["sidebar", "sidebar_width", "chat_width"]], ["Chat", ["avatars", "you_align", "composer", "sources_panel"]], ["More", ["toolbar"], true]]
};
const clone = (o) => JSON.parse(JSON.stringify(o));
const get = (f) => (f.colors ? theme[editMode][f.key] : theme[f.key]);
const setv = (f, v) => { if (f.colors) theme[editMode][f.key] = v; else theme[f.key] = v; changed(); };
let sendTimer = 0;
function pushPreview() {
  const t = clone(theme); const m = $("#pvmode .seg button[aria-checked=true], #pvmode button[aria-checked=true]"); t.mode = m ? m.dataset.m : t.mode;
  const w = $("#pv").contentWindow; if (w) w.postMessage({ ccTheme: t }, location.origin);
  const w2 = $("#pv").contentWindow; if (w2 && w2.CCTheme) { /* same-origin: also apply the wording/emoji source */ w2.CCTheme.value = t; }
}
function changed() {
  clearTimeout(sendTimer); sendTimer = setTimeout(pushPreview, 40);
  const dirty = JSON.stringify(theme) !== JSON.stringify(saved);
  $("#dirty").textContent = dirty ? "Unsaved changes (the preview shows them)" : "No unsaved changes"; $("#dirty").className = dirty ? "dirty" : "";
}
function control(f) {
  const id = "f-" + f.key; let input;
  const v = get(f);
  if (f.type === "color") {
    const swatch = el("input", { type: "color", id, value: v || "#888888", "aria-label": f.label }), hex = el("input", { type: "text", class: "hex", value: v || "", maxlength: "7", "aria-label": f.label + " hex code", placeholder: "automatic" });
    swatch.addEventListener("input", () => { hex.value = swatch.value; setv(f, swatch.value); });
    hex.addEventListener("input", () => { if (/^#[0-9a-fA-F]{6}$/.test(hex.value)) { swatch.value = hex.value; setv(f, hex.value.toLowerCase()); } else if (f.clearable && hex.value === "") setv(f, ""); });
    input = el("div", { class: "colorrow" }, swatch, hex); if (f.clearable) input.append(el("button", { type: "button", class: "mini", onclick: () => { hex.value = ""; setv(f, ""); } }, "Auto"));
  } else if (f.type === "select") {
    input = el("select", { id }); const opts = f.fonts ? Object.keys(meta.fonts).concat("custom") : meta.enums[f.key];
    opts.forEach((o) => input.append(el("option", { value: o, text: f.fonts ? FONTNAMES[o] || o : (LABELS[f.key] || {})[o] || o })));
    input.value = v; input.addEventListener("change", () => { setv(f, input.value); if (f.key === "mode" && input.value !== "auto") { editMode = input.value; setPvMode(editMode); drawLook(); } });
  } else if (f.type === "range") {
    const [lo, hi] = meta.ranges[f.key], out = el("output", { text: v + (f.unit || "") });
    input = el("div", { class: "rangerow" }, el("input", { type: "range", id, min: lo, max: hi, value: v, "aria-label": f.label }), out);
    input.firstChild.addEventListener("input", (e) => { out.textContent = e.target.value + (f.unit || ""); setv(f, +e.target.value); });
  } else if (f.type === "toggle") {
    input = el("label", { class: "check" }, el("input", { type: "checkbox", id }), "On"); input.firstChild.checked = !!v; input.firstChild.addEventListener("change", (e) => setv(f, e.target.checked));
  } else if (f.type === "area") {
    input = el("textarea", { id, rows: "4", placeholder: f.ph || "" }); input.value = v || ""; input.addEventListener("input", () => setv(f, input.value));
  } else {
    input = el("input", { type: "text", id, placeholder: f.ph || "", maxlength: f.type === "emoji" ? "8" : "300", class: f.type === "emoji" ? "emoji" : "" }); input.value = v || ""; input.addEventListener("input", () => setv(f, input.value));
  }
  if (!canEdit) input.querySelectorAll ? input.querySelectorAll("input,select,button").forEach((x) => (x.disabled = true)) : (input.disabled = true);
  if (!canEdit && input.tagName === "SELECT") input.disabled = true;
  return el("div", { class: "field" }, el("label", { for: id, class: "flabel" }, f.label), el("span", { class: "h", text: f.help }), input);
}
async function saveSection(s) {
  try {
    const base = clone(saved);
    for (const f of s.fields) { if (f.colors) { base.light[f.key] = theme.light[f.key]; base.dark[f.key] = theme.dark[f.key]; } else base[f.key] = theme[f.key]; }
    saved = clone((await api("/api/theme", { theme: base })).theme); changed(); say(s.title + " saved. Other sections keep their last saved values.");
  } catch (e) { say(e.message, true); }
}
/* the preview follows the section being edited */
let activeSec = "presets";
function pvFollow() {
  const m = activeSec === "model", card = $("#pvmodel"), fr = $("#pv"), cap = $("#pvcap");
  const names = { presets: "Whole look", wording: "Wording", colors: "Colors", background: "Background", fonts: "Fonts", shape: "Shape and spacing", emoji: "Icons", motion: "Motion", layout: "Layout", model: "Model" };
  if (cap) cap.textContent = "Showing: " + (names[activeSec] || "Chat");
  if (card.hidden === m) { (m ? card : fr).hidden = false; (m ? fr : card).hidden = true; (m ? card : fr).animate([{ opacity: 0, transform: "translateY(4px)" }, { opacity: 1, transform: "none" }], { duration: 180, easing: "ease-out" }); }
  if (m) {
    const k = keyInfo[cur.provider] || {}, r = $("#testres");
    card.replaceChildren(el("b", { text: NAMES[cur.provider] || cur.provider }), el("div", { class: "pvm-row", text: "Model: " + (chosenModel() || "not chosen yet") }), el("div", { class: "pvm-row", text: k.source === "saved" ? "Key saved" : (k.source === "env" ? "Key from environment" : (k.needed === false ? "No key needed" : "No key yet")) }), el("div", { class: "pvm-row " + (r && r.classList.contains("ok") ? "ok" : (r && r.classList.contains("bad") ? "bad" : "")), text: (r && r.textContent) || "Connection not tested yet" }), el("div", { class: "pvm-ans", text: "Sample answer: Refunds are available within 30 days of purchase [1]." }));
  }
}
function pvPop() { const f = document.getElementById("pv"); if (!f || matchMedia("(prefers-reduced-motion:reduce)").matches) return; f.animate([{ opacity: .55, transform: "scale(.985)" }, { opacity: 1, transform: "scale(1)" }], { duration: 220, easing: "ease-out" }); }
function drawLook() {
  const root = $("#look"); root.replaceChildren();
  for (const s of SECTIONS) {
    const sec = el("section", { class: "tile", id: "sec-" + s.id });
    const head = el("div", { class: "head" }, el("span", { class: "ic " + s.tone, text: s.icon }), el("div", {}, el("b", { text: s.title }), el("small", { text: s.sub })), el("button", { type: "button", class: "mini reset", title: "Put this group back to the defaults", disabled: canEdit ? undefined : "", onclick: () => resetGroup(s) }, "Reset group"));
    sec.append(head, el("div", { class: "help", text: s.help }));
    if (s.modeTabs) {
      const tabs = el("div", { class: "seg mini", role: "radiogroup", "aria-label": "Color set being edited" });
      for (const m of ["light", "dark"]) tabs.append(el("button", { type: "button", "data-m": m, role: "radio", "aria-checked": String(editMode === m), onclick: () => { editMode = m; setPvMode(m); drawLook(); } }, "Editing: " + (m === "light" ? "Light" : "Dark")));
      sec.append(tabs);
    }
    const byKey = Object.fromEntries(s.fields.map((f) => [f.key, f])); const gs = GROUPS[s.id];
    if (!gs) { const grid = el("div", { class: "fields" }); s.fields.forEach((f) => grid.append(control(f))); sec.append(grid); }
    else {
      const used = new Set();
      for (const [title, keys, collapsed] of gs) {
        const fs = keys.map((k) => byKey[k]).filter(Boolean); if (!fs.length) continue; fs.forEach((f) => used.add(f.key));
        const grid = el("div", { class: "fields" + (fs.every((f) => f.type === "color") ? " colorlist" : "") }); fs.forEach((f) => grid.append(control(f)));
        if (collapsed) { const d = el("details", { class: "grp" }, el("summary", { text: title }), grid); sec.append(d); }
        else sec.append(el("div", { class: "grp" }, el("h4", { text: title }), grid));
      }
      const rest = s.fields.filter((f) => !used.has(f.key)); if (rest.length) { const g = el("div", { class: "fields" }); rest.forEach((f) => g.append(control(f))); sec.append(el("details", { class: "grp" }, el("summary", { text: "More options" }), g)); }
    }
    sec.append(el("div", { class: "secfoot" }, el("button", { type: "button", class: "go blue", disabled: canEdit ? undefined : "", onclick: () => saveSection(s) }, "Save " + s.title.toLowerCase()), el("button", { type: "button", class: "go ghost", disabled: canEdit ? undefined : "", onclick: () => resetGroup(s) }, "Reset to default")));
    root.append(sec);
  }
  buildMenu();
}
function resetGroup(s) { const d = meta.default; for (const f of s.fields) { if (f.colors) theme[editMode][f.key] = d[editMode][f.key]; else theme[f.key] = d[f.key]; } drawLook(); changed(); }
function setPvMode(m) { document.querySelectorAll("#pvmode button").forEach((b) => b.setAttribute("aria-checked", String(b.dataset.m === m))); }
function buildMenu() {
  const m = $("#menu"); m.replaceChildren();
  const items = [["presets", "Presets and states"], ["model", "Model"]].concat(SECTIONS.map((s) => [s.id, s.title]));
  items.forEach(([id, t]) => m.append(el("a", { href: "#sec-" + id, text: t })));
  const links = [...m.children]; links[0].classList.add("on");
  const io = new IntersectionObserver((es) => { for (const e of es) if (e.isIntersecting) { activeSec = e.target.id.replace("sec-", ""); pvFollow(); links.forEach((a) => a.classList.toggle("on", a.getAttribute("href") === "#" + e.target.id)); } }, { rootMargin: "-20% 0px -70% 0px" });
  items.forEach(([id]) => { const n = document.getElementById("sec-" + id); if (n) io.observe(n); });
}
function buildPresets() {
  const box = $("#presets"); box.replaceChildren();
  let showMore = false;
  const draw = () => { box.replaceChildren();
  const all = showMore ? Object.assign({}, PRESETS, MORE_PRESETS) : PRESETS;
  for (const [name, p] of Object.entries(all)) {
    const t = Object.assign(clone(meta.default), clone(p)); t.light = Object.assign(clone(meta.default.light), p.light || {}); t.dark = Object.assign(clone(meta.default.dark), p.dark || {});
    const c = t.mode === "dark" ? t.dark : t.light;
    const b = el("button", { type: "button", class: "preset", title: "Apply the " + name + " look", disabled: canEdit ? undefined : "" }, el("span", { class: "sw", style: `background:linear-gradient(135deg,${c.bg} 0 50%,${c.brand} 50% 75%,${c.accent} 75%)` }), name);
    b.addEventListener("click", () => { const keep = ["txt_title", "txt_tagline", "txt_examples", "txt_placeholder", "txt_hint", "txt_disclaimer", "txt_sidebar", "txt_footer"]; for (const k of keep) t[k] = theme[k]; theme = t; editMode = theme.mode === "dark" ? "dark" : "light"; setPvMode(editMode); drawLook(); pvPop(); changed(); say("Preset \u201c" + name + "\u201d applied to the preview. Press Save look to keep it."); });
    box.append(b);
  }
  const more = el("button", { type: "button", class: "preset more", "aria-expanded": showMore ? "true" : "false" }, showMore ? "Show fewer" : "Load more");
  more.addEventListener("click", () => { showMore = !showMore; draw(); });
  box.append(more); };
  draw();
}
async function init() {
  const c = await api("/api/config"); $("#h").textContent = c.app.title + " configuration"; document.title = c.app.title + " configuration";
  const d = await api("/api/settings"); cur = d.settings; canEdit = d.can_edit; try { keyInfo = (await api("/api/provider/status")).keys; } catch (e) { keyInfo = {}; }
  const th = await api("/api/theme"); theme = th.theme; meta = th.meta; saved = clone(theme); canEdit = canEdit && th.can_edit !== false;
  const seg = $("#seg");
  buildChips(d.providers);
  draw(); await states(); buildPresets(); drawLook();
  document.querySelectorAll("#pvmode button").forEach((b) => b.addEventListener("click", () => { setPvMode(b.dataset.m); pushPreview(); }));
  $("#pv").addEventListener("load", () => { setPvMode(theme.mode === "dark" ? "dark" : "light"); setTimeout(pushPreview, 250); });
  if (!canEdit) say("View only. Open this page on the computer running the app, or sign in as the admin, to change anything.");
  $("#temp").addEventListener("input", () => ($("#tv").textContent = (+$("#temp").value).toFixed(2)));
  $("#topk").addEventListener("input", () => ($("#kv").textContent = $("#topk").value));
  $("#modelPick").addEventListener("change", pickChanged);
  $("#refreshModels").addEventListener("click", () => loadModels(true));
  $("#keysave").addEventListener("click", async () => { const v = $("#apikey").value.trim(); if (!v) { say("Paste a key first.", true); return; } try { const r = await api("/api/provider/key", { provider: cur.provider, key: v }); keyInfo[cur.provider] = r.key; $("#apikey").value = ""; await provExtras(); say("Key saved on this computer."); } catch (e) { say(e.message, true); } });
  $("#keyclear").addEventListener("click", async () => { try { const r = await api("/api/provider/key", { provider: cur.provider, clear: true }); keyInfo[cur.provider] = r.key; await provExtras(); say("Key removed."); } catch (e) { say(e.message, true); } });
  $("#testconn").addEventListener("click", async () => { const t = $("#testres"); t.className = "testres"; t.textContent = "Testing..."; try { const r = await api("/api/provider/test", { provider: cur.provider, model: chosenModel(), base_url: $("#base").value.trim() }); t.className = "testres " + (r.ok ? "ok" : "bad"); t.textContent = (r.ok ? "Passed. " : "Failed. ") + r.message; pvFollow(); } catch (e) { t.className = "testres bad"; t.textContent = "Failed. " + e.message; } });
  $("#apply").addEventListener("click", async () => { try { cur = (await api("/api/settings", { settings: read() })).settings; draw(); say("Applied. New questions use these settings."); } catch (e) { say(e.message, true); } });
  $("#save").addEventListener("click", async () => { try { const n = (await api("/api/states/save", { name: $("#sname").value })).name; await states(); say("Saved as \u201c" + n + "\u201d."); } catch (e) { say(e.message, true); } });
  $("#load").addEventListener("click", async () => { const n = $("#states").value; if (!n) return say("Choose a saved state first", true); try { cur = (await api("/api/states/load", { name: n })).settings; draw(); say("Loaded \u201c" + n + "\u201d."); } catch (e) { say(e.message, true); } });
  $("#del").addEventListener("click", async () => { const n = $("#states").value; if (!n) return say("Choose a saved state first", true); await api("/api/states/delete", { name: n }); await states(); say("Deleted."); });
  $("#saveLook").addEventListener("click", async () => { try { theme = (await api("/api/theme", { theme })).theme; saved = clone(theme); drawLook(); changed(); say("Look saved. The chat now uses it for everyone."); } catch (e) { say(e.message, true); } });
  $("#resetAll").addEventListener("click", () => { if (!confirm("Put every look setting back to the default? (Press Save look afterwards to keep it.)")) return; theme = clone(meta.default); drawLook(); changed(); });
  $("#exp").addEventListener("click", () => { const a = el("a", { href: URL.createObjectURL(new Blob([JSON.stringify(theme, null, 1)], { type: "application/json" })), download: "customchat-look.json" }); document.body.append(a); a.click(); a.remove(); });
  $("#imp").addEventListener("change", async (e) => { const f = e.target.files[0]; if (!f) return; try { const j = JSON.parse(await f.text()); const t = Object.assign(clone(meta.default), j); t.light = Object.assign(clone(meta.default.light), j.light || {}); t.dark = Object.assign(clone(meta.default.dark), j.dark || {}); theme = t; drawLook(); changed(); say("Look imported into the preview. Press Save look to keep it."); } catch (x) { say("That file is not a CustomChat look file", true); } e.target.value = ""; });
}
init().catch((e) => say(e.message, true));
})();
