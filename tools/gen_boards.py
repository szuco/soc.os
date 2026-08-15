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

  ACHTUNG: Dieses Skript SCHREIBT hardware/<slug>/<slug>.kicad_pcb - es
  ueberschreibt also die realen Boarddateien samt Bestueckung und Leiterbahnen.
  Der Regelweg ist tools/gen_layouts.py, das die Boards komplett aus den
  Schaltplan-Generatoren aufbaut. gen_boards.py ist nur noch die Referenz fuer
  die reine Mechanik.
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
# Grad, mathematisch (CCW, 0 = +X). Bohrbild v2: nur noch 0/180 -
# 120/240 kollidierten mit den frueheren Sicheltasten-Stoesseln,
# und andere Winkel sind durch Stackverbinder, ESP32-Antenne und
# Leistungsstecker blockiert. Begruendung in tools/gen_layouts.py.
HOLE_ANGLES      = (0.0, 180.0)
EDGE_CLEARANCE   = 0.5      # mm

# Das TOP-Board ist als einziges NICHT rund: Die Zentralscheibe
# Busch-Jaeger 6435-914 gibt ihren Tastendruck ueber vier Kreuze an den ECKEN
# weiter, bei (+/-18,0 / +/-20,0) - also r = 26,91 und damit ausserhalb einer
# Oe52-Platine. Es wird ein abgerundetes Quadrat und sitzt vor der Dose.
# Siehe docs/04-mechanical.md Abschnitt 1d und Punkt 48 in docs/06.
TOP_SQ           = 47.0     # mm Kantenlaenge
TOP_CR           = 4.0      # mm Eckradius

ANTENNA_KEEPOUT_W = 18.0    # mm; Sperrflaeche ESP32-Antenne (nur MID)
# Nur der echte Antennenabschnitt des WROOM-Moduls (oberste 6,5 mm; das
# Modul ragt 3 mm ueber die Boardkante). Eine groessere Flaeche schliesst
# Signalpads des Moduls ein und macht sie unroutbar - siehe gen_layouts.py.
ANTENNA_KEEPOUT_H = 3.6

FP_LIB = "/usr/share/kicad/footprints/MountingHole.pretty"
FP_NAME = "MountingHole_2.7mm_M2.5"

# slug, Beschriftung, Antennen-Keepout, quadratisch
BOARDS = [
    ("bottom_power_motor", "BOTTOM - Power & Motor", False, False),
    ("mid_logic",          "MID - Logic",            True,  False),
    ("top_ui",             "TOP - Front / UI",       False, True),
]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def mm(v):
    return pcbnew.FromMM(float(v))


def pt(x_mm, y_mm_math):
    """Mathematische Koordinate -> KiCad-Punkt (KiCad zaehlt Y nach unten)."""
    return pcbnew.VECTOR2I(mm(x_mm), mm(-y_mm_math))


def add_outline(board, square=False):
    if not square:
        c = pcbnew.PCB_SHAPE(board)
        c.SetShape(pcbnew.SHAPE_T_CIRCLE)
        c.SetLayer(pcbnew.Edge_Cuts)
        c.SetCenter(pt(0, 0))
        c.SetEnd(pt(BOARD_DIAMETER / 2.0, 0))
        c.SetWidth(mm(0.1))
        board.Add(c)
        return
    h, cr, k = TOP_SQ / 2.0, TOP_CR, 0.7071067811865476
    for a, b in (((-(h - cr), h), ((h - cr), h)),
                 (((h - cr), -h), (-(h - cr), -h)),
                 ((-h, -(h - cr)), (-h, (h - cr))),
                 ((h, (h - cr)), (h, -(h - cr)))):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetStart(pt(*a))
        seg.SetEnd(pt(*b))
        seg.SetWidth(mm(0.1))
        board.Add(seg)
    for sx, sy in ((1, 1), (1, -1), (-1, -1), (-1, 1)):
        cx, cy = sx * (h - cr), sy * (h - cr)
        arc = pcbnew.PCB_SHAPE(board)
        arc.SetShape(pcbnew.SHAPE_T_ARC)
        arc.SetLayer(pcbnew.Edge_Cuts)
        arc.SetArcGeometry(pt(sx * (h - cr), sy * h),
                           pt(cx + sx * k * cr, cy + sy * k * cr),
                           pt(sx * h, sy * (h - cr)))
        arc.SetWidth(mm(0.1))
        board.Add(arc)


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

    top = BOARD_DIAMETER / 2.0 + 0.2
    bot = top - ANTENNA_KEEPOUT_H
    hw = ANTENNA_KEEPOUT_W / 2.0
    outline = zone.Outline()
    outline.NewOutline()
    for x, y in ((-hw, top), (hw, top), (hw, bot), (-hw, bot)):
        outline.Append(mm(x), mm(-y))
    zone.SetZoneName("ESP32_ANTENNA_KEEPOUT")
    board.Add(zone)


