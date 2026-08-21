# 04 – Mechanik

## 1. Grunddaten

| Parameter | Wert |
|---|---|
| Leiterplattenform | Kreis |
| Durchmesser | **Ø 52,0 mm** (Radius 26,0 mm) |
| Leiterplattendicke | **1,0 mm** |
| Unterputzdose | massiv, Ø 60 mm außen, **61 mm tief** |
| **Abdeckrahmen** | **Busch-Jaeger 1721-914, Busch-balance SI, 1-fach** (2CKA001725A1555) |
| Stack-Abstand Bottom ↔ Mid | **10 mm** |
| Stack-Abstand Mid ↔ Top | **10 mm** — bewusst gleich wie unten |

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

> **Überholt am 18.08.2026 — aus vier Durchbrüchen sind zwei geworden.**
> Die vier Diagonalpositionen stammten aus der Zeit vor den Ecktastern; seit
> die dort stehen, ist auf der Diagonalen kein Platz mehr (siehe unten). Die
> neue Aufteilung nutzt den waagerechten Streifen zwischen Displayfenster und
> Platinenrand, der **10 mm hoch und über die ganze Breite frei** ist:
>
> | Durchbruch | Lage | Zweck |
> |---|---|---|
> | **oben** | (0 / −19), Schlitz 14 × 5 mm | **ToF und Raumsensor gemeinsam** |
> | **unten links** | (−10 / +19,4), rund 6 × 5 mm | **Sternanschluss**, JST GH |
>
> **Ein Loch für zwei Sensoren.** Der VL53L1X sitzt bei (−3,5 / −19), der
> SHT4x bei (+3,5 / −19) — 3 mm zwischen den Bauteilkanten. Näher wäre
> schlechter, und zwar aus zwei Gründen: Der ToF darf keine spiegelnde Fläche
> im Sichtfeld haben, sonst misst er Übersprechen statt Entfernung, und der
> Raumsensor darf die Eigenwärme des ToF nicht mitmessen. Bei 27° Öffnungs­winkel
> und 2,5 mm bis zur Scheibe ist der Messkegel dort erst 1,2 mm breit — 3 mm
> Abstand liegen sicher daneben.
>
> **Die Klinke sitzt exakt mittig — weil die USB-Kerbe an den linken Rand
> gewandert ist.** Zuerst lag sie unten und musste sich den 30-mm-Streifen
> zwischen den Ecktastern mit der Klinke teilen; die hätte dann 4 mm neben der
> Mitte sitzen müssen. Quergestellt passt die Buchse aber in den
> **Seitenstreifen**: Der ist zwischen Displayfenster (x = −16,35) und
> Boardrand 7,15 mm breit, und die Buchse ist quer nur 4,3 mm tief.
>
> Ihre Lage ist zwischen zwei Grenzen eingeklemmt und hat **0,75 mm Spiel**:
>
> | Grenze | ergibt |
> |---|---|
> | Mids Radius 26 erlaubt die Körperecke bis y = 12,63 | Mitte ≤ 8,48 |
> | Tops Befestigungsbohrung reicht bis y = 2,98 | Mitte ≥ 7,73 |
>
> Gewählt ist **8,4**. Die Kerbe misst 6,25 × 9,5 mm und braucht keine Öffnung
> in der Scheibe — sie liegt darunter verborgen. Sichtbar sind vorn also genau
> **zwei Löcher**: der Schlitz oben für ToF und Raumsensor, das Loch unten
> mittig für die Klinke.
>
> **Dafür entfällt der Reserve-UART auf dem Top-Board.** Er war ein
> DNP-Steckplatz; auf 47 × 47 mm mit Display, vier Tastern, zwei
> 40-poligen Stackverbindern, Klinke, ToF, Raumsensor und Randkerbe findet der
> Platzierer für ihn keine Stelle mehr. Die Signale `UART_AUX_TX/RX` liegen
> unverändert auf `J_STK_B` 18/20 und sind vom Mid-Board aus erreichbar.

| Position | Zweck |
|---|---|
| oben links | ~~ToF-Fenster (VL53L1X)~~ |
| unten links | ~~Klinkenbuchse Weihnachtsstern~~ |
| oben rechts | ~~Lüftungsschlitz Raumsensor~~ |
| unten rechts | ~~Lüftungsschlitz Raumsensor~~ |

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

### Ergebnisse, gemessen am 16.08.2026

| # | Messwert |
|---|---|
| F1 | **55,2 × 55,2 mm**, Sichtfläche **1,0 mm** dick |
| F2 | Gesamttiefe **7,5 mm** |
| F3 | Fenster **32,7 × 27,0 mm**, Eckradius klein (noch offen) |
| F4 | links 10,3 · oben 13,8 → rechnerisch rechts 12,2 · unten 14,4 |
| F5 | Symbole (von links / von oben): ↑ 28,0/8,0 · ▷ 6,0/27,5 · ↓ 28,0/46,0 · OK 50,0/27,5 |
| F6 | **starr** — keine beweglichen Felder, keine Trennfugen. Auf der Rückseite kleine Kreuze |
| F7 | entfällt |
| F8 | **4 Rastnasen**, je eine mittig pro Kante, 1,0 mm breit und hoch, vorn angeschrägt 1,0 → 1,4 mm. **Lichtes Innenmaß 50,0 mm** |
| F9 | kein Kragen, nur die 1,0 mm starke Wand |
| F10 | **4 Kreuze, 3,2 × 3,2 mm, 1,5 mm hoch** — laut Foto an den **Ecken**, nicht bei den Symbolen |
| F11 | Rahmenfenster **56,00 mm** |
| F12 | Scheibe hält **nicht** von allein im Rahmen; Sichtfläche liegt **bündig** |
| F13 | je Innenseite zwei Doppelstege — eher Justierung als Halt |

