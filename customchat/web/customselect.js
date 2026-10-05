/* Replaces native selects with a styled listbox. The real <select> stays in the DOM (hidden) so existing code keeps working. */
(function () {
  const open = { cur: null };
  function close() { if (open.cur) { open.cur.classList.remove("open"); open.cur.querySelector(".cs-btn").setAttribute("aria-expanded", "false"); open.cur = null; } }
  document.addEventListener("click", (e) => { if (open.cur && !open.cur.contains(e.target)) close(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") close(); });
  function enhance(sel) {
    if (sel.dataset.cs || sel.multiple) return; sel.dataset.cs = "1";
    const wrap = document.createElement("div"); wrap.className = "cs " + (sel.className || "");
    const btn = document.createElement("button"); btn.type = "button"; btn.className = "cs-btn"; btn.setAttribute("aria-haspopup", "listbox"); btn.setAttribute("aria-expanded", "false");
    btn.setAttribute("aria-label", sel.getAttribute("aria-label") || sel.title || "Choose");
    const lab = document.createElement("span"); lab.className = "cs-label"; const car = document.createElement("span"); car.className = "cs-car"; car.setAttribute("aria-hidden", "true");
    btn.append(lab, car);
    const list = document.createElement("div"); list.className = "cs-list"; list.setAttribute("role", "listbox");
    sel.parentNode.insertBefore(wrap, sel); wrap.append(btn, list, sel); sel.classList.add("cs-native"); sel.tabIndex = -1; sel.setAttribute("aria-hidden", "true");
    const sync = () => { const o = sel.options[sel.selectedIndex]; lab.textContent = o ? o.textContent : ""; btn.disabled = sel.disabled; };
    const build = () => {
      list.replaceChildren();
      [...sel.options].forEach((o, i) => {
        const it = document.createElement("div"); it.className = "cs-opt" + (i === sel.selectedIndex ? " on" : ""); it.setAttribute("role", "option"); it.setAttribute("aria-selected", i === sel.selectedIndex ? "true" : "false"); it.textContent = o.textContent; it.tabIndex = -1;
        if (o.disabled) it.classList.add("dis");
        it.addEventListener("click", () => { if (o.disabled) return; sel.selectedIndex = i; sel.dispatchEvent(new Event("change", { bubbles: true })); sync(); close(); btn.focus(); });
        list.append(it);
      }); sync();
    };
    btn.addEventListener("click", () => { if (wrap.classList.contains("open")) { close(); return; } close(); build(); wrap.classList.add("open"); btn.setAttribute("aria-expanded", "true"); open.cur = wrap;
      const r = btn.getBoundingClientRect(); wrap.classList.toggle("up", innerHeight - r.bottom < 240 && r.top > 240); const on = list.querySelector(".on"); if (on) on.scrollIntoView({ block: "nearest" }); });
    btn.addEventListener("keydown", (e) => { if (e.key === "ArrowDown" || e.key === "ArrowUp") { e.preventDefault(); const d = e.key === "ArrowDown" ? 1 : -1; const n = Math.max(0, Math.min(sel.options.length - 1, sel.selectedIndex + d)); sel.selectedIndex = n; sel.dispatchEvent(new Event("change", { bubbles: true })); sync(); } });
    sel.addEventListener("change", sync);
    new MutationObserver(() => { sync(); if (wrap.classList.contains("open")) build(); }).observe(sel, { childList: true, subtree: true, attributes: true });
    const d = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, "value"); Object.defineProperty(sel, "value", { get() { return d.get.call(this); }, set(v) { d.set.call(this, v); sync(); } });
    sync();
  }
  function scan() { document.querySelectorAll("select").forEach(enhance); }
  new MutationObserver(scan).observe(document.documentElement, { childList: true, subtree: true });
  if (document.readyState !== "loading") scan(); else document.addEventListener("DOMContentLoaded", scan);
})();
