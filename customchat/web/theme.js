/* Applies the saved look (colours, fonts, background, motion, layout) to a page. Shared by the chat and the Configuration preview. */
(() => {
"use strict";
const FONT_STACKS = {
  "dm-sans": ['"DM Sans",system-ui,sans-serif', "DM+Sans:wght@400;500;700;800"], inter: ['"Inter",system-ui,sans-serif', "Inter:wght@400;500;700"],
  system: ['-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif', null], georgia: ["Georgia,'Times New Roman',serif", null],
  fraunces: ['"Fraunces",Georgia,serif', "Fraunces:wght@600;700"], playfair: ['"Playfair Display",Georgia,serif', "Playfair+Display:wght@500;700"],
  lora: ['"Lora",Georgia,serif', "Lora:wght@400;600"], "space-grotesk": ['"Space Grotesk",system-ui,sans-serif', "Space+Grotesk:wght@400;500;700"],
  nunito: ['"Nunito",system-ui,sans-serif', "Nunito:wght@400;600;800"], poppins: ['"Poppins",system-ui,sans-serif', "Poppins:wght@400;500;600"],
  jetbrains: ['"JetBrains Mono",ui-monospace,monospace', "JetBrains+Mono:wght@400;600"], mono: ["ui-monospace,SFMono-Regular,Menlo,Consolas,monospace", null],
};
const lum = (hex) => { const v = [1, 3, 5].map((i) => parseInt(hex.substr(i, 2), 16) / 255).map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4)); return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]; };
const onColor = (hex) => (lum(hex) > 0.45 ? "#10201a" : "#fffdf7");
const rgba = (hex, a) => `rgba(${[1, 3, 5].map((i) => parseInt(hex.substr(i, 2), 16)).join(",")},${a})`;

function patternImage(name, c, op) {
  const col = rgba(c, op / 100);
  switch (name) {
    case "dots": return `radial-gradient(${col} 1.4px, transparent 1.6px)`;
    case "grid": return `linear-gradient(${col} 1px, transparent 1px), linear-gradient(90deg, ${col} 1px, transparent 1px)`;
    case "lines": return `repeating-linear-gradient(0deg, ${col} 0 1px, transparent 1px 100%)`;
    case "diagonal": return `repeating-linear-gradient(45deg, ${col} 0 1px, transparent 1px 8px)`;
    case "checker": return `conic-gradient(${col} 25%, transparent 0 50%, ${col} 0 75%, transparent 0)`;
    case "plus": return `linear-gradient(${col},${col}), linear-gradient(${col},${col})`;
    case "waves": return `radial-gradient(circle at 50% 100%, transparent 38%, ${col} 39% 41%, transparent 42%), radial-gradient(circle at 50% 0%, transparent 38%, ${col} 39% 41%, transparent 42%)`;
    default: return "none";
  }
}

function loadFonts(t) {
  const fams = [];
  for (const k of [t.font, t.heading_font]) { const f = FONT_STACKS[k]; if (f && f[1]) fams.push(f[1]); }
  if (t.custom_font && (t.font === "custom" || t.heading_font === "custom")) fams.push(t.custom_font.trim().replace(/ /g, "+") + ":wght@400;500;700");
  const href = fams.length ? "https://fonts.googleapis.com/css2?" + [...new Set(fams)].map((f) => "family=" + f).join("&") + "&display=swap" : "";
  let l = document.getElementById("cc-fonts");
  if (!href) { if (l) l.remove(); return; }
  if (!l) { l = document.createElement("link"); l.id = "cc-fonts"; l.rel = "stylesheet"; document.head.append(l); }
  if (l.getAttribute("href") !== href) l.setAttribute("href", href);
}
const stack = (k, custom, fallback) => (k === "custom" && custom ? `"${custom}",${fallback}` : (FONT_STACKS[k] || FONT_STACKS["dm-sans"])[0]);

