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

- Ø 52,0 mm, 1,0 mm Dicke
- Zwei Befestigungsbohrungen auf R = 21,5 mm bei 0° / 180° (Bohrbild v2, siehe docs/04)
- Bottom-Connector im Bereich −Y (unten), siehe Frontorientierung
- 2-oz-Kupfer prüfen

Exakte Koordinaten: [`../../docs/04-mechanical.md`](../../docs/04-mechanical.md)

## Referenzdokumente

- [`docs/01-power-tree.md`](../../docs/01-power-tree.md) – Power-Tree, Strombilanz, Schutz
- [`docs/02-motor-control.md`](../../docs/02-motor-control.md) – H-Bridges, Sense, Trip
- [`docs/03-stack-pinout.md`](../../docs/03-stack-pinout.md) – Stackverbinder
- [`docs/04-mechanical.md`](../../docs/04-mechanical.md) – Outline, Bohrbild, Tiefenbudget

## Dateien

| Datei | Stand |
|---|---|
| `bottom_power_motor.kicad_pcb` | Mechanik: Outline Ø 52 mm, Bohrbild, Dicke 1,0 mm |
| `bottom_power_motor.kicad_sch` | **Schaltplan, 103 Bauteile, 105 Netze** |
| `bom_bottom.csv` | Stückliste, aus derselben Quelle erzeugt |

Beides wird generiert, nicht von Hand gezeichnet:

```bash
python3 tools/gen_boards.py       # Mechanik
python3 tools/gen_bottom_sch.py   # Schaltplan + Stückliste + Netzlistenprüfung
```

## Status

**Schaltplan steht und ist netzlistengeprüft.** `tools/gen_bottom_sch.py` exportiert
nach dem Erzeugen die Netzliste mit `kicad-cli` und vergleicht sie gegen die im
Quelltext hinterlegte Soll-Konnektivität — 105 Netze, keine Abweichung, kein offener
Pin.

Enthalten: 24-V-Eingangsschutz (Sicherung, TVS, P-FET-Verpolschutz), 12-V-Gate-
Versorgung, drei DC/DC-Wandler, USB-ORing, Stern-Ausgang mit Polyfuse, zwei
vollständige H-Brücken aus je 2× IR2104 und 4 N-FETs, Inline-Strommessung mit
INA240A2, Fensterkomparator und Latch je Kanal, beide Stackverbinder.

**Was der Schaltplan noch nicht ist:**

- **Nicht geprüft im Sinne einer Schaltungsreview.** Werte sind gerechnet, aber die
  Regler sind noch nicht gegen die Hersteller-Referenzlayouts abgeglichen.
- **Pinbelegungen der ICs gegen die Datenblätter prüfen** — insbesondere INA240A2D,
  dessen KiCad-Symbol zwei GND-Pins gestapelt führt.
- **Die Darstellung ist zweckmäßig, nicht schön.** Jedes Bauteil hängt über kurze
  Stummel an globalen Labels. Das ist netzlistenidentisch mit einem gezeichneten Plan
  und lässt sich in KiCad frei umarrangieren, ohne die Verbindungen zu verlieren.
- **Kein Layout.** Das ist der nächste Schritt.

Offene Bauteilposition: der N-Kanal-MOSFET (Punkt 8 in
[`docs/06`](../../docs/06-open-decisions.md)) — er hängt am noch nicht gemessenen
Blockierstrom.
