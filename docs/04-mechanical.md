# 04 – Mechanik

## 1. Grunddaten

| Parameter | Wert |
|---|---|
| Leiterplattenform | Kreis |
| Durchmesser | **Ø 52,0 mm** (Radius 26,0 mm) |
| Leiterplattendicke | **1,0 mm** |
| Unterputzdose | massiv, Ø 60 mm außen, **61 mm tief** |
| Stack-Abstand Bottom ↔ Mid | ≈ 10 mm |
| Stack-Abstand Mid ↔ Top | ≈ 9 mm |

> **Revision: Ø 55,0 mm → Ø 52,0 mm.**
> Eine Gerätedose mit 60 mm Außendurchmesser hat je nach Hersteller nur etwa
> 55–57 mm lichte Weite, und im Inneren sitzen Schraubdome und Verstärkungsrippen.
> Eine Ø-55-mm-Platine wäre damit im besten Fall eine Presspassung ohne jede
> Toleranz — und beim Einbau von drei gestapelten Platinen mit Steckverbindern
> gibt es kein Nachjustieren.
>
> Ø 52,0 mm lässt ringsum 1,5–2,5 mm Luft. Das ist der Wert, mit dem die
> KiCad-Templates erzeugt wurden.
>
> **Vor dem Layout-Freeze die reale Dose ausmessen.** Ist mehr Platz vorhanden,
> ist die Änderung eine Zeile: `BOARD_DIAMETER` in
> [`../tools/gen_boards.py`](../tools/gen_boards.py) und Skript neu laufen lassen.

Board-Outline in KiCad: Kreis auf `Edge.Cuts`, Mittelpunkt (0,0), Radius 26,0 mm.
Board-Dicke über *Board Setup → Physical Stackup*.

Die drei Boards werden nicht von Hand gezeichnet, sondern von
[`../tools/gen_boards.py`](../tools/gen_boards.py) erzeugt. Damit ist ausgeschlossen,
dass Outline oder Bohrbild zwischen den Boards auseinanderlaufen.

## 2. Koordinatensystem

Ursprung (0,0) liegt im **Mittelpunkt der Leiterplatte**, auf allen drei Boards identisch.

> **Achtung — Y-Richtung.** KiCad zählt Y im PCB-Editor nach *unten*. Ein Punkt, der
> mathematisch bei y = +19,919 liegt, wird in KiCad als y = −19,919 eingegeben. Die
> Tabelle unten führt beide Konventionen, um Verwechslungen auszuschließen.

**Frontorientierung:** Für alle drei PCBs gilt dieselbe Definition —
mathematisch **+Y = Frontreferenz „oben“** (12-Uhr-Position). Der Hochstrom-Steckverbinder
sitzt entsprechend im Bereich **−Y (unten)** des Bottom-Boards. Diese Orientierung ist auf
jedem Board durch eine Silkscreen-Markierung an der 12-Uhr-Position kenntlich zu machen.

## 3. Befestigungsbohrungen

Drei Bohrungen **M2,5 (Ø 2,7 mm)** auf Radius **21,5 mm**, im Winkel 0° / 120° / 240°:

| Bohrung | Winkel | X [mm] | Y math. [mm] | Y KiCad [mm] |
|---|---|---:|---:|---:|
| H1 | 0° | +21,5000 | 0,0000 | 0,0000 |
| H2 | 120° | −10,7500 | +18,6195 | −18,6195 |
| H3 | 240° | −10,7500 | −18,6195 | +18,6195 |

Exakt: 21,5 · sin(120°) = 18,6195 mm.

**12 Uhr bleibt frei.** Die Winkel 0/120/240° halten die Position bei +Y bewusst
frei — dort sitzen die Frontmarkierung und der `FRONT`-Schriftzug. Ein Bohrbild bei
90/210/330° kollidiert damit.

**Randabstand:** Bohrungsrand bei Radius 22,85 mm, also 3,15 mm bis zur Kante bei
Ø 52 mm. Der Schraubenkopf einer M2,5 (≈ Ø 5 mm) reicht bis Radius 24 mm — 2 mm
Luft. M3 wäre ebenfalls fertigbar, **M2,5 ist empfohlen**: mehr freie Kupferfläche am
Rand, und in einer Unterputzdose mechanisch völlig ausreichend.

> Die Geometrie ist vor dem finalen Layout gegen Dose, Frontpanel und Steckverbinder zu
> prüfen. Insbesondere darf keine der drei Bohrungen mit dem Bottom-Connector oder mit
> den Stackverbindern kollidieren.

## 4. Tiefenbudget

Verfügbar sind 61 mm Dosentiefe. Überschlägige Rechnung von der Dosenrückwand nach vorn:

