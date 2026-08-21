# 06 – Offene Entscheidungen

Legende Priorität: **P0** blockiert den nächsten Arbeitsschritt · **P1** vor
Layout-Freeze nötig · **P2** vor Fertigungsfreigabe nötig.

Welche Funktionen diese Punkte blockieren, zeigt
[`13-funktionsstatus.md`](13-funktionsstatus.md).

## Kritischer Pfad

| # | Prio | Entscheidung | Abhängig davon |
|---|---|---|---|
| ~~1~~ | ✅ | **Blockierstrom gemessen: 1,7 A je Motor** (17.08.2026), Ankerwiderstand 14 Ω (Minimum aus drei Verfahren). Zwei unabhängige Messpunkte bei 2 V und 24 V stimmen überein | Shunt 1 → **5 mΩ**, Sicherung 15 → **6,3 A**, Firmware-Skalierung 20 → **4 A/V**. Der Trip-Teiler bleibt bei 10k0/40k2/10k0 und wandert mit dem Shunt von ± 22 A auf **± 4,4 A** — ein Bauteil weniger geändert. Kein Layout betroffen. Siehe [`11-motor-data.md`](11-motor-data.md) Abschnitt 5 |
| ~~1a~~ | ✅ | **PWM ist erlaubt** — der Motor hat keine eigene Elektronik, die gestört werden könnte | erledigt |
| ~~1b~~ | ✅ | **2 Adern je Motor ⇒ H-Brücke zwingend**, 6-poliger Bottom-Connector bestätigt | erledigt |
| ~~2~~ | ✅ | **Micro-Fit 3.0 genügt** (17.08.2026). Der Summenstrom beträgt 4,1 A statt der angenommenen 9 A, damit ist kein stromstärkeres System nötig | Spart Bauhöhe und Grundfläche auf dem Bottom-Board gegenüber Mini-Fit Jr. |
| ~~3~~ | ✅ | **Beide Motoren dürfen gleichzeitig laufen** (16.08.2026). Kein Interlock | Summenpfad **4,1 A** im ungünstigsten Fall (beide am Anschlag). Die anfangs vermerkte Verschärfung von Punkt 2 hat sich mit der Messung vom 17.08.2026 erledigt — der Interlock war nie nötig |

**Die Punkte 1, 2 und 3 sind seit dem 17.08.2026 alle erledigt** — und zwar
durch eine einzige Messung. Die defensive Auslegung hat sich dabei genau so
bewährt, wie sie gedacht war: Alle messabhängigen Größen steckten in
Widerstandswerten, keine im Layout. Der Blockierstrom fiel um den Faktor 16
niedriger aus als angenommen, geändert wurden trotzdem nur vier Bauteilwerte.

Was aus der Messung **neu** folgt, steht als Punkt 54 unten: Die Endlagenerkennung
hat weniger Signalabstand als gedacht.

## Bauteilauswahl Leistung

