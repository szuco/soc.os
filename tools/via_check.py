#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prueft, ob jedes Via den Strom seines Netzes tragen kann.

Anlass (20.08.2026): 24V_IN lief ueber genau EIN 0,6/0,3-Via. So ein Via
traegt rund 1,2 A - der Summenstrom des Geraets ist 4,1 A. Aufgefallen ist
das niemandem Automatischen, deshalb gibt es jetzt dieses Werkzeug; es
laeuft nach jedem Routing.

MODELL - bewusst konservativ und einfach:
  * Tragfaehigkeit eines Vias ~ Huelsenquerschnitt ~ Bohrdurchmesser.
    Angesetzt: 4 A je mm Bohrung (25-um-Huelse, moderate Erwaermung).
      0,3 mm -> 1,2 A      0,4 mm -> 1,6 A      0,6 mm -> 2,4 A
  * Vias desselben Netzes im Umkreis von 3 mm gelten als PARALLEL und
    duerfen ihre Tragfaehigkeit addieren - naeher beieinander teilen sich
    die Lagenwechsel den Strom tatsaechlich.
  * Gerechnet wird mit DAUERstrom, nicht mit Transienten: Der Blockierfall
    (1,7 A) dauert bis zum HW-Trip Millisekunden, thermisch traegt das
    jedes Via. Die 24-V-Schienen dagegen fuehren mit beiden Motoren
    dauerhaft ~2,3 A und im Grenzfall 4,1 A.

