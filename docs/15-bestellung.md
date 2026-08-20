# 15 – Bestellen bei JLCPCB: Anleitung

Diese Seite ist die Schritt-für-Schritt-Anleitung für die erste Bestellung.
Sie steht bewusst getrennt von der Fertigungsdoku ([`05-manufacturing.md`](05-manufacturing.md)),
die begründet, *warum* die Daten so aussehen.

> **Vor allem anderen: Das DRC-Gate muss grün sein.** `tools/gen_fab.py`
> schreibt keine Fertigungsdaten, solange auch nur eine Verbindung offen ist.
> Das ist Absicht — eine unvollständige Platine darf man nicht versehentlich
> bestellen. Wenn `gen_fab.py` kein ZIP herausgibt, ist die Bestellung noch
> nicht dran, egal wie fertig alles andere aussieht.

## 0. Die Reihenfolge der Abarbeitung (20.08.2026)

Zwei harte Tore bestimmen den Ablauf: Das **Papiermodell der Displayfahne**
(docs/17) entscheidet, ob J5 richtig herum sitzt — und Top steckt im
Nutzen, also hängt die GESAMTE Platinenbestellung daran. Und `gen_fab.py`
gibt **keine Gerber heraus, solange ein Netz offen ist**.

**Schritt 1 — Fahnenprüfung: ERLEDIGT (20.08., anhand Foto + Zeichnung).**
Das Raster ist 0,7 mm (nicht 0,5), die Fahne 12,96 mm — entschieden wurde
**Direktlöten** auf ein 12-Pad-Feld der Vorderseite; Schlitz und Buchse
sind entfallen. Kontaktseite und Pinreihenfolge sind damit analytisch
geklärt (docs/17). Das Papiermodell bleibt nur als Kontrolle am ersten
Muster. **Dieses Tor ist offen — die Bestellung hängt nicht mehr daran.**

**Schritt 2 — Handarbeit in KiCad (docs/16).**
Offene Netze schließen (Top 11, Mid 4, Bottom 4), Masse-Inseln, die
Via-Engpassliste. Danach Zonen füllen, DRC bis `unconnected = 0`.

**Schritt 3 — Fertigungsdaten erzeugen.**
`gen_panel.py` → `gen_fab.py` (das Gate öffnet sich) → `gen_assembly.py`.
Ergebnis: Gerber-ZIP, BOM, CPL für den Nutzen.

**Schritt 4 — parallel dazu: Messen und Testdruck.**
F14/F15/F16 am echten Rahmen/Scheibe/Dose messen → Werte in die PARAMS
von `adapter.py`/`tragring.py`/`gehaeuse.py` → Teile drucken →
Prüfpunkte 25/51/62/63/67 am Druck. Unabhängig von den Platinen.

**Schritt 5 — parallel dazu: Bestellungen ohne Tor.**
Mouser-Sammelbestellung (Abschnitt 2c), Display bei BuyDisplay (nach
Schritt 1!), Stapelverbinder-Paar aus dem Herstellerkatalog (Punkt 23),
Lötscheibe (`stern_puck_gerber.zip` liegt), DCX-909-Set, Hülsen M2,5 × 9.

**Schritt 6 — JLCPCB-Bestellung (nach 2 + 3).**
ZIP hochladen, BOM/CPL dazu, die ~29 Extended-Positionen per
Parametersuche wählen (E96-Werte, 1210-Kondensatoren, Zener),
VL53L1X als Global Sourcing, **Drehwinkel in der Vorschau prüfen**
(Abschnitt 4), bestellen.

**Schritt 7 — Aufbau (wenn alles da ist).**
Kabelbaum crimpen, Lötscheibe konfektionieren, Montage nach docs/04
(acht Schritte), flashen über USB-C bei abgenommener Scheibe.

## 1. Was bestellt wird

**Ein Nutzen, nicht drei Platinen.** `hardware/fab/panel/` enthält alle drei
Boards auf einem Träger von **173,4 × 72,4 mm**, verbunden über Stege mit
Mausbissen. Das ist billiger als drei Einzelaufträge und für die Bestückung
ohnehin nötig.

