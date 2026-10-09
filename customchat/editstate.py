"""Owner configuration and inert editor drafts. Never returns secret values or runs code."""
import copy,hashlib,json,os,tempfile
from pathlib import Path
import yaml
from . import schema
from .portable import _check_values

def view(cfg):
 return copy.deepcopy({k:cfg[k] for k in schema.DEFAULTS})
def saved_view(cfg):
 path=Path(cfg.get('_path',''))
 if not cfg.get('_path'):return view(cfg)
 if not path.is_file() or path.is_symlink():raise ValueError('Saved app file is not a regular file')
 try:raw=yaml.safe_load(path.read_text(encoding='utf-8'))
 except (OSError,UnicodeError,yaml.YAMLError):raise ValueError('Saved app file cannot be read') from None
 result=view(schema.validate(raw));_check_values(result);return result
def save_config(cfg,raw,revision):
 path=Path(cfg.get('_path',''))
 if not cfg.get('_path') or not path.is_file() or path.is_symlink():raise ValueError('This workspace has no writable app file')
 old=path.read_bytes()
 if hashlib.sha256(old).hexdigest()!=revision:raise ValueError('App file changed. Reload Configuration before saving.')
 _check_values(raw);new=schema.validate(raw)
 fd,tmp=tempfile.mkstemp(prefix='.app-edit-',dir=str(path.parent))
 try:
  with os.fdopen(fd,'w') as f:yaml.safe_dump(view(new),f,sort_keys=False);f.flush();os.fsync(f.fileno())
  if path.is_symlink() or path.read_bytes()!=old:raise ValueError('App file changed. Save stopped.')
  os.replace(tmp,path)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
 return hashlib.sha256(path.read_bytes()).hexdigest()
def revision(cfg):
 try:return hashlib.sha256(Path(cfg['_path']).read_bytes()).hexdigest()
 except (KeyError,OSError):return ''
def drafts(folder):
 try:
  d=json.loads((Path(folder)/'code-drafts.json').read_text())
  return d if isinstance(d,dict) else {}
 except (OSError,ValueError):return {}
def save_draft(folder,kind,brief,code):
 if kind not in ('search','clean_query') or not isinstance(brief,str) or not isinstance(code,str) or len(brief)>6000 or len(code)>200000:raise ValueError('Invalid helper draft')
 _check_values({'brief':brief,'code':code})
 data=drafts(folder);data[kind]={'brief':brief,'code':code}
 path=Path(folder)/'code-drafts.json';path.parent.mkdir(parents=True,exist_ok=True)
 fd,tmp=tempfile.mkstemp(prefix='.draft-',dir=str(path.parent))
 try:
  with os.fdopen(fd,'w') as f:json.dump(data,f)
  os.replace(tmp,path)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
 return data[kind]
def helper_state(cfg,folder):
 result=drafts(folder)
 if 'search' not in result:
  for src in cfg['sources']:
   if src['type']!='python':continue
   mod=src.get('entry','').partition(':')[0]
   path=Path(cfg.get('_dir','.'))/(mod.replace('.','/')+'.py')
   try:
    if path.is_symlink() or not path.resolve().is_relative_to(Path(cfg.get('_dir','.')).resolve()) or path.stat().st_size>200000:continue
    text=path.read_text();_check_values({'code':text})
    result['search']={'brief':src.get('label',src['id'])+' ('+src['entry']+')','code':text,'source':src['id'],'active':True};break
   except (OSError,UnicodeError,ValueError):continue
 return result
