# KiCad SwitchStack

Dreistufiges ESP32-Steuerungsmodul für eine massive Schalter-Unterputzdose (61 mm tief).
Drei runde, gestapelte Leiterplatten à Ø 55,0 mm steuern zwei 24-V-Jalousiemotoren,
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

## Repository-Struktur

```
hardware/
  bottom_power_motor/   KiCad-Projekt BOTTOM (24 V, Motor, DC/DC)
  mid_logic/            KiCad-Projekt MID (ESP32, RS-485, Radar, Audio)
  top_ui/               KiCad-Projekt TOP (USB-C, OLED, Taster, Sensorik)
  lib/                  Gemeinsame Symbol-/Footprint-/3D-Bibliotheken
firmware/               ESP32-Firmware (folgt nach Hardware-Freeze)
docs/                   Projektübergreifende Spezifikationen
archive/                Altbestand, nicht Teil dieses Projekts
```

Die drei KiCad-Projekte werden **nativ in KiCad 9.0.7 angelegt**, nicht per Skript
generiert. Details und Begründung in [`docs/08-kicad-workflow.md`](docs/08-kicad-workflow.md).

## Status

Mechanische Definition und Systemspezifikation sind dokumentiert. Der Schaltungsentwurf
beginnt beim Bottom-Board. Aktueller Arbeitsstand und nächste Schritte:
[`docs/07-roadmap.md`](docs/07-roadmap.md).
