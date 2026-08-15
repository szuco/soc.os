# Stückliste und Fertigung

> **Für das Bottom-Board gibt es jetzt eine erzeugte Stückliste:**
> [`../bottom_power_motor/bom_bottom.csv`](../bottom_power_motor/bom_bottom.csv) —
> 103 Bauteile, 52 Positionen, aus derselben Quelle wie der Schaltplan erzeugt und
> damit garantiert konsistent. Was dort noch fehlt, sind Hersteller-Teilenummern für
> die Leistungsbauteile.
>
> **Status ehrlich benannt:** Der Rest hier ist eine **Auswahl- und Beschaffungsliste**,
> keine fertigungsfähige BOM. Eine bestellbare BOM entsteht erst aus dem fertigen Schaltplan
> — Referenzbezeichner (`R1`, `U3`, …), Werte und Footprints kommen aus KiCad. Ohne
> Layout gibt es auch keine Positionsdatei (CPL) und keine Gerber. Was noch fehlt,
> steht unten unter „Weg zur Bestellung".

Alle Teile sind Empfehlungen mit Begründung. Preise und Lagerbestand sind bei der
Bestellung zu prüfen — beides ändert sich laufend.

## 1. Kernkomponenten

### MCU und Anzeige

| Funktion | Empfehlung | Warum |
|---|---|---|
| MCU | **ESP32-S3-WROOM-1-N16R8** | PSRAM für den Framebuffer (466² × 16 bit ≈ 434 kB), **nativer USB** spart den USB-UART-Baustein, 16 MB Flash für OTA |
| Display | **1,46" LCD rund, ST77916, 360×360, QSPI** | entschieden. Kein Einbrennen, kein Treiberaufwand — ESPHome `mipi_spi` mit `model: CUSTOM` und der Hersteller-Init-Sequenz. **Modul-Außendurchmesser vor dem Layout messen** |
| Taster | **4 ×** SMD-Kurzhubtaster, niedrig (z. B. Panasonic EVQP2 3,9×2,9 mm) | einer je Ecke, exakt unter den Druckkreuzen der Zentralscheibe bei (±18 · ±20). Bauhöhe ≤ 2,0 mm — sie steht in der Tiefenkette, siehe `docs/04` 1e |
| GPIO-Expander | **TCA9534** oder **PCF8574** | entlastet das knappe GPIO-Budget, ESPHome-nativ |

Begründung der Displaywahl im Detail: [`../../docs/09-display-and-mcu.md`](../../docs/09-display-and-mcu.md).

### Leistung

| Funktion | Kandidat | Kernkriterium bei der Auswahl |
|---|---|---|
| Gate-Treiber ×4 | **IR2104** (Halbbrücke, `~SD`-Eingang) | zwei je Motorkanal; `~SD` ist der Eingriffspunkt des Hardware-Trips |
| Shunt ×2 | **1 mΩ**, 1 W, 4-Terminal (Kelvin), 2512 | 4-Terminal ist Pflicht; Wert folgt aus INA240-Verstärkung 50 |
| Current-Sense-Amp ×2 | **INA240A2D** | bidirektional, hoher Gleichtaktbereich, PWM-tauglich |
| Comparator + Latch ×2 | **LM393** (Fenster) + **74AUP1G74** | wirkt ohne Firmware |
| Buck 24→5 V | **TPS54360DDA** | strikt nach Referenzlayout aufbauen |
| Buck 5→3,3 V | **TLV62569DBV** | |
| Buck 24→6,2 V | **TPS54360DDA** (gleiches Teil wie oben) | für den Weihnachtsstern |
| USB-ORing | 2× Schottky (D4/D5) | einfach, kein Rückstrom; bei hoher 5-V-Last durch Ideal-Diode ersetzen |

> **Einzige offene Leistungsposition: der N-Kanal-MOSFET** (8 Stück). Er bestimmt,
> welchen Blockierstrom die Endstufe übersteht, und genau der ist nicht gemessen.
> Vorgabe bis dahin: 40 V, ≥ 60 A Puls, PowerPAK SO-8, Rds(on) < 5 mΩ. Die diskrete
> Topologie wurde bewusst gewählt, damit diese eine Entscheidung nachträglich
> änderbar bleibt.

### Sensorik und Kommunikation