| # | Prio | Entscheidung | Bemerkung |
|---|---|---|---|
| ~~4~~ | ✅ | **TPS54360DDA**, 60 V Eingang | Layout noch nach Referenzdesign prüfen |
| ~~5~~ | ✅ | **TLV62569DBV**, 180k/40k2 → 3,29 V | |
| ~~6~~ | ✅ | **TPS54360DDA**, 68k1/10k0 → 6,25 V — gleiches Bauteil wie #4 | |
| ~~7~~ | ✅ | **Diskret: 2× IR2104 + 4 N-FET je Kanal.** Begründung in [`02-motor-control.md`](02-motor-control.md) Abschnitt 2 | |
| 8 | ✅ **entschieden (20.08.2026): Vishay SIR4409DP-T1-GE3** — P-Kanal, −40 V, 60 A, PowerPAK SO-8. Nicht bei LCSC → Mouser-Sammelbestellung, Handbestückung | einziges Leistungsbauteil ohne Teilenummer; hängt am Blockierstrom |
| ~~9~~ | ✅ | **INA240A2D**, Verstärkung 50, aus 3,3 V versorgt | Pinbelegung gegen Datenblatt prüfen |
| ~~10~~ | ✅ | **Inline-Messung**, Kelvin-Shunt im Motorzweig — **5 mΩ** seit dem 17.08.2026 (vorher 1 mΩ) | löst das Freilaufproblem vollständig; der größere Wert bringt die Auflösung, die die Endlagenerkennung braucht |
| ~~11~~ | ✅ | **Fensterkomparator + 74AUP1G74**, wirkt auf `~SD` der IR2104 | Typ am 17.08.2026 von LM393 auf **TLV3702** korrigiert — siehe Punkt 57 |
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
| 23 | 🔴 **BLOCKIERT — das Teil, das das Konzept braucht, gibt es nicht (Recherche 21.08.2026).** Gesucht war eine erhöhte 2×20-THT-Buchse im Raster 1,27 × 1,27 mit **9,0 mm Bauhöhe**. Branchenweite Obergrenze für diese Bauform: **4,0–4,6 mm** (Samtec SFM 4,57 · Sullins LPPB202CFFN 4,50 · Harwin M50-3002045 4,40 · Preci-Dip 853-87-040 4,00; LCSC-Vollauswertung über ~1.800 Teile mit Pitch 1,27: höchste 2×20-THT-Buchse 4,3 mm). Erhöhte Buchsen sind eine **2,54-mm-Bauform** (Pi-HAT-Welt) und existieren bei 1,27 mm nicht. Achtung Falle: Samtecs SSW/TSW/SSQ/ESQ sind 2,54 mm — die „120" im Bestellcode ist die Polzahl, nicht das Raster | **Bei 1,27 mm kommt die Stapelhöhe aus dem STIFT.** Samtec paart die feste Buchse `SFM-120-01-L-D` (4,57 mm, Einstecktiefe 4,2, **3,7 A/Pin**, Bohrbild 0,71 mm = unser Lochbild) mit `TFM-120-xx-L-D`, deren Lead Style die Höhe setzt: −01 → 5,97 · −11 → 7,75 · **−21 → 9,53** · −31 → 11,43 mm (Oberfläche zu Oberfläche). **9,00 gibt es nicht.** Zwei harte Haken: (a) TFM ist KEIN Durchsteck-Stift (Lötschwanz 1,97/2,77 — nach 1 mm Platine bleiben ≤ 1,8 mm), Mid bräuchte **zwei Lochbilder** je Position — und dafür ist **kein Platz**, alle vier Kandidatenzonen (±8 mm in y) sind belegt, u. a. vom ESP32-Modul. (b) Der einzige echte Durchsteck-Verbinder ist Samtec **FW-TH** (Pin bis 20,32 mm, Körper frei positionierbar) — „non-standard, non-returnable", nicht distributorgelagert, Angebot nur über ipg@samtec.com, und freistehende 0,41-mm-Pins über 7 mm sind mechanisch heikel. **Entscheidung des Nutzers nötig** — siehe die drei Wege unten |
| ~~24~~ | ✅ | **USB-UART entfällt** — ESP32-S3 hat nativen USB | erledigt |

## Mechanik

| # | Prio | Entscheidung | Bemerkung |
|---|---|---|---|
| 25 | P1 | **Adapter gegen Rahmen und Scheibe prüfen — am Testdruck.** Rahmen Busch-Jaeger 1721-914 (Fenster 55 × 55, außen 81 × 81 × 12), Zentralscheibe 6435-914. Rechnerisch passt alles: Flansch 70,0 = Klemmmaß der Doppelstege (F13), Schnapprand 49,8 gegen Rastmaß 50,0 (F8), Bauhöhe 10,0 unter 12 mm Rahmentiefe | **Die frühere offene Frage ist beantwortet:** Der Rahmen klemmt am Tragring, nicht an der Scheibe (F12 — sie hält nicht allein im Rahmen), und den Tragring bildet jetzt der Adapter selbst. Zu prüfen bleibt das Gefühl: Rastet die Scheibe satt? Sitzt der Rahmen spielfrei? Lässt sich die Scheibe ohne Werkzeug wieder abnehmen, ohne den Rahmen mitzureißen? |
| 26 | P2 | Bottom-Connector gerade oder abgewinkelt | War der größte Hebel im Tiefenbudget — **seit das Top-Board vor die Dose gewandert ist, stehen rund 17 mm Reserve statt 9** ([`04-mechanical.md`](04-mechanical.md) Abschnitt 4). Die Entscheidung bleibt, blockiert aber nichts mehr |
| 27 | P2 | Schraubengröße M2,5 vs. M3 | M2,5 empfohlen |
| 28 | P2 | Bestätigung des Bohrbilds gegen reale Dose und Frontpanel | |

## Neu aufgeworfen beim Umbau vom 15.08.2026

