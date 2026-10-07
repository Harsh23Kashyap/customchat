"""Installed-package local quickstart; keep user files outside disposable tool caches."""
from pathlib import Path
import shutil,socket,threading,time,urllib.request,webbrowser
from .schema import ConfigError

def workspace(directory):
    folder=Path(directory).expanduser().resolve()
    app=folder/'app.yaml'
    if app.is_file():return app  # Never overwrite a user's app or docs on rerun.
    if folder.exists():raise ConfigError('Destination exists without app.yaml; choose a new --directory.')
    template=Path(__file__).parent/'templates/minimal'
    shutil.copytree(template,folder)
    return app

def pick_port(port):
    if not 1<=port<=65515:raise ConfigError('Choose a port between 1 and 65515.')
    for candidate in range(port,port+20):
        with socket.socket() as sock:
            try:sock.bind(('127.0.0.1',candidate));return candidate
            except OSError:pass
    raise ConfigError('No free port in the requested 20-port range.')

def start(directory,port=8080,no_browser=False,lock_config=False):
    import os
    app=workspace(directory);chosen=pick_port(port)
    url='http://127.0.0.1:'+str(chosen)
    if lock_config:os.environ['CUSTOMCHAT_CONFIG']='off'
    from .server import serve
    from .terminal import start_banner
    start_banner(str(app.parent),url)
    print('Workspace: '+str(app.parent),flush=True)
    print('Starting CustomChat at '+url+' (Ctrl+C to stop)',flush=True)
    if not no_browser: open_when_ready(url)
    serve(str(app),'127.0.0.1',chosen)


def open_when_ready(url):
    def ready():
        end=time.monotonic()+30
        while time.monotonic()<end:
            try:
                with urllib.request.urlopen(url+'/api/health',timeout=1) as r:
                    if r.status==200:webbrowser.open(url);return
            except Exception:pass
            time.sleep(.4)
    threading.Thread(target=ready,daemon=True).start()
