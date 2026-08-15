# 00 – Systemübersicht

## 1. Zielsystem

Stackbares PCB-System aus drei gestapelten Leiterplatten in einer massiven
Schalter-Unterputzdose mit 61 mm Tiefe.

- **Bottom und Mid: rund, Ø 52,0 mm** — sie sitzen in der Dose
- **Top: quadratisch, 47 × 47 mm mit R 4** — es sitzt **vor** der Dose im
  Adapter, weil die Druckkreuze der Zentralscheibe auf r = 26,9 liegen und ein
  Kreis dort nicht hinreicht ([`04-mechanical.md`](04-mechanical.md) 1d/1e)
- Bevorzugte Leiterplattendicke: **1,0 mm**
- Die drei Ebenen trennen Benutzeroberfläche/Sensorik, Logik/Kommunikation und
  Leistungselektronik/Motorsteuerung.

## 2. Externe Versorgung und Verbraucher

| Verbraucher | Spannung | Leistung | Strom | Anmerkung |
|---|---|---|---|---|
| Klappladenmotor 1 | 24 V DC ±10 % | 100 W (Typenschild) | Dauer ≈ 0,3–1,0 A, **Blockierstrom offen** | 2 Adern, Umpolung, keine Elektronik |
| Klappladenmotor 2 | 24 V DC ±10 % | 100 W (Typenschild) | Dauer ≈ 0,3–1,0 A, **Blockierstrom offen** | 2 Adern, Umpolung, keine Elektronik |
| Weihnachtsstern | 6,0–6,5 V | 0,5 W | ≈ 80 mA | nur im 24-V-Normalbetrieb |

Antrieb: Drehflügelmotor für Fensterläden, 25 Nm bei 1,9 U/min, Fahrzeit **18 s**
(≈ 205° Schwenk), −20…+60 °C, bis 50 kg je Flügel.

Die mechanische Abtriebsleistung beträgt nur ≈ 5 W, der Laufstrom entsprechend
≈ 0,3–1,0 A. **Der Motor hat keine eigene Elektronik** — die Hinderniserkennung ist
Aufgabe dieses Geräts, und den Blockierstrom begrenzt nichts. Herleitung und
Messprotokoll: [`11-motor-data.md`](11-motor-data.md).

**Externe Verkabelung:** `24V_IN+` und `24V_IN−` kommen herein. Je Motor gehen zwei
Leitungen heraus: `M1_A`/`M1_B` und `M2_A`/`M2_B`. Insgesamt sechs Leistungsadern am
unteren Anschluss.

**USB-C** wird ausschließlich für Programmierung/Debug und ggf. Versorgung der Logik
während der Programmierung genutzt. Der Stern erhält einen **separaten
Frontanschluss** — eine 2,5-mm-Klinkenbuchse, Punkt 30 — und hängt nicht am USB-Port.

## 3. Peripherie (Stand der Schaltpläne)

| Funktion | Bauteil | Anzahl | Schnittstelle | Board |
|---|---|---|---|---|
| Temperatur + Feuchte | SHT40-AD1B, 0x44 | 1 | I2C | TOP |
| Runddisplay 360 × 360 | ST77916, 1,46" | 1 | QSPI + CS/RST/BL | TOP |
| Bedientaster | 8 SMD-Taster, je 2 parallel | 4 Tasten | GPIO | TOP |
| Präsenz / Durchstieg | VL53L1X (ToF) | 1 | I2C + INT | TOP |
| Stern-Ausgang 6,2 V | P-FET + PTC, 2,5-mm-Klinke | 1 | 2-polig | TOP (Front) |
| USB-C | nativer USB des S3, ESD USBLC6 | 1 | D+/D− durch den Stack | TOP |
| MCU | ESP32-S3-WROOM-1-N16R8 | 1 | — | MID |
| RS-485 | MAX3485 + Fail-Safe-Bias, JST-XH | 1 | UART + DIR | MID |
| GPIO-Expander | PCF8574, 0x20 | 1 | I2C | MID |
| Piezo | passiv + Treiberstufe | 1 | PWM (`rtttl`) | MID |
| Meldekontakt Haube | PhotoMOS AQY282GS (SELV) | 1 | Expander P5 | MID |
| Verschlusskontakte | Reed, Pull-up + RC + ESD, JST-SH | 2 | Expander P6/P7 | MID |
| Motorendstufe / H-Brücke | 2 × IR2104 + 4 N-FET je Kanal | 2 | 2 × PWM (INA/INB) | BOTTOM |
| Strommessung je Motor | 1 mΩ Inline-Shunt + INA240A2 | 2 | analog | BOTTOM |
| Hardware-Überstromabschaltung | LM393 + 74AUP1G74 auf `~SD` | 2 | Expander P0–P2 | BOTTOM |

