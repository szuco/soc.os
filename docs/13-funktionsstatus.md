# 13 – Funktionsstatus: was steht, was fehlt

Stand **16.08.2026**. Diese Datei ist die einzige Stelle, an der Hardware-,
Firmware- und Mechanikstand nebeneinander stehen. Sie beantwortet genau eine
Frage: *Was kann das Gerät heute, und was fehlt bis zum fertigen Produkt?*

Legende: ✅ fertig und geprüft · 🟡 begonnen, Rest benannt · ⛔ nicht vorhanden ·
🔒 blockiert durch eine offene Entscheidung ([`06-open-decisions.md`](06-open-decisions.md))

---

## 1. Kurzfassung

| Ebene | Stand |
|---|---|
| **Spezifikation** | ✅ vollständig — 13 Dokumente, alle Entscheidungen entweder getroffen oder als Punkt 1–52 offen benannt |
| **Mechanik** | ✅ Boards generiert; Front = BJ-Zentralscheibe 6435-914, **Adapter erzeugt und selbstgeprüft**; 🔒 offen ist die Bauhöhe des realen Displaymoduls |
| **Schaltpläne** | ✅ alle drei Boards erzeugt und netzlistengeprüft; ⛔ **keine Schaltungsreview gegen Datenblätter** |
| **Layouts** | 🟡 alle drei geroutet — 985 / 746 / 197 Segmente —, **alle drei mit Restarbeit**: offene Verbindungen und je eine lokale Kupferkollision auf Mid und Top |
| **Fertigungsdaten** | ⛔ **keine** — der frühere Top-Export war überholt und ist gelöscht; der Nutzen ist als Boarddatei erzeugt |
| **Firmware** | 🟡 **fertig übersetzt** (RAM 35 %, Flash 56 %), mit Menü und einstellbaren Fahrzeiten — aber **ohne Lasterkennung und ohne RS-485-Protokoll** |
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
| **MID** `mid_logic` | ✅ 46 Bauteile, 61 Netze | 🟡 **746 Segmente, 104 Vias**; 18 Signale offen, ein lokaler Kurzschluss | ⛔ DRC-Gate sperrt |
| **TOP** `top_ui` | ✅ 25 Bauteile, 53 Netze | 🟡 **197 Segmente, 12 Vias**; 14 Signale offen (alle vier Tasten, drei USB-Netze), eine Bahn im Befestigungsloch der USB-Buchse | ⛔ DRC-Gate sperrt |
| **Nutzen** `fab/panel` | — (Build-Ergebnis) | ✅ **173,4 × 64,4 mm**, zwei Kreise + ein Quadrat, DRC deckungsgleich mit der Summe der Einzelboards | 🟡 bestellbar, sobald geroutet |

Die 43 offenen Verbindungen auf Bottom sind **kein Rückstand des Autorouters**,
sondern Absicht: [`05-manufacturing.md`](05-manufacturing.md) Abschnitt 3 verlangt
für Leistungspfade und Buck-Schleifen ohnehin Handarbeit nach Referenzlayout.

**Zum Routing-Stand.** Am 15.08.2026 war zu korrigieren, dass frühere Fassungen
Top als vollständig und Mid als fast fertig geroutet meldeten — der Umbau auf
Reed-Kontakte, Haubenkontakt und ToF hatte beide Layouts neu erzeugt und ihre
Verdrahtung verworfen. Mid ist seit dem 16.08.2026 wieder geroutet (im
Container, siehe [`05-manufacturing.md`](05-manufacturing.md)), Top noch nicht.
Nachzählbar bleibt es: `grep -c '(segment'` liefert 985 / 746 / 0.

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
| Zwei Motoren auf/zu fahren | ✅ 2 H-Brücken, je 2 × IR2104 + 4 N-FET | ✅ `cover: template` + Fahrskripte, Umpolung über INA/INB, 300 ms Stoppause | 🟡 **fährt auf Zeit**, aber die Zeit ist **je Kanal und Richtung in HA einstellbar** |
| Hardware-Überstromabschaltung | ✅ INA240A2 → TLV3702-Fenster → 74AUP1G74 auf `~SD` | ✅ meldet `HW_TRIP1/2` nach Home Assistant, Reset-Taste vorhanden | ✅ wirkt firmwareunabhängig, **Schwelle ± 4,4 A ist gemessen begründet** (17.08.2026). ⚠️ Sie schützt die Elektronik, **nicht die Mechanik** — zum Verbiegen reichen 1,7 A. ✅ Komparator-Eingangsbereich geklärt (Punkt 57): TLV3702 statt LM393, rail-to-rail, ohne Layoutänderung |
| Strommessung anzeigen | ✅ **5 mΩ** Inline-Shunt, Kelvin, INA240A2 → 0,25 V/A, ± 6,6 A | ✅ zwei ADC-Sensoren, **Skalierung (4 A/V) und Nullpunkt (1,65 V) in HA einstellbar**, Betrag über beide Fahrtrichtungen | 🟡 taugt zur Anzeige und zum Kalibrieren, nicht zur Stall-Erkennung |
| **Lasterkennung / Stall** | ✅ Hardware vorhanden | ⛔ **fehlt vollständig** | ⛔ braucht PWM-synchrones Sampling → eigene C++-External-Component ([`09`](09-display-and-mcu.md) Abschnitt 4) |
| Endlagenerkennung | — **bewusst keine Hardware** | ⛔ | ⛔ Endlage ausschließlich über Fahrzeit + Strom. Die Reed-Kontakte gehören **nicht** dazu (Festlegung 15.08.2026) — es gibt damit **keine** absolute Positionsrückmeldung. ⚠️ **Seit 17.08.2026 schwieriger als gedacht**: Fahrt 0,3–1,0 A gegen Anschlag 1,7 A, nicht der erhoffte Faktor 40 (Punkt 54) |
| **Sanftauslauf vor der Endlage** | ✅ PWM-fähige Brücken | 🟡 **umgesetzt, aber auf Zeit**: ab einstellbaren % der Fahrzeit auf einstellbare PWM | 🟡 Am Stromverlauf festmachen kann ihn erst die C++-Komponente. **Wichtiger als gedacht**: Bei 50 % PWM liegen am Anschlag nur 0,8 A und halbes Moment an — das ist der einzige wirksame Mechanikschutz des Geräts |
| Beide Motoren gleichzeitig | ✅ Summenpfad **4,1 A** im ungünstigsten Fall | ✅ kein Interlock nötig | ✅ **entschieden 16.08.2026**, seit der Messung vom 17.08.2026 auch ohne jede Auflage an den Steckverbinder |
| Konkreter N-Kanal-MOSFET | ⛔ einziges Leistungsbauteil ohne Teilenummer | — | 🟢 Punkt 8 — **nicht mehr blockiert**: bei 1,7 A Blockierstrom genügt praktisch jeder 40-V-Typ im PowerPAK SO-8, die Auswahl ist reine Beschaffungsfrage |

