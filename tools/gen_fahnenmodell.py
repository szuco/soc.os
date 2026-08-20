#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Erzeugt die 1:1-Papierschablone fuer die Displayfahnen-Pruefung.

docs/17 verlangt vor der Bestellung ein Papiermodell: Kontaktseite und
Pinreihenfolge der Fahne nach Werksfaltung und Schlitzdurchgang. Diese
Schablone macht daraus eine Viertelstunde: ausschneiden, an der echten
Fahne die Kontaktseite und die Pin-1-Kante uebertragen, falten, durch den
Schlitzstreifen stecken, ablesen.

Masse aus docs/datasheets/ER-TFT1.69-3.md (Fahne 18,15 lang, 8,47 und
6,50 breit) und gen_layouts.py (Schlitz 10,0 x 1,6 bei y = 6,4;
Panelunterkante y = 15,3; J5-Kontakte bei y = 1,93). Beim Drucken:
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
    # Trapez: 8,47 breit am Abgang, 6,50 an der Spitze, 18,15 lang (nach unten)
    x0, x1 = ox, ox + 8.47
    xs0, xs1 = ox + (8.47 - 6.5) / 2, ox + (8.47 + 6.5) / 2
    yA, yS = oy, oy + 18.15
    a('<polygon points="%f,%f %f,%f %f,%f %f,%f" fill="none" '
      'stroke="#000" stroke-width="%f"/>'
      % (mm(x0), mm(yA), mm(x1), mm(yA), mm(xs1), mm(yS), mm(xs0), mm(yS),
         mm(0.4)))
    # Kontaktzone an der Spitze (3 mm), schraffiert
    a('<rect x="%f" y="%f" width="%f" height="%f" fill="#ffd" '
      'stroke="#b90" stroke-width="%f"/>'
      % (mm(xs0), mm(yS - 3), mm(6.5), mm(3), mm(0.3)))
    text(x1 + 3, yS - 4.5, "Kontaktzone: am ECHTEN Panel nachsehen,", 2.8)
    text(x1 + 3, yS - 0.7, "auf welcher Seite die Goldfinger liegen —", 2.8)
    text(x1 + 3, yS + 3.1, "diese Seite der Schablone ankreuzen und beschriften", 2.8)
    # Pin-1-Kante
    text(x0 - 1, yS + 7, "Pin-1-Kante am echten Panel ablesen:", 2.8)
    text(x0 - 1, yS + 11, "[ ] links   [ ] rechts   (auf der Schablone markieren)", 2.8)
    # Faltlinie am Abgang
    linie(x0 - 4, yA, x1 + 4, yA, 0.25, dash=1.2)
    text(x1 + 5, yA + 1, "Faltlinie = Panelunterkante (Werksfaltung 180°)", 2.8)

    # --- Teil 2: der Boardstreifen ----------------------------------------
    ox2, oy2 = 100, 38
    text(ox2, oy2 - 3, "TEIL 2 — Boardstreifen mit Schlitz (ausschneiden, Schlitz aufschneiden)", 3.4, True)
    # Streifen: von Panelunterkante (y=15,3) bis ueber J5 (y=1,93): Laenge 15,3-0 = 15,3+Rand
    # Masse in Board-y: Panelkante 15,3 / Schlitz 5,6..7,2 / J5-Kontakte 1,93
    sb, sh = 30, 20  # Streifen 30 breit, 20 hoch (y 0..20 des Boards)
    kasten(ox2, oy2, sb, sh)
    # Schlitz bei Board-y 5,6..7,2 -> im Streifen von oben (y=20 oben? Wir
    # zeichnen Board-y nach unten wachsend wie KiCad: Streifen-oben = y=0)
    a('<rect x="%f" y="%f" width="%f" height="%f" fill="#000"/>'
      % (mm(ox2 + (sb - 10) / 2), mm(oy2 + 5.6), mm(10), mm(1.6)))
    text(ox2 + sb + 2, oy2 + 7, "Schlitz 10,0 × 1,6 (aufschneiden)", 2.8)
    linie(ox2, oy2 + 15.3, ox2 + sb, oy2 + 15.3, 0.25, dash=1.2)
    text(ox2 + sb + 2, oy2 + 16, "Panelunterkante — Fahne hier anlegen und falten", 2.8)
    linie(ox2, oy2 + 1.93, ox2 + sb, oy2 + 1.93, 0.3, farbe="#b00")
    text(ox2 + sb + 2, oy2 + 2.6, "J5-Kontaktlinie (rot): bis hier muss die", 2.8, farbe="#b00")
    text(ox2 + sb + 2, oy2 + 6.0, "Kontaktzone reichen (Einschub ~2,5)", 2.8, farbe="#b00")

    # --- Ablauf ------------------------------------------------------------
    oy3 = 78
    text(10, oy3, "ABLAUF", 3.4, True)
    for i, z in enumerate([
        "1. Teil 1 an die echte Fahne halten: Goldfinger-Seite und Pin-1-Kante auf die Schablone uebertragen.",
        "2. An der Faltlinie um 180° falten (wie ab Werk: Fahne liegt an der Panelrueckseite an).",
        "3. Teil 1 auf Teil 2 legen (Faltlinie auf Panelunterkante), Spitze durch den Schlitz stecken,",
        "   auf der Rueckseite zur roten J5-Linie fuehren.",
        "4. KONTAKTSEITE: Zeigen die Goldfinger jetzt VOM Streifen WEG (zu dir, wenn du auf die",
        "   Rueckseite schaust)?  JA = passt (Top-Kontakt-Buchse).  NEIN = gespiegelte Buchse noetig.",
        "5. PIN 1: Notieren, an welcher Kante Pin 1 auf der Rueckseite ankommt (links/rechts) —",
        "   damit gleichen wir die J5-Verdrahtung ab (Rechnung sagt: links/rechts kippt NIE,",
        "   aber die Buchse ist auf der Rueckseite x-gespiegelt montiert).",
    ]):
        text(10, oy3 + 5 + i * 4.5, z, 2.9)
    text(10, oy3 + 46, "Vorhersage der Rechnung (docs/17): Kontakte am gelieferten Panel von HINTEN sichtbar -> passt.", 2.9, True)

    a('</svg>')
    open(ZIEL, "w", encoding="utf-8").write("\n".join(e))
    print("geschrieben:", ZIEL)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
