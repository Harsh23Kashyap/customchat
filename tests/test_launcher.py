import tempfile,unittest,socket
from pathlib import Path
from customchat.launcher import workspace,pick_port
from customchat.schema import ConfigError,load
class LauncherTests(unittest.TestCase):
    def test_packaged_template_and_rerun(self):
        with tempfile.TemporaryDirectory() as tmp:
            app=workspace(Path(tmp)/'demo');self.assertEqual(load(str(app))['provider']['type'],'mock')
            self.assertTrue((app.parent/'docs/about.md').is_file())
            app.write_text('custom user content');self.assertEqual(workspace(app.parent).read_text(),'custom user content')
    def test_existing_directory_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ConfigError):workspace(tmp)
    def test_busy_port_fallback(self):
        with socket.socket() as s:
            s.bind(('127.0.0.1',0));port=s.getsockname()[1]
            if port<=65515:self.assertNotEqual(pick_port(port),port)
    def test_bad_port(self):
        with self.assertRaises(ConfigError):pick_port(65535)
if __name__=='__main__':unittest.main()

class InstalledStartTests(unittest.TestCase):
    def test_locked_start_sets_flag_before_server_import(self):
        import inspect
        from customchat.launcher import start
        source=inspect.getsource(start)
        self.assertLess(source.index('if lock_config:'),source.index('from .server import serve'))
