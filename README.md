# KiCad SwitchStack

Dreistufiges ESP32-Steuerungsmodul für eine massive Schalter-Unterputzdose (61 mm tief).
Drei gestapelte Leiterplatten steuern zwei 24-V-Jalousiemotoren, lesen Sensorik aus und
kommunizieren primär über RS-485. **Bottom und Mid sind rund (Ø 52 mm) und sitzen in der
Dose; Top ist quadratisch (47 × 47 mm) und sitzt davor** — hinter der Busch-Jaeger
Zentralscheibe 6435-914, deren Drucktasten in den Ecken liegen.

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
| [`docs/12-legacy-socos.md`](docs/12-legacy-socos.md) | Vorgängerprojekt SoC OS: übernommene Anforderungen, verlorene Funktionen, Restriktionen |
| [`docs/13-funktionsstatus.md`](docs/13-funktionsstatus.md) | **Was steht, was fehlt** — Hardware, Firmware und Mechanik nebeneinander |
| [`hardware/bom/README.md`](hardware/bom/README.md) | Beschaffungsliste, Fertigerempfehlung, Bestellweg |

## Repository-Struktur

```
hardware/
  bottom_power_motor/   KiCad BOTTOM (24 V, Motor, DC/DC)
  mid_logic/            KiCad MID (ESP32-S3, RS-485, Expander, PhotoMOS, Piezo)
  top_ui/               KiCad TOP (USB-C, Display 1,69", 4 Ecktaster, SHT4x, ToF, Stern)
  lib/                  Gemeinsame Symbol-/Footprint-/3D-Bibliotheken
  bom/                  Beschaffung und Fertigerempfehlung
  fab/                  Erzeugte Fertigungsdaten und der Nutzen (Build-Ergebnis)
mechanical/             Adapter zur BJ-Zentralscheibe: build123d-Modell, STEP/STL
tools/                  Generatoren (Mechanik, Schaltpläne, Layouts, Routing, Fertigung)
firmware/
  esphome/              ESPHome-Konfiguration für Home Assistant
docs/                   Projektübergreifende Spezifikationen
```

Ein Verzeichnis `archive/` mit dem Altbestand der Vorgängerprojekte gab es bis zum
15.08.2026. Es ist ausgewertet und entfernt; das Ergebnis steht in
[`docs/12-legacy-socos.md`](docs/12-legacy-socos.md), die Dateien selbst liegen nur
noch in der Git-Historie.

## Erzeugen

Die mechanischen Teile sind **generiert, nicht handgezeichnet** — damit können die drei
Boards nicht auseinanderlaufen:

```bash
python3 tools/gen_boards.py          # 3 × .kicad_pcb: Outline, Bohrbild, Keepout
python3 tools/gen_bottom_sch.py      # Bottom-Schaltplan + BOM, mit Netzlistenprüfung
python3 tools/gen_mid_sch.py         # Mid-Schaltplan (ESP32, RS-485, Expander)
python3 tools/gen_top_sch.py         # Top-Schaltplan (USB-C, Taster, Sensorik)
python3 tools/gen_layouts.py         # 3 Layouts: Platzierung, Netze, Zonen, DRC
python3 tools/route_boards.py        # Freerouting-Pipeline (Container, s. docs/05)
python3 tools/gen_fab.py [board]     # Gerber/Drill/Pos + BOMs, nur nach DRC-Gate
python3 tools/gen_panel.py           # Fertigungsnutzen aus den drei Quellprojekten
python3 mechanical/adapter.py        # Adapter für die BJ-Zentralscheibe, mit Selbsttest
```

Jedes dieser Skripte prüft sein Ergebnis und meldet Abweichungen. `gen_boards.py`,
`gen_layouts.py`, `gen_fab.py` und `gen_panel.py` brauchen die `pcbnew`-Python-API aus
einer KiCad-Installation, `adapter.py` braucht `build123d` (`pip install build123d`),
`route_boards.py` einen Container (siehe `docs/05`).

Dazu zwei Werkzeuge ohne Hardware: `python3 tools/display_mock.py` zeichnet den
Displayinhalt als PNG, und `esphome compile firmware/esphome/switchstack.yaml`
übersetzt die Firmware vollständig.

Auch der Bottom-Schaltplan wird erzeugt: Die Konnektivität steht als Quelltext, und
nach dem Schreiben liest `kicad-cli` die Netzliste zurück und vergleicht sie gegen
genau diese Vorgabe. Das Ergebnis ist zweckmäßig gezeichnet, aber nachweislich
korrekt — und in KiCad frei umarrangierbar.

## Status

Vollständige Gegenüberstellung von umgesetzten und fehlenden Funktionen:
[`docs/13-funktionsstatus.md`](docs/13-funktionsstatus.md).

| Teil | Stand |
|---|---|
| Systemspezifikation, Power-Tree, Pinmapping | dokumentiert |
| Mechanik der drei Boards | erzeugt und verifiziert |
| Front | **Serienteil**: BJ-Zentralscheibe 6435-914 im Rahmen 1721-914. Der **Adapter** dazwischen ist erzeugt und selbstgeprüft (`mechanical/adapter.py`) |
| Schaltpläne aller drei Boards + Stücklisten | **erzeugt und netzlistengeprüft** — Schaltungsreview gegen Datenblätter steht aus |
| Layouts aller drei Boards: Platzierung + Zonen | **erzeugt, DRC ohne Platzierungsfehler** |
| **Routing BOTTOM** | 985 Segmente, 102 Vias, **43 Verbindungen offen** — Rest Handarbeit (docs/05 verlangt das für Leistungspfade ohnehin) |
| **Routing MID** | **746 Segmente, 104 Vias** (16.08.2026, Container). Offen: 18 Signalverbindungen und **ein Kurzschluss** `HOOD_B`/`RELAY_LED` an einer Stelle — Handarbeit, s. docs/05 |
| **Routing TOP** | **197 Segmente, 12 Vias** (16.08.2026, Container). Offen: 14 Signale, darunter **alle vier Tastenleitungen und drei USB-Netze**; dazu **eine neue Kollision** einer Leiterbahn mit dem Befestigungsloch der USB-Buchse |
| Fertigungsnutzen (3 Platinen in einer Boarddatei) | **erzeugt:** `hardware/fab/panel/` — 173,4 × 64,4 mm, zwei Kreise + ein Quadrat |
| Fertigungsdaten | **keine** — `python3 tools/gen_fab.py` nach dem Routing, mit DRC-Gate |
| ESPHome-Firmware | **übersetzt** (`esphome compile`, 2026.7.4 / IDF 5.5.5): RAM 35 %, Flash 56 %. Alle Lambdas geprüft. Motoren fahren **auf Zeit** |
| Lasterkennung, ToF-Distanz, RS-485-Protokoll | **fehlen** — die ersten beiden brauchen eine eigene C++-Komponente, s. docs/13 |
| Gefertigt oder gemessen | **nichts** |

Nächste Schritte: [`docs/07-roadmap.md`](docs/07-roadmap.md).
Der kritische Pfad ist die Messung des Blockierstroms — Messprotokoll in
[`docs/11-motor-data.md`](docs/11-motor-data.md), Abschnitt 4. Ohne sie bleiben
Sicherungen, Trip-Schwellen, Treiberauswahl und Steckverbinder provisorisch.
