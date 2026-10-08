#!/usr/bin/env python3
"""Run in the real guest after ServoKit; original PureIO via I2C_RDWR."""
from Adafruit_PureIO.smbus import SMBus
b=SMBus(1)
def write(reg,values): b.write_bytes(0x40,bytes([reg]+values))
def read(reg,count=1): return list(b.read_i2c_block_data(0x40,reg,count))
write(0,[0x30]);write(0xfe,[121]);write(0,[0x20])
write(6,[0,0,0x33,1]);assert read(6,4)==[0,0,0x33,1]
print('DEVICE_BLOCK_READ_PASS',flush=True)
write(6,[0,0x10,0,0]);assert read(7)==[0x10]
print('DEVICE_FULL_ON',flush=True)
write(9,[0x10]);assert read(9)==[0x10]
print('DEVICE_FULL_OFF_WINS',flush=True)
write(0xfa,[0,0,0x44,1]);assert read(6,4)==[0,0,0x44,1] and read(0x42,4)==[0,0,0x44,1]
print('DEVICE_ALL_LED_PASS',flush=True)
write(0,[0x30]);assert read(0)[0]&0x10
write(0xfe,[0]);assert read(0xfe)==[3]
write(0xfe,[121]);write(0,[0x20]);write(0,[0xa0]);assert read(0)==[0x20]
print('DEVICE_SLEEP_RESTART_PRESCALE_PASS',flush=True)
write(0xfd,[0x10]);b.close();print('DEVICE_MATRIX_PASS',flush=True)
