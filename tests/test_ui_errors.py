import os, unittest
W = os.path.join(os.path.dirname(__file__), "..", "customchat", "web")


class UiErrors(unittest.TestCase):
    """Static checks for the browser's error handling. The live behaviour was checked in headless Chrome
    with the stream request aborted, answered with HTTP 500, answered with a JSON error, and cut short."""
    def setUp(self): self.js = open(os.path.join(W, "app.js"), encoding="utf-8").read()

    def test_plain_messages_not_browser_text(self):
        self.assertIn("Could not reach the app", self.js)
        self.assertIn("The app returned an error (HTTP", self.js)
        self.assertIn("The answer was cut short", self.js)

    def test_unreadable_stream_lines_are_skipped(self):
        self.assertIn("try { ev = JSON.parse(line); } catch (e) { continue; }", self.js)

    def test_question_and_partial_text_are_kept(self):
        self.assertIn("$(\"#q\").value = q", self.js)
        self.assertIn("Cut short. Click the notice to ask again.", self.js)


if __name__ == "__main__": unittest.main()
