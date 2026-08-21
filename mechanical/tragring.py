#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Der Tragring-Ersatz - die Platte zwischen Dose und Abdeckrahmen.

Seit dem 19.08.2026 ist die Befestigung zweigeteilt (docs/04):

    Dose  <-schrauben-  TRAGRING (dieses Teil)  <-klemmen-  Abdeckrahmen
                            |
                            |  zentriert den Scheibenadapter in der Oeffnung
                            v
    Bottom =huelse= Mid =huelse= Top -> Scheibenadapter -> Zentralscheibe

Die Platte wird mit den Geraeteschrauben der Dose (60 mm, DIN 49073)
angeschraubt und uebernimmt zwei Aufgaben des originalen Tragrings: Der
Abdeckrahmen klemmt mit seinen Doppelstegen auf ihren Kanten, und die
Zentralscheibe presst ihn beim Verschrauben des Stapels gegen sie.

Das Mid-Board wird NICHT direkt an die Platte geschraubt, und auch die
Huelsen laufen frei durch die grosse Oeffnung: Seitlich gefuehrt wird der
Stapel dadurch, dass der 49,8er Basisring des Scheibenadapters mit 0,4 mm
Spiel in der 50,6er Oeffnung sitzt. Axial haelt die Klemmkette:
Schraubenkopf -> Top-Board -> Scheibenadapter -> Zentralscheibe ->
Rahmensteg -> diese Platte -> Dose. Wer den Stapel herausnehmen will,
loest zwei Schrauben von vorn.

MASSVORBEHALT: Die Rahmenmasse F11/F13 (docs/04) sind weiterhin ungemessen.
frame_grip = 70 stammt aus der Messung am Adapter-Vorgaenger; die
Klemmhoehe der Doppelstege ist eine Annahme und gehoert zum Testdruck.

KOORDINATEN - die Falle vom 21.08.2026
--------------------------------------
Alle PARAMS unten stehen in LAYOUT-Koordinaten, also wie in KiCad:
x nach rechts, y NACH UNTEN. build123d (und der STEP-Export von KiCad)
zaehlen y dagegen NACH OBEN. Jede Feature-Lage, die aus dem Layout
kommt, wird deshalb beim Bauen mit -y gespiegelt; die Parameter selbst
bleiben vergleichbar mit gen_layouts.py, und die Zeichnungen, die sie
lesen, stimmen weiter.

Gefunden hat das der Nutzer mit blossem Auge ("warum hat der Tragring
oben eine Aussparung?"). Nachgemessen am exportierten Top-Board: Die
USB-Randkerbe steht im Layout bei y = +8 und im STEP bei y = -8.
Betroffen waren drei Ausschnitte - USB-Freistellung, Kabeldurchlass
und Steckertunnel -, alle drei auf der falschen Seite.
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
    # 50,6 im Quadrat - gross genug, dass der GANZE Scheibenadapter
    # (Basisring 49,8) hindurchtaucht. Die Oeffnung zentriert ihn dabei mit
    # 0,4 mm Spiel je Seite; eigene Huelsenfuehrungen und eine
    # USB-Freistellung braucht es damit nicht mehr, beides liegt innerhalb.
    # Kleiner ging es nicht: Eine 35er Oeffnung kollidierte mit dem
    # Basisring im Tiefenband der Platte (19.08.2026). ACHTUNG Rastnasen:
    # Die Nasen der Scheibe fahren auf lichte 50,0 - zwischen Nase und
    # Oeffnungskante bleiben 0,3 mm. In den Testdruck aufnehmen.
    open_sq           = 50.6,

    # --- Kabeldurchlass fuer den Magnetkontakt -----------------------------
    # Der DCX-909 steckt im Abdeckrahmen unten mittig; sein Kabel laeuft
    # hinter dem Rahmen nach innen zur Kerbe des Top-Boards. Der Ausschnitt
    # reicht bis zur Plattenkante, damit auch der Gewindekoerper des
    # Steckers (8,5 mm lang, Flansch OD 12) nirgends aufsetzt.
    kabel_w           = 12.0,
    kabel_y0          = 26.0,

)


