"""News evidence adapters. Keys are env-only and never appear in URLs."""
import json,os,re,urllib.parse,urllib.request,urllib.error

def _query(q):
    # Treat a question as plain keywords, not an API boolean expression.
    words=re.findall(r"[\w]+",q,flags=re.UNICODE)
    stop={'what','whats','has','been','reported','about','compare','coverage','of','do','sources','say','the','is','are','and','how','tell','me','latest','news','please'}
    return ' '.join(w for w in words if w.lower() not in stop)[:200]

def _search(q,k,service):
    key=os.environ.get('GNEWS_API_KEY' if service=='gnews' else 'NEWSAPI_KEY','').strip()
    if not key: raise ValueError('Missing private news API key. Fill .env and restart.')
    query=_query(q)
    if not query:return []
    count=max(1,min(int(k),10))
    params={'q':query,'lang':'en','max':count,'sortby':'publishedAt'} if service=='gnews' else {'q':query,'language':'en','pageSize':count,'sortBy':'publishedAt'}
    base='https://gnews.io/api/v4/search' if service=='gnews' else 'https://newsapi.org/v2/everything'
    req=urllib.request.Request(base+'?'+urllib.parse.urlencode(params),headers={'X-Api-Key':key,'User-Agent':'NewsNerd-local/1.0','Accept':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=20) as reply: payload=json.loads(reply.read(2_000_001).decode('utf-8'))
    except urllib.error.HTTPError as e:
        # No key-bearing URL or response payload in error messages.
        raise ValueError('News API HTTP '+str(e.code)+'; check credentials, quota and plan.') from None
    if payload.get('status')=='error' or payload.get('errors'):raise ValueError('News API rejected query; check syntax, key and plan.')
    articles=payload.get('articles',[])
    if not isinstance(articles,list):raise ValueError('Unexpected news API response shape')
    out=[]
    for a in articles[:count]:
        if not isinstance(a,dict):continue
        title=str(a.get('title') or '').strip();snippet=str(a.get('description') or a.get('content') or '').strip();url=str(a.get('url') or '')
        if not title or not snippet or not url.startswith(('https://','http://')):continue
        date=str(a.get('publishedAt') or 'Not supplied');source=a.get('source') or {};name=str(source.get('name') or 'Unknown publisher') if isinstance(source,dict) else 'Unknown publisher'
        out.append({'id':url,'title':title,'text':'Published: '+date+'\nPublisher: '+name+'\nNews snippet (not full article): '+snippet[:6000],'url':url,'authors':[str(a['author'])] if a.get('author') else [],'year':date[:4] if date[:4].isdigit() else '', 'venue':name,'source':service,'score':1.0/(len(out)+1)})
    return out

def gnews(query,k=6): return _search(query,k,'gnews')
def newsapi(query,k=6): return _search(query,k,'newsapi')
