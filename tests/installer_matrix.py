"""Real shared-installer scenario matrix, repeated10x. No cloud or model calls."""
import argparse,json,os,signal,socket,subprocess,sys,tempfile,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--wheel',required=True);ap.add_argument('--uv',default='uv');ap.add_argument('--repeat',type=int,default=10);args=ap.parse_args()
    counts={k:0 for k in ['fresh','already_installed','partial_receipt','broken_venv','offline_rerun','occupied_port','active_rerun','concurrent_setup']}
    with tempfile.TemporaryDirectory() as tmp:
        base=Path(tmp)
        for n in range(args.repeat):
            state=base/str(n);workspace=base/('work'+str(n))
            cmd=[sys.executable,str(ROOT/'scripts/install.py'),'--uv',args.uv,'--source',str(Path(args.wheel).resolve()),'--state',str(state),'--directory',str(workspace)]
            def prep(extra=()):
                r=subprocess.run(cmd+['--prepare-only',*extra],capture_output=True,text=True,timeout=90)
                assert r.returncode==0,r.stderr+r.stdout
                return r.stdout
            prep();counts['fresh']+=1
            assert 'skipped' in prep();counts['already_installed']+=1
            (state/'installed.json').write_text('{partial');prep();counts['partial_receipt']+=1
            py=state/'venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python');py.unlink();prep();counts['broken_venv']+=1
            assert 'skipped' in prep(['--offline']);counts['offline_rerun']+=1
            with socket.socket() as blocker:
                blocker.bind(('127.0.0.1',0));port=blocker.getsockname()[1];blocker.listen(1)
                if port>65515:raise RuntimeError('Random test port out of range')
                log=state/'test.log'
                with open(log,'w') as out:p=subprocess.Popen(cmd+['--port',str(port),'--no-browser','--lock-config','--offline','--stop-after-seconds','4'],stdout=out,stderr=subprocess.STDOUT)
                try:
                    url=None
                    for _ in range(150):
                        if p.poll() is not None:raise RuntimeError(log.read_text())
                        if (state/'server.json').exists():url=json.loads((state/'server.json').read_text())['url'];break
                        time.sleep(.1)
                    assert url and not url.endswith(':'+str(port));counts['occupied_port']+=1
                    assert 'Already running' in prep(['--offline']);counts['active_rerun']+=1
                    req=urllib.request.Request(url+'/api/ask',data=b'{"question":"What is CustomChat?"}',headers={'Content-Type':'application/json'})
                    result=json.load(urllib.request.urlopen(req));assert '[1]' in result['answer'] and len(result['evidence'])==2
                    try:urllib.request.urlopen(url+'/api/settings');raise AssertionError('lock failed')
                    except urllib.error.HTTPError as e:assert e.code==404
                finally:
                    p.wait(timeout=15)
            # Hold actual OS lock, ensure competing invocation exits without writes.
            sys.path.insert(0,str(ROOT/'scripts'));import install
            with install.locked(state/'install.lock'):
                r=subprocess.run(cmd+['--prepare-only'],capture_output=True,text=True,timeout=10)
                assert r.returncode!=0 and 'Another installer' in r.stderr
            counts['concurrent_setup']+=1
    print(json.dumps(dict(platform=sys.platform,repeat=args.repeat,counts=counts,network_bootstrap_tested=False)))
if __name__=='__main__':main()
