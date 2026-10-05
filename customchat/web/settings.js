(() => {
"use strict";
const $ = (s) => document.querySelector(s);
const NAMES = { mock: "Demo", ollama: "Ollama", openai: "OpenAI", claude: "Claude", gemini: "Gemini", openai_compatible: "Other" };
let cur = {}, canEdit = false;
const token = localStorage.getItem("cc_token") || "";
async function api(path, body) {
  const h = { "Content-Type": "application/json" }; if (token) h.Authorization = "Bearer " + token;
  const r = await fetch(path, body === undefined ? { headers: h } : { method: "POST", headers: h, body: JSON.stringify(body) });
  const d = await r.json().catch(() => ({})); if (!r.ok) throw new Error(d.error || "Request failed"); return d;
}
const say = (t, err) => { const m = $("#msg"); m.textContent = t; m.className = "msg" + (err ? " err" : ""); };
function draw() {
  $("#model").value = cur.model || ""; $("#base").value = cur.base_url || ""; $("#temp").value = cur.temperature; $("#topk").value = cur.top_k; $("#rewrite").checked = !!cur.query_rewrite;
  $("#tv").textContent = (+cur.temperature).toFixed(2); $("#kv").textContent = cur.top_k;
  document.querySelectorAll("#seg button").forEach((b) => b.setAttribute("aria-checked", String(b.dataset.p === cur.provider)));
  for (const id of ["model", "base", "temp", "topk", "rewrite", "apply", "load"]) $("#" + id).disabled = !canEdit;
}
const read = () => ({ provider: cur.provider, model: $("#model").value.trim(), base_url: $("#base").value.trim(), temperature: +$("#temp").value, top_k: +$("#topk").value, query_rewrite: $("#rewrite").checked });
async function states() {
  const s = (await api("/api/states")).states; const sel = $("#states"); sel.replaceChildren();
  const o = document.createElement("option"); o.value = ""; o.textContent = "Select a state..."; sel.append(o);
  s.forEach((n) => { const x = document.createElement("option"); x.value = n; x.textContent = n; sel.append(x); });
}
async function init() {
  const c = await api("/api/config"); $("#h").textContent = "Configuration \u2014 " + c.app.title; document.title = "Configuration \u2014 " + c.app.title;
  const d = await api("/api/settings"); cur = d.settings; canEdit = d.can_edit;
  const seg = $("#seg");
  d.providers.forEach((p) => { const b = document.createElement("button"); b.type = "button"; b.dataset.p = p; b.setAttribute("role", "radio"); b.textContent = NAMES[p] || p;
    b.addEventListener("click", () => { if (canEdit) { cur = { ...read(), provider: p }; draw(); } }); seg.append(b); });
  draw(); await states();
  if (!canEdit) say("View only. Open this page on the computer running the app, or sign in with the access token, to change settings.");
  $("#temp").addEventListener("input", () => ($("#tv").textContent = (+$("#temp").value).toFixed(2)));
  $("#topk").addEventListener("input", () => ($("#kv").textContent = $("#topk").value));
  $("#apply").addEventListener("click", async () => { try { cur = (await api("/api/settings", { settings: read() })).settings; draw(); say("Applied. New questions use these settings."); } catch (e) { say(e.message, true); } });
  $("#save").addEventListener("click", async () => { try { const n = (await api("/api/states/save", { name: $("#sname").value })).name; await states(); say("Saved as \u201c" + n + "\u201d."); } catch (e) { say(e.message, true); } });
  $("#load").addEventListener("click", async () => { const n = $("#states").value; if (!n) return say("Choose a saved state first", true); try { cur = (await api("/api/states/load", { name: n })).settings; draw(); say("Loaded \u201c" + n + "\u201d."); } catch (e) { say(e.message, true); } });
  $("#del").addEventListener("click", async () => { const n = $("#states").value; if (!n) return say("Choose a saved state first", true); await api("/api/states/delete", { name: n }); await states(); say("Deleted."); });
}
init().catch((e) => say(e.message, true));
})();
