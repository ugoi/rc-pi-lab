#!/usr/bin/env python3
"""Independent oracle on measured device trace and guest serial output."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('trace');p.add_argument('boot');a=p.parse_args()
rows=[json.loads(x) for x in Path(a.trace).read_text().splitlines()]
boot=Path(a.boot).read_text(errors='replace')
assert 'APP_PASS' in boot, 'guest app did not pass'
assert 'MODE1_READ' in boot, 'no successful original PureIO combined read'
assert '"modified_files": []' in boot, 'original wheel bytes not verified'
assert 'INVALID_REJECTED -1' in boot and 'INVALID_REJECTED 181' in boot
assert any(r['event']=='read' and r['reg']==0 for r in rows)
assert any(r['event']=='read' and r['reg']==254 and r['value']==121 for r in rows)
stops=[r for r in rows if r['event']=='stop']
observed=[]
for target in (1000,1500,2000):
    candidates=[r for r in stops if abs(r['high_us'][0]-target)<10 and abs(r['period_us']-20000)<30]
    assert candidates, f'missing measured PWM near {target} us'
    observed.append(candidates[0])
assert [r['seq'] for r in observed]==sorted(r['seq'] for r in observed)
assert any(r['seq']>observed[-1]['seq'] and r['high_us'][0]==0 for r in stops), 'missing full-off'
print(json.dumps({'result':'PASS','angles_from_register_path':[
    {'target_us':t,'measured_us':r['high_us'][0],'seq':r['seq'],'virtual_ns':r['ns']}
    for t,r in zip((1000,1500,2000),observed)]},indent=2))
