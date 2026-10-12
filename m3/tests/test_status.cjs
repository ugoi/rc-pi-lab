const assert = require('node:assert/strict');
const {statusView} = require('../web/status.js');
const s = {mode:'ARMED', reason:'neutral_arm_confirmed', readiness:'ready', telemetry_age_s:.1,
  telemetry:{mode:'STOPPED', reason:'bridge_timeout', source_status:'stale', source:{mode:'ARMED'}}};
assert.equal(statusView(s).title, 'GESTOPPT');
assert.match(statusView(s).reason, /0,5 Sekunden/);
assert.equal(statusView(s).canArm, false);
for (const readiness of ['booting','handshake','timeout','handshake_timeout','unresponsive','disconnected']) {
  const view = statusView({...s, readiness});
  assert.equal(view.canArm, false);
  assert.notEqual(view.title, 'FAHRBEREIT');
  assert.ok(view.reason.length > 20);
}
assert.match(statusView({...s, readiness:'timeout'}).reason, /600 Sekunden/);
assert.equal(statusView(null).title, 'VERBINDUNG UNTERBROCHEN');
assert.match(statusView(null).reason, /Keine aktuellen Fahrzeugdaten/);
assert.equal(statusView({...s, mode:'STOPPED', telemetry:{mode:'STOPPED',source_status:'fresh'}}).canArm,true);
console.log('UI_STATUS_PASS: stale ARMED, startup, handshake, timeout, connection loss, explicit rearm');