def build_tragring(p=PARAMS):
    half = p["grip"] / 2.0
    with BuildPart() as tp:
        with BuildSketch(Plane.XY) as sk:
            Rectangle(p["grip"], p["grip"])
            fillet(sk.vertices(), 2.0)

            # zentrale Oeffnung - der Scheibenadapter taucht hindurch
            Rectangle(p["open_sq"], p["open_sq"], mode=Mode.SUBTRACT)
            # Kabeldurchlass, offen zur Kante
            # -y: kabel_y0 ist Layout-Koordinate (unten = +y in KiCad)
            with Locations((0, -(p["kabel_y0"] + half) / 2.0)):
                Rectangle(p["kabel_w"], half - p["kabel_y0"] + 1.0,
                          mode=Mode.SUBTRACT)
            # KEINE Bajonettschlitze mehr (Konzept v3, 21.08.): Die Dose
            # hat Dome auf allen vier Achsen, die Kartusche ist seitdem
            # von hinten durch den Becherboden verschraubt (gehaeuse.py).
            # Die Platte liegt lose auf dem Becherrand.
            # Geraeteschrauben
            for sx in (p["screw_pitch"] / 2.0, -p["screw_pitch"] / 2.0):
                with Locations((sx, 0)):
                    SlotOverall(p["screw_slot_len"] + p["screw_slot_w"],
                                p["screw_slot_w"], rotation=90,
                                mode=Mode.SUBTRACT)
        extrude(amount=p["t"])
    return tp.part


def check_tragring(part, p=PARAMS):
    """Zwangsbedingungen und Materialproben."""
    errs = []
    half = p["grip"] / 2.0

    # Der Scheibenadapter (49,8) muss durch die Oeffnung passen - das ist
    # seit dem 19.08.2026 die zentrale Bedingung dieses Teils.
    from adapter import PARAMS as AP
    rand_adapter = AP["snap_inner"] - AP["rim_play"]
    if p["open_sq"] <= rand_adapter:
        errs.append("Oeffnung %.1f laesst den Scheibenadapter %.1f nicht "
                    "durch" % (p["open_sq"], rand_adapter))
    if p["open_sq"] - rand_adapter > 1.6:
        errs.append("Oeffnung %.1f fuehrt den Adapter %.1f nicht mehr - "
                    "mehr als 0,8 mm Spiel je Seite"
                    % (p["open_sq"], rand_adapter))
    # Geraeteschrauben muessen im Plattenmaterial liegen
    if p["screw_pitch"] / 2.0 - p["screw_slot_w"] < p["open_sq"] / 2.0:
        errs.append("Schraubschlitz schneidet die zentrale Oeffnung")
    # Der Rahmensteg (Fensteroeffnung ~50, Steg bis ~55) braucht Auflage:
    # bei y = +-26 muss die Platte tragen - ausser im Kabeldurchlass.
    for name, (x, y) in (("Stegauflage oben", (10.0, -26.0)),
                         ("Stegauflage links", (-26.0, 10.0)),
                         ("Stegauflage rechts", (26.0, -10.0))):
        if (part & Pos(x, y, p["t"] / 2.0) * Box(0.6, 0.6, p["t"] - 0.4)).volume < 1e-6:
            errs.append("kein Material: %s" % name)
    # Kabeldurchlass frei
    if (part & Pos(0, -(half - 2.0), p["t"] / 2.0)
            * Box(4.0, 2.0, p["t"] + 1.0)).volume > 1e-6:
        errs.append("Kabeldurchlass nicht frei")
    # Die Oeffnung selbst frei - auch dort, wo frueher USB-Freistellung
    # und Huelsenfuehrungen extra geschnitten waren.
    for name, (x, y) in (("USB-Zone", (-20.0, 8.4)),
                         ("Huelse rechts", (21.5, 0.0)),
                         ("Huelse links", (-21.5, 0.0))):
        if (part & Pos(x, y, p["t"] / 2.0) * Box(3.0, 3.0, p["t"] + 1.0)).volume > 1e-6:
            errs.append("nicht frei: %s" % name)
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
    print("Oeffnung     : %.1f im Quadrat - Adapter 49,8 taucht durch und "
          "wird zentriert" % p["open_sq"])
    print("Export       : %s" % OUT)
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
