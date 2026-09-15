# 16 – Die letzten Handgriffe in KiCad

Der Autorouter ist fertig, ein paar Verbindungen bleiben. Diese Seite ist die
Anleitung dafür — kurz, weil es wenig ist.

> **Warum das übrig bleibt.** Freerouting löst rund 98 % und meldet dann
> selbst, es komme nicht weiter. Was übrig bleibt, sind fast immer Pads, die
> zwischen anderen Bauteilen eingeklemmt sind. Von Hand ist das jeweils ein
> Zug mit der Maus.

## 1. Was zu tun ist

Öffne jedes Board einzeln, **nicht den Nutzen** — der entsteht danach neu aus
den Einzelboards.

```
hardware/top_ui/top_ui.kicad_pro
hardware/mid_logic/mid_logic.kicad_pro
hardware/bottom_power_motor/bottom_power_motor.kicad_pro
```

Die verbindliche Liste liefert immer **Inspect → Design Rules Checker**,
Häkchen bei „Report all errors for each track" aus, dann **Run DRC**. Unter
`unconnected_items` steht jede offene Verbindung mit Koordinate.

Dasselbe ohne KiCad zu öffnen: `python3 tools/handarbeit_liste.py` läuft die
DRC über alle drei Boards und druckt jede offene Verbindung mit Netz,
Endpunkten, Koordinaten und Luftlinie. Nach jedem Speichern erneut aufrufen —
die Liste schrumpft mit.

## 2. Offene Verbindungen ziehen

1. **Ansicht aufräumen:** `Ansicht → Ratsnest anzeigen` einschalten. Die dünnen
   weißen Linien sind genau die offenen Verbindungen.
2. **Lagen einblenden:** Alle vier Kupferlagen sichtbar lassen. Der Router hat
   `In1.Cu` und `In2.Cu` benutzt, dort ist meistens noch Platz.
3. **Bahn ziehen:** Taste **X**, auf das Pad klicken, zum Ziel ziehen.
   Mit **V** wechselt man mitten im Zug die Lage und setzt automatisch ein Via.
4. **Nicht die Breite ändern.** Die Netzklassen stehen im Projekt; KiCad nimmt
   automatisch die richtige. Nur bei den Leistungsnetzen (`24V_IN`, `M1_A`,
   `M1_B`, `M2_A`, `M2_B`) darauf achten, dass die Bahn nicht schmaler wird
   als die vorhandene.

**Stand vom 15.09.2026** (nach dem Aufräumen, siehe Abschnitt 3):

| Board | offen | wo |
|---|---|---|
| **Top** | 5 | `3V3_SYS`, `I2C_SDA`, `I2C_SCL` — alle drei zu U2 an der Unterkante, 9–12 mm, als Bündel ziehen; `6V2_STAR_F` (Q2 Pad 2 → Bahn auf B.Cu, 5,4 mm); 1× `PGND` an J5 Pad 2 (0,3 mm — Bahn auf B.Cu, Pad auf F.Cu, es fehlt nur das Via) |
| **Mid** | 15 | `3V3_SYS` (2×), `RELAY_CTL` (zwei lose In1.Cu-Enden an der USB-Bohrung, außen herum führen), `USB_CC2` (R19 → J7 Pad B5, 7,5 mm), 11× `PGND` — davon 2 Zone-Inseln ohne Koordinate |
| **Bottom** | 26 | `24V_PROT` (2×, U2/U4 Pad 2 → Bahn bei (−4,05/−17,59) — Leistungspfad, breit), `3V3_SYS` (3×, UM1_FF/UM2_FF Pad 8, UM2_GB Pad 5), 21× `PGND` — davon 11 Zone-Inseln ohne Koordinate |

Fast alle `PGND`-Einträge mit Koordinate zeigen dasselbe Muster: Pad auf der
einen Lage, Bahn oder Pad auf der anderen, 1–4 mm auseinander — ein Via mit
kurzem Stich. Die Zone-Inseln haben in der DRC keine brauchbare Koordinate;
sie findet man nur über das Ratsnest nach **B**.

### `M1_ISNS` — inzwischen geroutet, die Lehre bleibt

