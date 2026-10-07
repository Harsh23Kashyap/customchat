"""Artifact acceptance in an isolated environment, separate from source checkout."""
import json, os, subprocess, sys, tempfile, urllib.request, time, venv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def run():
    wheel=next((ROOT/'dist').glob('*.whl'))
    with tempfile.TemporaryDirectory(prefix='customchat release ') as folder:
        root=Path(folder);envroot=root/'isolated env';venv.create(envroot,with_pip=True)
        py=envroot/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
        env=dict(os.environ);env.pop('PYTHONPATH',None);env['PYTHONNOUSERSITE']='1'
        subprocess.run([str(py),'-m','pip','install',str(wheel)],check=True,env=env,cwd=root)
        subprocess.run([str(py),'-m','pip','check'],check=True,env=env,cwd=root)
        subprocess.run([str(py),'-m','customchat','init','workspace'],check=True,env=env,cwd=root)
        subprocess.run([str(py),'-m','customchat','validate','workspace/app.yaml'],check=True,env=env,cwd=root)
        # Unsupported old versions are declared, not allowed to fail mid-install.
        import zipfile
        with zipfile.ZipFile(wheel) as z:
            metadata=z.read(next(n for n in z.namelist() if n.endswith('/METADATA'))).decode()
            assert 'Requires-Python: >=3.10' in metadata
            assert 'Name: customchat-app' in metadata
            assert 'sentence-transformers' in metadata  # optional, not installed by core
        # Core can answer with all network requests disabled, without document/semantic extras.
        script="""import urllib.request
urllib.request.urlopen=lambda *a,**k: (_ for _ in ()).throw(AssertionError('network forbidden'))
from customchat.cli import main
main(['ask','workspace/app.yaml','What is CustomChat?'])
"""
        subprocess.run([str(py),'-c',script],check=True,cwd=root,env=env)
        # A broken YAML package on the host must not contaminate the isolated invocation.
        bad=root/'host conflict';bad.mkdir();(bad/'yaml.py').write_text("raise RuntimeError('host conflict')")
        polluted=dict(env,PYTHONPATH=str(bad))
        subprocess.run([str(py),'-I','-m','customchat','validate','workspace/app.yaml'],check=True,cwd=root,env=polluted)
        # An incompatible core dependency is diagnosed, then repaired from the same wheel.
        subprocess.run([str(py),'-m','pip','install','PyYAML==6.0.2'],check=True,cwd=root,env=env)
        mismatch=subprocess.run([str(py),'-m','pip','check'],cwd=root,env=env,capture_output=True,text=True)
        assert mismatch.returncode!=0 and 'pyyaml' in (mismatch.stdout+mismatch.stderr).lower()
        subprocess.run([str(py),'-m','pip','install','--force-reinstall',str(wheel)],check=True,cwd=root,env=env)
        subprocess.run([str(py),'-m','pip','check'],check=True,cwd=root,env=env)
        # Deleted dependency is a partial install. Reinstallation must restore it.
        subprocess.run([str(py),'-m','pip','uninstall','-y','PyYAML'],check=True,cwd=root,env=env)
        subprocess.run([str(py),'-m','pip','install',str(wheel)],check=True,cwd=root,env=env)
        subprocess.run([str(py),'-m','customchat','validate','workspace/app.yaml'],check=True,cwd=root,env=env)
        subprocess.run([str(py),'-m','pip','check'],check=True,cwd=root,env=env)
        # Core executable aliases must both exist in the wheel install.
        bindir=envroot/('Scripts' if os.name=='nt' else 'bin')
        for name in ('customchat','customchat-app'):
            command=bindir/(name+('.exe' if os.name=='nt' else ''))
            subprocess.run([str(command),'--version'],check=True,cwd=root,env=env)
        print('Release acceptance: isolated install, spaced paths, pip check, offline Demo, host-conflict isolation, aliases, Python floor')
if __name__=='__main__':run()
