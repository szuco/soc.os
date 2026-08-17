# 05 – Fertigung

## 1. Lagenaufbau

| Board | Lagen | Kupfer | Begründung |
|---|---|---|---|
| BOTTOM | 2 oder 4 | **1 oz genügt** | Summenstrom ≈ 3,9 A im ungünstigsten Fall — seit der Blockierstrommessung vom 17.08.2026, siehe [`11-motor-data.md`](11-motor-data.md). Die vorhandenen breiten Bahnen bleiben, schaden nicht und kosten nichts |
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
| `24V_IN+` / `24V_IN−` | ≈ 3,9 A Spitze, 1,7 A im Fahrbetrieb | Summenpfad beider Motoren; weiterhin der stärkste Pfad, aber unkritisch |
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

## 5. Routing-Stand und Restarbeiten (2026-08-15)

| Board | Segmente im Repository | Stand |
|---|---:|---|
| **BOTTOM** | **985** (102 Vias) | ≈ 85 % geroutet, 0 Kupferfehler. Offen sind 43 Verbindungen im Motor-/Leistungsteil (SW-Knoten, Gate-Netze, `24V_PROT`). Der Autorouter konvergiert dort nicht mehr — die Leistungspfade sind laut Prüfliste (Abschnitt 3) **ohnehin von Hand zu ziehen**. |
| **MID** | **746** (104 Vias) | Am 16.08.2026 im Container geroutet. Offen: 59 Masseanbindungen (schließt die Zonenfüllung) und **18 Signalverbindungen** auf 16 Netzen. Dazu **fünf Kupferfehler, alle an derselben Stelle**: `HOOD_B` kreuzt `RELAY_LED` bei (12,2 / 19,2), also am PhotoMOS. |
| **TOP** | **197** (12 Vias) | Am 16.08.2026 im Container geroutet. Offen: 57 Masseanbindungen (schließt die Zonenfüllung) und **14 Signale** — darunter `BTN1`–`BTN4` vollständig sowie `USB_VBUS` (3×), `USB_DP_C` (2×) und `USB_CC2`. Der Router hat zusätzlich **eine Bahn (`STAR_OUT`, B.Cu) durch das Befestigungsloch der USB-Buchse gelegt** — zwei DRC-Meldungen aus derselben Ursache. |