| # | Prio | Entscheidung | Bemerkung |
|---|---|---|---|
| 29 | ✅ **gelöst (16.08.2026)** | **Zwei Stecker statt einem.** Ein 8-poliger JST-SH (11,9 mm) findet nachweislich keinen Platz; ein 6-poliger für die vier Reed-Signale und ein 2-poliger für den Haubenkontakt finden beide einen. Nebeneffekt: Eingänge und potentialfreier Schaltausgang sind sauber getrennt. Ursprünglicher Text: **Feldstecker für Reed-Kontakte und Haubenkontakt** — auf dem Mid-Board ist *kein* Platz mehr. Nachgerechnet gegen alle Courtyards: weder vorn noch hinten passt ein 6-poliger oder auch nur 3-poliger JST, mit 4 mm Abstand zu den Befestigungsbohrungen. Aktuell steht ein JST-SH 1 mm auf der Rückseite, 0,4 mm neben dem Keepout von H2 | Vier Wege: (a) Feldsignale auf das Bottom-Board legen und `REED1/2` über die Reservepins `RSV_A2`/`RSV_A4` hochführen, (b) Piezo BZ1 (12 × 9,5 mm) verkleinern und den Platz nutzen, (c) Lötpads statt Steckverbinder, (d) Boarddurchmesser überdenken |
| 30 | ✅ **überholt (19.08.2026): Sternanschluss ist magnetisch (DCX-909 im Abdeckrahmen), keine Klinke mehr** | **Konkrete 2,5-mm-Klinkenbuchse** — der Footprint ist ein Platzhalter (3,5 mm vertikal, Thonkiconn), und er **passt geometrisch nicht**: 14,4 mm Körperlänge mit dem Bund in der Mitte, bei einem Lochabstand von r = 22,5 mm steht das hintere Ende 3,3 mm über die Platinenkante. Das ist die einzige verbliebene Randabstandsverletzung des Top-Boards | **Das Zielteil muss in einen Ring von r ≈ 20,9 bis 25,5 mm passen — 4,6 mm radial.** Nach innen begrenzt das Displaymodul (Ø 41,5 + 0,5 Luft), nach außen die Kontur. Dazu die bekannten Grenzen: Bauhöhe über der Platine ≤ 10,5 mm, Bundloch Ø 5,6 mm in der Frontplatte bei (0, −22,5). Pads und Bundlage aus dem Datenblatt übernehmen — die Bundachse, nicht die Footprint-Mitte, gehört auf den Lochmittelpunkt |
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
| 44 | ✅ **überholt (19.08.2026): zwei Löcher ±5,5 + SW5-Öffnung statt vier Diagonal-Durchbrüche** | **Vier Durchbrüche in der Zentralscheibe, symmetrisch auf den Diagonalen** — je einer zwischen einem Pfeil und einer Taste | oben links **ToF-Fenster**, unten links **Klinkenbuchse** für den Stern, oben rechts und unten rechts **Lüftungsschlitze** für den Raumsensor (Punkt 46). Die Rückseite trägt die Löcher nicht mit: Alle vier liegen im 55er-Fenster und damit über der Dose — anders als der Rahmenrand, siehe Punkt 47 |
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
| 49 | ✅ **umgesetzt** | Der Flansch des Adapters ist 70,0 × 70,0 — genau das Maß, auf das die Doppelstege des Rahmens klemmen. Schraubschlitze auf 60 mm. **Ein Teil für alles:** Am 16.08.2026 wurde die Zwischenüberlegung verworfen, einen fertigen Blech-Tragring zu verwenden und den Adapter nur darauf zu setzen — der Blechring baut zusätzlich auf, und seine Krallen werden nicht gebraucht; das Gerät hängt an den zwei Geräteschrauben wie jeder Serieneinsatz. **Der Adapter muss dem Rahmen 70,0 mm anbieten** — auf dieses Maß klemmen seine Doppelstege (F13). Die bisherige Frontplatte hat 76 mm breite Ohren und stünde ihnen im Weg | Tragring-Maß nachbilden, Schraublöcher weiter auf 60 mm (DIN 49073). Damit ist auch Punkt 25 beantwortet: Der Rahmen hält am Tragring, nicht an der Zentralscheibe (F12 — sie hält nicht von allein im Rahmen) |

| # | Prio | Entscheidung | Bemerkung |
|---|---|---|---|
| 50 | P2 | **Sieben Bauteile haben kein 3D-Modell** — KiCad liefert für sie keines mit: Molex Micro-Fit 3.0 43045-0612 (**der Leistungsstecker**), PowerPAK SO-8 (die acht MOSFETs), Fuse 1812, Fuse Littelfuse NANO2, Drossel Bourns SRP7028A, USB-C G-Switch GT-USB-7051x, Klinke QingPu WQP-PJ398SM | Betrifft nur die 3D-Ansicht, nicht die Fertigung — aber ausgerechnet den Steckverbinder, der das Tiefenbudget dominiert. Herstellerdaten helfen: Molex, GCT und CUI bieten STEP zum Download; ablegen unter `~/Documents/KiCad/10.0/3dmodels` und im Footprint verknüpfen. **Kein Ersatzmodell zuweisen** — ein falscher Körper in der Kollisionsprüfung ist schlimmer als ein fehlender |

