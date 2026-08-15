# TOP – Front / UI

KiCad-Projekt `top_ui`. Bedien- und Sensorikebene des Stacks, zur Front orientiert.

## Umfang

Bestückt sind 29 Bauteile, 53 Netze (`bom_top.csv`):

- **USB-C-Buchse** (16-polig, nur USB 2.0), ausschließlich für Programmierung und
  Debug, mit **USBLC6-2SC6** als ESD-Schutz und 2 × 5k1 Rd
- **Runddisplay ST77916**, 1,46", 360 × 360, QSPI — über eine Steckerleiste;
  der Footprint ist ein **Platzhalter**, bis das reale Modul mit seinem FPC
  vermessen ist
- **Acht SMD-Taster** auf r = 23,2 mm, je zwei elektrisch parallel: vier
  Sicheltasten bei vier GPIOs, kein Verkippen am Bogenende
- **SHT40-AD1B** (0x44) für Temperatur und Feuchte, thermisch über Schlitze
  entkoppelt
- **VL53L1X** als Präsenz- und Durchstiegssensor hinter dem **oberen** Steg
  (12 Uhr), XSHUT über 10k dauerhaft aktiv
- **Stern-Ausgang** über P-FET-High-Side und 0,2-A-PTC auf eine
  2,5-mm-Klinkenbuchse im **unteren** Steg (6 Uhr, Footprint noch Platzhalter,
  Punkt 30)
- `J7` als **unbestückte Reserve-UART** für ein späteres Satellitenmodul
- Stackverbinder `J_STK_A` und `J_STK_B` nach unten

Ein USB-UART-Baustein entfällt — der ESP32-S3 hat nativen USB (Punkt 24).

## Kernregeln

- **USB `D+`/`D−` laufen durch den Stack** (`J_STK_A` 34/36, benachbart, PGND
  daneben). Das ist die Regeländerung v0.3 in
  [`docs/03-stack-pinout.md`](../../docs/03-stack-pinout.md): Mit dem nativen USB
  des ESP32-S3 auf dem **Mid**-Board gibt es keine Alternative, und Full-Speed-USB
  über zwei benachbarte Kontakte ist unkritisch.
- ESD-Schutz unmittelbar an der USB-C-Buchse, `D+`/`D−` kurz führen.
- USB-C bleibt **Device/UFP**: `CC1` und `CC2` jeweils einzeln mit 5,1 kΩ Rd nach GND.
- Der Stern-Ausgang wird aus `6V2_STAR` über den Stack versorgt und leuchtet damit nur im
  24-V-Normalbetrieb — **nicht** aus USB-VBUS speisen.

## Mechanik

- Ø 52,0 mm, 1,0 mm Dicke
- Bohrbild und Stackverbinder-Positionen **deckungsgleich** mit BOTTOM und MID
- USB-C, Displaymodul, Taster, Klinkenbuchse und das ToF-Fenster müssen zur
  Frontplatte passen — Geometrie aus `mechanical/frontplate.py`, Maßprüfung am
  realen Teil steht aus (Punkte 15c, 25)
- Frontorientierung: mathematisch +Y = „oben“, identisch auf allen drei Boards

Exakte Koordinaten: [`../../docs/04-mechanical.md`](../../docs/04-mechanical.md)

## Referenzdokumente

- [`docs/01-power-tree.md`](../../docs/01-power-tree.md) – USB-ORing, Stern-Versorgung
- [`docs/03-stack-pinout.md`](../../docs/03-stack-pinout.md) – Pinmapping
- [`docs/04-mechanical.md`](../../docs/04-mechanical.md) – Stern-Ausgang, Tiefenbudget
- [`docs/09-display-and-mcu.md`](../../docs/09-display-and-mcu.md) – Displaywahl, Sicheltasten, ToF
- [`docs/13-funktionsstatus.md`](../../docs/13-funktionsstatus.md) – Gesamtstand

## Status

Schaltplan erzeugt und netzlistengeprüft (`tools/gen_top_sch.py`, 29 Bauteile,
53 Netze).

**Layout: platziert, ohne Leiterbahnen.** Stand vom 15.08.2026, an diesem Tag
zweimal neu erzeugt:

1. **J1 stand um 180° verdreht** (Punkt 39) — die Stecköffnung zeigte zur
   Platinenmitte, die Lötpads standen über die Kante, sechs Bohrungen schnitten
   die Ø-52-Kontur an. Korrigiert: das engste Pad liegt jetzt 3,2 mm innerhalb
   der Kontur, die Randabstandsverletzungen sind von 11 auf 1 gefallen.
2. **Klinke und ToF getauscht**: Die Klinkenbuchse sitzt jetzt im **unteren**
   Steg (6 Uhr, mittig), der ToF allein im **oberen** (12 Uhr). Die USB-C-Buchse
   musste dafür von 6 nach 12 Uhr weichen und liegt links neben dem ToF; der
   unbestückte Reserve-UART J7 ist nach innen gerückt.

Die verbliebene Randabstandsverletzung gehört dem **Platzhalter**-Footprint der
Klinkenbuchse: Der 3,5-mm-Typ ist 14,4 mm lang, sein Bund sitzt in der Mitte —
bei einem Lochabstand von r = 22,5 steht das hintere Ende 3,3 mm über die
Platinenkante. Das reale 2,5-mm-Teil muss deutlich kleiner sein, siehe Punkt 30.

**Zwei Footprints sind Platzhalter** und vor der Bestellung zu ersetzen:
die Displaystiftleiste (Punkt 15c) und die Klinkenbuchse (Punkt 30, 3,5 mm
vertikal statt der gewollten 2,5 mm). Beides sind reale Bauteilmaße, die am
gekauften Teil zu nehmen sind — nicht aus einem Katalog.

**Nicht geprüft:** Schaltungsreview gegen Datenblätter.
