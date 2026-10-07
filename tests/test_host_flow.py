import importlib.util, os, sqlite3, subprocess, sys, tempfile, time, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def module(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'deploy/host'/f'{name}.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
class HostFlow(unittest.TestCase):
    def test_prepare_no_side_effect(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);app=root/'app.yaml';app.write_text('auth: {mode: token, token_env: CHAT_ACCESS}\n')
            files=module('prepare').prepare(app,root/'plan','chat.example.invalid','/opt/customchat/current','/var/lib/customchat/app','customchat','/opt/customchat/current/.venv/bin/python')
            self.assertIn('reverse_proxy 127.0.0.1:8100',files['Caddyfile']);self.assertIn('CUSTOMCHAT_CONFIG=off',files['customchat.service'])
            self.assertNotIn(os.environ.get('CHAT_ACCESS','unused-secret-sentinel'),files['customchat.env.example'])
            self.assertEqual((root/'plan/customchat.env.example').stat().st_mode&0o777,0o600)
            with self.assertRaises(FileExistsError):module('prepare').prepare(app,root/'plan','chat.example.invalid','/opt/current','/var/lib/app','customchat','/opt/python')
    def test_preflight_rejects_unsafe(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);app=root/'app.yaml';app.write_text('auth: {mode: none}\n')
            with self.assertRaises(ValueError):module('prepare').prepare(app,root/'plan','chat.example.invalid','/opt/current','/var/lib/app','customchat','/opt/python')
            app.write_text('auth: {mode: token, token_env: CHAT_ACCESS}\n')
            for domain in ('https://bad.invalid','x.invalid\nmalicious','127.0.0.1'):
                with self.assertRaises(ValueError):module('prepare').prepare(app,root/'plan',domain,'/opt/current','/var/lib/app','customchat','/opt/python')
    def test_backup_sqlite_and_secret_permissions(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);state=root/'state';state.mkdir();c=sqlite3.connect(state/'customchat.db');c.execute('CREATE TABLE example(x)');c.execute('INSERT INTO example VALUES(42)');c.commit();c.close()
            (state/'secrets.json').write_text('{"EXAMPLE":"local-test-only"}')
            module('backup').backup(state,root/'snapshot')
            c=sqlite3.connect(root/'snapshot/customchat.db');self.assertEqual(c.execute('SELECT x FROM example').fetchone()[0],42);c.close()
            self.assertEqual((root/'snapshot/secrets.json').stat().st_mode&0o777,0o600)
            with self.assertRaises(ValueError):module('backup').backup(state,state/'bad')
    def test_rollback(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);release=root/'releases'/'v1';(release/'.venv/bin').mkdir(parents=True);(release/'customchat').mkdir();(release/'.venv/bin/python').write_text('test')
            link=root/'current';module('rollback').select(root/'releases',link,'v1');self.assertEqual(link.resolve(),release)
            with self.assertRaises(ValueError):module('rollback').select(root/'releases',link,'../bad')
    def test_actual_locked_health(self):
        port=8255
        p=subprocess.Popen([sys.executable,'-m','customchat','run','apps/minimal/app.yaml','--port',str(port)],cwd=ROOT,env=dict(os.environ,CUSTOMCHAT_CONFIG='off'),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            for _ in range(40):
                try:module('health').verify(port);break
                except Exception:time.sleep(.1)
            else:self.fail('No healthy locked local server')
        finally:p.terminate();p.wait()
if __name__=='__main__':unittest.main()
