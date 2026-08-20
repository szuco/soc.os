#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Einbaupruefung gegen die GEMESSENE Dose - beantwortet: kleinere Boards?

Die Dose ist seit dem 21.08.2026 vermessen (F16a-f): 58 lichte Weite,
60 tief, vier OE-6-Schraubdome auf den Achsen, die bis r 27 hineinragen.
Dieses Werkzeug modelliert diese Dose als Volumenkoerper und prueft die
komplette Einbaugruppe boolesch dagegen: Becher, Tragring, Adapter, die
beiden runden Boards (als OE-52-Zylinder) und der Feldstecker-Koerper.
Jede Ueberschneidung mit Dosenmaterial ist ein Fehler.

Das Ergebnis entscheidet die Frage des Nutzers vom 21.08.: "wenn noetig
alles neu routen auf kleineren Boards". Solange hier alles BESTANDEN
meldet und die Abstandsliste positiv ist, ist ein Neulayout NICHT noetig.

Koordinaten: Boardrahmen (z = 0 ist die Rueckseite des Bottom-Boards,
z waechst nach vorn). Die Wandebene/Tragring-Auflage liegt bei 15,5,
die Dose reicht von dort 60 nach hinten (bis -44,5).
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from build123d import Box, Cylinder, Location, Pos

from adapter import PARAMS as AP, _z as adapter_z, build_adapter
from gehaeuse import PARAMS as GP, _becher
from tragring import PARAMS as TP, build_tragring

WAND_Z = 15.5          # Tragring-Auflage = Wandebene (docs/04)
DOM_KREIS = 30.0       # Schraubkreis 60 mm - Dommitte
DOM_R = 3.0            # F16d: OE 6
BOARD_R = 26.0         # OE 52


def dosenmaterial(p):
    """Mantel, Rueckwand und die vier Dome als ein Koerper."""
    r_licht = p["dose_licht"] / 2.0
    tief = p["dose_tief"]
    mitte = WAND_Z - tief / 2.0
    teil = (Pos(0, 0, mitte) * Cylinder(r_licht + 2.0, tief)
            - Pos(0, 0, mitte) * Cylinder(r_licht, tief + 1.0))
    teil += Pos(0, 0, WAND_Z - tief - 0.75) * Cylinder(r_licht + 2.0, 1.5)
    for wink in (0, 90, 180, 270):
        wr = math.radians(wink)
        teil += (Pos(DOM_KREIS * math.cos(wr), DOM_KREIS * math.sin(wr),
                     mitte) * Cylinder(DOM_R, tief))
    return teil


def main():
    dose = dosenmaterial(GP)
    becher = _becher(GP)
    ring = Location((0, 0, WAND_Z)) * build_tragring(TP)
    # Lage aus der Tiefenkette ABLEITEN, nicht hart kodieren: Die
    # Auflage (seat) traegt die Rueckseite des Top-Boards bei z = 20,0.
    adapter = (Location((0, 0, 20.0 - adapter_z(AP)["seat"]))
               * build_adapter(AP))
    boards = [Pos(0, 0, 0.5) * Cylinder(BOARD_R, 1.0),
              Pos(0, 0, 10.5) * Cylinder(BOARD_R, 1.0)]
    # Micro-Fit-Koerper samt gestecktem Gegenstueck, grob als Kasten
    feld = Pos(GP["fenster_x"], GP["fenster_y"], -5.0) * Box(16.4, 8.6, 10.0)

    errs = []

    def frei(a, b, was):
        v = (a & b).volume
        if v > 1e-6:
            errs.append("%s: %.1f mm3 Ueberschneidung" % (was, v))

    frei(becher, dose, "Becher gegen Dose")
    frei(ring, dose, "Tragring gegen Dose")
    frei(adapter, dose, "Adapter gegen Dose")
    frei(boards[0], dose, "Bottom-Board gegen Dose")
    frei(boards[1], dose, "Mid-Board gegen Dose")
    frei(feld, dose, "Feldstecker gegen Dose")
    frei(becher, ring, "Becher gegen Tragring")
    frei(adapter, ring, "Adapter gegen Tragring")
    frei(boards[0], becher, "Bottom-Board gegen Becher")
    frei(boards[1], becher, "Mid-Board gegen Becher")

    print("Einbaupruefung: %s" % ("BESTANDEN" if not errs else "FEHLGESCHLAGEN"))
    for e in errs:
        print("   ! %s" % e)

    # Abstaende, analytisch - die Zahlen hinter dem Urteil
    r_becher = (GP["board_d"] + GP["spiel"]) / 2.0 + GP["wand"]
    sehne = math.sqrt(max(DOM_R ** 2 - (DOM_KREIS - r_becher) ** 2, 0.0))
    print("Board OE52   -> Dom (r 27)      : %.1f mm Luft" % (27.0 - BOARD_R))
    print("Becher %.1f -> Dose (r %.0f)     : %.1f mm Luft"
          % (2 * r_becher, GP["dose_licht"] / 2.0,
             GP["dose_licht"] / 2.0 - r_becher))
    print("Dom-Fenster %.0f -> Dom-Sehne %.1f : %.1f mm Luft je Seite"
          % (GP["dom_fenster_b"], 2 * sehne,
             GP["dom_fenster_b"] / 2.0 - sehne))
    print("Schraube M2,5: Weg %.1f + Gewinde >= 4 -> Laenge >= %.0f"
          % (GP["tief_hinten"] + GP["boden_t"] + 1.0,
             math.ceil(GP["tief_hinten"] + GP["boden_t"] + 1.0 + 4)))
    print("URTEIL: kleinere Boards sind %s"
          % ("NICHT noetig" if not errs else "zu pruefen"))
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
