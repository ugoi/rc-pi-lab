/* Current status only. Historical telemetry.source is never an active state. */
function statusView(s) {
  if (!s) return {title: 'VERBINDUNG UNTERBROCHEN', reason: 'Die Steuerbrücke ist nicht erreichbar. Keine aktuellen Fahrzeugdaten; nach Wiederverbindung neu starten.', canArm: false};
  const readiness = {
    disconnected: ['GAST NICHT VERBUNDEN', 'Die serielle Verbindung zum Pi fehlt. Fahrzeug bleibt gestoppt.'],
    booting: ['PI STARTET', 'Linux und Originalbibliotheken werden geladen und geprüft. Das kann einige Minuten dauern.'],
    handshake: ['VERBINDUNG WIRD GEPRÜFT', 'Warte auf eine frische neutrale Antwort des Pi.'],
    timeout: ['START ZEITÜBERSCHREITUNG', 'Nach 600 Sekunden keine Bereitschaft. Gast über die Startanleitung neu starten.'],
    handshake_timeout: ['GAST ANTWORTET NICHT', 'Drei neutrale Verbindungsversuche ohne frische Antwort. Gast über die Startanleitung neu starten.'],
    unresponsive: ['SICHERHEITSSTOPP', 'Das Gastprogramm antwortet nicht mehr. Kein Wiederanfahren; Gast prüfen und gegebenenfalls neu starten.'],
    missing_pwm: ['SICHERHEITSSTOPP', 'Das gemessene PWM-Signal fehlt. Antrieb gesperrt.'],
  };
  if (readiness[s.readiness]) return {title: readiness[s.readiness][0], reason: readiness[s.readiness][1], canArm: false};
  if (s.telemetry_age_s > .5 || !s.telemetry?.mode) return {title: 'PHYSIK NICHT VERBUNDEN', reason: 'Keine aktuellen Fahrzeugdaten. Start bleibt gesperrt.', canArm: false};
  const reasons = {
    bridge_timeout: 'Die Steuerbrücke liefert seit über 0,5 Sekunden keine aktuellen Befehle. Die Physik bremst.',
    bridge_disconnected: 'Die Verbindung zur Steuerbrücke fehlt. Die Physik bremst.',
    invalid_actuator_data: 'Ungültige Antriebsdaten. Die Physik bremst.',
    browser_timeout: 'Die Browsersteuerung ist ausgefallen. Zum Weiterfahren erneut starten.',
    browser_stop: 'Mit STOP angehalten. Zum Weiterfahren erneut starten.',
    guest_liveness_timeout: 'Das Gastprogramm antwortet nicht mehr. Antrieb gesperrt; erst nach frischer Antwort erneut starten.',
    late_guest_ack: 'Die Antwort des Pi kam zu spät. Sicherheitsstopp; Gas ist null. Erst nach frischer Antwort erneut starten.',
    guest_timeout: 'Der Gast hat wegen ausbleibender Befehle auf Neutral geschaltet.',
    physics_timeout: 'Die Fahrzeugsimulation antwortet nicht mehr. Start bleibt gesperrt.',
    reversal_braking: 'Vor dem Richtungswechsel wird bis zum Stillstand gebremst.',
  };
  const t = s.telemetry;
  const reason = reasons[t.reason] || reasons[s.reason];
  if (t.mode === 'ARMED' && s.mode === 'ARMED') return {title: 'FAHRBEREIT', reason: reason || 'Gas und Lenkung sind aktiv. STOP hält an und sperrt den Antrieb.', canArm: false};
  if (s.mode === 'ARMING') return {title: 'NEUTRAL WIRD BESTÄTIGT', reason: 'Die Steuerung prüft Neutral und wartet die Einschaltzeit ab.', canArm: false};
  const fault = ['guest_liveness_timeout', 'late_guest_ack', 'guest_timeout', 'physics_timeout', 'browser_timeout', 'invalid_pwm', 'missing_pwm'].includes(s.reason);
  return {title: fault ? 'SICHERHEITSSTOPP' : 'GESTOPPT', reason: reason || 'Pi und Simulation bereit. Mit Start die neutrale Steuerung freigeben.', canArm: s.readiness === 'ready' && t.source_status === 'fresh'};
}
if (typeof module !== 'undefined') module.exports = {statusView};