### Was daraus folgt

Umgerechnet auf den Ursprung in der Plattenmitte (x rechts, y hoch):

| Merkmal | Lage |
|---|---|
| **Fenstermitte** | (−0,95 · +0,3) — praktisch mittig, minimal nach links |
| **Fensterdiagonale** | 42,4 mm = **1,67″** — deckt sich mit der Katalogangabe 1,68″ |
| Symbol ↑ | (+0,4 · +19,6), r = 19,6 |
| Symbol ▷ | (−21,6 · +0,1), r = 21,6 |
| Symbol ↓ | (+0,4 · −18,4), r = 18,4 |
| Symbol OK | (+22,4 · +0,1), r = 22,4 |
| **Fensterecke** | (±15,4 · ±13,8), r = **20,7** |

**Die Symbole liegen auf den Achsen, die Kreuze auf den Diagonalen.** Das ist
der wichtigste Befund: Gedrückt wird dort, wo die Beschriftung steht — die Kraft
kommt aber an den **Ecken** an. Die starre 1-mm-Platte hängt an vier Rastnasen
in den Kantenmitten und kippt beim Druck auf ein Symbol; die beiden benachbarten
Eckkreuze wandern dabei nach hinten.

Zwei Konsequenzen:

1. **Die Taster bleiben auf den Diagonalen.** Die Befürchtung aus Punkt 42 —
   Taster auf den Achsen, Kollision mit den Befestigungsbohrungen bei 0° und
   180°, Bohrbild aller drei Boards neu — ist damit **vom Tisch**. Die acht
   Taster sitzen heute bei r = 23,2 auf ±12° um die Diagonalen; sie müssen nur
   auf die Kreuzpositionen nachgezogen und von acht auf **vier** reduziert
   werden, denn ein Kreuz von 3,2 mm trifft genau einen Taster.
2. **Die Firmware muss Paare auswerten.** Vier Taster an den Ecken, vier
   Symbole an den Kanten: ↑ = oben links + oben rechts, ↓ = unten links + unten
   rechts, ▷ = oben links + unten links, OK = oben rechts + unten rechts. Jede
   Richtung ist über ihr Paar eindeutig. Das ersetzt die bisherige Annahme
   „vier Tasten, vier GPIOs, eine Taste pro Pin".

**Die vier Durchbrüche passen so nicht mehr.** Sie waren für die Diagonalen
geplant — dort sitzen jetzt die Taster. Auf der Diagonalen bleibt zwischen
Fensterecke (r = 20,7) und Platinenrand (r = 26,0) ein Band von 5,3 mm, in dem
zusätzlich das Kreuz und der Taster liegen. Für ein Ø-4,5-ToF-Fenster und eine
Ø-5,6-Klinke ist das zu wenig; die Lage der Durchbrüche ist neu zu bestimmen,
sobald die Kreuzpositionen vermessen sind.

### Display: der Ausschnitt trifft ein Serienpanel fast exakt

| | |
|---|---|
| Fenster | 32,70 × 27,00 mm |
| **1,69″ 240 × 280 (ST7789), quer** | aktiv **32,63 × 27,97 mm** |
| Passung | Breite **0,07 mm** Luft, Höhe 0,97 mm vom Fenster verdeckt |

Damit ist Punkt 43 praktisch entschieden: Das Panel füllt den Ausschnitt in der
Breite randlos und wird in der Höhe um einen halben Millimeter je Seite
beschnitten — genau das, was ein Fenster tun soll.

### Nachtrag 16.08.2026: die Kreuze liegen außerhalb der Platine

| Gemessen | |
|---|---|
| Kreuzmitten | **7,6 mm** von der oberen bzw. unteren Kante, **9,6 mm** von der linken bzw. rechten |
| Rahmentiefe (F11) | **12 mm** |
| Doppelstege im Rahmen (F13) | Innenmaß **70,0 mm** |

Umgerechnet liegen die vier Druckpunkte bei **(±18,0 · ±20,0)** — also auf
**r = 26,91 mm** unter 48°. Die Ø-52-Platine reicht bis r = 26,0.

> **Der Druckpunkt liegt 0,9 mm außerhalb der Leiterplatte.** Mit dem Taster
> selbst (3,9 × 2,9 mm) und 0,5 mm Randabstand müsste eine *runde* Platine bis
> r = 29,8 reichen, also Ø 59,7 — das passt in keine Dose mit 55–57 mm lichter
> Weite.

Der Grund ist strukturell, kein Rechenfehler: **Das Busch-Jaeger-System ist um
einen quadratischen Einsatz von 54 × 54 mm gebaut, und seine Tasten sitzen in
den Ecken. Ein Kreis hat keine Ecken.** Genau die 0,9 mm, die fehlen, sind der
Unterschied zwischen Quadrat und einbeschriebenem Kreis.

#### Konsequenz: das Top-Board wird eckig

