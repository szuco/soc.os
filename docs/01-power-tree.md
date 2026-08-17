# 01 – Power-Tree

## 1. Struktur

```
                 ┌────────────────────────────────► 24V_MOTOR ──► H-Bridge 1 + 2
                 │                                                (direkt, ungeregelt)
24V_IN ──[F1]──[TVS]──[Verpolschutz]──┬──► Buck 24 V → 5 V      ──► 5V_SYS   ≈ 3 A
                 │                    │
                 │                    ├──► Buck 24 V → 6,2 V    ──► 6V2_STAR ≈ 0,5 A
                 │                    │                             (Last real ≈ 80 mA)
                 │                    │
                 └────────────────────┘
                                      5V_SYS ──► Buck 5 V → 3,3 V ──► 3V3_SYS ≈ 1,5 A
                                                                      (ESP32 + Logik)

USB_VBUS (5 V) ──[ESD]──[ORing / Power-Mux]──► 5V_SYS
```

## 2. Rails

| Rail | Quelle | Zielgröße | Verbraucher |
|---|---|---|---|
| `24V_MOTOR` | direkt aus `24V_IN` | ≈ 8,3 A nominal (2 Motoren) | H-Bridges |
| `5V_SYS` | Buck 24 → 5 V | ≈ 3 A | 3,3-V-Buck, ggf. RS-485/Audio |
| `3V3_SYS` | Buck 5 → 3,3 V | ≈ 1,5 A | ESP32, Sensorik, Logik |
| `6V2_STAR` | Buck 24 → 6,2 V | ≈ 0,5 A | Weihnachtsstern (≈ 80 mA) |

Der Stern soll **nur im normalen 24-V-Betrieb** leuchten. Das ist durch die Topologie
automatisch erfüllt: `6V2_STAR` wird ausschließlich aus `24V_IN` erzeugt und hat keinen
Pfad zu USB-VBUS. Diese Eigenschaft beim Schaltplanentwurf nicht versehentlich aufweichen.

## 3. Strombilanz am 24-V-Eingang

> **Vollständig neu gerechnet am 17.08.2026.** Die frühere Bilanz setzte
> 4,17 A je Motor an — abgeleitet aus dem Typenschild (100 W / 24 V) — und kam
> auf ≈ 9 A. Die Messung des Ankerwiderstands ergibt **14 Ω und damit 1,7 A
> Blockierstrom je Motor**; mehr kann physikalisch nicht fließen. Die 100 W sind
> die Netzteilempfehlung der Anlage, nicht die Aufnahme eines Motors. Herleitung
> in [`11-motor-data.md`](11-motor-data.md).

Der ungünstigste Fall ist **nicht** der gleichzeitige Lauf, sondern der
gleichzeitige **Anschlag** beider Motoren — und der tritt bei jeder Fahrt auf,
weil das Gerät ohne Endschalter arbeitet:

| Pfad | Fahrt | Anschlag (Worst Case) |
|---|---:|---:|
| 2 × Motor | 0,6–2,0 A | **3,2 A** |
| 5-V-Rail 3 A bei η ≈ 0,9 | 0,69 A | 0,69 A |
| 6,2-V-Rail 80 mA | ≈ 0,02 A | ≈ 0,02 A |
| **Summe** | **≈ 1,7 A** | **≈ 4,1 A** |

Eine Anlaufspitze darüber hinaus gibt es nicht: Beim Einschalten steht der
Läufer, es fließt also genau der Blockierstrom von 1,7 A. Bei einem Motor ohne
eigene Elektronik ist der Einschaltstrom identisch mit dem Blockierstrom und
kann ihn nicht überschreiten.

> **Erledigt — der Steckverbinder ist kein Engpass mehr.**
> Dieser Abschnitt beschrieb bis zum 17.08.2026 das schwierigste Problem des
> Power-Trees: `24V_IN+` und `24V_IN−` führen die Summe beider Motoren, damals
> ≈ 9 A, und ein einzelner Micro-Fit-3.0-Kontakt trägt derated kaum mehr. Drei
> unangenehme Auswege standen zur Wahl — größeres Steckersystem, Software-
> Interlock oder ein anderes Pinout.
>
> **Alle drei sind hinfällig.** Der Summenstrom beträgt im ungünstigsten Fall
> 4,1 A, im Fahrbetrieb 1,7 A. Die Motorpins führen je 1,7 A. Micro-Fit 3.0
> trägt das auch bei voll bestücktem Gehäuse und benachbart stromführenden
> Kontakten mit deutlicher Reserve.
>
> Insbesondere ist der **Software-Interlock endgültig vom Tisch** — beide
> Motoren dürfen gleichzeitig laufen, ohne dass es den Steckverbinder
> interessiert. Das war Punkt 3 in [`06-open-decisions.md`](06-open-decisions.md)
> und dort noch als „verschärft Punkt 2" vermerkt; die Verschärfung existiert
> nicht mehr.

