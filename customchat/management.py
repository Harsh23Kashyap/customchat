"""Owner-only setup checks and private workspace workflows; no cloud deployment."""
import os,re,shutil,threading,time,copy
from pathlib import Path
from .workspace import Reviews,SettingsHistory,digest,archive,validate_archive

def diagnosis(message):
 text=str(message).lower()
 if any(x in text for x in ('401','403','key','credential','authentication')):kind='authentication';hint='Check the saved credential and service permission privately.'
 elif any(x in text for x in ('429','rate','quota','budget')):kind='limit';hint='Check the service quota and local budget. Retry later.'
 elif any(x in text for x in ('timeout','timed out')):kind='timeout';hint='The service did not reply in time. Check its address and try later.'
 elif any(x in text for x in ('404','model','not found')):kind='configuration';hint='Check the model or source configuration.'
 else:kind='connection';hint='Check that the service is running and reachable from this host.'
 return {'category':kind,'message':hint,'redacted':True}

def deploy_plan(cfg,data):
 fields=('target','account','region','audience','cost_limit','rollback')
 if not isinstance(data,dict) or set(data)!=set(fields) or any(not isinstance(data[k],str) or not data[k].strip() or len(data[k])>600 for k in fields):raise ValueError('Complete target, account, region, audience, cost limit and rollback')
 from .portable import _check_values,ExportError
 try:_check_values(data)
 except ExportError:raise ValueError('Use account labels only, never credentials or secret URLs') from None
 if data['audience'] not in ('private','team','public'):raise ValueError('Choose private, team or public')
 checks=[{'item':'Account / region','state':'unverified','detail':'User-entered labels only. No cloud access or ownership checked.'},
 {'item':'Authentication','state':'review' if cfg['auth']['mode']=='none' else 'configured','detail':cfg['auth']['mode']+' configured; hosted security still needs review.'},
 {'item':'Cost','state':'unverified','detail':'Your limit is a planning note, not a price quote or billing cap. Verify current compute, model, storage and network prices.'},
 {'item':'Rollback','state':'review','detail':'Verify backups, traffic switch-back and deletion steps before deployment.'},
 {'item':'Data and licenses','state':'review','detail':'Review documents, remote-source terms and logs for the chosen audience.'}]
 return {'plan_only':True,'inputs':data,'checks':checks,'next_steps':['Verify cloud account and permissions separately.','Review the exact resources, current prices, authentication and data audience.','Request approval before creating resources or spending money.'], 'notice':'No resources created. No credentials collected. No deployment or spending authorized.'}

