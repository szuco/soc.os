#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Das Gehaeuse um Bottom und Mid - ein Becher, der in den Tragring rastet.

Gewuenscht am 20.08.2026: Bottom und Mid sollen in der Dose verschwinden,
fixiert, nur der Feldstecker bleibt von hinten zugaenglich. Gedruckt wird
der Becher ZUSAMMEN mit dem Tragring; verbunden werden beide durch vier
Rasthaken, die in Schlitze der Tragring-Platte greifen. Damit wird aus
Becher + Boards + Tragring eine Einheit, die als Ganzes in die Dose geht
und dort verschraubt wird.

DIE ENGE STELLE - und warum der Becher zwei Fenster hat:

    Dose, lichte Weite            ~55 mm   (mit Schraubdomen nur ~54)
    Boards                          52 mm
    bleibt je Seite                1,5 mm  (an den Domen 1,0)

Eine umlaufende Wand braucht aussen 52,4 + 2 x 1,1 = 54,6 - das passt an
den Schraubdomen NICHT vorbei. Deshalb ist die Wand an der 3- und der
9-Uhr-Seite unterbrochen (dort sitzen die Dome, auf der Achse der
Geraeteschrauben). Durch diese zwei Fenster schaut die Platinenkante -
der Preis dafuer, dass der Rest verschwindet.

MASSVORBEHALT F16: Die lichte Weite DEINER Dose und die Lage ihrer
Schraubdome sind Annahmen (dose_licht, dom_fenster). Vor dem Druck messen.

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
    dom_fenster_b     = 16.0,   # Fensterbreite (Sehne) - F16d (Dombreite)
                                # steht noch aus, bis dahin die Annahme

    # BEKANNTER DEFEKT, bestaetigt am 21.08. (Einwand des Nutzers: die
    # Raender haengen in der Luft): Die Zapfen an 3 und 9 Uhr stehen auf
    # der Oberkante einer Wand, die dort vom Dom-Fenster KOMPLETT
    # entfernt ist - zwei von drei Zapfen schweben als lose Koerper im
    # STL. Reparatur geplant: Zapfen neben die Fenster ruecken (dort
    # traegt wieder Wand), moeglich gemacht durch die gemessene Dose
    # (r 29 statt 27,5). Der genaue Winkel braucht F16d.

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

    # --- Bajonett in den Tragring ------------------------------------------
    # KEINE radialen Rasthaken - die scheiterten dreifach: Auf den
    # Diagonalen sitzt der Adapter (die 50,6er Oeffnung ist QUADRATISCH,
    # ihre Ecken reichen bis r 35,8), radial nach aussen steht die
    # Dosenwand (r 27,5), radial nach innen der Adapter-Basisring (24,9).
    # Frei ist nur ein 2,2-mm-Band auf den ACHSEN: r 25,3 bis 27,5.
    #
    # Deshalb Bajonett: Drei Zapfen an 12, 3 und 9 Uhr fahren durch
    # Bogenschlitze der Platte, dann wird der Becher ~7 Grad gedreht und
    # die TANGENTIAL auskragenden Koepfe legen sich auf die
    # Plattenvorderseite. Tangential heisst: kein Millimeter radialer
    # Ueberstand - Dose und Adapter bleiben unberuehrt. 6 Uhr faellt aus,
    # dort laeuft das Magnetkabel durch die Platte.
    zapfen_r          = 26.1,   # Bandmitte; aussen 26,8 < Dose 27,5
    zapfen_b          = 3.0,    # tangential
    zapfen_t          = 1.4,    # radial
    kopf_l            = 2.6,    # tangentiale Auskragung des Kopfes
    dreh_grad         = 7.0,    # Verriegelungsdrehung
    schlitz_luft      = 0.3,
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

        # Dom-Fenster an 3 und 9 Uhr: Wand dort komplett heraus
        for vz in (1, -1):
            with BuildSketch(Plane.XY.offset(-tief)):
                with Locations((vz * (r_in + p["wand"] / 2.0), 0)):
                    Rectangle(2 * p["wand"] + 1.0, p["dom_fenster_b"])
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

        # Bajonettzapfen an 12, 3 und 9 Uhr (siehe Parameterblock)
        for wink in (90, 0, 180):
            wr = math.radians(wink)
            cx, cy = p["zapfen_r"] * math.cos(wr), -p["zapfen_r"] * math.sin(wr)
            # Zapfen: vom Becherrand durch die Plattenebene (15,5..17,5)
            with BuildSketch(Plane.XY.offset(p["rand_vorn"])):
                with Locations((cx, cy)):
                    Rectangle(p["zapfen_t"], p["zapfen_b"], rotation=-wink)
            extrude(amount=(17.5 - p["rand_vorn"]) + 1.3)
            # Kopf: kragt TANGENTIAL aus, liegt nach der Drehung auf der
            # Plattenvorderseite (z 17,5)
            tx, ty = -math.sin(wr), -math.cos(wr)
            klen = p["zapfen_b"] + p["kopf_l"]
            off = p["kopf_l"] / 2.0
            with BuildSketch(Plane.XY.offset(17.5 + 0.1)):
                with Locations((cx + off * tx, cy + off * ty)):
                    Rectangle(p["zapfen_t"], klen, rotation=-wink)
            extrude(amount=1.2)
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
    # Bajonett: Zapfenband muss zwischen Oeffnung, Adapter und Dose passen
    from tragring import PARAMS as TP
    innen = p["zapfen_r"] - p["zapfen_t"] / 2.0
    aussen = p["zapfen_r"] + p["zapfen_t"] / 2.0
    if innen < TP["open_sq"] / 2.0 + 0.1:
        errs.append("Zapfen innen %.2f beruehrt die Oeffnungskante (25,3)"
                    % innen)
    if aussen > p["dose_licht"] / 2.0 - 0.6:
        errs.append("Zapfen aussen %.2f zu nah an der Dosenwand (%.1f)"
                    % (aussen, p["dose_licht"] / 2.0))
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
    solid(Pos(0, -r_in - p["wand"] / 2.0, 0) * Box(0.5, 0.5, 0.5),
          "Wand bei 6 Uhr")
    clear(Pos(r_in + p["wand"] / 2.0, 0, 0) * Box(0.8, 4.0, 0.5),
          "Dom-Fenster bei 3 Uhr")
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
    print("Fenster      : Feldstecker %.0f x %.0f; Dom-Fenster 2 x %.0f"
          % (p["fenster_b"], p["fenster_h"], p["dom_fenster_b"]))
    print("Bajonett     : 3 Zapfen (12/3/9 Uhr) auf r %.1f, Drehung %.0f Grad"
          % (p["zapfen_r"], p["dreh_grad"]))
    print("Export       : %s" % OUT)
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
