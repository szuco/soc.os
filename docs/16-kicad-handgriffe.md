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

**Stand vom 18.08.2026 als Anhaltspunkt:**

| Board | offen | wo |
|---|---|---|
| **Top** | 3 Signale | alle drei am Raumsensor **U2** (SHT40) bei (3,5 / −19): Pin 1 `I2C_SDA`, Pin 2 `I2C_SCL`, Pin 3 `3V3_SYS`. Das Bauteil ist gerade dorthin gewandert, der Router kam zwischen ToF und Ecktaster nicht mehr heraus |
| **Mid** | 3 Signale | `3V3_SYS`, `QSPI_D3`, `USB_DP_C`, dazu 12 Masse-Inseln |
| **Bottom** | 7 Signale | `3V3_SYS` (3×), `24V_PROT` (2×), `5V_SYS`, `24V_EN`, dazu 10 Masse-Inseln |

## 3. Masse-Inseln schließen

Unter `unconnected_items` stehen auch Einträge mit `PGND`. Das sind Pads, die
die Massefläche nicht erreicht.

- **Meist genügt ein Via:** Taste **V** neben dem Pad, dann eine kurze Bahn
  vom Pad zum Via. Das Via verbindet sich mit der Fläche der anderen Lage von
  selbst.
- **Ausnahme Klinkenbuchse J6 auf Top:** Ihr Schirmpad ragt absichtlich über
  die Boardkante. Dort geht kein Via — eine kurze Bahn nach innen zur Fläche.

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
