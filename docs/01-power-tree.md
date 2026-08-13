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

Worst Case bei gleichzeitigem Lauf beider Motoren, ohne Anlaufspitze:

| Pfad | Rückgerechnet auf 24 V |
|---|---|
| 2 × Motor nominal | 8,33 A |
| 5-V-Rail 3 A bei η ≈ 0,9 | 0,69 A |
| 6,2-V-Rail 80 mA | ≈ 0,02 A |
| **Summe nominal** | **≈ 9,0 A** |

> **Wichtiger Prüfpunkt — Steckverbinder-Rating.**
> Am Bottom-Connector führen die Adern `M1_A/B` und `M2_A/B` jeweils nur *einen* Motor
> (≈ 4,17 A). Die Pins `24V_IN+` und `24V_IN−` führen dagegen die **Summe beider Motoren
> plus Logik**, also ≈ 9 A nominal und im Anlauf deutlich mehr. Diese beiden Pins sind
> damit der eigentliche Engpass, nicht die Motorpins.
>
> Molex Micro-Fit 3.0 wird oft mit „bis 8,5 A“ angegeben — dieser Wert gilt für dicken
> Leiterquerschnitt und wird bei voll bestückten Gehäusen mit benachbart stromführenden
> Kontakten derated. 9 A Dauerstrom auf einem einzelnen Micro-Fit-Kontakt ist damit
> grenzwertig bis unzulässig.
>
> Drei Auswege, vor der Footprint-Wahl zu entscheiden:
> 1. **Stromstärkeres System**, z. B. Molex Mini-Fit Jr. (4,20 mm Raster, 2×3), das
>    pro Kontakt deutlich mehr Reserve bietet. Kostet Bauhöhe und Grundfläche.
> 2. **Software-Interlock**, der beide Motoren nie gleichzeitig laufen lässt. Für
>    Jalousien meist akzeptabel und halbiert den Dauerstrom auf ≈ 4,9 A. Muss dann als
>    verbindliche Firmware-Anforderung dokumentiert und im Datenblatt vermerkt werden.
> 3. Anderes Pinout mit doppelt belegten Versorgungskontakten — kollidiert mit dem in
>    [`00-system-overview.md`](00-system-overview.md) festgelegten 6-poligen Pinout und
>    ist deshalb nur die letzte Wahl.
>
> Siehe [`06-open-decisions.md`](06-open-decisions.md).

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
- Sicherung `F1` am 24-V-Eingang, träge. Startwert nach Klärung der Anlaufströme;
  Größenordnung 12–15 A bei Zweimotorbetrieb, 8–10 A bei Interlock-Variante.
- TVS-Diode gegen Transienten, Durchbruchspannung oberhalb 24 V +10 % plus Toleranz.
- Optionaler Verpolschutz. Ein P-FET in der Plusleitung oder ein N-FET in der Rückleitung
  ist gegenüber einer Serien-Diode bei 9 A klar vorzuziehen.
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