### 3.2 Bedienung und Anzeige

| Funktion | Hardware | Firmware | Stand |
|---|---|---|---|
| Display | ✅ **ST7789, 1,69″ 240 × 280, quer** — füllt das Fenster der Zentralscheibe (0,07 mm Luft in der Breite); Footprint von J5 noch Platzhalter | ✅ `st7789v` nativ, Initsequenz entfallen, **Konfiguration validiert** | 🔒 Punkt 15c: Modul-Außenmaß messen; Panel-Offsets am realen Display prüfen |
| Anzeigeinhalt | — | ✅ Startbildschirm mit **allen Messwerten**: Raumklima, beide Fenster mit Sabotagezustand, Motorströme, Präsenz, Stern | ✅ frei gestaltbar im Display-Lambda |
| Vier Tasten | ✅ **4 SMD-Taster auf (±18 · ±20)**, exakt unter den Druckkreuzen | ✅ **Paarauswertung umgesetzt**: ↑ = ol+or, ↓ = ul+ur, OK = or+ur, ▷ = ol+ul | ✅ jede Taste hat zwei Bedeutungen — im Menü navigieren, sonst fahren |
| Bedienmenü | — | ✅ `graphical_display_menu` mit sechs Untermenüs; Fahrzeiten am Gerät einstellbar | ✅ Punkt 37 erledigt |
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
| **Sabotagekontakte** | ✅ 2 × Reed über **PCF8575** (P10/P11), gleiche Beschaltung wie die Verschlusskontakte | ✅ als `tamper`-Sensoren in HA | ✅ **entschieden 16.08.2026: bleiben** |

### 3.4 Ausgänge und Kommunikation

| Funktion | Hardware | Firmware | Stand |
|---|---|---|---|
| Weihnachtsstern 6,2 V | ✅ eigener Buck, P-FET-High-Side, PTC 0,2 A, 2,5-mm-Klinke | ✅ Schalter-Entität | 🔒 Punkt 30 — Platzhalter-Footprint; neue Position **unten links** in der Zentralscheibe (Punkt 44) |
| Meldekontakt Dunstabzugshaube | ✅ PhotoMOS AQY282GS, potentialfrei, **nur SELV** | ✅ Schalter-Entität, LOW = geschlossen | ✅ |
| **RS-485 (primärer Weg)** | ✅ MAX3485, Fail-Safe-Bias, Terminierung als DNP, JST-XH | ⛔ UART definiert, **aber ungenutzt**; `RS485_DIR` (GPIO48) unbelegt | ⛔ 🔒 Punkte 15b/16/38 — Transceiver-Auswahl und Registerkarte offen |
| WLAN / Home Assistant | ✅ ESP32-S3-WROOM-1-N16R8 | ✅ API, OTA, Fallback-AP | ✅ ausdrücklich **sekundär** |
| USB-C Programmierung | ✅ **stehende Buchse** (G-Switch GT-USB-7051x), zeigt nach vorn, verdeckt von der Zentralscheibe | ✅ Logging über USB-Serial-JTAG | ✅ nutzbar nach Abnahme der Scheibe — 🔒 Bauhöhe gegen 4,5 mm prüfen |
| Feldstecker für Reed + Haube | 🟡 JST-SH 6-polig auf der Mid-Rückseite, 0,4 mm neben einem Keepout | — | 🔒 **Punkt 29, P0** — es ist schlicht kein Platz |

---

## 4. Mechanik

| Teil | Stand |
|---|---|
| Board-Outline, Bohrbild, Keepouts (3 ×) | ✅ generiert, deckungsgleich, selbstgeprüft |
| Adapter für die BJ-Zentralscheibe | ✅ `mechanical/adapter.py` → STEP + STL, Selbsttest bestanden |
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
| `mechanical/adapter.py` | Adapter für die BJ-Zentralscheibe |

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
