#!/usr/bin/env python3
"""
Erzeugt die mechanischen Board-Templates fuer die drei SwitchStack-Leiterplatten.

Nutzt die pcbnew-Python-API, damit die Dateien von KiCad selbst geschrieben
werden - handgeschriebene .kicad_pcb-Dateien haben sich als nicht zuverlaessig
oeffenbar erwiesen.

    python3 tools/gen_boards.py

Erzeugt je Board eine .kicad_pcb mit:
  - runder Outline auf Edge.Cuts
  - drei Befestigungsbohrungen M2,5 auf gemeinsamem Teilkreis
  - Leiterplattendicke 1,0 mm
  - Frontmarkierung auf 12 Uhr, auf allen Boards gleich orientiert
  - Sperrflaeche fuer die ESP32-Antenne (nur Mid-Board)

WICHTIG: Alle drei Boards teilen dieselben mechanischen Konstanten. Aenderungen
nur hier vornehmen und das Skript neu laufen lassen, damit die Boards nicht
auseinanderlaufen.
"""

import math
import os
import sys

import pcbnew

# ---------------------------------------------------------------------------
# MECHANISCHE KONSTANTEN - gelten fuer alle drei Boards
# ---------------------------------------------------------------------------

BOARD_DIAMETER   = 52.0     # mm; siehe docs/04-mechanical.md, Abschnitt 1
BOARD_THICKNESS  = 1.0      # mm
HOLE_PITCH_R     = 21.5     # mm; Teilkreis der Befestigungsbohrungen
# Grad, mathematisch (CCW, 0 = +X). 12 Uhr bleibt bewusst frei fuer die
# Frontmarkierung und den FRONT-Schriftzug.
HOLE_ANGLES      = (0.0, 120.0, 240.0)
EDGE_CLEARANCE   = 0.5      # mm

ANTENNA_KEEPOUT_W = 18.0    # mm; Sperrflaeche ESP32-Antenne (nur MID)
ANTENNA_KEEPOUT_H = 10.0

FP_LIB = "/usr/share/kicad/footprints/MountingHole.pretty"
FP_NAME = "MountingHole_2.7mm_M2.5"

BOARDS = [
    ("bottom_power_motor", "BOTTOM - Power & Motor", False),
    ("mid_logic",          "MID - Logic",            True),
    ("top_ui",             "TOP - Front / UI",       False),
]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def mm(v):
    return pcbnew.FromMM(float(v))


def pt(x_mm, y_mm_math):
    """Mathematische Koordinate -> KiCad-Punkt (KiCad zaehlt Y nach unten)."""
    return pcbnew.VECTOR2I(mm(x_mm), mm(-y_mm_math))


def add_outline(board):
    c = pcbnew.PCB_SHAPE(board)
    c.SetShape(pcbnew.SHAPE_T_CIRCLE)
    c.SetLayer(pcbnew.Edge_Cuts)
    c.SetCenter(pt(0, 0))
    c.SetEnd(pt(BOARD_DIAMETER / 2.0, 0))
    c.SetWidth(mm(0.1))
    board.Add(c)


def add_holes(board):
    positions = []
    for ang in HOLE_ANGLES:
        a = math.radians(ang)
        x = HOLE_PITCH_R * math.cos(a)
        y = HOLE_PITCH_R * math.sin(a)
        fp = pcbnew.FootprintLoad(FP_LIB, FP_NAME)
        if fp is None:
            raise RuntimeError("Footprint %s nicht ladbar" % FP_NAME)
        fp.SetPosition(pt(x, y))
        board.Add(fp)
        positions.append((ang, x, y))
    return positions


def add_text(board, txt, x, y, size=1.2, layer=None, thickness=0.2):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(txt)
    t.SetLayer(pcbnew.F_SilkS if layer is None else layer)
    t.SetPosition(pt(x, y))
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(thickness))
    board.Add(t)


def add_front_marker(board):
    """Dreieck auf 12 Uhr - definiert die Frontorientierung aller Boards."""
    r = BOARD_DIAMETER / 2.0 - 2.0
    tip, half, depth = r, 1.6, 2.2
    for a, b in (((0, tip), (-half, tip - depth)),
                 ((-half, tip - depth), (half, tip - depth)),
                 ((half, tip - depth), (0, tip))):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetLayer(pcbnew.F_SilkS)
        seg.SetStart(pt(*a))
        seg.SetEnd(pt(*b))
        seg.SetWidth(mm(0.15))
        board.Add(seg)


