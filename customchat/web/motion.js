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
