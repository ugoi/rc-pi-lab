"""Verify installed original wheel bytes against upstream wheel RECORD hashes."""
import base64,csv,hashlib,json,pathlib
root=pathlib.Path('/opt/rc-lab/packages'); checked=0; failures=[]
for record in sorted(root.glob('*.dist-info/RECORD')):
    for path,digest,size in csv.reader(record.open()):
        if not digest: continue
        algorithm,expected=digest.split('=',1)
        actual=base64.urlsafe_b64encode(hashlib.new(algorithm,(root/path).read_bytes()).digest()).rstrip(b'=').decode()
        checked+=1
        if actual!=expected: failures.append(path)
print(json.dumps({'wheel_files_checked':checked,'modified_files':failures}),flush=True)
assert not failures
print('APP_SHA256',hashlib.sha256(pathlib.Path('/opt/rc-lab/app.py').read_bytes()).hexdigest(),flush=True)
