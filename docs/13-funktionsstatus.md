# 13 – Funktionsstatus: was steht, was fehlt

Stand **15.08.2026**. Diese Datei ist die einzige Stelle, an der Hardware-,
Firmware- und Mechanikstand nebeneinander stehen. Sie beantwortet genau eine
Frage: *Was kann das Gerät heute, und was fehlt bis zum fertigen Produkt?*

Legende: ✅ fertig und geprüft · 🟡 begonnen, Rest benannt · ⛔ nicht vorhanden ·
🔒 blockiert durch eine offene Entscheidung ([`06-open-decisions.md`](06-open-decisions.md))

---

## 1. Kurzfassung

| Ebene | Stand |
|---|---|
| **Spezifikation** | ✅ vollständig — 13 Dokumente, alle Entscheidungen entweder getroffen oder als Punkt 1–40 offen benannt |
| **Mechanik** | 🟡 Boards generiert; die **Frontplatte ist überholt** — die Front wird auf die Busch-Jaeger Zentralscheibe 6435-914 umgestellt (Punkte 41–47) |
| **Schaltpläne** | ✅ alle drei Boards erzeugt und netzlistengeprüft; ⛔ **keine Schaltungsreview gegen Datenblätter** |
| **Layouts** | 🟡 alle drei platziert; **geroutet ist nur Bottom** (≈ 85 %), Mid und Top haben null Leiterbahnen |
| **Fertigungsdaten** | ⛔ **keine** — der frühere Top-Export war überholt und ist gelöscht; der Nutzen ist als Boarddatei erzeugt |
| **Firmware** | 🟡 ESPHome-Konfiguration validiert und funktionsfähig, aber **ohne Lasterkennung, ohne Bedienmenü, ohne RS-485-Protokoll** |
| **Bestellt / gebaut** | ⛔ nichts — kein Board gefertigt, kein Motor vermessen |

**Der kritische Pfad ist nicht das Routing, sondern die Messung.** Solange der
Blockierstrom der Motoren nicht gemessen ist ([`11-motor-data.md`](11-motor-data.md)
Abschnitt 4, Messung M6, ≈ 5 Minuten Arbeit), bleiben Sicherung, Trip-Schwelle,
Soft-Limit und der einzige noch offene Leistungshalbleiter provisorisch.

---

## 2. Hardware je Board

| Board | Schaltplan | Layout / Routing | Fertigungsdaten |
|---|---|---|---|
| **BOTTOM** `bottom_power_motor` | ✅ 102 Bauteile, 105 Netze, Netzlistenvergleich bestanden | 🟡 **985 Segmente, 102 Vias**, 43 offene Verbindungen im Motor-/Leistungsteil, 0 Kupferfehler | ⛔ wartet auf das Rest-Routing |
| **MID** `mid_logic` | ✅ 37 Bauteile, 57 Netze | ⛔ platziert, **0 Leiterbahnen** | ⛔ |
| **TOP** `top_ui` | ✅ 29 Bauteile, 53 Netze | ⛔ platziert, **0 Leiterbahnen** — Stand 15.08.2026 mit Klinke auf 6 Uhr | ⛔ |
| **Nutzen** `fab/panel` | — (Build-Ergebnis) | ✅ 178,4 × 64,4 mm, drei Ø-52-Kreise, Stege + Mausbisse | 🟡 erst mit allen drei Boards bestellbar |

Die 43 offenen Verbindungen auf Bottom sind **kein Rückstand des Autorouters**,
sondern Absicht: [`05-manufacturing.md`](05-manufacturing.md) Abschnitt 3 verlangt
für Leistungspfade und Buck-Schleifen ohnehin Handarbeit nach Referenzlayout.

**Zum Routing-Stand, korrigiert am 15.08.2026:** Frühere Fassungen dieser Datei
und der README meldeten Top als vollständig und Mid als fast fertig geroutet.
Das galt für einen Arbeitsstand, der nie eingecheckt wurde — der Umbau auf
Reed-Kontakte, Haubenkontakt und ToF hat beide Layouts neu erzeugt und ihre
Verdrahtung dabei verworfen. Nachzählbar: `grep -c '(segment'` liefert für Mid
und Top null, für Bottom 985.

