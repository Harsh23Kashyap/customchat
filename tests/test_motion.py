import os, unittest
W = os.path.join(os.path.dirname(__file__), "..", "customchat", "web")
rd = lambda n: open(os.path.join(W, n), encoding="utf-8").read()


class Motion(unittest.TestCase):
    def test_segment_indicator(self):
        css, js = rd("motion.css"), rd("motion.js")
        self.assertIn(".seg-ind", css)
        self.assertIn("seg-ind", js)
        self.assertIn("translate(", js)
        # the old filled background is only removed once the indicator exists
        self.assertIn(".seg.slide>button[aria-checked=true]", css)

    def test_mode_swap_respects_reduced_motion(self):
        css, js = rd("motion.css"), rd("motion.js")
        self.assertIn("mode-swap", js)
        i = css.index(".mode-swap .col .tile")
        self.assertIn("prefers-reduced-motion:no-preference", css[max(0, i - 120):i])

    def test_decoration_never_throws(self):
        js = rd("motion.js")
        self.assertGreaterEqual(js.count("catch (e)"), 2)

    def test_pulse_and_picture_settle(self):
        css, js, st = rd("motion.css"), rd("motion.js"), rd("settings.js")
        self.assertIn("ccPulse", js)
        self.assertIn("ccPulse", st)  # reset group calls it, guarded so a failure cannot break reset
        self.assertIn(".pulse-soft", css)
        self.assertIn("m-img", css)
        i = css.index("select.pulse-soft")
        self.assertIn("prefers-reduced-motion:no-preference", css[max(0, i - 120):i])

    def test_drawer_scrim(self):
        css = rd("motion.css")
        self.assertIn(".app.menu-open::after{opacity:.35}", css)
        self.assertIn("pointer-events:none", css[css.index(".app::after"):css.index(".app::after") + 200])

    def test_preview_fade_and_grid(self):
        css, js = rd("motion.css"), rd("motion.js")
        self.assertIn("fade-soft", js)
        i = css.index(".preview.fade-soft")
        self.assertIn("prefers-reduced-motion:no-preference", css[max(0, i - 80):i])
        self.assertIn("grid-template-columns var(--m-layout)", css)

    def test_hidden_sidebar_stale_and_demo(self):
        css, js = rd("motion.css"), rd("motion.js")
        self.assertIn("html[data-sidebar=hidden] .app.menu-open::after", css)
        self.assertIn(".row.stale", css)
        self.assertIn("stale", js)
        self.assertIn(".preview.demo", css)
        self.assertIn("data-k=motion", js)

    def test_tip_underline_key_status_jump(self):
        css, js = rd("motion.css"), rd("motion.js")
        self.assertIn(".nf-tips .tip:hover>span:first-child", css)
        self.assertIn("m-mark", css)
        self.assertIn("keystate", js)
        self.assertIn("jump-in", css)
        self.assertIn("jump-in", js)

    def test_slider_value_tick(self):
        self.assertIn("output.tick", rd("motion.css"))
        self.assertIn('t.type !== "range"', rd("motion.js"))


if __name__ == "__main__":
    unittest.main()
