"""Review portable Nerds without importing code, then launch in a separate local workspace."""
import base64,hashlib,io,json,os,re,shutil,subprocess,sys,threading,zipfile
from pathlib import Path,PurePosixPath
import yaml
from . import schema
from .portable import _check_values,ExportError
MAX_UPLOAD=8*1024*1024
MAX_EXPANDED=32*1024*1024
_ALLOWED={'.yaml','.yml','.json','.md','.txt','.csv','.pdf','.py'}
class NerdLoader:
 def __init__(self,folder):
  self.root=Path(folder)/'nerds';self.pending={};self.children=[];self.lock=threading.Lock()
 def review(self,name,encoded):
  try:data=base64.b64decode(encoded,validate=True)
  except Exception:raise ValueError('Invalid upload') from None
  if len(self.children)>=4:raise ValueError('Up to four Nerds can run here. Restart CustomChat to close them before loading more.')
  if len(data)>MAX_UPLOAD:raise ValueError('Bundle limit is 8 MB')
  files={}
  if name.lower().endswith('.zip'):
   try:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
     if len(z.infolist())>500:raise ValueError('Too many files')
     total=0
     for info in z.infolist():
      path=PurePosixPath(info.filename)
      if path.is_absolute() or '..' in path.parts or '\\' in info.filename or re.match(r'^[A-Za-z]:',info.filename):raise ValueError('Unsafe path in bundle')
      if (info.external_attr>>16)&0o170000==0o120000:raise ValueError('Symlinks are not allowed')
      if info.is_dir():continue
      if any(x.startswith('.') for x in path.parts):raise ValueError('Hidden files are not allowed; never import .env')
      if re.search(r'(secret|credential|password|token|customchat\.db|accounts|sessions)',info.filename,re.I):raise ValueError('Private files are not allowed')
      if len(info.filename)>240:raise ValueError('Path too long')
      if path.suffix.lower() not in _ALLOWED:raise ValueError('Unsupported file: '+info.filename)
      total+=info.file_size
      if total>MAX_EXPANDED:raise ValueError('Expanded bundle is too large')
      if info.filename in files:raise ValueError('Duplicate path')
      files[info.filename]=z.read(info)
   except zipfile.BadZipFile:raise ValueError('Invalid ZIP') from None
  elif name.lower().endswith(('.yaml','.yml','.json')):files['app.yaml']=data
  else:raise ValueError('Choose a Nerd ZIP or YAML/JSON app file')
  apps=[n for n in files if PurePosixPath(n).name in ('app.yaml','app.yml','app.json')]
  if len(apps)!=1:raise ValueError('Bundle must contain exactly one app.yaml (or app.json)')
  prefix=str(PurePosixPath(apps[0]).parent)
  if prefix!='.':
   if any(not n.startswith(prefix+'/') for n in files):raise ValueError('All files must be inside the app folder')
   files={n[len(prefix)+1:]:v for n,v in files.items()}
  appname=next(n for n in files if PurePosixPath(n).name in ('app.yaml','app.yml','app.json'))
  try:raw=yaml.safe_load(files[appname].decode('utf-8'))
  except Exception:raise ValueError('Invalid app YAML/JSON') from None
  try:cfg=schema.validate(raw);_check_values(cfg)
  except (schema.ConfigError,ExportError) as e:raise ValueError(str(e)) from None
  for name,content in files.items():
   if name.endswith('.json'):
    try:_check_values(json.loads(content))
    except (ValueError,ExportError):raise ValueError('Invalid or private JSON file: '+name) from None
  if cfg['auth']['mode']!='none':raise ValueError('Local imported Nerds must use auth.mode: none. Set up hosted authentication separately.')
  for name in ('data/theme.json','data/prompts.json'):
   if name in files:
    from . import theme,prompts
    d=json.loads(files[name])
    if name.endswith('theme.json'):files[name]=json.dumps(theme.clean(d)).encode()
    elif not isinstance(d,dict) or set(d)-{'text','on'}:raise ValueError('Invalid prompt settings')
  for src in cfg['sources']:
   for field in ('path','module'):
    v=src.get(field)
    if not v:continue
    p=PurePosixPath(v)
    if p.is_absolute() or '..' in p.parts or '\\' in v:raise ValueError('Sources must stay inside the bundle')
   if src['type']=='local_files':
    path=src.get('path','docs').rstrip('/')
    if not any(n.startswith(path+'/') for n in files):raise ValueError('Missing local source folder '+path+'. Load a ZIP with its documents.')
   if src['type']=='python':
    mod=src.get('entry','').partition(':')[0]
    if not re.fullmatch(r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*',mod):raise ValueError('Invalid Python module entry')
    if mod.replace('.','/')+'.py' not in files:raise ValueError('Python connector module is missing from bundle')
  cfg['storage']={'path':'data/customchat.db'};cfg['server']['host']='127.0.0.1';cfg['actions']={'allow':[],'writes':False}
  files.pop(appname);files['app.yaml']=yaml.safe_dump(cfg,sort_keys=False).encode()
  code=[n for n in files if n.endswith('.py')]
  if sum(len(files[n]) for n in code)>200000:raise ValueError('Connector code is too large to review here')
  envs=sorted({src.get('api_key_env') for src in cfg['sources'] if src.get('api_key_env')}|({cfg['provider']['api_key_env']} if cfg['provider'].get('api_key_env') else set()))
  from .readiness import check
  readiness=check(cfg,files,raw)
  if not readiness['can_load']:raise ValueError('Python connector does not compile. Fix it before loading.')
  envs=readiness['required_env']
  token=hashlib.sha256(data).hexdigest()
  with self.lock:
   if len(self.pending)>=4:self.pending.pop(next(iter(self.pending)))
   self.pending[token]=(files,cfg,code)
  return {'readiness':readiness,'token':token,'title':cfg['app']['title'],'tagline':cfg['app']['tagline'],'provider':cfg['provider']['type'],'model':cfg['provider']['model'],'sources':[{'id':s['id'],'label':s.get('label',s['id']),'type':s['type']} for s in cfg['sources']],'required_env':envs,'code':[{'path':n,'text':files[n].decode('utf-8')} for n in code],'warnings':['Separate local workspace. Current app is not overwritten.','Keys, accounts and chat history are not imported.','Imported local apps disable write actions. Review remote sources before asking a question.']}
 def load(self,token,allow_code=False):
  with self.lock:item=self.pending.get(token)
  if not item:raise ValueError('Review the bundle first')
  files,cfg,code=item
  if len(self.children)>=4:raise ValueError('Maximum four running Nerds. Restart CustomChat before loading more.')
  if code and not allow_code:raise ValueError('Review Python code and explicitly allow it before loading')
  from .launcher import pick_port
  import tempfile
  self.root.mkdir(parents=True,exist_ok=True)
  folder=Path(tempfile.mkdtemp(prefix='nerd-',dir=str(self.root)))
  for name,data in files.items():
   p=folder/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
  port=pick_port(8090)
  cfg['server']['port']=port;(folder/'app.yaml').write_text(yaml.safe_dump(cfg,sort_keys=False))
  log=open(folder/'run.log','wb')
  child=subprocess.Popen([sys.executable,'-m','customchat','run',str(folder/'app.yaml'),'--no-browser'],stdout=log,stderr=subprocess.STDOUT,cwd=str(Path(__file__).resolve().parents[1]),env={k:v for k,v in os.environ.items() if not re.search(r'(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL)',k,re.I)})
  log.close();self.children.append(child)
  import time,urllib.request
  url='http://127.0.0.1:'+str(port)
  for _ in range(40):
   if child.poll() is not None:raise ValueError('Nerd could not start. Check dependencies and connector setup in '+str(folder/'run.log'))
   try:
    with urllib.request.urlopen(url+'/api/health',timeout=.5):return {'url':url,'title':cfg['app']['title'],'workspace':str(folder)}
   except OSError:time.sleep(.1)
  child.terminate();raise ValueError('Nerd did not become ready; current app is unchanged')
 def close(self):
  for child in self.children:
   if child.poll() is None:
    child.terminate()
    try:child.wait(timeout=3)
    except subprocess.TimeoutExpired:child.kill();child.wait()