Der frühere **Mini-Radar** ist durch den ToF-Sensor ersetzt (Punkt 17), das
frühere **Mini-Relais** durch den PhotoMOS (Punkt 21), der **USB-UART-Baustein**
entfällt durch den nativen USB des ESP32-S3 (Punkt 24). Was davon in Firmware
tatsächlich ausgewertet wird, steht in
[`13-funktionsstatus.md`](13-funktionsstatus.md).

RS-485 ist die **primäre** Kommunikation. WLAN am ESP32 ist sekundär/nice-to-have.

> **Die Feldperipherie ist gegenüber dem Ursprungsentwurf unvollständig.** Der
> Vorgängerentwurf führte je Laden **zwei** Kontakte (Verschluss *und* Sabotage) und
> einen externen Temperaturfühler an zwei 10-poligen Schraubklemmen. Beides fehlt hier.
> Auswertung und Belege: [`12-legacy-socos.md`](12-legacy-socos.md), Entscheidung
> offen als Punkte 34 und 35 in [`06-open-decisions.md`](06-open-decisions.md).

## 4. Board-Aufteilung

### TOP – Front / UI
Runddisplay ST77916 über QSPI, vier Sicheltasten (8 Taster), SHT4x, VL53L1X
hinter dem oberen Steg (12 Uhr), Klinkenbuchse für den Stern im unteren Steg
(6 Uhr), USB-C am Rand oben links neben dem ToF.

### MID – Logic
ESP32-S3, RS-485-Transceiver, GPIO-Expander, Piezo, PhotoMOS für den
Haubenkontakt, Feldstecker für die Verschlusskontakte.

### BOTTOM – Power & Motor
24-V-Eingangsschutz, zwei Motor-H-Bridges, Strommessung, hardwareseitige
Überstromabschaltung, DC/DC-Wandler, unterer Hochstrom-Steckverbinder.

## 5. Zentrale Designregel

Motor/24-V-Leistung unten, digitale Logik/Kommunikation in der Mitte, UI/Sensorik oben.
Hochstrom bleibt auf dem Bottom-Board. Stackverbinder transportieren nur Signale und
Kleinleistung.

## 6. Zuordnungshinweise / Prüfpunkte

Beide Punkte dieses Abschnitts sind inzwischen entschieden — sie bleiben als
Entscheidungsprotokoll stehen:

- ~~**Mini-Relais**~~ → **PhotoMOS AQY282GS auf dem Mid-Board** (Punkt 21). Potentialfrei,
  60 V / 0,8 A, kein Spulenstrom, keine Bauhöhe im Stapelspalt. **Die Freigabe gilt
  ausdrücklich nur für SELV.** Erwartet die Dunstabzugshaube 230 V, gehört das
  Schaltglied nicht in diese Dose — dann kippt die ganze Isolations- und
  Kriechstreckenbetrachtung und mit ihr die Board-Aufteilung.
- **ADC:** Die Strommessung hängt am **internen ADC des ESP32-S3** (`I_SENSE1/2` über
  `J_STK_A` 26/28). Ein externer ADC bleibt als Punkt 18 offen — er wird erst
  relevant, wenn die C++-Komponente zeigt, dass das PWM-synchrone Sampling mit dem
  internen ADC nicht ausreicht. Herleitung: [`02-motor-control.md`](02-motor-control.md),
  Grenzen: [`09-display-and-mcu.md`](09-display-and-mcu.md) Abschnitt 4.
