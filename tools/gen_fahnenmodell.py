#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Erzeugt die 1:1-Papierschablone fuer die Displayfahnen-Pruefung.

Seit dem Direktloet-Entscheid (20.08. spaetabends) ist das Modell kein
Bestell-Tor mehr, sondern die KONTROLLE am ersten Muster: Fahne falten,
auf den Pad-Streifen legen, pruefen, dass die Goldfinger nach unten auf
die Pads zeigen und Pin 1 rechts ankommt.

Masse aus der Originalzeichnung (Fahne 12,96 +-0,3 lang, 11,4 bzw. 9,34
breit, Finger 0,35/2,0 im 0,7-Raster) und gen_layouts.py. SEITENFALTUNG
seit dem 20.08. nachts: Die Fahne verlaesst das quer eingebaute Panel an
der RECHTEN Kante (x = 17,77), das Loetfeld steht 90 Grad gedreht um
x = 6,05, Raster in y, Pin 1 OBEN (y = -3,55). Beim Drucken:
100 %, keine Seitenanpassung - das 50-mm-Lineal auf dem Blatt nachmessen.
"""

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIEL = os.path.join(ROOT, "docs", "fahnenmodell.svg")

S = 3.7795275591  # px je mm bei 96 dpi - SVG in mm-Einheiten


def mm(v):
    return v * S


def main():
    e = []
    a = e.append
    B, H = 190, 130
    a('<svg xmlns="http://www.w3.org/2000/svg" width="%dmm" height="%dmm" '
      'viewBox="0 0 %f %f" font-family="Helvetica, Arial, sans-serif">'
      % (B, H, mm(B), mm(H)))
    a('<rect width="100%" height="100%" fill="white"/>')

    def text(x, y, s, gr=3.2, fett=False, farbe="#000"):
        a('<text x="%f" y="%f" font-size="%f" fill="%s"%s>%s</text>'
          % (mm(x), mm(y), mm(gr), farbe,
             ' font-weight="bold"' if fett else '', s))

    def linie(x0, y0, x1, y1, w=0.25, dash=None, farbe="#000"):
        a('<line x1="%f" y1="%f" x2="%f" y2="%f" stroke="%s" '
          'stroke-width="%f"%s/>'
          % (mm(x0), mm(y0), mm(x1), mm(y1), farbe, mm(w),
             ' stroke-dasharray="%f %f"' % (mm(dash), mm(dash)) if dash else ''))

    def kasten(x, y, b, h, w=0.35, fuell="none"):
        a('<rect x="%f" y="%f" width="%f" height="%f" fill="%s" '
          'stroke="#000" stroke-width="%f"/>'
          % (mm(x), mm(y), mm(b), mm(h), fuell, mm(w)))

    # --- Kopf und Lineal ---------------------------------------------------
    text(10, 10, "Fahnenmodell ER-TFT1.69-3 — 1:1 drucken (100 %, keine Anpassung)", 4.2, True)
    text(10, 16, "Kontrolle: dieses Lineal muss exakt 50 mm messen", 3)
    linie(10, 20, 60, 20, 0.5)
    for i in range(0, 51, 10):
        linie(10 + i, 18.5, 10 + i, 21.5, 0.35)
        text(9 + i, 25, str(i), 2.6)

    # --- Teil 1: die Fahne (1:1) ------------------------------------------
    ox, oy = 10, 38
    text(ox, oy - 3, "TEIL 1 — die Fahne (ausschneiden)", 3.4, True)
    # Trapez nach Originalzeichnung: 11,4 am Abgang, 9,34 an der Spitze,
    # 12,96 lang (nach unten)
    x0, x1 = ox, ox + 11.4
    xs0, xs1 = ox + (11.4 - 9.34) / 2, ox + (11.4 + 9.34) / 2
    yA, yS = oy, oy + 12.96
    a('<polygon points="%f,%f %f,%f %f,%f %f,%f" fill="none" '
      'stroke="#000" stroke-width="%f"/>'
      % (mm(x0), mm(yA), mm(x1), mm(yA), mm(xs1), mm(yS), mm(xs0), mm(yS),
         mm(0.4)))
    # Kontaktzone an der Spitze (3 mm), schraffiert
    a('<rect x="%f" y="%f" width="%f" height="%f" fill="#ffd" '
      'stroke="#b90" stroke-width="%f"/>'
      % (mm(xs0), mm(yS - 2), mm(9.34), mm(2), mm(0.3)))
    text(x1 + 3, yS - 4.5, "Kontaktzone: am ECHTEN Panel nachsehen,", 2.8)
    text(x1 + 3, yS - 0.7, "auf welcher Seite die Goldfinger liegen —", 2.8)
    text(x1 + 3, yS + 3.1, "diese Seite der Schablone ankreuzen und beschriften", 2.8)
    # Pin-1-Kante
    text(x0 - 1, yS + 7, "Pin-1-Kante am echten Panel ablesen:", 2.8)
    text(x0 - 1, yS + 11, "[ ] links   [ ] rechts   (auf der Schablone markieren)", 2.8)
    # Faltlinie am Abgang
    linie(x0 - 4, yA, x1 + 4, yA, 0.25, dash=1.2)
    text(x1 + 5, yA + 1, "Faltlinie = RECHTE Panelkante, quer eingebaut (Werksfaltung 180°)", 2.8)

    # --- Teil 2: der Boardstreifen ----------------------------------------
    ox2, oy2 = 100, 38
    text(ox2, oy2 - 3, "TEIL 2 — Boardstreifen mit Loetpads (ausschneiden)", 3.4, True)
    # Fenster in Boardkoordinaten (y nach unten wie in KiCad): x 0..22,
    # y -8..+8. Rechte Panelkante x = 17,77, Loetfeld um (6,05 / 0,3).
    bx0, by0, sb, sh = 0.0, -8.0, 22.0, 16.0

    def BX(x):
        return ox2 + (x - bx0)

    def BY(y):
        return oy2 + (y - by0)

    kasten(ox2, oy2, sb, sh)
    # Padspalte: 12 Pads 3,2 breit / 0,4 hoch im 0,7-Raster, Pin 1 OBEN
    for i in range(12):
        py = 0.3 - 3.85 + i * 0.7
        a('<rect x="%f" y="%f" width="%f" height="%f" fill="#b90"/>'
          % (mm(BX(4.45)), mm(BY(py - 0.2)), mm(3.2), mm(0.4)))
    text(ox2 + sb + 2, oy2 + 3.0, "12 Loetpads 0,7-Raster in y — Pin 1 OBEN (y = −3,55)", 2.8)
    linie(BX(17.77), oy2 - 2, BX(17.77), oy2 + sh + 2, 0.25, dash=1.2)
    text(ox2 + sb + 2, oy2 + 7.5, "gestrichelt: RECHTE Panelkante (x = 17,77) —", 2.8)
    text(ox2 + sb + 2, oy2 + 11.5, "Fahne hier anlegen und nach links falten", 2.8)


    # --- Ablauf ------------------------------------------------------------
    oy3 = 78
    text(10, oy3, "ABLAUF", 3.4, True)
    for i, z in enumerate([
        "1. Teil 1 an die echte Fahne halten: Goldfinger-Seite und Pin-1-Kante uebertragen.",
        "2. An der Faltlinie um 180° falten (wie ab Werk).",
        "3. Teil 1 auf Teil 2 legen: Faltlinie auf die RECHTE Panelkante, Fahne zeigt nach links.",
        "4. KONTROLLE 1: Die Goldfinger muessen NACH UNTEN auf die Pads zeigen (face-down).",
        "5. KONTROLLE 2: Pin 1 der Fahne muss auf dem OBERSTEN Pad ankommen (y = -3,55).",
        "6. KONTROLLE 3: Die Kontaktzone (2,0 lang) muss die Pads (x 4,45..7,65) ueberdecken -",
        "   Fahnenlaenge 12,96 +-0,3 ab Panelkante.",
    ]):
        text(10, oy3 + 5 + i * 4.5, z, 2.9)
    text(10, oy3 + 42, "Rechnung sagt: alles passt - dieses Blatt ist die Bestaetigung am ersten Muster.", 2.9, True)

    a('</svg>')
    open(ZIEL, "w", encoding="utf-8").write("\n".join(e))
    print("geschrieben:", ZIEL)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