function apply(t, root = document.documentElement) {
  if (!t || !t.light) return;
  const local = !window.__ccPreview && localStorage.getItem("cc_mode");
  const mode = local === "light" || local === "dark" ? local : t.mode;
  const dark = mode === "dark" || (mode === "auto" && matchMedia("(prefers-color-scheme:dark)").matches);
  const c = dark ? t.dark : t.light, s = root.style, set = (k, v) => s.setProperty(k, v);
  root.dataset.theme = dark ? "dark" : "light";
  set("--brand", c.brand); set("--on-brand", onColor(c.brand)); set("--accent", c.brand); set("--lime", c.accent); set("--accent2", c.accent); set("--on-lime", onColor(c.accent));
  set("--cream", c.bg); set("--paper", c.surface); set("--ink", c.ink); set("--mut", c.muted); set("--line", c.line); set("--side-bg", c.sidebar);
  set("--bot", c.bot); set("--you", c.you); set("--danger", c.danger); set("--soft", `color-mix(in srgb, ${c.sidebar} 70%, ${c.surface})`);
  set("--tool", rgba(c.brand, 0.12));
  set("--shadow", { none: "none", soft: dark ? "0 24px 70px rgba(0,0,0,.4)" : `0 24px 70px ${rgba(c.brand, 0.1)}`, strong: dark ? "0 30px 90px rgba(0,0,0,.65)" : `0 30px 90px ${rgba(c.brand, 0.28)}` }[t.shadow]);
  // fonts
  loadFonts(t);
  set("--font", stack(t.font, t.custom_font, 'system-ui,sans-serif,"Apple Color Emoji","Segoe UI Emoji","Noto Color Emoji"')); set("--serif", stack(t.heading_font, t.custom_font, 'Georgia,serif,"Apple Color Emoji","Segoe UI Emoji","Noto Color Emoji"'));
  set("--fs", t.font_size / 100); set("--lh", t.line_height / 100); set("--rs", t.radius / 100);
  set("--dens", { compact: 0.78, cozy: 1, roomy: 1.3 }[t.density]);
  set("--speed", 100 / t.speed);
  set("--side-w", t.sidebar_width + "px");
  set("--chat-max", { narrow: "640px", normal: "800px", wide: "1020px", full: "100%" }[t.chat_width]);
  // background and pattern
  const soft = c.bg;
  const layer = { soft, solid: c.bg, gradient: `linear-gradient(${t.bg_angle}deg,${c.bg},${t.bg_color2})`, image: t.bg_image ? `linear-gradient(${rgba(c.bg, 0.55)},${rgba(c.bg, 0.55)}),url("${t.bg_image}") center/cover fixed, ${c.bg}` : soft }[t.bg_style];
  set("--bg-layer", layer);
  const pc = t.pattern_color || c.ink, ps = t.pattern_size;
  set("--pat-img", patternImage(t.pattern, pc, t.pattern_opacity));
  set("--pat-size", t.pattern === "waves" ? `${ps * 2}px ${ps}px` : `${ps}px ${ps}px`);
  set("--pat-pos", t.pattern === "plus" ? "center" : "0 0");
  if (t.pattern === "plus") { set("--pat-img", `linear-gradient(${rgba(pc, t.pattern_opacity / 100)},${rgba(pc, t.pattern_opacity / 100)}),linear-gradient(${rgba(pc, t.pattern_opacity / 100)},${rgba(pc, t.pattern_opacity / 100)})`); set("--pat-size", `${ps}px 1px, 1px ${ps}px`); }
  const d = root.dataset;
  d.pattern = t.pattern; d.motion = t.motion; d.entrance = t.entrance; d.bubble = t.bubble; d.sidebar = t.sidebar; d.chatw = t.chat_width;
  d.avatars = t.avatars; d.align = t.you_align; d.composer = t.composer; d.toolbar = t.toolbar; d.lift = t.hover_lift ? "on" : "off"; d.sources = t.sources_panel ? "on" : "off";
  const meta = document.querySelector('meta[name="theme-color"]'); if (meta) meta.content = c.brand;
  window.CCTheme.value = t;
}
window.__ccPreview = /[?&]preview=1/.test(location.search);
window.CCTheme = { apply, value: null, fonts: FONT_STACKS };
try { const el = document.getElementById("cc-theme"); if (el) apply(JSON.parse(el.textContent)); } catch (e) { /* keep defaults */ }
matchMedia("(prefers-color-scheme:dark)").addEventListener("change", () => window.CCTheme.value && apply(window.CCTheme.value));
window.addEventListener("message", (e) => { if (e.origin === location.origin && e.data && e.data.ccTheme) apply(e.data.ccTheme); });
})();