Der Motorstrom-Messpfad von Motor 1 war auf Bottom eine Zeit lang mit
Absicht leer und ist inzwischen verdrahtet. Die Geschichte bleibt hier
stehen, weil die `3V3_SYS`-Reste bei UM1_FF/UM2_FF in derselben Ecke liegen
und dort dieselbe Regel gilt: Der Router hatte `M1_ISNS` geroutet, und zwar
falsch.

Freerouting hat `M1_ISNS` auf F.Cu direkt an `V_TRIP_LO` gepresst, auf
engstem Raum um (1,2–1,7 / 5,3–6,2). Ergebnis waren vier Kurzschlüsse, eine
Kreuzung und ein Abstandsfehler. Einzeln herausgelöste Segmente haben das
Problem nur verschoben: Nach jedem Eingriff meldete die DRC dieselben zwei
Netze an der nächsten Stelle.

Sachlich ist die Paarung ohnehin die schlechtestmögliche. `M1_ISNS` ist das
analoge Messsignal des Motorstroms, `V_TRIP_LO` die Vergleichsschwelle, gegen
die es ausgewertet wird. Koppeln die beiden, verschiebt sich die
Auslöseschwelle mit dem gemessenen Strom — die Hinderniserkennung würde sich
selbst verstimmen, und zwar ohne dass eine DRC das je bemerkt.

**Wer in dieser Ecke Hand anlegt, hält deshalb ein:**

- `M1_ISNS` mit **spürbarem Abstand** zu `V_TRIP_LO` führen, gern über eine
  andere Lage. Nicht parallel über längere Strecken.
- Zwischen beiden möglichst Massefläche stehen lassen.
- Kurz halten: vom Shunt `R_M1_SH` zum Messverstärker, nicht quer über das
  Board.

Bei Motor 2 hat der Router dieselbe Ecke ohne Fehler gelöst — `M2_ISNS` zeigt
also, dass dort ein Weg existiert. Als Vorbild taugt es aber nur für die
Wegführung, nicht für die Länge: Die Bahn ist 70,9 mm lang und läuft damit
weiter über das Board, als einem Messsignal guttut. Wer ohnehin gerade von
Hand routet, darf auch `M2_ISNS` gern kürzen.

## 2b. Via-Engpässe von Hand entschärfen (20.08.2026)

`tools/via_check.py` prüft nach jedem Routing, ob jedes Via den Dauerstrom
seines Netzes trägt (4 A je mm Bohrung; Vias im 3-mm-Umkreis zählen
parallel). `--fix` setzt Zwillinge — wo kein Platz war, bleibt Handarbeit.
Der Weg ist immer derselbe: eine Signalbahn im Umkreis um 1–2 mm verlegen,
dann ein zweites Via 0,8/0,4 neben das gemeldete setzen.

Stand 15.09.2026 (`via_check.py` mit KiCads Python, s. u.):

| Board | Netz | Stelle | trägt / braucht |
|---|---|---|---|
| Bottom | `24V_PROT` | (−2,5/20,0), (−11,2/−1,1), (8,1/−1,5) | 1,6 / 4,1 A |
| Bottom | `5V_BUCK` | (−6,7/−16,7) | 1,6 / 2,0 A |
| Bottom | `5V_SYS` | (−16,6/−4,3), (−16,6/−18,4) | 1,6 / 2,0 A |
| Bottom | `PGND` | (−9,0/14,7), (−1,6/−8,6) | 1,6 / 4,1 A |
| Bottom | `PGND` | (−5,8/−4,6) | 3,2 / 4,1 A |
| Mid | `PGND` | (5,8/2,6) | 1,2 / 1,5 A |

Vier Einträge sind gegenüber dem 20.08. neu, und zwar zu Recht: Auf Bottom
lagen zwei Vias exakt übereinander bei (−5,85/−4,64), zwei weitere saßen
0,0 und 0,22 mm neben dem Lötauge von J1 (so nicht bohrbar), und das
`5V_SYS`-Via bei (−16,0/−17,8) hing nur auf einer Lage. `via_check` hatte
sie alle als tragende Parallel-Vias gezählt. Sie sind am 15.09. entfernt;
was die Liste jetzt nennt, fehlt wirklich. Zwei Anmerkungen: Bei
(−9,0/14,7) sitzt direkt daneben das Durchsteck-Lötauge J1 Pad 2 (`PGND`),
das die Lagen selbst verbindet und das `via_check` nicht mitrechnet — ein
Zwilling mit sauberem Lochabstand schadet trotzdem nicht. Bei (−1,6/−8,6)
hat `rest_schliessen` eine Masseverbindung geschlossen, mit einem Via, das
nun einen Zwilling braucht.

