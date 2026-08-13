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

Konvention: ungerade Pins Reihe A, gerade Pins Reihe B. Pin *n* und *n+1* liegen
nebeneinander. Pin 1 ist markiert und auf allen drei Boards gleich orientiert.

| Pin | Signal | Pin | Signal |
|---:|---|---:|---|
| 1 | GND | 2 | GND |
| 3 | 5V_SYS | 4 | 5V_SYS |
| 5 | 5V_SYS | 6 | 5V_SYS |
| 7 | GND | 8 | GND |
| 9 | 3V3_SYS | 10 | 3V3_SYS |
| 11 | GND | 12 | GND |
| 13 | 6V2_STAR | 14 | GND_STAR |
| 15 | GND | 16 | M1_PWM |
| 17 | M1_DIR | 18 | M1_EN |
| 19 | GND | 20 | M1_FAULT |
| 21 | GND | 22 | M2_PWM |
| 23 | M2_DIR | 24 | M2_EN |
| 25 | GND | 26 | M2_FAULT |
| 27 | AGND | 28 | I_SENSE1 |
| 29 | AGND | 30 | I_SENSE2 |
| 31 | GND | 32 | HW_TRIP1 |
| 33 | HW_TRIP2 | 34 | TRIP_RST |
| 35 | RELAY_CTL | 36 | RSV_A1 |
| 37 | RSV_A2 | 38 | RSV_A3 |
| 39 | GND | 40 | GND |

Hinweise:

- `I_SENSE1`/`I_SENSE2` liegen bewusst jeweils neben `AGND`, damit die analoge Leitung
  einen definierten, ruhigen Rückpfad direkt daneben hat.
- `AGND` und `GND` werden **sternförmig an genau einer Stelle** auf dem Bottom-Board
  verbunden, nicht mehrfach über den Stack.
- `Mx_PWM` sind die schnellsten Signale auf diesem Verbinder und haben jeweils GND als
  direkten Nachbarn.
- `RELAY_CTL` liegt hier unter der Annahme, dass das Relais auf dem Bottom-Board sitzt —
  siehe Prüfpunkt in [`00-system-overview.md`](00-system-overview.md).
- `5V_SYS` ist **bidirektional**: im Normalbetrieb speist der Buck auf BOTTOM nach oben,
  im USB-Betrieb speist USB von TOP nach unten. Siehe
  [`01-power-tree.md`](01-power-tree.md).

## 4. J_STK_B – UI und Kommunikation (2×20, 1,27 mm)

| Pin | Signal | Pin | Signal |
|---:|---|---:|---|
| 1 | GND | 2 | GND |
| 3 | 3V3_SYS | 4 | 3V3_SYS |
| 5 | GND | 6 | I2C_SCL |
| 7 | GND | 8 | I2C_SDA |
| 9 | GND | 10 | I2C_INT |
| 11 | GND | 12 | UART485_TX |
| 13 | GND | 14 | UART485_RX |
| 15 | RS485_DE | 16 | RS485_RE |
| 17 | GND | 18 | UART_RADAR_TX |
| 19 | GND | 20 | UART_RADAR_RX |
| 21 | RADAR_INT | 22 | GND |
| 23 | AUDIO_PWM | 24 | AUDIO_EN |
| 25 | GND | 26 | BTN1 |
| 27 | BTN2 | 28 | BTN3 |
| 29 | BTN4 | 30 | GND |
| 31 | DISP_RST | 32 | DISP_DC |
| 33 | GND | 34 | SYS_RST |
| 35 | RSV_B1 | 36 | RSV_B2 |
| 37 | RSV_B3 | 38 | RSV_B4 |
| 39 | GND | 40 | GND |

Hinweise:

- `DISP_RST`/`DISP_DC` sind nur bei einem SPI-OLED nötig. Bei I2C-OLED bleiben sie frei
  und dienen als zusätzliche Reserve — der Displaytyp ist noch offen.
- Bei einem SPI-OLED fehlen auf diesem Verbinder `SCK`, `MOSI` und `CS`. Dann sind drei
  der `RSV_B*`-Pins entsprechend zu belegen; das ist beim Displayentscheid mitzuführen.
- `BTN1..BTN4` werden auf dem Mid-Board mit Pull-ups versehen; Entprellung in Software.
- Die vier `RSV_B*` sind bewusst frei, um spätere Sensorik ohne Redesign des Stacks
  anbinden zu können.

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
| 0.2 (angekündigt) | Displaywechsel auf 1,43"-AMOLED (QSPI): das Display braucht **7 Leitungen** durch den Stack (`QSPI_CLK`, `QSPI_D0–D3`, `DISP_CS`, `DISP_RST`). Vorhanden auf `J_STK_B`: `DISP_RST`, `DISP_DC` (entfällt bei QSPI) und `RSV_B1–B4` — macht 6, **einer fehlt**. Kandidat: `SYS_RST` (Pin 34) prüfen oder Doppelnutzung lösen. Die Neubelegung erfolgt zusammen mit dem Top-Board-Schaltplan; bis dahin gilt v0.1 nicht als eingefroren. |
