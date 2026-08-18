# 17 – Die vier offenen Bauteile: woher die Daten kommen

Vier Teile blockieren die Bestellung, weil ihre Maße, ihr Footprint oder ihr
3D-Modell fehlen. Diese Seite sagt für jedes, **was genau fehlt**, **wo es
herkommt** und **was davon abhängt**.

| Teil | Stand | fehlt |
|---|---|---|
| **Display** | 🟡 **ER-TFT1.69-3** gewählt | Raster der Fahne, Pinbelegung |
| **Klinkenbuchse** | 🟡 Footprint steht | Datenblatt, 3D-Modell |
| **USB-C** | 🟡 Footprint steht | Datenblatt, 3D-Modell |
| **Feldstecker** | ✅ Typ steht | 3D-Modell vom Hersteller |

---

## 1. Display — der kritische Fall

Im Schaltplan steht `J5` als **`Connector_Generic:Conn_01x10`** mit einem
1,27-mm-Stiftleisten-Footprint und dem Kommentar „PLATZHALTER". Es ist also
weder ein Bauteil gewählt noch ein Anschluss festgelegt.

### Zwei Bauformen, und nur eine passt

**Fertigmodul mit Trägerplatine** (Waveshare, AZ-Delivery, Seeed): 240×280,
ST7789V2, aber **48 × 31 mm** Außenmaß. Unser Top-Board misst 47 × 47 mm —
das Modul wäre einen Millimeter breiter als die Platine. **Scheidet aus.**

**Nacktes Panel mit FPC-Fahne:** rund 30 × 36 mm, wird in eine
FPC-Buchse gesteckt oder direkt angelötet. **Das ist die Bauform, die wir
brauchen**, und sie passt auch zum vorgesehenen Anschluss.

### Gewählt am 18.08.2026: ER-TFT1.69-3

| | |
|---|---|
| aktive Fläche | **27,97 × 32,63 mm** |
| sichtbare Fläche | 28,97 × 33,63 mm |
| Außenmaß (FPC gefaltet) | **30,07 × 37,43 × 1,6 mm** |
| Treiber | ST7789V, 4-Draht-SPI |
| Anschluss | **12-polige FPC, steckbar** |

Quer eingebaut misst die aktive Fläche 32,63 × 27,97 gegen ein Fenster von
32,70 × 27,00: **0,07 mm Luft in der Breite**, und in der Höhe verdeckt die
Scheibe oben und unten je 0,49 mm, also **rund acht Pixel je Seite**. Bewusst
in Kauf genommen — die Firmware darf in diesen Zeilen nichts Wichtiges
zeichnen.

Auf dem Top-Board: Dicke 1,6 mm gegen 2,0 mm Budget passt; in y reicht das
Panel bis ±15,04 und bleibt damit frei von den Ecktastern bei 18,27…21,73. In
x reicht es bis ±18,71 und liegt damit **neben** den Tastern — rund 1,5 mm
diagonaler Abstand. Am realen Teil ansehen.

### Was noch fehlt

Beides steht nur im Datenblatt
(`buydisplay.com/download/manual/ER-TFT1.69-3_Datasheet.pdf`, im Browser
öffnen — automatische Downloads liefern HTTP 403):

1. **Das Raster der Fahne.** Die Lötvariante ist mit 0,7 mm angegeben. KiCad
   bringt für 0,7 mm **kein einziges** FPC-Footprint mit, nur 0,5 und 1,0.
   Ist es wirklich 0,7, muss eines in die Projektbibliothek gezeichnet
   werden. Im Schaltplan steht solange ein 0,5-mm-Footprint mit der richtigen
   Polzahl.
2. **Die Pinbelegung.** Zwölf Pole sind gesichert, welches Signal auf welchem
   liegt nicht.

Solange beides offen ist, darf das Top-Board **nicht** bestellt werden.

### Frühere Kandidaten

| Quelle | Typ | Anschluss |
|---|---|---|
| buydisplay.com | **ER-TFT1.69-1** | FPC zum Anlöten |
| buydisplay.com | 1.69" 240×280, „Connector FPC" | FPC-Buchse |

Datenblätter liegen unter
`buydisplay.com/download/manual/ER-TFT1.69-1_Datasheet.pdf` — **im Browser
öffnen**, automatische Downloads blockt der Anbieter (HTTP 403).

### Was aus dem Datenblatt geholt werden muss

1. **Außenmaß des Panels** — muss auf 47 × 47 mm passen, mit Abstand zu den
   vier Ecktastern bei (±18 / ±20).
2. **Lage der aktiven Fläche im Außenmaß.** Das ist die entscheidende Zahl:
   Das Fenster der Zentralscheibe misst **32,7 × 27,0 mm** und liegt bei
   (−0,95 / +0,3). Die aktive Fläche muss dort hineinfallen — ein Panel, dessen
   Rand asymmetrisch ist, verschiebt das Bild im Fenster.
