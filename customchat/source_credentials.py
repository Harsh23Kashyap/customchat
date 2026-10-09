"""Private keys for declared native HTTP headers; never forwards keys to Python."""
import os,re,hashlib
from urllib.parse import urlsplit
from . import secrets

def declared(cfg):
 result=[]
 for source in cfg['sources']:
  if source['type']!='http_json':continue
  for header,env in (source.get('header_env') or {}).items():
   address=urlsplit(source.get('url',''))
   if address.scheme!='https' or not address.hostname or address.username or address.password:
    raise ValueError('Credential-bearing HTTP sources require an HTTPS address without embedded credentials')
   if not isinstance(header,str) or not re.fullmatch(r'[A-Za-z0-9-]+',header) or not isinstance(env,str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',env):
    raise ValueError('HTTP source credential headers need valid header and environment names')
   result.append({'source':source['id'],'label':source['label'],'header':header,'env':env,'url':source.get('url','')})
 return result

def name(source,env,url):return 'http:'+source+':'+env+':'+hashlib.sha256(url.encode()).hexdigest()[:16]

def value(source,env,url):return secrets.saved(name(source,env,url)) or os.environ.get(env,'')

def status(cfg):
 return [{**item,'has_key':bool(value(item['source'],item['env'],item['url']))} for item in declared(cfg)]

def update(cfg,data):
 source,env=data.get('source'),data.get('env')
 item=next((item for item in declared(cfg) if item['source']==source and item['env']==env),None)
 if not item:
  raise ValueError('Choose a declared native HTTP source credential')
 if data.get('clear'):secrets.STORE.delete(name(source,env,item['url']))
 else:secrets.STORE.set(name(source,env,item['url']),data.get('key'))
 return status(cfg)
