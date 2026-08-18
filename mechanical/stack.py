#!/usr/bin/env python3
"""
SwitchStack - der komplette Stapel als eine STEP-Baugruppe.

    python3 mechanical/stack.py

Setzt die drei von KiCad exportierten Boards und den gedruckten Adapter auf
ihre tatsaechlichen Hoehen und schreibt das Ergebnis nach
mechanical/export/switchstack_stack.step.

WOZU
----
Die Einzelteile sind alle geprueft, ihr Zusammenspiel bisher nur gerechnet.
Erst die Baugruppe zeigt, ob die Bauteilhoehen wirklich aufgehen - vor allem
die USB-C-Buchse, die vom Mid-Board durch die Randkerbe des Top-Boards
greift, und der Leistungsstecker, der nach hinten aus der Dose ragt.

DIE HOEHENKETTE
---------------
Nullpunkt ist die Vorderseite des BOTTOM-Boards; z waechst nach vorn, zur
Zentralscheibe hin. Aus docs/04, Abschnitt 4:

    Bottom-PCB Vorderseite      0,0
    Bauteile Bottom + Stack    10,0   -> Mid-PCB Rueckseite
    Mid-PCB                     1,0   -> Mid-PCB Vorderseite bei 11,0
    Bauteile Mid + Stack        9,0   -> Top-PCB Rueckseite bei 20,0
    Top-PCB                     1,0

Die KiCad-Exporte legen jedes Board mit seiner RUECKSEITE auf z = 0 und
zaehlen nach oben. Verschoben wird deshalb um die Rueckseitenhoehe.

Der Adapter kommt aus adapter.py und sitzt vor dem Top-Board; sein eigener
Nullpunkt ist der Flansch, deshalb der zusaetzliche Versatz.
"""

import os
import sys

from build123d import Compound, Location, export_step, import_step

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STACK = os.path.join(ROOT, "mechanical", "export", "stack")
OUT = os.path.join(ROOT, "mechanical", "export", "switchstack_stack.step")

# (Datei, z der Platinen-RUECKSEITE in mm)
TEILE = [
    ("bottom_power_motor.step", 0.0),
    ("mid_logic.step", 10.0),
    ("top_ui.step", 20.0),
]

# Der Adapter sitzt vor dem Top-Board. Seine Platinentasche nimmt das
# Top-Board auf; Tasche und Boardrueckseite liegen aufeinander.
ADAPTER = ("adapter.step", 21.0)


def bauen():
    teile = []
    for name, z in TEILE:
        pfad = os.path.join(STACK, name)
        if not os.path.exists(pfad):
            print("fehlt: %s - erst kicad-cli pcb export step laufen lassen" % name)
            return None
        koerper = import_step(pfad)
        koerper.label = name.replace(".step", "")
        teile.append(Location((0, 0, z)) * koerper)

    ad = os.path.join(ROOT, "mechanical", "export", ADAPTER[0])
    if os.path.exists(ad):
        a = import_step(ad)
        a.label = "adapter"
        teile.append(Location((0, 0, ADAPTER[1])) * a)
    else:
        print("Hinweis: adapter.step fehlt, Stapel ohne Adapter")

    return Compound(children=teile, label="SwitchStack")


def main():
    baugruppe = bauen()
    if baugruppe is None:
        return 1
    export_step(baugruppe, OUT)
    bb = baugruppe.bounding_box()
    print("Baugruppe   : %s" % OUT)
    print("Teile       : %d" % len(baugruppe.children))
    print("Huellmass   : %.1f x %.1f x %.1f mm"
          % (bb.size.X, bb.size.Y, bb.size.Z))
    print("Tiefe       : von z = %.1f bis %.1f" % (bb.min.Z, bb.max.Z))
    return 0


if __name__ == "__main__":
    sys.exit(main())
