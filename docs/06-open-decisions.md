# 06 – Offene Entscheidungen

Legende Priorität: **P0** blockiert den nächsten Arbeitsschritt · **P1** vor
Layout-Freeze nötig · **P2** vor Fertigungsfreigabe nötig.

Welche Funktionen diese Punkte blockieren, zeigt
[`13-funktionsstatus.md`](13-funktionsstatus.md).

## Kritischer Pfad

| # | Prio | Entscheidung | Abhängig davon |
|---|---|---|---|
| 1 | **P1** | **Blockierstrom je Motor** — Datenblatt nennt ihn nicht, und ohne Motorelektronik begrenzt ihn nichts | Comparator-Referenz, Soft-Limit, Sicherung. **Nur drei Werte, keiner layoutrelevant** — der Schaltplan kann vorher beginnen, siehe [`11-motor-data.md`](11-motor-data.md) Abschnitt 5. Einfachste Messung: **M6, Ankerwiderstand mit dem Multimeter** |
| ~~1a~~ | ✅ | **PWM ist erlaubt** — der Motor hat keine eigene Elektronik, die gestört werden könnte | erledigt |
| ~~1b~~ | ✅ | **2 Adern je Motor ⇒ H-Brücke zwingend**, 6-poliger Bottom-Connector bestätigt | erledigt |
| 2 | **P0** | Hochstrom-Steckverbinder: Micro-Fit 3.0 vs. stromstärkeres System | Footprint Bottom, Tiefenbudget, Layout-Start |
| 3 | **P0** | Laufen beide Motoren gleichzeitig, oder gibt es einen Software-Interlock? | Eingangsstrom ≈ 9 A vs. ≈ 4,9 A, damit Sicherung, Leiterbahnen und Steckverbinder |

**Punkt 1 blockiert den Schaltplan nicht mehr.** Die defensive Auslegung in
[`11-motor-data.md`](11-motor-data.md) Abschnitt 5 (Annahme: 25 A Blockierstrom) hält
alle messabhängigen Größen in drei nachträglich änderbaren Werten — Comparator-
Referenz, Soft-Limit, Sicherung. Die Messung muss **vor der Bestellung** vorliegen,
nicht vor dem Schaltplan.

Punkt 3 ist eine reine Nutzungsentscheidung, kostet nichts und entschärft Punkt 2
erheblich. Für Klappläden ist sequenzieller Betrieb meist unproblematisch.

## Bauteilauswahl Leistung

| # | Prio | Entscheidung | Bemerkung |
|---|---|---|---|
| ~~4~~ | ✅ | **TPS54360DDA**, 60 V Eingang | Layout noch nach Referenzdesign prüfen |
| ~~5~~ | ✅ | **TLV62569DBV**, 180k/40k2 → 3,29 V | |
| ~~6~~ | ✅ | **TPS54360DDA**, 68k1/10k0 → 6,25 V — gleiches Bauteil wie #4 | |
| ~~7~~ | ✅ | **Diskret: 2× IR2104 + 4 N-FET je Kanal.** Begründung in [`02-motor-control.md`](02-motor-control.md) Abschnitt 2 | |
| 8 | **P1** | **Konkreter N-FET-Typ** (40 V, ≥ 60 A, PowerPAK SO-8, Rds < 5 mΩ) | einziges Leistungsbauteil ohne Teilenummer; hängt am Blockierstrom |
| ~~9~~ | ✅ | **INA240A2D**, Verstärkung 50, aus 3,3 V versorgt | Pinbelegung gegen Datenblatt prüfen |
| ~~10~~ | ✅ | **Inline-Messung**, 1 mΩ Kelvin-Shunt im Motorzweig | löst das Freilaufproblem vollständig |
| ~~11~~ | ✅ | **LM393 als Fensterkomparator + 74AUP1G74**, wirkt auf `~SD` der IR2104 | |
| 12 | P2 | USB-ORing: aktuell **zwei Schottky-Dioden** (D4/D5) | einfach und richtig; bei > 1,5 A auf `5V_SYS` durch Ideal-Diode ersetzen |
| ~~13~~ | ✅ | **BOTTOM**, `USB_VBUS` kommt über `J_STK_A` Pin 18 herunter | |
| 14 | P2 | Bulk-Kondensatoren: Typ und Bauhöhe | 470–1000 µF, aber max. ≈ 10 mm Bauraum |

## Bauteilauswahl Logik und Peripherie

