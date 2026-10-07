"""Real official bootstrap in a disposable home, with uv removed from PATH."""
import os,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    wheel=next((ROOT/'dist').glob('*.whl')).resolve()
    with tempfile.TemporaryDirectory(prefix='cc absent uv ') as tmp:
        home=Path(tmp)/'new home';home.mkdir()
        env=dict(os.environ)
        env.update(HOME=str(home),USERPROFILE=str(home),UV_CACHE_DIR=str(home/'cache'))
        for key in ('UV_INSTALL_DIR','UV_UNMANAGED_INSTALL','XDG_BIN_HOME','XDG_DATA_HOME','UV_OFFLINE','PYTHONPATH'):
            env.pop(key,None)
        # Remove any PATH directory exposing uv, not the Python/shell/runtime tools.
        paths=[p for p in env['PATH'].split(os.pathsep) if p and os.access(p,os.X_OK) and not shutil.which('uv',path=p)]
        env['PATH']=os.pathsep.join(paths)
        assert shutil.which('uv',path=env['PATH']) is None
        assert not (home/'.local/bin/uv').exists() and not (home/'.local/bin/uv.exe').exists()
        opts=['--source',str(wheel),'--state',str(home/'private state'),'--directory',str(home/'my workspace'),'--no-browser','--lock-config','--verify-and-stop']
        if os.name=='nt':
            shell=shutil.which('powershell',path=env['PATH']);assert shell
            cmd=[shell,'-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'install.ps1'),*opts]
        else:cmd=['sh',str(ROOT/'install.sh'),*opts]
        result=subprocess.run(cmd,cwd=home,env=env,text=True,capture_output=True,timeout=300)
        print(result.stdout,flush=True);print(result.stderr,flush=True)
        assert result.returncode==0
        assert 'Installing uv from its official installer.' in result.stdout
        assert 'Verified health200, mock provider and cited Demo answer.' in result.stdout
        assert (home/'.local/bin'/('uv.exe' if os.name=='nt' else 'uv')).exists()
        print('Real absent-uv bootstrap, isolated HOME, spaced paths, wheel install, health and cited Demo passed.')
if __name__=='__main__':main()