| # | Prio | Entscheidung | Bemerkung |
|---|---|---|---|
| 51 | **P1** | **Halten die gedruckten Schraubaugen?** Der Adapter trägt die Geräteschrauben in Kunststoff — 2,5 mm Flansch, Langlöcher 3,9 mm auf 60 mm. Das ist der Schwachpunkt des Ein-Teil-Konzepts | Zu prüfen am ersten Druck: Zieht die Schraube das Auge durch, reißt der Flansch ein, hält er das Anziehen eines Elektrikers aus? Wege bei Problemen: Flansch dicker, Einlegemuttern, Metallscheiben unterlegen — oder als Rückfallweg doch ein Blech-Tragring, auf den der Adapter nur aufgesetzt wird. Die Bauhöhe von 10,0 mm hat dafür Luft: Der Rahmen ist 12 mm tief, das prüft der Selbsttest jetzt mit |

| # | Prio | Entscheidung | Bemerkung |
|---|---|---|---|
| 52 | P2 | **Der Nutzen ist für die Leiterplattenfertigung ausgelegt, nicht für die Bestückung.** Es fehlen Passermarken, breitere Ränder und Werkzeugbohrungen | Drei Fiducials global (diagonal versetzt) plus lokale an ESP32-Modul, PCF8575 (0,65 mm Raster) und USB-C; Ränder von 4,0 auf 5–10 mm an zwei gegenüberliegenden Seiten; zwei bis drei unbelegte Ø-3-Löcher. `gen_panel.py` erzeugt das alles noch nicht. Erst nötig, wenn bestückt bestellt wird — die reine Leiterplattenfertigung geht auch so |

| # | Prio | Entscheidung | Bemerkung |
|---|---|---|---|
| ~~53~~ | ✅ **umgesetzt 16.08.2026** | **Versatz beim Schließen — welcher Flügel zuerst?** Gelöst als Laufzeiteinstellung: `select` „Ueberdeckender Fluegel" plus `number` „Versatz" (0–20 s, Vorgabe 6 s), wirksam als `delay` am Anfang aller vier Fahrskripte, dazu ein Menüpunkt „Fluegelversatz". Damit muss die Frage gar nicht vorab beantwortet werden. Ursprünglich: Der Original-Controller K0000230 startet Flügel 2 beim Schließen **6 Sekunden später**. Zweiflügelige Klappläden überlappen geschlossen; ohne Versatz schlagen sie aufeinander. Die jetzige Firmware schließt beide gleichzeitig | Zu klären ist nur, **welcher** Flügel überdeckt — er muss zuletzt schließen und zuerst öffnen. Danach zwei Zeilen Firmware: eine `number`-Entität für den Versatz (Vorgabe 6 s) und ein `delay` im Schließskript des überdeckenden Kanals. Beim Öffnen gilt es spiegelbildlich |

## Aus der Blockierstrommessung vom 17.08.2026

| # | Prio | Entscheidung | Bemerkung |
|---|---|---|---|
| 54 | **P0** | **Reicht der Signalabstand für die Endlagenerkennung?** Das war bisher der bequemste Teil des Konzepts: Laufstrom ≈ 0,5 A gegen Blockierstrom ≈ 20 A, ein Faktor 40. Tatsächlich sind es **0,3–1,0 A gegen 1,7 A**, im ungünstigsten Fall also 60 % Anstieg. Ohne Reed-Endlagen hängt die gesamte Positionsbestimmung an diesem Abstand | Drei Maßnahmen sind schon getroffen: Der Shunt wurde auf 5 mΩ verfünffacht (0,25 V/A, ≈ 3 mA je LSB), der Nullpunkt wird in der Firmware jetzt korrekt abgezogen, und die Verlangsamung vor der Endlage senkt die Kraft. Was fehlt, ist die **PWM-synchrone Abtastung** — der gemittelte ADC-Wert taugt zur Anzeige, nicht zur Stall-Erkennung (siehe [`09-display-and-mcu.md`](09-display-and-mcu.md) Abschnitt 4). Beruhigend: Der Original-Controller K0000230 löst dieselbe Aufgabe am selben Motor mit derselben Physik |
| 55 | ✅ **erledigt (18.08.2026): DRV8871** | **Integrierter H-Brücken-Treiber statt diskretem Aufbau?** Die diskrete Brücke aus 2× IR2104 und 4 N-FET je Kanal wurde allein wegen des unbekannten Blockierstroms gewählt (Punkt 7). Bei 1,7 A wäre ein DRV8871 oder DRV8873 die naheliegende Wahl und würde das Bottom-Board erheblich entlasten | **Vorschlag: nicht umsetzen.** Die Platine ist geroutet, der Gewinn wäre Fläche, die ohnehin schon vergeben ist, und der Preis ein vollständiges Neulayout samt neuer Strommessung. Sinnvoll nur, falls das Bottom-Board aus anderem Grund neu entsteht |
| ~~56~~ | ✅ **geprüft 17.08.2026** | **Mechanischer Schaden am Antrieb — Entwarnung.** Bei der Blockiermessung wurde etwas verbogen, **der Motor selbst ist unbeschädigt** und läuft. Damit ist der Vorfall abgeschlossen | Die Lehre daraus bleibt trotzdem gültig und ist keine Folge des Schadens, sondern der Physik: 1,7 A sind elektrisch harmlos, das Getriebe macht daraus aber ein Moment, das Beschläge verformt. **Sicherung und Hardware-Trip schützen die Mechanik nicht und können es nicht** — sie liegen bei 6,3 A und 4,4 A, also weit über dem, was zum Verbiegen reicht. Der Mechanikschutz ist allein Sache der Software: Soft-Limit, Fahrzeit-Timeout und vor allem die Verlangsamung vor der Endlage. Festgehalten in [`11-motor-data.md`](11-motor-data.md) Abschnitt 3 |

