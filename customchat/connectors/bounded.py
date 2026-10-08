"""Separate, bounded plugin process. NOT a security sandbox: host files/network remain accessible."""
import json,os,re,subprocess,sys,tempfile
from pathlib import Path
SCRIPT = '''import importlib,json,sys,os
if os.name!='nt':
 import resource
 resource.setrlimit(resource.RLIMIT_FSIZE,(2097152,2097152))
 resource.setrlimit(resource.RLIMIT_CPU,(20,20))
from pathlib import Path
sys.path.insert(0,sys.argv[1])
m,f=sys.argv[2].split(':',1)
q,k=json.loads(sys.stdin.read())
x=list(getattr(importlib.import_module(m),f)(q,k))[:k]
Path(sys.argv[3]).write_text(json.dumps(x))
'''
class BoundedPlugin:
 def __init__(self,block,base):self.id=block['id'];self.label=block['label'];self.entry=block['entry'];self.base=os.path.abspath(base)
 def search(self,q,k):
  from .base import Evidence
  k=max(1,min(int(k),50))
  with tempfile.TemporaryDirectory(prefix='customchat-plugin-') as folder:
   result=Path(folder)/'result.json';log=Path(folder)/'output.log'
   allowed={'PATH','HOME','USERPROFILE','SYSTEMROOT','WINDIR','TEMP','TMP','TMPDIR','LANG','LC_ALL','LD_LIBRARY_PATH'}
   env={a:b for a,b in os.environ.items() if a.upper() in allowed}
   with log.open('wb') as out:
    p=subprocess.Popen([sys.executable,'-I','-c',SCRIPT,self.base,self.entry,str(result)],stdin=subprocess.PIPE,stdout=out,stderr=out,env=env,cwd=folder,start_new_session=os.name!='nt')
    p.stdin.write(json.dumps([str(q)[:2000],k]).encode());p.stdin.close()
    import time
    deadline=time.monotonic()+20
    while p.poll() is None:
     if time.monotonic()>deadline or log.stat().st_size>1024*1024 or (result.exists() and result.stat().st_size>2*1024*1024):
      if os.name!='nt':
       import signal
       try:os.killpg(p.pid,signal.SIGKILL)
       except ProcessLookupError:pass
      else:p.kill()
      p.wait();raise ValueError('Connector exceeded its time/output limit')
     time.sleep(.05)
   if p.returncode or not result.exists():raise ValueError('Connector failed in bounded mode; inspect its code and dependencies')
   if result.stat().st_size>2*1024*1024:raise ValueError('Connector result exceeds 2 MB')
   rows=json.loads(result.read_text())
   if not isinstance(rows,list) or not all(isinstance(x,dict) for x in rows):raise ValueError('Connector must return evidence objects')
   out=[]
   for e in rows[:k]:
    if any(key in e and not isinstance(e[key],str) for key in ('id','title','text','url','source','venue')):raise ValueError('Connector evidence text fields must be strings')
    out.append({**Evidence(),**e,'source':self.id})
   return out
