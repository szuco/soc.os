# 09 – Display, MCU und GPIO-Budget

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
| Display SPI (SCK, MOSI, CS, DC, RST, Backlight) | | 6 |
| I2C (Sensorik, ADC, Expander) | | 2 |
| Taster | | 4 |
| RS-485 (TX, RX, DE) | | 3 |
| Radar (TX, RX) | | 2 |
| Audio | | 1 |
| Motor Steuerung | 2 × PWM, 2 × DIR | 4 |
| Motor Sammelsignale | nFAULT, nSLEEP | 2 |
| **Summe direkt am MCU** | | **24** |

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
