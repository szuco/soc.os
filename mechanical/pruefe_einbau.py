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

# KOORDINATEN - die Falle, die am 21.08. drei Ausschnitte auf die
# falsche Seite gesetzt hat: KiCad zaehlt y NACH UNTEN, build123d und
# der STEP-Export zaehlen y NACH OBEN. Am exportierten Top-Board
# nachgemessen: Die USB-Randkerbe steht im Layout bei y = +8, im STEP
# liegt sie bei y = -8. Jede Feature-Lage, die aus dem Layout kommt,
# muss also mit ky() gespiegelt werden.
def ky(y):
    """KiCad-y (nach unten) -> CAD-y (nach oben)."""
    return -y


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
    # DIE GEGENSTUECKE AUS DEM LAYOUT - nicht aus den Gehaeuseparametern.
    # Genau hier lag der Denkfehler: Solange Becherfenster und Pruefkoerper
    # aus DERSELBEN Konstante kamen, hob sich jede Verschiebung auf und
    # die Pruefung blieb gruen. Jetzt kommen die Koerper aus gen_layouts
    # (KiCad-Koordinaten, per ky gespiegelt) - die Teile muessen sich
    # danach richten, nicht umgekehrt.
    import ast as _ast
    _q = _ast.parse(open(os.path.join(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))),
        "tools", "gen_layouts.py"), encoding="utf-8").read())
    _fix = {}
    for _k in _ast.walk(_q):
        if isinstance(_k, _ast.keyword) and _k.arg in ("J1", "J7"):
            try:
                _fix[_k.arg] = _ast.literal_eval(_k.value)
            except Exception:
                pass
    j1x, j1y = _fix["J1"][0], _fix["J1"][1]      # Feldstecker auf Bottom
    # Micro-Fit 43045-1612: Koerper 16,4 x 8,6, ragt 6,6 nach hinten,
    # das gesteckte Gegenstueck noch einmal so weit.
    feld = Pos(j1x, ky(j1y), -5.0) * Box(16.4, 8.6, 10.0)
    # USB-C des Mid-Boards: greift durch die Randkerbe des Top-Boards
    # nach vorn; Koerper 9,94 x 6,40, Hoehe 9,25 ab Mid-Vorderseite (11,0)
    usb = Pos(-20.0, ky(8.4), 11.0 + 9.25 / 2.0) * Box(6.40, 9.94, 9.25)
    # Magnetkabel: laeuft von der Kabelkerbe des Top-Boards (Unterkante,
    # KiCad y = +22,5) hinter dem Rahmen nach aussen durch den Tragring.
    kabel = Pos(0.0, ky(22.5), WAND_Z + 1.0) * Box(4.0, 3.0, 6.0)

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
    frei(feld, becher, "Feldstecker gegen Becher (Tunnel!)")
    frei(usb, adapter, "USB-C gegen Adapter (Freistellung!)")
    frei(usb, ring, "USB-C gegen Tragring")
    frei(kabel, ring, "Magnetkabel gegen Tragring (Durchlass!)")
    frei(becher, ring, "Becher gegen Tragring")
    frei(adapter, ring, "Adapter gegen Tragring")
    frei(boards[0], becher, "Bottom-Board gegen Becher")
    frei(boards[1], becher, "Mid-Board gegen Becher")

    # KRAFTKETTE: Der Adapter muss den Tragring wirklich beruehren -
    # Forderung des Nutzers vom 21.08. Geprueft wird, ob in der
    # Kragenebene (Tragring-Vorderseite) Adaptermaterial ausserhalb der
    # Ringoeffnung steht, also Auflage vorhanden ist.
    o = TP["open_sq"] / 2.0
    auflage = 0.0
    for sx, sy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        # Kragenebene = Tragring-VORDERseite (WAND_Z + Plattendicke)
        probe = (Pos(sx * (o + 0.45), sy * (o + 0.45),
                     WAND_Z + TP["t"] + AP["collar_t"] / 2.0)
                 * Box(12.0 if sy else 0.7, 0.7 if sy else 12.0, 0.8))
        auflage += (adapter & probe).volume
    if auflage < 1.0:
        errs.append("Adapter liegt NICHT auf dem Tragring auf "
                    "(Kragenprobe %.2f mm3)" % auflage)

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
    print("Kragen %.1f  -> Ringoeffnung %.1f : %.2f mm je Seite Auflage"
          % (AP["collar_sq"], TP["open_sq"],
             (AP["collar_sq"] - TP["open_sq"]) / 2.0))
    print("Kragen %.1f  -> Scheibe innen 53,2 : %.2f mm je Seite Luft"
          % (AP["collar_sq"], (53.2 - AP["collar_sq"]) / 2.0))
    print("Schraube M2,5: Weg %.1f + Gewinde >= 4 -> Laenge >= %.0f"
          % (GP["tief_hinten"] + GP["boden_t"] + 1.0,
             math.ceil(GP["tief_hinten"] + GP["boden_t"] + 1.0 + 4)))
    print("URTEIL: kleinere Boards sind %s"
          % ("NICHT noetig" if not errs else "zu pruefen"))
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
