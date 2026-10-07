#!/usr/bin/env python3
"""Make a private local SQLite state snapshot. Stop app writes for multi-file consistency."""
import argparse, json, os, shutil, sqlite3, sys
from pathlib import Path

def backup(state, destination):
    root=Path(state).absolute();out=Path(destination).absolute()
    if not root.is_dir() or root.is_symlink() or root.resolve()!=root:raise ValueError('State must be an existing non-symlink directory')
    if root==out or root in out.parents:raise ValueError('Snapshot destination must be outside the state folder')
    if out.exists():raise ValueError('Snapshot destination already exists')
    files=[]
    for p in root.rglob('*'):
        if p.is_symlink():raise ValueError('State snapshot refuses symlinks')
        if p.is_file() and not p.name.endswith(('-wal','-shm','-journal')):files.append(p)
    out.mkdir(mode=0o700,parents=True)
    try:
        for p in files:
            target=out/p.relative_to(root);target.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
            if p.suffix=='.db':
                source=sqlite3.connect('file:'+str(p)+'?mode=ro',uri=True);dest=sqlite3.connect(target)
                try:
                    source.backup(dest)
                    if dest.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('SQLite snapshot integrity failed')
                finally:source.close();dest.close()
            else:shutil.copyfile(p,target)
            target.chmod(0o600)
        (out/'snapshot.json').write_text(json.dumps({'files':[p.relative_to(root).as_posix() for p in files],'private':True,'stop_writes_required_for_cross_file_consistency':True},indent=2))
        (out/'snapshot.json').chmod(0o600)
    except Exception:
        shutil.rmtree(out);raise
    return len(files)

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('state');ap.add_argument('destination');ap.add_argument('--writes-stopped',action='store_true');a=ap.parse_args()
    if not a.writes_stopped:sys.exit('Stop app writes first and pass --writes-stopped. Snapshot contains keys/accounts; never share it.')
    try:print('Private snapshot:',backup(a.state,a.destination),'files')
    except (ValueError,OSError,sqlite3.Error) as e:sys.exit('Snapshot stopped: '+str(e))
