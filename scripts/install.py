#!/usr/bin/env python3
"""Shared local installer. Invoked by OS scripts after uv/Python bootstrap."""
import argparse,contextlib,json,os,shutil,subprocess,sys,time,urllib.request
from pathlib import Path
RELEASE='08ab51591a43edf382080add86e8eacbaff0e9cf'
SOURCE='https://github.com/Harsh23Kashyap/customchat/archive/'+RELEASE+'.zip'

def healthy(url):
    try:
        with urllib.request.urlopen(url+'/api/health',timeout=1) as r:return r.status==200
    except Exception:return False

@contextlib.contextmanager
def locked(path):
    f=open(path,'a+b');f.seek(0);f.write(b'0');f.flush();f.seek(0)
    try:
        if os.name=='nt':
            import msvcrt;msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl;fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except OSError:
        f.close();raise SystemExit('Another installer is active. Wait for it to finish; no state changed.')
    try:yield
    finally:
        if os.name=='nt':
            import msvcrt;f.seek(0);msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)
        f.close()

def run(args):
    root=Path(args.state).expanduser().resolve();root.mkdir(parents=True,exist_ok=True)
    uv=args.uv or shutil.which('uv')
    if not uv:raise SystemExit('uv bootstrap missing; use install.sh or install.ps1.')
    py=root/'venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    source=args.source or SOURCE
    receipt=root/'installed.json'
    env=dict(os.environ)
    if args.offline:env['UV_OFFLINE']='1'
    def command(*parts):subprocess.run([uv,*map(str,parts)],check=True,env=env)
    active=root/'server.json'
    if active.exists():
        try:
            state=json.loads(active.read_text())
            if healthy(state['url']):
                print('Already running at '+state['url']+'; no duplicate server started.',flush=True);return
        except (ValueError,KeyError):pass
    with locked(root/'install.lock'):
        valid=False
        if py.exists():
            try:valid=subprocess.run([str(py),'-c','import customchat.launcher,yaml'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
            except OSError:pass
        same=False
        try:same=json.loads(receipt.read_text()).get('source')==source
        except (OSError,ValueError):pass
        if valid and same:print('Environment and dependencies already ready; skipped.',flush=True)
        else:
            if not valid:
                print('Creating or repairing private environment.',flush=True)
                # Only this installer-owned venv is removed. User workspace is separate.
                shutil.rmtree(root/'venv',ignore_errors=True)
                command('venv','--python',sys.executable,root/'venv')
            print('Installing app and dependencies.',flush=True)
            command('pip','install','--python',py,source)
            subprocess.run([str(py),'-c','import customchat.launcher,yaml'],check=True)
            temp=receipt.with_suffix('.tmp');temp.write_text(json.dumps(dict(source=source)));temp.replace(receipt)
        if args.prepare_only:return
        # Holding the lock for server lifetime makes repeated invocations safe.
        log=root/'server.log'
        cmd=[str(py),'-m','customchat','start','--directory',str(Path(args.directory).expanduser().resolve()),'--port',str(args.port)]
        if args.no_browser:cmd.append('--no-browser')
        if args.lock_config:cmd.append('--lock-config')
        with open(log,'w') as out:
            child=subprocess.Popen(cmd,stdout=out,stderr=subprocess.STDOUT)
        try:
            url=None
            for _ in range(150):
                if child.poll() is not None:raise RuntimeError(log.read_text())
                for line in log.read_text().splitlines():
                    if line.startswith('Starting CustomChat at '):url=line.split()[3]
                if url and healthy(url):break
                time.sleep(.2)
            else:raise RuntimeError('App did not report ready; inspect '+str(log))
            active.write_text(json.dumps(dict(pid=child.pid,url=url)))
            print('Starting CustomChat at '+url+' (Ctrl+C to stop)',flush=True)
            print('Workspace: '+str(Path(args.directory).expanduser().resolve()),flush=True)
            if args.verify_and_stop:
                with urllib.request.urlopen(url+'/api/config',timeout=3) as response:
                    cfg=json.load(response)
                request=urllib.request.Request(url+'/api/ask',data=b'{"question":"What is CustomChat?"}',headers={'Content-Type':'application/json'})
                with urllib.request.urlopen(request,timeout=5) as response:answer=json.load(response)
                if cfg['provider']['type']!='mock' or not answer.get('evidence') or '[1]' not in answer.get('answer',''):
                    raise RuntimeError('Demo acceptance failed')
                print('Verified health200, mock provider and cited Demo answer.',flush=True)
                return
            if args.stop_after_seconds:
                try:child.wait(timeout=args.stop_after_seconds)
                except subprocess.TimeoutExpired:return
            else:child.wait()
            if child.returncode:raise RuntimeError('App stopped with code '+str(child.returncode))
        finally:
            child.terminate()
            try:child.wait(timeout=10)
            except subprocess.TimeoutExpired:child.kill()
            active.unlink(missing_ok=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--state',default=str(Path.home()/'.customchat/install'))
    p.add_argument('--directory',default='customchat-app');p.add_argument('--uv');p.add_argument('--source')
    p.add_argument('--port',type=int,default=8080);p.add_argument('--offline',action='store_true')
    p.add_argument('--verify-and-stop',action='store_true');p.add_argument('--stop-after-seconds',type=int,default=0,help=argparse.SUPPRESS)
    p.add_argument('--prepare-only',action='store_true');p.add_argument('--no-browser',action='store_true');p.add_argument('--lock-config',action='store_true')
    try:run(p.parse_args())
    except KeyboardInterrupt:print('Stopped.')
    except (subprocess.CalledProcessError,RuntimeError) as e:raise SystemExit('Setup stopped: '+str(e)+'. Rerun to resume; your workspace is retained.')
if __name__=='__main__':main()