> **Korrektur vom 15.08.2026.** Hier stand, Top sei vollständig und Mid bis auf
> zehn Masseanbindungen geroutet. Das galt für einen Arbeitsstand, der nie im
> Repository landete: Der Umbau vom 15.08. (Reed-Kontakte, Haubenkontakt,
> Klinkenbuchse, ToF) hat die Layouts von Mid und Top **neu erzeugt** und dabei
> deren Verdrahtung verworfen — `grep -c '(segment'` zählt in beiden Boarddateien
> null. Nur das Bottom-Board trägt Leiterbahnen. Die Angaben in der Nutzen-
> Dokumentation („Mid und Top sind platziert, aber noch nicht geroutet") waren
> die richtigen.

### Freerouting 2.3.0 geprüft — und wieder verworfen

Am 17.08.2026 gegen 1.9.0 gemessen, an derselben DSN des Top-Boards, importiert
in dieselbe Ausgangsplatine, DRC mit denselben Regeln:

| | Segmente | unconnected | Verletzungen |
|---|---:|---:|---|
| **1.9.0** | 197 | **71** | 5 (davon 3 bekannt und gewollt) |
| 2.3.0 | 214 | 74 | **26** — darunter 9 `via_dangling` und 5 `track_width` |

Beeindruckend ist sie trotzdem: neun Threads statt einem, eine **Fanout-Stufe**,
die die SMD-Pads erst ausfädelt, und ein Fortschrittslog mit Score je Durchgang.
Der ganze Lauf dauerte zwei Minuten statt vierzig.

Nur taugt das Ergebnis nicht. Zwei Befunde:

1. **Sie speichert nicht ihr bestes Ergebnis.** Das Log zeigt es wörtlich: Die
   Routing-Stufe endet mit *19 unrouted*, die Optimierung startet auf einem
   Board mit *22 unrouted* und speichert genau das. Das ist derselbe Fehler,
   wegen dem schon 2.1.0 verworfen wurde — nach einem Jahr unverändert.
2. **Sie hält die Netzklassen nicht ein.** Fünf `track_width`-Verletzungen und
   neun freistehende Vias sind kein Randproblem, sondern zeigen, dass die
   Regeln aus der DSN nicht durchgesetzt werden.

Der Test bleibt reproduzierbar: `tools/freerouting.Dockerfile` nimmt
`--build-arg FREEROUTING_VERSION` und `--build-arg JRE_TAG` (2.3.0 verlangt
Java 25, 1.9.0 läuft auf 21). Wenn eine spätere Version erscheint, ist der
Vergleich eine Viertelstunde Arbeit.

### Bottom: der frische Lauf war schlechter, der alte Stand bleibt

Am 17.08.2026 wurde das Bottom-Board auf ausdrücklichen Wunsch neu geroutet,
obwohl davon abgeraten war. Das Ergebnis bestätigt den Einwand:

| | Segmente | Vias | offene Verbindungen | Kupferfehler |
|---|---:|---:|---:|---:|
| **alter Stand** | **985** | 102 | 61 | **0** |
| frischer Lauf | 835 | 89 | 78 | **602** |

Der neue Lauf ist auf jeder Achse schlechter — weniger Verdrahtung, mehr
offene Verbindungen, und 503 Abstands- plus 99 Bohrungsverletzungen, wo vorher
keine einzige war. **Der alte Stand ist wiederhergestellt** (er lag ohnehin im
Git), der neue liegt zum Nachsehen im Scratchpad.

Der Grund ist kein Zufall und kein Fehler des Containers: Der 985er-Stand ist
laut Git-Historie **das ausgewählte beste Ergebnis aus mehreren Anläufen**
(„Fortsetzungsstand übernommen", „frischer Lauf gestartet", „bester
Routing-Stand übernommen"). Ein einzelner frischer Lauf kann das nicht
zuverlässig schlagen — Freerouting ist nicht deterministisch gut.

> **Methodenfehler, der dabei fast durchgegangen wäre:** Der erste Vergleich
> maß den alten Stand als Kopie *außerhalb* seines Projektverzeichnisses. Ohne
> `.kicad_pro` fällt `kicad-cli drc` auf KiCads Standardregeln zurück — 0,2 mm
> statt der hier gültigen 0,15 mm — und meldete 508 Verletzungen für ein Board,
> das in Wahrheit keine hat. **Ein DRC-Vergleich ist nur im Projektverzeichnis
> gültig.**

### Was der Mid-Lauf gezeigt hat

Der frühere Lauf unter Linux endete mit 655 Segmenten, 73 Vias und **null**
offenen Signalverbindungen. Der Lauf vom 16.08.2026 kommt auf 746 Segmente,
104 Vias — aber 18 offene Signale und fünf Kupferfehler. Das Board ist in der
Zwischenzeit dichter geworden: 46 statt 39 Bauteile, 61 statt 57 Netze, der
Expander auf der Rückseite und vier Reed-Netzwerke statt zwei.

Die Kupferfehler sind **nicht verstreut**: Alle fünf betreffen dasselbe
Netzpaar an derselben Stelle. Das ist eine lokale Reparatur, kein neuer Lauf.

> **Der Kurzschluss bleibt bewusst im Board stehen.** Ihn automatisch
> herauszuschneiden hieße, Leiterbahnen zu löschen, ohne zu wissen welche —
> und ein stillschweigend entfernter Fehler ist schlimmer als ein sichtbarer.
> Das DRC-Gate von `gen_fab.py` verhindert, dass daraus versehentlich
> Fertigungsdaten entstehen.

### Routing auf macOS: der Container

Freerouting 1.9.0 ist keine echte Konsolenanwendung — es instanziiert
AWT-Klassen auch im Batchbetrieb und braucht deshalb ein X-Display. Unter Linux
löst das `xvfb-run`; auf macOS gibt es kein Xvfb. Dafür gibt es jetzt
[`../tools/freerouting.Dockerfile`](../tools/freerouting.Dockerfile) — eine JRE,
Xvfb und das Jar, sonst nichts:

```bash
docker build -f tools/freerouting.Dockerfile -t switchstack-freerouting tools/
python3 tools/route_boards.py mid
```

`route_boards.py` wählt selbst: Liegt ein lokales Jar **und** `xvfb-run` vor,
läuft es wie bisher direkt; sonst nimmt es den Container und schreibt die Pfade
auf dessen Sicht um. Der Rest der Pipeline — DSN-Export und SES-Import — läuft
über die `pcbnew`-API und braucht keinen Container.

**Erfahrungswerte aus der Automatisierung, die weiter gelten:**

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

**Aktuell existieren keine Fertigungsdaten.** Der frühere Export
`hardware/fab/top_ui.zip` ist am 15.08.2026 gelöscht worden: Er enthielt die um
180° verdrehte USB-C-Buchse (Punkt 39) und passte auch sonst nicht mehr zum
Board. Neue Daten entstehen erst nach dem Routing — das DRC-Gate von
`gen_fab.py` lässt nichts anderes zu.

**Die 28 `clearance`-Meldungen des Top-Boards gehören nicht dazu.** Sie sind
Pad-zu-Pad-Abstände **innerhalb** des USB-C-Footprints: 0,85 mm Rasterteilung
gegen die Vorgabe von 0,15 mm Kupferabstand. Das ist eine Regel-gegen-Footprint-
Frage (lokale Regelausnahme oder anderer Verbinder), kein Layoutfehler, und sie
bestand vor und nach der Drehungskorrektur unverändert. Was die Korrektur
tatsächlich beseitigt hat: **11 → 1** Randabstandsverletzungen. Die eine
verbliebene ist der Platzhalter-Footprint der Klinkenbuchse (Punkt 30).

Die Stücklisten aller drei Boards liegen als `bom_bottom/mid/top.csv`
neben den Schaltplänen — erzeugt aus derselben Quelle wie die Schaltpläne
selbst (`tools/gen_*_sch.py`).

## Fertigungsnutzen

Die drei Platinen werden als **ein Nutzen** bestellt:
[`../hardware/fab/panel/`](../hardware/fab/panel/README.md), erzeugt mit
`tools/gen_panel.py`. **173,4 × 64,4 mm = 112 cm²**, gemischte Geometrie: zwei
Kreise Ø 52 (Bottom, Mid) und ein abgerundetes Quadrat 47 × 47 (Top). Je vier
Stege von 4 mm mit fünf Mausbissen — am Kreis auf den Diagonalen, am Quadrat je
einer pro Kante, um 10 mm aus der Kantenmitte versetzt. Mittig wäre dort
entweder eine Befestigungsbohrung oder der überstehende Klinken-Platzhalter.

Der Nutzen ist ein **Build-Ergebnis**, keine Quelle. Die drei Projekte unter
`hardware/` bleiben führend und einzeln revidierbar; erst im Nutzen bekommen
Referenzen (`B_`, `M_`, `T_`) und Netze (`BOT_`, `MID_`, `TOP_`) ein Präfix,
weil beides dort eindeutig sein muss. Die Designregeln werden aus den drei
Quellprojekten übernommen, sonst meldet KiCad die 0,15-mm-Leiterbahnen des
Bottom-Boards gegen seine 0,2-mm-Vorgabe als Fehler.

**Nach dem Ausbrechen ist jede Platine am Steg zu verputzen** — der Grat steht
rund 0,5 mm über, und in der Dose stehen nur 1,5–2,5 mm Luft zur Verfügung.