## Beim Nachrechnen der Reserve gefunden (17.08.2026)

| # | Prio | Entscheidung | Bemerkung |
|---|---|---|---|
| ~~57~~ | ✅ **entschieden 17.08.2026** | **Der LM393 kann die obere Trip-Schwelle nicht sehen** — er ist für einen Gleichtakt-Eingangsbereich von 0 bis V+ − 1,5 V spezifiziert, an `3V3_SYS` also bis 1,8 V, während `V_TRIP_HI` bei **2,752 V** liegt. Die obere Hälfte des Fensterkomparators arbeitete außerhalb ihres Bereichs; der Hardware-Trip hätte nur in **einer** Stromrichtung gewirkt. Der Fehler war älter als die Strommessung — die alte Schwelle lag genauso hoch | **Gelöst durch Bauteiltausch statt Layoutänderung: `TLV3702`.** Rail-to-Rail-Eingang, Open-Drain-Ausgang, SOIC-8 im Standard-Pinout eines dualen Komparators — **gleicher Footprint, gleiche Netze, keine Leiterbahn angefasst**, DRC unverändert. Bleibt an 3,3 V und damit auf derselben Schiene wie die INA240-Referenz, was die ratiometrische Kopplung der Schwelle erhält. Mit ≈ 5 µs ist er zudem **langsamer** als der LM393 (1,3 µs) — hier ein Vorteil, siehe Punkt 59. Wer Geschwindigkeit braucht, nimmt den TLV1702 (560 ns) und handelt sich mehr Störempfindlichkeit ein. **Verworfen wurden:** Versorgung aus `5V_SYS` (Netz liegt 27,3 bzw. 36,0 mm entfernt auf der anderen Boardhälfte — zwei lange Bahnen über 985 vorhandene Segmente) und aus `12V_GATE` (nur 3–7 mm entfernt, aber die lauteste Schiene der Platine, und der Komparator hat keinen Abblockkondensator). ⚠️ **KiCad 10 bringt für den TLV kein Symbol mit** — im Schaltplan steht weiter `Comparator:LM393`, das ja genau das Standard-Pinout ist. Wert und MPN nennen den echten Typ. Vor der Bestellung gegen das Datenblatt prüfen: dual, SOIC-8, **Open-Drain** (das Wire-OR auf `Mx_TRIP` hängt daran), Gleichtaktbereich bis mindestens 2,9 V |
| 58 | **P1** | **Wind bricht die Endlagenerkennung — in beide Richtungen.** Rechnung in [`11-motor-data.md`](11-motor-data.md) Abschnitt 6.4: Ab etwa 40 km/h übersteigt das Windmoment am Flügel das Motormoment von 25 Nm. Gegenwind bremst und sieht aus wie ein Anschlag; Rückenwind schlägt den Flügel schneller als erwartet gegen den Anschlag, bei *niedrigerem* Strom als normal | Drei Maßnahmen, absteigend nach Wirkung. **(1) Strom nur innerhalb eines Zeitfensters als Endlage werten** — Vorschlag ab 70 % der gelernten Fahrzeit. Ein Stromanstieg davor ist Hindernis oder Wind: anhalten, melden, Position **nicht** setzen. Reine Firmware, gehört in dieselbe C++-Komponente wie die Stall-Erkennung. **(2) Verlangsamung vor der Endlage** — vorhanden, wirkt gegen alles außer Rückenwind. **(3) Windsperre in Home Assistant** oberhalb ~40 km/h — die einzige Maßnahme gegen Rückenwind, gehört in die Automatisierung, nicht ins Gerät |
| 59 | P2 | **Der Komparator sieht das ungefilterte Sense-Signal.** Der RC-Filter (1 k / 1 n, 1 µs) sitzt nur im Zweig zum ESP32-ADC; `Mx_ISNS` geht direkt auf beide Komparatoreingänge. Zusammen mit dem Latch genügt ein einzelner Störimpuls aus dem PWM-Schalten, um die Endstufe dauerhaft abzuschalten | Erst am realen Aufbau zu beurteilen — vielleicht reicht die Bandbreitenbegrenzung des INA240 (400 kHz). Falls nicht: ein zweiter RC von etwa 100 ns vor die Komparatoreingänge. Zwei Bauteile je Kanal, Platz auf der Platine vorausgesetzt |

