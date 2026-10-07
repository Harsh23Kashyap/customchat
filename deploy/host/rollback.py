#!/usr/bin/env python3
"""Select an existing prepared code release. Does not start services or restore private data."""
import argparse, os, re
from pathlib import Path

def select(releases, current, name):
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',name):raise ValueError('Release name must be a plain folder name')
    root=Path(releases).absolute();target=root/name;link=Path(current).absolute()
    if root.is_symlink() or target.is_symlink() or not target.is_dir():raise ValueError('Release must be an existing non-symlink folder')
    if not (target/'.venv/bin/python').is_file() or not (target/'customchat').is_dir():raise ValueError('Release is missing code or its prebuilt Python environment')
    if link.exists() and not link.is_symlink():raise ValueError('Current must be a symlink, never a real directory')
    tmp=link.with_name(link.name+'.next')
    if tmp.exists() or tmp.is_symlink():raise ValueError('Pending release link exists')
    tmp.symlink_to(target);os.replace(tmp,link)
    return str(target)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('releases');p.add_argument('current');p.add_argument('name');p.add_argument('--apply',action='store_true');a=p.parse_args()
    if not a.apply:print('Plan only. Stop app writes; back up state; add --apply to switch code. Restart/health/data restore are separate.')
    else:print('Selected code:',select(a.releases,a.current,a.name),'Restart and verify health separately.')
