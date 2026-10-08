#!/usr/bin/env python3
"""Verify resolved wheel hashes against PyPI's version-specific metadata."""
from pathlib import Path
import concurrent.futures,hashlib,json,urllib.request,zipfile

def verify(w):
    with zipfile.ZipFile(w) as z:
        m=z.read(next(n for n in z.namelist() if n.endswith('.dist-info/METADATA'))).decode()
    name=next(l[6:] for l in m.splitlines() if l.startswith('Name: '))
    version=next(l[9:] for l in m.splitlines() if l.startswith('Version: '))
    source=f'https://pypi.org/pypi/{name}/{version}/json'
    data=json.load(urllib.request.urlopen(source,timeout=30))
    info=next(x for x in data['urls'] if x['filename']==w.name)
    sha=hashlib.sha256(w.read_bytes()).hexdigest()
    assert sha==info['digests']['sha256'], w.name
    return dict(name=name,version=version,filename=w.name,sha256=sha,url=info['url'],metadata=source,license=data['info'].get('license_expression') or data['info'].get('license'))
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
    rows=list(ex.map(verify,sorted(Path('build/wheels').glob('*.whl'))))
Path('evidence/pypi-provenance.json').write_text(json.dumps(rows,indent=2)+'\n')
print(f'PASS: {len(rows)} wheel hashes match original PyPI release metadata')
