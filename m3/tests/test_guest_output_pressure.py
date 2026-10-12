"""Guest command processing must not wait for verbose RX logging.

Actual app and PTY, ServoKit stub. This is a regression for a blocked outbound
UART, not an I2C/physics acceptance test. The bridge still requires a fresh ACK.
"""
import json,os,pty,select,subprocess,sys,tempfile,time,unittest,termios
from pathlib import Path
APP=Path(os.environ.get('M3_TEST_GUEST_APP',Path(__file__).resolve().parents[1]/'guest_control.py'))

class OutputPressure(unittest.TestCase):
    def test_apply_before_blocked_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker=Path(tmp,'applied')
            Path(tmp,'adafruit_servokit.py').write_text('''
import os
class Servo:
    def set_pulse_width_range(self,*a): pass
    @property
    def angle(self): return 90
    @angle.setter
    def angle(self,v):
        if v>100:
            with open(os.environ['APPLIED_MARKER'],'w') as f: f.write(str(v))
class ServoKit:
    def __init__(self,**kw): self.servo=[Servo(),Servo()]
''')
            master,slave=pty.openpty()
            proc=subprocess.Popen([sys.executable,'-u',str(APP)],stdin=slave,stdout=slave,stderr=slave,env={**os.environ,'PYTHONPATH':tmp,'APPLIED_MARKER':str(marker)})
            buf=b''
            def receive(kind):
                nonlocal buf
                end=time.monotonic()+3
                while time.monotonic()<end:
                    if select.select([master],[],[],.05)[0]:buf+=os.read(master,65536)
                    while b'\n' in buf:
                        line,buf=buf.split(b'\n',1)
                        if line.startswith(b'M3 '):
                            r=json.loads(line[3:])
                            if r['event']==kind:return r
                self.fail('missing '+kind)
            def send(seq,op,throttle=0):
                os.write(master,(json.dumps({'epoch':'a'*32,'seq':seq,'op':op,'steer':0,'throttle':throttle})+'\n').encode())
            try:
                receive('ready');send(1,'hello');receive('ack');send(2,'arm');receive('ack')
                # Stop only guest->host output. Incoming commands still arrive.
                # This deterministically models a blocked UART output sink.
                termios.tcflow(slave, termios.TCOOFF)
                send(3,'drive',.5)
                end=time.monotonic()+.4
                while not marker.exists() and time.monotonic()<end:time.sleep(.01)
                self.assertTrue(marker.exists(),'command blocked by output before applying ServoKit writes')
                self.assertEqual(float(marker.read_text()),135)
            finally:
                proc.kill();proc.wait(timeout=3);os.close(master);os.close(slave)

if __name__=='__main__':unittest.main()
