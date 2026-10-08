import os, subprocess, sys, time, unittest, urllib.request, urllib.error
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

def code(port, path):
    try: return urllib.request.urlopen("http://127.0.0.1:%d%s" % (port, path), timeout=3).status
    except urllib.error.HTTPError as e: return e.code
    except (urllib.error.URLError, ConnectionError, OSError): return 0

class T(unittest.TestCase):
    def test_locked_server(self):
        port = 8247
        p = subprocess.Popen([sys.executable, "-m", "customchat", "run", "apps/minimal/app.yaml", "--port", str(port)], cwd=ROOT,
                             env=dict(os.environ, CUSTOMCHAT_CONFIG="off", PYTHONPATH=ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            for _ in range(30):
                if code(port, "/api/health") == 200: break
                time.sleep(0.3)
            self.assertEqual(code(port, "/"), 200); self.assertEqual(code(port, "/api/health"), 200)
            for path in ("/settings.html", "/settings.js", "/api/settings", "/api/provider/status", "/api/prompts", "/api/workspace/status", "/workspace.js"):
                self.assertEqual(code(port, path), 404, path)
            self.assertNotIn(b"Configuration", urllib.request.urlopen("http://127.0.0.1:%d/" % port).read())
        finally: p.terminate()
if __name__ == "__main__": unittest.main()
