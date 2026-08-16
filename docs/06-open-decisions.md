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
| ~~3~~ | ✅ | **Beide Motoren dürfen gleichzeitig laufen** (16.08.2026). Kein Interlock | Damit gilt der Summenpfad von **≈ 9 A** — also genau die Auslegung, die Sicherung, Leiterbahnen und Steckverbinder ohnehin schon zugrunde legen. Die Entscheidung kostet nichts, weil defensiv gerechnet wurde; sie **verschärft aber Punkt 2**: Der Hochstrom-Steckverbinder muss die 9 A wirklich können, es gibt keinen Rückzug auf 4,9 A mehr |

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
| ~~15a~~ | ❌ **überholt** | ~~Display: ST77916, 1,46" rund, 360×360~~ — ersetzt durch Punkt 43. Das runde Panel passt nicht hinter das rechteckige Fenster der Zentralscheibe | Die Initsequenz ist gelöscht; sie liegt in der Git-Historie |
| 15c | **P0** | **Außenmaß des real gekauften 1,69″-Moduls messen** — Länge × Breite × Bauhöhe samt FPC-Abgang | Bestimmt den Footprint von J5, die Sperrfläche auf dem Top-Board und die Tasche im Adapter. Der frühere Bezug auf `disp_module_d` (rundes Modul) ist mit Punkt 43 hinfällig |
| 15b | P2 | Modbus-Registerkarte für den RS-485-Primärbetrieb | `modbus_server` ist in ESPHome enthalten (verifiziert); Registerlayout offen |
| 16 | P1 | RS-485-Transceiver | Versorgungsspannung, Fail-Safe-Bias, Terminierung |
| ~~17~~ | ✅ | **Radar entfällt — VL53L1X (ToF) auf dem Top-Board.** Hinter dieser Frontplatte hat kein 20-mm-Radarmodul freie Sicht; der ToF passt als 4,9 × 2,5 mm großer Chip in den oberen Steg | Begründung und Grenzen in [`09-display-and-mcu.md`](09-display-and-mcu.md) Abschnitt 5 |
| 18 | P1 | Externer ADC ja/nein | folgt aus #10; betrifft `J_STK_A` |
| 19 | P1 | Temperatur- und Feuchtesensor | I2C-Adressen dürfen nicht kollidieren |
| ~~20~~ | ✅ | **`J_STK_B` v0.2** festgelegt, QSPI-Bus untergebracht | [`03-stack-pinout.md`](03-stack-pinout.md) |
| ~~21~~ | ✅ | **PhotoMOS AQY282GS statt Relais**, SELV bestätigt. Potentialfrei, 60 V / 0,8 A, kein Spulenstrom, keine Bauhöhe im 9-mm-Stapelspalt | **Gilt nur für SELV.** Erwartet die Haube 230 V, gehört das Schaltglied nicht in diese Dose |
| 22 | 🟡 **Bauform entschieden** | **Murata PKMCS0909E o. ä., 9 × 9 × 3 mm, passiv, SMD.** Der frühere THT-Typ (12 × 9,5) blockierte **beide** Platinenseiten — und ohne diesen Wechsel fand der 16-Bit-Expander auf dem ganzen Mid-Board keinen Platz | Offen bleibt die Lautstärke: Ein 9-mm-SMD-Wandler ist leiser als ein 12-mm-THT-Typ. Am realen Aufbau hinter der zugeschraubten Blende prüfen, ob er für BIST und Alarm reicht |
| 23 | 🟡 **Bauart und Höhe festgelegt (16.08.2026), Teilenummer offen** | **Ein Durchsteck-Stapelverbinder, dasselbe Teil auf allen drei Boards, Stapelhöhe 10 mm — in beiden Spalten gleich.** Damit steckt der Stapel direkt zusammen: keine Distanzhülsen, keine Buchse/Stecker-Zuordnung, keine zwei Bestellnummern. Bisher trugen alle drei denselben *Buchsen*-Footprint, und drei Buchsen stecken nicht ineinander | Gesucht ist die Bauart „pass-through“: Buchsenkörper mit verlängerten Schwänzen, die in die Buchse darunter greifen — bei 2,54 mm als „stackable header“ bekannt, bei 1,27 mm z. B. in Samtecs Flexible-Stacking-Programm, das Stapelhöhen frei wählen lässt. Zu prüfen: Verfügbarkeit in 2×20 mit 10 mm, ≈ 1 A je Kontakt gegen [`03-stack-pinout.md`](03-stack-pinout.md) Abschnitt 2, Verpolungssicherheit A/B. **Bis dahin ist der KiCad-Footprint ein Platzhalter — sein 3D-Modell zeigt einen rund 6 mm hohen Buchsenkörper, nicht die 10 mm Stapelhöhe** |
| ~~24~~ | ✅ | **USB-UART entfällt** — ESP32-S3 hat nativen USB | erledigt |