| | Wert | woher |
|---|---|---|
| Maße | 173,4 × 72,4 mm | `tools/gen_panel.py` |
| Lagen | **4** | alle drei Boards vierlagig |
| Dicke | 1,0 mm | docs/05 |
| Kupfer | 1 oz | reicht bei 4,1 A Summenstrom |
| Oberfläche | HASL bleifrei oder ENIG | ENIG bei den 0,65-mm-Rastern besser |
| Mindeststrukturen | 0,15 mm Abstand, 0,2 mm Bahn | im Regelwerk hinterlegt |
| kleinste Bohrung | 0,3 mm | Vias 0,6/0,3 |

### Dazu: die Lötscheibe (19.08.2026)

`hardware/stern_puck/` ist eine **zweite, winzige Bestellposition**: die
Ø-16-Lötscheibe, die die Steckseite des Magnetkontakts DCX-909 mit den
Litzen des Weihnachtssterns verbindet (docs/17, 4b). Zweilagig, ohne
Bestückung — als eigener Auftrag kostet sie bei JLCPCB den Mindestpreis von
etwa 2 €. Sie in den Vierlagen-Nutzen zu integrieren wäre teurer, nicht
billiger: Sie würde dort als Vierlagerin mitbezahlt.

Gerber dafür erzeugt derselbe Ablauf wie unten, nur mit
`hardware/stern_puck/stern_puck.kicad_pcb` als Eingabe. Bei der Bestellung
**2 Lagen, 1,0 mm, beliebige Farbe** wählen; Stückzahl 5 ist das Minimum und
mehr als genug.

### Panel-DRC: zwölf bekannte Meldungen, bewusst akzeptiert (20.08.2026)

Die DRC des Nutzens meldet 6× `items_not_allowed` und 6×
`npth_inside_courtyard` — alle zwölf sind **dieselbe Sache**: Die
Mausbiss-Bohrungen des Stegs an der 12-Uhr-Kante des Mid-Boards liegen in
der (absichtlich riesigen) ESP32-Sperrfläche. Dort ist kein Kupfer im
Spiel, und die Bohrungen verschwinden mitsamt dem Steg beim Heraustrennen.
Kein Handlungsbedarf; alles andere im Nutzen ist kupferfehlerfrei.

## 2. Die Dateien

```
tools/gen_fab.py                    # Gerber + Bohrdaten + ZIP je Board
tools/gen_assembly.py               # Stückliste, Bestückungsdatei, Plan
hardware/fab/bestueckung/           # das Ergebnis von gen_assembly
  switchstack_panel-bom-jlcpcb.csv  #   -> "BOM file" im Portal
  switchstack_panel-cpl-jlcpcb.csv  #   -> "CPL file" im Portal
  switchstack_panel-bestueckung.pdf #   -> zum Gegenprüfen, nicht hochladen
```

Der Gerber-ZIP des Nutzens entsteht mit `gen_fab.py`, sobald das DRC-Gate
grün ist.

## 2b. Woher die LCSC-Nummern kommen (20.08.2026)

Von 131 Bestückpositionen des Nutzens tragen jetzt **97 eine verifizierte
Nummer** — aus drei Quellen, mit drei Verlässlichkeitsstufen:

1. **Einzeln nachgeschlagene Katalogteile** (17 Stück): jede Nummer von
   einer LCSC-Produktseite — alle Aktiven (DRV8871, TPS54360, INA240,
   ESP32, …), die Steckverbinder GH und USB-C, die Display-FPC-Buchse
   (C3169233), beide Speicherdrosseln, BC847C.
2. **JLCPCB-Basisbauteile** (Masse der Passiven): abgeglichen gegen die
   Basisliste, wert- und MPN-genau (z. B. `0603WAF4022T5E` = exakt
   40,2 kΩ → C12447). Das Portal prüft beim BOM-Upload ohnehin jede
   Nummer gegen den Lagerbestand — eine veraltete Nummer fällt dort auf,
   eine falsche Zuordnung nicht, deshalb der MPN-Abgleich.
3. **Werkzeug:** `tools/lcsc_nachtragen.py` schreibt alle Nummern als
   unsichtbare Felder auf die gerouteten Boards; die Generatoren tragen
   sie zusätzlich für künftige Neuerzeugungen. Nach jedem `gen_layouts`
   einmal laufen lassen.

