# 17 – Die vier offenen Bauteile: woher die Daten kommen

Vier Teile blockieren die Bestellung, weil ihre Maße, ihr Footprint oder ihr
3D-Modell fehlen. Diese Seite sagt für jedes, **was genau fehlt**, **wo es
herkommt** und **was davon abhängt**.

| Teil | Stand | 3D-Modell |
|---|---|---|
| **Display** | ✅ **ER-TFT1.69-3**, Datenblatt ausgewertet | Hüllkörper nötig |
| **Sternanschluss** | ✅ **JST GH SM02B-GHS-TB, liegend** — seit 19.08. abends: Die stehende BM02B ließ gesteckt nur 3,15 mm, und ihre Litzen zeigten axial aufs Mid-Board. Liegend baut sie 4,25 mm und entlässt die Litzen waagerecht in die Kabelkerbe | ✅ **von KiCad** |
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

### Der Weg der Fahne — Direktlöten (Stand 20.08. spätabends)

> Die frühere Fassung dieses Abschnitts beschrieb einen FPC-Schlitz und
> die Buchse J5 auf der Rückseite — beides beruhte auf den falschen
> Fahnendaten (0,5-Raster, 18,15 lang) und ist ersatzlos entfallen.

```
Panel (Werksklebeband auf der Rückseite)
  └─ Fahne faltet ab Werk an der Panelunterkante (y 15,3)
     └─ Goldfinger zeigen nach der Faltung NACH UNTEN aufs Board
        └─ landen face-down auf 12 Lötpads (0,7 mm) der VORDERSEITE
           bei (−0,95 / 3,6) — Footprint `FPC_Loetfeld_12x0.7mm`
```

**Reihenfolge beim Aufbau:** erst löten (Kolben + Flussmittel, Pin-1-
Marke auf F.Fab, Pin 1 in Frontsicht rechts), dann das Panel mit dem
Werksklebeband aufkleben. Kein Schlitz, keine Buchse, keine Spiegelung —
Pin 1 trifft Pin 1. Prüfpunkt am Muster: FPC 0,13 + Lot müssen in die
0,15er-Klebebandfuge; die Fahnenzone flach halten.

### Was noch fehlt — bereinigt am 20.08.2026

Die beiden früheren „Blocker" hier waren **veraltet**: Das Raster der Fahne
ist längst aus dem Datenblatt bestätigt (**0,50 mm**, siehe FPC-Tabelle
oben), und die Pinbelegung liegt vollständig vor und ist in `gen_top_sch`
verdrahtet. Beides stand hier trotzdem noch als offen — die Doku hinkte.

