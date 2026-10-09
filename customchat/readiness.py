"""Offline prerequisites, not a claim that models, keys or external services work."""
import ast,os
from . import schema

def check(cfg,files=None,provided=None):
 rows=[];provided=provided or cfg
 for key in schema.DEFAULTS:
  rows.append({'kind':'ready' if key in provided else 'default','item':key,'message':'Provided' if key in provided else 'Optional default applied'})
 p=cfg['provider'];requirements=[]
 if p['type']=='mock':rows.append({'kind':'warning','item':'Answers','message':'Offline Demo only. No real model answers.'})
 elif p['type']=='ollama':rows.append({'kind':'setup','item':'Local model','message':'Requires Ollama and '+p['model']+'. Not checked during import.'})
 elif p.get('api_key_env'):requirements.append(p['api_key_env'])
 if not cfg['sources']:rows.append({'kind':'warning','item':'Sources','message':'No evidence sources configured. Citation-backed answers are unavailable.'})
 for section, defaults in schema.DEFAULTS.items():
  if isinstance(defaults,dict):
   values=provided.get(section,{})
   missing=[k for k in defaults if k not in values]
   if missing:rows.append({'kind':'default','item':section+' optional fields','message':'Defaults applied: '+', '.join(missing)})
 for src in cfg['sources']:
  if src.get('api_key_env'):requirements.append(src['api_key_env'])
  if src['type']=='http_json':requirements.extend((src.get('header_env') or {}).values())
  if src['type']=='python' and files is not None:
   name=src['entry'].partition(':')[0].replace('.','/')+'.py'
   try:
    tree=ast.parse(files[name].decode())
    for n in ast.walk(tree):
     if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('getenv','get') and n.args and isinstance(n.args[0],ast.Constant) and isinstance(n.args[0].value,str) and n.args[0].value.endswith(('_KEY','_TOKEN')):requirements.append(n.args[0].value)
    imports=sorted({n.names[0].name.split('.')[0] for n in tree.body if isinstance(n,ast.Import)}|{n.module.split('.')[0] for n in tree.body if isinstance(n,ast.ImportFrom) and n.module})
    rows.append({'kind':'warning','item':src['label'],'message':'Python code included. Review code and dependencies: '+', '.join(imports)})
   except (SyntaxError,UnicodeDecodeError):rows.append({'kind':'blocked','item':src['label'],'message':'Python connector does not compile'})
  rows.append({'kind':'ready','item':'Source: '+src['label'],'message':src['type']+' configured'+(' · remote availability not checked' if src['type']!='local_files' else '')})
 for name in sorted(set(requirements)):rows.append({'kind':'setup','item':name,'message':'Key excluded. Set this privately in the new workspace; not checked during import.'})
 return {'rows':rows,'required_env':sorted(set(requirements)),'can_load':not any(x['kind']=='blocked' for x in rows),'scope':'Offline checks only. No model, network, credential or clinical-output test.'}
