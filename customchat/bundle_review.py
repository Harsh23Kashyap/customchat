"""Offline, non-executing bundle review. Findings are patterns, not safety proof."""
import ast
from collections import Counter
LIMIT=80
CATEGORIES={
 'network':{'urlopen','Request','get','post','request','connect','send','sendall','urlretrieve'},
 'environment':{'getenv','environ'},
 'files':{'open','read_text','read_bytes','write_text','write_bytes','unlink','remove','rmdir','rmtree','rename','mkdir'},
 'process':{'Popen','run','call','check_output','check_call','system','popen','fork','spawn'},
 'dynamic':{'eval','exec','compile','__import__','getattr','setattr'}}
def review(cfg,files):
 """Never import bundle modules, read environment values or contact destinations."""
 findings=[];imports=set();counts=Counter();py=[n for n in sorted(files) if n.endswith('.py')];functions=0
 for path in py:
  try:tree=ast.parse(files[path].decode('utf-8'))
  except (SyntaxError,UnicodeError):
   counts['unparsed']+=1
   if len(findings)<LIMIT:findings.append({'category':'unparsed','path':path,'line':1,'pattern':'Could not parse Python'})
   continue
  for node in ast.walk(tree):
   if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):functions+=1
   if isinstance(node,ast.Import):imports.update(a.name for a in node.names)
   if isinstance(node,ast.ImportFrom):imports.add(node.module or '(relative import)')
   name=''
   if isinstance(node,ast.Call):
    name=node.func.id if isinstance(node.func,ast.Name) else node.func.attr if isinstance(node.func,ast.Attribute) else ''
   elif isinstance(node,ast.Attribute) and node.attr=='environ':name='environ'
   if not name:continue
   for category,patterns in CATEGORIES.items():
    if name in patterns:
     counts[category]+=1
     if len(findings)<LIMIT:findings.append({'category':category,'path':path,'line':getattr(node,'lineno',1),'pattern':name})
 findings=sorted(findings,key=lambda x:(x['path'],x['line'],x['category']))
 sources=Counter(s['type'] for s in cfg.get('sources',[]))
 return {'static':True,'purpose':cfg['app']['tagline'],'purpose_basis':'Declared title/tagline and configuration, not verified behavior.',
  'python_files':len(py),'functions':functions,'file_count':len(files),'source_types':dict(sources),'imports':sorted(imports)[:40],
  'counts':dict(counts),'findings':findings,'truncated':sum(counts.values())>LIMIT,
  'scope':'Local AST pattern scan only. No code, model, network request or environment-value access.',
  'limits':'Names can match unrelated functions. Aliases, dynamic calls, dependencies and runtime behavior can evade this scan. No detected pattern does not mean absent or safe. Read all code. Bounded mode is NOT a sandbox; host files/network remain accessible.'}