## Beim Durchgehen von Einbaureihenfolge und Kraftfluss (19.08.2026)

Herleitung und Zahlen: [`18-montage-und-kraefte.md`](18-montage-und-kraefte.md).
Alle sechs Punkte sind aus dem vorhandenen Quelltext gelesen, **keiner ist
nachgerechnet oder am Teil geprüft**.

| # | Prio | Entscheidung | Bemerkung |
|---|---|---|---|
| 60 | 🟡 **entschärft (20.08.2026): 0,8/0,4-Vias + tools/via_check.py; Restliste in docs/16** | **Vias sind nicht beliebig stromtragfähig — die Regel „mehrfach setzen" ist keine Prüfgröße.** Die Belastbarkeit hängt an Bohrdurchmesser, **Kupferdicke in der Hülse**, Länge (Lagenabstand) und zulässiger Übertemperatur. Von diesen vier Größen ist im Projekt nur die Geometrie 0,6/0,3 mm benannt, und die als Fertigungsgrenze, nicht als Strombemessung. Die Hülsendicke ist nirgends festgelegt und **nicht** aus dem 1-oz-Lagenkupfer ableitbar | Betrifft vier Pfade: **Versorgung auf Top** (Stackverbinder liegen auf B, die Verbraucher auf F — jedes Ampere quert die Lage), **Sternpfad** `6V2_STAR_F` → P-FET → PTC → `STAR_OUT` → J6 (kommt über **einen** Stackpin herauf, Schaltstufe vorn, Buchse hinten), **`USB_VBUS`** (ein Stackpin, Buchse auf Mid vorn), **Motorpfade auf Bottom** (4,1 A Summe, 102 Vias, keine Auswertung welche im Strompfad liegen). Vor dem Routing-Freeze: je Pfad die Zahl paralleler Vias aus Strom, Hülsenkupfer und einer **benannten** Übertemperatur bestimmen. Besonders dort, wo schon ein einzelner Kontakt der Engpass ist — Pin und Via addieren ihre Erwärmung im selben luftlosen Volumen. Gegenstück für die Stackpins existiert bereits: [`03-stack-pinout.md`](03-stack-pinout.md) Abschnitt 2 |
| 61 | ✅ **gelöst (19.08.2026): Hülsen M2,5 × 9, Befestigungskonzept v2** | **Wer hält Mid und Bottom?** Beide hängen ausschließlich an den zwei Stackverbindern am Top-Board, und das liegt lose in der Adaptertasche. Die Befestigungsbohrungen M2,5 auf r = 21,5 (0°/180°) sind auf allen drei Boards vorhanden, haben im Adapter aber **kein Gegenstück**: Dort liegt bei x = ±21,5 genau die Kante der zentralen Durchführung (43 × 43), kein Dom, kein Gewinde | Drei Wege: (a) Schraubdome im Adapter ergänzen — sie müssten an der Durchführungskante stehen und kosten Auflagefläche, (b) durchgehende Schrauben mit Distanzhülsen — widerspricht Punkt 23, wonach der Plattenabstand aus der Steckhöhe kommt, (c) es bewusst so lassen und schriftlich festhalten, dass der Stapel am Steckverbinder hängt. Dann gehört die Haltekraft des Verbinders in die Auswahl von Punkt 23. Zusammen mit Punkt 28 zu entscheiden |
| 62 | **P1** | **Nullspalt zwischen Druckkreuz und Taster.** Die Tiefenkette setzt die Kreuzunterkante auf 2,5 und die Tasteroberkante ebenfalls auf 2,5 — nominal berühren sie sich spannungsfrei. Die Kette enthält **kein nachgiebiges Glied**: Drucktoleranz der Auflage, Platinendicke, Bauhöhe des Tasters und Tiefe der Scheibe addieren sich direkt auf den Schaltweg | Zu klein heißt Dauerdruck auf allen vier Tastern (das Gerät bootet in einen gedrückten Zustand), zu groß heißt Leerweg und schwammiger Druckpunkt. Am Testdruck zu messen, zusammen mit Punkt 25. Stellschrauben, falls nötig: `seat`-Höhe im Adapter (0,1-mm-Schritte), Tastertyp mit anderer Bauhöhe, oder eine dünne Auflage unter der Platine. **Keine gedruckte Feder** — das widerspräche der Regel aus [`09-display-and-mcu.md`](09-display-and-mcu.md) Abschnitt 1b |
| 63 | P2 | **Wie tief liegt die Sichtfläche im Rahmen?** Der Adapter baut 10,0 mm vor der Wand, der Rahmen ist 12 mm tief — rechnerisch liegt die Sichtfläche der Zentralscheibe damit **rund 2 mm hinter der Rahmenvorderkante**. F12 hat am realen Teil dagegen „bündig" ergeben, allerdings mit der Scheibe im Rahmen und ohne unseren Adapter | Der Selbsttest in `adapter.py` prüft nur, dass der Adapter unter dem Rahmen verschwindet (`z_total ≤ frame_depth`), nicht, wo die Sichtfläche landet. Am Testdruck zu klären. Falls die 2 mm real sind: entweder hinnehmen (ein Schattenfugen-Effekt, optisch nicht zwingend falsch) oder die Bauhöhe des Adapters über `flange_t` anheben — Luft dafür ist da, aber sie geht vom Rahmenüberstand ab |
| 64 | P2 | **Befestigung des Magnetkontakts und Zugänglichkeit hinter dem Top-Board.** Der Kontakt sitzt seit dem 18.08.2026 in einem Durchbruch Ø 6,7 bei (−10,0 / 19,6); `adapter.py` hält fest „die Platine hält ihn" — **wie**, steht nirgends: Flansch vorn und Mutter hinten, Klebung, Klemmung? Dazu die Reihenfolgefrage: Magnetlitzen, J6 und die Display-FPC liegen alle auf der **Rückseite** des Top-Boards und sind nach dem Stecken von Mid nur noch durch den 10-mm-Spalt erreichbar | Beides am realen Teil zu entscheiden. `magnet_d` und `magnet_h` in `adapter.py` sind weiterhin Platzhalter, das gekaufte Teil (Elsaybro, ASIN B0H9Y9NVSV) hat kein Datenblatt. Der Huelsenhalter im Adapter ist abgeschaltet, bleibt aber im Quelltext — er wird gebraucht, sobald ein flacher Kontakt (≤ 3,5 mm) ohne Durchbruch vor der Platine sitzen kann. Offen bleibt auch die **Abzugskraft** der magnetischen Verbindung: Sie ist die einzige Halterung des Sternkabels |
| 65 | P2 | **Widersprüchliche Quellenlage zum Sternanschluss.** [`04-mechanical.md`](04-mechanical.md) Abschnitte 6b und 7 sowie [`13-funktionsstatus.md`](13-funktionsstatus.md) führen weiterhin die **2,5-mm-Klinkenbuchse** und vier Durchbrüche in der Zentralscheibe; `tools/gen_layouts.py`, `mechanical/adapter.py` und [`17-bauteildaten.md`](17-bauteildaten.md) führen seit dem 18.08.2026 **JST GH auf der Rückseite plus Magnetkontakt im Boarddurchbruch** | Reine Dokumentationspflege, aber sie verfälscht die Lage: Punkt 30 (Klinkenbuchse, P0) ist dadurch möglicherweise gegenstandslos, und `13` nennt in Abschnitt 3.4 noch eine Klinke als vorhandene Hardware. Beim nächsten Durchgang durch `04` und `13` nachziehen und Punkt 30 entsprechend schließen oder umwidmen |

