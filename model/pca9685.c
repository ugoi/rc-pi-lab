/* SPDX-License-Identifier: GPL-2.0-or-later */
#include "qemu/osdep.h"
#include "qemu/module.h"
#include "qemu/timer.h"
#include "hw/i2c/i2c.h"
#include "hw/qdev-properties.h"
#include "hw/qdev-properties-system.h"
#include "chardev/char-fe.h"
#include "qapi/error.h"
#include "pca9685_core.h"

#define TYPE_PCA9685 "pca9685"
OBJECT_DECLARE_SIMPLE_TYPE(Pca9685State, PCA9685)
struct Pca9685State {
    I2CSlave parent_obj;
    PcaCore core;
    CharBackend bridge;
    char *trace_path;
    FILE *trace;
    uint64_t seq;
};
static void record(Pca9685State *s, const char *kind, int reg, int value) {
    char line[2048];
    int n = snprintf(line, sizeof(line),
        "{\"seq\":%"PRIu64",\"ns\":%"PRId64",\"event\":\"%s\",\"reg\":%d,\"value\":%d,\"mode1\":%u,\"mode2\":%u,\"prescale\":%u,\"period_us\":%.2f,\"high_us\":[",
        ++s->seq, qemu_clock_get_ns(QEMU_CLOCK_VIRTUAL), kind, reg, value,
        s->core.r[0], s->core.r[1], s->core.r[0xfe],
        4096.0 * (s->core.r[0xfe]+1) / 25.0);
    for (int c=0; c<16; c++) n += snprintf(line+n, sizeof(line)-n,
        "%s%.2f", c ? "," : "", pca_high_ticks(&s->core,c)/25.0);
    n += snprintf(line+n, sizeof(line)-n, "]}\n");
    if (s->trace) { fputs(line,s->trace); fflush(s->trace); }
    if (qemu_chr_fe_backend_connected(&s->bridge)) qemu_chr_fe_write(&s->bridge,(uint8_t *)line,n);
}
static void bridge_event(void *opaque, QEMUChrEvent event) {
    Pca9685State *s=opaque;
    if (event == CHR_EVENT_OPENED) record(s,"bridge_open",-1,-1);
    if (event == CHR_EVENT_CLOSED) record(s,"bridge_closed",-1,-1);
}
static int event(I2CSlave *i2c, enum i2c_event e) {
    Pca9685State *s=PCA9685(i2c);
    if (e==I2C_START_SEND) { s->core.address_byte=true; record(s,"start_write",-1,-1); }
    if (e==I2C_START_RECV) record(s,"start_read",-1,-1);
    if (e==I2C_FINISH) { pca_commit(&s->core); record(s,"stop",-1,-1); }
    return 0;
}
static int pca9685_send(I2CSlave *i2c, uint8_t v) {
    Pca9685State *s=PCA9685(i2c);
    int reg=s->core.address_byte ? -1 : s->core.ptr;
    pca_send(&s->core,v); record(s,reg<0 ? "pointer" : "write",reg,v); return 0;
}
static uint8_t pca9685_recv(I2CSlave *i2c) {
    Pca9685State *s=PCA9685(i2c); int reg=s->core.ptr;
    uint8_t v=pca_recv(&s->core); record(s,"read",reg,v); return v;
}
static void reset(DeviceState *dev) {
    Pca9685State *s=PCA9685(dev); pca_reset(&s->core); record(s,"reset",-1,-1);
}
static void realize(DeviceState *dev, Error **errp) {
    Pca9685State *s=PCA9685(dev);
    if (s->trace_path) {
        s->trace=fopen(s->trace_path,"w");
        if (!s->trace) { error_setg_errno(errp,errno,"open trace"); return; }
    }
    pca_reset(&s->core);
    qemu_chr_fe_set_handlers(&s->bridge,NULL,NULL,bridge_event,NULL,s,NULL,true);
}
static void finalize(Object *obj) {
    Pca9685State *s=PCA9685(obj); if (s->trace) fclose(s->trace);
}
static const Property props[] = {
    DEFINE_PROP_CHR("chardev",Pca9685State,bridge),
    DEFINE_PROP_STRING("trace-file",Pca9685State,trace_path),
};
static void class_init(ObjectClass *klass, const void *data) {
    DeviceClass *dc=DEVICE_CLASS(klass); I2CSlaveClass *ic=I2C_SLAVE_CLASS(klass);
    dc->realize=realize; device_class_set_legacy_reset(dc,reset);
    device_class_set_props(dc,props);
    ic->event=event; ic->send=pca9685_send; ic->recv=pca9685_recv;
    dc->desc="Functional PCA9685 register and PWM model (no electrical simulation)";
}
static const TypeInfo info={.name=TYPE_PCA9685,.parent=TYPE_I2C_SLAVE,
    .instance_size=sizeof(Pca9685State),.instance_finalize=finalize,.class_init=class_init};
static void register_types(void) { type_register_static(&info); }
type_init(register_types)
