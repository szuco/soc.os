# BOTTOM – Power & Motor

KiCad-Projekt `bottom_power_motor`. Leistungsebene des Stacks.

## Umfang

- 24-V-Eingangsschutz: Sicherung, TVS, optionaler Verpolschutz
- Hochstrom-Steckverbinder nach unten, 6-polig
- Zwei Motor-H-Bridges für die Jalousiemotoren
- Strommessung getrennt pro Motor
- Hardwareseitige Überstromabschaltung, Comparator + Latch **pro Motor**
- DC/DC-Wandler: 24 → 5 V, 5 → 3,3 V, 24 → 6,2 V
- Mini-Relais (Zuordnung noch zu bestätigen)
- Stackverbinder `J_STK_A` und `J_STK_B` nach oben

## Kernregel

**Hochstrom bleibt vollständig auf diesem Board.** Motorströme werden niemals über die
Stackverbinder geführt.

## Mechanik

- Ø 55,0 mm, 1,0 mm Dicke
- Drei Befestigungsbohrungen auf R = 23 mm bei 0° / 120° / 240°
- Bottom-Connector im Bereich −Y (unten), siehe Frontorientierung
- 2-oz-Kupfer prüfen

Exakte Koordinaten: [`../../docs/04-mechanical.md`](../../docs/04-mechanical.md)

## Referenzdokumente

- [`docs/01-power-tree.md`](../../docs/01-power-tree.md) – Power-Tree, Strombilanz, Schutz
- [`docs/02-motor-control.md`](../../docs/02-motor-control.md) – H-Bridges, Sense, Trip
- [`docs/03-stack-pinout.md`](../../docs/03-stack-pinout.md) – Stackverbinder
- [`docs/04-mechanical.md`](../../docs/04-mechanical.md) – Outline, Bohrbild, Tiefenbudget

## Status

Board-Outline (Kreis auf `Edge.Cuts`, R = 27,5 mm) und Board-Dicke 1,0 mm sind in KiCad
angelegt. Das KiCad-Projekt liegt noch nicht im Repository — es wird nativ in
KiCad 9.0.7 in dieses Verzeichnis erzeugt, siehe
[`docs/08-kicad-workflow.md`](../../docs/08-kicad-workflow.md).
