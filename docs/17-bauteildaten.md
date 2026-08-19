# 17 – Die vier offenen Bauteile: woher die Daten kommen

Vier Teile blockieren die Bestellung, weil ihre Maße, ihr Footprint oder ihr
3D-Modell fehlen. Diese Seite sagt für jedes, **was genau fehlt**, **wo es
herkommt** und **was davon abhängt**.

| Teil | Stand | 3D-Modell |
|---|---|---|
| **Display** | ✅ **ER-TFT1.69-3**, Datenblatt ausgewertet | Hüllkörper nötig |
| **Sternanschluss** | ✅ **JST GH BM02B-GHS-TBT** — die Klinke ist entfallen | ✅ **von KiCad** |
| **USB-C** | 🟡 GT-USB-7051x, LCSC C2843970 | 🟡 Hüllkörper, Höhe angenommen |
| **Feldstecker** | ✅ Molex Micro-Fit 43045-1612 | 🟡 Hüllkörper aus dem Footprint |

**Zwei Punkte haben sich seit dem 18.08.2026 erledigt.** Das Display hat sein
Datenblatt (Auszug in [`datasheets/ER-TFT1.69-3.md`](datasheets/ER-TFT1.69-3.md)),
und die Klinkenbuchse gibt es nicht mehr — sie passte neben dem Displaypanel
nicht mehr auf das Board und ist durch einen JST GH ersetzt, für den KiCad ein
Modell mitliefert.

**Was bleibt, sind zwei Hüllkörper.** Für USB-C und den Feldstecker erzeugt
[`../mechanical/connector_models.py`](../mechanical/connector_models.py) Körper
aus dem F.Fab-Grundriss des Footprints — der Grundriss ist damit so genau wie
das Footprint, nur die Höhe ist gesetzt:

| | Höhe | Herkunft |
|---|---|---|
| Micro-Fit 43045-1612 | 8,90 mm | Serienmaß der Baureihe |
| USB-C GT-USB-7051x | 9,25 mm | oberer Wert der Bauform (GCT USB4115) |

Für die Frage „stößt etwas an" reicht das. Die offiziellen Modelle liegen bei
Molex zu jeder Bestellnummer und bei GCT für den USB4115; beide Seiten geben
sie automatisierten Abrufen nicht heraus, sie müssen im Browser geholt und
unter `hardware/lib/3dmodels/` abgelegt werden. Sobald sie dort liegen,
benutzt `gen_layouts.py` sie ohne weitere Änderung — die Verknüpfung greift
über den Dateinamen.


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

## 4b. Magnetkontakt für den Stern — was er messen darf

Seit dem 18.08.2026 wird der Stern nicht mehr gesteckt, sondern magnetisch
angelegt. Der Kontakt sitzt in einem Loch der Zentralscheibe und taucht durch
einen Durchbruch des Top-Boards nach hinten in die 10 mm zwischen Top und Mid.
**Die Bauhöhe ist damit gleichgültig** — der Durchmesser nicht.

| Grenze | Wert | woher |
|---|---|---|
| Displaypanel (Sperrfläche) endet bei | y = 15,90 | `gen_layouts` `block_f` |
| Platinenkante | y = 23,50 | TOP_SQ/2 |
| freier Streifen | **7,60 mm** | |
| abzüglich 0,3 mm zum Panel, 0,5 mm zur Kante | **≤ 6,80 mm in y** | |
| in x, solange J6 bei x = −17 steht | **≤ 7,25 mm** | Achsabstand minus GH-Körper |

`_pruefe_magnetloch()` rechnet beides beim Erzeugen nach und bricht ab, statt
ein Loch unter das aufgeklebte Panel oder unter einen Steckverbinder zu
schneiden. Gegen alle vier Fälle getestet.

### Aufgelöst am 19.08.2026: Der Kontakt sitzt im Abdeckrahmen

Die ganze Durchmesserfrage hat sich erledigt: Der Magnetkontakt sitzt jetzt
**im Abdeckrahmen unten mittig**, nicht mehr in der Zentralscheibe. Dort ist
Platz für das vorhandene **DCX-909-Set** — die Einschraubseite (Gewinde Ø 8,
Flansch Ø 12, Länge 8,5) kommt in ein Ø-8-Loch der unteren Rahmenleiste,
vorausgesetzt der Rahmen ist dort hohl (**Messpunkt F14**, docs/04 2b).

