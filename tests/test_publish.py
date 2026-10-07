import os,stat,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class PublishTests(unittest.TestCase):
    def test_executable(self):
        self.assertTrue((ROOT/'deploy/publish.sh').stat().st_mode & stat.S_IXUSR)
    def test_dry_run_no_external_commands(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);calls=p/'calls'
            for name in ['ssh','rsync','aws','python3']:
                f=p/name;f.write_text('#!/bin/sh\necho '+name+' >> '+str(calls)+'\nexit 1\n');f.chmod(0o755)
            config=p/'config';config.write_text('EC2_HOST=example.invalid\nSSH_KEY=/tmp/no-key\nS3_BACKUP=s3://example.invalid\n')
            env=dict(os.environ,PATH=str(p)+':'+os.environ['PATH'],PUBLISH_ENV=str(config))
            r=subprocess.run([str(ROOT/'deploy/publish.sh')],cwd=ROOT,env=env,text=True,capture_output=True)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertIn('/opt/customchat/apps/dietchat/data',r.stdout)
            self.assertIn('not MySQL',r.stdout)
            self.assertFalse(calls.exists())
    def test_failed_backup_stops_before_copy(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);calls=p/'calls'
            for name,code in [('python3',0),('ssh',7),('rsync',0)]:
                f=p/name;f.write_text('#!/bin/sh\necho '+name+' >> '+str(calls)+'\nexit '+str(code)+'\n');f.chmod(0o755)
            config=p/'config';config.write_text('EC2_HOST=example.invalid\nSSH_KEY=/tmp/no-key\nS3_BACKUP=s3://example.invalid\n')
            r=subprocess.run([str(ROOT/'deploy/publish.sh'),'--yes'],cwd=ROOT,env=dict(os.environ,PATH=str(p)+':'+os.environ['PATH'],PUBLISH_ENV=str(config)),capture_output=True,text=True)
            self.assertEqual(r.returncode,7)
            self.assertEqual(calls.read_text().splitlines(),['python3','ssh'])
    def test_no_unused_app_file_option(self):
        self.assertNotIn('APP_FILE',(ROOT/'deploy/publish.sh').read_text())
        self.assertNotIn('APP_FILE',(ROOT/'deploy/publish.env.example').read_text())
if __name__=='__main__':unittest.main()
