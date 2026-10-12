# M3 QA-Korrektur F1/F2 — CTO-Prüfung

Unabhängige Ausgangs-QA: FAIL auf `387711d09211a8af284f088f50e53d58385024ac`
(STE-114, Berichtrevision `18c3304a-904a-4cb3-bb05-2658a3825870`). Dieser Bericht
ersetzt das historische QA-Urteil nicht. Die Nachprüfung erfolgt auf STE-114.

## Ursache und Änderung

F1 lokal zweimal reproduziert: vollständiges Linux-/App-ready und 631 unveränderte
Paketdateien, aber bis 600 Wandsekunden kein ACK. Der zweite Lauf schaltet allein
QEMUs UART-Trace hinzu: Host-Hello beginnt vor Linux-Bereitschaft, Linux liest
beim begrenzten Drain 32 Bytes, QEMU füllt währenddessen nach; anschließend bleibt
der RX-FIFO 16/16 voll und `can_receive=0`, ohne weitere RX-Lesevorgänge. Der
Gast kann weiter schreiben (`ready`), empfängt aber die späteren Hello nicht. Alle 49 empfangenen Bytes entsprechen
dem Präfix des ersten 172-Byte-Hello; der Stillstand liegt damit vor dem späteren
Reader/Timer-Burst.
Die offiziellen PL011-Quellen erläutern den dazu passenden Schwellwert-/Drain-
Mechanismus; der konkrete Stillstand ist durch den lokalen Trace nachgewiesen.

Die Bridge wartet jetzt vor dem ersten Hello auf Gast-ready nach Raw-UART und
neutralem I2C/PWM. Wiederholte Ready-Meldungen im disarmten Gast ermöglichen
Bridge-Neustart. Sie zählen weder als ACK noch als Liveness und erneuern das
Versuchsbudget nicht. Alle Hello-Sendepfade teilen eine zentrale Sperre von
mindestens einer Wandsekunde; höchstens drei Versuche pro Verbindung. Die separate
Reader/Timer-Rennbedingung ist durch einen vorher fehlschlagenden Regressionstest
belegt. QEMU, Kernel, DTB, I2C/PCA-Modell und Originalpakete bleiben unverändert.

F2: Die Physik setzt bei Ablauf aktuell `STOPPED / bridge_timeout / stale` und
behält den alten ARMED-Eingang nur in `source` als historische Korrelation.
Reversal-Braking überschreibt den Fehlergrund nicht. Bei fehlender Datei wird
kein alter Eingang wiederverwendet. Browserstart, fehlende Gastantwort und
Verbindungsverlust erhalten deutsche Erklärungen. Ein eingefrorenes Bild wird
als letzter Stand markiert; aktuelle Geschwindigkeit wird bei HTTP-Ausfall
nicht vorgetäuscht. Manuelles Neu-Armen bleibt erforderlich.

## Prüfungen

Unveränderte Grenzen vor der Prüfung: vollständiger Start höchstens 600 s;
Stop <0,03 m/s innerhalb 2,5 s bei Maximalgas. Alle Versuche bleiben im Rohpaket.
Keine Priming-Kommandos, keine stillen Overrides, keine Wiederholungen bis PASS.

| Prüfung | Ergebnis |
|---|---|
| Alter Stand: erster Start / Trace-Start | FAIL / FAIL, je 600 s ohne ACK (Diagnose) |
| Erster Korrekturkandidat, normal | PASS, 278,04 s (vor finaler Anzeige-/Methodenfassung) |
| Aktueller Steuerkern, Fault-Start | PASS, 251.395 s |
| SIGSTOP bei 0,555 m/s | PASS, Stop 1.240 s; PWM 1995,92 µs gehalten |
| Vollständiger Neustart nach SIGSTOP | PASS, 240.592 s; neue Epoche, neutral |
| Crash bei 0,555 m/s | PASS, Stop 1.304 s; PWM 1995,92 µs gehalten |
| Idle nach Crash | PASS, Exit 77 / Idle-init, 60.23 s ohne Wiederanlauf |
| Vollständiger Neustart nach Crash | PASS, 223.661 s; neue Epoche, neutral |
| Fahren / Lenken / Rückwärts / Stop | PASS, Stop 0.156 s |
| Alte Epoche / Sequenz / abgelaufenes Ticket | PASS, 409; kein Wiederanfahren |
| Finaler Normalstart ohne Test-Hooks | PASS, 222.199 s |
| Finale Browserfahrt + Bridge-SIGKILL | PASS, Stop 1.160 s bei 0.555 m/s; bridge_timeout |
| Finale Browseranzeige / Bridge-Neustart | PASS, VERBINDUNG UNTERBROCHEN / LETZTER STAND, danach GESTOPPT; neue Epoche |

Finaler Browserlauf: 21/21 bewegte Physiksamples mit echten Gast-ACKs korreliert; Dispatch→Physik Median 228 ms, p95 330 ms (9 kurze Fahrsequenzsamples). Simulationsfaktor Median 0.971×. Nur VM202-interne Uhren, kein Remote-/Pi-Leistungsbeweis. Jede Verbindung benötigt hier genau einen Hello; der Mehrfachversuchsabstand ist zusätzlich gezielt getestet. Die drei Fault-Phase-Boots und der finale Normalstart verwenden den unveränderten gelieferten Steuerkern; die erste Normalprobe war eine frühere Korrekturfassung. Alle fünf Audits meldeten 631 unveränderte Paketdateien.


Hostprüfungen: 16 Bridge-Tests, 4 Aktuatorzustand-Tests, ein Gastprotokolltest
mit echter PTY (ServoKit-Stub, kein I2C-Beweis), direkte JS-Statusassertionen,
Python-/JS-Syntax und undefinierte Namen bestanden. Live-Prüfungen verwenden
Browser/HTTP → echten Pi-3-Linux-Gast → originale Adafruit-Bibliotheken → Linux-
I2C → PCA9685/PWM → Webots. Das Modell wurde nicht umgestellt.

## Reproduktion und Grenzen

Siehe `METHOD.md`, `m3/README.md`, `input-sha256.txt` und die nativen Lieferlinks.
QA nutzt eigenen Checkout, eigenes Image, Compose-Projekt `ste114`, Port 18091
und Container `rc-pi-m3-qa-qemu`/`rc-pi-m3-qa-webots`. Keine CTO-Container übernehmen.
Normalstart ohne Hooks zuerst; danach explizites `M3_TESTING=1` für Gastfehler.
`wait_ready.py`, `browser_bridge_fault.py`, `live_matrix.py`, `idle_after_crash.py`
und `restart_guest.py` liefern Rohbelege ohne Reparatur am Prüfstand.

Geprüfter Browser: tatsächliches vorhandenes Cloak/Chrome 146.0.7680.177 auf
VM202 über Agent Browser 0.37.1. Ein Desktop-Screenshot/Video belegt diesen Client. Mac/Safari,
entfernter persönlicher Client, physischer Pi/Firmware-Boot, reale Elektrik und
Hardware-Abschaltung bleiben ungetestet. Simulations-Stop ist keine reale
Absturzsicherheitsabnahme. Unabhängige Nachprüfung noch ausstehend.
