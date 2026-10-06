import os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from customchat.store import Store
from customchat.pipeline import Engine
from customchat import providers

EV = [{"n": 1, "title": "A", "text": "First passage about refunds."}, {"n": 2, "title": "B", "text": "x " * 400}]

class T(unittest.TestCase):
    def test_damaged_data_file_is_set_aside(self):
        d = tempfile.mkdtemp(); p = os.path.join(d, "customchat.db")
        open(p, "wb").write(os.urandom(200))
        s = Store(p)
        self.assertEqual(s.q("select count(*) c from sqlite_master where name='turns'", one=True)["c"], 1)
        self.assertTrue(any(".corrupt-" in f for f in os.listdir(d)))
    def test_fallback_answer_cites_passages(self):
        a = Engine.fallback_answer(EV)
        self.assertIn("could not be reached", a); self.assertIn("[1]", a); self.assertIn("[2]", a); self.assertLess(len(a), 1200)
    def test_fallback_answer_with_no_evidence(self):
        self.assertIn("could not be reached", Engine.fallback_answer([]))
if __name__ == "__main__": unittest.main()
