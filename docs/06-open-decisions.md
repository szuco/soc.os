# 06 – Offene Entscheidungen

Legende Priorität: **P0** blockiert den nächsten Arbeitsschritt · **P1** vor
Layout-Freeze nötig · **P2** vor Fertigungsfreigabe nötig.

## Kritischer Pfad

| # | Prio | Entscheidung | Abhängig davon |
|---|---|---|---|
| 1 | **P0** | **Realer Anlauf- und Blockierstrom der Jalousiemotoren** | Sicherungen, Soft-Limit 9 A, Hard-Trip 13 A, FET-/Treiberwahl, Shunt-Leistung, Bulk-Cap-Größe, Steckverbinder |
| 2 | **P0** | Hochstrom-Steckverbinder: Micro-Fit 3.0 vs. stromstärkeres System | Footprint Bottom, Tiefenbudget, Layout-Start |
| 3 | **P0** | Laufen beide Motoren gleichzeitig, oder gibt es einen Software-Interlock? | Eingangsstrom ≈ 9 A vs. ≈ 4,9 A, damit Sicherung, Leiterbahnen und Steckverbinder |

Punkt 1 hängt an einer Messung bzw. am Motordatenblatt. Er ist der Engpass für nahezu
alle Schutz- und Auslegungswerte und sollte deshalb zuerst geklärt werden.

Punkt 3 ist eine reine Nutzungsentscheidung, kostet nichts und entschärft Punkt 2
erheblich. Für Jalousien ist sequenzieller Betrieb meist unproblematisch.

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
| 15a | P1 | Display final: ST77916-LCD (Wrapper nötig) oder AMOLED (Plan B, Auflagen) | Entscheidungsrahmen in [`10-firmware-strategy.md`](10-firmware-strategy.md), Abschnitt 5 |
| 15b | P2 | Modbus-Registerkarte für den RS-485-Primärbetrieb | `modbus_server` ist in ESPHome enthalten (verifiziert); Registerlayout offen |
| 16 | P1 | RS-485-Transceiver | Versorgungsspannung, Fail-Safe-Bias, Terminierung |
| 17 | P1 | Radar-Modul und dessen Versorgung/Logikpegel | Pegelanpassung nötig? Stromaufnahme? |
| 18 | P1 | Externer ADC ja/nein | folgt aus #10; betrifft `J_STK_A` |
| 19 | P1 | Temperatur- und Feuchtesensor | I2C-Adressen dürfen nicht kollidieren |
| 20 | P1 | OLED: Abmessungen, Schnittstelle I2C oder SPI | bei SPI drei zusätzliche Signale auf `J_STK_B`, siehe [`03-stack-pinout.md`](03-stack-pinout.md) |
| 21 | P1 | Mini-Relais und die zu schaltende Spannung/Stromstärke | **wenn Netzspannung: Isolations- und Kriechstreckenkonzept, verändert die Board-Aufteilung** |
| 22 | P2 | Speaker/Piezo und gewünschte Lautstärke | bestimmt Treiber und Stromaufnahme |
| 23 | P1 | Stackverbinder-Serie im 1,27-mm-Raster | Stackhöhe 10 mm bzw. 8–10 mm, Stromrating |
| 24 | P1 | USB-UART-Baustein | möglichst direkt neben der USB-C-Buchse |

## Mechanik

| # | Prio | Entscheidung | Bemerkung |
|---|---|---|---|
| 25 | P1 | Finale Frontpanel-Geometrie | Zugänglichkeit von USB-C, OLED, Buttons, Stern-Stecker |
| 26 | P1 | Bottom-Connector gerade oder abgewinkelt | größter Hebel im Tiefenbudget, siehe [`04-mechanical.md`](04-mechanical.md) |
| 27 | P2 | Schraubengröße M2,5 vs. M3 | M2,5 empfohlen |
| 28 | P2 | Bestätigung des Bohrbilds gegen reale Dose und Frontpanel | |
