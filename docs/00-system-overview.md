# 00 – Systemübersicht

## 1. Zielsystem

Stackbares PCB-System aus drei runden Leiterplatten, das in eine massive
Schalter-Unterputzdose mit 61 mm Tiefe passt.

- Zielgröße je PCB: **Ø 52,0 mm**
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
während der Programmierung genutzt. Der Stern erhält einen **separaten zweipoligen
Frontanschluss** und hängt nicht am USB-Port.

## 3. Geplante Peripherie

| Funktion | Anzahl | Schnittstelle | Board |
|---|---|---|---|
| Temperaturfühler | 1 | I2C (vorauss.) | TOP |
| Feuchtigkeitssensor | 1 | I2C (vorauss.) | TOP |
| OLED-Display | 1 | I2C oder SPI | TOP |
| Switch-/Bedientaster | 4 | GPIO | TOP |
| Stern-Ausgang 6,2 V | 1 | 2-polig | TOP (Front) |
| USB-C + USB-UART | 1 | — | TOP |
| ESP32 | 1 | — | MID |
| RS-485-Anschluss | 1 | UART + DE/RE | MID |
| Mini-Radar Bewegungsmelder | 1 | UART (vorauss.) | MID |
| Mini-Speaker / Piezo | 1 | PWM + Treiber | MID |
| Motorendstufe / H-Bridge | 2 | PWM/DIR/EN/FAULT | BOTTOM |
| Strommessung je Motor | 2 | analog | BOTTOM |
| Mini-Relais | 1 | GPIO | BOTTOM (siehe unten) |

RS-485 ist die **primäre** Kommunikation. WLAN am ESP32 ist sekundär/nice-to-have.

## 4. Board-Aufteilung

### TOP – Front / UI
USB-C, USB-UART möglichst direkt neben der USB-C-Buchse, OLED, vier Taster,
Temperatur- und Feuchtigkeitssensor, zweipoliger Stern-Ausgang.

### MID – Logic
ESP32, RS-485-Transceiver, Radar-Schnittstelle, Audio-Treiber und ggf. zusätzlicher ADC.

### BOTTOM – Power & Motor
24-V-Eingangsschutz, zwei Motor-H-Bridges, Strommessung, hardwareseitige
Überstromabschaltung, DC/DC-Wandler, unterer Hochstrom-Steckverbinder.

## 5. Zentrale Designregel

Motor/24-V-Leistung unten, digitale Logik/Kommunikation in der Mitte, UI/Sensorik oben.
Hochstrom bleibt auf dem Bottom-Board. Stackverbinder transportieren nur Signale und
Kleinleistung.

## 6. Zuordnungshinweise / Prüfpunkte

Zwei Dinge sind in der Ausgangsspezifikation nicht eindeutig festgelegt und beim
Schaltplanentwurf zu entscheiden:

- **Mini-Relais:** „Unterbrechen bzw. Verbinden einer Leitung“ — welche Spannung und
  welcher Strom geschaltet werden, ist offen. Die Zuordnung zum Bottom-Board ist die
  naheliegende Annahme, weil es zur Leistungsdomäne gehört; die Ansteuerung `RELAY_CTL`
  kommt dann über `J_STK_A` vom ESP32. Sobald die zu schaltende Last feststeht, ist die
  Board-Zuordnung zu bestätigen. Bei Netzspannung wäre eine komplett andere Isolations-
  und Kriechstreckenbetrachtung nötig — das würde die Board-Aufteilung verändern.
- **ADC:** Ob die Strommessung direkt am ESP32-ADC oder an einem externen ADC hängt,
  entscheidet über Signale und Pinbelegung von `J_STK_A`. Empfehlung in
  [`02-motor-control.md`](02-motor-control.md).
