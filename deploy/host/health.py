#!/usr/bin/env python3
"""Verify loopback health and configuration lock, without public network requests."""
import argparse, json, urllib.request, urllib.error

def verify(port):
    if not 1024<=int(port)<=65535:raise ValueError('Invalid local port')
    base='http://127.0.0.1:'+str(port)
    with urllib.request.urlopen(base+'/api/health?deep=1',timeout=5) as r:health=json.load(r)
    if not health.get('ok') or not health.get('db') or health.get('degraded'):raise ValueError('Deep health failed')
    for path in ('/settings.html','/api/settings','/api/budget','/api/app-export','/api/docs-freshness'):
        try:urllib.request.urlopen(base+path,timeout=5)
        except urllib.error.HTTPError as e:
            if e.code==404:continue
        raise ValueError('Configuration is not locked: '+path)
    return health
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--port',type=int,default=8100);a=p.parse_args();verify(a.port);print('Loopback health/database and configuration lock verified. Public HTTPS not checked.')