## Mechanik

| # | Prio | Entscheidung | Bemerkung |
|---|---|---|---|
| 25 | P1 | **Frontplatte gegen den festgelegten Rahmen prüfen: Busch-Jaeger 1721-914, Busch-balance SI, 1-fach** (2CKA001725A1555). Fenster 55 × 55, außen 81 × 81 × 12 mm — beides passt rechnerisch zur Platte (54,6 mm) und zu den Ohren (76 mm) | **Die offene Frage ist die Klemmbefestigung:** Der Rahmen rastet, und zwar bei den SI-Serien üblicherweise am *Tragring*. Diese Platte ersetzt den Tragring durch zwei angeformte Ohren — bietet sie den Rastnasen genug? Messliste in [`04-mechanical.md`](04-mechanical.md) Abschnitt 1b, zu klären am Testdruck |
| 26 | P2 | Bottom-Connector gerade oder abgewinkelt | War der größte Hebel im Tiefenbudget — **seit das Top-Board vor die Dose gewandert ist, stehen rund 17 mm Reserve statt 9** ([`04-mechanical.md`](04-mechanical.md) Abschnitt 4). Die Entscheidung bleibt, blockiert aber nichts mehr |
| 27 | P2 | Schraubengröße M2,5 vs. M3 | M2,5 empfohlen |
| 28 | P2 | Bestätigung des Bohrbilds gegen reale Dose und Frontpanel | |

## Neu aufgeworfen beim Umbau vom 15.08.2026

| # | Prio | Entscheidung | Bemerkung |
|---|---|---|---|
| 29 | ✅ **gelöst (16.08.2026)** | **Zwei Stecker statt einem.** Ein 8-poliger JST-SH (11,9 mm) findet nachweislich keinen Platz; ein 6-poliger für die vier Reed-Signale und ein 2-poliger für den Haubenkontakt finden beide einen. Nebeneffekt: Eingänge und potentialfreier Schaltausgang sind sauber getrennt. Ursprünglicher Text: **Feldstecker für Reed-Kontakte und Haubenkontakt** — auf dem Mid-Board ist *kein* Platz mehr. Nachgerechnet gegen alle Courtyards: weder vorn noch hinten passt ein 6-poliger oder auch nur 3-poliger JST, mit 4 mm Abstand zu den Befestigungsbohrungen. Aktuell steht ein JST-SH 1 mm auf der Rückseite, 0,4 mm neben dem Keepout von H2 | Vier Wege: (a) Feldsignale auf das Bottom-Board legen und `REED1/2` über die Reservepins `RSV_A2`/`RSV_A4` hochführen, (b) Piezo BZ1 (12 × 9,5 mm) verkleinern und den Platz nutzen, (c) Lötpads statt Steckverbinder, (d) Boarddurchmesser überdenken |
| 30 | **P0** | **Konkrete 2,5-mm-Klinkenbuchse** — der Footprint ist ein Platzhalter (3,5 mm vertikal, Thonkiconn), und er **passt geometrisch nicht**: 14,4 mm Körperlänge mit dem Bund in der Mitte, bei einem Lochabstand von r = 22,5 mm steht das hintere Ende 3,3 mm über die Platinenkante. Das ist die einzige verbliebene Randabstandsverletzung des Top-Boards | **Das Zielteil muss in einen Ring von r ≈ 20,9 bis 25,5 mm passen — 4,6 mm radial.** Nach innen begrenzt das Displaymodul (Ø 41,5 + 0,5 Luft), nach außen die Kontur. Dazu die bekannten Grenzen: Bauhöhe über der Platine ≤ 10,5 mm, Bundloch Ø 5,6 mm in der Frontplatte bei (0, −22,5). Pads und Bundlage aus dem Datenblatt übernehmen — die Bundachse, nicht die Footprint-Mitte, gehört auf den Lochmittelpunkt |
| 31 | P1 | **VL53L1X-Treiber**: ESPHome hat nur `vl53l0x` nativ. Für Distanzwert, ROI-Umschaltung und die Alarmauswertung ist eine External Component nötig | Fällt mit der ohnehin geplanten C++-Komponente für die Strommessung zusammen |
| 32 | P1 | **Sonnenlicht am ToF**: In der Fensterlaibung ist Fremdlicht der Störfall schlechthin. `short`-Modus und Statusflags auswerten, Blendung als eigener Zustand melden statt als Fehlalarm | vor der Freigabe am realen Fenster messen |
| 33 | P2 | **Sicheltasten sind kleiner geworden**: Steg 9 → 17 mm, Sichel je ~70° → ~45°, Stößelwinkel 18° → 12°. Seit dem 15.08.2026 trägt jeder der beiden senkrechten Stege nur noch **einen** Durchbruch (oben ToF, unten Klinke) | Damit wäre eine schmalere Stegbreite wieder denkbar — 17 mm waren für *zwei* Löcher nebeneinander gerechnet. Ob die Sicheln zurückwachsen sollen, entscheidet der Testdruck: erst am realen Teil zeigt sich, ob 45° gut zu treffen sind |

