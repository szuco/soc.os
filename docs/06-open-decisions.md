# 06 – Offene Entscheidungen

Legende Priorität: **P0** blockiert den nächsten Arbeitsschritt · **P1** vor
Layout-Freeze nötig · **P2** vor Fertigungsfreigabe nötig.

## Kritischer Pfad

| # | Prio | Entscheidung | Abhängig davon |
|---|---|---|---|
| 1 | **P1** | **Blockierstrom je Motor** — Datenblatt nennt ihn nicht, und ohne Motorelektronik begrenzt ihn nichts | Comparator-Referenz, Soft-Limit, Sicherung. **Nur drei Werte, keiner layoutrelevant** — der Schaltplan kann vorher beginnen, siehe [`11-motor-data.md`](11-motor-data.md) Abschnitt 5. Einfachste Messung: **M6, Ankerwiderstand mit dem Multimeter** |
| ~~1a~~ | ✅ | **PWM ist erlaubt** — der Motor hat keine eigene Elektronik, die gestört werden könnte | erledigt |
| ~~1b~~ | ✅ | **2 Adern je Motor ⇒ H-Brücke zwingend**, 6-poliger Bottom-Connector bestätigt | erledigt |
| 2 | **P0** | Hochstrom-Steckverbinder: Micro-Fit 3.0 vs. stromstärkeres System | Footprint Bottom, Tiefenbudget, Layout-Start |
| 3 | **P0** | Laufen beide Motoren gleichzeitig, oder gibt es einen Software-Interlock? | Eingangsstrom ≈ 9 A vs. ≈ 4,9 A, damit Sicherung, Leiterbahnen und Steckverbinder |

**Punkt 1 blockiert den Schaltplan nicht mehr.** Die defensive Auslegung in
[`11-motor-data.md`](11-motor-data.md) Abschnitt 5 (Annahme: 25 A Blockierstrom) hält
alle messabhängigen Größen in drei nachträglich änderbaren Werten — Comparator-
Referenz, Soft-Limit, Sicherung. Die Messung muss **vor der Bestellung** vorliegen,
nicht vor dem Schaltplan.

Punkt 3 ist eine reine Nutzungsentscheidung, kostet nichts und entschärft Punkt 2
erheblich. Für Klappläden ist sequenzieller Betrieb meist unproblematisch.

## Bauteilauswahl Leistung

| # | Prio | Entscheidung | Bemerkung |
|---|---|---|---|
| 4 | P1 | Buck 24 → 5 V, ca. 3 A | strikt nach Referenzlayout |
| 5 | P1 | Buck 5 → 3,3 V, ca. 1,5 A | |
| 6 | P1 | Buck 24 → 6,2 V, ca. 0,5 A | einstellbare Ausgangsspannung nötig |
| 7 | P1 | H-Bridge: diskret (4× N-FET + Gate-Driver) oder integrierter Treiber | Platz auf Ø 52 mm spricht für integriert, Thermik im geschlossenen Gehäuse ist die Prüffrage |
| 8 | P1 | MOSFET-Typ, falls diskret | RDS(on) vs. Gate-Ladung vs. Bauhöhe |
| 9 | P1 | Current-Sense-Amplifier | zusammen mit #10 zu entscheiden |
| 10 | **P1** | **Sense-Topologie: Low-Side-Shunt mit PWM-synchronem Sampling oder Inline-Messung** | siehe Prüfpunkt in [`02-motor-control.md`](02-motor-control.md); bestimmt, ob die Lasterkennung bei reduzierter PWM überhaupt funktioniert |
| 11 | P1 | Comparator + Latch für den Hard-Trip | muss ohne Firmware wirken, Reset-Pfad über `TRIP_RST` |
| 12 | P1 | Ideal-Diode-Controller / Power-Mux für USB-ORing | Priorität 24 V vor USB |
| 13 | P1 | Sitzt der Power-Mux auf TOP oder BOTTOM? | folgt aus #12; betrifft `5V_SYS`-Richtung im Stack |
| 14 | P2 | Bulk-Kondensatoren: Typ und Bauhöhe | 470–1000 µF, aber max. ≈ 10 mm Bauraum |

## Bauteilauswahl Logik und Peripherie

| # | Prio | Entscheidung | Bemerkung |
|---|---|---|---|
| 15 | P1 | Konkretes ESP32-Modul | Antennenvariante, Bauhöhe, Pinzahl |
| ~~15a~~ | ✅ | **Display: ST77916, 1,46" rund, 360×360.** Kein Treiberaufwand — `mipi_spi` mit `model: CUSTOM` + `init_sequence`, validiert | erledigt; Sequenz in [`../firmware/esphome/st77916_init.yaml`](../firmware/esphome/st77916_init.yaml) |
| 15c | **P0** | **Modul-Außendurchmesser des real gekauften ST77916-Boards messen** | `disp_module_d` in [`../mechanical/frontplate.py`](../mechanical/frontplate.py); bestimmt über eine Zwangsbedingung den Sichel-Innenradius und damit die ganze Frontplattengeometrie |
| 15b | P2 | Modbus-Registerkarte für den RS-485-Primärbetrieb | `modbus_server` ist in ESPHome enthalten (verifiziert); Registerlayout offen |
| 16 | P1 | RS-485-Transceiver | Versorgungsspannung, Fail-Safe-Bias, Terminierung |
| 17 | P1 | Radar-Modul und dessen Versorgung/Logikpegel | Pegelanpassung nötig? Stromaufnahme? |
| 18 | P1 | Externer ADC ja/nein | folgt aus #10; betrifft `J_STK_A` |
| 19 | P1 | Temperatur- und Feuchtesensor | I2C-Adressen dürfen nicht kollidieren |
| 20 | **P0** | **`J_STK_B` v0.2:** QSPI braucht 7 Leitungen, es fehlt genau ein Pin | siehe Änderungsverlauf in [`03-stack-pinout.md`](03-stack-pinout.md) |
| 21 | P1 | Mini-Relais und die zu schaltende Spannung/Stromstärke | **wenn Netzspannung: Isolations- und Kriechstreckenkonzept, verändert die Board-Aufteilung** |
| 22 | P2 | Speaker/Piezo und gewünschte Lautstärke | bestimmt Treiber und Stromaufnahme |
| 23 | P1 | Stackverbinder-Serie im 1,27-mm-Raster | Stackhöhe 10 mm bzw. 8–10 mm, Stromrating |
| ~~24~~ | ✅ | **USB-UART entfällt** — ESP32-S3 hat nativen USB | erledigt |

## Mechanik

| # | Prio | Entscheidung | Bemerkung |
|---|---|---|---|
| 25 | P1 | Finale Frontpanel-Geometrie am realen Rahmen prüfen | Testdruck der Platte in den vorhandenen 55er-Rahmen, siehe [`../mechanical/README.md`](../mechanical/README.md) |
| 26 | P1 | Bottom-Connector gerade oder abgewinkelt | größter Hebel im Tiefenbudget, siehe [`04-mechanical.md`](04-mechanical.md) |
| 27 | P2 | Schraubengröße M2,5 vs. M3 | M2,5 empfohlen |
| 28 | P2 | Bestätigung des Bohrbilds gegen reale Dose und Frontpanel | |
