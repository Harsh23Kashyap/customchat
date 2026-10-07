import io, json, os, tempfile, unittest, zipfile
from pathlib import Path
from customchat import schema
from customchat.portable import bundle, export_app, ExportError
from customchat.pipeline import Engine
from customchat.store import Store

class PortableTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name); (self.root/'docs').mkdir(); (self.root/'data').mkdir()
        (self.root/'docs'/'guide.md').write_text('# Guide\nCustomChat provides citation-backed answers.')
        self.cfg = schema.validate({'app': {'title': 'Portable demo'}, 'sources': [{'id':'docs','type':'local_files','path':'docs'}]})
        self.cfg['_dir'] = str(self.root)
    def test_roundtrip(self):
        (self.root/'.env').write_text('PORTABLE_TEST_SECRET=hidden-key')
        for n in ('secrets.json','customchat.db','accounts.json','uploads.json','states.json'):
            (self.root/'data'/n).write_text('DO_NOT_EXPORT')
        (self.root/'data'/'theme.json').write_text(json.dumps({'font':'georgia','txt_title':'Branded'}))
        (self.root/'data'/'prompts.json').write_text(json.dumps({'text':{'answer':'Use citations.'},'on':{'relevance':True}}))
        data, m = bundle(self.cfg)
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            self.assertEqual(set(z.namelist()), {'app.yaml','assets/source-1/guide.md','data/theme.json','data/prompts.json','manifest.json','README.txt'})
            self.assertNotIn(b'DO_NOT_EXPORT', b''.join(z.read(n) for n in z.namelist()))
            self.assertEqual(json.loads(z.read('data/theme.json'))['font'],'georgia')
            self.assertTrue(json.loads(z.read('data/prompts.json'))['on']['relevance'])
            z.extractall(self.root/'moved')
        cfg = schema.load(str(self.root/'moved'/'app.yaml'))
        self.assertEqual(cfg['app']['title'],'Portable demo')
        st = Store(':memory:'); e = Engine(cfg,st)
        res = e.ask('local',st.new_chat('local'),'What does CustomChat provide?')
        self.assertTrue(res['evidence'])
    def test_override_live_settings(self):
        data,_ = bundle(self.cfg, {'txt_title':'Live'}, {'text':{'answer':'Current'}, 'on':{}})
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            self.assertEqual(json.loads(z.read('data/prompts.json'))['text']['answer'],'Current')
    def test_secret_config(self):
        for block in ({'headers':{'Authorization':'secret'}}, {'url':'https://user:pass@example.com/a'}, {'url':'https://example.com/?token=secret'}):
            self.cfg['sources'].append(dict(type='http_json', id='remote', **block))
            with self.assertRaises(ExportError): bundle(self.cfg)
            self.cfg['sources'].pop()
    def test_private_source(self):
        for n in ('secrets.json','.env.txt','passwords.csv'):
            p = self.root/'docs'/n; p.write_text('secret')
            with self.assertRaises(ExportError): bundle(self.cfg)
            p.unlink()
    def test_symlink(self):
        p=self.root/'docs'/'linked.txt';p.symlink_to(self.root/'data'/'customchat.db')
        with self.assertRaises(ExportError): bundle(self.cfg)
    def test_external_root(self):
        self.cfg['sources'][0]['path']=str(self.root/'docs')
        _,m = bundle(self.cfg)
        self.assertIn('assets/source-1/guide.md',m['files'])
    def test_no_overwrite(self):
        p=self.root/'app.yaml';p.write_text('provider: {type: mock}\n')
        out=self.root/'app.zip';export_app(p,out)
        with self.assertRaises(FileExistsError): export_app(p,out)
    def test_mysql_removed(self):
        self.cfg['storage']['path']='mysql://user:password@localhost/db'
        with self.assertRaises(ExportError): bundle(self.cfg)
    def test_env_names_not_values(self):
        self.cfg['provider'].update(type='openai',model='gpt-4o-mini',api_key_env='MY_KEY')
        os.environ['MY_KEY']='not-in-export'
        data,m=bundle(self.cfg)
        self.assertEqual(m['required_env'],['MY_KEY']);self.assertNotIn(b'not-in-export',data)
    def test_private_state_source(self):
        self.cfg['sources'][0]['path']='data'
        with self.assertRaises(ExportError): bundle(self.cfg)
    def test_size_limit(self):
        import unittest.mock
        with unittest.mock.patch('customchat.portable.MAX_BYTES',1):
            with self.assertRaises(ExportError):bundle(self.cfg)
if __name__ == '__main__': unittest.main()

class ExportPermissions(unittest.TestCase):
    def test_permissions_and_lock(self):
        import threading, urllib.request, urllib.error
        from customchat import server
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as folder:
            cfg = schema.validate({'auth':{'mode':'token','token_env':'EXPORT_TEST_TOKEN'}, 'storage':{'path':':memory:'}});cfg['_dir']=folder
            engine=Engine(cfg,Store(':memory:'))
            srv=server.LocalHTTPServer(('127.0.0.1',0),server.make_handler(cfg,engine))
            th=threading.Thread(target=srv.serve_forever,daemon=True);th.start()
            url='http://127.0.0.1:%d/api/app-export'%srv.server_port
            try:
                with patch.dict(os.environ,{'EXPORT_TEST_TOKEN':'example-test-only'}):
                    with self.assertRaises(urllib.error.HTTPError) as err: urllib.request.urlopen(url)
                    self.assertEqual(err.exception.code,401)
                    req=urllib.request.Request(url,headers={'Authorization':'Bearer example-test-only'})
                    with urllib.request.urlopen(req) as r:self.assertEqual(r.headers['Content-Type'],'application/zip')
                    with patch.object(server,'LOCKED',True):
                        with self.assertRaises(urllib.error.HTTPError) as err:urllib.request.urlopen(req)
                        self.assertEqual(err.exception.code,404)
            finally:srv.shutdown();srv.server_close();th.join()
