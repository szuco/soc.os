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
- 2 × Klappladenmotor 24 V DC ±10 %, 2 Adern, Umpolung — Laufstrom ≈ 0,3–1,0 A, Blockierstrom offen
- Herrnhuter Mini-Weihnachtsstern 6,0–6,5 V / 0,5 W / ≈ 80 mA, nur im 24-V-Normalbetrieb
- USB-C ausschließlich für Programmierung und Debug
- Positionserkennung ausschließlich über Stromverlauf und Timeout, keine Endschalter
- KiCad-Version: **10.0.5** (migriert von 9.0.7, siehe `docs/08-kicad-workflow.md`)

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
| [`docs/11-motor-data.md`](docs/11-motor-data.md) | Motordatenblatt, Leistungsanalyse, **Messprotokoll M1–M7** |
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
tools/                  Generatoren (Board-Mechanik, Bottom-Schaltplan)
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
python3 tools/gen_bottom_sch.py      # Bottom-Schaltplan + BOM, mit Netzlistenprüfung
python3 tools/gen_mid_sch.py         # Mid-Schaltplan (ESP32, RS-485, Expander)
python3 tools/gen_top_sch.py         # Top-Schaltplan (USB-C, Taster, Sensorik)
python3 tools/gen_layouts.py         # 3 Layouts: Platzierung, Netze, Zonen, DRC
python3 mechanical/frontplate.py     # Frontplatte → STEP + STL, mit Selbsttest
```

Beide Skripte prüfen ihr Ergebnis und melden Abweichungen. `gen_boards.py` braucht die
`pcbnew`-Python-API aus einer KiCad-Installation, `frontplate.py` braucht `build123d`
(`pip install build123d`).

Auch der Bottom-Schaltplan wird erzeugt: Die Konnektivität steht als Quelltext, und
nach dem Schreiben liest `kicad-cli` die Netzliste zurück und vergleicht sie gegen
genau diese Vorgabe. Das Ergebnis ist zweckmäßig gezeichnet, aber nachweislich
korrekt — und in KiCad frei umarrangierbar.

## Status

| Teil | Stand |
|---|---|
| Systemspezifikation, Power-Tree, Pinmapping | dokumentiert |
| Mechanik der drei Boards | erzeugt und verifiziert |
| Frontplatte, druckfertig | erzeugt und verifiziert |
| ESPHome-Konfiguration inkl. ST77916-Display | validiert (`esphome config`) |
| **Bottom-Board: Schaltplan + Stückliste** | **erzeugt und netzlistengeprüft** |
| Schaltpläne Mid und Top | **erzeugt und netzlistengeprüft** |
| Layouts aller drei Boards: Platzierung + Zonen | **erzeugt, DRC ohne Platzierungsfehler** |
| **Routing TOP** | **vollständig** — alle Netze verbunden, Kupfer-DRC sauber |
| **Routing MID** | Signale vollständig; **10 PGND-Pour-Anbindungen offen** (Handgriff in KiCad, s. docs/05) |
| **Routing BOTTOM** | Leistungsteil ≈ 85 % — **Rest Handarbeit** (docs/05 verlangt das für Leistungspfade ohnehin) |
| Fertigungsdaten TOP (Gerber/Drill/Pos) | **erzeugt:** `hardware/fab/top_ui.zip` |
| Stücklisten aller drei Boards | **erzeugt** (`bom_bottom/mid/top.csv`) |
| Fertigungsdaten Mid + Bottom | nach Rest-Routing: `python3 tools/gen_fab.py` |

Nächste Schritte: [`docs/07-roadmap.md`](docs/07-roadmap.md).
Der kritische Pfad ist die Messung des Blockierstroms — Messprotokoll in
[`docs/11-motor-data.md`](docs/11-motor-data.md), Abschnitt 4. Ohne sie bleiben
Sicherungen, Trip-Schwellen, Treiberauswahl und Steckverbinder provisorisch.
