"""Read-only preservation witness. Never opens a CDP WebSocket or modifies a tab.

snapshot OUTPUT; verify BASELINE OUTPUT. Only URL/target hashes leave memory.
Concurrent user navigation is reported as a changed page, not blamed on a test.
"""
import collections
import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def snapshot():
    def get(route):
        with urllib.request.urlopen('http://127.0.0.1:9222/'+route, timeout=5) as response:
            return json.load(response)
    version = get('json/version')
    pages = get('json/list')
    return {'time_ns': time.time_ns(), 'browser_version': version['Browser'],
            'browser_instance_sha256': digest(version['webSocketDebuggerUrl']),
            'page_hashes': sorted(digest(p['id']+'\0'+p['url'])
                                  for p in pages if p['type']=='page')}


if __name__ == '__main__':
    if len(sys.argv) not in (3, 4) or sys.argv[1] not in ('snapshot', 'verify'):
        raise SystemExit('snapshot OUTPUT | verify BASELINE OUTPUT')
    after = snapshot()
    result = after
    if sys.argv[1] == 'verify':
        before = json.loads(Path(sys.argv[2]).read_text())
        missing = list((collections.Counter(before['page_hashes']) -
                        collections.Counter(after['page_hashes'])).elements())
        same = before['browser_instance_sha256'] == after['browser_instance_sha256']
        result = {'result': 'PASS' if same and not missing else 'FAIL',
                  'same_browser_instance': same, 'missing_or_changed_pages': missing,
                  'baseline_page_count': len(before['page_hashes']), 'after': after}
    Path(sys.argv[-1]).write_text(json.dumps(result, indent=2))
    print({k:v for k,v in result.items() if k not in ('page_hashes', 'after')})
    if result.get('result') == 'FAIL': raise SystemExit(1)
