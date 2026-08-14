# 03 – Stackverbinder und Pinmapping

> **Verbindlichkeit:** Dieses Pinmapping ist ein ausgearbeiteter Vorschlag als
> Arbeitsgrundlage. Sobald es bestätigt ist, gilt es **identisch für alle drei Projekte**.
> Änderungen ab dann nur gemeinsam und mit Versionsvermerk am Ende dieser Datei.

## 1. Grundregeln

- Motor-Hochströme werden **nicht** über die Stackverbinder geführt. Sie bleiben
  vollständig auf dem Bottom-Board.
- Stackverbinder führen ausschließlich Kleinleistung und Signale.
- USB `D+`/`D−` werden **nicht** durch den Stack geführt. USB-C und USB-UART gehören auf
  dasselbe Top-Board.
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

**Version 0.2 — aus dem erzeugten Bottom-Schaltplan, damit Doku und Schaltplan
nicht auseinanderlaufen.** Quelle: `tools/gen_bottom_sch.py`.

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
| 23 | `RSV_A1` | 24 | `RSV_A2` |
| 25 | `PGND` | 26 | `I_SENSE1` |
| 27 | `AGND` | 28 | `I_SENSE2` |
| 29 | `AGND` | 30 | `HW_TRIP1` |
| 31 | `HW_TRIP2` | 32 | `TRIP_RST` |
| 33 | `RELAY_CTL` | 34 | `RSV_A3` |
| 35 | `RSV_A4` | 36 | `RSV_A5` |
| 37 | `RSV_A6` | 38 | `PGND` |
| 39 | `PGND` | 40 | `PGND` |

Änderungen gegenüber v0.1:

- **`Mx_PWM`/`Mx_DIR` → `Mx_INA`/`Mx_INB`.** Je ein PWM-Ausgang pro Brückenzweig;
  spart Richtungslogik. `Mx_EN`/`Mx_FAULT` entfallen — `~SD` gehört dem Hardware-Trip.
- **`USB_VBUS` neu** (Pin 18). Beim Programmieren speist USB über das ORing auf dem
  Bottom-Board die Logik; die Datenleitungen bleiben wie bisher auf dem Top-Board.
- `RELAY_CTL` und `TRIP_RST` bleiben, `HW_TRIP1/2` kommen jetzt direkt vom Latch.

## 4. J_STK_B – UI und Kommunikation (2×20, 1,27 mm)

**Version 0.2.** Der QSPI-Bus des ST77916 braucht sieben Leitungen — das war der in
v0.1 vermerkte fehlende Pin. Gelöst, indem `DISP_DC` (bei QSPI unnötig) und die
Reservepins umgewidmet wurden.

| Pin | Signal | Pin | Signal |
|---:|---|---:|---|
| 1 | `PGND` | 2 | `PGND` |
| 3 | `3V3_SYS` | 4 | `3V3_SYS` |
| 5 | `PGND` | 6 | `I2C_SCL` |
| 7 | `PGND` | 8 | `I2C_SDA` |
| 9 | `PGND` | 10 | `I2C_INT` |
| 11 | `PGND` | 12 | `UART485_TX` |
| 13 | `PGND` | 14 | `UART485_RX` |
| 15 | `RS485_DE` | 16 | `RS485_RE` |
| 17 | `PGND` | 18 | `UART_RADAR_TX` |
| 19 | `PGND` | 20 | `UART_RADAR_RX` |
| 21 | `RADAR_INT` | 22 | `PGND` |
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
