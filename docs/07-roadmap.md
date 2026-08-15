# 07 – Arbeitsschritte

Diese Datei sagt, **was als Nächstes zu tun ist**. Wo das Projekt steht, sagt
[`13-funktionsstatus.md`](13-funktionsstatus.md); die Begründungen einzelner
Entscheidungen stehen in [`06-open-decisions.md`](06-open-decisions.md).

## Erledigt

| Phase | Ergebnis |
|---|---|
| **1 – Spezifikation** | 13 Dokumente: System, Power-Tree, Motorkonzept, Pinout, Mechanik, Fertigung, Display/MCU, Firmwarestrategie, Motordaten, Altbestand |
| **2 – Mechanik** | `tools/gen_boards.py` erzeugt alle drei Boards: Ø-52-Outline, gemeinsames Bohrbild, Keepouts. Frontplatte aus `mechanical/frontplate.py` |
| **3 – Leistung und Motorkanal** | 24-V-Schutz, drei DC/DC, USB-ORing, zwei identische H-Brücken aus einer Funktion, Inline-Shunt + INA240A2 + LM393-Fenster + Latch auf `~SD` |
| **4 – Schaltpläne** | alle drei Boards erzeugt, Netzliste je Board gegen die Sollvorgabe im Quelltext geprüft, Stücklisten daraus |
| **5 – Layouts** | Platzierung, Netze und Zonen generiert; Routing über die Freerouting-Pipeline: **Top vollständig**, Mid alle Signalnetze, Bottom ≈ 85 % |
| **6 – Fertigungsvorbereitung** | `gen_fab.py` mit DRC-Gate, Top exportiert, Fertigungsnutzen aus den drei Quellprojekten erzeugt |

## Als Nächstes

### A. Messen (blockiert am meisten, kostet am wenigsten)

1. **Ankerwiderstand der Motoren messen (M6).** Multimeter an die zwei Adern, Welle
   langsam drehen, kleinsten Wert nehmen → Blockierstrom = 24 V / R. Fünf Minuten
   Arbeit, und aus Annahmen werden Zahlen: Comparator-Referenz, Soft-Limit,
   Sicherung, N-FET-Auswahl (Punkte 1 und 8).
   Protokoll: [`11-motor-data.md`](11-motor-data.md) Abschnitt 4.
2. **Reale Dose und realen 55er-Rahmen vermessen**, Bohrbild und Frontplatte
   dagegen prüfen (Punkte 25, 28). Testdruck der Platte.
3. **Displaymodul kaufen und den Außendurchmesser messen** (Punkt 15c) — er bestimmt
   über eine Zwangsbedingung die gesamte Sichelgeometrie der Frontplatte.

### B. Entscheiden

4. **Punkt 34 (P0): Sabotagekontakte** nachrüsten oder schriftlich streichen.
   Zusammen mit **Punkt 29 (P0): Feldstecker** — beide betreffen dieselbe Ecke des
   Mid-Boards, und der PCF8574 ist restlos belegt.
5. **Punkt 3: Interlock** — dürfen beide Motoren gleichzeitig laufen? Kostet nichts
   und halbiert den Eingangsstrom, von dem Sicherung, Leiterbahnen und Punkt 2
   (Hochstrom-Steckverbinder) abhängen.
6. **Punkt 23 (P0): Stackverbinder-Paar** auswählen — heute sitzt auf allen drei
   Boards dieselbe Buchse. Die Steckhöhe des Paares soll den Plattenabstand
   ergeben (10 mm bzw. 8–10 mm), damit keine Distanzhülsen nötig werden.
7. **Punkt 35: externer Temperaturfühler** ja/nein. Ohne ihn ist der SHT4x konsequent
   als Elektroniktemperatur zu benennen — als Raumtemperatur ist er falsch.

### C. Layout fertigstellen

8. **Mid:** 10 PGND-Pour-Anbindungen mit dem interaktiven Router schließen (~10 min).
9. **Bottom:** 43 offene Verbindungen im Leistungsteil **von Hand** — kurze breite
   Wege, Buck-Schleifen nach Hersteller-Referenzlayout, Sternpunkt AGND/PGND über R12.
   [`05-manufacturing.md`](05-manufacturing.md) verlangt das für Leistungspfade ohnehin.
10. **Schaltungsreview:** IC-Pinbelegungen gegen Datenblätter (besonders INA240A2D mit
    seinen gestapelten GND-Pins), Reglerdimensionierung, Leiterbahnstromrechnung.

### D. Fertigen

11. `python3 tools/gen_fab.py` für Mid und Bottom, danach `gen_panel.py` neu erzeugen.
12. Prüfliste [`05-manufacturing.md`](05-manufacturing.md) Abschnitt 3 abarbeiten,
    Git-Tag je Fertigungsstand setzen, Nutzen bestellen.

### E. Firmware

13. **External Component in C++** — der größte zusammenhängende Brocken. Drei Dinge
    fallen hinein, die alle am selben Problem hängen (ESPHomes Polling-Modell):
    PWM-synchrone Strommessung mit Lasterkennung (Punkt 4 in
    [`09-display-and-mcu.md`](09-display-and-mcu.md)), der VL53L1X-Distanzwert samt
    ROI-Umschaltung (Punkt 31) und die Blendungsauswertung (Punkt 32).
14. **Bedienkonzept:** Menü-Zustandsmaschine mit der Belegung OK / Hoch / Runter /
    Home (Punkt 37) — heute sind die vier Tasten fest auf Auf/Zu verdrahtet.
15. **Verschlusskontakte in die Motorlogik ziehen:** Verschlusslage erreicht ⇒ Fahrt
    beenden. Sie sind der einzige absolute Positionsbezug im System.
16. **BIST und Heartbeat** nach [`../firmware/README.md`](../firmware/README.md).
17. **RS-485 in Betrieb nehmen** (Punkte 15b, 16, 38): Transceiver bestätigen,
    Modbus-Registerkarte festlegen. RS-485 ist der *primäre* Weg — heute ist der
    UART zwar konfiguriert, aber ungenutzt.