**Die USB-C-Buchse stand falsch herum** (Punkt 39) — die Stecköffnung zeigte zur
Platinenmitte, die Lötpads standen über die Kante. Korrigiert: das engste Pad
liegt jetzt 3,2 mm innerhalb der Kontur, die Randabstandsverletzungen sind von
11 auf 1 gefallen. Die verbliebene gehört dem Platzhalter-Footprint der
Klinkenbuchse (Punkt 30). Getrennt davon die Nutzungsfrage: **im eingebauten
Zustand ist USB-C nicht erreichbar** (Punkt 40) — Erstflash auf dem Tisch,
danach OTA.

**Die Stackverbinder sind noch kein Verbinderpaar.** Auf allen drei Boards sitzt
derselbe Footprint (`PinSocket_2x20_P1.27mm_Vertical`) — dreimal die Buchse. Als
Platzhalter für die Mechanik ist das in Ordnung, gesteckt werden kann es nicht.
Der Plattenabstand soll aus der Steckhöhe des Verbinders kommen, nicht aus
Distanzhülsen: 🔒 Punkt 23, hochgestuft auf P0.

**Was allen drei Boards fehlt, unabhängig vom Routing:** eine Schaltungsreview.
Die Netzliste ist maschinell gegen die Sollvorgabe geprüft — dass die
IC-Pinbelegungen den Datenblättern entsprechen und die Reglerdimensionierung
stimmt, ist damit *nicht* gezeigt.

---

## 3. Gerätefunktionen

### 3.1 Antrieb und Schutz

| Funktion | Hardware | Firmware | Stand |
|---|---|---|---|
| Zwei Motoren auf/zu fahren | ✅ 2 H-Brücken, je 2 × IR2104 + 4 N-FET | ✅ `cover: time_based`, Umpolung über INA/INB, 300 ms Stoppause | 🟡 **fährt auf Zeit** (30 s Timeout), keine Positionsrückmeldung |
| Hardware-Überstromabschaltung | ✅ INA240A2 → LM393-Fenster → 74AUP1G74 auf `~SD` | ✅ meldet `HW_TRIP1/2` nach Home Assistant, Reset-Taste vorhanden | ✅ wirkt firmwareunabhängig — 🔒 **Schwelle ist eine Annahme** (Punkt 1) |
| Strommessung anzeigen | ✅ 1 mΩ Inline-Shunt, Kelvin, INA240A2 | 🟡 zwei ADC-Sensoren, Skalierung `multiply: 5.0` ist **Platzhalter** | 🟡 taugt zur Anzeige, nicht zur Auswertung |
| **Lasterkennung / Stall** | ✅ Hardware vorhanden | ⛔ **fehlt vollständig** | ⛔ braucht PWM-synchrones Sampling → eigene C++-External-Component ([`09`](09-display-and-mcu.md) Abschnitt 4) |
| Endlagenerkennung | — **bewusst keine Hardware** | ⛔ | ⛔ Endlage ausschließlich über Fahrzeit + Strom. Die Reed-Kontakte gehören **nicht** dazu (Festlegung 15.08.2026) — es gibt damit **keine** absolute Positionsrückmeldung |
| **Sanftauslauf vor der Endlage** | ✅ PWM-fähige Brücken vorhanden | ⛔ | ⛔ Ab ≈ 80 % der Fahrzeit auf ≈ 40 % PWM rampen: schont die Mechanik und macht den Stromanstieg früher auswertbar ([`../firmware/README.md`](../firmware/README.md)) |
| Interlock „nur ein Motor gleichzeitig" | — | ⛔ | 🔒 Punkt 3 — Nutzungsentscheidung, kostet nichts, entschärft Punkt 2 |
| Konkreter N-Kanal-MOSFET | ⛔ einziges Leistungsbauteil ohne Teilenummer | — | 🔒 Punkt 8, hängt am Blockierstrom |

### 3.2 Bedienung und Anzeige

