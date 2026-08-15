# 05 – Fertigung

## 1. Lagenaufbau

| Board | Lagen | Kupfer | Begründung |
|---|---|---|---|
| BOTTOM | 2 oder 4 | **2 oz außen prüfen** | Motorströme bis ≈ 9 A, breite Leiterbahnen nötig |
| MID | 4 empfohlen | 1 oz | ESP32-Routingdichte, durchgehende GND-Referenz |
| TOP | 2 ausreichend | 1 oz | wenig Strom, geringe Dichte |

Alle drei Boards: **1,0 mm Dicke**, Ø 52,0 mm.

Bei 1,0 mm Gesamtdicke und vier Lagen wird der dielektrische Abstand dünn — das ist
herstellbar, aber der konkrete Stackup ist beim Fertiger zu bestätigen, bevor
Impedanz- oder Isolationsannahmen darauf aufgebaut werden.

Für das Bottom-Board gilt: 2 oz Kupfer erlaubt bei gleicher Erwärmung deutlich
schmalere Leiterbahnen als 1 oz, kostet aber Aufpreis und vergrößert die minimalen
Strukturbreiten. Ob es nötig ist, entscheidet die Leiterbahnstromrechnung nach dem
Placement — nicht vorab.

## 2. Leiterbahnauslegung

Für jeden Hochstrompfad ist die Breite gegen den realen Strom zu rechnen, nicht zu
schätzen. Zu prüfende Netze auf dem Bottom-Board:

| Netz | Strom | Bemerkung |
|---|---|---|
| `24V_IN+` / `24V_IN−` | ≈ 9 A nominal | Summenpfad beider Motoren, kritischster Pfad |
| `M1_A` / `M1_B` | ≈ 4,17 A nominal, Peak offen | je ein Motor |
| `M2_A` / `M2_B` | ≈ 4,17 A nominal, Peak offen | je ein Motor |
| Shunt-Rückpfad | wie Motorzweig | Kelvin-Abgriff nicht in den Strompfad legen |

Regeln:

- Motorstromschleifen kurz und breit halten, Hin- und Rückpfad möglichst übereinander.
- Vias in Hochstrompfaden ausreichend dimensionieren und **mehrfach** setzen.
- Thermische Betrachtung im geschlossenen Gehäuse ohne Luftstrom — die üblichen
  Leiterbahn-Rechner setzen freie Konvektion voraus und sind hier optimistisch.
  Konservativ auslegen.

## 3. Prüfungen vor Fertigungsfreigabe

Pro Projekt abzuarbeiten:

- [ ] **ERC** sauber, verbleibende Meldungen einzeln begründet
- [ ] **DRC** sauber, inklusive Kupfer-zu-Rand-Abstand am Kreisrand
- [ ] Leiterbahnbreiten gegen Strom gerechnet (Abschnitt 2)
- [ ] Thermische Betrachtung der Endstufen und DC/DC-Wandler
- [ ] Alle drei Boards: Bohrbild und Stackverbinder deckungsgleich
  (Koordinaten aus [`04-mechanical.md`](04-mechanical.md))
- [ ] Tiefenbudget mit realen Bauteilhöhen nachgerechnet
- [ ] Steckverbinder-Stromrating gegen Datenblatt bestätigt
- [ ] Antennen-Keepout auf allen Lagen frei
- [ ] Buck-Layouts gegen Hersteller-Referenzlayout verglichen
- [ ] 3D-Ansicht: keine mechanischen Kollisionen im gestapelten Zustand

## 4. Fertigungsdaten

Ausgabe pro Projekt nach `<projekt>/production/`. Dieses Verzeichnis ist in
`.gitignore` ausgenommen — Fertigungsstände werden **bewusst und getaggt** eingecheckt
(`git add -f`), nicht bei jedem Zwischenstand.

Umfang eines Fertigungsstands:

- Gerber (Protel- oder X2-Format nach Fertigervorgabe)
- Excellon-Bohrdaten
- IPC-356-Netzliste für den elektrischen Test
- BOM (CSV) mit Herstellerteilenummern
- Pick-and-Place-Datei
- PDF-Plots von Schaltplan und Assembly-Zeichnung
- README mit Fertiger, Datum, Git-Commit und Stackup-Vorgabe