**Die 54 restlichen Positionen** (38 Zeilen) sind zwei Sorten:

| Sorte | Positionen | Weg |
|---|---|---|
| Extended-Teile — im Portal per Parametersuche wählen | ~35 | 1210-Kondensatoren (22u/47u/10u/100u-50V), E96-Widerstände (10k2, 39R, 53k6, 68k1, 88k7, 392k), Zener 5V6/12V/33V, SMBJ30A, 60V-3A-Schottky SMB, Shunts 5m0-2512, PTC + Sicherungen, SRP5030T-2R2M, Taster TL3342/SKRK/CVS-01, Buzzer PKMCS0909E |
| **Bewusst offene Entscheidungen** — erst entscheiden, dann Nummer | ~19 | Stapelverbinder 6× (Punkt 23), Q1-FET (Punkt 8), P-/N-FET SOT-23 2×, PhotoMOS-Typ, TLV3702 (bei LCSC nicht geführt), VL53L1X (nicht geführt), Micro-Fit 43045-1612 (nicht geführt — THT, zur Not von Hand) |

## 2c. Beschaffung neben LCSC — entschieden am 20.08.2026

**Mouser-Sammelbestellung (Handbestückung, alles gut lötbar):**

| Teil | Menge | Zweck |
|---|---|---|
| Vishay SIR4409DP-T1-GE3 | 1 (+1 Reserve) | Q1 Verpolschutz (PowerPAK SO-8) |
| TI TLV3702IDR | 2 (+2) | Fensterkomparatoren (SOIC-8) |
| E-Switch TL3342 | 2 | RESET/BOOT auf Mid (SMD, große Pads) |
| Molex 43045-1612 | 1 | Feldstecker (THT) |
| Molex 43025-1600 + 43030-Kontakte | 1 Satz | **Gegenstück** für den Kabelbaum in der Dose |
| JST GHR-02V-S + SSHL-002T-P0.2 | 2 Sätze | **Gegenstücke** für J6 (Stern) |

**JLC Global Sourcing (maschinell bestücken lassen):**
VL53L1CXV0FY/1 — LGA-Reflow, nicht handlötbar.

**Herstellerkatalog (Wayconn/Scondar/Samtec):**
Das Stapelverbinder-Paar nach Punkt 23: erhöhte 2×20-Buchse 1,27 mm
(H ≈ 8,5, Einstecktiefe ≥ 2,5) für Bottom/Top plus THT-Stiftleiste mit
beidseitigem Überstand ≥ 3 mm für Mid.

## 3. Ablauf im Portal

### Schritt 1 — Gerber hochladen
`switchstack_panel.zip` auf jlcpcb.com hochladen. Das Portal liest Maße und
Lagenzahl selbst aus. **Kontrollieren, dass es 4 Lagen erkennt** — erkennt es
2, fehlen die Innenlagen im ZIP, und das ist ein Fehler in den Exporteinstellungen,
kein Portalproblem.

### Schritt 2 — Optionen
| Feld | Wert | Warum |
|---|---|---|
| Layers | 4 | |
| PCB Thickness | 1,0 mm | Tiefenbudget, docs/04 |
| Surface Finish | ENIG | 0,65-mm-Raster am PCF8575, feine Pads |
| Outline Tolerance | ±0,2 mm | der Adapter hat 0,4 mm Spiel |
| **Panel** | „Panel by Customer" | **wichtig** — der Nutzen ist fertig, JLCPCB soll ihn nicht selbst panelisieren |
| Remove Order Number | „Specify a location" | sonst druckt das Portal seine Nummer irgendwohin |

### Schritt 3 — Bestückung (PCBA)
„Assemble your PCB boards" einschalten.

| Feld | Wert |
|---|---|
| PCBA Type | Economic reicht; Standard nur, falls Bauteile es verlangen |
| Assembly Side | **Both sides** — alle drei Boards sind beidseitig bestückt |
| Tooling holes | „Added by JLCPCB" **abwählen** — der Nutzen bringt eigene mit |

