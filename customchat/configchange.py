"""Offline config comparison and revision-checked replacement with private backup."""
import hashlib, os, tempfile, time
from pathlib import Path
from .configdoctor import inspect
from .schema import ConfigError

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def checked(path):
    issues,cfg=inspect(path)
    if issues:raise ConfigError('Config has errors; run config-doctor first.')
    return cfg

def diff(current,candidate):
    a,b=checked(current),checked(candidate);changes=[]
    labels={'provider':'model behavior or remote requests','sources':'retrieval corpus/access','auth':'visitor access','prompt':'answer behavior','budget':'request/model quotas','storage':'saved data location','server':'network exposure','memory':'conversation context','citations':'evidence display','retrieval':'ranking/cache behavior','app':'brand/UI','schema_version':'config compatibility'}
    def walk(a,b,key=''):
        if isinstance(a,dict) and isinstance(b,dict):
            for k in sorted(set(a)|set(b)):
                walk(a.get(k),b.get(k),(key+'.' if key else '')+str(k))
        elif a!=b:
            changes.append({'key':key,'effect':labels.get(key.split('.')[0],'configuration')})
    walk(a,b)
    return {'current_sha256':digest(current),'candidate_sha256':digest(candidate),'changes':changes}

def apply(current,candidate,current_sha,candidate_sha):
    """Never copies .env or state, never follows a target symlink, no hot reload."""
    dst,src=Path(current),Path(candidate)
    if dst.is_symlink() or src.is_symlink():raise ConfigError('Use regular config files, not symlinks.')
    checked(dst);checked(src)
    old,new=dst.read_bytes(),src.read_bytes()
    if hashlib.sha256(old).hexdigest()!=current_sha or hashlib.sha256(new).hexdigest()!=candidate_sha:
        raise ConfigError('Config changed since preview. Run config-diff again.')
    if old==new:raise ConfigError('No file change to apply.')
    name=dst.with_name(dst.name+'.backup-'+str(time.time_ns()))
    fd=os.open(str(name),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'wb') as f:f.write(old);f.flush();os.fsync(f.fileno())
    fd,tmp=tempfile.mkstemp(prefix='.'+dst.name+'.',dir=str(dst.parent))
    try:
        with os.fdopen(fd,'wb') as f:f.write(new);f.flush();os.fsync(f.fileno())
        # Catch edits during backup creation. This is not a multi-writer lock.
        if dst.is_symlink() or digest(dst)!=current_sha:raise ConfigError('Current file changed; replacement stopped. Backup retained.')
        os.replace(tmp,dst)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    return str(name)
