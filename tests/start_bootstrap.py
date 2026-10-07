"""Run the README bootstrap with no uv, Python, Git or host package access."""
import json, os, shutil, subprocess, tempfile, time, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    with tempfile.TemporaryDirectory(prefix='cc fresh laptop ') as tmp:
        base=Path(tmp);home=base/'new home';home.mkdir();bins=base/'system tools';bins.mkdir()
        if os.name!='nt':
            for name in ('realpath','ldd','sha256sum','sh','curl','uname','mktemp','rm','mkdir','chmod','mv','cp','tar','gzip','cat','sed','grep','head','tail','sort','cut','tr','dirname','basename','readlink','ln','rmdir','touch','wc','date','which','env','awk','find','ls','xargs','install'):
                exe=shutil.which(name)
                if exe:(bins/name).symlink_to(exe)
            cmd=[str(bins/'sh'),str(ROOT/'start.sh')]
            path=str(bins)
        else:
            path=os.pathsep.join(p for p in os.environ['PATH'].split(os.pathsep) if not any(shutil.which(n,path=p) for n in ('uv','uvx','python','python3','git')))
            shell=shutil.which('powershell',path=path) or shutil.which('pwsh',path=path)
            assert shell,'PowerShell required'
            cmd=[shell,'-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'start.ps1')]
        env={k:v for k,v in os.environ.items() if not k.upper().startswith(('PYTHON','UV_','XDG_')) and k.upper()!='PSMODULEPATH'}
        env.update(HOME=str(home),USERPROFILE=str(home),PATH=path,UV_CACHE_DIR=str(home/'cache'),UV_PYTHON_INSTALL_DIR=str(home/'python'))
        assert all(shutil.which(n,path=path) is None for n in ('uv','uvx','python','python3','git'))
        if not os.environ.get('CUSTOMCHAT_TEST_REMOTE'):
            env['CUSTOMCHAT_INSTALL_SOURCE']=str(next((ROOT/'dist').glob('*.whl')).resolve())
        work=base/'my workspace';work.mkdir()
        with open(base/'run.log','w+') as log:
            proc=subprocess.Popen(cmd+['--no-browser','--lock-config','--port','18750'],cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT)
            try:
                url=None
                for _ in range(900):
                    if proc.poll() is not None:raise AssertionError((base/'run.log').read_text())
                    for line in (base/'run.log').read_text().splitlines():
                        if line.startswith('Starting CustomChat at '):url=line.split()[3]
                    if url:break
                    time.sleep(.2)
                assert url,(base/'run.log').read_text()
                with urllib.request.urlopen(url+'/api/health') as r:assert r.status==200
                req=urllib.request.Request(url+'/api/ask',data=b'{"question":"What is CustomChat?"}',headers={'Content-Type':'application/json'})
                with urllib.request.urlopen(req) as r:answer=json.load(r)
                assert answer['evidence'] and '[1]' in answer['answer'],answer
                assert (home/'.local/bin'/('uv.exe' if os.name=='nt' else 'uv')).exists()
                print((base/'run.log').read_text());print('Fresh laptop bootstrap passed: no uv/Python/Git, empty cache, health 200, cited Demo.')
            finally:
                proc.terminate()
                try:proc.wait(timeout=10)
                except subprocess.TimeoutExpired:proc.kill();proc.wait()
if __name__=='__main__':main()