Einordnung: 4,1 A ist der rechnerische Grenzfall (beide Motoren blockiert
plus Volllast); der reale Dauerstrom liegt bei ~2,3 A. Die Liste ist also
Pflicht vor der Bestellung, aber kein Grund zur Panik.

## 3. Masse-Inseln schließen

Unter `unconnected_items` stehen auch Einträge mit `PGND`. Das sind Pads, die
die Massefläche nicht erreicht.

- **Meist genügt ein Via:** Taste **V** neben dem Pad, dann eine kurze Bahn
  vom Pad zum Via. Das Via verbindet sich mit der Fläche der anderen Lage von
  selbst.
- **Was `tools/rest_schliessen.py` liegen lässt**, braucht einen Umweg:
  erst eine kurze Bahn vom Pad weg, dann das Via. Das Skript ist am
  15.09.2026 neu geschrieben: Es behält nur, was die Zahl der offenen
  Verbindungen seines Netzes nachweislich senkt, und setzt kein Via mehr auf
  eine vorhandene Bohrung. Sein Vorgänger hatte genau das getan — sechs
  Vias übereinander bei (−21,0/−9,1) auf Mid, dazu Dutzende doppelte und
  0-mm-Segmente auf allen drei Boards; alles am 15.09. entfernt. Es
  schließt ehrlich wenig (Bottom 28 → 26, sonst nichts), macht aber nichts
  kaputt. Aufruf wie alle `pcbnew`-Werkzeuge mit KiCads eigenem Python:

  ```
  /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3 tools/rest_schliessen.py
  ```

- **`gnd_stitch.py` und `gnd_connect.py` nicht verwenden.** Beide haben am
  15.09. auf Bottom und auf Mid je einen Kurzschluss (`shorting_items`)
  gesetzt und als sauber gespeichert, weil ihr DRC-Aufruf `kicad-cli` ohne
  Pfad suchte, auf dem Mac nichts fand und ein leeres Ergebnis bekam.
  `run_drc` in `gen_layouts.py` bricht seit dem 15.09. laut ab, statt leer
  zurückzugeben — die Kurzschluss-Neigung selbst ist damit nicht behoben.

## 4. Danach — und das ist wichtig

1. **Zonen füllen:** Taste **B**. Ohne das meldet die DRC jede Masseverbindung
   als offen, und man sucht Fehler, die keine sind.
2. **DRC erneut laufen lassen.** Ziel: `unconnected_items` **null**,
   `clearance` **null**. Meldungen zu `silk_*` sind Bestückungsdruck und
   dürfen bleiben.
3. **Speichern.**

## 5. Wenn alle drei sauber sind

```bash
python3 tools/gen_panel.py       # Nutzen neu aus den drei Boards
python3 tools/gen_fab.py         # Gerber, Bohrdaten, ZIP - nur wenn DRC grün
python3 tools/gen_assembly.py    # Stückliste, Bestückungsdatei, Plan
python3 mechanical/stack.py      # 3D-Baugruppe zur Kontrolle
```

`gen_fab.py` hat ein eingebautes Gate: Solange eine Verbindung offen ist,
schreibt es **keine** Fertigungsdaten. Wenn es ein ZIP herausgibt, bist du
fertig — dann weiter mit [`15-bestellung.md`](15-bestellung.md).

## 6. Zwei Dinge, die du nicht anfassen solltest

**Bauteile verschieben.** Die Positionen kommen aus `tools/gen_layouts.py`
und sind gegen Zentralscheibe, Adapter und Tiefenbudget gerechnet. Wer in
KiCad schiebt, verliert das beim nächsten Neuerzeugen — und merkt es
womöglich erst am gedruckten Adapter.

**Die Regeln lockern.** 0,15 mm Abstand und ein Wärmefallensteg sind bewusst
gesetzt (docs/05). Wenn die DRC meckert, ist die Bahn falsch, nicht die Regel.
