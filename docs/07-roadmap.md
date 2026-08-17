# 07 – Arbeitsschritte

Diese Datei sagt, **was als Nächstes zu tun ist**. Wo das Projekt steht, sagt
[`13-funktionsstatus.md`](13-funktionsstatus.md); die Begründungen einzelner
Entscheidungen stehen in [`06-open-decisions.md`](06-open-decisions.md).

## Erledigt

| Phase | Ergebnis |
|---|---|
| **1 – Spezifikation** | 13 Dokumente: System, Power-Tree, Motorkonzept, Pinout, Mechanik, Fertigung, Display/MCU, Firmwarestrategie, Motordaten, Altbestand, Funktionsstatus |
| **2 – Mechanik** | Board-Mechanik aus `tools/gen_boards.py`: Bottom und Mid rund Ø 52, **Top quadratisch 47 × 47**. Adapter für die BJ-Zentralscheibe aus `mechanical/adapter.py`, Selbsttest bestanden |
| **3 – Leistung und Motorkanal** | 24-V-Schutz, drei DC/DC, USB-ORing, zwei identische H-Brücken aus einer Funktion, Inline-Shunt + INA240A2 + LM393-Fenster + Latch auf `~SD` |
| **4 – Schaltpläne** | alle drei Boards erzeugt, Netzliste je Board gegen die Sollvorgabe im Quelltext geprüft, Stücklisten daraus |
| **5 – Layouts** | Platzierung, Netze und Zonen aller drei Boards. **Top ist DRC-frei**; Bottom zu ≈ 85 % geroutet (985 Segmente); Mid und Top tragen **keine** Leiterbahnen |
| **6 – Fertigungsvorbereitung** | `gen_fab.py` mit DRC-Gate; `gen_panel.py` erzeugt den Nutzen aus gemischter Geometrie (173,4 × 64,4 mm) |
| **7 – Front** | Sichtfläche ist ein Serienteil: BJ-Zentralscheibe 6435-914 im Rahmen 1721-914, vermessen (Protokoll F1–F13). Vier Ecktaster unter den Druckkreuzen, Display ST7789 1,69″, stehende USB-C-Buchse |

## Als Nächstes

### A. Messen (blockiert am meisten, kostet am wenigsten)

1. ✅ **Blockierstrom gemessen (17.08.2026): 1,6 A je Motor**, Ankerwiderstand
   15 Ω, bestätigt durch zwei Messpunkte bei 2 V und 24 V. Damit sind die Punkte
   1, 2 und 3 erledigt und vier Werte angepasst — Shunt 5 mΩ, Trip 4,0 A,
   Sicherung 6,3 A, Firmware-Skalierung 4 A/V.
   Offen bleibt daraus **Punkt 54**: Der Signalabstand für die Endlagenerkennung
   ist kleiner als gedacht.
   Protokoll: [`11-motor-data.md`](11-motor-data.md) Abschnitt 4.
2. **Displaymodul 1,69″ kaufen und vermessen** (Punkt 15c): Außenmaß, Bauhöhe,
   FPC-Abgang. Bestimmt den Footprint von J5, die Sperrfläche auf dem Top-Board
   und die Tasche im Adapter — zwischen Platine und Scheibe stehen 4,5 mm.
3. **Adapter drucken und zusammenstecken.** Erst am realen Teil zeigt sich, ob
   die Scheibe hält, ob der Rahmen klemmt und ob die Taster den Druck sauber
   annehmen.

### B. Entscheiden

4. **Punkt 34 (P0): Sabotagekontakte** nachrüsten oder schriftlich streichen.
   Zusammen mit **Punkt 29 (P0): Feldstecker** — beide betreffen dieselbe Ecke des
   Mid-Boards, und der PCF8574 ist restlos belegt.
5. ✅ **Punkt 3: Interlock** entfällt — beide Motoren dürfen gleichzeitig laufen,
   und seit der Strommessung interessiert das den Steckverbinder nicht mehr
   (3,9 A statt 9 A). Punkt 2 ist damit ebenfalls erledigt: Micro-Fit 3.0 reicht.
6. **Punkt 23 (P0): Stackverbinder-Paar** auswählen — heute sitzt auf allen drei
   Boards dieselbe Buchse. Die Steckhöhe des Paares soll den Plattenabstand
   ergeben, damit keine Distanzhülsen nötig werden.

### C. Layout fertigstellen

7. **Top und Mid routen.** Beide tragen null Leiterbahnen. Die Pipeline dafür ist
   `tools/route_boards.py` (Freerouting 1.9.0 unter `xvfb-run`, siehe docs/05) —
   sie braucht Linux, auf macOS läuft sie nicht. Nacharbeit an der Masse mit
   `tools/gnd_*.py`.
8. **Bottom:** 43 offene Verbindungen im Leistungsteil **von Hand** — kurze breite
    Wege, Buck-Schleifen nach Hersteller-Referenzlayout, Sternpunkt AGND/PGND über R12.
    [`05-manufacturing.md`](05-manufacturing.md) verlangt das für Leistungspfade ohnehin.
9. **Schaltungsreview:** IC-Pinbelegungen gegen Datenblätter (besonders INA240A2D mit
    seinen gestapelten GND-Pins), Reglerdimensionierung, Leiterbahnstromrechnung.

### D. Fertigen

10. `python3 tools/gen_fab.py` für alle drei Boards, danach `gen_panel.py` neu erzeugen.
11. Prüfliste [`05-manufacturing.md`](05-manufacturing.md) Abschnitt 3 abarbeiten,
    Git-Tag je Fertigungsstand setzen, Nutzen bestellen.

### E. Firmware

12. **External Component in C++** — der größte zusammenhängende Brocken. Drei Dinge
    fallen hinein, die alle am selben Problem hängen (ESPHomes Polling-Modell):
    PWM-synchrone Strommessung mit Lasterkennung (Punkt 4 in
    [`09-display-and-mcu.md`](09-display-and-mcu.md)), der VL53L1X-Distanzwert samt
    ROI-Umschaltung (Punkt 31) und die Blendungsauswertung (Punkt 32).
13. **Bedienkonzept:** Menü-Zustandsmaschine hinter der Paarauswertung (Punkt 37).
    Die Scheibe bringt die Beschriftung mit: ↑ ▷ ↓ OK.
14. **Sanftauslauf** vor der Endlage: ab ≈ 80 % der Fahrzeit auf ≈ 40 % PWM rampen,
    Schwellwerte der Lastanalyse mitführen. Die Reed-Kontakte gehören **nicht**
    dazu — sie sichern das Fenster ([`../firmware/README.md`](../firmware/README.md)).
15. **BIST und Heartbeat** nach [`../firmware/README.md`](../firmware/README.md).
16. **RS-485 in Betrieb nehmen** (Punkte 15b, 16, 38): Transceiver bestätigen,
    Modbus-Registerkarte festlegen. RS-485 ist der *primäre* Weg — heute ist der
    UART zwar konfiguriert, aber ungenutzt.
