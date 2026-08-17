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
| Display | **1,69" LCD rechteckig, ST7789, 240×280, quer** | Das Fenster der Zentralscheibe (32,70 × 27,00) gibt die Form vor; die aktive Fläche 32,63 × 27,97 füllt es randlos. ESPHome-nativ. **Modulaußenmaß vor dem Layout messen** (Punkt 15c) |
| Taster | **4 ×** SMD-Kurzhubtaster, niedrig (z. B. Panasonic EVQP2 3,9×2,9 mm) | einer je Ecke, exakt unter den Druckkreuzen der Zentralscheibe bei (±18 · ±20). Bauhöhe ≤ 2,0 mm — sie steht in der Tiefenkette, siehe `docs/04` 1e |
| GPIO-Expander | **PCF8575** (16 Bit, SSOP-24) | Acht Portpins reichten mit vier Reed-Kontakten nicht mehr. Gleiche Adresse, gleicher ESPHome-Treiber (`pcf8574` mit `pcf8575: true`) |

Begründung der Displaywahl im Detail: [`../../docs/09-display-and-mcu.md`](../../docs/09-display-and-mcu.md).

### Leistung

| Funktion | Kandidat | Kernkriterium bei der Auswahl |
|---|---|---|
| Gate-Treiber ×4 | **IR2104** (Halbbrücke, `~SD`-Eingang) | zwei je Motorkanal; `~SD` ist der Eingriffspunkt des Hardware-Trips |
| Shunt ×2 | **5 mΩ**, 1 W, 4-Terminal (Kelvin), 2512 | 4-Terminal ist Pflicht. 5 statt 1 mΩ seit der Blockierstrommessung (1,7 A): ergibt mit INA240-Verstärkung 50 genau 0,25 V/A und ±6,6 A Messbereich |
| Current-Sense-Amp ×2 | **INA240A2D** | bidirektional, hoher Gleichtaktbereich, PWM-tauglich |
| Comparator + Latch ×2 | **TLV3702** (Fenster) + **74AUP1G74** | wirkt ohne Firmware. **Kein LM393** — dessen Gleichtakt-Eingangsbereich reicht bei 3,3 V nur bis 1,8 V, die obere Trip-Schwelle liegt bei 2,752 V. Pflicht sind **Rail-to-Rail-Eingang** und **Open-Drain-Ausgang** (das Wire-OR hängt daran), SOIC-8 im Standard-Pinout. Vor der Bestellung gegen das Datenblatt prüfen — siehe Punkt 57 |
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
| Bottom, 6-polig | **Micro-Fit 3.0 2×3 reicht** | Pin 1/2 führen ≈ 4,1 A Spitze, nicht die früher angenommenen 9 A. Mini-Fit Jr. ist nicht mehr nötig — siehe [`../../docs/01-power-tree.md`](../../docs/01-power-tree.md) |
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

## 6. Bestellung: Fertiger und Bestückung

**Stand 16.08.2026: bestellbar ist noch nichts.** Was zuerst erledigt sein muss,
steht in [`../../docs/13-funktionsstatus.md`](../../docs/13-funktionsstatus.md);
die harten Blocker sind der ungemessene Blockierstrom (damit der N-FET,
Punkt 8), zwei Platzhalter-Footprints (Klinke Punkt 30, Displaystiftleiste
Punkt 15c), der Stapelverbinder ohne Teilenummer (Punkt 23) und das fehlende
Routing von Mid und Bottom.

### Was der Nutzen für eine Bestückung noch braucht

Der Nutzen ist für die **Leiterplattenfertigung** ausgelegt, nicht für die
Bestückung. Drei Dinge fehlen und sind vor der PCBA-Bestellung zu ergänzen
(Punkt 52):

| fehlt | warum |
|---|---|
| **Passermarken** (Fiducials) | Der Bestücker richtet den Nutzen daran aus. Üblich sind drei global, diagonal versetzt, plus lokale Marken an feinpoligen Bauteilen — hier ESP32-Modul, PCF8575 (0,65 mm) und USB-C |
| **Breitere Ränder** | 4,0 mm reichen zum Fräsen, nicht zum Transport durch die Bestückungslinie. Üblich sind 5–10 mm an zwei gegenüberliegenden Seiten |
| **Werkzeugbohrungen** | zwei bis drei unbelegte Ø-3-mm-Löcher im Rand |

### Anbieterwahl

Für **5 Stück** und für **25 Stück** liegen beide noch im Prototypentarif —
die Losgröße ist nicht das, was die Wahl entscheidet. Entscheidend sind drei
andere Dinge:

1. **Bauteilabdeckung.** Der günstigste Tarif bei JLCPCB verlangt, dass die
   *gesamte* Stückliste aus dem LCSC-Lager kommt. Was dort fehlt, muss
   beigestellt werden — und Beistellung ist bei Kleinserien der teuerste Teil.
   **Konsequenz für die noch offene Bauteilauswahl: Wo es die Wahl gibt, ein
   LCSC-gelistetes Teil nehmen.** Die USB-C-Buchse ist mit C2843970 bereits so
   gewählt; beim N-FET (Punkt 8) ist das jetzt zu berücksichtigen.
2. **Doppelseitige Bestückung plus Durchsteckteile.** Das Mid-Board trägt
   Bauteile auf beiden Seiten (Expander und Feldstecker hinten), dazu kommen
   THT-Teile: Stapelverbinder, Leistungsstecker, Klinke. Beides zusammen
   schließt die billigsten Stufen aus.
3. **Wohin die Rechnung zeigt.** Aus der EU (AISLER, Eurocircuits) entfallen
   Zoll, Wartezeit und Einfuhrumsatzsteuer, und man bekommt brauchbares
   DFM-Feedback; aus China (JLCPCB, PCBWay) ist der reine Preis in dieser
   Stückzahl deutlich niedriger.

**Ein Mittelweg, der für dieses Projekt gut passt:** Leiterplatten und
**SMD-Bestückung** fertigen lassen, die **Durchsteckteile selbst löten**. Das
sind genau die Teile, die schwer zu beschaffen sind (Micro-Fit, Stapelverbinder,
Klinke) — und die man beim Prototyp ohnehin noch tauschen will.

