#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Der Tragring-Ersatz - die Platte zwischen Dose und Abdeckrahmen.

Seit dem 19.08.2026 ist die Befestigung zweigeteilt (docs/04):

    Dose  <-schrauben-  TRAGRING (dieses Teil)  <-klemmen-  Abdeckrahmen
                            |
                            |  fuehrt die beiden Huelsen seitlich
                            v
    Bottom =huelse= Mid =huelse= Top -> Scheibenadapter -> Zentralscheibe

Die Platte wird mit den Geraeteschrauben der Dose (60 mm, DIN 49073)
angeschraubt und uebernimmt zwei Aufgaben des originalen Tragrings: Der
Abdeckrahmen klemmt mit seinen Doppelstegen auf ihren Kanten, und die
Zentralscheibe presst ihn beim Verschrauben des Stapels gegen sie.

Das Mid-Board wird NICHT direkt an die Platte geschraubt. Die beiden
M2,5-Huelsen zwischen Mid und Top laufen durch enge Durchgangsbohrungen
dieser Platte - das fixiert den Stapel seitlich. Axial haelt ihn die
Klemmkette: Schraubenkopf -> Top-Board -> Scheibenadapter -> Zentralscheibe
-> Rahmensteg -> diese Platte -> Dose. Wer den Stapel herausnehmen will,
loest zwei Schrauben von vorn.

