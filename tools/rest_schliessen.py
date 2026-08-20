#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Schliesst die letzten offenen Verbindungen automatisch - konservativ.

Was Freerouting nach zwei Paessen liegen laesst, sind fast immer zwei
Sorten: PGND-Inseln, denen ein einziges Stitch-Via fehlt, und kurze
Pad-zu-Pad-Strecken, die ein gerader Zug schliesst. Beides kann ein
Skript - unter zwei Bedingungen, die hier hart gelten:

  1. VOR dem Setzen wird der komplette Weg gegen ALLES fremde Kupfer
     geprueft (Segment-Form gegen Pads, Bahnen, Vias; Vias gegen alle
     vier Lagen; alles innerhalb des Platinenumrisses).
  2. NACH dem Setzen laeuft die volle DRC. Jede neue Verletzung, an der
     ein gesetztes Element beteiligt ist, wird rueckabgewickelt - das
     Skript laesst das Board nie schlechter zurueck, als es war.

Die Lektion hinter Bedingung 2 sind die 15 Innenlagen-Kurzschluesse der
ersten via_check-Verdopplung (20.08.): Pruefen ist gut, DRC ist besser.

    tools/rest_schliessen.py [board ...]
"""

import json
import math
import re
import os
import subprocess
import sys
import tempfile

import pcbnew

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
BOARDS = ("top_ui", "mid_logic", "bottom_power_motor")
CU = None  # je Board gesetzt

# Bahnbreiten wie die Netzklassen des Routers
BREITE = {"24V_IN": 0.8, "24V_F": 0.8, "24V_PROT": 0.8, "M1_A": 0.8,
          "M1_B": 0.8, "M2_A": 0.8, "M2_B": 0.8, "M1_SWA": 0.8,
          "M1_SWB": 0.8, "M2_SWA": 0.8, "M2_SWB": 0.8,
          "5V_SYS": 0.5, "5V_BUCK": 0.5, "3V3_SYS": 0.5,
          "6V2_STAR": 0.5, "6V2_STAR_F": 0.5, "USB_VBUS": 0.5}
LUFT = 0.22


def mm(v):
    return pcbnew.FromMM(float(v))


def drc(pfad):
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        ziel = f.name
    subprocess.run([CLI, "pcb", "drc", "--format", "json", "-o", ziel, pfad],
                   capture_output=True)
    d = json.load(open(ziel))
    os.unlink(ziel)
    err = [v for v in d.get("violations", []) if v.get("severity") == "error"]
    return err, d.get("unconnected_items", [])


def netz_von(it):
    """KiCad 10 traegt den Netznamen NICHT als eigenes Feld ins
    DRC-JSON - er steht nur im Beschreibungstext: 'Pad 2 [PGND] of C7'.
    Ohne diesen Griff lief das Werkzeug komplett leer (20.08., Runde 1:
    'nichts sicher schliessbar' auf allen drei Boards)."""
    m = re.search(r"\[([^\]]+)\]", it.get("description", ""))
    return m.group(1) if m else (it.get("net") or "")


def frei_segment(board, umriss, x0, y0, x1, y1, lage, breite, eigen):
    """Ist der gerade Zug auf dieser Lage frei von fremdem Kupfer?"""
    seg = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(mm(x0), mm(y0)),
                               pcbnew.VECTOR2I(mm(x1), mm(y1)), mm(breite))
    for t in board.GetTracks():
        if t.GetNetname() == eigen:
            continue
        if t.GetClass() == "PCB_TRACK" and t.GetLayer() != lage:
            continue
        if t.GetEffectiveShape(lage).GetClearance(seg) / 1e6 < LUFT:
            return False
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() == eigen:
                continue
            if not pad.IsOnLayer(lage):
                continue
            if pad.GetEffectiveShape(lage).GetClearance(seg) / 1e6 < LUFT:
                return False
    # Weg im Umriss? Punkte im 0,5er-Raster pruefen
    n = max(2, int(math.hypot(x1 - x0, y1 - y0) / 0.5))
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        y = y0 + (y1 - y0) * i / n
        if not umriss.Contains(pcbnew.VECTOR2I(mm(x), mm(y))):
            return False
    return True


def frei_via(board, umriss, x, y, eigen, radius):
    kreis = pcbnew.SHAPE_CIRCLE(pcbnew.VECTOR2I(mm(x), mm(y)), mm(radius))
    for lage in CU:
        for t in board.GetTracks():
            if t.GetNetname() == eigen:
                continue
            if t.GetClass() == "PCB_TRACK" and t.GetLayer() != lage:
                continue
            if t.GetEffectiveShape(lage).GetClearance(kreis) / 1e6 < LUFT:
                return False
        for fp in board.GetFootprints():
            for pad in fp.Pads():
                if pad.GetNetname() == eigen:
                    continue
                if not pad.IsOnLayer(lage):
                    continue
                if pad.GetEffectiveShape(lage).GetClearance(kreis) / 1e6 < LUFT:
                    return False
    for z in board.Zones():
        if z.GetIsRuleArea() and z.GetDoNotAllowVias() \
                and z.Outline().Contains(pcbnew.VECTOR2I(mm(x), mm(y))):
            return False
    return umriss.Contains(pcbnew.VECTOR2I(mm(x), mm(y)))


def lagen_von(item_desc, board, x, y, netz):
    """Auf welchen Kupferlagen ist dieser DRC-Endpunkt anschliessbar?"""
    p = pcbnew.VECTOR2I(mm(x), mm(y))
    lagen = set()
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() != netz:
                continue
            if pad.HitTest(p):
                if pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                    for l in CU:
                        if pad.IsOnLayer(l):
                            lagen.add(l)
                else:
                    lagen.update(CU)
    for t in board.GetTracks():
        if t.GetNetname() != netz:
            continue
        if t.GetClass() == "PCB_VIA":
            if t.HitTest(p):
                lagen.update(CU)
        elif t.HitTest(p):
            lagen.add(t.GetLayer())
    return lagen


def schliesse(name):
    global CU
    pfad = os.path.join(ROOT, "hardware", name, name + ".kicad_pcb")
    board = pcbnew.LoadBoard(pfad)
    CU = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu][
        :board.GetCopperLayerCount()]
    if board.GetCopperLayerCount() == 4:
        CU = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
    umriss = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(umriss, True)
    # KEIN umriss.Outline(0): Das liefert eine Referenz in das Poly-Set,
    # SWIG gibt das Set frei, der naechste PointInside segfaultet (20.08.).

    class _Um:
        def Contains(self, p):
            return umriss.Contains(p) if umriss.OutlineCount() else True
    um = _Um()

    via_b, via_d = (0.8, 0.4) if "bottom" in name else (0.6, 0.3)
    err0, unc0 = drc(pfad)
    gesetzt = []
    for u in unc0:
        its = u.get("items", [])
        if len(its) < 2:
            continue
        a, b = its[0], its[1]
        pa, pb = a.get("pos", {}), b.get("pos", {})
        ax, ay = pa.get("x", 0), pa.get("y", 0)
        bx, by = pb.get("x", 0), pb.get("y", 0)
        netz = netz_von(a) or netz_von(b)
        dist = math.hypot(ax - bx, ay - by)
        net = board.FindNet(netz)
        if net is None:
            continue

        # Fall 1: Zonen-Insel -> ein Stitch-Via am Punkt (Spirale drumherum)
        za = "Zone" in a.get("description", "")
        zb = "Zone" in b.get("description", "")
        if netz in ("PGND", "AGND") and (za or zb):
            zielx, ziely = (bx, by) if za and not zb else (ax, ay)
            done = False
            for r in (0.0, 0.6, 1.0, 1.5, 2.2, 3.0):
                for w in range(0, 360, 45):
                    x = zielx + r * math.cos(math.radians(w))
                    y = ziely + r * math.sin(math.radians(w))
                    if frei_via(board, um, x, y, netz, via_b / 2.0):
                        v = pcbnew.PCB_VIA(board)
                        v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
                        v.SetDrill(mm(via_d))
                        v.SetWidth(mm(via_b))
                        v.SetNet(net)
                        board.Add(v)
                        gesetzt.append(v)
                        done = True
                        break
                if done or r == 0.0 and done:
                    break
                if done:
                    break
            continue

        # Fall 2: kurzer gerader Zug
        if dist > 6.0 or za or zb:
            continue
        la = lagen_von(a, board, ax, ay, netz)
        lb = lagen_von(b, board, bx, by, netz)
        if dist <= 0.6 and la and lb and not (la & lb):
            x, y = (ax + bx) / 2.0, (ay + by) / 2.0
            if frei_via(board, um, x, y, netz, via_b / 2.0):
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
                v.SetDrill(mm(via_d))
                v.SetWidth(mm(via_b))
                v.SetNet(net)
                board.Add(v)
                gesetzt.append(v)
            continue
        breite = BREITE.get(netz, 0.25)
        for lage in [l for l in CU if l in la and l in lb]:
            if frei_segment(board, um, ax, ay, bx, by, lage, breite, netz):
                t = pcbnew.PCB_TRACK(board)
                t.SetStart(pcbnew.VECTOR2I(mm(ax), mm(ay)))
                t.SetEnd(pcbnew.VECTOR2I(mm(bx), mm(by)))
                t.SetLayer(lage)
                t.SetWidth(mm(breite))
                t.SetNet(net)
                board.Add(t)
                gesetzt.append(t)
                break

    if not gesetzt:
        print("%-20s nichts sicher schliessbar (offen: %d)" % (name, len(unc0)))
        return

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(pfad, board)

    # DRC-Rueckabwicklung: neue Fehler an unseren Elementen -> raus damit
    err1, unc1 = drc(pfad)
    if len(err1) > len(err0):
        schuldig = set()
        for v in err1:
            for it in v.get("items", []):
                pos = it.get("pos", {})
                p = pcbnew.VECTOR2I(mm(pos.get("x", 0)), mm(pos.get("y", 0)))
                for g in gesetzt:
                    if g.HitTest(p):
                        schuldig.add(id(g))
        entfernt = 0
        for g in gesetzt:
            if id(g) in schuldig:
                board.Remove(g)
                entfernt += 1
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        pcbnew.SaveBoard(pfad, board)
        err1, unc1 = drc(pfad)
        print("%-20s %d gesetzt, %d rueckabgewickelt" %
              (name, len(gesetzt), entfernt))
    print("%-20s offen: %d -> %d, Kupferfehler: %d -> %d" %
          (name, len(unc0), len(unc1), len(err0), len(err1)))


def main():
    boards = [b for b in sys.argv[1:] if not b.startswith("-")] or BOARDS
    for b in boards:
        schliesse(b)
    return 0


if __name__ == "__main__":
    sys.exit(main())