Nur das Top-Board ist betroffen — Mid und Bottom bleiben rund und bleiben in der
Dose. Das Top-Board wandert **vor** die Dose, so wie es der BJ-Einsatz auch tut,
und wird zum abgerundeten Quadrat:

| Randbedingung | Wert |
|---|---|
| Taster muss abdecken bis | (20,4 · 22,4) → Mindestgröße **40,8 × 44,8 mm** |
| Rastnasen der Scheibe (innen 50,0) | Kante höchstens **25,0** von der Mitte |
| **Umgesetzt** | **47 × 47 mm**, Ecken R 4 — die Größe folgt aus der Tiefenkette, siehe Abschnitt 1e |

Das kostet den gemeinsamen Umriss der drei Boards, bringt aber zwei Dinge:
Die Taster sitzen ohne Umlenkung direkt unter den Kreuzen — kein Hebel, kein
bewegliches Druckteil, die Federung bleibt beim Taster —, und weil das
Top-Board die Dose verlässt, **wächst das Tiefenbudget für Mid und Bottom**.

Die Alternative wäre ein Adapter mit vier Hebeln, der den Druck von r = 26,9 nach
innen auf r ≤ 23 umlenkt. Das widerspricht der Kernregel aus
[`09-display-and-mcu.md`](09-display-and-mcu.md) Abschnitt 1b — gedruckte
bewegliche Teile ermüden, Metallkuppel-Taster nicht — und wird deshalb nicht
empfohlen. Aufgenommen als Punkt 48.

#### Und der Adapter wird zum Tragring

F13 sagt: Der Rahmen klemmt auf **70,0 mm**. Das ist Tragring-Maß. Die bisherige
Frontplatte hat Ohren mit **76 mm** Spannweite — die stünden den Klemmstegen des
Rahmens im Weg. Der Adapter muss dem Rahmen also eine Fläche von 70,0 mm
anbieten, mit den Schraublöchern weiterhin auf 60 mm (DIN 49073).

### Noch offen

