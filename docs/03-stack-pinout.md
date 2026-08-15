# 03 – Stackverbinder und Pinmapping

> **Verbindlichkeit:** Dieses Pinmapping ist ein ausgearbeiteter Vorschlag als
> Arbeitsgrundlage. Sobald es bestätigt ist, gilt es **identisch für alle drei Projekte**.
> Änderungen ab dann nur gemeinsam und mit Versionsvermerk am Ende dieser Datei.

## 1. Grundregeln

- Motor-Hochströme werden **nicht** über die Stackverbinder geführt. Sie bleiben
  vollständig auf dem Bottom-Board.
- Stackverbinder führen ausschließlich Kleinleistung und Signale.
- **Regeländerung v0.3:** USB `D+`/`D−` laufen **doch** durch den Stack
  (`J_STK_A` 34/36, benachbart, PGND daneben). Die alte Regel stammte aus der Zeit
  mit USB-UART-Baustein auf dem Top-Board; mit dem nativen USB des ESP32-S3 auf dem
  Mid-Board gibt es keine Alternative — und Full-Speed-USB (12 MHz) über zwei
  benachbarte Kontakte ist unkritisch. ESD-Schutz sitzt an der Buchse auf TOP.
- Zwei Verbinder: `J_STK_A` (Power/Motor) und `J_STK_B` (UI/Kommunikation).
- Ausgangspunkt: zwei **2×20-Steckverbinder mit 1,27 mm Raster**. Die konkrete Serie ist
  anhand Stackhöhe und Verfügbarkeit auszuwählen.

## 2. Strombelastbarkeit der Stackpins

Steckverbinder im 1,27-mm-Raster liegen typisch bei **≈ 1 A pro Kontakt**, bei mehreren
benachbart stromführenden Kontakten weniger. Die Zielgröße von 3 A für `5V_SYS` lässt
sich daher **nicht** über einen Pin führen.

| Rail | Zielstrom | Pins | Bemerkung |
|---|---|---|---|
| `5V_SYS` | bis 3 A | **4** | plus mindestens gleiche Anzahl GND als Rückpfad |
| `3V3_SYS` | bis 1,5 A | **2** | |
| `6V2_STAR` | 0,08 A real | 1 | mit eigenem `GND_STAR` |
| `GND` | Summe | **12** | verteilt, auch als Schirmung zwischen Signalen |

Vor dem Footprint-Freeze ist das Datenblatt des gewählten Verbinders gegen diese Tabelle
zu prüfen. Reicht die Belastbarkeit nicht, ist entweder die 3-A-Zielgröße für `5V_SYS`
zu senken (die realen 5-V-Verbraucher oberhalb des Bottom-Boards sind gering) oder ein
gröberes Raster zu wählen.

## 3. J_STK_A – Power und Motor (2×20, 1,27 mm)

**Version 0.3 — alle drei Generatoren importieren `tools/stack_pinout.py`; diese
Tabellen sind daraus erzeugt.** Damit können die Boards nicht auseinanderlaufen.

Konvention: ungerade Pins Reihe A, gerade Reihe B; Pin *n* und *n+1* liegen
nebeneinander. Pin 1 auf allen drei Boards gleich orientiert.

| Pin | Signal | Pin | Signal |
|---:|---|---:|---|
| 1 | `PGND` | 2 | `PGND` |
| 3 | `5V_SYS` | 4 | `5V_SYS` |
| 5 | `5V_SYS` | 6 | `5V_SYS` |
| 7 | `PGND` | 8 | `PGND` |
| 9 | `3V3_SYS` | 10 | `3V3_SYS` |
| 11 | `PGND` | 12 | `PGND` |
| 13 | `6V2_STAR_F` | 14 | `PGND` |
| 15 | `PGND` | 16 | `M1_INA` |
| 17 | `M1_INB` | 18 | `USB_VBUS` |
| 19 | `PGND` | 20 | `M2_INA` |
| 21 | `PGND` | 22 | `M2_INB` |
| 23 | `STAR_EN` | 24 | `RSV_A2` |
| 25 | `PGND` | 26 | `I_SENSE1` |
| 27 | `AGND` | 28 | `I_SENSE2` |
| 29 | `AGND` | 30 | `HW_TRIP1` |
| 31 | `HW_TRIP2` | 32 | `TRIP_RST` |
| 33 | `RELAY_CTL` | 34 | `USB_DP` |
| 35 | `RSV_A4` | 36 | `USB_DN` |
| 37 | `RSV_A6` | 38 | `PGND` |
| 39 | `PGND` | 40 | `PGND` |

Änderungen gegenüber v0.1:

- **`Mx_PWM`/`Mx_DIR` → `Mx_INA`/`Mx_INB`.** Je ein PWM-Ausgang pro Brückenzweig;
  spart Richtungslogik. `Mx_EN`/`Mx_FAULT` entfallen — `~SD` gehört dem Hardware-Trip.
- **`USB_VBUS` neu** (Pin 18). Beim Programmieren speist USB über das ORing auf dem
  Bottom-Board die Logik; die Datenleitungen bleiben wie bisher auf dem Top-Board.
