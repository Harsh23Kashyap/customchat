"""Explicit source/document readers. Missing policy is public, empty readers deny all."""
import copy

def restricted(cfg):return any('read_users' in s or s.get('document_users') for s in cfg['sources'])
def source(cfg,sid):return next((s for s in cfg['sources'] if s['id']==sid),None)
def allowed(cfg,owner,sid,document=None):
    s=source(cfg,sid)
    if s is None:return not restricted(cfg) or sid=='uploads'  # own uploads are retrieved through the owner store only
    if 'read_users' in s and owner not in s['read_users']:return False
    rules=s.get('document_users',{})
    return document not in rules or owner in rules[document]
def documents(cfg,owner,sid,conn):
    if not allowed(cfg,owner,sid):return []
    s=source(cfg,sid)
    if not s or not s.get('document_users'):return None
    return sorted({d.get('document') for d in conn.docs if d.get('document') and allowed(cfg,owner,sid,d['document'])})
def view(cfg,owner,row):
    row=copy.deepcopy(row)
    if any(not allowed(cfg,owner,e.get('source'),e.get('document')) for e in row.get('evidence',[])):
        row.update(answer='This saved answer is no longer available under your document permissions.',evidence=[],ledger=[],standalone='',followups=[],scope=None)
    return row
