# Stückliste und Fertigung

> **Status ehrlich benannt:** Dies ist eine **Auswahl- und Beschaffungsliste**, keine
> fertigungsfähige BOM. Eine bestellbare BOM entsteht erst aus dem fertigen Schaltplan
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
| Display | **1,43" AMOLED rund, CO5300, 466×466, QSPI** | ESPHome-nativ (`mipi_spi`), echtes Schwarz, Helligkeit per Kommando. **Auflage:** Radar-Dunkeltastung gegen Einbrennen ist Pflicht — Details und Alternativen in `docs/09` |
| Taster | **8 ×** SMD-Kurzhubtaster, niedrig (z. B. Panasonic EVQP2 3,9×2,9 mm) | je Sicheltaste zwei, elektrisch parallel; Positionen r = 23,3 mm, siehe `docs/09` |
| GPIO-Expander | **TCA9534** oder **PCF8574** | entlastet das knappe GPIO-Budget, ESPHome-nativ |

Begründung der Displaywahl im Detail: [`../../docs/09-display-and-mcu.md`](../../docs/09-display-and-mcu.md).

### Leistung

| Funktion | Kandidat | Kernkriterium bei der Auswahl |
|---|---|---|
| Motortreiber ×2 | integrierte Vollbrücke mit **PWM/DIR-Interface**, ≥ 5 A Dauer, ≥ 15 A Peak, 24 V+ | **Thermik im geschlossenen Gehäuse ohne Luftstrom** — das ist die eigentliche Hürde, nicht der Nennstrom |
| Shunt ×2 | 10 mΩ, ≥ 2 W, 4-Terminal (Kelvin) | 4-Terminal ist Pflicht, nicht optional |
| Current-Sense-Amp ×2 | bidirektional, für Inline-Messung geeignet | siehe Sense-Topologie unten |
| Comparator + Latch ×2 | Comparator mit Referenz + SR-Latch | **muss ohne Firmware wirken** |
| Buck 24→5 V | ≥ 3 A, synchron | strikt nach Referenzlayout |
| Buck 5→3,3 V | ≥ 1,5 A | |
| Buck 24→6,2 V | ≥ 0,5 A, einstellbar | für den Weihnachtsstern |
| Power-Mux USB/24 V | Ideal-Diode-Controller | Priorität 24 V vor USB, kein Rückstrom in den PC |

> Ich nenne hier bewusst **keine konkreten Hersteller-Teilenummern für die
> Leistungspfade**. Die Auswahl hängt am realen Anlauf- und Blockierstrom der Motoren
> ([`../../docs/06-open-decisions.md`](../../docs/06-open-decisions.md), Punkt 1), und
> der ist nicht gemessen. Ein Treiber, der für 4,17 A nominal passt, kann bei einem
> Blockierstrom von 25 A sofort sterben. Diese Messung ist der Türöffner für den
> gesamten Leistungsteil.

### Sensorik und Kommunikation

| Funktion | Empfehlung | Warum |
|---|---|---|
| Temperatur + Feuchte | **SHT4x** (SHT40/41/45), I2C | ein Baustein für beides, spart Platz und eine I2C-Adresse; ESPHome `sht4x` |
| RS-485 | Transceiver mit **Fail-Safe-Bias**, 3,3 V | ohne Fail-Safe klappert der Bus im Leerlauf |
| Radar | UART-Modul, 3,3-V-Logik | Pegel und Stromaufnahme vor der Auswahl prüfen |
| Piezo | passiver Signalgeber | passiv, nicht aktiv — nur so funktioniert ESPHome `rtttl` |

### Steckverbinder

| Position | Kandidat | Prüfpunkt |
|---|---|---|
| Bottom, 6-polig | **Mini-Fit Jr. 2×3** statt Micro-Fit 3.0 | Pin 1/2 führen ≈ 9 A — siehe [`../../docs/01-power-tree.md`](../../docs/01-power-tree.md) |
| Stern-Ausgang | JST-PH 2-polig | 80 mA, unkritisch |
| Stack ×2 | 2×20, 1,27 mm | **≈ 1 A pro Kontakt** — `5V_SYS` braucht mehrere Pins |

## 2. Leiterplatten

| | BOTTOM | MID | TOP |
|---|---|---|---|
| Durchmesser | Ø 52,0 mm | Ø 52,0 mm | Ø 52,0 mm |
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
