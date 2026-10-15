"""Own disposable browser process; real mouse/key events and browser video."""
import atexit,json,os,select,subprocess,time
from pathlib import Path
_proc=None
_evidence=None

def browser_command(args):
    global _proc,_evidence
    if _proc is None:
        env=os.environ.copy()
        evidence=Path(__file__).resolve().parents[2]/'evidence/m3'
        evidence.mkdir(parents=True,exist_ok=True)
        env.setdefault('M3_BROWSER_EVIDENCE',str(evidence/f'browser-lifecycle-{time.time_ns()}.json'))
        _evidence=Path(env['M3_BROWSER_EVIDENCE'])
        _proc=subprocess.Popen(['node',str(Path(__file__).with_name('browser_cdp.mjs'))],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,bufsize=1,env=env)
    _proc.stdin.write(json.dumps(args)+'\n');_proc.stdin.flush()
    if not select.select([_proc.stdout],[],[],40 if args[:2]==('record','stop') else 10)[0]:
        close()
        raise TimeoutError('CDP command deadline: '+repr(args))
    line=_proc.stdout.readline()
    if not line:raise RuntimeError('CDP helper exited')
    return json.loads(line)

@atexit.register
def close():
    global _proc,_evidence
    if _proc:
        try:_proc.stdin.close()
        except BrokenPipeError:pass
        try:_proc.wait(timeout=7)
        except subprocess.TimeoutExpired:
            _proc.terminate()
            try:_proc.wait(timeout=7)
            except subprocess.TimeoutExpired:_proc.kill();_proc.wait(timeout=3)
        _proc.stdout.close()
        code=_proc.returncode
        _proc=None
        evidence=_evidence;_evidence=None
        if code!=0:raise RuntimeError(f'CDP helper exit {code}; check owned browser cleanup')
        lifecycle=json.loads(evidence.read_text())
        if lifecycle['remainingPids'] or not lifecycle['profileRemoved']:
            raise RuntimeError('owned browser cleanup incomplete')
