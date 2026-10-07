import tempfile,unittest,os
from pathlib import Path
from customchat.configchange import diff,apply,digest
from customchat.schema import ConfigError,validate
class ConfigChange(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.a=Path(self.t.name)/'app.yaml';self.b=Path(self.t.name)/'candidate.yaml'
  self.a.write_text('# preserve me\napp: {title: Old}\n');self.b.write_text('# candidate\napp: {title: New}\nauth: {mode: accounts}\n')
 def test_diff_no_values(self):
  d=diff(self.a,self.b);self.assertNotIn('New',str(d));self.assertEqual({x['key'] for x in d['changes']},{'app.title','auth.mode'})
 def test_apply_backup_rollback(self):
  old=self.a.read_bytes();d=diff(self.a,self.b);backup=Path(apply(self.a,self.b,d['current_sha256'],d['candidate_sha256']))
  self.assertEqual(backup.read_bytes(),old);self.assertEqual(self.a.read_bytes(),self.b.read_bytes());self.assertEqual(backup.stat().st_mode&0o777,0o600)
  d=diff(self.a,backup);apply(self.a,backup,d['current_sha256'],d['candidate_sha256']);self.assertEqual(self.a.read_bytes(),old)
 def test_current_stale(self):
  d=diff(self.a,self.b);self.a.write_text('{}')
  with self.assertRaises(ConfigError):apply(self.a,self.b,d['current_sha256'],d['candidate_sha256'])
 def test_candidate_stale(self):
  d=diff(self.a,self.b);self.b.write_text('{}')
  with self.assertRaises(ConfigError):apply(self.a,self.b,d['current_sha256'],d['candidate_sha256'])
 def test_invalid_candidate_no_backup(self):
  self.b.write_text('unknown: yes')
  with self.assertRaises(ConfigError):apply(self.a,self.b,digest(self.a),digest(self.b))
  self.assertEqual(len(list(self.a.parent.glob('*.backup-*'))),0)
 def test_symlink_target(self):
  link=self.a.parent/'link.yaml';link.symlink_to(self.a)
  with self.assertRaises(ConfigError):apply(link,self.b,digest(link),digest(self.b))
 def test_schema_version(self):
  self.assertEqual(validate({})['schema_version'],1)
  for version in [True,2,'1']:
   with self.assertRaises(ConfigError):validate({'schema_version':version})
 def test_defaults_not_reported(self):
  self.b.write_text('# version\nschema_version: 1\napp: {title: Old}\n');self.assertEqual(diff(self.a,self.b)['changes'],[])
