# 07 – Arbeitsschritte

## Aktueller Stand

- Systemspezifikation und Mechanik dokumentiert
- Repository-Struktur angelegt
- **Bottom-Board: Mechanik und Schaltplan fertig.** Ø-52-mm-Outline, Bohrbild,
  103 Bauteile, 105 Netze, netzlistengeprüft gegen die Soll-Konnektivität
- Stückliste erzeugt, Stack-Pinout v0.2 daraus abgeleitet
- **Offen ab hier: das Layout des Bottom-Boards**, danach Mid und Top

## Reihenfolge

### Phase 1 – Bottom-Board Mechanik
1. Bottom-Projekt nativ in KiCad 9.0.7 fertig mechanisch anlegen: Ø-52-mm-Outline,
   Befestigungsbohrungen nach [`04-mechanical.md`](04-mechanical.md), Connector-Keepouts.
2. Konkreten Hochstrom-Steckverbinder auswählen und dessen Stromrating und Footprint
   verifizieren. → offene Punkte 2 und 3 in [`06-open-decisions.md`](06-open-decisions.md).

### Phase 2 – Bottom-Board Leistung ✅
3. ~~Power-Tree aufbauen~~ — erledigt: 24-V-Schutz, 24 → 5 V, 5 → 3,3 V, 24 → 6,2 V,
   12-V-Gate-Versorgung, USB-ORing.
4. ~~Buck-Regler auswählen~~ — TPS54360DDA (2×), TLV62569DBV.
   **Offen:** Reglerlayout gegen Hersteller-Referenzdesign abgleichen (beim Routing).

### Phase 3 – Motorkanal ✅
5. ~~H-Brücke entwickeln und duplizieren~~ — beide Kanäle identisch aus derselben
   Funktion erzeugt, damit sie nicht auseinanderlaufen können.
6. ~~Shunt, Sense-Amplifier, Comparator und Latch~~ — 1 mΩ inline, INA240A2,
   LM393-Fenster, 74AUP1G74 auf `~SD`.

### Phase 3b – Layouts (alle drei Boards) — Platzierung ✅, Routing offen
6a. ~~Bauteile platzieren~~ — `tools/gen_layouts.py` erzeugt alle drei Layouts:
    Footprints mit Netzen, mechanisch gebundene Teile exakt, Rest kollisionsfrei,
    PGND-Zonen beidseitig, DRC ohne Platzierungsfehler.
6b. **Routing** — Handarbeit in KiCad: Leistungspfade kurz und breit, Sternpunkt
    AGND/PGND über R12, Reglerlayouts nach Referenzdesign, QSPI gebündelt.
6c. Schaltungsreview: IC-Pinbelegungen gegen Datenblätter, Reglerdimensionierung.

### Phase 4 – Stack und weitere Boards
7. Stackverbinder und endgültiges Pinmapping in allen drei Projekten identisch
   definieren. → [`03-stack-pinout.md`](03-stack-pinout.md).
8. Mid-Board mit ESP32, RS-485, Radar und Audio erstellen.
9. Top-Board mit USB-C/UART, OLED, vier Tastern, Temperatur/Feuchte und Stern-Ausgang
   erstellen.

### Phase 5 – Absicherung und Fertigung
10. ERC und DRC, thermische Betrachtung, Leiterbahnstrom- und Kupferprüfung, danach
    Fertigungsdaten. → [`05-manufacturing.md`](05-manufacturing.md).

## Parallel und unabhängig

Diese Punkte hängen nicht am Layout und können jederzeit vorgezogen werden:

- **Ankerwiderstand der Motoren messen (M6).** Multimeter an die zwei Adern, Welle
  langsam drehen, kleinsten Wert nehmen → Blockierstrom = 24 V / R. Fünf Minuten
  Arbeit, und alle Schutzschwellen werden aus Annahmen zu Zahlen.
  Protokoll: [`11-motor-data.md`](11-motor-data.md) Abschnitt 4.
- Entscheidung, ob beide Motoren gleichzeitig laufen dürfen.
- Musterbestellung für Radar-Modul, OLED und Sensoren, um Abmessungen und
  Stromaufnahme mit realen Teilen zu bestätigen.
- Reale Dosen- und Frontpanel-Geometrie vermessen und das Bohrbild dagegen prüfen.