> **KORREKTUR 20.08. spätabends, anhand von Foto + Originalzeichnung:**
> Das Fahnenraster ist **0,70 mm** (`P0.7*(12-1)=7.7`), nicht 0,50 — die
> TE-Buchse 1-1734839-2 passt NICHT. Die Fahne ist zudem nur **12,96 mm**
> lang (nicht 18,15) und die Panelrückseite ist **selbstklebend**.
> Kontaktseite und Pinlage sind jetzt vom Foto ablesbar: Goldfinger auf
> der Vorderseite der ungefalteten Fahne, 12 links / 1 rechts.
> **Entschieden (gleicher Abend): DIREKTLÖTEN.** Für 0,7 mm existiert
> keine seriöse Buchse, und das Panel klebt ohnehin fest auf dem Board —
> der Stecker hätte keine Servicefreiheit gekauft. J5 ist jetzt ein
> **12-Pad-Lötfeld** (Projekt-Footprint `FPC_Loetfeld_12x0.7mm`, Pads
> 0,4 × 3,2) auf der **Vorderseite** bei (−0,95 / 3,6); FPC-Schlitz und
> TE-Buchse sind ersatzlos entfallen.
>
> **Beide Torfragen sind damit analytisch geschlossen:**
> Die Werksfaltung legt die Goldfinger **face-down auf die Pads** (Foto:
> Kontakte auf der Fahnen-Vorderseite; Faltung kippt die Fläche einmal),
> und ohne Rückseiten-Montage gibt es **keine x-Spiegelung** — Pin 1
> rechts trifft Pin 1 rechts. Das Papiermodell (`fahnenmodell.svg`)
> bleibt als Verifikation am ersten Muster, ist aber kein Bestell-Tor
> mehr.
>
> **Lötablauf:** erst die Fahne auf die Pads löten (0,7 mm mit Kolben und
> Flussmittel gut machbar, Pin-1-Marke auf F.Fab), dann das Panel mit dem
> Werksklebeband aufkleben. Prüfpunkt Musteraufbau: FPC 0,13 + Lot in der
> 0,15-Klebebandfuge — die Fahnenzone flach halten.
>
> **Das Bügel-Rezept im Detail (Frage vom 21.08.: „von oben auf die
> Fahne drücken?" — ja, genau so, mit drei Bedingungen):**
> 1. Pads fluxen, hauchdünn verzinnen, mit Entlötlitze wieder
>    **abziehen** — es bleibt ein ebener Film (Dickenbudget der Fuge!).
>    Später kommt von oben KEIN Lot dazu. Schonvariante: Sn42/Bi58,
>    dann reicht ~200 °C.
> 2. **Buch aufklappen:** Werksfaltung als Scharnier, Panel nach rechts
>    umgeklappt, Displayseite nach unten auf eine Unterlage in
>    Boardhöhe (Schutzfolie bleibt drauf). Die Finger liegen dann von
>    allein face-down auf den Pads. Pin 1 aufs oberste Pad, Kapton über
>    den Fahnenkörper, Flux auf die Zone.
> 3. **Bügeln:** Meißelspitze 300–320 °C, Pin 1 heften, Lage prüfen,
>    Pin 12, dann die Reihe — je Pin 1–2 s ruhig aufsetzen, nicht
>    schieben. Kontrolle: Lot glänzt am 0,36er Padstummel vor der
>    Fahnenspitze (dort zieht es auch kapillar nach, wenn die Spitze
>    direkt ansetzt). Brücken in den 0,3er Lücken mit Flux + Litze
>    räumen. Zug- und Durchgangsprobe VOR dem Zuklappen — danach ist
>    Nacharbeit Zerstörung. Liner abziehen (liegt aufgeklappt oben),
>    zuklappen, ausrichten, andrücken.

> **NACHTRAG 20.08., nachts — die Faltkante war falsch (Einwand des
> Nutzers, am Foto verifiziert):** Die Fahne verlässt das Modul an der
> Datenblatt-**Unterkante**, also an einem Ende der 37,43er-Achse. **Quer
> eingebaut kommt sie von der Seite**, nicht von unten — die Fassung oben
> faltete fälschlich bei y = 15,3. Das Panel wird so gedreht, dass die
> Fahne **rechts** abgeht (links sitzt die USB-Freistellung), und J5
> steht seitdem **90° gedreht** bei **(6,05 / 0,3)**: Raster in y, die
> 2,0-mm-Finger enden bei x ≈ 4,8–6,8, gefaltet wird an der rechten
> Panelkante x = 17,77. Die Kippregel gilt sinngemäß weiter: Die
> Werksfaltung dreht jetzt um die **senkrechte** Kante, **oben/unten
> kippt also nie** — Pin 1 (ungefaltete Fahne, Portrait-Frontsicht:
> rechts) landet quer eingebaut auf dem **obersten** Pad (y = −3,55).
> Faltwulst ≈ 0,5 endet bei x ≈ 18,3, der H2-Schraubkopf beginnt erst
> bei 19,25 — Prüfpunkt für den Musteraufbau.
>
> **Kann eine zu lange Fahne die Zentralscheibe stören? Nein.** Gelötet
> wird vor dem Falten, die 2,0-mm-Finger auf 3,2-mm-Pads geben ±0,6
> Positionierspiel; was übrig bleibt, geht in die Schlaufe, und dort
> wird aus +0,3 Länge nur ~0,1 mehr Radius (ΔL = π·Δr, Wulst 0,5 → 0,6).
> Die Scheibe ist weit weg: Rastnase x = 25,0, Wand innen 26,6, Kavität
> ab z ≈ 24,65 — die Schlaufe bleibt unter der Panel-Vorderseite (22,75),
> darüber federt der Schaum (1,90). Eng ist allein der **H2-Schraubkopf
> (ab 19,25, ≈ 0,9 frei)**; zweites Risiko ist die Sandwich-Dicke
> (FPC 0,13 + Lot in der 0,15er-Fuge — Falten heben das Panel lokal an,
> kosten Schaumweg, erreichen die Scheibe aber nicht).

**Stand 20.08. abends — die Kette ist durchgerechnet** (TE 1734839 ist
laut Herstellerserie ein **Top-Kontakt**-Verbinder; alle Biegungen der
Fahne drehen um die Faltkante, die Gegenrichtung kippt also nie):

> **Kriterium:** Panel umdrehen und auf die Rückseite schauen. Sind die
> Goldfinger der werksgefalteten Fahne **sichtbar → es passt**. Liegen
> sie verdeckt an der Panelrückseite an → gespiegelte Buchse nötig.
> **Pin 1:** Die Buchse ist auf der Rückseite x-gespiegelt montiert — am
> Papiermodell ablesen, an welcher Kante Pin 1 ankommt, dann gleichen
> wir die J5-Verdrahtung ab (reiner Schaltplan-Eingriff).

Die 1:1-Schablone dafür liegt unter `docs/fahnenmodell.svg` — bei 100 %
drucken, das 50-mm-Lineal nachmessen, Ablauf steht auf dem Blatt.

**Die ursprünglichen zwei Fragen im Wortlaut:**

1. **Die Kontaktseite der Fahne.** Die TE-Buchse 1-1734839-2 kontaktiert
   auf EINER Seite. Die Fahne wird an der Panelunterkante um 180° gefaltet
   und taucht durch den FPC-Schlitz — jede dieser Stationen wendet die
   Fahne. Ob am Ende die Kontaktflächen zur Kontaktseite der Buchse
   zeigen, ist **ungeprüft**. Falsch herum wäre das Board wertlos; die
   Alternative wäre die spiegelbildliche Buchse (2-1734839-2 o. ä.) oder
   eine andere Faltung. **Vor der Bestellung am Papiermodell prüfen:**
   Fahne aus Papier im Maßstab falten und durchstecken.
2. **Die Pinreihenfolge nach der Faltung.** Dieselben zwei Wendungen können
   Pin 1↔12 spiegeln. `gen_top_sch` verdrahtet J5 nach der
   Datenblatt-Reihenfolge der *ungefalteten* Fahne — ob sie nach Faltung
   und Durchstecken noch stimmt oder rückwärts läuft, entscheidet dasselbe
   Papiermodell.
3. **Backlight-Vorwiderstand.** R_BL = 39 Ω an 5 V ist gerechnet, nicht
   gegen die LED-Kette des Datenblatts geprüft (Anzahl LEDs in Serie,
   Flussspannung, Nennstrom).

Bis 1. und 2. geprüft sind, gilt weiter: **Top-Board nicht bestellen.**

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
