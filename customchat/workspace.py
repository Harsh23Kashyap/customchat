"""Private management helpers. Reviews are owner-bound, one-use and short-lived."""
import hashlib,json,secrets,threading,time
class Reviews:
 def __init__(self):self.items={};self.lock=threading.Lock()
 def put(self,owner,kind,value):
  with self.lock:
   self.items={k:v for k,v in self.items.items() if time.monotonic()-v[0]<600}
   if len(self.items)>=100:raise ValueError('Too many pending reviews')
   token=secrets.token_urlsafe(24);self.items[token]=(time.monotonic(),owner,kind,value);return token
 def take(self,owner,kind,token,confirmed):
  if confirmed is not True:raise ValueError('Review and confirm first')
  with self.lock:
   item=self.items.get(token)
   if not item or item[1:3]!=(owner,kind) or time.monotonic()-item[0]>600:raise ValueError('Review expired or unavailable')
   self.items.pop(token);return item[3]
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def archive(chats):return {'format':'customchat-private-chats','version':1,'chats':chats}
def validate_archive(data):
 if not isinstance(data,dict) or set(data)!={'format','version','chats'} or data['format']!='customchat-private-chats' or data['version']!=1:raise ValueError('Choose a CustomChat private chat archive')
 chats=data['chats']
 if not isinstance(chats,list) or len(chats)>200:raise ValueError('Archive limit is 200 chats')
 clean=[];total=0
 for chat in chats:
  if not isinstance(chat,dict) or set(chat)-{'id','title','pinned','created','turns'}:raise ValueError('Invalid chat fields')
  turns=chat.get('turns',[])
  if not isinstance(turns,list) or len(turns)>500:raise ValueError('Chat limit is 500 turns')
  out=[]
  for turn in turns:
   if not isinstance(turn,dict) or set(turn)-{'question','answer','evidence','created'}:raise ValueError('Invalid turn fields')
   q,a=turn.get('question'),turn.get('answer')
   if not isinstance(q,str) or not isinstance(a,str) or len(q)>2000 or len(a)>100000:raise ValueError('Invalid question or answer')
   evidence=turn.get('evidence',[])
   if not isinstance(evidence,list) or len(evidence)>100 or not all(isinstance(x,dict) for x in evidence):raise ValueError('Invalid evidence')
   total+=len(json.dumps(turn))
   if total>8*1024*1024:raise ValueError('Archive limit is 8 MB')
   out.append({'question':q,'answer':a,'evidence':evidence})
  clean.append({'title':str(chat.get('title','Imported'))[:120],'turns':out})
 return clean
class SettingsHistory:
 def __init__(self,store):self.store=store
 def record(self,owner,settings):
  name='history-'+str(time.time_ns());self.store.save_state(owner,name,settings)
  names=sorted(n for n in self.store.states(owner) if n.startswith('history-'))
  for n in names[:-30]:self.store.delete_state(owner,n)
  return name
 def list(self,owner):return sorted((n for n in self.store.states(owner) if n.startswith('history-')),reverse=True)
 def compare(self,owner,name,current):
  if not name.startswith('history-'):raise ValueError('Choose a settings revision')
  old=self.store.get_state(owner,name)
  return old,[{'field':k,'current':current.get(k),'restore':old.get(k)} for k in sorted(set(current)|set(old)) if current.get(k)!=old.get(k)]