def add_antenna_keepout(board):
    """Sperrflaeche fuer den ESP32-Antennenbereich, alle Kupferlagen."""
    zone = pcbnew.ZONE(board)
    zone.SetIsRuleArea(True)
    zone.SetDoNotAllowCopperPour(True)
    zone.SetDoNotAllowTracks(True)
    zone.SetDoNotAllowVias(True)
    zone.SetDoNotAllowPads(True)
    zone.SetDoNotAllowFootprints(True)

    lset = pcbnew.LSET()
    for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
        lset.addLayer(lay)
    zone.SetLayerSet(lset)

    top = BOARD_DIAMETER / 2.0 - 1.0
    bot = top - ANTENNA_KEEPOUT_H
    hw = ANTENNA_KEEPOUT_W / 2.0
    outline = zone.Outline()
    outline.NewOutline()
    for x, y in ((-hw, top), (hw, top), (hw, bot), (-hw, bot)):
        outline.Append(mm(x), mm(-y))
    zone.SetZoneName("ESP32_ANTENNA_KEEPOUT")
    board.Add(zone)


def build(slug, label, antenna):
    board = pcbnew.CreateEmptyBoard()

    ds = board.GetDesignSettings()
    ds.SetBoardThickness(mm(BOARD_THICKNESS))
    ds.m_CopperEdgeClearance = mm(EDGE_CLEARANCE)

    add_outline(board)
    holes = add_holes(board)
    add_front_marker(board)

    add_text(board, label, 0, 6.5, size=1.6)
    add_text(board, "SwitchStack  D%.0f  t%.1f" % (BOARD_DIAMETER, BOARD_THICKNESS),
             0, 3.8, size=1.0)
    add_text(board, "FRONT", 0, BOARD_DIAMETER / 2.0 - 6.2, size=1.0)

    if antenna:
        add_antenna_keepout(board)

    out_dir = os.path.join(ROOT, "hardware", slug)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "%s.kicad_pcb" % slug)
    pcbnew.SaveBoard(path, board)
    return path, holes


def verify(path, expect_antenna):
    """Datei neu einlesen und den Inhalt gegen die Vorgaben pruefen."""
    errs = []
    b = pcbnew.LoadBoard(path)

    circles = [d for d in b.GetDrawings()
               if d.GetClass() == "PCB_SHAPE"
               and d.GetShape() == pcbnew.SHAPE_T_CIRCLE
               and d.GetLayer() == pcbnew.Edge_Cuts]
    if len(circles) != 1:
        errs.append("%d Edge.Cuts-Kreise, erwartet 1" % len(circles))
    else:
        r = pcbnew.ToMM(circles[0].GetRadius())
        if abs(r - BOARD_DIAMETER / 2.0) > 0.01:
            errs.append("Radius %.3f mm, erwartet %.3f" % (r, BOARD_DIAMETER / 2.0))

    fps = list(b.GetFootprints())
    if len(fps) != len(HOLE_ANGLES):
        errs.append("%d Bohrungen, erwartet %d" % (len(fps), len(HOLE_ANGLES)))
    for fp in fps:
        x = pcbnew.ToMM(fp.GetPosition().x)
        y = -pcbnew.ToMM(fp.GetPosition().y)
        rad = math.hypot(x, y)
        if abs(rad - HOLE_PITCH_R) > 0.01:
            errs.append("Bohrung auf r=%.3f mm, erwartet %.3f" % (rad, HOLE_PITCH_R))
        if rad + 1.35 + EDGE_CLEARANCE > BOARD_DIAMETER / 2.0:
            errs.append("Bohrung verletzt Randabstand")

    t = pcbnew.ToMM(b.GetDesignSettings().GetBoardThickness())
    if abs(t - BOARD_THICKNESS) > 0.001:
        errs.append("Dicke %.3f mm, erwartet %.3f" % (t, BOARD_THICKNESS))

    zones = [b.GetArea(i) for i in range(b.GetAreaCount())]
    rule_areas = [z for z in zones if z.GetIsRuleArea()]
    if expect_antenna and not rule_areas:
        errs.append("Antennen-Sperrflaeche fehlt")
    if not expect_antenna and rule_areas:
        errs.append("unerwartete Sperrflaeche")

    return errs


def main():
    print("Mechanik: D=%.1f mm, t=%.1f mm, Bohrungen r=%.1f mm @ %s Grad\n"
          % (BOARD_DIAMETER, BOARD_THICKNESS, HOLE_PITCH_R,
             "/".join("%.0f" % a for a in HOLE_ANGLES)))

    ok = True
    ref_holes = None
    for slug, label, antenna in BOARDS:
        path, holes = build(slug, label, antenna)
        errs = verify(path, antenna)

        if ref_holes is None:
            ref_holes = holes
        elif holes != ref_holes:
            errs.append("Bohrbild weicht vom ersten Board ab")

        status = "OK" if not errs else "FEHLER"
        print("%-22s %-7s %s" % (slug, status,
                                 os.path.relpath(path, ROOT)))
        for e in errs:
            print("    ! %s" % e)
            ok = False

    if ref_holes:
        print("\nBohrbild (mathematische Koordinaten, KiCad-Y ist negiert):")
        for ang, x, y in ref_holes:
            print("  %3.0f Grad   x=%+8.4f   y=%+8.4f   (KiCad y=%+8.4f)"
                  % (ang, x, y, -y))

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