## 4. USB-Power-ORing

- USB-C bleibt ein **Device/UFP-Port**. `CC1` und `CC2` jeweils mit **5,1 kΩ Rd nach GND**.
  Beide Leitungen einzeln, kein gemeinsamer Widerstand.
- USB-VBUS darf `5V_SYS` beim Programmieren speisen.
- Reverse-Current-Blocking bzw. Power-Mux verhindert Rückspeisung in den PC. Ein reiner
  Schottky-Dioden-OR erfüllt das zwar, kostet aber Spannung und verheizt bei 3 A zu viel —
  praktisch geeignet ist ein Ideal-Diode-Controller oder ein Power-Mux mit definierter
  Priorität.
- **Priorität: 24 V vor USB.** Liegen beide an, versorgt der 24-V-Buck; USB wird
  zurückgeblockt. So verhält sich das System beim Programmieren mit angeschlossener
  Anlage identisch zum Normalbetrieb.
- ESD-Schutz unmittelbar an der USB-C-Buchse, `D+`/`D−` kurz führen.
- USB-C und USB-UART gehören auf dasselbe Top-Board. `D+`/`D−` werden **nicht** durch den
  Stack geführt.

> **Konsequenz für den Stack:** Wird nur über USB versorgt, ist das Bottom-Board
> stromlos — der 5-V-Buck sitzt dort. `5V_SYS` muss dann *vom Top-Board in den Stack
> hinein* gespeist werden. `J_STK_A` führt `5V_SYS` also bidirektional. Das ist beim
> ORing-Konzept und bei der Pin-Anzahl für `5V_SYS` zu berücksichtigen (siehe
> [`03-stack-pinout.md`](03-stack-pinout.md)), und es ist eine offene Entscheidung, ob
> der Power-Mux auf TOP oder BOTTOM sitzt.

## 5. Schutz und EMV

### Eingang
- Sicherung `F1` am 24-V-Eingang, träge, **6,3 A**. Sie muss die 4,1 A des
  beidseitigen Anschlags dauerhaft tragen — das ist ein normaler Betriebszustand,
  kein Fehler — und darf im Unterputzgehäuse auch bei Wärme nicht zum
  Fehlauslöser werden. 5 A wäre nach Derating zu knapp. Ein echter Kurzschluss
  liegt weit darüber und löst sicher aus.
- TVS-Diode gegen Transienten, Durchbruchspannung oberhalb 24 V +10 % plus Toleranz.
- Optionaler Verpolschutz. Ein P-FET in der Plusleitung oder ein N-FET in der
  Rückleitung bleibt die bessere Wahl; bei nur 4,1 A wäre eine Serien-Diode
  inzwischen aber vertretbar (≈ 1,6 W Verlust).
- Je Motorzweig eigene Sicherung bzw. eigenes Schutzkonzept.

### Bulk und Layout
- Bulk-Kondensatoren nahe den Motorendstufen, Größenordnung zunächst **470–1000 µF**,
  abhängig von Platz, Leitungslänge und Messergebnissen.
  → Bauhöhe beachten, siehe Tiefenbudget in [`04-mechanical.md`](04-mechanical.md).
    Klassische 1000-µF-Elkos sprengen den Stack-Abstand; mehrere niedrigbauende oder
    Polymer-Typen sind der wahrscheinlichere Weg.
- Motorstromschleifen kurz und breit halten. 2-oz-Kupfer für das Bottom-Board prüfen.
- Shunt-Sense-Leitungen als **Kelvin-Leitungen** führen.
- Power-GND und Signal-GND mit kontrolliertem Rückstrompfad verbinden. Motorströme nicht
  durch die ESP32-/Sensor-GND-Bereiche führen.
- Schaltknoten der Bucks und H-Bridges von ADC, USB, I2C, ESP32 und Antenne fernhalten.
- Konkrete Buck-Regler strikt nach **Hersteller-Referenzlayout** dimensionieren und routen.

### Antenne
ESP32-Antennenbereich kupfer- und bauteilfrei halten, Keepout auf allen Lagen.
Antenne möglichst zur Front orientieren. Realistisch bleibt die WLAN-Performance in
einer massiven Unterputzdose hinter einem Frontpanel schwach — deshalb ist RS-485 die
primäre Kommunikation und WLAN ausdrücklich sekundär.
