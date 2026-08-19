#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Erzeugt alle Bilder und 3D-Ausgaben des Projekts aus den Boarddateien.

Bis zum 18.08.2026 wurden Renderings, STEP-Ausgaben und die Stapelansicht
von Hand angestossen. Das ging so lange gut, bis die selbst erzeugten
Steckverbinder-Huellkoerper dazukamen: Die Stapel-STEPs stammten danach aus
einem Lauf VOR den Modellen, die Unterseiten-Renderings sogar aus einem noch
frueheren. Auf genau den Bildern, auf denen die Stecker sitzen, fehlten sie
deshalb. Seitdem laeuft die ganze Kette hier durch, in einem Rutsch:

    Board -> STEP (mit Modellen)  ->  Stapel-STEP
          -> Rendering Ober-/Unterseite
          -> drei transparente Schraegansichten -> uebereinandergelegt

Die Stapelansicht ist eine Explosionsdarstellung ohne eigenes Rendersystem:
drei Einzelbilder mit transparentem Hintergrund, um STAPEL_VERSATZ Pixel
gegeneinander versetzt.
"""

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
RENDERS = os.path.join(ROOT, "docs", "renders")
STACKDIR = os.path.join(ROOT, "mechanical", "export", "stack")

# Reihenfolge von unten nach oben - so wird auch gestapelt.
BOARDS = ["bottom_power_motor", "mid_logic", "top_ui"]

BREITE, HOEHE = 1600, 1200
SCHRAEG = "-32,0,-22"      # Blickwinkel der Stapelansicht
STAPEL_ZOOM = 0.62         # kleiner als 1, damit die Schraeglage Platz hat
STAPEL_VERSATZ = 0.46      # Anteil der Bildhoehe, Versatz je Board

# Reale Boardbreite in mm - Grundlage der Massstabskorrektur im Stapelbild.
BOARD_MM = {
    "bottom_power_motor": 52.0,
    "mid_logic": 52.0,
    "top_ui": 47.0,
}


def pcb(name):
    return os.path.join(ROOT, "hardware", name, name + ".kicad_pcb")


def lauf(args):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(" ".join(args) + "\n" + r.stderr[-800:] + "\n")
    return r.returncode == 0


def rendern(name, ziel, side="top", rotate=None, hintergrund="transparent",
            zoom=None):
    # Transparent auch fuer die Einzelansichten: Die HTML-Doku bettet sie
    # ein, und auf transparentem Grund sitzen sie dort im hellen wie im
    # dunklen Theme richtig - eine weisse Kachel taete das nicht.
    args = [CLI, "pcb", "render", "-o", ziel,
            "--side", side, "--background", hintergrund,
            "--quality", "high",
            "--width", str(BREITE), "--height", str(HOEHE)]
    if rotate:
        args += ["--rotate", rotate]
    if zoom:
        args += ["--zoom", str(zoom)]
    args.append(pcb(name))
    return lauf(args)


def step_export(name):
    ziel = os.path.join(STACKDIR, name + ".step")
    return lauf([CLI, "pcb", "export", "step", "--force",
                 "--subst-models", "-o", ziel, pcb(name)])


def stapelbild():
    """Explosionsdarstellung aus drei Schraegansichten.

    Zwei Fallstricke, beide am 18.08.2026 in einem missratenen Bild
    besichtigt:

    1. KiCad zoomt JEDES Board auf seinen eigenen Bildrahmen. Ein 47er
       Quadrat kommt damit genauso gross heraus wie eine 52er Scheibe -
       uebereinandergelegt stimmen die Groessenverhaeltnisse dann nicht.
       Deshalb wird hier nachskaliert: Aus der Alphamaske jedes Bildes
       kommt seine tatsaechliche Breite in Pixeln, aus BOARD_MM seine
       Breite in Millimetern. Das Verhaeltnis ist der Massstab, und alle
       drei werden auf den kleinsten gemeinsamen gebracht.
    2. Ein zu kleiner Versatz laesst die Boards zu 80 % ueberlappen. Der
       Versatz richtet sich deshalb nach der Bildhoehe, nicht nach einer
       festen Pixelzahl.
    """
    from PIL import Image

    lagen = []
    for name in BOARDS:
        tmp = os.path.join(RENDERS, "_tmp_" + name + ".png")
        if not rendern(name, tmp, side="top", rotate=SCHRAEG,
                       hintergrund="transparent", zoom=STAPEL_ZOOM):
            return False
        lagen.append(tmp)

    zugeschnitten = []
    for pfad, name in zip(lagen, BOARDS):
        im = Image.open(pfad).convert("RGBA")
        kasten = im.getbbox()          # aus der Alphamaske
        im = im.crop(kasten)
        px_je_mm = im.width / float(BOARD_MM[name])
        zugeschnitten.append((im, px_je_mm))

    ziel = min(p for _, p in zugeschnitten)
    skaliert = []
    for im, p in zugeschnitten:
        if abs(p - ziel) > 1e-6:
            f = ziel / p
            im = im.resize((max(1, round(im.width * f)),
                            max(1, round(im.height * f))), Image.LANCZOS)
        skaliert.append(im)

    breite = max(im.width for im in skaliert)
    hoehe = max(im.height for im in skaliert)
    versatz = round(hoehe * STAPEL_VERSATZ)
    rand = round(breite * 0.04)
    gesamt = Image.new(
        "RGBA",
        (breite + 2 * rand, hoehe + versatz * (len(skaliert) - 1) + 2 * rand),
        (0, 0, 0, 0))

    # Von unten nach oben: Das erste Board der Liste sitzt am tiefsten
    # Punkt des Bildes, das letzte ganz oben. Gezeichnet wird von oben
    # nach unten, damit das jeweils tiefere Board verdeckt wird.
    for i in reversed(range(len(skaliert))):
        im = skaliert[i]
        y = (len(skaliert) - 1 - i) * versatz + rand
        x = rand + (breite - im.width) // 2
        gesamt.alpha_composite(im, (x, y))

    gesamt.save(os.path.join(RENDERS, "stack.png"))

    for p in lagen:
        os.remove(p)
    return True


def main():
    os.makedirs(RENDERS, exist_ok=True)
    os.makedirs(STACKDIR, exist_ok=True)
    fehler = 0

    for name in BOARDS:
        for seite in ("top", "bottom"):
            ziel = os.path.join(RENDERS, "%s_%s.png" % (name, seite))
            ok = rendern(name, ziel, side=seite)
            print("%-20s %-7s %s" % (name, seite, "ok" if ok else "FEHLER"))
            fehler += 0 if ok else 1
        ok = step_export(name)
        print("%-20s %-7s %s" % (name, "step", "ok" if ok else "FEHLER"))
        fehler += 0 if ok else 1

    print("%-20s %-7s %s" % ("stapelbild", "", "ok" if stapelbild() else "FEHLER"))

    # Die Schnittzeichnung der Front. Sie braucht weder KiCad noch einen
    # Geometriekern - sie liest die Masse aus den Quellen und zeichnet sie.
    # Deshalb laeuft sie hier immer mit, auch wenn kein Board neu erzeugt
    # wurde: Aendert sich ein Parameter in adapter.py, ist das Bild sonst
    # still veraltet.
    r = subprocess.run([sys.executable,
                        os.path.join(ROOT, "tools", "gen_explosion.py")],
                       capture_output=True, text=True)
    print("%-20s %-7s %s" % ("frontschnitt", "",
                             "ok" if r.returncode == 0 else "FEHLER"))
    for zeile in (r.stdout or r.stderr[-400:]).splitlines():
        if zeile.strip().startswith("!"):
            print("   %s" % zeile.strip())

    # Gesamtbaugruppe erst danach - sie liest die eben geschriebenen STEPs.
    r = subprocess.run([sys.executable,
                        os.path.join(ROOT, "mechanical", "stack.py")],
                       capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr[-400:])
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