### Schritt 4 — BOM und CPL hochladen
`…-bom-jlcpcb.csv` als BOM, `…-cpl-jlcpcb.csv` als CPL. Beide sind bereits im
erwarteten Spaltenformat.

### Schritt 5 — Die Bauteilprüfung, und hier wird es ernst
Das Portal zeigt jede Position mit dem gefundenen Bauteil und einer Vorschau
der Drehlage. **Diesen Schritt nicht durchklicken.** Er ist der einzige, bei
dem Fehler noch nichts kosten.

## 4. Worauf du achten musst

### 4.1 LCSC-Nummern fehlen
`gen_assembly.py` meldet die Zahl der Positionen ohne LCSC-Nummer. Solange
die nicht null ist, sucht das Portal die Bauteile selbst aus — und trifft bei
Widerständen und Kondensatoren meist richtig, bei allem anderen nicht.

**Vorgehen:** Für jede Position ohne Nummer im LCSC-Katalog das Bauteil
suchen, Nummer notieren, in die BOM-Datei eintragen. Bei Widerständen und
Kondensatoren genügt: Wert, Bauform, Spannung, Toleranz.

### 4.2 Drehwinkel
**Das ist die häufigste Fehlerquelle bei JLCPCB.** Die Winkel in der
CPL-Datei stammen aus KiCad und beziehen sich auf KiCads Footprint. JLCPCB
rechnet gegen die Lage im eigenen Bauteilkatalog. Für zweipolige Bauteile
stimmt beides fast immer, für ICs, Dioden, Elkos und Steckverbinder oft nicht.

**Vorgehen:** In der Vorschau jedes gepolte Bauteil einzeln ansehen —
Pin 1 des ICs, Kathode der Diode, Plus des Elkos. Gegen
`…-bestueckung.pdf` halten. Falsch gedreht bestückte ICs sind
der klassische Weg, eine ganze Charge zu verlieren.

Besonders zu prüfen:
- **U1** ESP32-S3-WROOM (Mid) — die Antenne muss zur Frontkante zeigen
- **UM1_BR / UM2_BR** DRV8871 (Bottom) — Thermalpad und Pin 1
- **U2/U4** Buck-Regler (Bottom)
- die vier **Ecktaster** auf Top — Drehlage egal, Position kritisch
- **J1** Feldstecker (Bottom) — Codierung des Gehäuses

### 4.3 Durchsteckteile
Der Feldstecker, die Klinkenbuchse und die Stackverbinder sind THT. JLCPCB
bestückt die im Economic-Verfahren nicht automatisch; sie werden je nach
Auftrag von Hand gelötet oder gar nicht. **Vor der Bestellung klären**, ob
sie mitkommen — sonst lötest du sie selbst, was möglich, aber bei den
1,27-mm-Stackverbindern mühsam ist.

### 4.4 Was der Fertiger nicht prüft
- **ob die Bauteile zueinander passen** — die Netzliste ist geprüft, die
  Schaltung selbst hat nie ein Review gesehen (steht im Kopf jedes
  Schaltplan-Generators)
- **ob die Höhen ins Gehäuse passen** — dafür ist die STEP-Baugruppe da
- **ob die Drehwinkel stimmen** — er baut, was in der CPL steht

## 5. Stückzahlen

| Menge | wofür |
|---|---|
| **5** | erste Runde. Fehler kosten dann fünf Nutzen, nicht fünfundzwanzig |
| **25** | erst, wenn ein aufgebautes Gerät nachweislich läuft |

Jeder Nutzen ergibt drei Boards, ein Satz also ein Gerät. Fünf Nutzen sind
fünf Geräte.

## 6. Vor dem Absenden — die letzte Liste

- [ ] `gen_fab.py` läuft durch und schreibt das ZIP (DRC-Gate grün)
- [ ] Portal erkennt **4 Lagen**
- [ ] „Panel by Customer" gewählt, Tooling holes **nicht** von JLCPCB
- [ ] Assembly **beidseitig**
- [ ] **null** Positionen ohne LCSC-Nummer
- [ ] jedes gepolte Bauteil in der Vorschau gegen den Bestückungsplan geprüft
- [ ] geklärt, ob die Durchsteckteile mitbestückt werden
- [ ] Stückzahl **5**, nicht 25
