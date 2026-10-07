"""Durable, atomic request/call quotas. Dollar limits fail closed without a meter."""
import copy, datetime, hashlib, json, math, sqlite3, threading
from pathlib import Path
from .providers import ProviderError

DEFAULT = {'daily_questions': 0, 'user_daily_questions': 0, 'daily_model_calls': 0, 'spend_cap_usd': None}

class BudgetError(ProviderError):
    pass

def clean(raw):
    if not isinstance(raw, dict): raise ValueError('budget must be a mapping')
    if set(raw) - set(DEFAULT): raise ValueError('Unknown budget key')
    out = dict(DEFAULT, **raw)
    for k in ('daily_questions','user_daily_questions','daily_model_calls'):
        v=out[k]
        if isinstance(v,bool) or not isinstance(v,int) or not math.isfinite(v) or not 0 <= v <= 10000000:
            raise ValueError(k + ' must be a whole number from 0 to 10000000')
    v=out['spend_cap_usd']
    if v is not None and (isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not 0 <= v <= 1000000):
        raise ValueError('spend_cap_usd must be null or 0-1000000')
    return out

class Budget:
    def __init__(self, cfg, folder=None):
        self.value=clean(cfg.get('budget',{}));self.folder=Path(folder) if folder else None
        self.lock=threading.RLock()
        if self.folder:
            self.folder.mkdir(parents=True,exist_ok=True)
            path=self.folder/'budget.json'
            if path.exists():self.value=clean(json.loads(path.read_text()))
        self.db=sqlite3.connect(str(self.folder/'budget.db') if self.folder else ':memory:',check_same_thread=False)
        self.db.execute('CREATE TABLE IF NOT EXISTS usage(day TEXT, scope TEXT, kind TEXT, amount INTEGER, PRIMARY KEY(day,scope,kind))');self.db.commit()
    def day(self):return datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    def take(self, kind, owner=''):
        with self.lock:
            limits=[('*', self.value['daily_questions' if kind=='question' else 'daily_model_calls'])]
            if kind=='question':limits.append(('user:' + hashlib.sha256(str(owner).encode()).hexdigest(),self.value['user_daily_questions']))
            day=self.day()
            try:
                self.db.execute('BEGIN IMMEDIATE')
                for scope,limit in limits:
                    row=self.db.execute('SELECT amount FROM usage WHERE day=? AND scope=? AND kind=?',(day,scope,kind)).fetchone()
                    if limit and (row[0] if row else 0)>=limit:raise BudgetError('Daily '+kind+' limit reached. Resets at midnight UTC.',429)
                for scope,_ in limits:
                    self.db.execute('INSERT INTO usage VALUES(?,?,?,1) ON CONFLICT(day,scope,kind) DO UPDATE SET amount=amount+1',(day,scope,kind))
                self.db.commit()
            except Exception:
                self.db.rollback();raise
    def save(self, raw):
        value=clean(raw)
        with self.lock:
            if self.folder:
                path=self.folder/'budget.json';tmp=self.folder/'budget.json.tmp'
                tmp.write_text(json.dumps(value,indent=2));tmp.replace(path)
            self.value=value
        return self.view()
    def view(self):
        with self.lock:
            rows=self.db.execute('SELECT kind,amount FROM usage WHERE day=? AND scope=?',(self.day(),'*')).fetchall()
            return {'limits':copy.deepcopy(self.value),'used':dict(rows),'day':self.day(),'reset_timezone':'UTC',
                    'spend_meter':'unavailable','spend_note':'Dollar caps block all non-Demo model calls. No verified provider billing meter is installed.'}
    def wrap(self, provider):return Guarded(provider,self)

class Guarded:
    def __init__(self, provider, budget):self.provider,self.budget=provider,budget
    def _check(self):
        from .providers import Mock
        if self.budget.value['spend_cap_usd'] is not None and not isinstance(self.provider,Mock):
            raise BudgetError('Dollar cap is set, but verified billing is unavailable. Non-Demo model calls are blocked.',429)
        self.budget.take('model')
    def complete(self,messages):self._check();return self.provider.complete(messages)
    def stream(self,messages):
        self._check();yield from self.provider.stream(messages)