| # | Prio | Entscheidung | Bemerkung |
|---|---|---|---|
| 15 | P1 | Konkretes ESP32-Modul | Antennenvariante, Bauhöhe, Pinzahl |
| ~~15a~~ | ✅ | **Display: ST77916, 1,46" rund, 360×360.** Kein Treiberaufwand — `mipi_spi` mit `model: CUSTOM` + `init_sequence`, validiert | erledigt; Sequenz in [`../firmware/esphome/st77916_init.yaml`](../firmware/esphome/st77916_init.yaml) |
| 15c | **P0** | **Modul-Außendurchmesser des real gekauften ST77916-Boards messen** | `disp_module_d` in [`../mechanical/frontplate.py`](../mechanical/frontplate.py); bestimmt über eine Zwangsbedingung den Sichel-Innenradius und damit die ganze Frontplattengeometrie |
| 15b | P2 | Modbus-Registerkarte für den RS-485-Primärbetrieb | `modbus_server` ist in ESPHome enthalten (verifiziert); Registerlayout offen |
| 16 | P1 | RS-485-Transceiver | Versorgungsspannung, Fail-Safe-Bias, Terminierung |
| ~~17~~ | ✅ | **Radar entfällt — VL53L1X (ToF) auf dem Top-Board.** Hinter dieser Frontplatte hat kein 20-mm-Radarmodul freie Sicht; der ToF passt als 4,9 × 2,5 mm großer Chip in den oberen Steg | Begründung und Grenzen in [`09-display-and-mcu.md`](09-display-and-mcu.md) Abschnitt 5 |
| 18 | P1 | Externer ADC ja/nein | folgt aus #10; betrifft `J_STK_A` |
| 19 | P1 | Temperatur- und Feuchtesensor | I2C-Adressen dürfen nicht kollidieren |
| ~~20~~ | ✅ | **`J_STK_B` v0.2** festgelegt, QSPI-Bus untergebracht | [`03-stack-pinout.md`](03-stack-pinout.md) |
| ~~21~~ | ✅ | **PhotoMOS AQY282GS statt Relais**, SELV bestätigt. Potentialfrei, 60 V / 0,8 A, kein Spulenstrom, keine Bauhöhe im 9-mm-Stapelspalt | **Gilt nur für SELV.** Erwartet die Haube 230 V, gehört das Schaltglied nicht in diese Dose |
| 22 | P2 | Speaker/Piezo und gewünschte Lautstärke | bestimmt Treiber und Stromaufnahme |
| 23 | **P0** | **Stackverbinder-Serie im 1,27-mm-Raster — und die Buchse/Stecker-Zuordnung.** Aktuell tragen **alle drei Boards denselben Footprint** (`PinSocket_2x20_P1.27mm_Vertical`), also dreimal die Buchse; drei Buchsen stecken nicht ineinander. Das ist ein Mechanik-Platzhalter, kein Verbinderpaar | Der Plattenabstand soll aus dem **Verbinder** kommen, nicht aus Distanzhülsen: Stapelverbinder gibt es in gestuften Steckhöhen (z. B. Samtec SFM/TFM oder ESQ/TSM, Harwin M50-3xx). Gesucht ist ein Paar, das gesteckt **10 mm** (Bottom↔Mid) bzw. **8–10 mm** (Mid↔Top) ergibt. Zu prüfen: Verfügbarkeit dieser Höhen im 1,27er-Raster, ≈ 1 A je Kontakt gegen [`03-stack-pinout.md`](03-stack-pinout.md) Abschnitt 2, Verpolungssicherheit A/B, und ob die Höhe des *unteren* Verbinders zum Tiefenbudget passt |
| ~~24~~ | ✅ | **USB-UART entfällt** — ESP32-S3 hat nativen USB | erledigt |

## Mechanik

| # | Prio | Entscheidung | Bemerkung |
|---|---|---|---|
| 25 | P1 | **Frontplatte gegen den festgelegten Rahmen prüfen: Busch-Jaeger 1721-914, Busch-balance SI, 1-fach** (2CKA001725A1555). Fenster 55 × 55, außen 81 × 81 × 12 mm — beides passt rechnerisch zur Platte (54,6 mm) und zu den Ohren (76 mm) | **Die offene Frage ist die Klemmbefestigung:** Der Rahmen rastet, und zwar bei den SI-Serien üblicherweise am *Tragring*. Diese Platte ersetzt den Tragring durch zwei angeformte Ohren — bietet sie den Rastnasen genug? Messliste in [`04-mechanical.md`](04-mechanical.md) Abschnitt 1b, zu klären am Testdruck |
| 26 | P1 | Bottom-Connector gerade oder abgewinkelt | größter Hebel im Tiefenbudget, siehe [`04-mechanical.md`](04-mechanical.md) |
| 27 | P2 | Schraubengröße M2,5 vs. M3 | M2,5 empfohlen |
| 28 | P2 | Bestätigung des Bohrbilds gegen reale Dose und Frontpanel | |

## Neu aufgeworfen beim Umbau vom 15.08.2026