| # | Element | Höhe [mm] | Kumuliert |
|---:|---|---:|---:|
| 1 | Kabelbogen / Steckraum hinter dem Bottom-Connector | 12,0 | 12,0 |
| 2 | Bottom-Connector inkl. gestecktem Gegenstück über PCB | 10,0 | 22,0 |
| 3 | Bottom-PCB | 1,0 | 23,0 |
| 4 | Bauteile Bottom-Oberseite + Stack-Abstand | 10,0 | 33,0 |
| 5 | Mid-PCB | 1,0 | 34,0 |
| 6 | Bauteile Mid-Oberseite + Stack-Abstand | 9,0 | 43,0 |
| 7 | Top-PCB | 1,0 | 44,0 |
| 8 | OLED, Taster, Frontpanel | 8,0 | 52,0 |
| | **Reserve** | | **≈ 9,0** |

Das Budget schließt, aber mit wenig Luft. Zwei Positionen sind die kritischen:

- **Positionen 1 + 2 zusammen 22 mm** — mehr als ein Drittel der gesamten Tiefe geht für
  den Leistungsstecker und den Kabelbogen drauf. Ein **abgewinkelter Steckverbinder**
  oder eine Platzierung, die den Kabelbogen seitlich statt nach hinten führt, würde hier
  mehrere Millimeter freimachen. Das ist der wirksamste Hebel, falls das Budget später
  eng wird. Hinweis: ein stromstärkeres System wie Mini-Fit Jr. (siehe
  [`01-power-tree.md`](01-power-tree.md)) baut höher als Micro-Fit — Stromrating und
  Tiefenbudget hängen also direkt zusammen und müssen gemeinsam entschieden werden.
- **Position 4, Bauteile Bottom-Oberseite in 10 mm** — die in
  [`01-power-tree.md`](01-power-tree.md) genannten Bulk-Kondensatoren von 470–1000 µF
  passen als klassische Elkos hier nicht hinein. Realistisch sind mehrere niedrigbauende
  Typen, Polymer-Kondensatoren oder eine Platzierung auf der Unterseite neben dem
  Steckverbinder. Diese Entscheidung fällt beim Bottom-Layout und wirkt auf das gesamte
  Budget zurück.

Sobald die konkreten Bauteile feststehen, ist diese Tabelle mit realen Datenblattmaßen zu
aktualisieren.

## 5. Keepouts

| Bereich | Board | Regel |
|---|---|---|
| ESP32-Antenne | MID | kupfer- und bauteilfrei auf **allen** Lagen, Antenne zur Front |
| Befestigungsbohrungen | alle | Freihaltezone auf allen drei Boards deckungsgleich |
| Bottom-Connector | BOTTOM | Steck- und Entriegelungsraum berücksichtigen, nicht nur den Footprint |
| Stackverbinder | alle | Position auf allen drei Boards deckungsgleich |
| Frontelemente | TOP | USB-C, OLED, Taster, Stern-Stecker müssen zum Frontpanel passen |

Die Positionen von Befestigungsbohrungen und Stackverbindern müssen auf allen drei Boards
**exakt** übereinstimmen. Empfohlenes Vorgehen: mechanische Elemente einmal im
Bottom-Projekt festlegen und die Koordinaten aus dieser Datei in die beiden anderen
Projekte übernehmen, statt sie neu zu zeichnen.

## 6. Externer Bottom-Connector

Verriegelnder, vorkonfektionierbarer Steckverbinder mit PCB-Buchse und steckbarem
Kabelgegenstück.

**Festes logisches Pinout:**

| Pin | Signal |
|---:|---|
| 1 | 24V_IN+ |
| 2 | 24V_IN− |
| 3 | M1_A |
| 4 | M1_B |
| 5 | M2_A |
| 6 | M2_B |

Ausgangspunkt: Micro-Fit 3.0 2×3. **Vor der Footprint-Wahl ist zu prüfen, dass der
konkrete Steckverbinder Nenn- und Peakstrom sicher verträgt** — siehe die Analyse zum
Engpass an den Pins 1 und 2 in [`01-power-tree.md`](01-power-tree.md), Abschnitt 3.

## 7. Stern-Ausgang

Separater zweipoliger Anschluss im Frontpanel, Ausgangspunkt **JST-PH 2-polig**.

| Pin | Signal |
|---:|---|
| 1 | 6V2_STAR |
| 2 | GND_STAR |

- Eigene kleine Absicherung, z. B. Polyfuse ≈ 0,3–0,5 A (Last real ≈ 80 mA)
- Lokaler Kondensator 10–22 µF am Stecker
- Die 6,2-V-Versorgung wird im Normalbetrieb aus 24 V erzeugt und hängt **nicht** vom
  USB-Port ab
