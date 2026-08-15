# 09 – Display, MCU und GPIO-Budget

> **Revision 2:** Die ursprüngliche Empfehlung (1,28"-GC9A01-LCD) wurde als zu klein
> bewertet. Neue Empfehlung in [Abschnitt 1b](#1b-revision-größeres-display-und-sicheltasten):
> **1,43"-AMOLED (CO5300) mit vier sichelförmigen Tasten** — inklusive der ehrlichen
> Begründung, warum die Einbrenn-Abwägung jetzt anders ausfällt als in Revision 1.
>
> **Revision 3:** Die Support-Tabelle in 1b behandelte fehlende ESPHome-Treiber als
> K.-o.-Kriterium — das war die falsche Abhängigkeitsrichtung und ist in
> [`10-firmware-strategy.md`](10-firmware-strategy.md) korrigiert.
>
> **Revision 4 — ENTSCHIEDEN: ST77916, 1,46" rund, 360×360, aktiv Ø 37,25 mm.**
> Und der befürchtete Treiberaufwand entfällt vollständig: ESPHomes `mipi_spi`
> kennt ein **`model: CUSTOM` mit `init_sequence` in YAML**. Damit läuft der
> ST77916 **ohne jede C++-Komponente**. Die Hersteller-Initialisierungssequenz
> (214 Kommandos) liegt als
> [`../firmware/esphome/st77916_init.yaml`](../firmware/esphome/st77916_init.yaml)
> bei; die Konfiguration ist mit `esphome config` validiert. Das AMOLED entfällt
> als Plan B, die Einbrenn-Auflagen aus Revision 2 sind damit gegenstandslos.

## 1. Die Displayfrage: Touchscreen oder OLED mit 4 Tastern?

### Randbedingung

Der Rahmenausschnitt der 55er-Schalterprogramme ist **55 × 55 mm**. Abzüglich
Blendenrand und Toleranz bleibt eine nutzbare Sichtfläche von **maximal ca. 40 × 40 mm**.
Das Board darunter ist rund. Damit scheiden alle größeren Rechteckdisplays aus.

### Bewertung der Optionen

| | 0,96" OLED SSD1306 | 1,3" OLED SH1106 | **1,28" LCD GC9A01** | 2,8" Touch |
|---|---|---|---|---|
| Auflösung | 128×64 mono | 128×64 mono | **240×240, 262 k Farben** | 320×240 |
| Modulgröße | ~27×27 mm | ~35×33 mm | **~37 mm rund** | ~50×70 mm |
| Passt in 55er | ja | ja | **ja, rund wie das Board** | **nein** |
| Einbrennen bei Dauerbetrieb | **ja, real** | **ja, real** | nein (LCD) | nein |
| ESPHome-Support | `ssd1306_i2c` | `sh1106_i2c` | `ili9xxx`, `model: gc9a01a` | ja |
| Touch | nein | nein | optional (CST816S) | ja |

### Warum kein Touch

Drei Gründe, jeder für sich ausreichend:

1. **Kapazitiver Touch funktioniert hinter einer 3D-gedruckten Platte schlecht.**
   FDM-Drucke haben Lufteinschlüsse zwischen den Lagen und schwankende Wandstärke. Die
   kapazitive Kopplung wird dadurch inhomogen und temperaturabhängig. Zuverlässig wäre
   nur eine Frontplatte aus Acryl oder Glas — das widerspricht der Vorgabe „3D-Druck".
2. **Ein Wandschalter wird blind bedient.** Man greift im Dunkeln zum Lichtschalter.
   Ein Touchfeld ohne Haptik erzwingt Hinsehen; vier physische Taster nicht.
3. **Der 2,8"-Touchscreen passt geometrisch nicht** in einen 55×55-Ausschnitt.

### Empfehlung

> **Rundes 1,28"-IPS-LCD mit GC9A01A (240×240) plus vier physische Taster.**

Begründung:

- Die runde Form entspricht dem runden Board und der runden Unterputzdose — die vier
  Taster lassen sich symmetrisch auf einem Teilkreis anordnen. Das ergibt ein Layout,
  das wie ein entworfenes Produkt aussieht statt wie ein Modul hinter einem Loch.
- **Kein Einbrennen.** Ein Wandpanel zeigt 24/7 weitgehend statischen Inhalt
  (Temperatur, Uhrzeit, Symbole). Genau dafür ist OLED der falsche Technologietyp —
  das ist das stärkste Einzelargument gegen die ursprünglich vorgesehene OLED-Lösung.
- Die Hintergrundbeleuchtung ist über PWM dimmbar. In Verbindung mit dem Radar-
  Bewegungsmelder lässt sich das Display nachts dunkeltasten und bei Annäherung
  aufblenden — ein Verhalten, das mit OLED zwar auch ginge, dort aber die
  Einbrenn-Problematik verschärft.
- Voller Farbraum erlaubt Statusfarben (Jalousie fährt, Störung, Stern an) ohne Text.

**Kosten der Entscheidung, ehrlich benannt:** Das LCD braucht SPI statt I2C (6 statt
2 GPIOs), mehr RAM für den Framebuffer und mehr Strom durch die Hintergrundbeleuchtung
(typ. 20–60 mA). Das ist der Grund für die MCU-Wahl im nächsten Abschnitt.

**Fallback**, falls das Budget oder der Bauraum doch nicht reicht: `ssd1306_i2c` mit
0,96". Die Frontplatte bleibt verwendbar — nur `disp_window_d` und `disp_rebate_d` in
`mechanical/frontplate.py` anpassen und neu erzeugen.

## 1b. Revision: größeres Display und Sicheltasten

### Was maximal geht

Der 55×55-Rahmenausschnitt setzt die harte Grenze. Mit vier Tasten **neben** dem
Display (Revision 1) war bei Ø 32 mm Schluss. Die Sichelidee löst das: Die Tasten
werden **Ringsegmente um das Fenster** statt Kreise daneben — dann trägt der Ring
r 21–25,8 mm die Tasten, und das Fenster kann bis ≈ Ø 40 mm wachsen. Mehr geht
geometrisch nicht: Bei Fenster > Ø 40 mm bricht der Sichelring durch die
Plattenkante an den Seitenmitten (Platte halb = 27,3 mm).

### Marktlage runder Panels, geprüft gegen ESPHome 2026.6.5

Support-Status direkt aus dem installierten ESPHome-Quellcode ermittelt
(`mipi_spi/models/`, `qspi_dbi`), nicht aus Foren:

| Panel | aktiv | Auflösung | Treiber | ESPHome | Einbrennen |
|---|---|---|---|---|---|
| 1,28" LCD | Ø 32,4 | 240×240 | GC9A01A | ✅ nativ | nein |
| **1,43" AMOLED** | **Ø 36,3** | **466×466** | **CO5300, QSPI** | **✅ nativ (`mipi_spi`)** | **ja — beherrschbar, s. u.** |
| 1,46"/1,5" LCD | Ø 37–40 | 360×360 | ST77916 | ❌ nicht enthalten | nein |
| 1,6" LCD | Ø 40,6 | 400×400 | ST77903 | ❌ nicht enthalten | nein |
| 1,85"+ rund | Ø 47+ | 360×360+ | ST77916 | ❌ | passt ohnehin nicht (Tasten) |

Das ist die unbequeme Wahrheit dieser Tabelle: **die größeren runden LCDs — die
technisch beste Wahl — haben keinen ESPHome-Treiber.** Wer sie will, schreibt eine
External Component gegen `esp_lcd_st77916` (existiert in Espressifs
esp-iot-solution). Machbar, aber echter Aufwand mit Pflegelast.

### Entscheidung

> ~~**1,43"-AMOLED rund, 466×466, CO5300**~~ — **überholt durch Revision 4 (ST77916).**
> Der folgende Abschnitt bleibt als Entscheidungsprotokoll stehen.
> Fenster Ø 37,4 mm, +26 % aktive Fläche,
> 3,8× Pixel gegenüber GC9A01, mit `esphome config` end-to-end validiert.

**Damit revidiere ich das stärkste Argument aus Revision 1** — „kein OLED wegen
Einbrennen" — und das braucht eine saubere Begründung: Das Argument galt für ein
Panel, das 24/7 statischen Inhalt zeigt. Der Radar-Bewegungsmelder ändert die
Rechnung: Das Panel ist **nur bei Anwesenheit an** und wird nach 2 Minuten ohne
Bewegung dunkelgetastet (Automation in
[`../firmware/esphome/switchstack.yaml`](../firmware/esphome/switchstack.yaml)).
Ein Flurpanel kommt so auf wenige Stunden Leuchtzeit pro Tag statt 24 — bei AMOLED
der Unterschied zwischen „brennt in Monaten ein" und „hält viele Jahre". Dazu kommt,
was AMOLED an der Wand ausspielt: echtes Schwarz (das Panel verschwindet optisch in
der Blende), keine Hintergrundbeleuchtung, Helligkeit per Kommando.

**Auflagen, ohne die diese Entscheidung kippt:**
1. Die Radar-Dunkeltastung ist **Pflichtbestandteil**, keine Option.
2. Statische UI-Elemente bei gedimmter Grundhelligkeit (≤ 80 %) darstellen.
3. Fällt der Radar aus der Stückliste, fällt das AMOLED mit — dann GC9A01
   (klein) oder ST77916 (External-Component-Aufwand).

**Alternative rechteckig:** siehe [Abschnitt 1c](#1c-warum-kein-rechteckiges-display).

> **Korrektur.** An dieser Stelle stand: ein 2,0"-Rechteck habe „fast die doppelte
> Fläche" und die Entscheidung sei eine Geschmacksfrage. **Beides war falsch.** Es sind
> +52 % gegenüber dem GC9A01 und nur +15 % gegenüber dem ST77916 — und das Modul passt
> gar nicht auf das Ø-52-Board. Nachrechnung in 1c.

## 1c. Warum kein rechteckiges Display?

Die Frage ist berechtigt: Rechteckpanels sind billiger, breiter verfügbar, besser
treiberunterstützt, und für Text (Temperatur, Status, Listen) ist ein Rechteck
das bessere UI-Format — ein Kreis verschenkt die Ecken bei jedem Textlayout.

Trotzdem fällt die Entscheidung hier eindeutig gegen das Rechteck, aus **Geometrie,
nicht aus Formensprache**.

### Der harte Grund: die Diagonale

Das Modul sitzt auf einer **runden Ø-52-mm-Leiterplatte** in einer **runden Dose**.
Bei 3 mm Randabstand je Seite bleibt ein Hüllkreis von **Ø 46 mm**. Was da hineinpasst:

| Form im Hüllkreis Ø 46 | Fläche | Anteil |
|---|---:|---:|
| **Kreis** | **1 662 mm²** | **100 %** |
| Quadrat 32,5 × 32,5 | 1 058 mm² | 63,7 % |
| 4:3 — 36,8 × 27,6 | 1 016 mm² | 61,1 % |
| 16:9 — 40,1 × 22,6 | 904 mm² | 54,4 % |

Das ist kein Zufall, sondern Mathematik: **in einem runden Bauraum ist der Kreis
flächenoptimal.** Das bestflächige einbeschriebene Rechteck — das Quadrat — erreicht
nur 2/π = 63,7 % der Kreisfläche. Jedes Rechteck verschenkt in einer runden Dose ein
gutes Drittel.

### Konkrete Panels gegen das Ø-52-Board

| Panel | aktiv | Modul-Diagonale/Ø | passt? |
|---|---:|---:|---|
| GC9A01 1,28" rund | 824 mm² | Ø 37,5 | ✅ |
| **ST77916 1,46" rund** | **1 090 mm²** | Ø 41,5 | ✅ |
| CO5300 1,43" AMOLED | 1 035 mm² | Ø 41,0 | ✅ |
| ST7789V 1,69" rechteckig | 913 mm² | 46,1 mm | ⚠️ auf Kante |
| ST7789V **2,0" rechteckig** | 1 256 mm² | **54,0 mm** | ❌ **> Ø 52 Board** |

Zwei Ergebnisse, die die frühere Aussage widerlegen:

1. **Das 2,0"-Panel passt nicht.** Modul-Diagonale 54,0 mm gegen 52 mm Boarddurchmesser
   — die Ecken stehen über die Platine hinaus. Selbst die *aktive* Fläche hat schon
   51,1 mm Diagonale. Es war nie eine Option, sondern ein Rechenfehler.
2. **Das 1,69"-Panel passt gerade so — und ist trotzdem kleiner** als das runde
   ST77916 (913 vs. 1 090 mm², −16 %). Genau der erwartete Effekt aus der Tabelle oben.

### Der Ausweg, und warum er nicht genommen wird

Man könnte das Display **an der Frontplatte statt auf der Leiterplatte** befestigen und
per Flexleitung anbinden. Dann begrenzt nicht mehr das Ø-52-Board, sondern die lichte
Dosenweite (≈ 55–57 mm, an den Schraubdomen weniger). Ein 2,0"-Modul mit 54,0 mm
Diagonale hätte dort **unter 0,5 mm Luft je Seite** — im Toleranzfeld einer
Kunststoffdose ist das keine Passung, sondern ein Glücksspiel. Dazu käme eine
mechanisch entkoppelte Flexverbindung zwischen Platte und Stack. Beides für −25 %
Pixel und +15 % Fläche gegenüber dem runden ST77916: kein guter Handel.

### Wann das Rechteck doch richtig wäre

- **Wenn die runde Dose fällt.** In einem Aufputzgehäuse oder hinter einer 2-fach-Blende
  ändert sich die Rechnung komplett — dann gewinnt das Rechteck deutlich.
- **Wenn viel Text angezeigt werden soll.** Fahrpläne, Listen, mehrzeilige Zustände
  liegen auf einem Kreis schlecht. Bei Temperatur + Symbol + Statusfarbe ist der Kreis
  kein Nachteil.
- **Wenn Stückzahl und Preis zählen.** Rechteckpanels sind spürbar billiger und breiter
  verfügbar als runde.

Für dieses Gerät — rund, in der Dose, mit vier Sicheltasten und wenig Text — bleibt es
beim runden Panel.

### Sicheltasten-Mechanik

Vier Ringsegment-Kappen (r 21–25,8 mm, je ≈ 63° Bogen) als **separate Druckteile**,
von hinten eingesetzt, mit Rückhaltekragen gegen Herausfallen und je zwei
Druckstößeln (Ø 2,2 mm, r = 23,3 mm, ±18° um die Diagonalen), die auf SMD-Taster
der Top-Leiterplatte drücken. **Die Federung kommt vom Taster, nicht vom
Kunststoff** — gedruckte Federscharniere ermüden, Metallkuppel-Taster nicht. Zwei
Stößel pro Kappe verhindern das Verkippen beim Druck ans Bogenende; die beiden
Taster je Kappe werden elektrisch parallel geschaltet (bleibt bei 4 GPIOs).
Tastfläche je Sichel ≈ 124 mm² statt 38 mm² beim alten Ø-7-Loch.

Konsequenz fürs Top-Board-Layout: 8 Tasterpositionen bei r = 23,3 mm auf
27/63/117/153/207/243/297/333°, Modulfreiraum Ø 41,5 mm zentral. Der
Displaymodul-Außendurchmesser ist **vor dem Layout am realen Teil zu messen**.

## 2. MCU

> **Empfehlung: ESP32-S3-WROOM-1-N16R8** (16 MB Flash, 8 MB PSRAM)

| Kriterium | Warum S3 statt klassischem ESP32 |
|---|---|
| Framebuffer 240×240×16 bit = 115 kB | PSRAM vorhanden, kein Gedränge im internen RAM |
| USB | **Nativ (USB-Serial-JTAG)** — der separate USB-UART-Baustein entfällt |
| ESPHome | volle Unterstützung, `esp32` mit `variant: esp32s3` |
| Flash 16 MB | OTA mit zwei Slots plus Grafikassets ohne Enge |

Der Wegfall des USB-UART-Bausteins ist ein direkter Gewinn für das Top-Board: weniger
Bauteile auf der ohnehin knappen Fläche, und `D+`/`D−` gehen von der USB-C-Buchse
direkt an das Modul.

> **Achtung bei der N16R8-Variante:** Die Oktal-PSRAM belegt **GPIO 35, 36 und 37**.
> Diese Pins stehen **nicht** zur Verfügung. Ebenso sind GPIO 19/20 für nativen USB
> reserviert und 0/3/45/46 sind Strapping-Pins.

## 3. GPIO-Budget — und warum es knapp wird

Zusammengezählt aus der Peripherieliste:

| Domäne | Signale | GPIOs |
|---|---|---:|
| Display QSPI (CLK, D0–D3, CS, RST, Backlight; QSPI braucht kein DC) | | 8 |
| I2C (Sensorik, ADC, Expander) | | 2 |
| Taster | | 4 |
| RS-485 (TX, RX, DE) | | 3 |
| Radar (TX, RX) | | 2 |
| Audio | | 1 |
| Motor Steuerung | 2 × PWM, 2 × DIR | 4 |
| Motor Sammelsignale | nFAULT, nSLEEP | 2 |
| **Summe direkt am MCU** | | **26** |

Tatsächlich belegt in [`../firmware/esphome/switchstack.yaml`](../firmware/esphome/switchstack.yaml):
**26 GPIOs**, geprüft auf Doppelbelegung sowie auf Kollision mit PSRAM (35–37),
nativem USB (19/20) und Strapping-Pins (0/3/45/46). Das Backlight liegt auf **GPIO43**
— frei, weil das Logging über den nativen USB läuft und UART0 damit unbenutzt bleibt.

Direkt am MCU nicht mehr unterzubringen wären zusätzlich `HW_TRIP1/2`, `TRIP_RST`,
`RELAY_CTL` sowie zwei getrennte FAULT-Leitungen. Zwei Konsequenzen:

1. **I2C-GPIO-Expander** (TCA9534 oder PCF8574) für die langsamen Signale
   `HW_TRIP1`, `HW_TRIP2`, `TRIP_RST`, `RELAY_CTL`. Kostet zwei bereits vorhandene
   I2C-Leitungen statt vier bis sechs GPIOs. ESPHome unterstützt beide nativ.
2. **Motortreiber mit PWM/DIR-Interface wählen**, nicht mit vier Einzel-Gate-Signalen.
   Das halbiert die Steuerleitungen pro Kanal.

Das wirkt direkt auf das Stack-Pinmapping in [`03-stack-pinout.md`](03-stack-pinout.md)
zurück und ist dort beim nächsten Update nachzuziehen.

## 4. Der Konflikt zwischen ESPHome und der Strommessung

Dies ist die wichtigste Erkenntnis dieses Kapitels.

Das Motorkonzept in [`02-motor-control.md`](02-motor-control.md) verlangt eine
Strommessung, die **PWM-synchron** abtastet — bei reduzierter PWM misst ein
Low-Side-Shunt sonst systematisch zu wenig.

**ESPHome kann das nicht.** Sein Ausführungsmodell ist eine Polling-Schleife; Sensoren
werden in Intervallen von typischerweise ≥ 60 ms abgefragt. Ein ADS1115 über I2C schafft
maximal 860 Samples/s und ist ebenfalls nicht mit dem PWM-Timing gekoppelt. Eine
Stall-Erkennung, die auf einem sauberen Stromsignal beruht, lässt sich in reinem
ESPHome-YAML nicht bauen.

### Lösung

Die Aufgabenteilung folgt der Zeitkonstante:

| Ebene | Zuständig für | Realisierung |
|---|---|---|
| **Hardware** | Hard-Trip bei ≈ 13 A | Comparator + Latch, ohne Firmware |
| **C++-Komponente** | PWM, ADC-Sampling, Baseline, Stall, 60-s-Timeout | ESPHome **External Component** |
| **ESPHome-YAML** | Entitäten, Display, Taster, Sensorik, HA-Anbindung | Standardkomponenten |

ESPHome unterstützt eigene C++-Komponenten über `external_components` als
vollwertigen, dokumentierten Weg. Der schnelle Regelkreis läuft dort mit
LEDC-Hardware-PWM und ADC im Continuous Mode; nach außen erscheint er als normale
`cover`-Entität in Home Assistant.

Bis diese Komponente geschrieben ist, arbeitet
[`../firmware/esphome/switchstack.yaml`](../firmware/esphome/switchstack.yaml) mit
`template`-Covers. Die sind in Home Assistant voll bedienbar, haben aber **keine
Lasterkennung** — sie fahren auf Zeit. Das ist ein bewusster Zwischenstand, kein
Endzustand.

## 5. Präsenzerkennung: warum ToF statt Radar

Ziel ist nicht Raumüberwachung, sondern **Präsenz bis etwa 1 m vor dem Display**
— und, weil das Gerät in der Fensterlaibung sitzt, zusätzlich ein Hinweis, wenn
jemand durch die geöffnete Fensteröffnung steigt.

### Der harte Grund gegen Radar: es gibt kein Fenster

Die Frontplatte hat genau vier Stellen, an denen nach vorn durchbrochen werden
darf — die vier Stege zwischen den Sicheltasten. Innen liegt das Displaymodul
(Ø 41,5 mm), im Ring r 22…26,2 mm bewegen sich die Kappen, und auf 3 und 9 Uhr
sitzen die Befestigungsbohrungen der Platinen. Bleiben 12 und 6 Uhr.

24 GHz strahlt zwar durch gedruckten Kunststoff, aber nicht durch das LCD — und
für ein Modul von 20 × 20 mm (LD2420, LD2410S) oder 22 × 16 mm (LD2410C) ist in
einem 17 mm breiten Steg kein Platz. Radar scheitert hier an der Mechanik, nicht
an der Physik.

### Was stattdessen gewählt wurde

| | VL53L1X (gewählt) | LD2410C | PIR AM312 | Kapazitiv |
|---|---|---|---|---|
| Baugröße | **4,9 × 2,5 mm** | 22 × 16 mm | 10 × 8 + Linse | beliebig |
| Reichweite | 4 m, Schwelle frei | 6 m | 3–5 m | 10–20 cm |
| Fenster | Loch Ø 4,5 mm | keins | Linse sichtbar | keins |
| ESPHome | External Component | nativ | `gpio` | `esp32_touch` |
| passt hinter diese Platte | **ja** | nein | nein | ja, zu kurz |

Der ToF misst **Entfernung**. Die Schwelle liegt damit exakt bei 1,0 m statt bei
einer Empfindlichkeitsstufe, und der Öffnungswinkel von rund 25° schaut genau
nach vorn — ein Radar mit ±60° und 6 m würde auf jeden ansprechen, der durch den
Flur geht.

### Zweitfunktion: Durchstiegsmeldung

In der Laibung montiert misst der Sensor **quer durch die Fensteröffnung**. Die
Baseline ist die gegenüberliegende Laibung (0,8–1,4 m), alles Nähere steht in der
Öffnung. Das ergibt eine Lichtschranke ohne Gegenstück. Der VL53L1X kann seine
**ROI umschalten** und den Messkegel damit um ±10–15° schwenken; drei
nacheinander abgetastete Zonen spannen ein Dreieck über die Öffnung.

Grenzen, die zur Auslegung gehören:

- **Fremdlicht.** Ein ToF am Fenster ist der ungünstigste Ambient-Fall. In der
  Sonne bricht die Reichweite ein; `short`-Modus und die Statusflags jeder
  Messung sind Pflicht, Blendung ist als eigener Zustand zu melden.
- **Eine Ebene, kein Volumen.** Auch mit drei Zonen bleibt es eine Fläche knapp
  über der Fensterbank.
- **Kein Sabotageschutz.** Das Loch lässt sich zukleben. Der Sensor ist ein
  Indiz neben den Reed-Kontakten, kein VdS-tauglicher Melder.
- **Der geschlossene Flügel** kann im Strahl stehen. Die Baseline wird beim
  Einbau gemessen, nicht angenommen.
