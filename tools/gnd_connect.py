#!/usr/bin/env python3
"""
Schliesst die letzten PGND-Luecken deterministisch.

    xvfb-run -a python3 tools/gnd_connect.py <board>

Berechnet die PGND-Konnektivitaet selbst (Union-Find ueber Bahnen, Vias,
Pads und Pour-Fragmente), bestimmt den Hauptcluster und setzt fuer jeden
verwaisten Cluster ein Via an einem Punkt, der (a) auf Eigenkupfer des
Clusters liegt, (b) mit Randabstand in einem Pour-Fragment des
HAUPTclusters der Gegenlage steckt, (c) seg_clear gegen Fremdkupfer
besteht und (d) Lochabstaende einhaelt. Danach Zonen fuellen und DRC.
Wiederholt bis nichts mehr offen ist oder keine Kandidaten existieren.
"""

import math
import os
import sys

if not os.environ.get("DISPLAY"):
    os.execvp("xvfb-run", ["xvfb-run", "-a", sys.executable] + sys.argv)

import pcbnew  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_layouts import run_drc, inside_outline                 # noqa: E402
from route_boards import classify_unrouted                      # noqa: E402
from gnd_stitch import (seg_clear, contains_margin, fragments,  # noqa: E402
                        hole_positions, _seg_dist)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mm = lambda v: pcbnew.FromMM(v)   # noqa: E731

F, B = pcbnew.F_Cu, pcbnew.B_Cu
# Alle Kupferlagen des Boards. Seit der Umstellung auf vier Lagen (17.08.2026)
# reicht F/B nicht mehr: Das Skript setzte durchgehende Vias, pruefte den
# Freiraum aber nur auf den Aussenlagen - und traf damit Leiterbahnen auf
# In1/In2. Ergebnis waren zwei Kurzschluesse auf Mid und einer auf Top.
CU_ALL = (F, pcbnew.In1_Cu, pcbnew.In2_Cu, B)


def copper_layers(board):
    en = board.GetEnabledLayers()
    return [l for l in CU_ALL if en.Contains(l)]


class Item:
    def __init__(self, kind, layer, geom, w):
        self.kind = kind      # track|via|pad|frag
        self.layer = layer    # F/B oder None (durchgehend)
        self.geom = geom      # ((x0,y0),(x1,y1)) | (x,y) | poly
        self.w = w            # Breite/Radius


def collect(board):
    items = []
    for t in board.GetTracks():
        if t.GetNetname() != "PGND":
            continue
        if t.GetClass() == "PCB_VIA":
            p = t.GetPosition()
            items.append(Item("via", None,
                              (pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)),
                              pcbnew.ToMM(t.GetWidth()) / 2))
        else:
            s, e = t.GetStart(), t.GetEnd()
            items.append(Item("track", t.GetLayer(),
                              ((pcbnew.ToMM(s.x), pcbnew.ToMM(s.y)),
                               (pcbnew.ToMM(e.x), pcbnew.ToMM(e.y))),
                              pcbnew.ToMM(t.GetWidth()) / 2))
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() != "PGND":
                continue
            pos = p.GetPosition()
            pth = p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
            layer = None if pth else (B if fp.IsFlipped() else F)
            half = max(pcbnew.ToMM(p.GetSize().x),
                       pcbnew.ToMM(p.GetSize().y)) / 2
            items.append(Item("pad", layer,
                              (pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y)), half))
    for layer in copper_layers(board):
        for poly in fragments(board, layer):
            items.append(Item("frag", layer, poly, 0))
    return items


def touch(a, b_):
    la, lb = a.layer, b_.layer
    if la is not None and lb is not None and la != lb:
        return False
    if a.kind == "frag" or b_.kind == "frag":
        fr, ot = (a, b_) if a.kind == "frag" else (b_, a)
        if ot.kind == "frag":
            return False
        if ot.kind == "track":
            return False        # Pour beruehrt Bahnen nie (Clearance)
        x, y = ot.geom
        # Via/Pad: Pour platiert an - Mittelpunkt oder Randpunkt im Polygon
        for dx, dy in ((0, 0), (ot.w * 0.7, 0), (-ot.w * 0.7, 0),
                       (0, ot.w * 0.7), (0, -ot.w * 0.7)):
            if fr.geom.Contains(pcbnew.VECTOR2I(mm(x + dx), mm(y + dy))):
                return True
        return False
    ga = a.geom if a.kind == "track" else (a.geom, a.geom)
    gb = b_.geom if b_.kind == "track" else (b_.geom, b_.geom)
    d = _seg_dist(ga[0][0], ga[0][1], ga[1][0], ga[1][1],
                  gb[0][0], gb[0][1], gb[1][0], gb[1][1])
    return d <= a.w + b_.w + 0.01


