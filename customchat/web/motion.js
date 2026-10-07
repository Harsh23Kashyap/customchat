/* Small motion helpers. Everything here is decoration: if it fails, the page still works. */
(function () {
  try {
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var root = document.documentElement;
    // header shadow after scrolling
    var on = function () { root.classList.toggle("is-scrolled", (window.scrollY || 0) > 4); };
    window.addEventListener("scroll", on, { passive: true }); on();
    var th = document.getElementById("thread");
    if (th) th.addEventListener("scroll", function () { root.classList.toggle("thread-scrolled", th.scrollTop > 4); }, { passive: true });
    // sections reveal once; skipped for reduced motion or when IntersectionObserver is missing
    if (!reduce && "IntersectionObserver" in window) {
      var io = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } }); }, { rootMargin: "0px 0px -8% 0px" });
      var seen = new WeakSet();
      var scan = function () {
        document.querySelectorAll(".tile").forEach(function (t) {
          if (seen.has(t)) return; seen.add(t);
          var r = t.getBoundingClientRect();
          if (r.top < window.innerHeight) return; // already visible: leave it alone
          t.classList.add("rv"); io.observe(t);
        });
      };
      scan(); setTimeout(scan, 600);
    }
  } catch (e) { /* decoration only */ }
})();

// sliding indicator for segmented controls, and a short settle when Simple/Advanced changes
(function () {
  try {
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var place = function (seg, animate) {
      var a = seg.querySelector(":scope > button[aria-checked=true]");
      var ind = seg.querySelector(":scope > .seg-ind");
      if (!a) { if (ind) ind.classList.remove("on"); seg.classList.remove("slide"); return; }
      if (!ind) { ind = document.createElement("i"); ind.className = "seg-ind"; ind.setAttribute("aria-hidden", "true"); seg.insertBefore(ind, seg.firstChild); }
      seg.classList.add("slide");
      ind.style.setProperty("width", a.offsetWidth + "px", "important"); ind.style.setProperty("height", a.offsetHeight + "px", "important"); ind.style.setProperty("min-height", "0", "important");
      ind.style.transform = "translate(" + a.offsetLeft + "px," + a.offsetTop + "px)";
      ind.classList.add("on");
      if (animate && !reduce) ind.classList.add("go");
    };
    var scan = function (animate) { document.querySelectorAll(".seg").forEach(function (s) { place(s, animate); }); };
    var t; var later = function () { clearTimeout(t); t = setTimeout(function () { scan(true); }, 0); };
    scan(false);
    new MutationObserver(later).observe(document.body, { subtree: true, childList: true, attributes: true, attributeFilter: ["aria-checked"] });
    window.addEventListener("resize", function () { document.querySelectorAll(".seg-ind.go").forEach(function (i) { i.classList.remove("go"); }); scan(false); });
    // Simple <-> Advanced: the sections settle in again
    var last = document.body.classList.contains("simple");
    new MutationObserver(function () {
      var now = document.body.classList.contains("simple");
      if (now === last) return; last = now;
      if (reduce) return;
      document.body.classList.add("mode-swap");
      setTimeout(function () { document.body.classList.remove("mode-swap"); }, 420);
    }).observe(document.body, { attributes: true, attributeFilter: ["class"] });
  } catch (e) { /* decoration only */ }
})();

// small confirmations: fields tint briefly (reset, saved looks list), pictures settle in once loaded
(function () {
  try {
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.ccPulse = function (el) {
      if (!el || reduce) return;
      el.classList.remove("pulse-soft"); void el.offsetWidth; el.classList.add("pulse-soft");
      setTimeout(function () { el.classList.remove("pulse-soft"); }, 700);
    };
    var st = document.getElementById("states");
    if (st) { var first = true; new MutationObserver(function () { if (first) { first = false; return; } window.ccPulse(st); }).observe(st, { childList: true }); }
    document.addEventListener("load", function (e) {
      var t = e.target; if (!reduce && t && t.tagName === "IMG" && t.classList && t.classList.contains("logoprev")) {
        t.classList.remove("pop"); void t.offsetWidth; t.classList.add("pop");
      }
    }, true);
  } catch (e) { /* decoration only */ }
})();

// fonts, background and pattern choices cannot interpolate, so the preview eases in from slightly faded
(function () {
  try {
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    document.addEventListener("change", function (e) {
      if (reduce || !e.target || !e.target.closest) return;
      var f = e.target.closest("[data-k]"); if (!f) return;
      var k = f.dataset.k || "";
      if (!/font|^bg|background|pattern|emoji|icon/.test(k)) return;
      [/font/.test(k) ? document.getElementById("typeprev") : null].forEach(function (pv) {
        if (!pv) return;
        pv.classList.remove("fade-soft"); void pv.offsetWidth; pv.classList.add("fade-soft");
        setTimeout(function () { pv.classList.remove("fade-soft"); }, 400);
      });
    }, true);
  } catch (e) { /* decoration only */ }
})();

// dim the old no-evidence answer when a new question arrives; demo the chosen motion level on the preview
(function () {
  try {
    var th = document.getElementById("thread");
    if (th) new MutationObserver(function (ms) {
      ms.forEach(function (m) { m.addedNodes.forEach(function (n) {
        if (!(n.classList && n.classList.contains("row") && n.classList.contains("u"))) return;
        th.querySelectorAll(".row:not(.u)").forEach(function (r) { if (r.querySelector(".nf-tips")) r.classList.add("stale"); });
      }); });
    }).observe(th, { childList: true });
    document.addEventListener("change", function (e) {
      var f = e.target && e.target.closest && e.target.closest("[data-k=motion]"); if (!f) return;
      var pv = document.querySelector(".preview"); if (!pv) return;
      setTimeout(function () { pv.classList.remove("demo"); void pv.offsetWidth; pv.classList.add("demo"); setTimeout(function () { pv.classList.remove("demo"); }, 500); }, 60);
    }, true);
  } catch (e) { /* decoration only */ }
})();

// key status text eases in when it changes; the section you jump to from the menu settles in
(function () {
  try {
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var restart = function (el, cls, ms) { el.classList.remove(cls); void el.offsetWidth; el.classList.add(cls); setTimeout(function () { el.classList.remove(cls); }, ms); };
    var ks = document.getElementById("keystate");
    if (ks && !reduce) {
      var last = ks.textContent;
      new MutationObserver(function () { if (ks.textContent !== last) { last = ks.textContent; restart(ks, "swap", 300); } }).observe(ks, { childList: true, characterData: true, subtree: true });
    }
    document.addEventListener("click", function (e) {
      if (reduce || !e.target.closest) return;
      var a = e.target.closest("#menu a[href^='#']"); if (!a) return;
      var t = document.getElementById(a.getAttribute("href").slice(1)); if (t) restart(t, "jump-in", 400);
    }, true);
  } catch (e) { /* decoration only */ }
})();

// slider values ease instead of snapping: the number brightens as it changes
(function () {
  try {
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var timers = new WeakMap();
    document.addEventListener("input", function (e) {
      var t = e.target; if (reduce || !t || t.type !== "range") return;
      var o = t.closest("label,.rangerow,.row2,div"); o = o && o.querySelector("output"); if (!o) return;
      o.classList.remove("tick"); void o.offsetWidth; o.classList.add("tick");
      clearTimeout(timers.get(o)); timers.set(o, setTimeout(function () { o.classList.remove("tick"); }, 160));
    }, true);
  } catch (e) { /* decoration only */ }
})();
