# TOP – Front / UI

KiCad-Projekt `top_ui`. Bedien- und Sensorikebene des Stacks, zur Front orientiert.

## Umfang

- USB-C-Buchse, ausschließlich für Programmierung und Debug
- USB-UART-Baustein, **möglichst direkt neben der USB-C-Buchse**
- OLED-Display
- Vier Switch-/Bedientaster
- Temperatur- und Feuchtigkeitssensor
- Zweipoliger Stern-Ausgang, JST-PH als Ausgangspunkt
- Stackverbinder `J_STK_A` und `J_STK_B` nach unten

## Kernregeln

- **USB `D+`/`D−` bleiben auf diesem Board.** Sie werden nicht durch den Stack geführt.
  Deshalb gehören USB-C und USB-UART zwingend zusammen hierher.
- ESD-Schutz unmittelbar an der USB-C-Buchse, `D+`/`D−` kurz führen.
- USB-C bleibt **Device/UFP**: `CC1` und `CC2` jeweils einzeln mit 5,1 kΩ Rd nach GND.
- Der Stern-Ausgang wird aus `6V2_STAR` über den Stack versorgt und leuchtet damit nur im
  24-V-Normalbetrieb — **nicht** aus USB-VBUS speisen.

## Mechanik

- Ø 55,0 mm, 1,0 mm Dicke
- Bohrbild und Stackverbinder-Positionen **deckungsgleich** mit BOTTOM und MID
- USB-C, OLED, Taster und Stern-Stecker müssen zur Frontpanel-Geometrie passen —
  diese ist noch offen
- Frontorientierung: mathematisch +Y = „oben“, identisch auf allen drei Boards

Exakte Koordinaten: [`../../docs/04-mechanical.md`](../../docs/04-mechanical.md)

## Referenzdokumente

- [`docs/01-power-tree.md`](../../docs/01-power-tree.md) – USB-ORing, Stern-Versorgung
- [`docs/03-stack-pinout.md`](../../docs/03-stack-pinout.md) – Pinmapping
- [`docs/04-mechanical.md`](../../docs/04-mechanical.md) – Stern-Ausgang, Tiefenbudget

## Status

Noch nicht begonnen. Startet nach Phase 4 der [Roadmap](../../docs/07-roadmap.md).
