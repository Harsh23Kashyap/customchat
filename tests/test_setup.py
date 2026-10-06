import os, socket, sys, tempfile, unittest
sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")]
import setup_and_run as S

class T(unittest.TestCase):
    def test_port_helpers(self):
        s = socket.socket(); s.bind(("127.0.0.1", 0)); s.listen(1); p = s.getsockname()[1]
        try:
            self.assertFalse(S.port_free(p)); self.assertNotEqual(S.pick_port(p), p)
        finally: s.close()
        self.assertTrue(S.port_free(p))
    def test_req_hash_ignores_mtime(self):
        f = tempfile.NamedTemporaryFile(delete=False); f.write(b"PyYAML\n"); f.close()
        a = S.req_hash(f.name); os.utime(f.name, (1, 1)); self.assertEqual(a, S.req_hash(f.name)); os.unlink(f.name)
    def test_wsl_detect(self):
        self.assertIsInstance(S.is_wsl(), bool)
    def test_venv_python_path(self):
        self.assertTrue(S.venv_python().endswith(("bin/python", "Scripts\\python.exe")))
    def test_check_reports_without_changing_anything(self):
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = S.check(os.path.join(S.ROOT, "apps", "minimal", "app.yaml"))
        out = buf.getvalue(); self.assertIn("Python", out); self.assertIn(code, (0, 1))
    def test_ask_key_survives_closed_input(self):
        old = S.input if hasattr(S, "input") else None
        import builtins
        orig = builtins.input
        def eof(*a): raise EOFError
        builtins.input = eof
        try:
            import os, tempfile
            os.environ.pop("OPENAI_API_KEY", None); os.environ.pop("ANTHROPIC_API_KEY", None); os.environ.pop("GEMINI_API_KEY", None); os.environ.pop("DEEPSEEK_API_KEY", None)
            S.ask_key(os.path.join(tempfile.mkdtemp(), "app.yaml"))
        finally:
            builtins.input = orig
if __name__ == "__main__": unittest.main()
