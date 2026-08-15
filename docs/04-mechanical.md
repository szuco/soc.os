# 04 – Mechanik

## 1. Grunddaten

| Parameter | Wert |
|---|---|
| Leiterplattenform | Kreis |
| Durchmesser | **Ø 52,0 mm** (Radius 26,0 mm) |
| Leiterplattendicke | **1,0 mm** |
| Unterputzdose | massiv, Ø 60 mm außen, **61 mm tief** |
| **Abdeckrahmen** | **Busch-Jaeger 1721-914, Busch-balance SI, 1-fach** (2CKA001725A1555) |
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

## 1b. Der Abdeckrahmen ist festgelegt

Verwendet wird der **Busch-Jaeger 1721-914** (Bestellnummer 2CKA001725A1555),
Serie *Busch-balance SI*, 1-fach, alpinweiß. Damit sind zwei Maße keine
Annahmen mehr:

| Maß laut Herstellerangabe | Wert | Folge für dieses Projekt |
|---|---|---|
| Einbaumaß (Fenster) | **55 × 55 mm** | Die Frontplatte mit 54,6 × 54,6 mm passt mit 0,2 mm Luft je Seite — das bisher angenommene 55er-Maß ist bestätigt |
| Außenmaß | **81 × 81 mm** | Die Tragring-Ohren der Platte sind 76 mm breit und verschwinden vollständig hinter dem Rahmen (2,5 mm Überdeckung je Seite) |
| Tiefe | 12 mm | sitzt vor der Wand, geht **nicht** ins 61-mm-Tiefenbudget |
| Bohrungsöffnung | 71 mm | deckt die Ø-60-Dose sicher ab |
| Befestigung | „Klemmbefestigung" | **Das ist die offene Stelle — siehe unten** |

### Was am realen Rahmen zu messen ist

Der Rahmen hält durch Klemmung, und die Herstellerangaben sagen nicht, *woran*.
Bei den SI-Serien greifen die Rastnasen üblicherweise am Tragring, nicht an der
Zentralscheibe — unsere Frontplatte ersetzt aber den Tragring durch zwei
angeformte Ohren und bietet den Rastnasen damit möglicherweise nichts zum
Greifen. Das entscheidet, ob die Platte überhaupt so montierbar ist, und gehört
zum Testdruck (Punkt 25):

1. **Woran rastet der Rahmen?** Innenkontur der Rastnasen ausmessen und
   prüfen, ob die Platte dort Material anbieten muss.
2. **Hat das 55er-Fenster vorn einen umlaufenden Absatz**, der die
   Zentralscheibe hält? Dann übernimmt er die Halterung, und die Platte braucht
   nur die richtige Dicke an der Kante.
3. **Eckradius des Fensters** gegen `plate_corner_r` = 2,0 mm — ein anderer
   Radius zeigt sich als Spalt in den Ecken.
4. **Freiraum für den Tastenüberstand:** Die Sicheln stehen 0,8 mm vor der
   Sichtfläche; sie liegen bei r ≤ 26,2 mm und damit sicher im 55er-Fenster,
   dürfen aber nicht an einem Innenabsatz des Rahmens streifen.

## 1c. Frontkonzept: Zentralscheibe statt eigener Platte

**Festgelegt am 15.08.2026.** Die Sichtfläche ist keine Eigenentwicklung mehr,
sondern die **Busch-Jaeger Zentralscheibe 6435-914** (2CKA006430A0402) mit dem
Aufdruck „Pfeile und OK". Sie gehört systemisch zum Bedienelement 6456-101 und
wird auch für Raumthermostat 1098 U-101 und CO₂-Sensor 1091 U verwendet.

| Zielhülle laut Datenblatt 6456-101 | Wert |
|---|---|
| Korpus | **54 × 54 × 23 mm** |
| Display | **1,68″**, hochauflösend, mit Hintergrundbeleuchtung |
| Bedienung | vier Tasten, Symbole *play / hoch / runter / OK* auf der Scheibe |

Damit entfallen die vier Sicheltasten und die gedruckte 54,6er-Platte; an ihre
Stelle tritt ein Adapter, der diesen Korpus nachbildet (Punkt 41). Das Display
wird rechteckig (Punkt 43), USB-C zeigt nach vorn und liegt unter der Scheibe
(Punkt 45).

### Die vier Durchbrüche

Alle vier liegen **auf den Diagonalen**, je einer zwischen einem Pfeil und einer
Taste — symmetrisch, und alle vier im 55er-Fenster und damit über der Dose:

