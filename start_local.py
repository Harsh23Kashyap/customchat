#!/usr/bin/env python3
"""Create an isolated environment, install public CustomChat, and start it."""
import os
from pathlib import Path
import subprocess
import sys
import venv

VERSION = '0.1.5'


def main(args=None):
    args = list(sys.argv[1:] if args is None else args)
    if sys.version_info < (3, 10):
        raise SystemExit('Needs Python 3.10 or newer. On macOS: brew install python')
    folder = Path(__file__).resolve().parent / '.customchat-venv'
    python = folder / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    env = dict(os.environ)
    # Keep package imports and pip isolated from shell-level Python settings.
    for name in ('PYTHONPATH', 'PYTHONHOME', 'PIP_TARGET', 'PIP_PREFIX', 'PIP_USER'):
        env.pop(name, None)
    if not folder.exists():
        print('Creating private .customchat-venv (system Python stays unchanged).', flush=True)
        try:
            venv.EnvBuilder(with_pip=True).create(str(folder))
        except Exception as exc:
            raise SystemExit('Could not create the environment: %s. No app data was changed.' % exc)
    if not python.is_file():
        raise SystemExit('Existing .customchat-venv is incomplete. Rename it and retry. No files were deleted.')
    try:
        subprocess.run([str(python), '-I', '-c', 'import sys; assert sys.prefix != sys.base_prefix'],
                       check=True, env=env)
        print('Installing CustomChat %s from public PyPI into the private environment.' % VERSION, flush=True)
        subprocess.run([str(python), '-I', '-m', 'pip', '--isolated', 'install',
                        '--disable-pip-version-check', '--index-url', 'https://pypi.org/simple',
                        '--upgrade', 'customchat-app==' + VERSION], check=True, env=env)
        return subprocess.call([str(python), '-I', '-m', 'customchat', 'start'] + args, env=env)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit('Setup stopped: %s. Check the message above and retry; app files are untouched.' % exc)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)
