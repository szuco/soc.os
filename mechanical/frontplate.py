#!/usr/bin/env python3
"""
KiCad SwitchStack - Frontplatte fuer 55x55-Schalterprogramme.

Parametrisches Modell einer kombinierten Zentralplatte + Tragring, die in die
Rahmen (Blenden) gaengiger 55er-Schalterprogramme passt (Gira System 55,
Jung A/AS, Berker S.1/B.x, Merten M-Smart, Busch-Jaeger 55er-Linien).

Erzeugt STEP (fuer FreeCAD/KiCad) und STL (fuer den 3D-Druck).

    python3 mechanical/frontplate.py

Alle Masse in mm. Aenderungen ausschliesslich im PARAMS-Block vornehmen.
"""

from pathlib import Path
import math

from build123d import (
    BuildPart, BuildSketch, Plane, Rectangle, Circle, SlotOverall, Locations,
    extrude, fillet, chamfer, Mode, export_step, export_stl, Axis,
)

# ---------------------------------------------------------------------------
# PARAMETER
# ---------------------------------------------------------------------------

PARAMS = dict(
    # --- Zentralplatte (Sichtflaeche im Rahmenausschnitt) -------------------
    plate_size        = 54.6,   # 55er-Norm; 0,4 mm Untermass fuer Druckertoleranz
    plate_thickness   = 2.5,
    plate_corner_r    = 2.0,
    plate_edge_cham   = 0.5,    # Fase an der Sichtkante

    # --- Zentrierbund nach hinten (fuehrt die Platte im Rahmen) ------------
    # Umlaufender Kragen, KEIN massiver Block - dahinter sitzt das Display.
    boss_size         = 50.0,
    boss_wall         = 2.0,
    boss_depth        = 3.0,

    # --- Tragring-Ohren mit Geraeteschrauben (DIN 49073, 60 mm Abstand) ----
    ear_span          = 76.0,   # Gesamtbreite ueber beide Ohren
    ear_width         = 14.0,
    ear_thickness     = 2.5,
    screw_pitch       = 60.0,   # Achsabstand der Geraeteschrauben
    screw_slot_len    = 4.0,    # Langloch (vertikal) zum Ausrichten
    screw_slot_w      = 3.9,    # M3,5 Geraeteschraube mit Spiel

    # --- Displayfenster (rund, 1.28" GC9A01 240x240) -----------------------
    disp_window_d     = 32.0,   # Sichtoeffnung; aktive Flaeche ~32,4 mm
    disp_rebate_d     = 37.0,   # Rueckseitige Tasche fuer das Modul
    disp_rebate_depth = 1.2,

    # --- Taster ------------------------------------------------------------
    btn_count         = 4,
    btn_hole_d        = 7.0,    # Durchbruch fuer den Tastenstoessel
    btn_radius        = 22.5,   # Teilkreis um die Plattenmitte
    btn_angle0        = 45.0,   # erster Taster auf 45 Grad (Ecken)

    # --- Kabelausgang Weihnachtsstern --------------------------------------
    star_exit         = True,
    star_exit_d       = 4.5,
    star_exit_y       = -20.5,  # unten mittig, innerhalb des Kragens

    # --- USB-C Zugang ------------------------------------------------------
    # False = nur bei abgenommener Blende erreichbar (empfohlen, saubere Front)
    usb_slot          = False,
    usb_slot_w        = 10.0,
    usb_slot_h        = 4.0,
    usb_slot_y        = 20.5,
)


def build(p=PARAMS):
    """Baut die Frontplatte und gibt das Solid zurueck."""

    with BuildPart() as fp:

        # -- Zentralplatte --------------------------------------------------
        with BuildSketch(Plane.XY) as s_plate:
            Rectangle(p["plate_size"], p["plate_size"])
            fillet(s_plate.vertices(), p["plate_corner_r"])
        extrude(amount=p["plate_thickness"])

        # -- Tragring-Ohren, nach hinten (negatives Z) ----------------------
        with BuildSketch(Plane.XY) as s_ears:
            Rectangle(p["ear_span"], p["ear_width"])
        extrude(amount=-p["ear_thickness"], mode=Mode.ADD)

        # -- Zentrierbund als umlaufender Kragen ----------------------------
        with BuildSketch(Plane.XY.offset(-p["ear_thickness"])) as s_boss:
            Rectangle(p["boss_size"], p["boss_size"])
            Rectangle(p["boss_size"] - 2 * p["boss_wall"],
                      p["boss_size"] - 2 * p["boss_wall"], mode=Mode.SUBTRACT)
        extrude(amount=-p["boss_depth"], mode=Mode.ADD)

        # Gesamttiefe hinter der Sichtflaeche - alle Durchbrueche gehen
        # ueber die volle Tiefe, damit Modul, Stoessel und Kabel frei liegen.
        back = p["ear_thickness"] + p["boss_depth"]

        # -- Freiraum hinter dem Displayfenster -----------------------------
        # Raeumt die Ohren im Zentrum aus, sodass das Modul einbauen kann.
        with BuildSketch(Plane.XY) as s_clear:
            Circle(p["disp_rebate_d"] / 2)
        extrude(amount=-back, mode=Mode.SUBTRACT)

        # -- Displayfenster (Sichtoeffnung, bildet die Blende) --------------
        with BuildSketch(Plane.XY) as s_win:
            Circle(p["disp_window_d"] / 2)
        extrude(amount=p["plate_thickness"], mode=Mode.SUBTRACT)

        # -- Taster, volle Tiefe fuer die Stoessel --------------------------
        btn_pts = []
        for i in range(p["btn_count"]):
            a = math.radians(p["btn_angle0"] + i * 360.0 / p["btn_count"])
            btn_pts.append((p["btn_radius"] * math.cos(a),
                            p["btn_radius"] * math.sin(a)))
        with BuildSketch(Plane.XY.offset(p["plate_thickness"])) as s_btn:
            with Locations(*btn_pts):
                Circle(p["btn_hole_d"] / 2)
        extrude(amount=-(p["plate_thickness"] + back), mode=Mode.SUBTRACT)

        # -- Schraubenlanglocher --------------------------------------------
        with BuildSketch(Plane.XY) as s_slots:
            with Locations((p["screw_pitch"] / 2, 0), (-p["screw_pitch"] / 2, 0)):
                SlotOverall(p["screw_slot_len"] + p["screw_slot_w"],
                            p["screw_slot_w"], rotation=90)
        extrude(amount=-p["ear_thickness"], mode=Mode.SUBTRACT)

        # -- Kabelausgang Stern ---------------------------------------------
        if p["star_exit"]:
            with BuildSketch(Plane.XY.offset(p["plate_thickness"])) as s_star:
                with Locations((0, p["star_exit_y"])):
                    Circle(p["star_exit_d"] / 2)
            extrude(amount=-(p["plate_thickness"] + back), mode=Mode.SUBTRACT)

        # -- optionaler USB-C-Schlitz ---------------------------------------
        if p["usb_slot"]:
            with BuildSketch(Plane.XY.offset(p["plate_thickness"])) as s_usb:
                with Locations((0, p["usb_slot_y"])):
                    SlotOverall(p["usb_slot_w"], p["usb_slot_h"])
            extrude(amount=-(p["plate_thickness"] + back), mode=Mode.SUBTRACT)

        # -- Sichtkante brechen ---------------------------------------------
        top_edges = fp.faces().sort_by(Axis.Z)[-1].edges()
        try:
            chamfer(top_edges, p["plate_edge_cham"])
        except Exception:                      # pragma: no cover
            pass                               # Fase ist rein kosmetisch

    return fp.part