MASSVORBEHALT: Die Rahmenmasse F11/F13 (docs/04) sind weiterhin ungemessen.
frame_grip = 70 stammt aus der Messung am Adapter-Vorgaenger; die
Klemmhoehe der Doppelstege ist eine Annahme und gehoert zum Testdruck.
"""

import os
import sys

from build123d import (
    BuildPart, BuildSketch, Plane, Rectangle, Circle, Locations, SlotOverall,
    extrude, fillet, Mode, export_step, export_stl, Pos, Box,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "mechanical", "export")

PARAMS = dict(
    # --- Platte ------------------------------------------------------------
    grip              = 70.0,   # Kantenmass; darauf klemmen die Doppelstege
                                # des Rahmens (F13 - Annahme wie bisher)
    t                 = 2.0,    # Plattendicke; gedruckt lieber steif

    # --- Geraeteschrauben der Dose ----------------------------------------
    screw_pitch       = 60.0,   # DIN 49073
    screw_slot_w      = 3.9,
    screw_slot_len    = 4.0,

    # --- Zentrale Oeffnung -------------------------------------------------
    # Durch die Platte muessen: die beiden Stapelverbinder (x +-11,5..16,9,
    # y -3,1..23,3), die Display-FPC in der Mitte und Luft fuer die Kerbe.
    open_x            = 35.0,   # Rechteck, gesamt
    open_y0           = -15.0,
    open_y1           = 24.0,

    # --- Freistellung USB-C ------------------------------------------------
    # Die Buchse greift vom Mid-Board durch die Randkerbe des Top-Boards
    # nach vorn; ihr Koerper liegt bei x -23,5..-17,25, y 3,4..13,4.
    usb_x0            = -24.3,
    usb_x1            = -16.0,
    usb_y0            = 2.4,
    usb_y1            = 14.4,

    # --- Kabeldurchlass fuer den Magnetkontakt -----------------------------
    # Der DCX-909 steckt im Abdeckrahmen unten mittig; sein Kabel laeuft
    # hinter dem Rahmen nach innen zur Kerbe des Top-Boards. Der Ausschnitt
    # reicht bis zur Plattenkante, damit auch der Gewindekoerper des
    # Steckers (8,5 mm lang, Flansch OD 12) nirgends aufsetzt.
    kabel_w           = 12.0,
    kabel_y0          = 26.0,

    # --- Huelsenfuehrung ---------------------------------------------------
    # M2,5-Sechskanthuelsen, Schluesselweite 4,5 -> Eckenmass 5,2.
    huelse_x          = 21.5,   # wie H1/H2 aller drei Boards
    huelse_d          = 6.0,    # Durchgangsloch: fuehrt, klemmt nicht
)


def build_tragring(p=PARAMS):
    half = p["grip"] / 2.0
    with BuildPart() as tp:
        with BuildSketch(Plane.XY) as sk:
            Rectangle(p["grip"], p["grip"])
            fillet(sk.vertices(), 2.0)

            # zentrale Oeffnung
            with Locations((0, (p["open_y0"] + p["open_y1"]) / 2.0)):
                Rectangle(p["open_x"], p["open_y1"] - p["open_y0"],
                          mode=Mode.SUBTRACT)
            # USB-C
            with Locations(((p["usb_x0"] + p["usb_x1"]) / 2.0,
                            (p["usb_y0"] + p["usb_y1"]) / 2.0)):
                Rectangle(p["usb_x1"] - p["usb_x0"],
                          p["usb_y1"] - p["usb_y0"], mode=Mode.SUBTRACT)
            # Kabeldurchlass, offen zur Kante
            with Locations((0, (p["kabel_y0"] + half) / 2.0)):
                Rectangle(p["kabel_w"], half - p["kabel_y0"] + 1.0,
                          mode=Mode.SUBTRACT)
            # Geraeteschrauben
            for sx in (p["screw_pitch"] / 2.0, -p["screw_pitch"] / 2.0):
                with Locations((sx, 0)):
                    SlotOverall(p["screw_slot_len"] + p["screw_slot_w"],
                                p["screw_slot_w"], rotation=90,
                                mode=Mode.SUBTRACT)
            # Huelsenfuehrungen
            for sx in (p["huelse_x"], -p["huelse_x"]):
                with Locations((sx, 0)):
                    Circle(p["huelse_d"] / 2.0, mode=Mode.SUBTRACT)
        extrude(amount=p["t"])
    return tp.part


def check_tragring(part, p=PARAMS):
    """Zwangsbedingungen und Materialproben."""
    errs = []
    half = p["grip"] / 2.0

    # Huelsenloch muss ausserhalb der Oeffnung liegen, sonst fuehrt nichts.
    if p["huelse_x"] - p["huelse_d"] / 2.0 < p["open_x"] / 2.0:
        errs.append("Huelsenloch schneidet die zentrale Oeffnung")
    # Geraeteschrauben ausserhalb von allem
    if p["screw_pitch"] / 2.0 - p["screw_slot_w"] < p["huelse_x"] + p["huelse_d"] / 2.0:
        errs.append("Schraubschlitz kollidiert mit Huelsenfuehrung")
    # Der Rahmensteg (Fensteroeffnung ~50, Steg bis ~55) braucht Auflage:
    # bei y = +-26 muss die Platte tragen - ausser im Kabeldurchlass.
    for name, (x, y) in (("Stegauflage oben", (0.0, -26.0)),
                         ("Stegauflage links", (-26.0, 0.0)),
                         ("Stegauflage rechts", (26.0, 0.0))):
        if (part & Pos(x, y, p["t"] / 2.0) * Box(0.6, 0.6, p["t"] - 0.4)).volume < 1e-6:
            errs.append("kein Material: %s" % name)
    # Kabeldurchlass frei
    if (part & Pos(0, half - 2.0, p["t"] / 2.0) * Box(4.0, 2.0, p["t"] + 1.0)).volume > 1e-6:
        errs.append("Kabeldurchlass nicht frei")
    # Huelsenfuehrung frei
    for sx in (p["huelse_x"], -p["huelse_x"]):
        if (part & Pos(sx, 0, p["t"] / 2.0) * Box(4.0, 4.0, p["t"] + 1.0)).volume > 1e-6:
            errs.append("Huelsenfuehrung x=%+.1f nicht frei" % sx)
    return errs


def main():
    p = PARAMS
    part = build_tragring(p)
    errs = check_tragring(part, p)
    os.makedirs(OUT, exist_ok=True)
    export_step(part, os.path.join(OUT, "tragring.step"))
    export_stl(part, os.path.join(OUT, "tragring.stl"))
    print("Selbsttest   : %s" % ("BESTANDEN" if not errs else "FEHLGESCHLAGEN"))
    for e in errs:
        print("   ! %s" % e)
    print("Platte       : %.0f x %.0f x %.1f mm" % (p["grip"], p["grip"], p["t"]))
    print("Oeffnung     : %.0f x %.0f, USB und Kabeldurchlass extra"
          % (p["open_x"], p["open_y1"] - p["open_y0"]))
    print("Huelsen      : M2,5 bei x = +-%.1f, Fuehrung Ø %.1f"
          % (p["huelse_x"], p["huelse_d"]))
    print("Export       : %s" % OUT)
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