| Position | Zweck |
|---|---|
| oben links | **ToF-Fenster** (VL53L1X) |
| unten links | **Klinkenbuchse** Weihnachtsstern |
| oben rechts | **Lüftungsschlitz** Raumsensor |
| unten rechts | **Lüftungsschlitz** Raumsensor |

### Warum nicht im Abdeckrahmen

Naheliegend wäre, Klinke und ToF durch den Rahmen zu führen — er hat 13 mm
Rand rings um das Fenster. Das geht nicht, und zwar aus Maßen, nicht aus
Geschmack:

```
Rahmenfenster 55 × 55        -> halbe Kante            27,5 mm
Dose Ø 60 aussen             -> lichte Weite 55…57 mm  -> Radius 27,5…28,5 mm
```

Die Fensterkante des Rahmens fällt also mit der Dosenwand zusammen. Alles
außerhalb — der gesamte Rand — liegt **auf der Wand**. Hinter einem Loch dort
ist Putz, keine Platine. Aufgenommen als Punkt 47.

## 1d. Messprotokoll F1–F13: Zentralscheibe und Abdeckrahmen

Diese Maße geben das Top-Layout und den Adapter frei. Ein Maßbild ist öffentlich
nicht zu bekommen, deshalb werden sie am realen Teil genommen. Benötigt werden
nur **Zentralscheibe 6435-914** und **Abdeckrahmen 1721-914** — der Einsatz
6422 U ist bequem, aber nicht nötig.

**Bezugssystem:** Blick auf die Sichtfläche. Ursprung ist die Mitte der
Zentralscheibe, **x nach rechts, y nach oben**. Weil die Mitte nicht direkt
messbar ist, wird alles gegen die **Plattenkanten** gemessen; die Umrechnung
mache ich. Messschieber, 0,1 mm genügt.

### A – Zentralscheibe, Sichtseite

| # | Maß | Warum |
|---|---|---|
| **F1** | Außenmaß Breite × Höhe, und die Dicke der Sichtfläche | Prüft die 55-mm-Annahme und gibt die Materialstärke für die vier Durchbrüche |
| **F2** | Gesamttiefe: Sichtfläche bis zur hintersten Kante (Rastnasen eingerechnet) | Obergrenze für alles, was zwischen Platine und Scheibe steht — Display, USB-C-Buchse, Klinke |
| **F3** | Fensterausschnitt: Breite × Höhe, dazu der Eckradius | **Bestimmt das Display** (Punkt 43) |
| **F4** | Lage des Fensters: Abstand linke Fensterkante ↔ linke Plattenkante, obere Fensterkante ↔ obere Plattenkante | Sitzt das Fenster mittig? Falls nicht, ist genau das die entscheidende Zahl |

### B – Die vier Symbolfelder

| # | Maß | Warum |
|---|---|---|
| **F5** | Je Symbol: Abstand seiner Mitte zur **linken** und zur **oberen** Plattenkante | **Entscheidet Punkt 42.** Liegen die vier auf den Achsen oder auf den Diagonalen? Daran hängt, ob die acht Taster wandern müssen — und damit das Bohrbild aller drei Boards |
| **F6** | Sind die Symbolfelder **beweglich**? Draufdrücken: federt es, klickt es, oder ist es starres Material? Gibt es Trennfugen oder Schlitze rings um das Feld? | Entscheidet, ob die Scheibe selbst die Taste ist oder ob der Adapter Tastenkappen tragen muss |
| **F7** | Falls beweglich: Breite × Höhe der beweglichen Fläche, und wo sie angebunden ist (umlaufender Steg, Filmscharnier auf einer Seite?) | Bestimmt, wo der Druck ankommt und wie viel Hub zur Verfügung steht |

### C – Zentralscheibe, Rückseite (das eigentliche Interface)

| # | Maß | Warum |
|---|---|---|
| **F8** | **Rastnasen:** Anzahl, Lage (Abstand zu den Plattenkanten), Höhe über der Rückfläche — und das **lichte Innenmaß zwischen gegenüberliegenden Nasen**, in x und in y | Das ist das Maß, auf das der Adapter geklemmt wird. Die wichtigste Zahl für Punkt 41 |
| **F9** | Umlaufender Kragen oder Rand auf der Rückseite: lichte Innenmaße und Tiefe | Der Adapter muss hineinpassen, ohne die Scheibe aufzudrücken |
| **F10** | **Druckstößel oder Dome hinter den Symbolfeldern:** vorhanden? Wenn ja Ø, Höhe über der Rückfläche und Lage | Falls vorhanden, sind **das** die Punkte, auf die unsere SMD-Taster müssen — dann ist F5 nur die Kontrollrechnung |

