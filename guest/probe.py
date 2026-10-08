import sys, time, hashlib, pathlib, importlib.metadata as md
from Adafruit_PureIO.smbus import SMBus
print('PYTHON', sys.version, flush=True)
for name in ('adafruit-circuitpython-servokit','adafruit-circuitpython-pca9685','Adafruit-Blinka','Adafruit-PureIO'):
    print('PACKAGE',name,md.version(name),flush=True)
bus=SMBus(1)
print('COMBINED_I2C_READ_BEGIN',flush=True)
try:
    print('MODE1_READ', bus.read_byte_data(0x40,0),flush=True)
except Exception as e:
    print('COMBINED_I2C_READ_FAILED',repr(e),flush=True)
    raise
finally:
    bus.close()
