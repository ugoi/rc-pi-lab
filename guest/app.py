"""Identical application for emulated and physical Pi, original ServoKit."""
import time
from adafruit_servokit import ServoKit
kit = ServoKit(channels=16, frequency=50)
kit.servo[0].set_pulse_width_range(1000, 2000)
for angle in (0, 90, 180):
    print('ANGLE', angle, 'monotonic_ns', time.monotonic_ns(), flush=True)
    kit.servo[0].angle = angle
    time.sleep(2)
for invalid in (-1, 181):
    try:
        kit.servo[0].angle = invalid
        raise AssertionError('invalid angle accepted')
    except ValueError:
        print('INVALID_REJECTED', invalid, flush=True)
kit.servo[0].angle = None
print('FULL_OFF', flush=True)
time.sleep(2)
kit._pca.reset()
print('DRIVER_RESET_MODE1', kit._pca.mode1_reg, flush=True)
print('APP_PASS', flush=True)
