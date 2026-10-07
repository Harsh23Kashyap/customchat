"""Explicit app-only export. Never copy a workspace or its database wholesale."""
import copy
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path
from urllib.parse import urlsplit
import yaml
from . import schema, theme, prompts

class ExportError(ValueError):
    pass

MAX_BYTES = 64 * 1024 * 1024
DOC_TYPES = {'.md', '.txt', '.json', '.csv', '.pdf'}
PRIVATE = {'secrets', 'credentials', 'accounts', 'sessions', 'uploads', 'private'}
SECRET_KEYS = re.compile(r'^(api_key|key|password|secret|token|authorization|cookie|headers|credentials|dsn)$', re.I)

def _check_values(value):
    if isinstance(value, dict):
        for k, v in value.items():
            if SECRET_KEYS.fullmatch(str(k)) and v:
                raise ExportError('Remove inline credentials before exporting; use environment-variable names instead.')
            _check_values(v)
    elif isinstance(value, list):
        for v in value: _check_values(v)
    elif isinstance(value, str) and '://' in value:
        try:
            u = urlsplit(value)
            if u.username or u.password or re.search(r'(?:[?&])(api_key|key|token|secret|password)=', value, re.I):
                raise ExportError('A configured URL contains credentials. Use an environment variable instead.')
        except ExportError:
            raise
        except ValueError:
            raise ExportError("A configured URL is invalid.")

def _state_folder(cfg):
    path = cfg['storage']['path']
    if path == ':memory:' or '://' in path: return None
    p = Path(path)
    return (p if p.is_absolute() else Path(cfg.get('_dir', '.')) / p).absolute().parent

def _safe_doc(p, root):
    parts = p.relative_to(root).parts
    return not any(x.startswith('.') or x.lower() in PRIVATE for x in parts) and not any(
        re.search(r'(secret|credential|password|token|api[_-]?key)', x, re.I) for x in parts)

def bundle(cfg, theme_value=None, prompt_value=None):
    """Returns ZIP bytes and a manifest; only configured local evidence is copied."""
    clean = schema.validate({k: copy.deepcopy(v) for k, v in cfg.items() if k in schema.DEFAULTS})
    if state_folder := _state_folder(cfg):
        budget_path = state_folder / 'budget.json'
        if budget_path.exists():
            from .budget import clean as clean_budget
            clean['budget'] = clean_budget(json.loads(budget_path.read_text()))
    _check_values(clean)
    base = Path(cfg.get('_dir', '.')).absolute()
    state = _state_folder(cfg)
    clean['storage'] = {'path': 'data/customchat.db'}
    clean['server']['host'] = '127.0.0.1'
    files = {}
    warnings = ['Local source documents are included. Review them before sharing.',
                'Keys, accounts, conversations, uploads, caches and saved looks are not included.',
                'Remote sources, fonts and background URLs still require their original services.']
    used = 0
    for i, source in enumerate(clean['sources']):
        if source['type'] != 'local_files':
            if source['type'] == 'python': warnings.append('Python source %s needs its module installed separately.' % source['id'])
            continue
        root = Path(source.get('path', 'docs'))
        root = root if root.is_absolute() else base / root
        if root.is_symlink() or not root.is_dir() or root.resolve() != root.absolute():
            raise ExportError('Local source %s must be an existing, non-symlink directory.' % source['id'])
        root = root.absolute()
        if state and root == state:
            raise ExportError('Local source %s points at the private state directory.' % source['id'])
        target = 'assets/source-%d' % (i + 1)
        source['path'] = target
        for p in sorted(root.rglob('*')):
            if p.is_symlink(): raise ExportError('Local source %s contains a symlink; remove it before exporting.' % source['id'])
            if not p.is_file() or p.suffix.lower() not in DOC_TYPES: continue
            if not _safe_doc(p, root) or (state and (p == state or state in p.parents)):
                raise ExportError('Local source %s contains a private-looking file. Move it out before exporting.' % source['id'])
            size = p.stat().st_size
            if used + size > MAX_BYTES: raise ExportError('Local assets exceed the 64 MB export limit.')
            data = p.read_bytes(); used += len(data)
            if used > MAX_BYTES: raise ExportError('Local assets exceed the 64 MB export limit.')
            files[target + '/' + p.relative_to(root).as_posix()] = data
        # Keep empty sources runnable after extraction.
        if not any(k.startswith(target + '/') for k in files):
            files[target + '/'] = b''
    if theme_value is None:
        theme_value = theme.ThemeStore(str(state)).value if state else {}
    files['data/theme.json'] = json.dumps(theme.clean(theme_value), indent=2).encode()
    if prompt_value is None:
        prompt_value = prompts.PromptStore(str(state) if state else '')._load()
    pv = prompt_value if isinstance(prompt_value, dict) else {}
    pv = {'text': {k: v for k, v in (pv.get('text') or {}).items() if k in prompts.STAGES and isinstance(v, str) and len(v) <= prompts.MAX_LEN},
          'on': {k: bool(v) for k, v in (pv.get('on') or {}).items() if k in prompts.STAGES and prompts.STAGES[k]['optional']}}
    files['data/prompts.json'] = json.dumps(pv, indent=2).encode()
    files['app.yaml'] = yaml.safe_dump(clean, sort_keys=False, allow_unicode=True).encode()
    envs = set()
    def env_names(v):
        if isinstance(v, dict):
            for k, x in v.items():
                if str(k).endswith('_env') and isinstance(x, str) and x: envs.add(x)
                elif k == 'header_env' and isinstance(x, dict): envs.update(str(n) for n in x.values())
                else: env_names(x)
        elif isinstance(v, list):
            for x in v: env_names(x)
    env_names(clean)
    manifest = {'format': 'customchat-app', 'version': 1, 'required_env': sorted(envs), 'warnings': warnings,
                'files': {k: {'bytes': len(v), 'sha256': hashlib.sha256(v).hexdigest()} for k, v in sorted(files.items())}}
    files['manifest.json'] = json.dumps(manifest, indent=2).encode()
    files['README.txt'] = ('CustomChat portable app\n\nExtract into a new empty directory.\nRun: customchat validate app.yaml\nThen: customchat run app.yaml\n\nSet these environment variables yourself: ' + (', '.join(sorted(envs)) or 'none declared') + '\n\n' + '\n'.join(warnings) + '\n').encode()
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in sorted(files.items()): z.writestr(name, data)
    return out.getvalue(), manifest

def export_app(path, destination):
    cfg = schema.load(str(path))
    dest = Path(destination)
    data, manifest = bundle(cfg)
    with dest.open('xb') as f: f.write(data)
    return manifest
