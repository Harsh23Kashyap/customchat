"""Opt-in local Ollama installer. Fixed official sources, no user shell commands."""
import hashlib, os, platform, secrets, shutil, subprocess, tempfile, threading, time, urllib.request
from pathlib import Path
from urllib.parse import urlparse
from . import hardware
SOURCES = {'Windows': 'https://ollama.com/download/OllamaSetup.exe', 'Darwin': 'https://ollama.com/download/Ollama.dmg', 'Linux': 'https://ollama.com/install.sh'}
PAGES = {'Windows': 'https://ollama.com/download/windows', 'Darwin': 'https://ollama.com/download/mac', 'Linux': 'https://ollama.com/download/linux'}
BASE = 'http://127.0.0.1:11434'
LIMIT = 2 * 1024 ** 3

def detect():
    system = platform.system()
    binary = shutil.which('ollama')
    if not binary and system == 'Darwin':
        p = Path('/Applications/Ollama.app/Contents/Resources/ollama')
        if p.is_file(): binary = str(p)
    if not binary and system == 'Windows':
        p = Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs/Ollama/ollama.exe'
        if p.is_file(): binary = str(p)
    running = hardware.installed(BASE) is not None
    return {'system': system, 'arch': platform.machine(), 'state': 'running' if running else 'stopped' if binary else 'not_detected',
            'binary': bool(binary), 'supported': system in SOURCES, 'source': SOURCES.get(system, ''), 'page': PAGES.get(system, ''),
            'disk_free_gb': round(shutil.disk_usage(tempfile.gettempdir()).free / 1024 ** 3, 1),
            'host_note': 'The computer running CustomChat, not the browser or phone.', '_binary': binary}

class OfficialRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urlparse(newurl).scheme != 'https' or urlparse(newurl).hostname not in ('ollama.com', 'github.com', 'objects.githubusercontent.com', 'release-assets.githubusercontent.com'):
            raise ValueError('Installer redirected outside the official download hosts')
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def download(url, folder, cancelled=None, progress=None):
    if url not in SOURCES.values(): raise ValueError('Unknown installer source')
    target = Path(folder) / url.rsplit('/', 1)[1]
    opener = urllib.request.build_opener(OfficialRedirect)
    with opener.open(url, timeout=60) as response, target.open('wb') as out:
        total = int(response.headers.get('Content-Length') or 0)
        if total > LIMIT: raise ValueError('Installer exceeds the 2 GB download limit')
        used = 0
        while True:
            if cancelled and cancelled.is_set(): raise ValueError('Download cancelled')
            chunk = response.read(1024 * 1024)
            if not chunk: break
            used += len(chunk)
            if used > LIMIT: raise ValueError('Installer exceeds the 2 GB download limit')
            out.write(chunk)
            if progress:progress(used,total)
    if not used: raise ValueError('Empty installer download')
    return target