| # | Prio | Entscheidung | Bemerkung |
|---|---|---|---|
| 29 | **P0** | **Feldstecker für Reed-Kontakte und Haubenkontakt** — auf dem Mid-Board ist *kein* Platz mehr. Nachgerechnet gegen alle Courtyards: weder vorn noch hinten passt ein 6-poliger oder auch nur 3-poliger JST, mit 4 mm Abstand zu den Befestigungsbohrungen. Aktuell steht ein JST-SH 1 mm auf der Rückseite, 0,4 mm neben dem Keepout von H2 | Vier Wege: (a) Feldsignale auf das Bottom-Board legen und `REED1/2` über die Reservepins `RSV_A2`/`RSV_A4` hochführen, (b) Piezo BZ1 (12 × 9,5 mm) verkleinern und den Platz nutzen, (c) Lötpads statt Steckverbinder, (d) Boarddurchmesser überdenken |
| 30 | **P0** | **Konkrete 2,5-mm-Klinkenbuchse** — der Footprint ist ein Platzhalter (3,5 mm vertikal, Thonkiconn), und er **passt geometrisch nicht**: 14,4 mm Körperlänge mit dem Bund in der Mitte, bei einem Lochabstand von r = 22,5 mm steht das hintere Ende 3,3 mm über die Platinenkante. Das ist die einzige verbliebene Randabstandsverletzung des Top-Boards | **Das Zielteil muss in einen Ring von r ≈ 20,9 bis 25,5 mm passen — 4,6 mm radial.** Nach innen begrenzt das Displaymodul (Ø 41,5 + 0,5 Luft), nach außen die Kontur. Dazu die bekannten Grenzen: Bauhöhe über der Platine ≤ 10,5 mm, Bundloch Ø 5,6 mm in der Frontplatte bei (0, −22,5). Pads und Bundlage aus dem Datenblatt übernehmen — die Bundachse, nicht die Footprint-Mitte, gehört auf den Lochmittelpunkt |
| 31 | P1 | **VL53L1X-Treiber**: ESPHome hat nur `vl53l0x` nativ. Für Distanzwert, ROI-Umschaltung und die Alarmauswertung ist eine External Component nötig | Fällt mit der ohnehin geplanten C++-Komponente für die Strommessung zusammen |
| 32 | P1 | **Sonnenlicht am ToF**: In der Fensterlaibung ist Fremdlicht der Störfall schlechthin. `short`-Modus und Statusflags auswerten, Blendung als eigener Zustand melden statt als Fehlalarm | vor der Freigabe am realen Fenster messen |
| 33 | P2 | **Sicheltasten sind kleiner geworden**: Steg 9 → 17 mm, Sichel je ~70° → ~45°, Stößelwinkel 18° → 12°. Seit dem 15.08.2026 trägt jeder der beiden senkrechten Stege nur noch **einen** Durchbruch (oben ToF, unten Klinke) | Damit wäre eine schmalere Stegbreite wieder denkbar — 17 mm waren für *zwei* Löcher nebeneinander gerechnet. Ob die Sicheln zurückwachsen sollen, entscheidet der Testdruck: erst am realen Teil zeigt sich, ob 45° gut zu treffen sind |

## Aus dem Vorgängerprojekt zurückgeholt (Auswertung 15.08.2026)

Herleitung und Belege: [`12-legacy-socos.md`](12-legacy-socos.md).