Vom Kontakt läuft ein kurzes Kabel hinter dem Rahmen nach innen, durch den
Kabeldurchlass des Tragring-Adapters und die Unterkerbe des Top-Boards auf
dessen Rückseite in J6. Im Board selbst gibt es **kein Magnetloch mehr**.

### Die Gegenseite: Litzen an die Steckseite (Lötscheibe)

Die abnehmbare Seite des DCX-909 ist ein Platinenbauteil — drei Lötstifte
Ø 0,8 im Abstand 3,70. Litzen direkt an solche Stifte zu löten hält nicht:
Jede Bewegung arbeitet in der Lötstelle.

Deshalb gibt es `hardware/stern_puck/` — eine **Ø-14-Lötscheibe**, die im
selben Fertigungsauftrag mitbestellt wird:

1. DCX-909-Stifte in die drei Durchstecklöcher löten
2. Litzen des Sterns von hinten durch die **Fesselbohrungen** fädeln,
   umschlagen, in die Lötaugen löten — die Zugentlastung ist die Bohrung,
   nicht das Zinn
3. Schrumpfschlauch mit Innenkleber über alles

Polung ist auf dem Siebdruck markiert; die N-Pol-Kodierung des DCX-909
verhindert verkehrtes Anlegen am Rahmen.

### Überholt: Das vorhandene Teil passt nicht (galt nur für den Scheiben-Einbau)

**DCX-909-(9×8)-H5.2**, gemessen aus der Maßzeichnung: Körper Ø 8,00 mm,
Flansch Ø 9,00 mm, Bauhöhe 5,20 mm, magnetisch kodiert (N-Pol markiert). Die
Kodierung ist vorbildlich, die Höhe seit dem Durchbruch belanglos — aber
8,00 mm sind 1,2 mm zu viel für den Streifen. Wird abgewiesen.

### Was die Suche ergeben hat

Gesucht wurde nach einem Katalogteil mit öffentlichem Datenblatt. **Es gibt
keines.** Diese Bauteilklasse wird fast ausschließlich als Auftragsfertigung
ohne Datenblatt verkauft:

- [Promax](https://promaxpogopin.com/magnetic-connector-2pin/), [SUNMON](https://smeconn.com/magnetic-pogo-pin-connector/),
  [QH Industrial](https://www.connectors-cables.com/magnetic-pogo-pin-connector/) — nur Auftragsfertigung
- [HytePro](https://www.hyte.pro/product/m423.html) M416/M423/M430 — echte Modellnummern, Seite
  aber gegen Abruf gesperrt (403)
- [EDAC POGO+ bei DigiKey](https://www.digikey.com/en/product-highlight/e/edac/pogo-magnetic-spring-loaded-connectors) — Katalogware mit Datenblatt, aber
  Kontaktleisten mit 1,8/2,0 mm Raster, kein fertiger Magnetstecker
- LCSC führt Pogo-Pins, jedoch keinen 2-poligen Magnetkontakt mit Maßzeichnung

**Also gilt dasselbe Verfahren wie beim DCX-909: kaufen und messen.** Neu ist
nur, dass wir jetzt genau wissen, worauf zu achten ist — ein Maß, nicht drei.

**Einkaufszettel:** 2-polig, magnetisch kodiert (N/S, „anti-reverse"),
**eine Abmessung ≤ 6,5 mm**, Strom ≥ 0,2 A (der Stern zieht 80 mA). Bauhöhe
und die zweite Abmessung sind frei — bei einem länglichen Teil muss dann
allerdings J6 weichen, was der Wächter meldet.

## 5. Reihenfolge

1. **Display entscheiden.** Es blockiert am meisten — Footprint, Pinzahl und
   Fensterlage hängen daran, und `J5` ist heute reine Erfindung.
2. **Molex-STEP holen.** Zehn Minuten, und der Feldstecker ist erledigt.
3. **Klinke und USB-C** über LCSC und SnapEDA. Beide sind unkritisch, weil die
   Footprints stehen und nur die Modelle fehlen.

Erst wenn alle vier stehen, ist die STEP-Baugruppe belastbar — und damit die
Aussage, ob der Stapel wirklich in die Dose passt.