## Beim maßstäblichen Zeichnen der Front gefunden (19.08.2026)

Die Explosionszeichnung [`renders/front-explosion.png`](renders/front-explosion.png)
setzt die fünf Frontteile erstmals maßstäblich nebeneinander
([`18-montage-und-kraefte.md`](18-montage-und-kraefte.md) Abschnitt 7). Jede
Einzelzahl war richtig; erst im Bild passen sie nicht zusammen.
`tools/gen_explosion.py` prüft die drei Punkte bei jedem Lauf und schreibt sie
in die Zeichnung.

| # | Prio | Entscheidung | Bemerkung |
|---|---|---|---|
| 66 | P2 | **Ein Millimeter Unterschied im Ebenenabstand.** `mechanical/stack.py` setzt die Boardrückseiten auf 0 / 10 / 20 — zwischen Boardvorderseite und nächster Boardrückseite bleiben damit **9,0 mm** frei. Das Tiefenbudget in [`04-mechanical.md`](04-mechanical.md) Abschnitt 4 rechnet **10,0 mm ab Boardvorderseite**, was auf Rückseiten von 0 / 11 / 22 führt | Eine der beiden Lesarten ist falsch. Welche, entscheidet sich mit Punkt 23: Bei Stapelverbindern ist die „Stapelhöhe" üblicherweise das Maß von Boardoberfläche zu Boardoberfläche — dann stimmt die Doku und `stack.py` ist um 1 mm je Ebene zu eng. Betrifft keine Leiterbahn, aber jede Aussage über Bauhöhen im Spalt (USB-C 9,25 · JST GH 5,7 · Magnetkörper) und die Gesamttiefe |
| 67 | **GELÖST 21.08.2026** | **Die Zentralscheibe rastete rechnerisch nicht ein.** Ihr lichtes Maß zwischen den Nasen ist 50,0 (F8), der Schnapprand des Adapters 49,8 — die Nasenspitzen lagen 0,1 mm je Seite **außerhalb** der Schulter und glitten darüber, statt dahinterzugreifen | **Rastnocken statt Übermaß am ganzen Rand.** Der Nutzer brachte es auf den Punkt: „die Zentralscheibe muss sich praktisch in diesen Aussparungen rüberklicken." An jeder der vier Kantenmitten — genau dort, wo F8 die Nasen misst — sitzt jetzt ein Nocken **50,6** (6,0 breit, 0,7 hoch) am hinteren Ende der Schulter: **0,30 mm Hintergriff je Seite**, aufgefahren über die gemessene Nasenfase (1,0 → 1,4). Der umlaufende Rand bleibt bei 49,8, damit sich die dünne Serienwand nur an vier kurzen Stellen aufweiten muss statt rundum. `check_adapter()` prüft den Hintergriff jetzt auf 0,2…0,6 mm, der Selbsttest der Explosionszeichnung ebenso. **Im Testdruck (Punkt 25) zu bestätigen:** Klickkraft und ob die Nase bleibend verformt |
| 68 | ✅ **behoben (20.08.2026): Freistellung als Randkerbe der linken Adapterkante, deckt die Buchse; Selbsttest der Zeichnung wacht darüber** | **Die USB-Freistellung des Adapters liegt auf der falschen Seite.** Sie steht bei x = −1,2…8,2 auf der 6-Uhr-Seite (`usb_relief_x0/x1`), und der Selbsttest prüft sie gegen die alten Buchsenkoordinaten −0,65…7,65. Die Buchse ist am 18.08.2026 aber an den **linken Rand** gewandert: J7 auf Mid bei (−20,0 / 8,4), quer, Körper x = −23,2…−16,8, dazu die Randkerbe des Top-Boards bei x = −23,5…−17,25 / y = 3,25…12,75 | Der Adapter stellt damit heute eine Stelle frei, an der nichts steht, und lässt Material dort stehen, wo der Buchsenkörper durchgreift — genau die Kollision, die die Freistellung verhindern sollte. Zu tun: `usb_relief_*` auf die Kerbenlage umstellen (sie liegt in x, nicht in y — die Freistellung muss die **linke** Auflagekante unterbrechen), den Selbsttest auf die realen Buchsenkoordinaten umstellen und Adapter neu erzeugen. Nicht in dieser Sitzung gemacht: Das ist eine Geometrieänderung samt CAD-Lauf, keine Zeichnungsfrage |
| 69 | ✅ **gelöst (20.08.2026): Alps SKQGABE010, LCSC C115351** — Alps' Standard-Flachtaster, 5,2 × 5,2 × 1,5, 1,6 N wie das abgekündigte SKRK, 24 000 Stück ab Lager. Größere Betätigungsfläche fängt das Druckkreuz besser; `switch_h` im Adapter auf 1,5 umgestellt, die Tiefenkette rechnet sich neu (Platine 0,5 nach vorn, Adapter im Stapel auf z 15,0) |
| 70 | P2 | **RESET/BOOT-Taster TL3342 führt LCSC nicht.** Zwei Stück, gut zugänglich auf Mid | Entweder JLC-verfügbaren 6×6-Taster wählen (Footprintwechsel) oder die zwei von Hand bestücken — bei zwei Positionen der einfachste Weg |
| 71 | ✅ **entschieden (20.08.2026)** | **Eingangssicherung flink statt träge**: NANO2-453 (Slo-Blo) endet bei 5 A, 15 A gibt es nur flink (451). Die Sicherung schützt die Leitung, den Motor schützt der HW-Trip | — |
| 72 | ✅ **behoben (20.08.2026)** | **Brücken-Bulk „100 µF/50 V in 1210" existierte nicht** — 1210-Keramik endet bei ~10 V für 100 µF. Jetzt Polymer 100 µF/35 V in 8×6,5, wie C3/C4 | — |