- **Eckradius** des Fensters (F3) und des Rahmenfensters.
- Bestätigung, dass die Platte beim Druck auf ein Symbol um die Mitte **kippt**
  (dann sind die Tasterpaare wie in Abschnitt „Was daraus folgt" beschrieben).

## 1e. Die Tiefenkette — sie bestimmt Platinengröße und Adapter

Von der Sichtfläche der Zentralscheibe nach hinten gezählt:

| von … bis | was |
|---|---|
| 0,0 … 1,0 | Zentralscheibe, Sichtfläche (F1) |
| 1,0 … 2,5 | Druckkreuz auf ihrer Rückseite (F10) |
| 2,5 … 4,5 | SMD-Taster über der Leiterplatte |
| 4,5 … 5,5 | **Top-Leiterplatte** |
| 7,5 | Rastebene und hinterer Rand der Scheibe (F2) |

### Die Displayfläche im Besonderen

Dort gilt eine eigene Kette, denn das Panel liegt zwischen Platine und
Scheibe:

| von … bis | was |
|---|---|
| 0,0 … 1,0 | Zentralscheibe |
| 1,0 … 2,9 | **Luft, 1,90 mm** — hier sitzt die Schaumdichtung |
| 2,9 … 4,5 | **Panel ER-TFT1.69-3**, 1,60 mm |
| 4,5 | Klebefuge, 0,1 bis 0,2 mm |
| 4,5 … 5,5 | Top-Leiterplatte |

**Befestigt wird geklebt, nicht geklemmt.** Doppelseitiges Band umlaufend auf
den Rand außerhalb der aktiven Fläche — **2,40 mm** an den langen Seiten,
**1,05 mm** an den kurzen. Die Schaumdichtung in den 1,90 mm davor drückt das
Panel zusätzlich an und hält Staub ab, **darf aber nicht die Befestigung
sein**: Die Zentralscheibe ist bewusst abnehmbar, damit man an USB kommt —
ein nur geklemmtes Panel fiele beim Abnehmen heraus.

**Die Vorderseite unter dem Panel ist im Layout gesperrt** (`block_f` in
`gen_layouts.py`). Das war nötig, weil dort zunächst die beiden
Stackverbinder standen — 8 mm hoch, mitten unter der Klebefläche. Sie liegen
jetzt auf der Rückseite, wo sie ohnehin hingehören, ebenso die FPC-Buchse.

> **Und eine dritte, am 18.08.2026 dazugekommen: die USB-C-Buchse passt hier
> nicht.** Zwischen Platinenvorderseite (4,5) und Sichtfläche liegen 4,5 mm,
> davon gehören 1,0 mm der Scheibe selbst und 1,5 mm ihren Druckkreuzen —
> nutzbar sind rund **3,5 mm**. Eine stehende USB-C-Buchse baut 7 bis 9,25 mm
> (GCT USB4115: H = 9,25 mm laut Datenblatt); keine Bauform liegt unter 7 mm.
> Sie hätte die Zentralscheibe durchstoßen, und liegend hätte sie radial nach
> außen gegen die Adapterwand gezeigt.
>
> Die Buchse steht deshalb jetzt auf dem **Mid-Board** bei (3,5 / 20,3) und
> greift durch eine **offene Randkerbe** des Top-Boards nach vorn. Zwischen
> Mids und Tops Oberseite liegen 10,0 mm — dort passt sie bequem. Gesteckt
> wird weiterhin frontal, sobald die Zentralscheibe ab ist.
>
> Die Kerbe misst 11,0 mm in der Breite und reicht von y = 16,8 bis zur
> Boardkante bei 23,5. Offen statt geschlossen, weil ein Fenster einen Steg
> von einem halben Millimeter stehen ließe — der bricht beim Nutzentrennen.
> Der Buchsenkörper liegt mit −0,65…7,65 / 18,15…22,45 vollständig darin, mit
> 3,3 mm Abstand zum Displayfenster, 4 mm zur Klinkenbuchse und 9 mm zum
> Ecktaster.
>
> Der Adapter musste mitziehen: Seine zentrale Durchführung endete bei 21,5
> und ist an dieser Stelle bis 24,0 verlängert. Damit ist er **nicht mehr
> punktsymmetrisch** — die Freistellung liegt auf der 6-Uhr-Seite, dieselbe
> Richtung wie Kerbe und Klinkenbuchse.

Zwei Folgerungen, die nicht verhandelbar sind:

**Die Rastebene liegt hinter der Leiterplatte.** Der Schnapprand des Adapters
steht also hinter ihr und trägt sie zugleich — er ist Rastglied und Auflage in
einem.

**Das Top-Board misst 47 × 47 mm.** Die Scheibe rastet auf lichte 50,0 (F8),
der Rand ist außen 49,8, und bei 1,4 mm Wand bleiben innen genau 47,0. Nach
unten begrenzen die Taster: Sie stehen auf (±18 · ±20), reichen mit Footprint
bis 22,2, und mit Randabstand braucht es mindestens 45,4 — also liegt 47,0
zwischen zwei harten Grenzen und ist keine gewählte Zahl.

Der Adapter ist damit vollständig bestimmt und erzeugt:
[`../mechanical/adapter.py`](../mechanical/adapter.py), Selbsttest bestanden.
Flansch 70 × 70 × 2,5 (darauf klemmt der Rahmen, F13), Schnapprand 49,8 mit
zurückspringendem Rastraum, Platinentasche 47,4, zentrale Durchführung 43 × 43
für die beiden Stackverbinder, Schraubschlitze auf 60 mm. Gesamthöhe 10,0 mm.

Board-Outline in KiCad: Kreis auf `Edge.Cuts`, Mittelpunkt (0,0), Radius 26,0 mm
— **außer TOP**, das ist ein abgerundetes Quadrat 47 × 47 mit R 4.
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

## 2b. Befestigungskonzept v2 — verschraubt statt nur gesteckt (19.08.2026)

Bisher hielt der Stapel allein durch die Steckverbinder, und der Adapter
übernahm Tragring UND Scheibenträger in einem Teil. Beides ist aufgeteilt:

```
Dose
 └─ schrauben (60 mm) ─ TRAGRING-ADAPTER  (mechanical/tragring.py, gedruckt)
                          ├─ Abdeckrahmen klemmt mit den Doppelstegen darauf
                          ├─ zentriert den Adapter-Basisring in der 50,6er Öffnung
                          └─ Kabeldurchlass für den Magnetkontakt
Bottom ═ Hülse M2,5×10 ═ Mid ═ Hülse M2,5×10 ═ Top
                                                └─ liegt in der Tasche des
                                                   SCHEIBENADAPTERS (adapter.py)
                                                    └─ Zentralscheibe rastet darauf
```

**Der Kraftfluss beim Anziehen der beiden Schrauben von vorn — korrigiert
am 20.08.2026:** Schraubenkopf → Top-Board → Adaptertasche →
**Adapter-Drucklippe** → Rahmensteg → Tragring-Adapter → Dose.

Die erste Fassung führte die Kraft über die Zentralscheibe. Das war falsch,
und der Einwand kam aus der Anschauung des echten Teils: **Die 6435-914 ist
das Bedienelement** — die ganze Scheibe bewegt sich, um die Ecktaster zu
drücken. Ein bewegliches Teil kann keine Klemmkraft tragen. Deshalb hat der
Scheibenadapter jetzt eine **Drucklippe** an der Vorderkante (51,6, an den
Kantenmitten für die Rastnasen unterbrochen), die den Rahmensteg direkt
gegen den Tragring presst. Die Scheibe wird zum Schluss nur aufgeclippt und
bleibt kraftfrei beweglich. **Messpunkt F15:** Steg-Innenmaß des Rahmens
(Lippe muss darüber greifen) und Innenmaß des Scheibenkorpus (Lippe muss
darunter bleiben) — 51,6 ist ein Platzhalter zwischen beiden Annahmen.

> **DIE KETTE — neun Stationen, von hinten nach vorn.** So und nur so
> steht sie in jeder Zeichnung und jeder Ansicht (Festlegung des Nutzers
> vom 21.08.):
>
> **1** Feldstecker → **2** Gehäuse-Becher → **3** Bottom → **4** Mid →
> **5** Tragring → **6** Abdeckrahmen → **7** Scheibenadapter →
> **8** Top-Board → **9** Zentralscheibe
>
> Displaypanel und Schaumdichtung sind **keine** eigenen Stationen: Sie
> sind vor der Montage auf das Top-Board geklebt bzw. aufgelegt und
> gehören zu Station 8. Die Handgriffe unten folgen derselben Kette; nur
> der Feldstecker wird praktisch erst angesteckt, wenn die Kartusche
> verschraubt ist — räumlich bleibt er das hinterste Glied.

**Montagereihenfolge — Kartusche, Fassung vom 20.08.2026 (abends).** Die
erste Fassung begann mit dem Tragring in der Dose (unbaubar: Ø 52 passt
nicht durch die 50,6er Öffnung), die zweite schob die Boards lose in die
Dose und setzte den Tragring danach. Auch das ist überholt, seit der
Becher da ist: Die Boards wohnen im **Becher unter dem Tragring** und
gehen mit ihm zusammen als **eine Kartusche** in die Dose.

1. **Mid zwischen die Hülsen schrauben.** Untere Hülsen (M2,5 × 6,
   Buchse/Buchse) auf Bottom auflegen, Mid darüber, obere Hülsen
   (M2,5 × 6, **Stift/Buchse**) von vorn durch Mid in die unteren —
   ihr Gewindestift klemmt Mid. Bottom liegt noch lose an.
2. **Board-Paar in den Becher legen.** Bottom voran auf die vier
   Auflagebosse (Oberkante z = 0); USB-C zeigt zur 9-Uhr-Seite.
3. **Kartusche verschrauben:** zwei **M2,5 × 14** von hinten durch den
   Becherboden und seine Führungsrohre, durch Bottom (H1/H2) in die
   unteren Hülsen — Becher, Bottom und Mid sind jetzt EIN Teil
   (Konzept v3; das Bajonett ist Geschichte, die Dose hat vier Dome).
   Länge gerechnet: Weg 9,7 (Boden 1,5 + Hohlraum 6,9 + Board 1,0 +
   Luft) plus ≥ 4 Gewinde = 13,7 — eine 16er könnte in der 9er-Hülse
   aufsetzen, falls deren Gewinde kürzer als 6,3 ist.
4. **Feldstecker anstecken.** Die gecrimpte, in der Dose vorverdrahtete
   Micro-Fit-Leiste klickt von hinten durch den Stecker-Tunnel der
   Becher-Rückwand an Bottom.
5. **Tragring lose auflegen** (die Öffnung fädelt über die oberen
   Hülsen, Luft 3,8, und die USB-C-Buchse, Luft 2,1), dann **Kartusche
   samt Ring in die Dose schieben** und mit den Geräteschrauben auf
   60 mm festschrauben — erst sie machen Ring und Kartusche zur
   Einheit.
6. **Abdeckrahmen auf den Tragring klemmen** — er sitzt noch lose.
7. **Magnetkontakt-Kabel** aus der unteren Rahmenleiste durch den
   Kabeldurchlass des Tragrings nach innen führen und in J6 auf der
   Top-Rückseite stecken (liegende Buchse, Öffnung zur Kerbe).
8. **Top-Board in den Scheibenadapter**, aufsetzen, zwei Schrauben M2,5
   von vorn durch H1/H2 in die oberen Hülsen. Der Adapter taucht durch
   die Tragring-Öffnung, wird von ihr zentriert und presst mit der
   Drucklippe den Rahmensteg gegen den Tragring — jetzt erst sitzt der
   Abdeckrahmen fest.
9. **Zentralscheibe aufrasten** — nur noch das: Sie hält nichts und
   presst nichts, sie ist das bewegliche Bedienelement.

**Die Steckverbinder tragen seitdem nichts mehr.** Sie sind rein elektrisch;
Punkt 23 (durchsteckbarer Stapelverbinder) verliert dadurch seine mechanische
Bedingung und reduziert sich auf die Frage nach einem elektrisch passenden
Paar mit 10 mm Stapelhöhe.

**Maßvorbehalte, in den Testdruck aufzunehmen:** die Klemmhöhe der
Doppelstege am 70er-Kantenmaß (F13) und neu **F14**: Ist der Abdeckrahmen
unten mittig **hohl** — mindestens Ø 12 frei und ≈ 9 mm tief? Dort sitzt der
Einschraubkörper des Magnetkontakts (DCX-909: Gewinde Ø 8, Länge 8,5); hinter
dem Rahmenrand ist Putz, der Körper muss also vollständig in den Hohlraum des
Rahmens passen.

## 2c. Das Gehäuse — ein Becher, der in den Tragring rastet (20.08.2026)

`mechanical/gehaeuse.py` kapselt Bottom und Mid: Ein Becher (Ø 54,6 außen,
Wand 1,1) geht von hinten über die beiden Boards, die Rückwand hat ein
Tunnel-Fenster für die Feldstecker-Leiste — sie bleibt als einziges von
hinten zugänglich. Vier Auflagebosse tragen das Bottom-Board; gedruckt wird
der Becher zusammen mit dem Tragring.

**Verbindung v3: verschraubt, kein Bajonett (21.08.).** Radiale Haken
scheiterten dreifach (Diagonalen: Öffnungsecken bis r 35,8; außen die
Dose; innen der Basisring), und das Bajonett starb doppelt: Seine Zapfen
standen auf der weggefensterten Wand (zwei von drei schwebten im STL),
und die gemessene Dose hat Dome auf **allen vier Achsen** — es gibt kein
tragfähiges Band mehr. Jetzt halten die zwei Hülsenschrauben der
H1/H2-Achse die Kartusche: M2,5 × 14 von hinten durch den Becherboden,
durch Führungsrohre und Bottom in die unteren Hülsen. Der Tragring liegt
lose auf dem Becherrand.

**Die Dome (F16 gemessen):** Dose 58 licht, über die Dome 54 — die
Ø-6-Pfosten sitzen auf allen vier Achsen. Der Becher (außen 54,6) hat
1,7 mm Luft und vier Fenster à 10; durch sie schaut die Platinenkante.

**F16 im Detail — das Messprotokoll (mit Messschieber, an der echten
Dose):**

| # | Was | Annahme | **gemessen 21.08.** |
|---|---|---|---|
| F16a | Lichte Weite vorn am Rand | 55,0 | **58,0** |
| F16b | Lichte Weite in ~20 mm Tiefe | 55,0 | **58,0** |
| F16c | Weite über die Schraubdome | ~54 | **54,0** |
| F16d | Breite eines Doms, tangential (→ Fensterbreite) | 16 | **Ø 6** |
| F16e | Tiefe: Dosenrand bis Rückwand innen | 61 | **60,0** |
| F16f | Kabeleinführungen | mittig hinten | **seitlich, ~50 mm tief** |
| F16g | Dosentyp | — | — |

**Folgen der Messung:** Der Becher (außen 54,6) hat **1,7 mm Luft**
statt 0,2 — kein Hebel nötig, die Boards bleiben Ø 52. Die Dome sind
**Ø-6-Rundpfosten bis r 27 auf ALLEN VIER Achsen** (12/3/6/9 Uhr,
Nutzerbefund 21.08.) — der Becher bekommt vier Fenster à 10 statt zwei
à 16. Die Tiefe schrumpft auf 60 (Reserve ≈ 16). Die seitlichen
Kabeleinführungen bei ~50 mm Tiefe sind günstig: Der Kabelbogen muss
nicht mehr hinter den Stecker, er kommt von der Seite.

**Der Adapter trägt wieder — drei Einwände des Nutzers vom 21.08.**
„Der Adapter muss ja trotzdem geschlossen sein, sonst hält ja nichts",
„die Aussparungen sind doch genau invers, dort hält doch die
Zentralscheibe" und „es muss sichergestellt sein, dass der
Scheibenadapter auch wirklich auf den Tragring drückt". Alle drei
trafen, alle drei sind behoben:

1. **USB-Freistellung endet an der Auflage.** Sie lief über die volle
   Bauhöhe und trennte den tragenden Ring an der linken Kante komplett
   auf. Die Buchse endet aber bei Modellhöhe 4,75 und liegt dort mit
   x = −23,2 längst **innerhalb** der Platinentasche (deren Rand erst
   bei 23,7 beginnt) — oberhalb der Auflage braucht sie keinen
   Millimeter. Tasche, Lippe und Kragen sind jetzt umlaufend
   geschlossen.
2. **Nasenpass 14,0 → 3,0 mm — und ein Rastnocken dahinter.** F8 misst
   die Rastnasen mit **1,0 mm Breite**; der Platzhalter war
   vierzehnfach überdimensioniert. Die Durchfahrt bleibt nötig — die
   Nasen müssen an Lippe und Kragen vorbei —, ist aber jetzt ein
   schmaler Schlitz statt eines großen Lochs.

   **Und der eigentliche Halt fehlte bisher ganz (Punkt 67).** Der
   umlaufende Rand ist 49,8, das lichte Nasenmaß 50,0: Die Nase fuhr mit
   0,1 mm Luft darüber und griff hinter **nichts** — die Scheibe hätte
   nur lose aufgelegen. Auf den Punkt gebracht hat es der Nutzer: „die
   Zentralscheibe muss sich praktisch in diesen Aussparungen
   rüberklicken." Jetzt sitzt an jeder der vier Kantenmitten — genau
   dort, wo F8 die Nasen misst — ein **Rastnocken 50,6** (6,0 breit,
   0,7 hoch) am hinteren Ende der Schulter. Die Nase weitet sich beim
   Aufschieben um **0,30 mm je Seite** auf (ihre eigene Auflauffase
   1,0 → 1,4 aus F8 übernimmt das) und fällt dahinter in den Rastraum.
   Erst dieser Nocken macht aus dem Aufstecken ein Einrasten; der
   Selbsttest prüft den Hintergriff seither auf 0,2…0,6 mm.
3. **Neuer Auflagekragen 52,0 × 0,8.** Er kragt auf der Vorderseite des
   Basisrings über die Tragring-Öffnung (50,6) und legt sich mit
   **0,70 mm je Seite** auf die Platte. Damit läuft die Kraft
   nachweisbar Schraube → Top-Board → Adapterauflage → **Kragen** →
   Tragring → Geräteschrauben → Dose — **unabhängig von F15**, dessen
   Rahmensteg-Maß weiter offen ist. Obergrenzen eingehalten: Der Kragen
   bleibt im Rahmenfenster (F11: 56,0) und hält 0,60 mm je Seite Luft
   zum Scheibenkorpus (innen 53,2). `pruefe_einbau.py` prüft die
   Auflage jetzt als eigene Materialprobe in der Kragenebene.

**Die y-Falle — drei Ausschnitte lagen spiegelverkehrt (21.08., mit
bloßem Auge gefunden: „warum hat der Tragring oben eine Aussparung?").**
KiCad zählt y **nach unten**, build123d und der STEP-Export **nach
oben**. Die gedruckten Teile hatten Layout-Zahlen direkt übernommen —
damit saßen **USB-Freistellung** (Adapter), **Kabeldurchlass**
(Tragring) und **Steckertunnel** (Becher) alle auf der falschen Seite.
Nachgemessen am exportierten Top-Board: Die USB-Randkerbe steht im
Layout bei y = +8 und im STEP bei y = −8 — Beweis geführt, nicht
vermutet. Der Steckertunnel war zusätzlich an einer veralteten
Position (−10,5 / 15,6 statt J1 bei 0,0 / 17,5).

Behoben, indem die PARAMS in Layout-Koordinaten **bleiben** (so bleiben
sie mit `gen_layouts.py` vergleichbar und die Zeichnungen, die sie
lesen, stimmen weiter) und die `build_*`-Funktionen beim Erzeugen mit
−y spiegeln; der Konventionsblock steht im Kopf aller drei Dateien.

**Warum das keiner der Selbsttests gemerkt hat — und was jetzt anders
ist:** Fenster und Prüfkörper kamen aus **derselben** Konstante, jede
Verschiebung hob sich auf. `mechanical/pruefe_einbau.py` liest die
Gegenstücke jetzt per `ast` aus `gen_layouts.py` (Feldstecker J1,
USB-Buchse J7, Kabelkerbe) und prüft sie boolesch gegen die gedruckten
Teile — die Teile müssen sich nach dem Layout richten, nicht umgekehrt.
Der Fehler war damit reproduzierbar (212 mm³ Stecker im Becherboden,
76 mm³ Buchse im Adapter), und die Prüfung ist grün, seit er behoben
ist.

**Warum Tragring und Scheibenadapter so filigran aussehen — und warum
das kein Fehler ist (21.08., Einwand des Nutzers):** Beide Teile sind
fast nur Wände, und **jede dieser Wandstärken ist von den
Busch-Jaeger-Schnittstellen diktiert**, nicht gewählt: Außen begrenzt
das Rastmaß der Zentralscheibe (50,0 → Rand 49,8), innen das Top-Board
in der Tasche (47,0 + 0,4 Spiel = 47,4) — dazwischen bleiben **1,2 mm
Wand**, mehr gibt die Geometrie nicht her. Die Drucklippe (51,6) folgt
dem Rahmensteg, die Ringdicke (2,0) der Klemmhöhe der Rahmen-Doppelstege
(F13). Verstärken lässt sich nur über das Material (PETG oder PC statt
PLA) und die Druckrichtung (flach, Lasten in der Ebene) — genau dafür
ist der Testdruck mit F13/F15 da. Der Tragring aus dem Originalsystem
ist zum Vergleich ~1 mm Stahlblech; unsere 2 mm Druck sind dagegen
schon die kräftige Fassung.

**Einbauprüfung gegen die gemessene Dose (21.08.,
`mechanical/pruefe_einbau.py`):** Die Dose aus F16 (58 licht, 60 tief,
vier Ø-6-Dome bis r 27) steht als Volumenkörper im Prüfwerkzeug; Becher,
Tragring, Adapter, beide Ø-52-Boards und der Feldstecker werden boolesch
dagegen geschnitten. Ergebnis: **BESTANDEN, kleinere Boards sind NICHT
nötig** — Board→Dom 1,0 Luft, Becher→Dose 1,7, Fensterrand→Dom-Sehne
3,7 je Seite. Ein Treffer wurde dabei gefunden und behoben: Der
Scheibenadapter endete 0,5 **unter** der Wandebene, seine Ecken
(Quadrat-Eckradius 35,2) drückten auf den runden Dosenrand — der
Flansch ist von 2,5 auf 2,0 gekürzt, der Adapter endet jetzt bündig
(stack.py 15,5). Dazu zählt `tools/stl_shells.py` die Schalen jeder
STL: je **eine** — nichts schwebt. Beide Werkzeuge sind die Lektion aus
dem Zapfen-Defekt in Werkzeugform.

**Der bestätigte Defekt und seine Auflösung — Konzept v3, verschraubt
statt Bajonett (21.08.).** Der Einwand „die Ränder hängen in der Luft"
traf: Zwei der drei Bajonettzapfen standen auf der weggefensterten Wand
und schwebten als lose Körper im STL. Mit Domen auf allen vier Achsen
ist das Bajonett auch nicht reparierbar — Zapfen und Ringschlitze
finden kein tragfähiges Band mehr (die Diagonalen blockiert die
quadratische Ringöffnung). Stattdessen fassen die zwei Schrauben, die
Bottom ohnehin von hinten in die unteren Hülsen halten, jetzt **durch
den Becherboden** (M2,5 × 14 statt × 6, Führungsrohre Ø 6 überbrücken
den Hohlraum): Becher + Bottom + Mid sind die verschraubte Kartusche.
Der Tragring liegt lose auf dem Becherrand und kommt mit den
Geräteschrauben an die Dose. Kein neues Teil, keine engen Toleranzen,
und die Rohre stützen Bottom zusätzlich auf der Schraubenachse.

Nach der Messung werden `gehaeuse.py` (Weite, Spiel, Fensterlage/-breite,
Tunnel), die Gegenproben in `tragring.py`, STL/STEP, Renderings und die
Doku in einem Durchgang nachgezogen. Fällt F16 großzügig aus, bekommt
der Becher mehr Luft statt 0,2 mm Passung; fällt er eng aus:

**Falls F16 eng ausfällt — Hebel in dieser Reihenfolge (20.08., nachts,
Einwand des Nutzers):** Der Becher steht mit 54,6 gegen die 55er-Annahme
rechnerisch auf Kante; ob das real reicht, entscheidet allein F16 (eine
60er-Dose hat nominell ~60 lichte Weite, die Annahme ist bewusst
pessimistisch). Wird es eng: **1.** Wand 1,1 → 0,8 und Spiel 0,4 → 0,3
(außen 53,7 — ein Parameter, ein Neudruck); **2.** Dome-Fenster
verbreitern (kostet Wandanteil, keine Elektronik); **3.** erst als
letzter Hebel die Boards verkleinern — Ø 52 → Ø 50 wäre ein Neulayout
beider runden Boards, und Bottom ist heute schon das vollste.

**Baugruppe ≠ Druckdatei.** Wer `switchstack_stack.step` sliced, sieht
den 70er-Ring frei über dem Becher schweben — im Einbau liegt er auf
Dosenrand und Wandputz, die das Modell nicht enthält. Gedruckt werden
**drei Einzelteile**, jedes flach: der Becher auf dem Boden (Wände
senkrecht, Zapfen minimal überhängend), der Tragring als Platte, der
Adapter auf der Lippenseite. Nichts davon braucht Stützen; verbunden
wird erst nach dem Druck, per Bajonett.

Montage ändert sich vorn nicht; neu ist Schritt 2b: Boards in den Becher,
Leiste durch das Rückwandfenster anstecken, Becher an den Tragring
bajonettieren — dann als Einheit in die Dose.

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

Verfügbar sind **60 mm** Dosentiefe (F16e gemessen; vorher 61 angenommen). Überschlägige Rechnung von der Dosenrückwand nach vorn:

| # | Element | Höhe [mm] | Kumuliert |
|---:|---|---:|---:|
| 1 | Kabelbogen / Steckraum hinter dem Bottom-Connector | 12,0 | 12,0 |
| 2 | Bottom-Connector inkl. gestecktem Gegenstück über PCB | 10,0 | 22,0 |
| 3 | Bottom-PCB | 1,0 | 23,0 |
| 4 | Bauteile Bottom-Oberseite + Stack-Abstand | **6,0** | 29,0 |
| 5 | Mid-PCB | 1,0 | 30,0 |
| 6 | Bauteile Mid-Oberseite + Stack-Abstand | **6,0** | 36,0 |
| 7 | Top-PCB | 1,0 | 37,0 |
| 8 | Adapter, Zentralscheibe, Rahmen | — | **außerhalb** |
| | **Reserve** | | **≈ 23,0** (auf 60 gemessen) |

> **Kurzer Stapel seit 21.08.2026 (Punkt 23).** Die Ebenen standen
> 9,0 mm frei auseinander, weil der Steckverbinder diese Höhe tragen
> sollte — bis die Recherche zeigte, dass es erhöhte 1,27-mm-Buchsen
> Jetzt sind es **6,0 mm** — und diese Zahl gibt der Verbinder vor,
> nicht die Mechanik. **Korrigiertes Steckmodell (22.08.):** Die 2,4 mm
> der Buchse sind ihr *Lötpin*, nicht die Einstecktiefe; beim Stecken
> stoßen die Kunststoffkörper aneinander. Es gilt **Spalt =
> Isolatorhöhe des Stifts + Buchsenhöhe** und **Eingriff = Pin-Überstand
> − (Spalt − Buchsenhöhe)**. Mit der 4,3er Buchse braucht der günstigste
> Stift (Isolator 1,5) mindestens 5,80 mm — bei 5,0 würde **jeder** am
> Markt verfügbare Stift klemmen. Nächste Standard-Hülsenlänge: 6,0,
> dort bleiben 1,35 mm Kontakteingriff.
> Die Bauteilhöhen wurden dagegen geprüft: unten steht als höchstes die
> Drossel SRP7028A mit 2,8 mm, oben das ESP32-Modul (3,2) und J6 (4,25),
> die sich örtlich **nicht** überlappen. Nebeneffekt: **9 mm mehr
> Reserve** — und Punkt 66 (Modell 9,0 gegen Doku 10,0) löst sich auf,
> weil Modell und Doku jetzt beide 5,0 sagen.

> **Revision 16.08.2026: das Top-Board verlässt die Dose.** Vorher standen hier
> 8,0 mm für „OLED, Taster, Frontpanel" und ≈ 9 mm Reserve. Seit der Umstellung
> auf die Busch-Jaeger Zentralscheibe sitzt das Top-Board **vor** der Dose im
> Adapter — dessen 10,0 mm Bauhöhe liegen vor der Wand, nicht in der Dose
> (Abschnitt 1e). Die Reserve steigt damit auf **rund 17 mm**.
>
> Das entschärft ausgerechnet die Position, die bisher am engsten war: Für den
> Leistungsstecker samt Kabelbogen (Positionen 1 + 2) ist jetzt Luft, ohne dass
> ein abgewinkelter Verbinder zwingend wird. Punkt 26 verliert damit seine
> Dringlichkeit — die Entscheidung bleibt, aber sie blockiert nichts mehr.

Zwei Positionen bleiben die kritischen:

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