3. **Pinzahl und Raster der FPC-Fahne** (meist 8 bis 14 Pins, 0,5 oder 0,7 mm).
   Danach wird `J5` getauscht: heute 10 Pins im 1,27er-Raster, künftig eine
   FPC-Buchse.
4. **Länge und Abgangsrichtung der Fahne** — sie muss zum Anschluss führen,
   ohne über die Boardkante zu ragen.
5. **Dicke.** Zwischen Platinenoberfläche und Scheibenrückseite liegen 2,0 mm
   (docs/04, Tiefenkette). Ein Panel von 2,5 mm passt nicht.

### 3D-Modell

Panelhersteller liefern selten STEP. Ersatz: Hüllkörper aus den
Datenblattmaßen, wie bei den Steckverbindern —
[`../mechanical/connector_models.py`](../mechanical/connector_models.py) nimmt
den Grundriss aus dem Footprint und extrudiert ihn auf die Datenblatthöhe.

---

## 2. Klinkenbuchse

Verbaut: `Jack_3.5mm_QingPu_WQP-PJ398SM_Vertical_CircularHoles`. Das ist die
Bauform, die überall als **PJ-320A** oder **PJ-398SM** verkauft wird —
stehend, 3,5 mm, mit Schaltkontakt.

| gesucht | wo |
|---|---|
| Datenblatt | LCSC-Produktseite, dort liegt das Herstellerdatenblatt als PDF |
| 3D-Modell | SnapEDA und Ultra Librarian führen PJ-320A/PJ-398SM mit STEP |
| Alternative | GrabCAD hat mehrere Modelle dieser Bauform |

**Zu prüfen:** Der Körper ist 12,0 mm lang (unser Hüllkörper) und ragt
absichtlich über die Boardkante. Das reale Maß entscheidet, wie weit — und ob
der Abdeckrahmen davor genug Freiraum hat.

---

## 3. USB-C-Buchse

Verbaut: `USB_C_Receptacle_G-Switch_GT-USB-7051x`, **LCSC C2843970**.

| gesucht | wo |
|---|---|
| Datenblatt | LCSC-Produktseite zu C2843970 |
| 3D-Modell | G-Switch liefert keines; SnapEDA hat vergleichbare vertikale USB-C |

**Die Alternative mit besserer Datenlage:** GCT veröffentlicht für seine
eigenen Teile STEP-Modelle und vollständige Zeichnungen auf `gct.co`. Der
**USB4115** ist die vertikale Bauform dort — allerdings mit **H = 9,25 mm**,
was wir schon geprüft haben. Über Mid ist das kein Problem mehr, seit die
Buchse dort steht.

**Zu prüfen:** die reale Bauhöhe. Unser Hüllkörper rechnet mit 9,25 mm; ist
die GT-Buchse niedriger, gewinnen wir Luft zwischen Mid und Top.

---

## 4. Feldstecker — und die Frage nach Schraubklemmen

Verbaut: **Molex Micro-Fit 3.0, 43045-1612**, 2×8 stehend.

**Das Modell gibt es beim Hersteller.** Molex veröffentlicht zu jeder
Bestellnummer eine Produktseite mit Zeichnung und **STEP zum Download**. Das
ist die beste Datenlage aller vier Teile — nur liefert KiCad das Modell nicht
mit, deshalb war der Stecker im 3D-View unsichtbar.

### Schraubklemmen statt Steckverbinder?

Geprüft, und die Geometrie spricht dagegen:

| Bauform | 16 Pole brauchen | Platz auf Ø 52 |
|---|---|---|
| Schraubklemme 3,5 mm | **56 mm** | passt nicht |
| Schraubklemme 5,0 mm | 80 mm | passt nicht |
| Schraubklemme 2,54 mm | 40,6 mm | passt, aber winzig |
| **Micro-Fit 3.0, 2×8** | **28,15 mm** | passt |

Schraubklemmen sind einreihig — sechzehn Pole werden dadurch doppelt so lang
wie ein zweireihiger Steckverbinder. Dazu käme, dass der vorbereitete
Kabelbaum mit einem Klick entfiele: Bei Schraubklemmen wird in der Dose
geschraubt, einzeln, über Kopf.

**Empfehlung: beim Micro-Fit bleiben** und das Modell bei Molex holen.

---

## 5. Reihenfolge

1. **Display entscheiden.** Es blockiert am meisten — Footprint, Pinzahl und
   Fensterlage hängen daran, und `J5` ist heute reine Erfindung.
2. **Molex-STEP holen.** Zehn Minuten, und der Feldstecker ist erledigt.
3. **Klinke und USB-C** über LCSC und SnapEDA. Beide sind unkritisch, weil die
   Footprints stehen und nur die Modelle fehlen.

Erst wenn alle vier stehen, ist die STEP-Baugruppe belastbar — und damit die
Aussage, ob der Stapel wirklich in die Dose passt.
