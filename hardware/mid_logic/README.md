# MID – Logic

KiCad-Projekt `mid_logic`. Logik- und Kommunikationsebene des Stacks.

## Umfang

- ESP32 als zentrale Steuerung
- RS-485-Transceiver als **primäre** Kommunikation, mit DE/RE-Steuerung
- Radar-Schnittstelle, voraussichtlich UART
- Audio-Treiber für Mini-Speaker/Piezo
- Ggf. zusätzlicher externer ADC für die Strommessung
- Stackverbinder `J_STK_A` und `J_STK_B` nach unten und nach oben

## Kernregeln

- **Antennen-Keepout:** ESP32-Antennenbereich kupfer- und bauteilfrei auf **allen** Lagen,
  Antenne möglichst zur Front orientiert. WLAN ist sekundär — in einer massiven
  Unterputzdose ist die Performance realistisch schwach, deshalb RS-485 als primäre
  Kommunikation.
- Keine Motorströme, keine USB-Datenleitungen auf diesem Board.
- Durchgehende GND-Referenzlage, 4 Lagen empfohlen.

## Mechanik

- Ø 55,0 mm, 1,0 mm Dicke
- Bohrbild und Stackverbinder-Positionen **deckungsgleich** mit BOTTOM und TOP
- Abstand nach unten ≈ 10 mm, nach oben ≈ 8–10 mm

Exakte Koordinaten: [`../../docs/04-mechanical.md`](../../docs/04-mechanical.md)

## Referenzdokumente

- [`docs/03-stack-pinout.md`](../../docs/03-stack-pinout.md) – Pinmapping beider Verbinder
- [`docs/00-system-overview.md`](../../docs/00-system-overview.md) – Peripherieübersicht
- [`docs/06-open-decisions.md`](../../docs/06-open-decisions.md) – ESP32-Modul, Transceiver, Radar, ADC

## Status

Noch nicht begonnen. Startet nach Phase 3 der [Roadmap](../../docs/07-roadmap.md).
