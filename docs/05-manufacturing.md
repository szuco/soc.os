# 05 – Fertigung

## 1. Lagenaufbau

| Board | Lagen | Kupfer | Begründung |
|---|---|---|---|
| BOTTOM | 2 oder 4 | **2 oz außen prüfen** | Motorströme bis ≈ 9 A, breite Leiterbahnen nötig |
| MID | 4 empfohlen | 1 oz | ESP32-Routingdichte, durchgehende GND-Referenz |
| TOP | 2 ausreichend | 1 oz | wenig Strom, geringe Dichte |

Alle drei Boards: **1,0 mm Dicke**, Ø 55,0 mm.

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