- `RELAY_CTL` und `TRIP_RST` bleiben, `HW_TRIP1/2` kommen jetzt direkt vom Latch.

## 4. J_STK_B – UI und Kommunikation (2×20, 1,27 mm)

**Version 0.3.** Pins 15/16 führen beide `RS485_DIR` — DE und /RE des MAX3485 sind
auf dem Mid-Board zusammengelegt (Standard-Halbduplex, ein GPIO).

| Pin | Signal | Pin | Signal |
|---:|---|---:|---|
| 1 | `PGND` | 2 | `PGND` |
| 3 | `3V3_SYS` | 4 | `3V3_SYS` |
| 5 | `PGND` | 6 | `I2C_SCL` |
| 7 | `PGND` | 8 | `I2C_SDA` |
| 9 | `PGND` | 10 | `I2C_INT` |
| 11 | `PGND` | 12 | `UART485_TX` |
| 13 | `PGND` | 14 | `UART485_RX` |
| 15 | `RS485_DIR` | 16 | `RS485_DIR` |
| 17 | `PGND` | 18 | `UART_AUX_TX` |
| 19 | `PGND` | 20 | `UART_AUX_RX` |
| 21 | `PRESENCE_INT` | 22 | `PGND` |
| 23 | `AUDIO_PWM` | 24 | `QSPI_CLK` |
| 25 | `PGND` | 26 | `BTN1` |
| 27 | `BTN2` | 28 | `BTN3` |
| 29 | `BTN4` | 30 | `PGND` |
| 31 | `QSPI_D0` | 32 | `QSPI_D1` |
| 33 | `PGND` | 34 | `QSPI_D2` |
| 35 | `QSPI_D3` | 36 | `DISP_CS` |
| 37 | `DISP_RST` | 38 | `DISP_BL` |
| 39 | `PGND` | 40 | `PGND` |

- `QSPI_CLK` und `QSPI_D0–D3` laufen mit 40 MHz. Sie liegen bewusst gebündelt und
  bekommen im Layout gleiche Länge und durchgehende Massereferenz.
- `DISP_BL` ist die PWM für die Hintergrundbeleuchtung (LCD, kein AMOLED).
- Zwei Reservepins sind entfallen; ohne Reserve steht der Verbinder nicht da, aber
  eng ist es.

## 4b. Version 0.4 – Umbenennung nach dem Sensorwechsel

Der Radar ist durch einen **ToF-Sensor VL53L1X auf dem Top-Board** ersetzt
(Begründung: [`09-display-and-mcu.md`](09-display-and-mcu.md), Abschnitt 5).
Die Pinlage bleibt unverändert, nur die Namen sind jetzt ehrlich:

| Pin | v0.3 | v0.4 | Funktion |
|---:|---|---|---|
| `J_STK_B` 18 | `UART_RADAR_TX` | `UART_AUX_TX` | Reserve-UART auf J7 (unbestückt) |
| `J_STK_B` 20 | `UART_RADAR_RX` | `UART_AUX_RX` | Reserve-UART auf J7 (unbestückt) |
| `J_STK_B` 21 | `RADAR_INT` | `PRESENCE_INT` | GPIO1 des VL53L1X, geht auf PCF8574 P4 |

Neu belegt sind zwei bisher freie Expanderpins — **nicht** am Stackverbinder,
sondern nur auf dem Mid-Board:

| PCF8574 | Signal | Funktion |
|---|---|---|
| P6 | `REED1_IN` | Fensterkontakt 1 |
| P7 | `REED2_IN` | Fensterkontakt 2 |
| P5 | `RELAY_CTL` | PhotoMOS zur Dunstabzugshaube (LOW = geschlossen) |

## 5. Prüfliste vor dem Footprint-Freeze

- [ ] Stromrating des gewählten Verbinders gegen Abschnitt 2 geprüft
- [ ] Stapelhöhe passt zu 10 mm (Bottom↔Mid) und 8–10 mm (Mid↔Top)
- [ ] Buchse/Stecker-Zuordnung je Board eindeutig festgelegt
- [ ] Pin 1 auf allen drei Boards identisch orientiert
- [ ] Verpolungssicherheit: mechanisch unmöglich, A und B zu vertauschen
- [ ] Verfügbarkeit und Second Source geprüft

## 6. Änderungsverlauf

| Version | Änderung |
|---|---|
| 0.1 | Erster ausgearbeiteter Vorschlag aus der Projektzusammenfassung |
| **0.2** | **Aus dem Bottom-Schaltplan erzeugt.** `INA`/`INB` statt `PWM`/`DIR`, QSPI-Bus für das Display, `USB_VBUS` ergänzt |
| **0.3** | **Gemeinsame Quelle `tools/stack_pinout.py`** für alle drei Boards. `USB_DP`/`USB_DN` durch den Stack (nativer USB), `STAR_EN` neu (Sternstecker sitzt auf TOP, der frühere J4 auf Bottom war ein Fehler), `RS485_DE`+`RE` → `RS485_DIR` |