--fix verdoppelt unterdimensionierte Uebergaenge: Neben das Via kommt ein
Zwilling gleicher Groesse, sofern im Umkreis Platz ist (geprueft gegen
alle fremden Bahnen und Pads mit 0,25 mm Abstand). Danach IMMER die DRC
laufen lassen - sie ist die letzte Instanz.
"""

import math
import sys

import pcbnew

# Dauerstroeme je Netz. Was hier nicht steht, gilt als Signal (<= 0,5 A)
# und ist mit jedem Via zufrieden.
STROEME = {
    "bottom_power_motor": {
        "24V_IN": 4.1, "24V_F": 4.1, "24V_PROT": 4.1, "PGND": 4.1,
        "M1_A": 1.0, "M1_B": 1.0, "M2_A": 1.0, "M2_B": 1.0,
        "M1_SWA": 1.0, "M1_SWB": 1.0, "M2_SWA": 1.0, "M2_SWB": 1.0,
        "5V_BUCK": 2.0, "5V_SYS": 2.0, "3V3_SYS": 1.0,
        "6V2_STAR": 0.5, "6V2_STAR_F": 0.5,
    },
    "mid_logic": {
        "5V_SYS": 1.5, "3V3_SYS": 1.0, "PGND": 1.5, "USB_VBUS": 1.0,
    },
    "top_ui": {
        "3V3_SYS": 0.8, "6V2_STAR_F": 0.5, "STAR_OUT": 0.5, "PGND": 0.8,
    },
}

A_JE_MM = 4.0        # Tragfaehigkeit je mm Bohrdurchmesser
PARALLEL_MM = 3.0    # bis hierhin duerfen Vias sich den Strom teilen
LUFT = 0.25          # Mindestabstand des Zwillings zu fremdem Kupfer


def mm(v):
    return pcbnew.FromMM(float(v))


def _vias(board, netz):
    return [t for t in board.GetTracks()
            if t.GetClass() == "PCB_VIA" and t.GetNetname() == netz]


def _gruppen(vias):
    """Vias zu Parallelgruppen zusammenfassen (Union-Find, klein genug)."""
    eltern = list(range(len(vias)))

    def wurzel(i):
        while eltern[i] != i:
            i = eltern[i]
        return i

    for i in range(len(vias)):
        for j in range(i + 1, len(vias)):
            a, b = vias[i].GetPosition(), vias[j].GetPosition()
            if math.hypot((a.x - b.x) / 1e6, (a.y - b.y) / 1e6) <= PARALLEL_MM:
                eltern[wurzel(j)] = wurzel(i)
    gruppen = {}
    for i, v in enumerate(vias):
        gruppen.setdefault(wurzel(i), []).append(v)
    return list(gruppen.values())


def _frei(board, x, y, netz, radius):
    """Ist an (x,y) Platz fuer ein Via dieses Netzes?"""
    # KiCad 10 verlangt fuer die Formabfrage eine LAGE. Ein Via geht durch
    # ALLE Kupferlagen - die erste Fassung pruefte nur F und B und bohrte
    # prompt 15 Innenlagenbahnen an (20.08.2026). Seitdem alle vier.
    p = pcbnew.VECTOR2I(mm(x), mm(y))
    kreis = pcbnew.SHAPE_CIRCLE(p, mm(radius))
    for lage in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
        for t in board.GetTracks():
            if t.GetNetname() == netz:
                continue
            if t.GetClass() == "PCB_TRACK" and t.GetLayer() != lage:
                continue
            d = t.GetEffectiveShape(lage).GetClearance(kreis) / 1e6
            if d < LUFT:
                return False
        for fp in board.GetFootprints():
            for pad in fp.Pads():
                if pad.GetNetname() == netz:
                    continue
                if not pad.IsOnLayer(lage):
                    continue
                d = pad.GetEffectiveShape(lage).GetClearance(kreis) / 1e6
                if d < LUFT:
                    return False
    # innerhalb der Platine bleiben (grob: Umriss-BBox minus Rand)
    bb = board.GetBoardEdgesBoundingBox()
    if not (bb.GetLeft() / 1e6 + radius + 0.5 < x < bb.GetRight() / 1e6 - radius - 0.5
            and bb.GetTop() / 1e6 + radius + 0.5 < y < bb.GetBottom() / 1e6 - radius - 0.5):
        return False
    return True


def pruefe(name, fix=False):
    pfad = "hardware/%s/%s.kicad_pcb" % (name, name)
    board = pcbnew.LoadBoard(pfad)
    stroeme = STROEME.get(name, {})
    probleme = []
    ergaenzt = 0

    for netz, strom in sorted(stroeme.items()):
        vias = _vias(board, netz)
        for gruppe in _gruppen(vias):
            kann = sum(v.GetDrillValue() / 1e6 * A_JE_MM for v in gruppe)
            if kann + 1e-9 >= strom:
                continue
            v0 = gruppe[0]
            x0, y0 = v0.GetPosition().x / 1e6, v0.GetPosition().y / 1e6
            if fix:
                # Zwillinge gleicher Groesse daneben, bis es reicht
                d = v0.GetDrillValue() / 1e6
                w = v0.GetWidth(pcbnew.F_Cu) / 1e6
                platziert = True
                while kann + 1e-9 < strom and platziert:
                    platziert = False
                    for wink in range(0, 360, 45):
                        nx = x0 + 1.1 * w * math.cos(math.radians(wink))
                        ny = y0 + 1.1 * w * math.sin(math.radians(wink))
                        if not _frei(board, nx, ny, netz, w / 2.0):
                            continue
                        z = pcbnew.PCB_VIA(board)
                        z.SetPosition(pcbnew.VECTOR2I(mm(nx), mm(ny)))
                        z.SetDrill(mm(d))
                        z.SetWidth(mm(w))
                        z.SetNet(v0.GetNet())
                        board.Add(z)
                        kann += d * A_JE_MM
                        ergaenzt += 1
                        platziert = True
                        x0, y0 = nx, ny
                        break
                if kann + 1e-9 >= strom:
                    continue
            probleme.append((netz, strom, kann, x0, y0, len(gruppe)))

    if ergaenzt:
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        pcbnew.SaveBoard(pfad, board)

    print("%-20s %d Netze geprueft, %d Zwillinge ergaenzt, %d Engpaesse"
          % (name, len(stroeme), ergaenzt, len(probleme)))
    for netz, soll, ist, x, y, n in probleme:
        print("   ! %-10s braucht %.1f A, %d Via(s) tragen %.1f A  @ %.1f/%.1f"
              % (netz, soll, n, ist, x, y))
    return len(probleme)


def main():
    fix = "--fix" in sys.argv
    boards = [a for a in sys.argv[1:] if not a.startswith("-")] or \
        list(STROEME.keys())
    fehler = 0
    for b in boards:
        fehler += pruefe(b, fix=fix)
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
