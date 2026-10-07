#!/usr/bin/env python3
"""Generate a one-host plan, not a deployment. No SSH, cloud or root commands."""
import argparse, ipaddress, json, os, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from customchat import schema

def prepare(app, output, domain, release, workspace, user, executable, port=8100):
    cfg=schema.load(str(app))
    if not re.fullmatch(r'[a-zA-Z0-9](?:[a-zA-Z0-9.-]{0,251}[a-zA-Z0-9])?',domain) or '.' not in domain:
        raise ValueError('Use a DNS name you own, with no scheme, port or path')
    try: ipaddress.ip_address(domain)
    except ValueError: pass
    else: raise ValueError("Use a DNS name, not an IP address")
    if not re.fullmatch(r'[a-z_][a-z0-9_-]{0,31}',user):raise ValueError('Invalid service user')
    for value in (release,workspace,executable):
        if not re.fullmatch(r'/[A-Za-z0-9_./-]+',value) or '..' in Path(value).parts:
            raise ValueError('Host paths must be absolute, without spaces or traversal')
    if not 1024<=port<=65535:raise ValueError('Port must be 1024-65535')
    if cfg['auth']['mode']=='none':raise ValueError('Public hosting needs token or accounts auth; configure it first')
    if os.environ.get('CUSTOMCHAT_DB_URL'):raise ValueError('This path supports local SQLite only; clear CUSTOMCHAT_DB_URL')
    path=cfg['storage']['path']
    if path==':memory:' or os.path.isabs(path) or '..' in Path(path).parts or '://' in path:
        raise ValueError('Use a workspace-relative SQLite storage path')
    required=[]
    def check(p):
        if p['type'] not in ('mock','ollama'):
            name=p.get('api_key_env') or {'claude':'ANTHROPIC_API_KEY','gemini':'GEMINI_API_KEY'}.get(p['type'],'')
            if not name:
                from customchat.schema import PRESET_PROVIDERS
                name=PRESET_PROVIDERS.get(p['type'],('',''))[1]
            if not name or not re.fullmatch(r'[A-Z][A-Z0-9_]*',name):raise ValueError('Remote provider needs an explicit valid key environment-variable name')
            required.append(name)
        if p.get('fallback'):check(p['fallback'])
    check(cfg['provider'])
    if cfg['auth']['mode']=='token':
        name=cfg['auth']['token_env']
        if not re.fullmatch(r'[A-Z][A-Z0-9_]*',name):raise ValueError('Token auth needs a valid token_env')
        required.append(name)
    if cfg['auth']['mode']=='accounts' and cfg['auth']['signup']:
        raise ValueError('Set auth.signup: false after creating the owner account before public hosting')
    # No inline credentials or credential-bearing URLs should enter the plan.
    from customchat.portable import _check_values
    _check_values(cfg)
    out=Path(output);out.mkdir(mode=0o700,parents=True,exist_ok=False)
    app_path=workspace+'/app.yaml'
    service=f'''[Unit]
Description=CustomChat (one host)
After=network-online.target
Wants=network-online.target
[Service]
User={user}
WorkingDirectory={workspace}
Environment=CUSTOMCHAT_CONFIG=off
Environment=PYTHONDONTWRITEBYTECODE=1
EnvironmentFile=/etc/customchat.env
ExecStart={executable} -m customchat run {app_path} --host 127.0.0.1 --port {port}
Restart=on-failure
RestartSec=5
UMask=0077
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths={workspace}
[Install]
WantedBy=multi-user.target
'''
    caddy=f'''{domain} {{
    encode gzip
    reverse_proxy 127.0.0.1:{port}
}}
'''
    env='CUSTOMCHAT_CONFIG=off\n'+'\n'.join(name+'=REPLACE_PRIVATELY_ON_HOST' for name in sorted(set(required)))+'\n'
    files={'customchat.service':service,'Caddyfile':caddy,'customchat.env.example':env,
           'plan.json':json.dumps({'app':cfg['app']['id'],'release_directory':release,'workspace':workspace,'python':executable,'port':port,'domain':domain,'required_env':sorted(set(required)),
                     'status':'prepared only; not deployed or HTTPS verified'},indent=2)+'\n'}
    for name,text in files.items():
        p=out/name;p.write_text(text);p.chmod(0o600)
    return files

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('app');p.add_argument('output');p.add_argument('--domain',required=True)
    p.add_argument('--release',default='/opt/customchat/current');p.add_argument('--workspace',default='/var/lib/customchat/app');p.add_argument('--user',default='customchat');p.add_argument('--python',default='/opt/customchat/current/.venv/bin/python');p.add_argument('--port',type=int,default=8100)
    a=p.parse_args()
    try:prepare(a.app,a.output,a.domain,a.release,a.workspace,a.user,a.python,a.port)
    except (ValueError,OSError) as e:sys.exit('Preparation stopped: '+str(e))
    print('Prepared local plan. No host changed; no DNS, TLS, cloud, registry or service commands ran.')
