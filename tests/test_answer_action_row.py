from pathlib import Path
import unittest

class AnswerActionRow(unittest.TestCase):
    def test_feedback_controls_removed_without_losing_answer_actions(self):
        script = (Path(__file__).resolve().parents[1] / 'customchat/web/app.js').read_text()
        turn = script.split('function turnView(t, prev) {', 1)[1].split('async function branchQuestion', 1)[0]
        for label in ['Helpful', 'Not helpful', '/api/rate']:
            self.assertNotIn(label, turn)
        for label in ['"Copy"', '"More"', '"Context"', '"Markdown"', '"PDF"']:
            self.assertIn(label, turn)

    def test_sidebar_toggle_handles_docked_and_overlay_modes(self):
        web = Path(__file__).resolve().parents[1] / 'customchat/web'
        script = (web / 'app.js').read_text()
        for code in ['sidebarOverlay() ? "menu-open" : "side-collapsed"', '"aria-expanded"', '"aria-controls", "side"', '$("#side").inert = !open']:
            self.assertIn(code, script)
        self.assertIn('.app.side-collapsed.src', (web / 'style.css').read_text())

    def test_temporary_transition_and_empty_chat_start_at_top(self):
        script = (Path(__file__).resolve().parents[1] / 'customchat/web/app.js').read_text()
        self.assertIn('$("#tempPill").addEventListener("click", toggleTemp)', script)
        self.assertIn('S.temp ? "Temporary chat"', script)
        self.assertIn('PREVIEW || !S.turns.length ? 0', script)
