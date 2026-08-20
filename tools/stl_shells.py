#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Zaehlt zusammenhaengende Schalen in binaeren STLs - der Schwebe-Detektor.

Anlass: Die Bajonettzapfen des Bechers standen auf einer weggefensterten
Wand und schwebten als lose Koerper im STL (21.08.2026, Nutzerbefund
"die Raender haengen in der Luft"). Die Selbsttests der Teile pruefen
seither gezielte Stellen - dieses Werkzeug prueft die GANZE Datei: Ein
druckbares Einzelteil hat genau EINE Schale. Jede weitere ist entweder
ein bewusster Hohlraum oder ein schwebender Koerper.

    tools/stl_shells.py [datei.stl ...]     (ohne Argumente: die drei
                                             Druckteile aus export/)
"""

import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STANDARD = [os.path.join(ROOT, "mechanical", "export", n + ".stl")
            for n in ("gehaeuse", "tragring", "adapter")]


def schalen(pfad):
    d = open(pfad, "rb").read()
    n = struct.unpack_from("<I", d, 80)[0]

    # Eckpunkte auf 1 um runden und nummerieren
    punkt_id = {}
    tri_punkte = []
    for t in range(n):
        o = 84 + t * 50 + 12
        ids = []
        for k in range(3):
            x, y, z = struct.unpack_from("<fff", d, o + k * 12)
            key = (round(x, 3), round(y, 3), round(z, 3))
            if key not in punkt_id:
                punkt_id[key] = len(punkt_id)
            ids.append(punkt_id[key])
        tri_punkte.append(ids)

    # Union-Find ueber gemeinsame Eckpunkte
    eltern = list(range(len(punkt_id)))

    def wurzel(a):
        while eltern[a] != a:
            eltern[a] = eltern[eltern[a]]
            a = eltern[a]
        return a

    def vereine(a, b):
        ra, rb = wurzel(a), wurzel(b)
        if ra != rb:
            eltern[ra] = rb

    for a, b, c in tri_punkte:
        vereine(a, b)
        vereine(b, c)

    gruppen = {}
    for a, b, c in tri_punkte:
        gruppen[wurzel(a)] = gruppen.get(wurzel(a), 0) + 1
    return n, sorted(gruppen.values(), reverse=True)


def main():
    dateien = sys.argv[1:] or STANDARD
    schlecht = 0
    for pfad in dateien:
        n, gr = schalen(pfad)
        name = os.path.basename(pfad)
        if len(gr) == 1:
            print("%-16s %6d Dreiecke, 1 Schale - OK" % (name, n))
        else:
            schlecht += 1
            print("%-16s %6d Dreiecke, %d SCHALEN: %s  <- schwebende "
                  "Koerper oder Hohlraeume!"
                  % (name, n, len(gr), gr))
    return 1 if schlecht else 0


if __name__ == "__main__":
    sys.exit(main())