class OllamaSetup:
    def __init__(self):
        self.lock = threading.Lock(); self.pending = {}; self.jobs = {}; self.processes = []; self.cancel_events = {}; self.job_processes = {}
    def status(self):
        data = detect(); data.pop('_binary', None)
        return data
    def prepare(self, action):
        if action not in ('install', 'start'): raise ValueError('Choose install or start')
        data = detect(); data.pop('_binary', None)
        if not data['supported']: raise ValueError('Use the official Ollama installer on this platform')
        if action == 'install' and data['state'] != 'not_detected': raise ValueError('Ollama is already detected. Start it or recheck instead.')
        if action == 'start' and data['state'] != 'stopped': raise ValueError('Start is available only for a detected, stopped Ollama')
        if action == 'install' and data['disk_free_gb'] < 5: raise ValueError('At least 5 GB free disk space is required before installation. Models need more.')
        ticket = secrets.token_urlsafe(24)
        with self.lock:
            self.pending = {ticket: (action, time.monotonic(), data['system'])}
        data.update(ticket=ticket, action=action, download_size='Not known until download; limit 2 GB',
                    changes='Install Ollama on this host. OS installer may require local interaction or permission. No models or cloud accounts added.' if action == 'install' else 'Start the detected local Ollama service.',
                    instructions={'Darwin': 'In the disk image, drag Ollama to Applications, then open it. Approve the CLI link only in the local OS prompt.',
                                  'Windows': 'Complete the official installer on this computer. Ollama should run in the background.',
                                  'Linux': 'The official script may require sudo. CustomChat never asks for a password. If permission is needed, follow the official page in a local terminal.'}[data['system']])
        return data
    def execute(self, ticket, confirmed):
        if confirmed is not True: raise ValueError('Review and confirm this installation first')
        with self.lock:
            item = self.pending.pop(ticket, None)
            if not item or time.monotonic() - item[1] > 600: raise ValueError('Review the installation again; approval expired')
            if any(x['state'] in ('downloading', 'starting', 'waiting') for x in self.jobs.values()): raise ValueError('A setup is already in progress')
            action, _, system = item
            if system != platform.system(): raise ValueError('Host changed; review again')
            current = detect()
            if action == 'install' and current['state'] != 'not_detected': raise ValueError('Ollama is now detected; recheck instead of installing again')
            if action == 'start' and current['state'] != 'stopped': raise ValueError('Service state changed; recheck')
            jid = secrets.token_urlsafe(18)
            self.cancel_events[jid]=threading.Event()
            self.jobs = {jid: {'id': jid, 'state': 'starting' if action == 'start' else 'downloading', 'message': 'Starting Ollama' if action == 'start' else 'Downloading the official installer', 'action': action}}
        threading.Thread(target=self._work, args=(jid, action, system), daemon=True).start()
        return {'id': jid}
    def job(self, jid):
        with self.lock: result = dict(self.jobs.get(jid, {}))
        if not result: raise ValueError('Unknown setup')
        return result
    def _update(self, jid, **values):
        with self.lock:
            if self.jobs[jid]['state']!='cancelled':self.jobs[jid].update(values)
    def cancel(self, jid):
        with self.lock:
            job=self.jobs.get(jid)
            if not job:raise ValueError('Unknown setup')
            if job['state'] in ('ready','failed','needs_manual','cancelled'):return dict(job)
            self.cancel_events[jid].set()
            proc=self.job_processes.get(jid)
            if proc and proc.poll() is None:
                try:proc.terminate()
                except OSError:pass
            job.update(state='cancelled',message='CustomChat stopped its setup work. An OS wizard or child installer may still be open; close it on the host. Installed changes are not rolled back. Retry requires a new review; installer downloads restart, not resume.')
            return dict(job)
    def _work(self, jid, action, system):
        try:
            if action == 'start':
                binary = detect().get('_binary')
                if not binary: raise ValueError('Ollama executable no longer detected; recheck')
                cmd = [binary, 'serve']
            else:
                # Keep mounted disk images available until the OS wizard is finished.
                folder = tempfile.mkdtemp(prefix='customchat-ollama-')
                target = download(SOURCES[system], folder, self.cancel_events.get(jid), lambda used,total:self._update(jid,downloaded_bytes=used,total_bytes=total,progress_pct=round(100*used/total) if total else None))
                digestor = hashlib.sha256()
                with target.open('rb') as downloaded:
                    for chunk in iter(lambda: downloaded.read(1024 * 1024), b''): digestor.update(chunk)
                digest = digestor.hexdigest()
                self._update(jid, state='starting', message='Opening the official installer on this computer', sha256=digest)
                cmd = [str(target)] if system == 'Windows' else ['open', str(target)] if system == 'Darwin' else ['sh', str(target)]
            with self.lock:
                if self.cancel_events.get(jid) and self.cancel_events[jid].is_set(): return
                proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.processes.append(proc);self.job_processes[jid]=proc
            self._update(jid, state='waiting', message='Complete any OS installer or permission prompt on the host, then recheck. No password is collected here.')
            for _ in range(300):
                if self.cancel_events.get(jid) and self.cancel_events[jid].is_set():return
                if hardware.installed(BASE) is not None:
                    self._update(jid, state='ready', message='Local Ollama service verified. Choose a model separately.'); return
                if system == 'Linux' and proc.poll() not in (None, 0):
                    self._update(jid, state='needs_manual', message='Installer could not complete non-interactively. Use the official install page in a local terminal; then recheck.', page=PAGES[system]); return
                time.sleep(2)
            self._update(jid, state='needs_manual', message='Local service is not reachable yet. Complete the OS setup or use the official instructions, then recheck.', page=PAGES[system])
        except Exception:
            self._update(jid, state='failed', message='Setup could not complete. No success claimed. Use the official install page, then recheck.', page=PAGES.get(system, 'https://ollama.com'))
