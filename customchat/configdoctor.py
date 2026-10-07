"""Offline configuration diagnostics and editor schema. Never runs connectors."""
import copy, difflib, json, re
from pathlib import Path
from . import schema

SOURCE_KEYS = {'id','label','type','weight','path','semantic_model','rerank_model','ocr','refresh_interval','url','results_path','fields','header_env','timeout','name','filter','category','entry','providers','provider','mailto','limit','language','endpoint','api_key_env'}

def editor_schema():
    def node(v):
        if isinstance(v, dict): return {'type':'object','properties':{k:node(x) for k,x in v.items()},'additionalProperties':False}
        if isinstance(v, bool): return {'type':'boolean'}
        if isinstance(v, int): return {'type':'integer'}
        if isinstance(v, float): return {'type':'number'}
        if isinstance(v, list): return {'type':'array','items':{'type':'string'}}
        if v is None: return {}
        return {'type':'string'}
    out=node(schema.DEFAULTS);out.update({'$schema':'https://json-schema.org/draft/2020-12/schema','title':'CustomChat app configuration'})
    props=out['properties'];p=props['provider']['properties'];p['type']['enum']=sorted(schema.PROVIDERS)
    fallback=copy.deepcopy(p);fallback.pop('fallback',None)
    p['fallback']={'anyOf':[{'type':'null'}, {'type':'object','properties':fallback,'additionalProperties':False}]}
    props['auth']['properties']['mode']['enum']=sorted(schema.AUTH_MODES)
    props['app']['properties']['theme']['enum']=['auto','light','dark']
    props['prompt']['properties']['style']={'type':'object','additionalProperties':{'type':'string'}}
    props['sources']={'type':'array','items':{'type':'object','required':['type'],'properties':{k:{} for k in sorted(SOURCE_KEYS)},'additionalProperties':True}}
    sp=props['sources']['items']['properties'];sp['type']={'type':'string','enum':sorted(schema.CONNECTORS)}
    for k in ('id','label','path','url','semantic_model','rerank_model','entry'):sp[k]={'type':'string'}
    sp['ocr']={'type':'boolean'};sp['weight']={'type':'number','exclusiveMinimum':0}
    props['retrieval']['properties']['top_k'].update(minimum=1,maximum=50)
    props['server']['properties']['port'].update(minimum=1,maximum=65535)
    return out

def inspect(path):
    """Return issues and validated config; never echoes scalar values or reads .env."""
    import yaml
    text=Path(path).read_text(encoding='utf-8');issues=[];positions={};duplicates=[]
    def walk(n, key=''):
        positions[key]=(n.start_mark.line+1,n.start_mark.column+1)
        if isinstance(n,yaml.MappingNode):
            seen=set()
            for k,v in n.value:
                child=(key+'.' if key else '')+str(k.value)
                positions[child]=(k.start_mark.line+1,k.start_mark.column+1)
                if k.value in seen:duplicates.append(child)
                seen.add(k.value);walk(v,child)
                positions[child]=(k.start_mark.line+1,k.start_mark.column+1)
        elif isinstance(n,yaml.SequenceNode):
            for i,v in enumerate(n.value):walk(v,key+'['+str(i)+']')
    def issue(key,msg,fix=''):
        line,col=positions.get(key,positions.get(key.split('.')[0],(1,1)))
        issues.append({'key':key or '(root)','line':line,'column':col,'message':msg,'suggestion':fix})
    try:
        n=yaml.compose(text)
        if n:walk(n)
        raw=yaml.safe_load(text) if not str(path).endswith('.json') else json.loads(text)
        if raw is None:raw={}
    except (yaml.YAMLError,json.JSONDecodeError) as e:
        mark=getattr(e,'problem_mark',None)
        issues.append({'key':'(syntax)','line':mark.line+1 if mark else getattr(e,'lineno',1),'column':mark.column+1 if mark else getattr(e,'colno',1),'message':'Invalid YAML/JSON syntax.','suggestion':'Check indentation, colons and quoted strings near this line.'})
        return issues,None
    for key in duplicates:issue(key,'Duplicate key; only the last value would be used.','Keep one entry for this key.')
    def check(v, spec, key=''):
        if 'anyOf' in spec:
            if v is None:return
            spec=next(x for x in spec['anyOf'] if x.get('type')=='object')
        typ=spec.get('type');types={'object':dict,'array':list,'string':str,'integer':int,'number':(int,float),'boolean':bool}
        if typ in types and (not isinstance(v,types[typ]) or typ in ('integer','number') and isinstance(v,bool)):
            issue(key,'Expected '+typ+'.','Use a '+typ+' value.');return
        if 'enum' in spec and v not in spec['enum']:issue(key,'Unsupported choice.','Choose: '+', '.join(spec['enum']))
        for op in ('minimum','maximum','exclusiveMinimum'):
            if op in spec and (v<spec[op] if op=='minimum' else v>spec[op] if op=='maximum' else v<=spec[op]):issue(key,'Number outside allowed range.','Use '+op+' '+str(spec[op])+'.')
        if isinstance(v,dict):
            known=spec.get('properties',{})
            for k,x in v.items():
                child=(key+'.' if key else '')+str(k)
                if k in known:check(x,known[k],child)
                elif spec.get('additionalProperties') is False:
                    near=difflib.get_close_matches(str(k),known,n=1)
                    issue(child,'Unknown key.','Use '+near[0]+'.' if near else 'Remove this key or check the schema.')
                elif isinstance(spec.get('additionalProperties'),dict):check(x,spec['additionalProperties'],child)
            for k in spec.get('required',[]):
                if k not in v:issue(key+'.'+k,'Required key is missing.','Add '+k+'.')
        if isinstance(v,list):
            for i,x in enumerate(v):check(x,spec.get('items',{}),key+'['+str(i)+']')
    check(raw,editor_schema())
    cfg=None
    if not issues:
        try:cfg=schema.validate(raw)
        except (schema.ConfigError,TypeError,KeyError,AttributeError,ValueError) as e:
            msg=str(e) if isinstance(e,schema.ConfigError) else 'Configuration shape is invalid.'
            if msg.startswith('Duplicate source id'):msg='sources: Duplicate source id. Each source needs a unique id.'
            key=next((k for k in positions if k and k in msg),'')
            match=re.search(r'(sources\[\d+\](?:\.\w+)?|(?:provider|retrieval|auth|budget|app)\.\w+)',msg)
            if match:key=match.group(0)
            issue(key,msg,'Check this key against the editor schema.')
    return issues,cfg

def report(path):
    try:issues,cfg=inspect(path)
    except OSError:
        print('Cannot read config file. Check the path and permissions.');return False
    if issues:
        for i in issues:print('%s:%d:%d %s: %s %s' % (path,i['line'],i['column'],i['key'],i['message'],i['suggestion']))
    else:print('Config OK: %d source(s). No connectors or models were called.' % len(cfg['sources']))
    return not issues
