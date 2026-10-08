#include <assert.h>
#include <stdio.h>
#include "../model/pca9685_core.h"
int main(void) {
    PcaCore s; pca_reset(&s);
    assert(s.r[0]==0x11 && s.r[1]==4 && s.r[0xfe]==30);
    assert(pca_high_ticks(&s,0)==0);
    pca_write(&s,0xfe,121); pca_write(&s,0,0x20);
    pca_write(&s,0xfe,10); assert(s.r[0xfe]==121); /* only asleep */
    pca_write(&s,6,0); pca_write(&s,7,0);
    pca_write(&s,8,0x33); pca_write(&s,9,1);
    assert(pca_high_ticks(&s,0)==0); /* change on STOP */
    pca_commit(&s); assert(pca_high_ticks(&s,0)==307*122);
    pca_write(&s,7,0x10); pca_commit(&s);
    assert(pca_high_ticks(&s,0)==4096*122);
    pca_write(&s,9,0x10); pca_commit(&s);
    assert(pca_high_ticks(&s,0)==0); /* full off wins */
    pca_write(&s,0xfa,0); pca_write(&s,0xfb,0);
    pca_write(&s,0xfc,0x66); pca_write(&s,0xfd,1); pca_commit(&s);
    for(int c=0;c<16;c++) assert(pca_high_ticks(&s,c)==358*122);
    pca_write(&s,0,0x30); assert(s.r[0]&0x80);
    assert(pca_high_ticks(&s,0)==0);
    pca_write(&s,0,0xa0); assert(!(s.r[0]&0x80));
    assert(pca_high_ticks(&s,0)==358*122);
    pca_write(&s,1,0x14); assert(pca_high_ticks(&s,0)==(4096-358)*122);
    pca_write(&s,1,0x0c); pca_write(&s,8,0x77);
    assert(pca_high_ticks(&s,0)==358*122); /* four bytes required */
    pca_write(&s,6,0); pca_write(&s,7,0); pca_write(&s,9,1);
    assert(pca_high_ticks(&s,0)==375*122); /* change on fourth ACK */
    s.ptr=0x45; pca_advance(&s); assert(s.ptr==0);
    s.ptr=0xfe; pca_advance(&s); assert(s.ptr==0);
    pca_write(&s,0,0); s.ptr=6; pca_advance(&s); assert(s.ptr==6);
    pca_write(&s,0,0x50); pca_write(&s,0,0); assert(s.r[0]&0x40);
    pca_reset(&s); assert(!(s.r[0]&0x40));
    pca_write(&s,0,0x20);
    pca_write(&s,6,0); pca_write(&s,7,15);
    pca_write(&s,8,0); pca_write(&s,9,1); pca_commit(&s);
    assert(pca_high_ticks(&s,0)==512*31); /* ON wraps over counter zero */
    s.address_byte=true; pca_send(&s,6); pca_send(&s,0x42); pca_send(&s,0x03);
    assert(s.r[6]==0x42 && s.r[7]==0x03 && s.ptr==8);
    puts("PASS: reset, prescale, STOP/ACK, PWM, full-on/off, all-led, sleep/restart, invert, AI wrap, sticky EXTCLK");
}
