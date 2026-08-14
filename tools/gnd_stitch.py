#!/usr/bin/env python3
"""
Verbindet getrennte PGND-Pour-Fragmente per Stitching-Vias.

    xvfb-run -a python3 tools/gnd_stitch.py <board>

Vorgehen: Die gefuellten Polygone der PGND-Zonen werden je Lage in
Fragmente zerlegt. Das groesste Fragment je Lage ist die Hauptflaeche.
Fuer jedes kleinere Fragment wird per Rastersuche ein Punkt gefunden,
der MIT RANDABSTAND sowohl im kleinen Fragment als auch in der
Hauptflaeche der anderen Lage liegt - dort verbindet ein Via beide.
Weil der Punkt vollstaendig in Kupfer beider Lagen liegt und die Zone
selbst alle Clearances einhaelt, ist das Via konstruktionsbedingt
DRC-sauber; nur Lochabstaende zu bestehenden Bohrungen werden extra
geprueft. Danach: Zonen neu fuellen, DRC.
"""

import os
import sys

if not os.environ.get("DISPLAY"):
    os.execvp("xvfb-run", ["xvfb-run", "-a", sys.executable] + sys.argv)

import pcbnew  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_layouts import run_drc                                 # noqa: E402
from route_boards import classify_unrouted                      # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mm = lambda v: pcbnew.FromMM(v)   # noqa: E731
MARGIN = 0.45      # mm; Punkt+Margin muss im Kupfer liegen (Via Ø0,6)
HOLE_DIST = 1.0    # mm; Mindestabstand zu bestehenden Bohrungen
STEP = 0.4         # mm; Suchraster


def fragments(board, layer):
    """Alle gefuellten PGND-Fragmente einer Lage als Poly-Liste."""
    out = []
    for i in range(board.GetAreaCount()):
        z = board.GetArea(i)
        if z.GetIsRuleArea() or z.GetNetname() != "PGND":
            continue
        if not z.IsOnLayer(layer):
            continue
        polys = z.GetFilledPolysList(layer)
        for k in range(polys.OutlineCount()):
            single = pcbnew.SHAPE_POLY_SET()
            single.AddOutline(polys.Outline(k))
            out.append(single)
    return out


def contains_margin(poly, x, y):
    for dx, dy in ((0, 0), (MARGIN, 0), (-MARGIN, 0), (0, MARGIN),
                   (0, -MARGIN), (0.32, 0.32), (-0.32, 0.32),
                   (0.32, -0.32), (-0.32, -0.32)):
        if not poly.Contains(pcbnew.VECTOR2I(mm(x + dx), mm(y + dy))):
            return False
    return True


def hole_positions(board):
    holes = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetDrillSize().x > 0:
                holes.append((pcbnew.ToMM(p.GetPosition().x),
                              pcbnew.ToMM(p.GetPosition().y)))
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            holes.append((pcbnew.ToMM(t.GetPosition().x),
                          pcbnew.ToMM(t.GetPosition().y)))
    return holes


def stitch(name):
    pcb = os.path.join(ROOT, "hardware", name, name + ".kicad_pcb")
    board = pcbnew.LoadBoard(pcb)
    net = board.FindNet("PGND")
    holes = hole_positions(board)

    placed = 0
    for layer, other in ((pcbnew.F_Cu, pcbnew.B_Cu),
                         (pcbnew.B_Cu, pcbnew.F_Cu)):
        frags = fragments(board, layer)
        if not frags:
            continue
        frags.sort(key=lambda p: -abs(p.Area()))
        main_other = fragments(board, other)
        if not main_other:
            continue
        main_other.sort(key=lambda p: -abs(p.Area()))
        big_other = main_other[0]
        for frag in frags[1:]:
            bb = frag.BBox()
            x0, y0 = pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop())
            x1, y1 = pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom())
            best = None
            y = y0
            while y <= y1 and best is None:
                x = x0
                while x <= x1:
                    if (contains_margin(frag, x, y)
                            and contains_margin(big_other, x, y)
                            and all((x - hx) ** 2 + (y - hy) ** 2
                                    >= HOLE_DIST ** 2 for hx, hy in holes)):
                        best = (x, y)
                        break
                    x += STEP
                y += STEP
            if best:
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(pcbnew.VECTOR2I(mm(best[0]), mm(best[1])))
                v.SetWidth(mm(0.6))
                v.SetDrill(mm(0.3))
                v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                v.SetNet(net)
                board.Add(v)
                holes.append(best)
                placed += 1
                print("  Stitch-Via %s (%.2f, %.2f)"
                      % (board.GetLayerName(layer), best[0], best[1]))

    print("%d Stitching-Vias gesetzt" % placed)
    pcbnew.SaveBoard(pcb, board)
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    pcbnew.SaveBoard(pcb, board)

    res, errs = run_drc(pcb)
    if errs:
        raise RuntimeError(errs[0])
    print("violations:", dict(res["violations"]))
    print("offen:", classify_unrouted("/tmp/drc_%s.rpt" % name))


if __name__ == "__main__":
    stitch(sys.argv[1] if len(sys.argv) > 1 else "mid_logic")