def check(part, p=PARAMS):
    """Geometrische Selbsttests. Gibt die Liste der Fehler zurueck (leer = ok)."""
    from build123d import Cylinder, Pos, Location

    errs = []
    back = p["ear_thickness"] + p["boss_depth"]
    full = p["plate_thickness"] + back

    if len(part.solids()) != 1:
        errs.append(f"Bauteil besteht aus {len(part.solids())} Solids, erwartet 1 "
                    f"(sonst nicht druckbar)")

    bb = part.bounding_box()
    for name, got, want in (("Breite ueber Ohren", bb.size.X, p["ear_span"]),
                            ("Hoehe Platte", bb.size.Y, p["plate_size"]),
                            ("Gesamttiefe", bb.size.Z, full)):
        if abs(got - want) > 0.01:
            errs.append(f"{name}: {got:.2f} mm, erwartet {want:.2f} mm")

    def clear(probe, label):
        """Probevolumen muss vollstaendig frei sein."""
        v = (part & probe).volume
        if v > 1e-6:
            errs.append(f"{label}: {v:.1f} mm3 Material im Freiraum")

    # Displayfenster und der Raum dahinter muessen durchgaengig frei sein
    clear(Pos(0, 0, (p["plate_thickness"] - back) / 2)
          * Cylinder(p["disp_window_d"] / 2, full), "Displaydurchbruch")

    # Jedes Tasterloch muss durchgaengig frei sein
    for i in range(p["btn_count"]):
        a = math.radians(p["btn_angle0"] + i * 360.0 / p["btn_count"])
        x, y = p["btn_radius"] * math.cos(a), p["btn_radius"] * math.sin(a)
        clear(Pos(x, y, (p["plate_thickness"] - back) / 2)
              * Cylinder(p["btn_hole_d"] / 2, full), f"Taster {i + 1}")

    # Kabelausgang Stern
    if p["star_exit"]:
        clear(Pos(0, p["star_exit_y"], (p["plate_thickness"] - back) / 2)
              * Cylinder(p["star_exit_d"] / 2, full), "Kabelausgang Stern")

    # Geraeteschrauben muessen durch die Ohren gehen
    for sx in (p["screw_pitch"] / 2, -p["screw_pitch"] / 2):
        clear(Pos(sx, 0, -p["ear_thickness"] / 2)
              * Cylinder(p["screw_slot_w"] / 2, p["ear_thickness"]),
              f"Schraubenloch x={sx:+.0f}")

    # Die Sichtflaeche muss zwischen Fenster und Tastern Material behalten
    ring_r = (p["disp_window_d"] / 2 + p["btn_radius"] - p["btn_hole_d"] / 2) / 2
    probe = Pos(ring_r, 0, p["plate_thickness"] / 2) * Cylinder(0.4, p["plate_thickness"])
    if (part & probe).volume < 1e-6:
        errs.append("Steg zwischen Displayfenster und Tastern fehlt")

    return errs


def main():
    out = Path(__file__).parent / "export"
    out.mkdir(exist_ok=True)
    part = build()

    errs = check(part)
    for e in errs:
        print(f"  FEHLER: {e}")
    print(f"Selbsttest   : {'BESTANDEN' if not errs else str(len(errs)) + ' FEHLER'}")

    export_step(part, str(out / "frontplate.step"))
    export_stl(part, str(out / "frontplate.stl"))

    bb = part.bounding_box()
    print(f"Volumen      : {part.volume / 1000:.2f} cm3")
    print(f"Bounding box : {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f} mm")
    print(f"Z von/bis    : {bb.min.Z:.2f} .. {bb.max.Z:.2f} mm")
    print(f"Solid        : {len(part.solids())} Solid(s)")
    print(f"Export       : {out}")


if __name__ == "__main__":
    main()
