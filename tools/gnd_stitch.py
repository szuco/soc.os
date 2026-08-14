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


def _seg_dist(ax, ay, bx, by, cx, cy, dx, dy):
    """Minimaler Abstand zweier Strecken AB und CD (mm)."""
    import math

    def pt_seg(px, py, x1, y1, x2, y2):
        vx, vy = x2 - x1, y2 - y1
        L2 = vx * vx + vy * vy
        if L2 < 1e-12:
            return math.hypot(px - x1, py - y1)
        t = max(0.0, min(1.0, ((px - x1) * vx + (py - y1) * vy) / L2))
        return math.hypot(px - x1 - t * vx, py - y1 - t * vy)

    def ccw(x1, y1, x2, y2, x3, y3):
        return (y3 - y1) * (x2 - x1) - (y2 - y1) * (x3 - x1)

    d1 = ccw(cx, cy, dx, dy, ax, ay)
    d2 = ccw(cx, cy, dx, dy, bx, by)
    d3 = ccw(ax, ay, bx, by, cx, cy)
    d4 = ccw(ax, ay, bx, by, dx, dy)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        return 0.0
    return min(pt_seg(ax, ay, cx, cy, dx, dy),
               pt_seg(bx, by, cx, cy, dx, dy),
               pt_seg(cx, cy, ax, ay, bx, by),
               pt_seg(dx, dy, ax, ay, bx, by))


def seg_clear(board, layer, x0, y0, x1, y1, w, own_net="PGND",
              skip_pad=None):
    """Prueft eine geplante Bahn gegen alles fremde Kupfer der Lage."""
    for t in board.GetTracks():
        is_via = t.GetClass() == "PCB_VIA"
        if t.GetNetname() == own_net:
            continue
        if not is_via and t.GetLayer() != layer:
            continue
        s, e = t.GetStart(), t.GetEnd()
        d = _seg_dist(x0, y0, x1, y1,
                      pcbnew.ToMM(s.x), pcbnew.ToMM(s.y),
                      pcbnew.ToMM(e.x), pcbnew.ToMM(e.y))
        limit = w / 2 + pcbnew.ToMM(t.GetWidth()) / 2 + 0.16
        if d < limit:
            return False
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p is skip_pad or p.GetNetname() == own_net:
                continue
            on = (p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
                  or (fp.IsFlipped() == (layer == pcbnew.B_Cu)))
            if not on:
                continue
            px, py = pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y)
            half = max(pcbnew.ToMM(p.GetSize().x), pcbnew.ToMM(p.GetSize().y)) / 2
            d = _seg_dist(x0, y0, x1, y1, px, py, px, py)
            if d < w / 2 + half + 0.16:
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

    # 2. Baumelnde PGND-Bahnenden: Via ans Ende, wenn die Gegenlage dort
    #    Pour hat (Containment mit Randabstand garantiert Clearance).
    frag_f = fragments(board, pcbnew.F_Cu)
    frag_b = fragments(board, pcbnew.B_Cu)
    frag_f.sort(key=lambda p: -abs(p.Area()))
    frag_b.sort(key=lambda p: -abs(p.Area()))
    for t in list(board.GetTracks()):
        if t.GetNetname() != "PGND" or t.GetClass() == "PCB_VIA":
            continue
        other = frag_b if t.GetLayer() == pcbnew.F_Cu else frag_f
        if not other:
            continue
        for endp in (t.GetStart(), t.GetEnd()):
            x, y = pcbnew.ToMM(endp.x), pcbnew.ToMM(endp.y)
            if not all((x - hx) ** 2 + (y - hy) ** 2 >= HOLE_DIST ** 2
                       for hx, hy in holes):
                continue
            if contains_margin(other[0], x, y):
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
                v.SetWidth(mm(0.6))
                v.SetDrill(mm(0.3))
                v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                v.SetNet(net)
                board.Add(v)
                holes.append((x, y))
                placed += 1
                print("  End-Via (%.2f, %.2f)" % (x, y))

    # 3. Verwaiste PGND-Pads: Via im Pad (SMD) bzw. Stub in den Pour (PTH).
    #    Nur Pads, die der DRC-Bericht als unverbunden fuehrt.
    import re as _re
    orphans = set()
    rpt = "/tmp/drc_%s.rpt" % name
    if os.path.exists(rpt):
        for m in _re.finditer(r'(?:PTH )?[Pp]ad (\S+) \[PGND\] of (\S+)',
                              open(rpt, encoding="utf-8").read()):
            orphans.add((m.group(2), m.group(1)))
    print("verwaiste PGND-Pads laut DRC:", sorted(orphans))
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() != "PGND":
                continue
            if (fp.GetReference(), p.GetPadName()) not in orphans:
                continue
            x, y = pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y)
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                targets = ((frag_f, pcbnew.F_Cu), (frag_b, pcbnew.B_Cu))
            else:
                own_layer = pcbnew.B_Cu if fp.IsFlipped() else pcbnew.F_Cu
                own = frag_b if fp.IsFlipped() else frag_f
                other = frag_f if fp.IsFlipped() else frag_b
                # SMD: Via im Pad, wenn die Gegenlage dort Pour hat ...
                if other and contains_margin(other[0], x, y) and all(
                        (x - hx) ** 2 + (y - hy) ** 2 >= HOLE_DIST ** 2
                        for hx, hy in holes):
                    v = pcbnew.PCB_VIA(board)
                    v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
                    v.SetWidth(mm(0.6))
                    v.SetDrill(mm(0.3))
                    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                    v.SetNet(net)
                    board.Add(v)
                    holes.append((x, y))
                    placed += 1
                    print("  Pad-Via %s-%s (%.2f, %.2f)"
                          % (fp.GetReference(), p.GetPadName(), x, y))
                    continue
                # ... sonst Stub auf der eigenen Lage in den Pour
                targets = ((own, own_layer),)
            # PTH: kurzer Stub in Richtung Pour (8 Richtungen, 0,8-2,4 mm)
            done = False
            for frags, layer in targets:
                if done or not frags:
                    continue
                for dist in (0.9, 1.3, 1.8, 2.4):
                    if done:
                        break
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1),
                                   (0.707, 0.707), (-0.707, 0.707),
                                   (0.707, -0.707), (-0.707, -0.707)):
                        ex, ey = x + dx * dist, y + dy * dist
                        if (contains_margin(frags[0], ex, ey)
                                and seg_clear(board, layer, x, y, ex, ey,
                                              0.25, skip_pad=p)):
                            t = pcbnew.PCB_TRACK(board)
                            t.SetStart(pcbnew.VECTOR2I(mm(x), mm(y)))
                            t.SetEnd(pcbnew.VECTOR2I(mm(ex), mm(ey)))
                            t.SetLayer(layer)
                            t.SetWidth(mm(0.25))
                            t.SetNet(net)
                            board.Add(t)
                            placed += 1
                            print("  PTH-Stub %s-%s -> (%.2f, %.2f) %s"
                                  % (fp.GetReference(), p.GetPadName(), ex, ey,
                                     board.GetLayerName(layer)))
                            done = True
                            break

    print("%d Stitching-Elemente gesetzt" % placed)
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
