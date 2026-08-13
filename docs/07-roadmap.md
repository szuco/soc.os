# 07 – Arbeitsschritte

## Aktueller Stand

- Systemspezifikation und Mechanik dokumentiert
- Repository-Struktur angelegt
- **Bottom-Board:** begonnen — Board-Outline als Kreis auf `Edge.Cuts` mit Radius 27,5 mm
  (Ø 55 mm), Board-Dicke 1,0 mm über *Board Setup → Physical Stackup*
- KiCad-Projektdateien noch nicht im Repository, siehe
  [`08-kicad-workflow.md`](08-kicad-workflow.md)

## Reihenfolge

### Phase 1 – Bottom-Board Mechanik
1. Bottom-Projekt nativ in KiCad 9.0.7 fertig mechanisch anlegen: Ø-55-mm-Outline,
   Befestigungsbohrungen nach [`04-mechanical.md`](04-mechanical.md), Connector-Keepouts.
2. Konkreten Hochstrom-Steckverbinder auswählen und dessen Stromrating und Footprint
   verifizieren. → offene Punkte 2 und 3 in [`06-open-decisions.md`](06-open-decisions.md).

### Phase 2 – Bottom-Board Leistung
3. Power-Tree im Bottom-Schaltplan aufbauen: 24-V-Schutz, 24 → 5 V, 5 → 3,3 V,
   24 → 6,2 V, USB-Power-OR.
4. Konkrete Buck-Regler auswählen und **strikt nach Hersteller-Referenzlayout**
   dimensionieren.

### Phase 3 – Motorkanal
5. Motor-H-Bridge Kanal 1 vollständig entwickeln und prüfen, anschließend identisch für
   Kanal 2 duplizieren.
6. Shunt und Sense-Amplifier sowie Hardware-Comparator/Latch hinzufügen.

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

- **Anlauf- und Blockierstrom der Motoren messen.** Das ist der kritische Pfad für
  Sicherungen, Trip-Schwellen, FET-Auswahl und Steckverbinder — je früher, desto besser.
  Ohne diesen Wert bleiben alle Schutzschwellen provisorisch.
- Entscheidung, ob beide Motoren gleichzeitig laufen dürfen.
- Musterbestellung für Radar-Modul, OLED und Sensoren, um Abmessungen und
  Stromaufnahme mit realen Teilen zu bestätigen.
- Reale Dosen- und Frontpanel-Geometrie vermessen und das Bohrbild dagegen prüfen.
