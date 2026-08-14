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
from gen_layouts import run_drc                                 # noqa: E402
from route_boards import classify_unrouted                      # noqa: E402
from gnd_stitch import (seg_clear, contains_margin, fragments,  # noqa: E402
                        hole_positions, _seg_dist)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mm = lambda v: pcbnew.FromMM(v)   # noqa: E731

F, B = pcbnew.F_Cu, pcbnew.B_Cu


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
    for layer in (F, B):
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
        main_frags = {F: [], B: []}
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
                    layers_other = [B, F] if it.layer == F else [F, B]
                else:
                    x, y = it.geom
                    pts = [(x + dx, y + dy)
                           for dx in (-0.3, 0, 0.3) for dy in (-0.3, 0, 0.3)]
                    layers_other = [B, F] if it.layer in (F, None) else [F]
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
                        if not (seg_clear(board, F, x, y, x, y, 0.6)
                                and seg_clear(board, B, x, y, x, y, 0.6)):
                            continue
                        v = pcbnew.PCB_VIA(board)
                        v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
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
                sample = items[g[0]]
                print("  Cluster ohne Kandidat (%d Elemente, z.B. %s %s)"
                      % (len(g), sample.kind, sample.geom))
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
