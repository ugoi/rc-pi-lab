#!/usr/bin/env python3
"""Bundle source, measured traces, logs and visuals without caches or credentials."""
from pathlib import Path
import tarfile,hashlib,json,subprocess
root=Path('.');files=[]
subprocess.run(['git','diff','--quiet'],check=True)
subprocess.run(['git','diff','--cached','--quiet'],check=True)
revision=Path('build/source-revision.txt')
revision.write_text(subprocess.check_output(['git','rev-parse','HEAD'],text=True))
files.append(revision)
for directory in ('docs','model','guest','scripts','tests'):
 files.extend(p for p in Path(directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
files.extend(Path(n) for n in ('README.md','Dockerfile','LICENSE'))
for p in Path('evidence').iterdir():
 if p.suffix in ('.log','.json','.jsonl','.tsv','.txt') and not p.name.startswith(('artifact-','workproduct-','brave-','delivery-','report-')):
  files.append(p)
files.extend(p for p in Path('build/visual').iterdir() if p.suffix in ('.png','.mp4','.html','.json'))
required=['evidence/boot-stock.log','evidence/pca-stock.jsonl','evidence/boot-image.log',
 'evidence/pca-image.jsonl','evidence/image-boot-result.json','evidence/compressed-image-check.json',
 'evidence/image-sha256.txt']
assert all(Path(n) in files for n in required), 'Required evidence missing'
manifest={p.as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(files))}
Path('build/evidence-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
with tarfile.open('build/ste91-evidence.tar.gz','w:gz') as tar:
 for p in sorted(set(files)):tar.add(p,arcname=p.as_posix(),recursive=False)
 tar.add('build/evidence-manifest.json',arcname='evidence-manifest.json')
print('build/ste91-evidence.tar.gz',Path('build/ste91-evidence.tar.gz').stat().st_size,'bytes')
