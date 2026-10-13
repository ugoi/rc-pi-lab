"""Stable owned-tab CDP client; real mouse/key events, actual browser video."""
import atexit,json,os,select,subprocess
from pathlib import Path
_proc=None

def browser_command(args):
    global _proc
    if _proc is None:
        _proc=subprocess.Popen(['node',str(Path(__file__).with_name('browser_cdp.mjs'))],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,bufsize=1)
    _proc.stdin.write(json.dumps(args)+'\n');_proc.stdin.flush()
    if not select.select([_proc.stdout],[],[],40 if args[:2]==('record','stop') else 10)[0]:
        raise TimeoutError('CDP command deadline: '+repr(args))
    line=_proc.stdout.readline()
    if not line:raise RuntimeError('CDP helper exited')
    return json.loads(line)

@atexit.register
def close():
    if _proc:
        _proc.stdin.close()
        try:_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:_proc.kill();_proc.wait(timeout=3)