class Management:
 def __init__(self,cfg,engine,settings,apply,safe_export):
  self.cfg,self.engine,self.store=cfg,engine,engine.store;self.settings=settings;self.apply=apply;self.export=safe_export
  self.reviews=Reviews();self.history=SettingsHistory(self.store);self.lock=threading.RLock();self.jobs={};self.active=False
 def fingerprint(self):return digest({'settings':self.settings(),'sources':self.cfg['sources'],'prompts':self.engine.prompts._load()})
 def status(self,owner):
  p=self.cfg['provider'];sources=self.cfg['sources']
  from .providers import has_key
  rows=[{'item':'Model','state':'demo' if p['type']=='mock' else 'configured','detail':'Offline demo, not a real model' if p['type']=='mock' else p['type']+' / '+p['model']+' - live response not checked'},
  {'item':'Credential','state':'present / not required' if p['type'] in ('mock','ollama') or has_key(p['type'],p.get('api_key_env','')).get('has') or not has_key(p['type'],p.get('api_key_env','')).get('needed') else 'setup','detail':'Presence only; validity not checked'},
  {'item':'Evidence sources','state':'configured' if sources else 'setup','detail':str(len(sources))+' sources configured; remote availability not checked'},
  {'item':'Data audience','state':'review','detail':'Authentication: '+self.cfg['auth']['mode']+'. Review before sharing or hosting.'},
  {'item':'Connector code','state':'review' if any(s['type']=='python' for s in sources) else 'ready','detail':'Bounded mode is NOT a sandbox. Review code; host files and network remain accessible.' if any(s['type']=='python' for s in sources) else 'No Python plugin configured'}]
  required=sorted({s.get('api_key_env') for s in sources if s.get('api_key_env')})
  from . import source_credentials
  missing=[k for k in required if not os.environ.get(k)]
  missing.extend(item['env'] for item in source_credentials.status(self.cfg) if not item['has_key'])
  if missing:rows.append({'item':'Source credentials','state':'setup','detail':'Not detected in host environment: '+', '.join(missing)+'. Set them privately; presence does not prove validity.'})
  for source in sources:
   if source['type']=='local_files':
    conn=self.engine.connectors.get(source['id']);rows.append({'item':source['label'],'state':'review' if getattr(conn,'last_error','') else 'indexed','detail':'Local index needs attention' if getattr(conn,'last_error','') else str(len(getattr(conn,'docs',[])))+' local evidence chunks indexed; no freshness/network check performed'})
  return {'rows':rows,'scope':'Configuration checks only. Live calls run only after review.','last_live':self.store.get_state(owner,'workspace-live') if 'workspace-live' in self.store.states(owner) else None}
 def prepare_live(self,owner,data,kind='preflight'):
  if kind=='smoke':
   questions=self.store.get_state(owner,'workspace-questions') if 'workspace-questions' in self.store.states(owner) else []
   if not questions:raise ValueError('Save test questions first')
  else:questions=['CustomChat connection check']
  from . import permissions
  selected=data.get('sources',[])
  if not isinstance(selected,list) or len(selected)>20 or any(s not in self.engine.connectors or not permissions.allowed(self.cfg,owner,s) for s in selected):raise ValueError('Choose configured sources')
  spec={'settings':self.fingerprint(),'sources':selected,'model':data.get('model') is True,'questions':questions}
  if kind=='smoke':spec['model']=True
  if not spec['model'] and not selected:raise ValueError('Choose a model check or source check')
  token=self.reviews.put(owner,kind,spec)
  return {'ticket':token,'model_calls':('Multiple calls per question may run for rewrite, answer checks and followups' if kind=='smoke' else 1) if spec['model'] else 0,'sources':selected,'questions':questions,'notice':'Live calls may send these questions to configured services and consume API budget. Test output does not prove correctness. No saved chat is created.'}
 def start(self,owner,kind,data):
  with self.lock:
   if self.active:raise ValueError('A workspace test is already running')
   spec=self.reviews.take(owner,kind,str(data.get('ticket','')),data.get('confirmed'))
   if self.fingerprint()!=spec['settings']:raise ValueError('Settings changed. Review the test again')
   jid=os.urandom(12).hex();self.jobs={k:v for k,v in self.jobs.items() if time.time()-v['at']<3600}
   self.jobs[jid]={'id':jid,'owner':owner,'state':'running','at':time.time()};self.active=True
  runner=copy.copy(self.engine);runner.cfg=copy.deepcopy(self.engine.cfg);runner.cfg['retrieval']['cache_ttl']=0;runner.connectors=dict(self.engine.connectors);runner._cache={}
  threading.Thread(target=self._run,args=(jid,owner,kind,spec,runner),daemon=True).start();return {'id':jid}
 def _run(self,jid,owner,kind,spec,runner):
  results=[]
  try:
   if kind=='preflight':
    runner.queries=lambda q:[q]
    if spec['model']:
     try:
      result=runner.provider.complete([{'role':'user','content':'Reply with the single word OK.'}])
      results.append({'item':'Model','ok':bool(result),'message':'A response was received; accuracy not checked.' if result else 'Empty response'})
     except Exception as exc:results.append({'item':'Model','ok':False,**diagnosis(exc)})
    for sid in spec['sources']:
     try:
      rows,errors=runner.retrieve('CustomChat connection check',[sid],owner)
      results.append({'item':sid,'ok':not bool(errors),'count':len(rows),**(diagnosis(str(errors)) if errors else {'message':'Request completed. Empty results do not prove a failure.'})})
     except Exception as exc:results.append({'item':sid,'ok':False,**diagnosis(exc)})
    self.store.save_state(owner,'workspace-live',{'at':time.time(),'results':results,'settings':spec['settings']})
   else:
    previous=self.store.get_state(owner,'workspace-smoke') if 'workspace-smoke' in self.store.states(owner) else []
    for question in spec['questions']:
     try:
      answer=next(v for k,v in runner.ask_stream(owner,None,question,sources=spec['sources'],temporary=True,use_cache=False) if k=='done')
      old=next((r for r in previous if r['question']==question),None)
      citations=[{'title':str(e.get('title','')),'id':str(e.get('id','')),'url':str(e.get('url',''))} for e in answer['evidence']]
      results.append({'question':question,'answer':answer['answer'],'citations':citations,'previous_answer':old.get('answer') if old else None,'previous_citations':old.get('citations') if old else None,'changed':bool(old and (old.get('answer')!=answer['answer'] or old.get('citations')!=citations)), 'source_errors':[diagnosis(x) for x in answer.get('source_errors',[])]})
     except Exception as exc:results.append({'question':question,'answer':'Test failed','citations':[],**diagnosis(exc)})
    self.store.save_state(owner,'workspace-smoke',results)
   with self.lock:self.jobs[jid].update(state='done',results=results,notice='Comparison only. No correctness score or certification.')
  except Exception as exc:
   with self.lock:self.jobs[jid].update(state='failed',**diagnosis(exc))
  finally:
   with self.lock:self.active=False
 def job(self,owner,jid):
  with self.lock:job=self.jobs.get(jid)
  if not job or job['owner']!=owner:raise ValueError('Unknown test job')
  return {k:v for k,v in job.items() if k!='owner'}
 def handle(self,owner,path,method,data,qs):
  name=path.removeprefix('/api/workspace/')
  if name=='status' and method=='GET':return self.status(owner)
  if name=='sources' and method=='GET':
   from . import permissions
   return {'sources':[{'id':s['id'],'label':s['label']} for s in self.cfg['sources'] if permissions.allowed(self.cfg,owner,s['id'])]}
  if name=='deploy' and method=='POST':return deploy_plan(self.cfg,data.get('plan'))
  if name=='history' and method=='GET':return {'revisions':self.history.list(owner),'scope':'Model and retrieval settings; not appearance, prompts or secrets.'}
  if name=='history/review' and method=='POST':
   old,diff=self.history.compare(owner,str(data.get('name','')),self.settings())
   from .portable import _check_values,ExportError
   try:_check_values({'current':self.settings(),'old':old})
   except ExportError:raise ValueError('This revision contains a credential URL. Remove it privately before reviewing history') from None
   token=self.reviews.put(owner,'settings',{'settings':old,'revision':digest(self.settings())})
   return {'ticket':token,'diff':diff,'notice':'Restores model and retrieval settings only. Current settings are saved first.'}
  if name=='history/restore' and method=='POST':
   with self.lock:
    if self.active:raise ValueError('Wait for the workspace test to finish before restoring settings')
    item=self.reviews.take(owner,'settings',str(data.get('ticket','')),data.get('confirmed'))
    if item['revision']!=digest(self.settings()):raise ValueError('Settings changed. Review again')
    self.history.record(owner,self.settings());self.apply(item['settings'])
   return {'settings':self.settings()}
  if name=='archive' and method=='GET':return archive(self.export(owner))
  if name=='archive/review' and method=='POST':
   chats=validate_archive(data.get('archive'));token=self.reviews.put(owner,'archive',chats)
   return {'ticket':token,'chats':len(chats),'turns':sum(len(c['turns']) for c in chats),'notice':'Private conversation content. Restore adds new chats; does not overwrite existing chats. Evidence and source visibility follow this app\'s permissions. Not a shareable Nerd.'}
  if name=='archive/restore' and method=='POST':
   chats=self.reviews.take(owner,'archive',str(data.get('ticket','')),data.get('confirmed'))
   return {'imported':self.store.import_chats(owner,chats)}
  if name=='questions' and method=='GET':return {'questions':self.store.get_state(owner,'workspace-questions') if 'workspace-questions' in self.store.states(owner) else []}
  if name=='questions' and method=='POST':
   questions=data.get('questions')
   if not isinstance(questions,list) or len(questions)>10 or any(not isinstance(q,str) or not q.strip() or len(q)>2000 for q in questions):raise ValueError('Save up to 10 nonempty questions, 2000 characters each')
   self.store.save_state(owner,'workspace-questions',questions);return {'questions':questions}
  if name in ('preflight/review','smoke/review') and method=='POST':return self.prepare_live(owner,data,name.split('/')[0])
  if name in ('preflight/run','smoke/run') and method=='POST':return self.start(owner,name.split('/')[0],data)
  if name=='job' and method=='GET':return self.job(owner,qs.get('id',''))
  raise ValueError('Unknown workspace action')

