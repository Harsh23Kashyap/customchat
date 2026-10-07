"""Small TTY-only color helper; plain logs and NO_COLOR stay plain."""
import os, sys

def styled(text, color='cyan', stream=None):
    stream=stream or sys.stdout
    enabled=stream.isatty() and 'NO_COLOR' not in os.environ and os.environ.get('TERM')!='dumb'
    if not enabled:return text
    code={'cyan':'36','green':'32','purple':'35','bold':'1'}.get(color,'36')
    return '\033['+code+'m'+text+'\033[0m'

def start_banner(workspace,url):
    print('\n'+styled('CustomChat','bold')+'  '+styled('your docs, with sources','purple'))
    print('  '+styled('Workspace','cyan')+'  '+workspace)
    print('  '+styled('Open','green')+'       '+url)
    print('  Ctrl+C to stop. Your files stay in the workspace.\n',flush=True)