| Funktion | Hardware | Firmware | Stand |
|---|---|---|---|
| Display | 🟡 **wechselt von rund auf rechteckig** (ST77916 → Kandidat ST7789 1,69″), Footprint Platzhalter | 🟡 die validierte ST77916-Konfiguration wird damit hinfällig, ST7789 ist in ESPHome nativ | 🔒 Punkt 43 — Endmaß erst nach dem Ausmessen des Scheibenfensters |
| Anzeigeinhalt | — | 🟡 Temperatur, Luftfeuchte, „anwesend" | 🟡 eine feste Seite, keine Zustände, keine Statusfarben |
| Vier Tasten | 🟡 8 SMD-Taster, je 2 parallel, r = 23,2 mm auf den **Diagonalen** — die Zentralscheibe drückt möglicherweise auf den **Achsen** | 🟡 fest auf Jalousie 1 auf/zu und Jalousie 2 auf/zu verdrahtet | 🔒 **Punkt 42** — Druckpunkte messen; liegen sie auf den Achsen, kollidieren die Taster mit den Befestigungsbohrungen und das Bohrbild **aller drei** Boards wandert |
| Bedienmenü | — | ⛔ | ⛔ Die Scheibe bringt die Beschriftung mit (*play / hoch / runter / OK*) — die Zustandsmaschine dahinter fehlt (Punkt 37) |
| Displayhelligkeit | ✅ PWM-Backlight auf GPIO43 | ✅ dimmbar, Präsenz weckt auf 80 %, 120 s Nachlauf | ✅ |
| Helligkeit nach Umgebungslicht | ⛔ kein Sensor bestückt | ⛔ | 🔒 Punkt 36 — evtl. kostenlos über den Ambient-Zähler des VL53L1X |
| Signalton / Alarm | ✅ Piezo passiv + Treiberstufe | 🟡 `rtttl`, nur eine Test-Schaltfläche | 🟡 kein Alarmkonzept, keine Zuordnung zu Ereignissen |
| **BIST beim Hochlauf** | ✅ Piezo und Display vorhanden | ⛔ | ⛔ als Regel festgehalten, nicht umgesetzt — in einer zugeschraubten Dose der einzige Funktionsnachweis |
| **Heartbeat** | ✅ Piezo/Display/Expander vorhanden | ⛔ | ⛔ trennt „Firmware hängt" von „Bus gestört" |

### 3.3 Sensorik

| Funktion | Hardware | Firmware | Stand |
|---|---|---|---|
| Temperatur + Feuchte **des Raums** | 🟡 SHT40-AD1B, 0x44 — braucht Lüftungsschlitze in der Scheibe | ✅ `sht4x`, 30 s | 🔒 **Punkt 46** — Raummessung ist jetzt Anforderung, ein externer Fühler ist ausgeschlossen. Ohne Schlitze, Entkopplung und Offset misst der Sensor die Dose |
| Externer Temperaturfühler | ⛔ | ⛔ | ✅ **entschieden: gibt es nicht** (Punkt 46 ersetzt Punkt 35) |
| Präsenz vor dem Display | ✅ VL53L1X auf Top, Fenster im oberen Steg | 🟡 nur der Interrupt-Pin über den Expander | 🟡 „jemand da / nicht da", **keine Entfernung** |
| Durchstiegsmeldung durchs Fenster | ✅ derselbe Sensor | ⛔ | 🔒 Punkt 31 — braucht Distanzwert und ROI-Umschaltung, also eine External Component |
| Blendungserkennung (Sonne) | ✅ Statusflags des Sensors | ⛔ | 🔒 Punkt 32 — am realen Fenster zu messen |
| **Fensterkontakte (Reed)** | ✅ 2 × Reed, Pull-up, RC, ESD | ✅ als `window`-Sensoren in HA | ✅ Zweck ist die **Fensterabsicherung**, nicht die Ladenposition |
| **Sabotagekontakte** | ⛔ keine Eingänge frei (PCF8574 P0–P7 belegt) | ⛔ | 🔒 **Punkt 34, P0** — im Ursprungsentwurf vorhanden, hier verloren; entweder zweiter Expander oder schriftlich streichen |

### 3.4 Ausgänge und Kommunikation