def model_review(cfg,data):
 from . import hardware
 model=str(data.get('model',''));base=str(data.get('base_url') or 'http://localhost:11434').rstrip('/')
 from urllib.parse import urlparse
 if not hardware.TAG_OK.fullmatch(model) or urlparse(base).hostname not in ('localhost','127.0.0.1','::1') or urlparse(base).scheme!='http':raise ValueError('Model review requires a local Ollama address and valid model name')
 hw=hardware.detect();budget,mode,note=hardware.budget(hw)
 match=next((x for x in hardware.CATALOG if x[0]==model),None)
 gb=match[3] if match else None
 # Ollama may use its own mount or service account; this is only the host default-location estimate.
 root=Path(os.environ.get('OLLAMA_MODELS') or str(Path.home()/'.ollama/models'))
 while not root.exists() and root!=root.parent:root=root.parent
 free=round(shutil.disk_usage(root).free/1024**3,1)
 if gb and free<gb+1:raise ValueError('Not enough free disk at the estimated model location. Free space before downloading.')
 return {'model':model,'base_url':base,'download_gb_estimate':gb,'free_disk_gb':free,'memory_budget_gb':round(budget,1),'memory_need_gb_estimate':round(gb+hardware.OVERHEAD_GB,1) if gb else None,'fit':hardware.fit_of(gb+hardware.OVERHEAD_GB,budget)[0] if gb else 'unknown','location_note':'Host default location estimate only. Ollama may store models on a different mount or account. Actual size varies by model tag.','notice':'Downloads model files on this host; no cloud account or purchase. Retry sends a fresh pull request; Ollama decides whether partial files can be reused.'}