def build(slug, label, antenna, square=False):
    board = pcbnew.CreateEmptyBoard()

    ds = board.GetDesignSettings()
    ds.SetBoardThickness(mm(BOARD_THICKNESS))
    ds.m_CopperEdgeClearance = mm(EDGE_CLEARANCE)

    add_outline(board, square)
    holes = add_holes(board)
    add_front_marker(board)

    add_text(board, label, 0, 6.5, size=1.6)
    add_text(board, "SwitchStack  D%.0f  t%.1f" % (BOARD_DIAMETER, BOARD_THICKNESS),
             0, 3.8, size=1.0)
    add_text(board, "FRONT", 0,
             (TOP_SQ / 2.0 if square else BOARD_DIAMETER / 2.0) - 6.2, size=1.0)

    if antenna:
        add_antenna_keepout(board)

    out_dir = os.path.join(ROOT, "hardware", slug)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "%s.kicad_pcb" % slug)
    pcbnew.SaveBoard(path, board)
    return path, holes


def verify(path, expect_antenna, square=False):
    """Datei neu einlesen und den Inhalt gegen die Vorgaben pruefen."""
    errs = []
    b = pcbnew.LoadBoard(path)

    if square:
        edge = [d for d in b.GetDrawings()
                if d.GetClass() == "PCB_SHAPE"
                and d.GetLayer() == pcbnew.Edge_Cuts]
        segs = [d for d in edge if d.GetShape() == pcbnew.SHAPE_T_SEGMENT]
        arcs = [d for d in edge if d.GetShape() == pcbnew.SHAPE_T_ARC]
        if len(segs) != 4 or len(arcs) != 4:
            errs.append("Kontur: %d Geraden / %d Boegen, erwartet 4 / 4"
                        % (len(segs), len(arcs)))
    else:
        circles = [d for d in b.GetDrawings()
                   if d.GetClass() == "PCB_SHAPE"
                   and d.GetShape() == pcbnew.SHAPE_T_CIRCLE
                   and d.GetLayer() == pcbnew.Edge_Cuts]
        if len(circles) != 1:
            errs.append("%d Edge.Cuts-Kreise, erwartet 1" % len(circles))
        else:
            r = pcbnew.ToMM(circles[0].GetRadius())
            if abs(r - BOARD_DIAMETER / 2.0) > 0.01:
                errs.append("Radius %.3f mm, erwartet %.3f"
                            % (r, BOARD_DIAMETER / 2.0))

    fps = list(b.GetFootprints())
    if len(fps) != len(HOLE_ANGLES):
        errs.append("%d Bohrungen, erwartet %d" % (len(fps), len(HOLE_ANGLES)))
    for fp in fps:
        x = pcbnew.ToMM(fp.GetPosition().x)
        y = -pcbnew.ToMM(fp.GetPosition().y)
        rad = math.hypot(x, y)
        if abs(rad - HOLE_PITCH_R) > 0.01:
            errs.append("Bohrung auf r=%.3f mm, erwartet %.3f" % (rad, HOLE_PITCH_R))
        limit = TOP_SQ / 2.0 if square else BOARD_DIAMETER / 2.0
        if rad + 1.35 + EDGE_CLEARANCE > limit:
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
    for slug, label, antenna, square in BOARDS:
        path, holes = build(slug, label, antenna, square)
        errs = verify(path, antenna, square)

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
