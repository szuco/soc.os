#!/usr/bin/env python3
"""
Vorschau des Displayinhalts, ohne Hardware und ohne Flash.

    python3 tools/display_mock.py [--zustand normal|alarm|fahrt] [--menue]

Erzeugt PNG-Dateien in der Groesse des realen Panels (280 x 240, ST7789 quer
hinter dem Fenster der Zentralscheibe) und zeichnet denselben Inhalt wie das
Lambda in firmware/esphome/switchstack.yaml.

  DAS IST KEIN EMULATOR. Es fuehrt die Firmware nicht aus - es zeichnet nach,
  was das Lambda zeichnet. Der Nutzen ist die Bildaufteilung: Passt der Text in
  die Zeilen, kollidiert nichts, ist die grosse Zahl gross genug? Genau das
  laesst sich sonst erst am fertigen Geraet beurteilen, und dafuer ist der Weg
  ueber Compilieren, Flashen und Blende-Abnehmen zu lang.

  Wer die Aufteilung aendert, aendert BEIDES: hier und im Lambda. Das ist der
  Preis dafuer, dass man sie vorher sieht.
"""

import argparse
import os
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("Pillow fehlt:  pip install Pillow")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "mechanical", "export")

# Reales Panel: 240 x 280 hochkant, quer eingebaut -> 280 x 240.
W, H = 280, 240

# Das Fenster der Zentralscheibe ist 32,70 x 27,00 mm, die aktive Flaeche
# 32,63 x 27,97 - in der Hoehe verdeckt die Scheibe also je Seite rund einen
# halben Millimeter. Bei 240 Pixeln auf 27,97 mm sind das gut 4 Pixel.
CROP_PX = 4

FONT_DIRS = ["/System/Library/Fonts/Supplemental", "/System/Library/Fonts",
             "/usr/share/fonts/truetype/dejavu", "/usr/share/fonts"]
FONT_CANDIDATES = ["Arial.ttf", "Helvetica.ttc", "DejaVuSans.ttf", "Verdana.ttf"]


def _font(size):
    for d in FONT_DIRS:
        for name in FONT_CANDIDATES:
            p = os.path.join(d, name)
            if os.path.exists(p):
                try:
                    return ImageFont.truetype(p, size)
                except OSError:
                    continue
    return ImageFont.load_default()


# Groessen wie im Lambda: font_big 34, font_mid 18, font_small 13
F_BIG, F_MID, F_SMALL = _font(34), _font(18), _font(13)

WEISS = (255, 255, 255)
GRAU = (150, 150, 150)
ROT = (255, 90, 90)


def _text(d, x, y, s, font, anchor="la", fill=WEISS):
    d.text((x, y), s, font=font, anchor=anchor, fill=fill)


def startbildschirm(z):
    """Zeichnet denselben Inhalt wie das display-Lambda."""
    img = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img)

    _text(d, 140, 8, "%.1f°C" % z["temp"], F_BIG, "ma")
    _text(d, 140, 50, "%.0f %% rF" % z["hum"], F_MID, "ma")
    d.line((20, 82, 260, 82), fill=GRAU)

    for i, (nr, offen, sab) in enumerate(
            ((1, z["fenster1"], z["sab1"]), (2, z["fenster2"], z["sab2"]))):
        y = 92 + i * 20
        _text(d, 20, y, "Fenster %d: %s" % (nr, "offen" if offen else "zu"), F_SMALL)
        if sab:
            _text(d, 150, y, "SABOTAGE", F_SMALL, "la", ROT)

    zeile = 138
    for nr, strom in ((1, z["i1"]), (2, z["i2"])):
        if strom > 0.05:
            _text(d, 20, zeile, "Motor %d: %.2f A" % (nr, strom), F_SMALL)
            zeile += 20

    if z["praesenz"]:
        _text(d, 20, 216, "anwesend", F_SMALL, "ls")
    if z["stern"]:
        _text(d, 260, 216, "Stern an", F_SMALL, "rs")
    return img


MENUE = ["Jalousie 1", "Jalousie 2", "Sanftauslauf", "Weihnachtsstern",
         "Dunstabzugshaube", "Messwerte", "Alles stoppen", "Zurueck"]


def menue(auswahl=2):
    """Naeherung an graphical_display_menu: Titel, Liste, Markierung."""
    img = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img)
    zeile_h = 26
    sichtbar = (H - 40) // zeile_h
    erste = max(0, min(auswahl - sichtbar // 2, len(MENUE) - sichtbar))
    for i in range(sichtbar):
        idx = erste + i
        if idx >= len(MENUE):
            break
        y = 20 + i * zeile_h
        if idx == auswahl:
            d.rectangle((10, y - 3, W - 10, y + zeile_h - 6), fill=(40, 40, 40))
            _text(d, 20, y, ">", F_MID)
        _text(d, 40, y, MENUE[idx], F_MID)
    return img


def rahmen(img):
    """Zeigt, was die Zentralscheibe oben und unten verdeckt."""
    d = ImageDraw.Draw(img)
    for y in (CROP_PX, H - CROP_PX):
        d.line((0, y, W, y), fill=(90, 0, 0))
    return img


ZUSTAENDE = {
    "normal": dict(temp=21.4, hum=47, fenster1=False, fenster2=False,
                   sab1=False, sab2=False, i1=0.0, i2=0.0,
                   praesenz=False, stern=False),
    "fahrt":  dict(temp=21.4, hum=47, fenster1=False, fenster2=True,
                   sab1=False, sab2=False, i1=1.24, i2=0.98,
                   praesenz=True, stern=True),
    "alarm":  dict(temp=-3.5, hum=88, fenster1=True, fenster2=True,
                   sab1=True, sab2=False, i1=0.0, i2=0.0,
                   praesenz=True, stern=False),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zustand", default="alle",
                    choices=list(ZUSTAENDE) + ["alle"])
    ap.add_argument("--skalierung", type=int, default=2,
                    help="Vergroesserung der PNG-Ausgabe")
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    namen = list(ZUSTAENDE) if args.zustand == "alle" else [args.zustand]
    bilder = [("display_%s.png" % n, rahmen(startbildschirm(ZUSTAENDE[n])))
              for n in namen]
    bilder.append(("display_menue.png", rahmen(menue())))

    for name, img in bilder:
        if args.skalierung > 1:
            img = img.resize((W * args.skalierung, H * args.skalierung),
                             Image.NEAREST)
        img.save(os.path.join(OUT, name))
        print("%-22s %d x %d" % (name, img.width, img.height))
    print("Panel        : %d x %d, Verdeckung je %d Pixel oben und unten"
          % (W, H, CROP_PX))
    print("Ausgabe      : %s" % os.path.relpath(OUT, ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