## Aus dem Vorgängerprojekt zurückgeholt (Auswertung 15.08.2026)

Herleitung und Belege: [`12-legacy-socos.md`](12-legacy-socos.md).

| # | Prio | Entscheidung | Bemerkung |
|---|---|---|---|
| 34 | ✅ **entschieden und umgesetzt (16.08.2026)** | **Die Sabotageüberwachung bleibt — vier Reed-Kontakte, zwei je Fenster.** Umgesetzt über einen **PCF8575** (16 Bit) statt des PCF8574: gleiche Adresse, gleicher Treiber, ein Bauteil statt zwei, SSOP-24 auf der Rückseite. Verschluss auf P6/P7, Sabotage auf P10/P11 (ESPHome 8/9), P12–P17 Reserve. Ursprünglicher Text: **Sabotagekontakte je Laden — zwei zusätzliche Eingänge.** Der v0-Plan und die alte Firmware hatten je Laden *zwei* Kontakte: Verschluss **und** Sabotage. Heute existiert nur der Verschlusskontakt, obwohl [`09-display-and-mcu.md`](09-display-and-mcu.md) Abschnitt 5 den fehlenden Sabotageschutz des ToF ausdrücklich auf „die Reed-Kontakte" abwälzt | **Der PCF8574 ist mit P0–P7 restlos belegt.** Nötig wären ein zweiter Expander (eigene Adresse, Platz auf Mid) oder Reservepins am Stack. Fällt mit Punkt 29 zusammen — dort ist die Steckerfrage für die *vorhandenen* Kontakte schon ungelöst. Entweder beide Punkte gemeinsam lösen oder die Sabotageüberwachung schriftlich streichen |
| 35 | **P1** | **Externer Temperaturfühler ja/nein — und was der SHT4x dann misst.** Der On-Board-SHT4x sitzt in der geschlossenen Dose über einer 9-A-Endstufe und misst damit *Elektroniktemperatur*, nicht Raumtemperatur. v0 führte einen „Externen Thermistor" als Feldsignal, v3 hatte einen eigenen Block „Internal Temperature" | Zwei fertig ausgearbeitete Altvarianten: **DS18B20** (1-Wire, 10k Pull-up, mehrere Fühler an einer Leitung — die alte Firmware kann das bereits) oder **NTC MF52-103, B = 3435, 1 %**. Entscheidet über eine weitere Feldader und damit erneut über Punkt 29. Ohne externen Fühler ist der SHT4x konsequent als Innentemperatur (Derating/Schutz) zu benennen und zu bewerten |
| 36 | P1 | **Umgebungslichtsensor für die Displayhelligkeit.** Über v0, v3 und die alte Pinout-Datei durchgehend vorgesehen („Ambient light detection", 2 Fotodioden), heute entfallen — die Helligkeit hängt allein an der ToF-Präsenz | In der Fensterlaibung ist der Dynamikumfang der Störfall: direkte Sonne bis Dunkelheit. Zu prüfen ist, ob der **VL53L1X** das mit abdeckt: sein Ambient-Rate-Zähler ist ohnehin auszuwerten (Punkt 32) und liefert ein grobes Helligkeitsmaß. Dann kostet die Funktion kein Bauteil und keinen Pin |
| 37 | ✅ **umgesetzt (16.08.2026)** | **Bedienung steht.** `graphical_display_menu` mit Untermenüs für beide Jalousien, Sanftauslauf, Stern, Haube und Messwerte; die vier Tasten navigieren im Menü und fahren außerhalb. Die Zentralscheibe bringt die Beschriftung mit (↑ ▷ ↓ OK). Ursprünglicher Text: **Verbindliche Tastenbelegung festlegen.** Vier Tasten, und eine davon muss aus jeder Menütiefe direkt herausführen — die Altfirmware belegte OK / Hoch / Runter / **Home**, v0 hatte dafür sogar einen fünften RESET-Taster, der heute fehlt | Betrifft nur Firmware und Beschriftung, kein Layout. Festhalten in [`../firmware/README.md`](../firmware/README.md), bevor die Display-Zustandsmaschine entsteht |
| 38 | P2 | **RS-485-Transceiver: MAX13450E als Ausgangspunkt für Punkt 16** — in v0 bereits ausgewählt, 3,3 V, Fail-Safe-Bias integriert | Ersetzt Punkt 16 nicht, verkürzt aber die Auswahl. Verfügbarkeit und Preis gegen aktuelle Alternativen prüfen |

## Am Layout gefunden (15.08.2026)

| # | Prio | Entscheidung | Bemerkung |
|---|---|---|---|
| 39 | ~~P0~~ ✅ | **Die USB-C-Buchse stand um 180° verdreht — das Top-Layout war so nicht fertigbar.** Im Footprint `USB_C_Receptacle_GCT_USB4085` liegen die THT-Pins am Ende `y = 0`, die Stecköffnung am Ende `y = +8,61` (auf F.Fab als Schlitz bei 6,1 markiert). `gen_layouts.py` drehte J1 um 180°, damit **zeigt die Öffnung zur Platinenmitte** und die Lötseite steht über den Rand | **Nicht kosmetisch:** sechs Bohrungen schneiden die Ø-52-Kontur an — die Schirmbeine um 0,22 mm, die A-Reihe um 0,15 mm. Beim Fräsen werden diese Löcher aufgeschnitten. Der Randabstands-Waiver in [`05-manufacturing.md`](05-manufacturing.md) („Pads ragen gewollt über die Kante") wurde unter der falschen Annahme erteilt, es handle sich um die Steckzunge. **Erledigt am 15.08.2026:** Drehung in `gen_layouts.py` korrigiert, Top-Layout neu erzeugt, der überholte Export `hardware/fab/top_ui.zip` gelöscht. Das engste Pad liegt jetzt 3,2 mm innerhalb der Kontur, die Randabstandsverletzungen sind von 11 auf 1 gefallen — die verbliebene gehört Punkt 30. Bleibt offen: Das Board ist neu zu routen |
| 40 | P1 | **Im eingebauten Zustand ist USB-C nicht erreichbar** — und das ist eine Festlegung, keine Panne. Die Frontplatte hat nur zwei Durchbrüche, beide auf 12 Uhr (Klinke, ToF); die Buchse sitzt auf 6 Uhr und zeigt radial nach außen in den Spalt zwischen Platine (Ø 52) und Dosenwand (lichte Weite 55–57 mm) — **1,5–2,5 mm, ein Stecker braucht ein Vielfaches** | Zu entscheiden ist nur, ob das so bleibt. Drei Wege: (a) **so lassen** — Erstflash auf dem Tisch, danach OTA über WLAN und RS-485; das ist der Normalfall bei Unterputzgeräten, (b) einen dritten Durchbruch im **unteren** Steg vorsehen und die Buchse nach vorn richten — kostet Bauhöhe und den frei gewordenen Kabelausgang, (c) Programmierkontakte (Pogo-Pads) auf der Rückseite. Fällt zusammen mit Punkt 26 (Bottom-Connector) und dem Tiefenbudget |

## Umbau auf das Busch-Jaeger-Bedienkonzept (15.08.2026)

Die Front wird nicht mehr selbst gestaltet, sondern übernommen: Sichtfläche ist
die **Zentralscheibe 6435-914** (2CKA006430A0402, Busch-balance SI) mit dem
Aufdruck „Pfeile und OK". Sie gehört zum Bedienelement **6456-101**
(54 × 54 × 23 mm, 1,68″-Display mit Hintergrundbeleuchtung, vier Tasten) und
wird von Busch-Jaeger auch für Raumthermostat 1098 U-101 und CO₂-Sensor 1091 U
verwendet. Herleitung: [`04-mechanical.md`](04-mechanical.md) Abschnitt 1c.

| # | Prio | Entscheidung | Bemerkung |
|---|---|---|---|
| 41 | ✅ **erzeugt 16.08.2026** | `mechanical/adapter.py`, Selbsttest bestanden: Flansch 70 × 70 für den Rahmen, Schnapprand 49,8 mit Rastraum, Platinentasche 47,4, Durchführung 43 × 43, Gesamthöhe 10,0. Die alte Frontplatte ist gelöscht. **Gedruckter Adapter statt eigener Frontplatte.** | Damit ist die Scheibe **werkzeuglos abnehmbar** — Voraussetzung für den USB-Zugang darunter (Punkt 45). Die alte Frontplatte samt Sicheltasten, Stößeln und Blendring ist gelöscht |
| 42 | 🟡 **P1, entschärft** | **Gemessen am 16.08.2026: Die Kraft kommt an den ECKEN an, nicht auf den Achsen.** Die Symbole stehen zwar auf den Achsen, die vier Druckkreuze auf der Rückseite der Scheibe sitzen aber auf den **Diagonalen** — dort, wo die Taster ohnehin liegen. **Das Bohrbild bleibt, die Routings bleiben.** Zu tun: acht Taster auf **vier** reduzieren und exakt unter die Kreuze setzen (ein 3,2-mm-Kreuz trifft genau einen Taster), sobald deren Positionen vermessen sind. Ursprünglicher Text: **Tastenpositionen sind zu messen — sie entscheiden über das Bohrbild aller drei Boards.** Heute sitzen acht SMD-Taster bei r = 23,2 mm auf ±12° um die **Diagonalen**. Liegen die Druckpunkte der Scheibe stattdessen auf den **Achsen** (Pfeile oben/unten, Tasten links/rechts — so die Aufteilung der Durchbrüche in Punkt 44), müssen die Taster dorthin | **Dann kollidieren sie mit den Befestigungsbohrungen** bei 0° und 180° (r = 21,5, Keepout r 3,2 — belegt r 18,3…24,7). Das Bohrbild ist in `tools/gen_boards.py` für **alle drei** Boards gemeinsam definiert; es zu ändern heißt, alle drei Layouts neu zu erzeugen und die 985 Leiterbahnen des Bottom-Boards zu verlieren. Ausweg wäre, die Platinen im Adapter statt in der Dose zu halten und die Frontbohrungen ganz aufzugeben |
| 43 | ✅ **entschieden und umgesetzt** | **1,69″ 240 × 280 (ST7789), quer.** Der gemessene Ausschnitt 32,70 × 27,00 mm trifft die aktive Fläche (32,63 × 27,97) auf 0,07 mm in der Breite. Schaltplan und ESPHome-Konfiguration sind umgestellt, `st77916_init.yaml` mit seinen 214 Kommandos ist gelöscht — ESPHome kennt den ST7789 nativ. **Offen:** Modul-Außenmaß am realen Teil, Footprint von J5 (Platzhalter, 10-polig; reale Module haben meist 8), und die Panel-Offsets (0/20) sind ungeprüft Der Fensterausschnitt der Zentralscheibe gibt die Form vor. Kandidat: **1,69″ / 240 × 240, ST7789** — in [`09-display-and-mcu.md`](09-display-and-mcu.md) Abschnitt 1c bereits vermessen (Moduldiagonale 46,1 mm, passt auf Ø 52) und dicht am BJ-Maß von 1,68″ | Nebenwirkung: **ESPHome unterstützt ST7789 nativ**, die 214-Kommando-Initsequenz `st77916_init.yaml` entfällt. Der QSPI-Bus im Stack bleibt nutzbar (ST7789 ist 4-Draht-SPI: `QSPI_D0` → MOSI, ein freier Datenpin → DC), nur die Namen stimmen dann nicht mehr. Endmaß erst nach dem Ausmessen des Scheibenfensters |
| 44 | **P1** | **Vier Durchbrüche in der Zentralscheibe, symmetrisch auf den Diagonalen** — je einer zwischen einem Pfeil und einer Taste | oben links **ToF-Fenster**, unten links **Klinkenbuchse** für den Stern, oben rechts und unten rechts **Lüftungsschlitze** für den Raumsensor (Punkt 46). Die Rückseite trägt die Löcher nicht mit: Alle vier liegen im 55er-Fenster und damit über der Dose — anders als der Rahmenrand, siehe Punkt 47 |
| 45 | ✅ **umgesetzt** | **USB-C zeigt nach vorn und ist von der Zentralscheibe verdeckt** — nutzbar erst, wenn die Scheibe abgenommen ist | Gewählt: **G-Switch GT-USB-7051x**, vertikal SMT, 22 Pads (A- und B-Reihe vollständig, also steckrichtungsunabhängig), Footprint 9,94 × 6,40 mm, LCSC C2843970. Sitzt mittig oben. **Nebeneffekt: die 28 `clearance`-Meldungen des Top-Boards sind verschwunden** — sie waren die zu eng gerasterten Pads der liegenden GCT USB4085. Offen bleibt nur die Bauhöhe gegen die 4,5 mm bis zur Scheibe |
| 46 | **P1** | **Der SHT4x muss den RAUM messen, nicht die Dose.** Ein externer Fühler ist nicht vorgesehen (ersetzt Punkt 35) | Drei Maßnahmen zusammen: Lüftungsschlitze rechts (Punkt 44), Sensor so weit vorn und so weit weg von Endstufe und Backlight wie möglich, thermische Entkopplung durch Schlitze in der Leiterplatte (bereits im Schaltplan vermerkt). **Ein Offset bleibt nötig** — aus einer geschlossenen Unterputzdose misst niemand die reine Raumtemperatur, auch Busch-Jaeger nicht. Zu kalibrieren gegen ein Referenzthermometer, mit Display an und aus |
| 47 | ✅ | **Löcher im Abdeckrahmen sind ausgeschlossen** — nachgerechnet, nicht abgewogen | Fenster 55 × 55 ⇒ halbe Kante 27,5 mm; Dose Ø 60 außen ⇒ lichte Weite 55–57 mm ⇒ Radius 27,5–28,5 mm. Der 13 mm breite Rahmenrand liegt damit **vollständig auf der Wand**. Hinter einem Loch dort ist Putz, keine Platine — für Klinke wie für ToF gleichermaßen |

**Was dieser Umbau an früheren Entscheidungen kippt:** 15a (ST77916 rund) wird
durch 43 ersetzt; 33 (Sicheltasten-Geometrie) verliert mit Punkt 41 den
Gegenstand; 30 (Klinkenbuchse) behält die Bauteilfrage, wechselt aber auf die
neue Position unten links; 25 (Frontplatte am Rahmen prüfen) wird zur
Vermessung von Scheibe **und** Rahmen; 35 (externer Temperaturfühler) ist mit
Punkt 46 beantwortet — es gibt keinen.

### Messliste — und woher die Teile kommen

Ohne diese Maße ist kein Layout möglich, und ein Maßbild ist öffentlich nicht zu
bekommen. Die Quelle ist deshalb das reale Teil:

> **Busch-Jaeger 6422 UJ-914, „Jalousie-Compact-Timer, Komplettset"**
> (2CKA006410A0412, Busch-balance SI, alpinweiß)

Der Lieferumfang ist für dieses Projekt der Glücksfall — er enthält **genau die
beiden Teile, auf die wir uns festgelegt haben**, plus den geometrischen
Referenzkörper:

| Im Set | Wofür wir es brauchen |
|---|---|
| **Zentralscheibe 6435-914** | Punkte 41–44: Druckpunkte, Fensterausschnitt, Rastgeometrie |
| **Abdeckrahmen 1721-914** | Punkt 25: woran die Klemmbefestigung greift |
| **Einsatz 6422 U** (Jalousie-Timer) | Der Körper, den unser Adapter nachbildet — und zugleich die Antwort darauf, wie Busch-Jaeger den Einsatz in der Dose hält. Genau das ist der Ausweg aus Punkt 42, falls die Frontbohrungen fallen sollen |

**Der Einsatz ist ein Messobjekt, kein Bauteil.** Er arbeitet mit 230 V und zwei
Wechslern à 3 A. In dieses Gerät kommt er nicht — der gesamte Aufbau ist SELV
(Punkt 21), und ein 230-V-Einsatz in dieser Dose wäre die Rücknahme genau der
Entscheidung, die [`12-legacy-socos.md`](12-legacy-socos.md) Abschnitt 5 als
geschlossen führt.

Als Zugabe ist er trotzdem lehrreich: Es ist **Busch-Jaegers eigene
Jalousiesteuerung**. Die Symbolbelegung der Scheibe ist also für genau unseren
Anwendungsfall entworfen worden, und die Bedienlogik des Originals ist der
naheliegende Maßstab für Punkt 37 (verbindliche Tastenbelegung).

Der Einsatz ist dabei **bequem, aber nicht nötig**: Die Rückseite der
Zentralscheibe ist das Negativ dessen, was der Adapter anbieten muss. Mit
Scheibe und Rahmen allein lässt sich alles abnehmen.

Das ausgearbeitete Messprotokoll **F1–F13** steht in
[`04-mechanical.md`](04-mechanical.md) Abschnitt 1d. Vier Werte daraus geben das
Layout frei: **F3** (Fensterausschnitt → Display), **F5/F10** (Tastenpositionen
→ Punkt 42), **F8** (Rastmaß → Adapter) und **F2** (Bauhöhe).

| # | Prio | Entscheidung | Bemerkung |
|---|---|---|---|
| 48 | ✅ **umgesetzt 16.08.2026** | **Das Top-Board ist eckig.** **47 × 47** mm, Eckradius 4; vier Taster exakt auf (±18,0 · ±20,0), Platzierung kollisionsfrei, **DRC ohne Fehler**. `gen_panel.py` beherrscht die gemischte Geometrie inzwischen. Ursprüngliche Begründung: **Das Top-Board wird eckig.** Die vier Druckkreuze der Zentralscheibe sitzen bei (±18,0 · ±20,0), also auf **r = 26,91 mm** — 0,9 mm außerhalb der Ø-52-Platine. Mit Taster und Randabstand bräuchte eine runde Platine Ø 59,7; das passt in keine Dose. Ursache ist strukturell: Das BJ-System ist um einen **quadratischen** Einsatz gebaut und setzt seine Tasten in die Ecken | **Vorschlag: 49 × 49 mm mit gerundeten Ecken**, vor der Dose sitzend wie der BJ-Einsatz. Mid und Bottom bleiben rund und bleiben in der Dose. Kosten: der gemeinsame Umriss fällt, `gen_boards.py` und der Fertigungsnutzen ändern sich, das Top-Layout wird neu erzeugt (es trägt ohnehin keine Leiterbahnen). Gewinn: Taster direkt unter den Kreuzen, kein Hebel, kein bewegliches Druckteil — und das Tiefenbudget für Mid und Bottom wächst, weil Top die Dose verlässt. Alternative wäre ein Adapter mit vier Hebeln; das widerspricht der Regel „die Federung kommt vom Taster, nicht vom Kunststoff" |
| 49 | ✅ **umgesetzt** | Der Flansch des Adapters ist 70,0 × 70,0 — genau das Maß, auf das die Doppelstege des Rahmens klemmen. Schraubschlitze weiter auf 60 mm. **Der Adapter muss dem Rahmen 70,0 mm anbieten** — auf dieses Maß klemmen seine Doppelstege (F13). Die bisherige Frontplatte hat 76 mm breite Ohren und stünde ihnen im Weg | Tragring-Maß nachbilden, Schraublöcher weiter auf 60 mm (DIN 49073). Damit ist auch Punkt 25 beantwortet: Der Rahmen hält am Tragring, nicht an der Zentralscheibe (F12 — sie hält nicht von allein im Rahmen) |

| # | Prio | Entscheidung | Bemerkung |
|---|---|---|---|
| 50 | P2 | **Sieben Bauteile haben kein 3D-Modell** — KiCad liefert für sie keines mit: Molex Micro-Fit 3.0 43045-0612 (**der Leistungsstecker**), PowerPAK SO-8 (die acht MOSFETs), Fuse 1812, Fuse Littelfuse NANO2, Drossel Bourns SRP7028A, USB-C G-Switch GT-USB-7051x, Klinke QingPu WQP-PJ398SM | Betrifft nur die 3D-Ansicht, nicht die Fertigung — aber ausgerechnet den Steckverbinder, der das Tiefenbudget dominiert. Herstellerdaten helfen: Molex, GCT und CUI bieten STEP zum Download; ablegen unter `~/Documents/KiCad/10.0/3dmodels` und im Footprint verknüpfen. **Kein Ersatzmodell zuweisen** — ein falscher Körper in der Kollisionsprüfung ist schlimmer als ein fehlender |