Empfehlung: pro Fertigungsstand ein Git-Tag der Form
`bottom-v0.1`, `mid-v0.1`, `top-v0.1`, damit der gefertigte Stand später eindeutig
rekonstruierbar ist.

## 5. Routing-Stand und Restarbeiten (2026-08-14)

Alle drei Boards sind mit der Freerouting-Pipeline geroutet
(`tools/route_boards.py`, Nacharbeit mit `tools/gnd_*.py`); die Zonen sind
gefüllt (Vollanbindung, Zonen-Clearance 0,15 mm). Der Stand im Einzelnen:

| Board | Stand | Rest |
|---|---|---|
| **TOP** | vollständig, Kupfer-DRC sauber | — (Randabstands-Waiver: USB-Zunge, Pads ragen gewollt über die Kante) |
| **MID** | alle Signalnetze verbunden | **10 PGND-Pour-Anbindungen**: Massepins der Stackverbinder hinter eng geführten Signal-Verticals. In KiCad 9 mit dem interaktiven Router (Push-and-Shove) in ~10 min zu schließen — die DRC-Liste (`unconnected_items`) zeigt die Stellen. |
| **BOTTOM** | ≈ 85 % geroutet (985 Segmente, 102 Vias) | 43 Verbindungen im Motor-/Leistungsteil (SW-Knoten, Gate-Netze, 24V_PROT). Der Autorouter konvergiert dort nicht mehr — die Leistungspfade sind laut Prüfliste (Abschnitt 3) **ohnehin von Hand zu ziehen**: kurze dicke Wege, Buck-Schleifen nach Referenzlayout. |

**Wichtige Erfahrungswerte aus der Automatisierung** (Details in den
Werkzeug-Docstrings):

- Freerouting 2.1.0 headless ist unbrauchbar (SES vom falschen Stand);
  1.9.0 unter `xvfb-run` funktioniert zuverlässig.
- `ZONE_FILLER` braucht ein X-Display; headless stürzt er ab.
- Ein baumelndes Bahnende verbindet sich **nie** mit einer Zone — die
  Füllung hält auch um Endkappen Abstand. Zonen verbinden nur Pads
  (Anbindungsmodus) und Vias.
- Nach `SaveBoard()` ist das Board-Objekt in der SWIG-API instabil —
  erst speichern, dann für weitere Schritte neu laden.

## 6. Erzeugte Fertigungsdaten

`python3 tools/gen_fab.py [bottom|mid|top]` erzeugt je Board Gerber
(9 Lagen), Excellon-Bohrdaten mit PDF-Karte und CSV-Positionsdatei und
packt sie nach `hardware/fab/<board>.zip` — aber **nur, wenn das DRC-Gate
besteht** (keine Kupferfehler, keine offenen Verbindungen).

Aktuell erzeugt: **`hardware/fab/top_ui.zip`**. Mid und Bottom folgen,
sobald ihre Restarbeiten (oben) erledigt sind.

Die Stücklisten aller drei Boards liegen als `bom_bottom/mid/top.csv`
neben den Schaltplänen — erzeugt aus derselben Quelle wie die Schaltpläne
selbst (`tools/gen_*_sch.py`).

## Fertigungsnutzen

Die drei Platinen werden als **ein Nutzen** bestellt:
[`../hardware/fab/panel/`](../hardware/fab/panel/README.md), erzeugt mit
`tools/gen_panel.py`. 178,4 × 64,4 mm, drei Kreise Ø 52 in einer Reihe, je vier
Stege von 4 mm auf den Diagonalen mit Mausbissen.

Der Nutzen ist ein **Build-Ergebnis**, keine Quelle. Die drei Projekte unter
`hardware/` bleiben führend und einzeln revidierbar; erst im Nutzen bekommen
Referenzen (`B_`, `M_`, `T_`) und Netze (`BOT_`, `MID_`, `TOP_`) ein Präfix,
weil beides dort eindeutig sein muss. Die Designregeln werden aus den drei
Quellprojekten übernommen, sonst meldet KiCad die 0,15-mm-Leiterbahnen des
Bottom-Boards gegen seine 0,2-mm-Vorgabe als Fehler.

**Nach dem Ausbrechen ist jede Platine am Steg zu verputzen** — der Grat steht
rund 0,5 mm über, und in der Dose stehen nur 1,5–2,5 mm Luft zur Verfügung.
