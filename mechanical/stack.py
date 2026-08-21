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
    # EBENENABSTAND 5,0 statt 9,0 (21.08.2026, Entscheidung des Nutzers
    # nach der Steckverbinder-Recherche, Punkt 23): Eine erhoehte
    # 1,27-mm-Buchse mit 9 mm Bauhoehe existiert nicht - herstellerweit
    # ist bei 4,0..4,6 mm Schluss. Mit einem kurzen Stapel greifen
    # dagegen ganz normale Katalogteile (Buchse 4,3 + durchgesteckter
    # Stift 8,1), das Durchsteck-Konzept bleibt, und die Lochbilder
    # aller drei Boards bleiben unveraendert.
    #
    # Gegenprobe der Bauteilhoehen (per Kollisionspruefung):
    #   Bottom-Vorderseite -> Mid: hoechstes Teil Drossel SRP7028A 2,8
    #   Mid-Vorderseite -> Top:    ESP32-Modul 3,2 und J6 4,25, die sich
    #                              oertlich NICHT ueberlappen
    # 5,0 mm reichen also mit Luft; die USB-C-Buchse ragt wie bisher
    # durch die Randkerbe des Top-Boards.
    ("bottom_power_motor.step", 0.0),
    ("mid_logic.step", 6.0),
    ("top_ui.step", 12.0),
]

# Der Adapter sitzt vor dem Top-Board. Seine Platinentasche nimmt das
# Top-Board auf; Tasche und Boardrueckseite liegen aufeinander.
#
# KORREKTUR 19.08.2026: Hier stand 21,0 - die Zahl der Board-VORDERseite.
# Der Nullpunkt des Adapters ist aber seine Flanschrueckseite, und seine
# Auflage (Modellhoehe seat) liegt 4,5 mm davor. Gefordert ist, dass die
# Auflage auf der Board-RUECKseite sitzt:
#
#     seat  = plate_depth + flange_t - (face + cross + switch + pcb)
#           = 10,0 - 5,5 = 4,5
#     Versatz = Rueckseite Top (20,0) - seat (4,5) = 15,5
#
# Mit 21,0 schwebte der Adapter 5,5 mm zu weit vorn, das Top-Board lag
# nicht in seiner Tasche. Gegenprobe: Mit 15,5 faellt die hintere Kante
# der Zentralscheibe (Tiefe 7,5 vor der Sichtflaeche bei 25,5, also 18,0)
# genau auf die Flanschvorderkante (15,5 + 2,5) - so muss es sein.
# Aufgefallen beim Zeichnen von tools/gen_explosion.py.
# 15,0 seit dem Tasterwechsel (SKQG, 1,5 statt 2,0 hoch): Die Tasche des
# Adapters haelt die Platinenrueckseite, und die sitzt jetzt 5,0 statt
# 5,5 hinter der Sichtflaeche - der Adapter rueckt 0,5 nach hinten.
# gen_explosion.py prueft diesen Wert gegen die Adapterparameter.
# 7,5 seit dem kurzen Stapel (21.08.): Rueckseite Top (12,0) - seat (4,5).
# Der Wert davor war 15,5 bei Top-Rueckseite 20,0 - dieselbe Rechnung.
ADAPTER = ("adapter.step", 7.5)
# Der Tragring liegt auf der Wandebene - dieselbe Ebene wie die
# Adapterrueckseite (7,5 seit dem kurzen Stapel). Der Adapter-Basisring
# taucht durch seine Oeffnung, sein Kragen legt sich auf die Platte.
TRAGRING = ("tragring.step", 7.5)
# Der Becher ist in seinen eigenen Koordinaten schon richtig gelagert
# (z 0 = Rueckseite Bottom-Board), deshalb Versatz 0.
GEHAEUSE = ("gehaeuse.step", 0.0)


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

    for datei, z, label in ((ADAPTER[0], ADAPTER[1], "adapter"),
                            (TRAGRING[0], TRAGRING[1], "tragring"),
                            (GEHAEUSE[0], GEHAEUSE[1], "gehaeuse")):
        pfad = os.path.join(ROOT, "mechanical", "export", datei)
        if os.path.exists(pfad):
            a = import_step(pfad)
            a.label = label
            teile.append(Location((0, 0, z)) * a)
        else:
            print("Hinweis: %s fehlt, Stapel ohne %s" % (datei, label))

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