| # | Prio | Entscheidung | Bemerkung |
|---|---|---|---|
| 34 | **P0** | **Sabotagekontakte je Laden — zwei zusätzliche Eingänge.** Der v0-Plan und die alte Firmware hatten je Laden *zwei* Kontakte: Verschluss **und** Sabotage. Heute existiert nur der Verschlusskontakt, obwohl [`09-display-and-mcu.md`](09-display-and-mcu.md) Abschnitt 5 den fehlenden Sabotageschutz des ToF ausdrücklich auf „die Reed-Kontakte" abwälzt | **Der PCF8574 ist mit P0–P7 restlos belegt.** Nötig wären ein zweiter Expander (eigene Adresse, Platz auf Mid) oder Reservepins am Stack. Fällt mit Punkt 29 zusammen — dort ist die Steckerfrage für die *vorhandenen* Kontakte schon ungelöst. Entweder beide Punkte gemeinsam lösen oder die Sabotageüberwachung schriftlich streichen |
| 35 | **P1** | **Externer Temperaturfühler ja/nein — und was der SHT4x dann misst.** Der On-Board-SHT4x sitzt in der geschlossenen Dose über einer 9-A-Endstufe und misst damit *Elektroniktemperatur*, nicht Raumtemperatur. v0 führte einen „Externen Thermistor" als Feldsignal, v3 hatte einen eigenen Block „Internal Temperature" | Zwei fertig ausgearbeitete Altvarianten: **DS18B20** (1-Wire, 10k Pull-up, mehrere Fühler an einer Leitung — die alte Firmware kann das bereits) oder **NTC MF52-103, B = 3435, 1 %**. Entscheidet über eine weitere Feldader und damit erneut über Punkt 29. Ohne externen Fühler ist der SHT4x konsequent als Innentemperatur (Derating/Schutz) zu benennen und zu bewerten |
| 36 | P1 | **Umgebungslichtsensor für die Displayhelligkeit.** Über v0, v3 und die alte Pinout-Datei durchgehend vorgesehen („Ambient light detection", 2 Fotodioden), heute entfallen — die Helligkeit hängt allein an der ToF-Präsenz | In der Fensterlaibung ist der Dynamikumfang der Störfall: direkte Sonne bis Dunkelheit. Zu prüfen ist, ob der **VL53L1X** das mit abdeckt: sein Ambient-Rate-Zähler ist ohnehin auszuwerten (Punkt 32) und liefert ein grobes Helligkeitsmaß. Dann kostet die Funktion kein Bauteil und keinen Pin |
| 37 | P2 | **Verbindliche Tastenbelegung festlegen.** Vier Tasten, und eine davon muss aus jeder Menütiefe direkt herausführen — die Altfirmware belegte OK / Hoch / Runter / **Home**, v0 hatte dafür sogar einen fünften RESET-Taster, der heute fehlt | Betrifft nur Firmware und Beschriftung, kein Layout. Festhalten in [`../firmware/README.md`](../firmware/README.md), bevor die Display-Zustandsmaschine entsteht |
| 38 | P2 | **RS-485-Transceiver: MAX13450E als Ausgangspunkt für Punkt 16** — in v0 bereits ausgewählt, 3,3 V, Fail-Safe-Bias integriert | Ersetzt Punkt 16 nicht, verkürzt aber die Auswahl. Verfügbarkeit und Preis gegen aktuelle Alternativen prüfen |

## Am Layout gefunden (15.08.2026)

| # | Prio | Entscheidung | Bemerkung |
|---|---|---|---|
| 39 | ~~P0~~ ✅ | **Die USB-C-Buchse stand um 180° verdreht — das Top-Layout war so nicht fertigbar.** Im Footprint `USB_C_Receptacle_GCT_USB4085` liegen die THT-Pins am Ende `y = 0`, die Stecköffnung am Ende `y = +8,61` (auf F.Fab als Schlitz bei 6,1 markiert). `gen_layouts.py` drehte J1 um 180°, damit **zeigt die Öffnung zur Platinenmitte** und die Lötseite steht über den Rand | **Nicht kosmetisch:** sechs Bohrungen schneiden die Ø-52-Kontur an — die Schirmbeine um 0,22 mm, die A-Reihe um 0,15 mm. Beim Fräsen werden diese Löcher aufgeschnitten. Der Randabstands-Waiver in [`05-manufacturing.md`](05-manufacturing.md) („Pads ragen gewollt über die Kante") wurde unter der falschen Annahme erteilt, es handle sich um die Steckzunge. **Erledigt am 15.08.2026:** Drehung in `gen_layouts.py` korrigiert, Top-Layout neu erzeugt, der überholte Export `hardware/fab/top_ui.zip` gelöscht. Das engste Pad liegt jetzt 3,2 mm innerhalb der Kontur, die Randabstandsverletzungen sind von 11 auf 1 gefallen — die verbliebene gehört Punkt 30. Bleibt offen: Das Board ist neu zu routen |
| 40 | P1 | **Im eingebauten Zustand ist USB-C nicht erreichbar** — und das ist eine Festlegung, keine Panne. Die Frontplatte hat nur zwei Durchbrüche, beide auf 12 Uhr (Klinke, ToF); die Buchse sitzt auf 6 Uhr und zeigt radial nach außen in den Spalt zwischen Platine (Ø 52) und Dosenwand (lichte Weite 55–57 mm) — **1,5–2,5 mm, ein Stecker braucht ein Vielfaches** | Zu entscheiden ist nur, ob das so bleibt. Drei Wege: (a) **so lassen** — Erstflash auf dem Tisch, danach OTA über WLAN und RS-485; das ist der Normalfall bei Unterputzgeräten, (b) einen dritten Durchbruch im **unteren** Steg vorsehen und die Buchse nach vorn richten — kostet Bauhöhe und den frei gewordenen Kabelausgang, (c) Programmierkontakte (Pogo-Pads) auf der Rückseite. Fällt zusammen mit Punkt 26 (Bottom-Connector) und dem Tiefenbudget |