def clusters(items):
    parent = list(range(len(items)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj

    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if touch(items[i], items[j]):
                union(i, j)
    groups = {}
    for i in range(len(items)):
        groups.setdefault(find(i), []).append(i)
    return groups


def fremd_frags(items, gruppe):
    """Alle Flaechenfragmente, die NICHT zu dieser Gruppe gehoeren."""
    aus = {}
    drin = set(gruppe)
    for k, it in enumerate(items):
        if it.kind != "frag" or k in drin:
            continue
        aus.setdefault(it.layer, []).append(it.geom)
    return aus


def _punkte(it):
    """Repraesentative Punkte eines Items - fuer Pads und Vias einer, fuer
    Bahnen beide Enden und die Mitte."""
    if it.kind == "track":
        (x0, y0), (x1, y1) = it.geom
        return [(x0, y0), ((x0 + x1) / 2, (y0 + y1) / 2), (x1, y1)]
    if it.kind == "frag":
        return []
    return [it.geom]


def _bruecke(board, net, items, gruppe, main_frags, holes, square=False,
             breite=0.4, max_len=6.0, alle_frags=None):
    """Kurze Leiterbahn von einem verwaisten Cluster in die Hauptflaeche.

    Das Stitching-Via braucht Eigenkupfer UEBER einem Flaechenfragment der
    GEGENlage. Wo das nicht zutrifft - und das ist bei den meisten Resten der
    Fall -, half das Skript bisher gar nicht. Eine gerade Bahn auf DERSELBEN
    Lage kommt oft trotzdem durch: Die Reste liegen meist wenige Millimeter
    neben Kupfer, das schon zur Hauptmasse gehoert.

    Gesucht wird radial: vom Rest aus in 24 Richtungen und in 0,25-mm-
    Schritten, bis ein Punkt in einem Fragment des Hauptclusters derselben
    Lage liegt. Gesetzt wird nur, was seg_clear ueber die ganze Strecke gegen
    Fremdkupfer freigibt. Laenger als max_len wird nicht gebrueckt - das waere
    kein Reparieren mehr, sondern Routen.
    """
    # Ziel ist NICHT nur der Hauptcluster. Zu irgendeinem anderen Cluster zu
    # bruecken genuegt: Die Runden wiederholen sich, und was einmal verbunden
    # ist, waechst beim naechsten Durchlauf mit zusammen. Nur auf den
    # Hauptcluster zu zielen liess fast alle Reste stehen - ihre naechste
    # Flaeche gehoerte meist einem anderen Rest.
    ziel = alle_frags if alle_frags is not None else main_frags
    import math as _m
    for i in gruppe:
        a = items[i]
        if a.kind == "frag":
            continue
        lagen = copper_layers(board) if a.layer is None else [a.layer]
        for pa in _punkte(a):
            # Startpunkte ausserhalb der Platine sind tabu. Das Massepad der
            # Klinkenbuchse ragt absichtlich ueber die Kante; eine Bahn von
            # dort aus faengt im Nichts an und erzeugt prompt einen zweiten
            # Randabstandsfehler.
            if not inside_outline(pa[0], pa[1], square, 0.6):
                continue
            for lay in lagen:
                frags = ziel.get(lay) or []
                if not frags:
                    continue
                for k in range(24):
                    ang = _m.radians(360.0 * k / 24.0)
                    dx, dy = _m.cos(ang), _m.sin(ang)
                    d = 0.5
                    while d <= max_len:
                        x, y = pa[0] + dx * d, pa[1] + dy * d
                        if not inside_outline(x, y, square, 0.6):
                            break
                        if any(contains_margin(fr, x, y) for fr in frags):
                            if all((x - hx) ** 2 + (y - hy) ** 2 >= 1.0
                                   for hx, hy in holes) and \
                               seg_clear(board, lay, pa[0], pa[1], x, y, breite):
                                tr = pcbnew.PCB_TRACK(board)
                                tr.SetStart(pcbnew.VECTOR2I(mm(pa[0]), mm(pa[1])))
                                tr.SetEnd(pcbnew.VECTOR2I(mm(x), mm(y)))
                                tr.SetWidth(mm(breite))
                                tr.SetLayer(lay)
                                tr.SetNet(net)
                                board.Add(tr)
                                print("  Bruecke %.2f mm auf %s (%.2f,%.2f)"
                                      % (d, board.GetLayerName(lay), pa[0], pa[1]))
                                return "track"
                            break
                        d += 0.25
    return False


def connect(name, max_rounds=4):
    pcb = os.path.join(ROOT, "hardware", name, name + ".kicad_pcb")
    for rnd in range(max_rounds):
        board = pcbnew.LoadBoard(pcb)
        net = board.FindNet("PGND")
        holes = hole_positions(board)
        items = collect(board)
        groups = clusters(items)

        def gsize(g):
            tot = 0
            for i in g:
                it = items[i]
                if it.kind == "frag":
                    tot += abs(it.geom.Area()) / 1e12
                else:
                    tot += 1
            return tot

        glist = sorted(groups.values(), key=gsize, reverse=True)
        main = set(glist[0])
        print("Runde %d: %d Cluster (Hauptcluster: %d Elemente)"
              % (rnd + 1, len(glist), len(main)))
        if len(glist) == 1:
            break
        main_frags = {l: [] for l in copper_layers(board)}
        for i in main:
            if items[i].kind == "frag":
                main_frags[items[i].layer].append(items[i].geom)

        placed = 0
        for g in glist[1:]:
            done = False
            for i in g:
                it = items[i]
                if done or it.kind == "frag":
                    continue
                # Kandidatenpunkte auf dem Element
                if it.kind == "track":
                    (x0, y0), (x1, y1) = it.geom
                    steps = max(2, int(math.hypot(x1 - x0, y1 - y0) / 0.3))
                    pts = [(x0 + (x1 - x0) * k / steps,
                            y0 + (y1 - y0) * k / steps)
                           for k in range(steps + 1)]
                    layers_other = [l for l in copper_layers(board)
                                    if l != it.layer]
                else:
                    x, y = it.geom
                    pts = [(x + dx, y + dy)
                           for dx in (-0.3, 0, 0.3) for dy in (-0.3, 0, 0.3)]
                    layers_other = [l for l in copper_layers(board)
                                    if l != it.layer]
                for (x, y) in pts:
                    if done:
                        break
                    for lo in layers_other:
                        hit = any(contains_margin(fr, x, y)
                                  for fr in main_frags[lo])
                        if not hit:
                            continue
                        if not all((x - hx) ** 2 + (y - hy) ** 2 >= 1.0
                                   for hx, hy in holes):
                            continue
                        # Keine Vias in Footprint-Sperrflaechen: Der
                        # SKQG-Taster verbietet Vias unter seinem
                        # Metalldom, und gnd_connect setzte prompt zwei
                        # hinein (20.08.2026).
                        in_sperre = False
                        for z in board.Zones():
                            if (z.GetIsRuleArea()
                                    and z.GetDoNotAllowVias()
                                    and z.HitTestFilledArea(
                                        pcbnew.F_Cu,
                                        pcbnew.VECTOR2I(mm(x), mm(y)), 0)):
                                in_sperre = True
                                break
                            if (z.GetIsRuleArea() and z.GetDoNotAllowVias()
                                    and z.Outline().Contains(
                                        pcbnew.VECTOR2I(mm(x), mm(y)))):
                                in_sperre = True
                                break
                        if in_sperre:
                            continue
                        # Freiraum auf ALLEN Lagen pruefen - das Via geht
                        # durch das ganze Board, nicht nur durch F und B.
                        # Die Suchbreite folgt der VIAGROESSE: Auf Bottom
                        # sind die Bruecken 0,8 breit - mit der alten
                        # 0,6er-Suche wurden sie in 0,6er-Luecken gesetzt
                        # und rissen vier Abstandsfehler (20.08.2026).
                        via_b = 0.8 if "bottom" in name else 0.6
                        if not all(seg_clear(board, l, x, y, x, y, via_b + 0.1)
                                   for l in copper_layers(board)):
                            continue
                        v = pcbnew.PCB_VIA(board)
                        v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
                        # Auf dem Leistungsboard 0,8/0,4: Auch eine
                        # Massebruecke kann im Rueckstrompfad liegen.
                        if "bottom" in name:
                            v.SetWidth(mm(0.8))
                            v.SetDrill(mm(0.4))
                        else:
                            v.SetWidth(mm(0.6))
                            v.SetDrill(mm(0.3))
                        v.SetLayerPair(F, B)
                        v.SetNet(net)
                        board.Add(v)
                        holes.append((x, y))
                        placed += 1
                        print("  Via (%.2f, %.2f)" % (x, y))
                        done = True
                        break
            if not done:
                done = _bruecke(board, net, items, g, main_frags, holes,
                                square=(name == "top_ui"),
                                alle_frags=fremd_frags(items, g))
            if not done:
                sample = items[g[0]]
                print("  Cluster ohne Kandidat (%d Elemente, z.B. %s %s)"
                      % (len(g), sample.kind, sample.geom))
            elif done == "track":
                placed += 1
        pcbnew.SaveBoard(pcb, board)
        board2 = pcbnew.LoadBoard(pcb)
        filler = pcbnew.ZONE_FILLER(board2)
        filler.Fill(board2.Zones())
        pcbnew.SaveBoard(pcb, board2)
        if placed == 0:
            break

    res, errs = run_drc(pcb)
    if errs:
        raise RuntimeError(errs[0])
    print("violations:", dict(res["violations"]))
    print("offen:", classify_unrouted("/tmp/drc_%s.rpt" % name))


if __name__ == "__main__":
    connect(sys.argv[1] if len(sys.argv) > 1 else "mid_logic")
