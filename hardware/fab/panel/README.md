# Fertigungsnutzen

> **Gemischte Geometrie seit dem 16.08.2026.** Bottom und Mid sind Kreise
> Ø 52, das Top-Board ist ein abgerundetes Quadrat 47 × 47 (Punkt 48). Der
> Generator behandelt beide Formen: die Kreise über die Bogenlogik, das Quadrat
> über eine Parallelkurve seiner Kontur. **173,4 × 64,4 mm = 112 cm²**, vier
> Stege je Platine.

`switchstack_panel.kicad_pcb` enthält alle drei Platinen in einer Datei —
Bottom, Mid und Top nebeneinander, gehalten von Trennstegen in einem Rahmen.

> **Erzeugt, nicht gezeichnet.** Diese Datei ist ein Build-Ergebnis wie die
> Gerber. Sie wird nie von Hand bearbeitet, sondern neu erzeugt:
>
> ```bash
> /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3 \
>     tools/gen_panel.py
> ```
>
> Änderungen gehören in die drei Quellprojekte unter `hardware/`. Der Nutzen
> greift beim nächsten Lauf darauf zu.

## Warum überhaupt ein Nutzen

KiCad kennt nur ein Board je Projekt — das Handbuch zu 10.0 ist da eindeutig:
*„a project can only contain a single board."* Wer die drei Platinen in einer
Datei will, hat zwei Möglichkeiten: die Quellen verschmelzen, oder einen Nutzen
erzeugen. Das Verschmelzen kostet die Referenzbezeichner (alles müsste ein
Präfix bekommen) und die Möglichkeit, ein Board allein zu revidieren. Der
erzeugte Nutzen kostet nichts davon: Bauteil- und Netznamen bekommen ihr Präfix
erst hier drin, wo Eindeutigkeit gefordert ist.

| Ebene | Präfix Referenz | Präfix Netz |
|---|---|---|
| Bottom | `B_` | `BOT_` |
| Mid | `M_` | `MID_` |
| Top | `T_` | `TOP_` |

## Geometrie

| | |
|---|---|
| Nutzengröße | **178,4 × 64,4 mm** (115 cm²) |
| Anordnung | drei Kreise Ø 52,0 in einer Reihe, Teilung 57,0 mm |
| Fräsfuge | 2,2 mm (Fräser 2,0 mm plus Toleranz) |
| Rahmen | 4,0 mm ringsum |
| Stege | 4 je Platine, 4,0 mm breit, auf den Diagonalen |
| Mausbisse | 5 × Ø 0,6 mm je Steg, 0,45 mm außerhalb der Platinenkante |

Die Reihe ist die flächengünstigste Anordnung: 115 cm² gegenüber 129 cm² beim
Dreieck (zwei oben, eine unten). Unter 100 × 100 mm ist nichts zu holen — drei
Kreise Ø 52 brauchen mathematisch mindestens ein Quadrat von 102 mm
Kantenlänge, und das ohne jede Trennfuge.

Die Stege liegen auf den **Diagonalen**, weil alle vier Achsrichtungen belegt
sind: 0° und 180° sind die Befestigungsbohrungen, 90° ist beim Top-Board der
überstehende USB-C-Stecker, 270° beim Mid-Board der Antennen-Keepout.

## Trennen — das ist Handarbeit

Runde Platinen lassen sich nicht ritzen. Nach dem Ausbrechen steht am Steg ein
Grat von etwa **0,5 mm** über. Der muss verputzt werden, bevor die Platine in
die Dose geht: Ø 52 in einer Dose mit 55–57 mm lichter Weite lässt 1,5–2,5 mm
Luft, ein unbearbeiteter Nub kann davon die Hälfte fressen.

Die Perforation liegt bewusst **außerhalb** der Platinenkante. Genau auf der
Kante würde jede Bohrung in den Randabstand des Kupfers ragen — das waren im
ersten Entwurf 480 zusätzliche Clearance-Fehler. Der Preis dafür ist genau
dieser Grat.

## Designregeln

Ohne eigene Projektdatei fiele der Nutzen auf KiCads Standardwerte zurück und
meldete Fehler, die keine sind — das Bottom-Board ist mit 0,15 mm Clearance
geroutet, die Vorgabe lautet 0,2 mm. `gen_panel.py` erzeugt deshalb auch
`switchstack_panel.kicad_pro` und überträgt die Regeln aus den drei
Quellprojekten: jede Ebene behält über ein Netzklassenmuster (`BOT_*`, `MID_*`,
`TOP_*`) ihre eigenen Werte, die Mindestvorgaben werden zur durchlässigsten
Variante zusammengefasst.

## Stand der Prüfung

Neu erzeugt am 15.08.2026, nachdem das Top-Board umgebaut wurde (Klinke auf
6 Uhr, ToF auf 12 Uhr, USB-C-Drehung korrigiert). Der DRC des Nutzens ist
**deckungsgleich mit der Summe der Einzelboards**:

| Klasse | Anzahl | Was dahintersteckt |
|---|---:|---|
| `clearance` | 28 | Pad-zu-Pad **innerhalb** des USB-C-Footprints: 0,85 mm Raster gegen 0,15 mm Vorgabe. Eine Regel-gegen-Footprint-Frage, kein Layoutfehler |
| `copper_edge_clearance` | 2 | Platzhalter-Footprint der Klinkenbuchse (Punkt 30) |
| `unconnected_items` | 342 | erwartet: **Mid und Top tragen keine Leiterbahnen**, Bottom ist zu ≈ 85 % geroutet, und die Masseflächen werden erst beim Öffnen in KiCad gefüllt |

Was der Nutzen **zusätzlich** meldet, sind Silkscreen-Überlappungen: durch die
Präfixe werden die Bezeichner länger. Das ist kosmetisch und betrifft keine
Kupferlage.

**Vor der Bestellung:** Mid und Top routen, Masseflächen füllen, DRC auf null
Kupferfehler bringen und die Fertigungsanweisung um das Verputzen der Stege
ergänzen.
