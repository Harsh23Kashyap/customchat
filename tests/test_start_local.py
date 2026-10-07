import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('start_local', Path(__file__).parents[1] / 'start_local.py')
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)


class LocalStartTests(unittest.TestCase):
    def test_private_install_and_args_preserve_spaces(self):
        with tempfile.TemporaryDirectory(prefix='chat with spaces ') as tmp:
            script = Path(tmp) / 'start_local.py'
            with patch.object(S, '__file__', str(script)), patch.object(S.venv, 'EnvBuilder') as builder, patch.object(S.subprocess, 'run') as run, patch.object(S.subprocess, 'call', return_value=0) as call:
                def create(folder):
                    python = Path(folder) / 'bin/python'
                    python.parent.mkdir(parents=True)
                    python.touch()
                builder.return_value.create.side_effect = create
                self.assertEqual(S.main(['--directory', 'my chat', '--no-browser']), 0)
                command = run.call_args_list[-1].args[0]
                self.assertIn('--isolated', command)
                self.assertIn('https://pypi.org/simple', command)
                self.assertIn('customchat-app==0.1.5', command)
                self.assertIn('-I', command)
                self.assertNotIn('--break-system-packages', command)
                self.assertEqual(call.call_args.args[0][-3:], ['--directory', 'my chat', '--no-browser'])
                S.main([])
                self.assertEqual(builder.return_value.create.call_count, 1)

    def test_incomplete_env_not_reset(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / '.customchat-venv'
            folder.mkdir()
            marker = folder / 'keep'
            marker.write_text('do not delete')
            with patch.object(S, '__file__', str(Path(tmp) / 'start_local.py')), patch.object(S.subprocess, 'call') as call:
                with self.assertRaisesRegex(SystemExit, 'incomplete'):
                    S.main([])
                self.assertEqual(marker.read_text(), 'do not delete')
                call.assert_not_called()

    def test_install_failure_does_not_launch(self):
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            python = Path(tmp) / '.customchat-venv/bin/python'
            python.parent.mkdir(parents=True)
            python.touch()
            with patch.object(S, '__file__', str(Path(tmp) / 'start_local.py')), patch.object(S.subprocess, 'run', side_effect=[None, subprocess.CalledProcessError(1, 'pip')]), patch.object(S.subprocess, 'call') as call:
                with self.assertRaisesRegex(SystemExit, 'Setup stopped'):
                    S.main([])
                call.assert_not_called()
