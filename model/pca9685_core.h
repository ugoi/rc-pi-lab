/* SPDX-License-Identifier: MIT
 * Functional PCA9685 register/PWM model, NXP PCA9685 Rev.4, 2015-04-16.
 * No electrical, oscillator tolerance, edge timing, OE or EXTCLK simulation.
 */
#ifndef PCA9685_CORE_H
#define PCA9685_CORE_H
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
typedef struct {
    uint8_t r[256], active[64], dirty[16], ptr;
    bool address_byte, pwm_dirty;
} PcaCore;
static inline void pca_reset(PcaCore *s) {
    memset(s, 0, sizeof(*s));
    s->r[0] = 0x11; s->r[1] = 4; s->r[2] = 0xe2;
    s->r[3] = 0xe4; s->r[4] = 0xe8; s->r[5] = 0xe0;
    s->r[0xfe] = 0x1e;
    for (int c = 0; c < 16; c++) s->r[9 + 4*c] = 0x10;
    memcpy(s->active, s->r + 6, 64);
}
static inline void pca_advance(PcaCore *s) {
    if (s->r[0] & 0x20) s->ptr = (s->ptr == 0x45 || s->ptr == 0xfe) ? 0 : s->ptr + 1;
}
static inline void pca_commit(PcaCore *s) {
    if (s->r[1] & 8) return;
    memcpy(s->active, s->r + 6, 64);
    memset(s->dirty, 0, 16);
    if (s->pwm_dirty) s->r[0] &= ~0x80;
    s->pwm_dirty = false;
}
static inline void pca_write(PcaCore *s, uint8_t a, uint8_t v) {
    if (a == 0) {
        uint8_t old = s->r[0], restart = old & 0x80;
        if (!(old & 0x10) && (v & 0x10)) {
            for (int c = 0; c < 16; c++) if (!(s->active[c*4+3] & 0x10)) restart = 0x80;
        }
        if ((v & 0x80) && !(v & 0x10)) restart = 0;
        s->r[0] = (v & 0x7f) | (old & 0x40) | restart;
    } else if (a == 1) s->r[a] = v & 0x1f;
    else if (a >= 2 && a <= 5) s->r[a] = v & 0xfe;
    else if (a == 0xfe) { if (s->r[0] & 0x10) s->r[a] = v < 3 ? 3 : v; }
    else if ((a >= 6 && a <= 0x45) || (a >= 0xfa && a <= 0xfd)) {
        if (a & 1) v &= 0x1f;
        if (a >= 0xfa) {
            for (int c = 0; c < 16; c++) {
                s->r[6+c*4+a-0xfa] = v;
                s->dirty[c] |= 1 << (a-0xfa);
            }
        } else { s->r[a] = v; s->dirty[(a-6)/4] |= 1 << ((a-6)%4); }
        s->pwm_dirty = true;
        if (s->r[1] & 8) {
            for (int c = 0; c < 16; c++) if (s->dirty[c] == 15) {
                memcpy(s->active + c*4, s->r + 6 + c*4, 4);
                s->dirty[c] = 0; s->r[0] &= ~0x80;
            }
        }
    }
}
static inline void pca_send(PcaCore *s, uint8_t v) {
    if (s->address_byte) { s->ptr = v; s->address_byte = false; }
    else { pca_write(s, s->ptr, v); pca_advance(s); }
}
static inline uint8_t pca_recv(PcaCore *s) {
    uint8_t v = s->r[s->ptr]; pca_advance(s); return v;
}
/* High time in internal 25 MHz oscillator ticks, avoiding rounding. */
static inline unsigned pca_high_ticks(PcaCore *s, int c) {
    uint8_t *r = s->active + c*4;
    unsigned n;
    if (s->r[0] & 0x50) return 0; /* sleep or no modelled external clock */
    if (r[3] & 0x10) n = 0;
    else if (r[1] & 0x10) n = 4096;
    else n = (((r[2] | (r[3]&15)<<8) - (r[0] | (r[1]&15)<<8)) & 4095);
    if (s->r[1] & 0x10) n = 4096 - n;
    return n * (s->r[0xfe]+1);
}
#endif