### D – Abdeckrahmen und Zusammenbau

| # | Maß | Warum |
|---|---|---|
| **F11** | Lichtes Fenstermaß des Rahmens und dessen Eckradius; Tiefe von der Sichtfläche bis zur Rückkante | Gegenprobe zu den 55 × 55 aus dem Katalog |
| **F12** | Scheibe in den Rahmen setzen: **Hält sie von allein?** Und wie tief liegt ihre Sichtfläche hinter der Rahmenvorderkante? | Klärt, ob der Rahmen die Scheibe hält oder der Adapter — und wie weit die Tastenfelder vorstehen dürfen |
| **F13** | Klemmelemente des Rahmens auf seiner Rückseite: Lage und lichtes Maß — worauf klemmt er? | Punkt 25: Der Adapter muss dem Rahmen anbieten, was sonst der Tragring bietet |

### Ergebnisse eintragen

Werte hier ergänzen, sobald gemessen. Vier davon geben das Layout frei: **F3**
(Displaygröße), **F5** oder **F10** (Tastenpositionen), **F8** (Rastmaß) und
**F2** (Bauhöhe).

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

> **Bohrbild v2 — ZWEI Bohrungen statt drei.** Die Layout-Kollisionsprüfung hat
> einen Konflikt aufgedeckt, den die Frontplatten-Selbsttests nicht sehen konnten:
> Die Bohrungen bei 120°/240° lagen nur ≈ 2 mm neben den Sicheltasten-Stößeln
> (117°/243°) — Schraubenkopf und Taster kollidieren. Und auf r = 21,5 mm blockieren
> die Stackverbinder (um 45/135/225/315°), die ESP32-Antenne (um 90°) und der
> Leistungsstecker (um 270°) alle übrigen Kandidaten. **Frei sind genau 0° und 180°.**
> Die Verdrehsicherung übernehmen die beiden Stackverbinder selbst.

Zwei Bohrungen **M2,5 (Ø 2,7 mm)** auf Radius **21,5 mm**:

| Bohrung | Winkel | X [mm] | Y [mm] |
|---|---|---:|---:|
| H1 | 0° | +21,5 | 0,0 |
| H2 | 180° | −21,5 | 0,0 |

Quelle und Durchsetzung: `tools/gen_layouts.py` (Kollisionsmodell mit Kreisprüfung
für die Schraubenköpfe) und `tools/gen_boards.py`; beide aus denselben Konstanten.

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

## 6b. Durchbrüche in der Frontplatte

Die Sichtfläche darf nur an den vier Stegen zwischen den Sicheltasten
durchbrochen werden. Auf 3 und 9 Uhr liegen die Befestigungsbohrungen, es
bleiben **12 und 6 Uhr**. Jeder der beiden trägt **genau einen** Durchbruch:

| Durchbruch | Ø | Position (math, Y nach oben) | Zweck |
|---|---|---|---|
| **ToF-Fenster, 12 Uhr** | 4,5 vorn / 3,0 hinten | x = +5,0, y = **+22,5** | VL53L1X, konisch für den Sichtkegel |
| **Klinkenbuchse, 6 Uhr** | 5,6 mm | x = 0,0, y = **−22,5** | Weihnachtsstern, 2,5-mm-Klinke |

**Warum diese Aufteilung und nicht umgekehrt:** Der ToF muss nach oben — er soll
nach vorn und in die Fensteröffnung schauen, nicht auf die Fensterbank. Der
Steckplatz gehört nach unten, sonst hängt das Sternkabel quer über der Anzeige.
Vorher saßen beide Durchbrüche oben; die Klinke ist am 15.08.2026 nach unten
gewandert und liegt dort mittig, weil sie den Steg allein hat.

Die Stege sind von 9 auf **17 mm** verbreitert (`key_spoke_hw` 4,5 → 8,5) — und
zwar alle vier, weil `_ring_sketch` beide Rechtecke symmetrisch schneidet. Die
Sicheln schrumpfen dadurch von rund 70° auf 45°, die Stößel rücken von ±18° auf
±12° um die Diagonalen, sonst stünden die Taster den Durchbrüchen im Weg.

Der Kabelausgang Ø 4,5 mm im unteren Steg entfällt — der Stern wird gesteckt.
**Für die Klinkenbuchse gilt ein hartes Höhenmaß: 10,5 mm über der
Top-Leiterplatte**, mehr Platz ist bis zur Sichtfläche nicht da.

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
