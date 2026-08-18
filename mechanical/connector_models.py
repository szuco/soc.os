#!/usr/bin/env python3
"""
Erzeugt die fehlenden 3D-Modelle fuer Steckverbinder.

    python3 mechanical/connector_models.py

WARUM ES SIE BRAUCHT
--------------------
Drei Steckverbinder dieses Projekts sind im 3D-View unsichtbar, weil KiCad
fuer sie kein Modell mitliefert - ausgerechnet die drei, die das Tiefenbudget
bestimmen: der Leistungs-/Motorstecker (Molex Micro-Fit 3.0), die
USB-C-Buchse und die Klinkenbuchse. Ihr Footprint verweist auf eine
STEP-Datei, die es in der Bibliothek nicht gibt.

WAS DIESE MODELLE SIND - UND WAS NICHT
--------------------------------------
Sie sind HUELLKOERPER, keine Nachbildungen. Der Grundriss stammt aus der
F.Fab-Lage des jeweiligen Footprints und ist damit so genau wie das Footprint
selbst. Die HOEHE ist die einzige Zahl, die nicht aus KiCad kommt; sie steht
unten je Bauteil mit ihrer Quelle.

Fuer den Zweck reicht das: Man will sehen, ob der Stecker gegen den Adapter
stoesst, ob die USB-Buchse durch die Randkerbe passt und wie weit der
Leistungsstecker nach hinten ragt. Fuer eine Fotomontage taugen sie nicht.

Ein falsches Ersatzmodell aus einem aehnlichen Bauteil waere schlechter als
gar keines - deshalb keine geliehenen Modelle, sondern gerechnete Huellen mit
dokumentierter Herkunft.
"""

import os
import re
import sys

from build123d import BuildPart, BuildSketch, Location, Mode, Plane
from build123d import Polygon, export_step, extrude, fillet

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KIFP = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"
OUT = os.path.join(ROOT, "hardware", "lib", "3dmodels")

# (Footprint-Bibliothek, Footprint, Hoehe ueber der Platine, Quelle der Hoehe)
TEILE = [
    ("Connector_Molex", "Molex_Micro-Fit_3.0_43045-2012_2x10_P3.00mm_Vertical",
     8.9, "Molex 43045, Serienmass Steckerhoehe ueber Platine; docs/04 "
          "rechnet mit 10,0 mm inklusive gestecktem Gegenstueck"),
    ("Connector_Molex", "Molex_Micro-Fit_3.0_43045-1612_2x08_P3.00mm_Vertical",
     8.9, "wie oben - das ist der Feldstecker, ueber den seit dem 18.08.2026 "
          "die gesamte Verdrahtung laeuft"),
    ("Connector_Molex", "Molex_Micro-Fit_3.0_43045-0612_2x03_P3.00mm_Vertical",
     8.9, "wie oben, nur kuerzer"),
    ("Connector_USB", "USB_C_Receptacle_G-Switch_GT-USB-7051x",
     9.25, "stehende USB-C-Buchsen dieser Bauform liegen zwischen 7 und "
           "9,25 mm; genommen ist der obere Wert aus dem Datenblatt der "
           "GCT USB4115, damit die Huelle nicht zu klein ist"),
    ("Connector_Audio", "Jack_3.5mm_QingPu_WQP-PJ398SM_Vertical_CircularHoles",
     12.0, "WQP-PJ398SM, Korpuslaenge der stehenden Bauform"),
]


def fab_umriss(lib, name):
    """Grundriss aus der F.Fab-Lage des Footprints."""
    pfad = os.path.join(KIFP, lib + ".pretty", name + ".kicad_mod")
    if not os.path.exists(pfad):
        return None
    txt = open(pfad, encoding="utf-8").read()
    xs, ys = [], []
    # KiCad schreibt fp_line/fp_rect je nach Version unterschiedlich
    # verschachtelt; deshalb blockweise suchen und die Lage im Block pruefen.
    for m in re.finditer(r'\(fp_(?:line|rect)\b(.*?)\n\t\)', txt, re.S):
        blk = m.group(1)
        if '"F.Fab"' not in blk:
            continue
        for s in re.finditer(r'\((?:start|end) ([-\d.]+) ([-\d.]+)\)', blk):
            xs.append(float(s.group(1)))
            ys.append(float(s.group(2)))
    if not xs:
        return None
    return min(xs), max(xs), min(ys), max(ys)


def bauen(lib, name, hoehe):
    box = fab_umriss(lib, name)
    if box is None:
        return None, None
    x0, x1, y0, y1 = box
    # Y SPIEGELN. Das Footprint zaehlt Y nach unten, KiCads 3D-Ansicht nach
    # oben - ein unveraendert uebernommener Grundriss sitzt sonst spiegelbildlich
    # neben seinen Pads. Beim ersten Versuch am 18.08.2026 lag der Feldstecker
    # deshalb quer ueber der halben Platine statt auf seinem Padfeld.
    y0, y1 = -y1, -y0
    with BuildPart() as p:
        with BuildSketch(Plane.XY):
            Polygon((x0, y0), (x1, y0), (x1, y1), (x0, y1), align=None)
        extrude(amount=hoehe)
        try:
            fillet(p.edges().filter_by(lambda e: True).group_by()[-1], 0.3)
        except Exception:
            pass
    return p.part, (x1 - x0, y1 - y0, hoehe)


def main():
    os.makedirs(OUT, exist_ok=True)
    n = 0
    for lib, name, hoehe, quelle in TEILE:
        koerper, masse = bauen(lib, name, hoehe)
        if koerper is None:
            print("%-52s Footprint oder F.Fab fehlt" % name[:52])
            continue
        ziel = os.path.join(OUT, name + ".step")
        export_step(koerper, ziel)
        print("%-52s %5.2f x %5.2f x %5.2f mm" % (name[:52], *masse))
        print("%-52s Hoehe: %s" % ("", quelle))
        n += 1
    print()
    print("Ausgabe : %s" % os.path.relpath(OUT, ROOT))
    print("Hinweis : Huellkoerper, keine Nachbildungen - Grundriss aus F.Fab, "
          "Hoehen wie oben belegt.")
    return 0 if n else 1


if __name__ == "__main__":
    sys.exit(main())