| Funktion | Hardware | Firmware | Stand |
|---|---|---|---|
| Weihnachtsstern 6,2 V | ✅ eigener Buck, P-FET-High-Side, PTC 0,2 A, 2,5-mm-Klinke | ✅ Schalter-Entität | 🔒 Punkt 30 — Platzhalter-Footprint; neue Position **unten links** in der Zentralscheibe (Punkt 44) |
| Meldekontakt Dunstabzugshaube | ✅ PhotoMOS AQY282GS, potentialfrei, **nur SELV** | ✅ Schalter-Entität, LOW = geschlossen | ✅ |
| **RS-485 (primärer Weg)** | ✅ MAX3485, Fail-Safe-Bias, Terminierung als DNP, JST-XH | ⛔ UART definiert, **aber ungenutzt**; `RS485_DIR` (GPIO48) unbelegt | ⛔ 🔒 Punkte 15b/16/38 — Transceiver-Auswahl und Registerkarte offen |
| WLAN / Home Assistant | ✅ ESP32-S3-WROOM-1-N16R8 | ✅ API, OTA, Fallback-AP | ✅ ausdrücklich **sekundär** |
| USB-C Programmierung | 🟡 nativer USB des S3, ESD-Schutz, D+/D− über den Stack — **die Buchse wird von liegend auf stehend umgebaut** | ✅ Logging über USB-Serial-JTAG | 🔒 Punkt 45 — nach vorn zeigend, verdeckt von der Zentralscheibe, nutzbar nach deren Abnahme |
| Feldstecker für Reed + Haube | 🟡 JST-SH 6-polig auf der Mid-Rückseite, 0,4 mm neben einem Keepout | — | 🔒 **Punkt 29, P0** — es ist schlicht kein Platz |

---

## 4. Mechanik

| Teil | Stand |
|---|---|
| Board-Outline, Bohrbild, Keepouts (3 ×) | ✅ generiert, deckungsgleich, selbstgeprüft |
| Frontplatte mit vier Sicheltasten | ✅ `mechanical/frontplate.py` → STEP + STL, mit Selbsttest |
| Tiefenbudget 61 mm | 🟡 gerechnet, 🔒 mit realen Bauteilhöhen nachzurechnen (Punkte 26, 14) |
| Passung im realen 55er-Rahmen | ⛔ 🔒 Punkt 25 — Testdruck steht aus |
| Bohrbild gegen reale Dose | ⛔ 🔒 Punkt 28 |

---

## 5. Werkzeuge

Alles Generierte ist reproduzierbar; die Werkzeuge prüfen ihr Ergebnis selbst.

| Werkzeug | Zweck |
|---|---|
| `tools/gen_boards.py` | Board-Mechanik aller drei Projekte |
| `tools/gen_bottom_sch.py`, `gen_mid_sch.py`, `gen_top_sch.py` | Schaltpläne + Netzlistenvergleich |
| `tools/stack_pinout.py` | **gemeinsame** Quelle des Stack-Pinmappings — die Boards können nicht auseinanderlaufen |
| `tools/gen_layouts.py` | Platzierung, Netze, Zonen |
| `tools/route_boards.py`, `gnd_stitch.py`, `gnd_connect.py`, `gnd_iterate.py` | Routing-Pipeline und Masseanbindung |
| `tools/gen_fab.py` | Gerber/Drill/Pos + Stücklisten, **nur nach bestandenem DRC-Gate** |
| `tools/gen_panel.py` | Fertigungsnutzen aus den drei Quellprojekten |
| `mechanical/frontplate.py` | Frontplatte |

---

## 6. Reihenfolge der nächsten Schritte

1. **Blockierstrom messen** (M6, Multimeter, 5 min) → Punkte 1, 8, 2 werden entscheidbar.
2. **Punkt 34 entscheiden**: Sabotagekontakte nachrüsten oder schriftlich streichen.
   Zusammen mit Punkt 29 (Feldstecker) — beide betreffen dieselbe Ecke des Mid-Boards.
3. **Routing**: Mid und Top von Grund auf, Bottom die restlichen 43 Verbindungen
   im Leistungsteil von Hand.
5. **Schaltungsreview** gegen Datenblätter, Reglerlayouts gegen Referenzdesign.
6. **Fertigungsdaten** für Mid und Bottom, dann den Nutzen bestellen.
7. **Firmware**: External Component für Strommessung, Lasterkennung und VL53L1X-Distanz —
   der größte zusammenhängende Brocken, und alle drei Funktionen fallen in dieselbe Komponente.

Detaillierte Arbeitsschritte: [`07-roadmap.md`](07-roadmap.md).
