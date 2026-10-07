"""Finite, registered actions with owner-bound, expiring, one-use review tickets."""
import copy,json,secrets,threading,time
REGISTRY={
 'list_notes':{'label':'List my notes','mode':'read','fields':{}},
 'save_note':{'label':'Save a private note','mode':'write','fields':{'title':{'type':'string','maxLength':120},'text':{'type':'string','maxLength':4000}}},
}
class Actions:
 def __init__(self,cfg,store):self.cfg,self.store=cfg,store;self.lock=threading.RLock()
 def catalog(self):
  policy=self.cfg.get('actions',{});allow=policy.get('allow')
  return [dict(id=k,**copy.deepcopy(v)) for k,v in REGISTRY.items() if (allow is None or k in allow) and (v['mode']!='write' or policy.get('writes',True))]
 def prepare(self,owner,tool,args):
  spec=next((x for x in self.catalog() if x['id']==tool),None)
  if not spec:raise PermissionError('Action unavailable')
  if not isinstance(args,dict) or set(args)!=set(spec['fields']):raise ValueError('Use exactly the declared action fields')
  for k,f in spec['fields'].items():
   if not isinstance(args[k],str) or not args[k].strip() or len(args[k])>f['maxLength']:raise ValueError(k+' needs nonempty text within '+str(f['maxLength'])+' characters')
  ticket=secrets.token_urlsafe(24);payload={'tool':tool,'args':copy.deepcopy(args),'expires':time.time()+300,'used':False}
  self.store.save_state(owner,'action-'+ticket,payload)
  return dict(ticket=ticket,tool=tool,label=spec['label'],mode=spec['mode'],args=args,expires_in=300)
 def execute(self,owner,ticket):
  with self.lock:
   p=self.store.get_state(owner,'action-'+str(ticket))
   if p['used'] or time.time()>p['expires']:raise PermissionError('Review expired or already used')
   if p['tool'] not in {x['id'] for x in self.catalog()}:raise PermissionError('Action no longer allowed')
   p['used']=True;self.store.save_state(owner,'action-'+str(ticket),p)
   if p['tool']=='save_note':
    name='note-'+secrets.token_hex(8);self.store.save_state(owner,name,p['args']);return {'saved':True,'id':name}
   if p['tool']=='list_notes':
    return {'notes':[self.store.get_state(owner,n) for n in self.store.states(owner) if n.startswith('note-')][:100]}
   raise PermissionError('Action unavailable')
