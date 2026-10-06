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


if __name__ == "__main__":
    unittest.main()
