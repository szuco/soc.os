#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Das Gehaeuse um Bottom und Mid - ein verschraubter Becher unterm Tragring.

Gewuenscht am 20.08.2026: Bottom und Mid sollen in der Dose verschwinden,
fixiert, nur der Feldstecker bleibt von hinten zugaenglich. Der Becher
kapselt beide Boards; die Kartusche Becher + Bottom + Mid haelt mit zwei
Schrauben von hinten durch den Boden (Konzept v3, unten). Der Tragring
liegt lose auf dem Becherrand und kommt mit den Geraeteschrauben an die
Dose - erst dann ist alles eine Einheit.

DIE DOME - und warum der Becher VIER Fenster hat (F16 gemessen 21.08.):

    Dose, lichte Weite             58 mm   (F16a/b)
    ueber die Dome                 54 mm   (F16c - sie ragen bis r 27)
    Dom-Durchmesser               ~ 6 mm   (F16d - Rundpfosten)
    Becher aussen                54,6 mm   -> 1,7 mm Luft, ausser an den Domen

Die Dome sitzen auf ALLEN VIER Achsen (12/3/6/9 Uhr - Nutzerbefund
21.08.), nicht nur auf der Schraubenachse. Die Wand ist deshalb an vier
Stellen gefenstert (je 10 breit: Dom 6 + 2 Luft je Seite).

KONZEPT v3 - VERSCHRAUBT STATT BAJONETT (21.08.). Das Bajonett ist
doppelt gestorben: Seine Zapfen an 3/9 Uhr standen auf der
weggefensterten Wand (zwei von drei schwebten als lose Koerper im STL -
Nutzerbefund 'die Raender haengen in der Luft'), und mit Domen auf allen
vier Achsen gibt es fuer Zapfen samt Ringschlitzen kein tragfaehiges
Band mehr (die Diagonalen blockiert die quadratische Ringoeffnung).
Stattdessen fassen die zwei Schrauben, die Bottom ohnehin von hinten in
die unteren Huelsen halten, jetzt DURCH den Becherboden (M2,5 x 14
statt x 6): Becher + Bottom + Mid sind die verschraubte Kartusche, der
Tragring liegt lose auf dem Becherrand und kommt mit den
Geraeteschrauben an die Dose.

