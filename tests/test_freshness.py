import os, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from customchat import schema
from customchat.connectors.local_files import LocalFiles
from customchat.pipeline import Engine
from customchat.store import Store

class FreshnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.docs=self.root/'docs';self.docs.mkdir()
        self.file=self.docs/'doc.md';self.file.write_text('# Fruit\nApple nutrition facts old.')
        self.cfg=schema.validate({'sources':[{'id':'docs','type':'local_files','path':'docs','refresh_interval':0}]});self.cfg['_dir']=str(self.root)
        self.engine=Engine(self.cfg,Store(':memory:'));self.conn=self.engine.connectors['docs']
    def test_edit_invalidates_same_question_cache(self):
        one,_=self.engine.retrieve('apple');self.file.write_text('# Fruit\nApple nutrition facts new.')
        two,_=self.engine.retrieve('apple');self.assertIn('new',two[0]['text']);self.assertNotEqual(one[0]['version'],two[0]['version'])
    def test_add_and_remove(self):
        self.engine.retrieve('apple');other=self.docs/'pear.txt';other.write_text('Pear nutrition.')
        found,_=self.engine.retrieve('pear');self.assertTrue(found)
        other.unlink();found,_=self.engine.retrieve('pear');self.assertFalse(found)
    def test_same_size_mtime_edit(self):
        before=self.file.stat();old=self.conn.revision;self.file.write_text('# Fruit\nApple nutrition facts new.');os.utime(self.file,ns=(before.st_atime_ns,before.st_mtime_ns))
        self.conn.refresh();self.assertNotEqual(old,self.conn.revision)
    def test_missing_folder_no_stale_answer(self):
        self.engine.retrieve('apple');self.file.unlink();self.docs.rmdir()
        found,errors=self.engine.retrieve('apple');self.assertFalse(found);self.assertIn('docs',errors)
        self.docs.mkdir();self.file.write_text('Apple recovered.')
        found,errors=self.engine.retrieve('apple');self.assertTrue(found);self.assertFalse(errors)
    def test_atomic_failed_scan(self):
        old=self.conn.revision
        with patch.object(self.conn,'_scan',side_effect=OSError):
            with self.assertRaises(OSError):self.conn.refresh()
        self.assertEqual(old,self.conn.revision);self.assertTrue(self.conn.last_error)
    def test_no_change(self):
        old=self.conn.indexed_at;self.assertFalse(self.conn.refresh());self.assertEqual(old,self.conn.indexed_at)
    def test_interval_and_force(self):
        self.conn.refresh_interval=86400;self.file.write_text('Apple changed.')
        self.assertFalse(self.conn.refresh());self.assertTrue(self.conn.refresh(force=True))
    def test_symlink(self):
        (self.docs/'link.txt').symlink_to(self.file)
        with self.assertRaises(OSError):self.conn.refresh()
    def test_missing_at_startup(self):
        self.file.unlink(); self.docs.rmdir()
        conn=LocalFiles(self.cfg['sources'][0],str(self.root))
        self.assertTrue(conn.last_error)
        with self.assertRaises(OSError):conn.search('apple')
        self.docs.mkdir();self.file.write_text('Apple restored.')
        self.assertTrue(conn.search('apple'))
    def test_invalid_interval(self):
        for v in (-1,True,'fast',86401):
            with self.assertRaises(schema.ConfigError):schema.validate({'sources':[{'type':'local_files','refresh_interval':v}]})
    def test_version_metadata(self):
        found=self.conn.search('apple');self.assertEqual(found[0]['document'],'doc.md');self.assertEqual(len(found[0]['version']),64)
if __name__=='__main__':unittest.main()
