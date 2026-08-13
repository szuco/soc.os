# KiCad SwitchStack

Dreistufiges ESP32-Steuerungsmodul für eine massive Schalter-Unterputzdose (61 mm tief).
Drei runde, gestapelte Leiterplatten à Ø 52,0 mm steuern zwei 24-V-Jalousiemotoren,
lesen Sensorik aus und kommunizieren primär über RS-485.

## Zentrale Designregel

Das System ist konsequent in drei Stör- und Leistungsdomänen getrennt:

| Ebene      | Projekt                        | Domäne                                   |
|------------|--------------------------------|------------------------------------------|
| **TOP**    | `hardware/top_ui`              | UI und Sensorik                          |
| **MID**    | `hardware/mid_logic`           | Digitale Logik und Kommunikation         |
| **BOTTOM** | `hardware/bottom_power_motor`  | 24-V-Leistung, Motoren, DC/DC            |

Hochstrom bleibt **vollständig** auf dem Bottom-Board. Die Board-to-Board-Stackverbinder
transportieren ausschließlich Signale und Kleinleistung. Diese Trennung ist für Bauraum,
EMV, Messqualität und Wartbarkeit zentral.

## Eckdaten

- Versorgung: 24 V DC über zwei Adern
- 2 × Jalousiemotor 24 V DC ±10 %, 100 W, Polarity-Reversal (≈ 4,17 A nominal je Motor)
- Herrnhuter Mini-Weihnachtsstern 6,0–6,5 V / 0,5 W / ≈ 80 mA, nur im 24-V-Normalbetrieb
- USB-C ausschließlich für Programmierung und Debug
- Positionserkennung ausschließlich über Stromverlauf und Timeout, keine Endschalter
- KiCad-Version: **9.0.7**

## Dokumentation

| Dokument | Inhalt |
|---|---|
| [`docs/00-system-overview.md`](docs/00-system-overview.md) | Gesamtsystem, Peripherie, Board-Aufteilung |
| [`docs/01-power-tree.md`](docs/01-power-tree.md) | Power-Tree, Strombilanz, USB-ORing, Schutz |
| [`docs/02-motor-control.md`](docs/02-motor-control.md) | H-Bridges, Strommessung, Überstromschutz, Software-Konzept |
| [`docs/03-stack-pinout.md`](docs/03-stack-pinout.md) | Stackverbinder, verbindliches Pinmapping |
| [`docs/04-mechanical.md`](docs/04-mechanical.md) | Outline, Bohrbild, Koordinaten, Tiefenbudget |
| [`docs/05-manufacturing.md`](docs/05-manufacturing.md) | Lagenaufbau, Kupfer, DRC, Fertigungsdaten |
| [`docs/06-open-decisions.md`](docs/06-open-decisions.md) | Offene Bauteil- und Auslegungsentscheidungen |
| [`docs/07-roadmap.md`](docs/07-roadmap.md) | Konkrete Arbeitsschritte in Reihenfolge |
| [`docs/08-kicad-workflow.md`](docs/08-kicad-workflow.md) | KiCad-Konventionen, Bedienhinweise, Repo-Regeln |
| [`docs/09-display-and-mcu.md`](docs/09-display-and-mcu.md) | Displaywahl, MCU, GPIO-Budget, ESPHome-Grenzen |
| [`docs/10-firmware-strategy.md`](docs/10-firmware-strategy.md) | Firmware-Schichten, ESPHome-Unabhängigkeit, Modbus-Pfad |
| [`hardware/bom/README.md`](hardware/bom/README.md) | Beschaffungsliste, Fertigerempfehlung, Bestellweg |

## Repository-Struktur

```
hardware/
  bottom_power_motor/   KiCad BOTTOM (24 V, Motor, DC/DC)
  mid_logic/            KiCad MID (ESP32, RS-485, Radar, Audio)
  top_ui/               KiCad TOP (USB-C, Display, Taster, Sensorik)
  lib/                  Gemeinsame Symbol-/Footprint-/3D-Bibliotheken
  bom/                  Stückliste und Fertigung
mechanical/             Frontplatte: build123d-Modell, FreeCAD-Makro, STEP/STL
tools/                  Generatoren (Board-Mechanik)
firmware/
  esphome/              ESPHome-Konfiguration für Home Assistant
docs/                   Projektübergreifende Spezifikationen
archive/                Altbestand, nicht Teil dieses Projekts
```

## Erzeugen

Die mechanischen Teile sind **generiert, nicht handgezeichnet** — damit können die drei
Boards nicht auseinanderlaufen:

```bash
python3 tools/gen_boards.py          # 3 × .kicad_pcb: Outline, Bohrbild, Keepout
python3 mechanical/frontplate.py     # Frontplatte → STEP + STL, mit Selbsttest
```

Beide Skripte prüfen ihr Ergebnis und melden Abweichungen. `gen_boards.py` braucht die
`pcbnew`-Python-API aus einer KiCad-Installation, `frontplate.py` braucht `build123d`
(`pip install build123d`).

Die **Schaltpläne** werden nativ in KiCad 9.0.7 angelegt, nicht generiert — Begründung in
[`docs/08-kicad-workflow.md`](docs/08-kicad-workflow.md).

## Status

| Teil | Stand |
|---|---|
| Systemspezifikation, Power-Tree, Pinmapping | dokumentiert |
| Mechanik der drei Boards | erzeugt und verifiziert |
| Frontplatte, druckfertig | erzeugt und verifiziert |
| ESPHome-Konfiguration | validiert (`esphome config`) |
| Schaltpläne, Layout, Routing | **offen** |
| Fertigungsdaten zum Bestellen | **offen** (setzt das Layout voraus) |

Nächste Schritte: [`docs/07-roadmap.md`](docs/07-roadmap.md).
Der kritische Pfad ist die Messung des realen Anlauf- und Blockierstroms der Motoren —
davon hängen Sicherungen, Trip-Schwellen, Treiberauswahl und Steckverbinder ab.