Rueckwand: Fenster fuer den Micro-Fit-Feldstecker samt Rastnase - die
vorverdrahtete Leiste wird durch dieses Fenster gesteckt, BEVOR der
Becher in die Dose geht.
"""

import math
import os
import sys

from build123d import (
    BuildPart, BuildSketch, Plane, Rectangle, Circle, Locations,
    extrude, Mode, export_step, export_stl, Pos, Box, Rot,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "mechanical", "export")

PARAMS = dict(
    # --- Umgebung (F16 GEMESSEN am 21.08.2026) -----------------------------
    dose_licht        = 58.0,   # F16a/b: vorn und in 20 mm Tiefe gemessen
    dome_licht        = 54.0,   # F16c: Weite UEBER die Dome - sie ragen
                                # also je 2,0 nach innen (bis r 27)
    dose_tief         = 60.0,   # F16e: Rand bis Rueckwand innen
    dom_fenster_b     = 10.0,   # F16d: Dom OE6 + 2 Luft je Seite

    # --- Becher ------------------------------------------------------------
    board_d           = 52.0,   # Bottom und Mid
    spiel             = 0.4,    # radial, gesamt
    wand              = 1.1,
    boden_t           = 1.5,

    # --- Tiefen, z ab Rueckseite Bottom-Board ------------------------------
    # Der Feldstecker ragt 6,6 nach hinten; die Rueckwand liegt dahinter.
    tief_hinten       = 7.2,    # Innenraum hinter Bottom
    rand_vorn         = 15.4,   # Becherrand endet knapp unter dem Tragring
                                # (Platte ab 15,5)

    # --- Feldstecker-Fenster in der Rueckwand ------------------------------
    # Micro-Fit 43045-1612 bei (-10,5 / 15,6), Koerper 16,4 x 8,6; die
    # Rastnase der Kabelleiste braucht nach oben Luft.
    fenster_x         = -10.5,
    fenster_y         = 15.6,
    fenster_b         = 18.0,
    fenster_h         = 11.0,

    # --- Auflagebosse fuer das Bottom-Board --------------------------------
    boss_r            = 24.0,   # auf den Diagonalen, traegt die Boardkante
    boss_b            = 6.0,

    # --- Kartuschen-Verschraubung von hinten (Konzept v3, 21.08.) ----------
    # Kein Bajonett mehr (Begruendung im Kopf). Die zwei Schrauben der
    # unteren Huelsen (H1/H2-Achse) fassen durch den Boden; ein
    # Fuehrungsrohr ueberbrueckt den Hohlraum bis unter Bottom und
    # stuetzt das Board gleich mit.
    schraube_x        = 21.5,   # H1/H2-Achse, wie ueberall im Projekt
    kanal_bohr        = 2.8,    # Durchgang M2,5
    kanal_od          = 6.0,    # Fuehrungsrohr aussen
    kanal_luft        = 0.3,    # Rohr endet knapp unter Bottom (z = -0,3)
)


def _becher(p):
    r_in = (p["board_d"] + p["spiel"]) / 2.0          # 26,2
    r_out = r_in + p["wand"]                          # 27,3
    tief = p["tief_hinten"] + p["boden_t"]

    with BuildPart() as g:
        # Wand: Kreisring von der Rueckwand bis zum vorderen Rand
        with BuildSketch(Plane.XY.offset(-tief)):
            Circle(r_out)
            Circle(r_in, mode=Mode.SUBTRACT)
        extrude(amount=tief + p["rand_vorn"])

        # Rueckwand
        with BuildSketch(Plane.XY.offset(-tief)) as sk:
            Circle(r_out)
        extrude(amount=p["boden_t"])

        # Steckerfenster als TUNNEL bis zur Boardebene: Der Micro-Fit
        # steht so nah an der Boardkante, dass sein Eck (r 27,3) im
        # Wandring (ab 26,2) liegt - das Fenster muss also auch die Wand
        # an dieser Stelle oeffnen, nicht nur die Rueckwand.
        with BuildSketch(Plane.XY.offset(-tief - 0.5)):
            with Locations((p["fenster_x"], p["fenster_y"])):
                Rectangle(p["fenster_b"], p["fenster_h"])
        extrude(amount=tief + 0.5, mode=Mode.SUBTRACT)

        # Dom-Fenster an ALLEN VIER Achsen: Wand dort komplett heraus
        # (die Dose hat vier OE6-Dome bis r 27, F16c/d, Nutzerbefund)
        for vz in (1, -1):
            with BuildSketch(Plane.XY.offset(-tief)):
                with Locations((vz * (r_in + p["wand"] / 2.0), 0)):
                    Rectangle(2 * p["wand"] + 1.0, p["dom_fenster_b"])
                with Locations((0, vz * (r_in + p["wand"] / 2.0))):
                    Rectangle(p["dom_fenster_b"], 2 * p["wand"] + 1.0)
            extrude(amount=tief + p["rand_vorn"], mode=Mode.SUBTRACT)

        # Auflagebosse: das Bottom-Board liegt bei z = 0 auf ihnen.
        # NICHT auf den Diagonalen: Bei 225 Grad stand der Boss mitten im
        # Steckerfenster (und im Steckerkoerper). Jetzt paarweise neben
        # der x-Achse - dort ist Bottoms Rueckseite frei, und die
        # Schraubenkoepfe bei (+-21,5/0) behalten 0,9 mm Abstand.
        for wink in (15, 165, 195, 345):
            x = p["boss_r"] * math.cos(math.radians(wink))
            y = p["boss_r"] * math.sin(math.radians(wink))
            with BuildSketch(Plane.XY.offset(-p["tief_hinten"])):
                with Locations((x, y)):
                    Rectangle(p["boss_b"], p["boss_b"], rotation=wink)
            extrude(amount=p["tief_hinten"])

        # Schraubkanaele der Kartusche: Fuehrungsrohr vom Boden bis
        # knapp unter Bottom, Bohrung durch Boden und Rohr. Beruehrt das
        # Rohr einen Auflageboss, verschmelzen beide - unkritisch.
        for vz in (1, -1):
            with BuildSketch(Plane.XY.offset(-p["tief_hinten"])):
                with Locations((vz * p["schraube_x"], 0)):
                    Circle(p["kanal_od"] / 2.0)
            extrude(amount=p["tief_hinten"] - p["kanal_luft"])
        for vz in (1, -1):
            with BuildSketch(Plane.XY.offset(-tief - 0.5)):
                with Locations((vz * p["schraube_x"], 0)):
                    Circle(p["kanal_bohr"] / 2.0)
            extrude(amount=tief + 0.5, mode=Mode.SUBTRACT)
    return g.part


def check_gehaeuse(part, p):
    errs = []
    r_in = (p["board_d"] + p["spiel"]) / 2.0
    r_out = r_in + p["wand"]

    if 2 * r_out > p["dose_licht"] - 0.4:
        errs.append("Becher %.1f passt nicht in die Dose (%.1f, F16 messen)"
                    % (2 * r_out, p["dose_licht"]))
    if r_in * 2 < p["board_d"] + 0.2:
        errs.append("Innenraum %.1f klemmt die Boards (%.1f)"
                    % (2 * r_in, p["board_d"]))
    # Kartuschen-Schrauben: Kanal muss im Boden liegen und die
    # Schraubenachse (H1/H2) treffen
    if p["schraube_x"] + p["kanal_od"] / 2.0 > r_in:
        errs.append("Schraubkanal ragt aus dem Boden (%.1f > %.1f)"
                    % (p["schraube_x"] + p["kanal_od"] / 2.0, r_in))
    if p["schraube_x"] != 21.5:
        errs.append("Schraubkanal nicht auf der H1/H2-Achse (21,5)")
    # Steckerfenster ganz in der Rueckwand
    if abs(p["fenster_x"]) + p["fenster_b"] / 2.0 > r_in:
        errs.append("Steckerfenster ragt aus der Rueckwand")

    # Materialproben
    tief = p["tief_hinten"] + p["boden_t"]
    def solid(probe, was):
        if (part & probe).volume < 1e-6:
            errs.append("kein Material: %s" % was)
    def clear(probe, was):
        if (part & probe).volume > 1e-6:
            errs.append("nicht frei: %s" % was)
    # LEKTION aus dem Bajonett-Defekt (zwei Zapfen schwebten auf der
    # weggefensterten Wand): Fenster an allen vier Achsen FREI pruefen,
    # Wand ZWISCHEN den Fenstern (45 Grad) vorhanden pruefen.
    rw = r_in + p["wand"] / 2.0
    for wink in (0, 90, 180, 270):
        wr = math.radians(wink)
        clear(Pos(rw * math.cos(wr), rw * math.sin(wr), 0)
              * Box(0.8, 0.8, 0.5), "Dom-Fenster bei %d Grad" % wink)
    for wink in (45, 135, 225, 315):
        wr = math.radians(wink)
        solid(Pos(rw * math.cos(wr), rw * math.sin(wr), 0)
              * Box(0.5, 0.5, 0.5), "Wand bei %d Grad" % wink)
    solid(Pos(p["schraube_x"] + p["kanal_od"] / 2.0 - 0.6, 0,
              -p["tief_hinten"] / 2.0) * Box(0.4, 0.4, 0.5),
          "Schraubkanal-Rohr rechts")
    clear(Pos(p["schraube_x"], 0, -tief + p["boden_t"] / 2.0)
          * Box(1.6, 1.6, p["boden_t"] + 0.6), "Schraubbohrung rechts")
    clear(Pos(p["fenster_x"], p["fenster_y"], -tief + p["boden_t"] / 2.0)
          * Box(p["fenster_b"] - 1, p["fenster_h"] - 1, p["boden_t"] + 1),
          "Steckerfenster")
    solid(Pos(p["boss_r"] * math.cos(math.radians(15)),
              p["boss_r"] * math.sin(math.radians(15)),
              -p["tief_hinten"] / 2.0) * Box(0.5, 0.5, 0.5), "Boss 15 Grad")
    return errs


def main():
    p = PARAMS
    part = _becher(p)
    errs = check_gehaeuse(part, p)
    os.makedirs(OUT, exist_ok=True)
    export_step(part, os.path.join(OUT, "gehaeuse.step"))
    export_stl(part, os.path.join(OUT, "gehaeuse.stl"))
    r_out = (p["board_d"] + p["spiel"]) / 2.0 + p["wand"]
    print("Selbsttest   : %s" % ("BESTANDEN" if not errs else "FEHLGESCHLAGEN"))
    for e in errs:
        print("   ! %s" % e)
    print("Becher       : Ø %.1f aussen, Rueckwand bei z = %.1f"
          % (2 * r_out, -(p["tief_hinten"] + p["boden_t"])))
    print("Fenster      : Feldstecker %.0f x %.0f; Dom-Fenster 4 x %.0f"
          % (p["fenster_b"], p["fenster_h"], p["dom_fenster_b"]))
    print("Kartusche    : 2 x M2,5 x 14 von hinten durch den Boden "
          "(Kanal OE%.0f auf x = +-%.1f)"
          % (p["kanal_od"], p["schraube_x"]))
    print("Export       : %s" % OUT)
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