| Funktion | Empfehlung | Warum |
|---|---|---|
| Temperatur + Feuchte | **SHT4x** (SHT40/41/45), I2C | ein Baustein für beides, spart Platz und eine I2C-Adresse; ESPHome `sht4x` |
| RS-485 | Transceiver mit **Fail-Safe-Bias**, 3,3 V | ohne Fail-Safe klappert der Bus im Leerlauf |
| Präsenz | **VL53L1X** (ToF), I2C + INT | ersetzt den früheren Radar — 4,9 × 2,5 mm passen hinter den Steg, ein 20-mm-Radarmodul nicht |
| Piezo | passiver Signalgeber | passiv, nicht aktiv — nur so funktioniert ESPHome `rtttl` |

### Steckverbinder

| Position | Kandidat | Prüfpunkt |
|---|---|---|
| Bottom, 6-polig | **Mini-Fit Jr. 2×3** statt Micro-Fit 3.0 | Pin 1/2 führen ≈ 9 A — siehe [`../../docs/01-power-tree.md`](../../docs/01-power-tree.md) |
| Stern-Ausgang | **2,5-mm-Klinkenbuchse** an der Front | 80 mA, unkritisch; Bauhöhe max. 10,5 mm, Footprint noch Platzhalter (Punkt 30) |
| Stack ×2 | 2×20, 1,27 mm | **≈ 1 A pro Kontakt** — `5V_SYS` braucht mehrere Pins |

## 2. Leiterplatten

| | BOTTOM | MID | TOP |
|---|---|---|---|
| Umriss | Ø 52,0 mm | Ø 52,0 mm | **47 × 47 mm, R 4** |
| Dicke | 1,0 mm | 1,0 mm | 1,0 mm |
| Lagen | 2 oder 4 | 4 | 2 |
| Kupfer | **2 oz prüfen** | 1 oz | 1 oz |
| Oberfläche | ENIG empfohlen | ENIG | ENIG |

ENIG statt HASL, weil die 1,27-mm-Stackverbinder und das ESP32-Modul feine Raster
haben und HASL dort ungleichmäßig aufträgt.

## 3. Weg zur Bestellung

Was noch fehlt, in der Reihenfolge, in der es entsteht:

1. **Schaltplan je Board** — liefert Referenzbezeichner und Werte.
2. **Bauteilauswahl abschließen** — setzt die Motorstrommessung voraus.
3. **Layout und Routing** — liefert die Positionsdatei.
4. **DRC und Stromtragfähigkeit prüfen** — siehe [`../../docs/05-manufacturing.md`](../../docs/05-manufacturing.md).
5. **Export** aus KiCad:
   ```
   kicad-cli pcb export gerbers  -o production/gerber <board>.kicad_pcb
   kicad-cli pcb export drill    -o production/gerber <board>.kicad_pcb
   kicad-cli pcb export pos      -o production/cpl.csv --format csv --units mm <board>.kicad_pcb
   kicad-cli sch export bom      -o production/bom.csv <board>.kicad_sch
   ```
6. **BOM auf das Format des Fertigers mappen** — bei JLCPCB sind die Spalten
   `Comment`, `Designator`, `Footprint`, `LCSC Part #`.

### Fertigerempfehlung

| Anbieter | Wofür | Anmerkung |
|---|---|---|
| **JLCPCB** | Prototyp mit Bestückung | günstigste Bestückung, aber Teile müssen aus dem LCSC-Katalog kommen; runde Boards und 1,0 mm sind Standard |
| **Aisler** | EU, kleine Serie | Versand aus DE/NL, keine Zollthemen, teurer |
| **PCBWay** | Sonderwünsche | 2 oz, ungewöhnliche Stackups, mehr Handarbeit möglich |

Für dieses Projekt: **Bottom-Board bei einem Anbieter mit 2-oz-Option**, Mid und Top
unkritisch. Die Bestückung der Leistungsbauteile von Hand nachzuarbeiten ist bei
Prototypen oft günstiger, als sie durch den Bestückungsservice zu treiben.

> Bei JLCPCB-Bestückung: die Bauteilauswahl wird faktisch vom LCSC-Katalog
> vorgegeben. Wer dort bestücken lassen will, sollte die Verfügbarkeit **vor** dem
> Schaltplan prüfen, nicht danach — sonst wird das halbe Design nochmal angefasst.
