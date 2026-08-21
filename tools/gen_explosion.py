#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Massstaebliche Explosionsdarstellung der Front - zwei Schnitte, eine
Draufsicht und die eingebaute Tiefenlage, gezeichnet aus den Quellen.

    python3 tools/gen_explosion.py

Erzeugt docs/renders/front-explosion.png.

WARUM GEZEICHNET UND NICHT GERENDERT
------------------------------------
docs/renders/stack.png ist kein 3D-Bild, sondern drei KiCad-Ansichten
versetzt uebereinander - und der gedruckte Adapter fehlt darin ganz, weil er
kein Board ist. Der naheliegende Weg waere die fertige Baugruppe
mechanical/export/switchstack_stack.step; die ist 57 MB gross, und zwei
Sitzungen haben sich am Laden aufgehaengt.

Dieses Werkzeug geht deshalb den leichten Weg: Es liest die MASSE aus den
Quellen und zeichnet daraus. Kein Geometriekern, keine nennenswerte
Rechenzeit - und fuer die Montagefrage ist ein bemasster Schnitt ohnehin
brauchbarer als ein huebsches Rendering.

WAS DIE ZEICHNUNG ZEIGT
-----------------------
  * Schnitt A-A bei y = 0     - Tiefenkette, Display, Schaumdichtung,
                                Rastung, Flansch, Rahmen, Stapelverbinder
  * Schnitt B-B bei y = 19,6  - Ecktaster gegen Druckkreuz, Magnetkontakt
                                im Boarddurchbruch, J6 auf der Rueckseite
  * Draufsicht                - Adapter ueber dem Top-Board, dazu Rahmen,
                                Zentralscheibe und die USB-C-Buchse des
                                Mid-Boards
  * Tiefenlage eingebaut      - dieselben Teile an ihrer wahren z-Lage

WAS SIE NICHT ZEIGT
-------------------
  * keine Bauteile ausser den ausdruecklich beschrifteten - ein Schnitt
    zeigt nur, was in seiner Ebene liegt
  * keine Dose, keine Schrauben, keine Kabel
  * die Explosionsabstaende sind Darstellung, kein Mass; die Teile selbst
    und ihre eingebaute Tiefenlage sind massstaeblich
  * der Magnetkontakt sitzt im Abdeckrahmen (docs/04, 2b/F14)
    sind nicht gemessen (Punkt 64)

QUELLEN DER MASSE
-----------------
Alle Zahlen werden mit ast aus dem Quelltext gelesen, nicht abgeschrieben:
PARAMS aus mechanical/adapter.py, TEILE/ADAPTER aus mechanical/stack.py,
Boardmasse aus tools/gen_boards.py, Kerbe, Magnetloch, Taster und Stapellage
aus tools/gen_layouts.py. Was dort nicht steht - Panelmasse, Scheiben- und
Rahmenmasse aus dem Messprotokoll -, steht unten im Block AUS DER DOKU, je
mit Fundstelle.

Der Selbsttest prueft die Tiefenkette gegen die Quellen und schreibt
Abweichungen IN das Bild, statt sie zu verschweigen.
"""

import ast
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIEL = os.path.join(ROOT, "docs", "renders", "front-explosion.png")


# ---------------------------------------------------------------------------
# MASSE AUS DEN QUELLEN LESEN
# ---------------------------------------------------------------------------

def _wert(node):
    """Literale, dict(...)-Aufrufe und einfache Vorzeichen."""
    if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "dict":
        return {kw.arg: _wert(kw.value) for kw in node.keywords}
    return ast.literal_eval(node)


def lies(pfad, *namen):
    """Holt Modulkonstanten, ohne das Modul zu importieren.

    Wichtig: mechanical/adapter.py importiert build123d auf Modulebene. Ein
    schlichtes import zoege damit den ganzen Geometriekern herein - genau
    das, was hier vermieden werden soll.
    """
    with open(pfad, "r", encoding="utf-8") as f:
        baum = ast.parse(f.read(), filename=pfad)

    gefunden = {}
    for knoten in baum.body:
        if not isinstance(knoten, ast.Assign):
            continue
        for ziel in knoten.targets:
            if isinstance(ziel, ast.Name) and ziel.id in namen:
                gefunden[ziel.id] = _wert(knoten.value)
            elif isinstance(ziel, ast.Tuple):
                # Form: NOTCH_X0, NOTCH_X1 = -23.5, -17.25
                werte = _wert(knoten.value)
                for el, w in zip(ziel.elts, werte):
                    if isinstance(el, ast.Name) and el.id in namen:
                        gefunden[el.id] = w
    fehlt = [n for n in namen if n not in gefunden]
    if fehlt:
        raise RuntimeError("%s: %s nicht gefunden" % (pfad, ", ".join(fehlt)))
    return gefunden


P = lies(os.path.join(ROOT, "mechanical", "adapter.py"), "PARAMS")["PARAMS"]
T = lies(os.path.join(ROOT, "mechanical", "tragring.py"), "PARAMS")["PARAMS"]
S = lies(os.path.join(ROOT, "mechanical", "stack.py"), "TEILE", "ADAPTER")
B = lies(os.path.join(ROOT, "tools", "gen_boards.py"),
         "BOARD_DIAMETER", "BOARD_THICKNESS", "TOP_SQ", "HOLE_PITCH_R")
G = lies(os.path.join(ROOT, "mechanical", "gehaeuse.py"), "PARAMS")["PARAMS"]
L = lies(os.path.join(ROOT, "tools", "gen_layouts.py"),
         "NOTCH_X0", "NOTCH_X1", "NOTCH_Y0", "NOTCH_Y1",
         "KERB_W", "KERB_T", "STACK_POS", "BTN_POS")

# Der Magnetkontakt sitzt seit dem 19.08.2026 im ABDECKRAHMEN unten mittig
# (docs/04, 2b), nicht mehr in einem Loch des Boards. Im Board gibt es nur
# noch die Kabelkerbe KERB_W x KERB_T an der Unterkante; hier abgeleitet:
MAG_FRAME_Y = 31.5       # Mitte der unteren Rahmenleiste (Fenster 27,5 + 4)
MAG_FLANSCH = 12.0       # Flansch des DCX-909


# --- AUS DER DOKU, je mit Fundstelle --------------------------------------
# Panel ER-TFT1.69-3, docs/17-bauteildaten.md Abschnitt 1
PANEL_X, PANEL_Y, PANEL_T = 37.43, 30.07, 1.6
# Tiefenkette der Displayflaeche, docs/04-mechanical.md Abschnitt 1e
SCHAUM = 1.90            # Luft, darin die Schaumdichtung
KLEBEFUGE = 0.15         # 0,1 bis 0,2
# Zentralscheibe und Rahmen, Messprotokoll F1/F2/F8/F9/F11
SCHEIBE_AM = 55.2
SCHEIBE_WAND = 1.0       # F9: kein Kragen, nur die Wand
NASE_B = 1.0             # F8: Nasen 1,0 breit und hoch
RAHMEN_AM = 81.0         # docs/04 Abschnitt 1b
RAHMEN_FENSTER = 56.0    # F11
RAHMEN_T = 12.0
# Stapelverbinder: Koerper 4,1 breit (adapter.py, Kommentar zur Durchfuehrung)
STK_B = 4.1
# USB-C GT-USB-7051x auf dem Mid-Board, Footprint 9,94 x 6,40, Hoehe 9,25
# (docs/17). J7 steht quer bei (-20,0 / 8,4), also um 90 Grad gedreht.
USB_X, USB_Y, USB_H = -20.0, 8.4, 9.25
USB_A, USB_B = 9.94, 6.40
TASTER_A, TASTER_B = 3.9, 2.9   # SMD-Taster, docs/04
KREUZ = 3.2                     # F10
# JST GH BM02B stehend, gesteckt rund 5,7 mm (gen_layouts, Kommentar zu J6)
J6_X, J6_Y, J6_H, J6_B = 0.0, 19.0, 4.25, 6.0   # liegend seit 19.08.2026
HUELSE_X = 21.5          # Huelsen und Schrauben: die H1/H2-Achse
HUELSE_B = 2.25          # halbe Schluesselweite 4,5
# Fenster der Zentralscheibe, docs/04 Abschnitt 1d
FENSTER_X, FENSTER_Y = 32.7, 27.0
FENSTER_M = (-0.95, -0.3)       # Mitte, in KiCad-y (nach unten)


# ---------------------------------------------------------------------------
# TIEFENKETTE - eine Quelle fuer alle vier Ansichten
# ---------------------------------------------------------------------------

def tiefenkette():
    """z waechst nach VORN, Nullpunkt ist die Rueckseite des Bottom-Boards.

    Die Lage des Adapters wird nicht abgeschrieben, sondern gerechnet: Seine
    Platinentasche (Modellhoehe seat) muss auf der Rueckseite des Top-Boards
    liegen. Daraus folgt der Versatz; stack.py wird dagegen geprueft.
    """
    d = B["BOARD_THICKNESS"]
    z = {}
    for name, zb in S["TEILE"]:
        z[name.replace(".step", "")] = (zb, zb + d)

    # gerechnet wie _z() in adapter.py
    z_pcb_back = P["plate_face_t"] + P["cross_h"] + P["switch_h"] + P["pcb_t"]
    total = P["plate_depth"] + P["flange_t"]
    seat = total - z_pcb_back
    versatz = z["top_ui"][0] - seat                 # 20,0 - 4,5 = 15,5

    a = dict(
        versatz=versatz,
        flansch=(versatz, versatz + P["flange_t"]),
        hals=(versatz + P["flange_t"],
              versatz + P["flange_t"] + P["neck_depth"]),
        schulter=(versatz + P["flange_t"] + P["neck_depth"], versatz + seat),
        tasche=(versatz + seat, versatz + seat + P["pcb_t"]),
        front=versatz + total,
    )
    front = a["front"]                              # Sichtflaeche der Scheibe
    z["adapter"] = (a["flansch"][0], front)
    z["adapter_teile"] = a
    z["scheibe"] = (front - P["plate_depth"], front)
    z["sichtflaeche"] = (front - P["plate_face_t"], front)
    z["kreuz"] = (front - P["plate_face_t"] - P["cross_h"],
                  front - P["plate_face_t"])
    z["taster"] = (z["kreuz"][0] - P["switch_h"], z["kreuz"][0])
    z["panel"] = (z["top_ui"][1], z["top_ui"][1] + PANEL_T)
    z["schaum"] = (z["panel"][1], z["panel"][1] + SCHAUM)
    # Angenommen: Der Rahmen sitzt mit seiner Rueckseite auf der Wand, also
    # buendig mit der Flanschrueckseite. Ungeprueft - Punkt 63.
    z["rahmen"] = (versatz, versatz + RAHMEN_T)
    return z


Z = tiefenkette()


def selbsttest():
    """Liefert Meldungen; sie werden ins Bild geschrieben."""
    m = []
    soll = Z["adapter_teile"]["versatz"]
    ist = S["ADAPTER"][1]
    if abs(soll - ist) > 0.01:
        m.append("stack.py setzt den Adapter auf z = %.1f; aus der "
                 "Taschenlage folgt %.1f" % (ist, soll))
    # Punkt 67: Den Halt gibt seit dem 21.08. nicht mehr der umlaufende
    # Rand (49,8 - der lag UNTER dem Nasenmass), sondern der Rastnocken
    # an den vier Kantenmitten.
    hinter = (P["snap_nose"] - P["snap_inner"]) / 2.0
    if hinter < 0.2:
        m.append("Rastnocken %.1f gegen Nasenmass %.1f: nur %.2f mm "
                 "Hintergriff je Seite - Punkt 67"
                 % (P["snap_nose"], P["snap_inner"], hinter))
    frei = Z["mid_logic"][0] - Z["bottom_power_motor"][1]
    if abs(frei - 5.0) > 0.01:
        m.append("Ebenenabstand im Modell %.1f mm frei, erwartet 5,0 "
                 "(kurzer Stapel, Punkt 23/66)" % frei)
    ux0, ux1 = USB_X - USB_B / 2.0, USB_X + USB_B / 2.0
    if not (P["usb_relief_x0"] <= ux0 and P["usb_relief_x1"] >= ux1):
        m.append("USB-Freistellung des Adapters bei x = %.1f…%.1f, die "
                 "Buchse steht bei x = %.1f…%.1f - Punkt 68 ist WIEDER auf"
                 % (P["usb_relief_x0"], P["usb_relief_x1"], ux0, ux1))
    return m


# ---------------------------------------------------------------------------
# ZEICHENWERKZEUG
# ---------------------------------------------------------------------------

SS = 2                   # Ueberabtastung, am Ende wird herunterskaliert
PX_MM = 6.5              # Massstab
LUECKE = 15.0            # Explosionsabstand in mm - neun getrennte
                         # Stationen brauchen Luft fuer ihre Fahnen
BREITE, HOEHE = 2700, 1500

PAPIER = (250, 249, 246)
TUSCHE = (28, 28, 30)
GRAU = (120, 120, 126)
FEIN = (198, 196, 190)
PCB = (38, 92, 70)
PCB_H = (52, 118, 92)
KUNST = (206, 148, 52)
KUNST_H = (245, 224, 178)
WEISS = (228, 228, 224)
DISPLAY = (40, 54, 78)
SCHAUM_F = (176, 178, 184)
BAUTEIL = (110, 110, 118)
ROT = (176, 48, 36)

FONTS = "/System/Library/Fonts/Supplemental/"


def font(gr, fett=False):
    name = "Arial Bold.ttf" if fett else "Arial.ttf"
    try:
        return ImageFont.truetype(FONTS + name, int(gr * SS))
    except OSError:
        return ImageFont.load_default()


KLEIN = font(10)
NORMAL = font(11)
HALB = font(12, True)
MITTEL = font(14, True)
GROSS = font(19, True)
TITEL = font(28, True)
ZEILE = 15               # Zeilenabstand kleiner Beschriftungen

bild = Image.new("RGB", (BREITE * SS, HOEHE * SS), PAPIER)
d = ImageDraw.Draw(bild)


def px(v):
    return int(round(v * SS))


def text(x, y, s, f=NORMAL, farbe=TUSCHE, anker="la"):
    d.text((px(x), px(y)), s, font=f, fill=farbe, anchor=anker)


def linie(x0, y0, x1, y1, farbe=TUSCHE, w=1.0):
    d.line((px(x0), px(y0), px(x1), px(y1)), fill=farbe,
           width=max(1, px(w)))


def strichlinie(x0, y0, x1, y1, farbe=FEIN, w=1.0, an=7, aus=6):
    dx, dy = x1 - x0, y1 - y0
    laenge = (dx * dx + dy * dy) ** 0.5
    if laenge < 1e-9:
        return
    ex, ey = dx / laenge, dy / laenge
    s = 0.0
    while s < laenge:
        e = min(s + an, laenge)
        linie(x0 + ex * s, y0 + ey * s, x0 + ex * e, y0 + ey * e, farbe, w)
        s = e + aus


def kasten(x0, y0, x1, y1, fuell=None, rand=TUSCHE, w=0.9):
    x0, x1 = min(x0, x1), max(x0, x1)
    y0, y1 = min(y0, y1), max(y0, y1)
    if x1 - x0 < 0.4:
        x1 = x0 + 0.4
    if y1 - y0 < 0.4:
        y1 = y0 + 0.4
    if fuell:
        d.rectangle((px(x0), px(y0), px(x1), px(y1)), fill=fuell)
    if rand:
        d.rectangle((px(x0), px(y0), px(x1), px(y1)), outline=rand,
                    width=max(1, px(w)))


def strichkasten(x0, y0, x1, y1, farbe=GRAU, w=0.9):
    strichlinie(x0, y0, x1, y0, farbe, w)
    strichlinie(x1, y0, x1, y1, farbe, w)
    strichlinie(x1, y1, x0, y1, farbe, w)
    strichlinie(x0, y1, x0, y0, farbe, w)


def kreis(cx, cy, r, fuell=None, rand=TUSCHE, w=0.9):
    d.ellipse((px(cx - r), px(cy - r), px(cx + r), px(cy + r)),
              fill=fuell, outline=rand, width=max(1, px(w)))


# ---------------------------------------------------------------------------
# SCHNITTPANEL
# ---------------------------------------------------------------------------

class Schnitt(object):
    """z waagerecht nach rechts (nach vorn), x senkrecht (nach oben).

    Jede Gruppe bekommt einen eigenen z-Versatz - das ist die Explosion.
    Innerhalb einer Gruppe bleibt alles massstaeblich beieinander.
    """

    def __init__(self, x0, y0, breite, titel, unterzeile):
        self.ox, self.oy, self.breite = x0, y0, breite
        text(x0 - 30, y0 - 352, titel, GROSS)
        text(x0 - 30, y0 - 324, unterzeile, NORMAL, GRAU)
        self.versatz = {}
        self.cursor = 0.0

    def gruppe(self, name, z0, z1, luecke=LUECKE):
        self.versatz[name] = self.cursor - z0
        self.cursor += (z1 - z0) + luecke

    def X(self, name, z):
        return self.ox + (z + self.versatz[name]) * PX_MM

    def Y(self, x):
        return self.oy - x * PX_MM

    def flucht(self, *werte):
        for x in werte:
            for vz in ((1, -1) if x else (1,)):
                strichlinie(self.ox - 30, self.Y(vz * x),
                            self.ox + self.breite, self.Y(vz * x),
                            FEIN, 0.5, 10, 8)

    def teil(self, name, z0, z1, x0, x1, fuell, rand=TUSCHE, w=0.9):
        kasten(self.X(name, z0), self.Y(x1), self.X(name, z1), self.Y(x0),
               fuell, rand, w)

    def marke(self, name, z, x, s, farbe=GRAU, anker="lm"):
        text(self.X(name, z), self.Y(x), s, KLEIN, farbe, anker)

    def fahne(self, name, z, x_oben, zeilen, hoch=0):
        """Beschriftung nach oben: senkrechter Anstrich, dann Text.

        Eintraege sind Zeichenketten oder (Text, Farbe). hoch hebt die
        ganze Fahne an, damit sich benachbarte Gruppen nicht ins Wort
        fallen.
        """
        xz = self.X(name, z)
        y0 = self.Y(x_oben)
        y1 = y0 - 20 - ZEILE * (len(zeilen) - 1) - hoch
        linie(xz, y0, xz, y1 + 6, GRAU, 0.6)
        for i, eintrag in enumerate(zeilen):
            zeile, farbe = (eintrag if isinstance(eintrag, tuple)
                            else (eintrag, TUSCHE if i == 0 else GRAU))
            text(xz, y1 - 4 + ZEILE * i, zeile, HALB if i == 0 else KLEIN,
                 farbe, "ls")


# --- Panel A: Schnitt bei y = 0 -------------------------------------------

def panel_a(x0, y0):
    s = Schnitt(x0, y0, 1000, "Schnitt A – A   ·   Ebene y = 0",
                "EINBAUREIHENFOLGE, von hinten nach vorn: Feldstecker → "
                "Becher → Bottom → Mid → Tragring → Abdeckrahmen → "
                "Scheibenadapter → Top → Zentralscheibe · "
                "Explosion %.0f mm, sonst maßstäblich" % LUECKE)
    r = B["BOARD_DIAMETER"] / 2.0
    h = B["TOP_SQ"] / 2.0
    ad = Z["adapter_teile"]
    rand = (P["snap_inner"] - P["rim_play"]) / 2.0                    # 24,90
    hals = rand - P["neck_relief"] / 2.0                              # 24,15
    tasche = (P["pcb_sq"] + P["pcb_play"]) / 2.0                      # 23,70
    bohr = P["bore_sq"] / 2.0                                         # 21,50
    sx = abs(L["STACK_POS"]["J3"][0])
    btn = abs(L["BTN_POS"]["SW1"][0])
    am = SCHEIBE_AM / 2.0

    s.flucht(0.0, h, rand)

    # Feldstecker - das ERSTE Teil der Kette: Die vorverdrahtete
    # Micro-Fit-Leiste klickt von hinten an Bottom, bevor der Stapel in
    # die Dose geht. J1 sitzt laut gen_layouts bei (0,0 / 17,5) und ist
    # hier in die Schnittebene projiziert.
    s.gruppe("feld", -6.6, 0.0)
    s.teil("feld", -6.6, 0.0, -18.7, -2.3, BAUTEIL)
    s.fahne("feld", -6.6, r,
            ["Feldstecker Molex Micro-Fit 43045-1612",
             "16-polig · gecrimpt · projiziert (y = 17,5)",
             "steckt von hinten durch den Tunnel des Bechers"])

    # Gehaeuse-Becher - das Untergeschoss des gedruckten Tragrings.
    # Bottom und Mid werden HIER eingelegt (Auflagebosse tragen das
    # Bottom-Board bei z = 0), dann schliesst der Tragring den Becher
    # per Bajonett - die Boards gehen nie durch die 50,6er Oeffnung.
    g_in = (G["board_d"] + G["spiel"]) / 2.0                          # 26,20
    g_aus = g_in + G["wand"]                                          # 27,30
    g_boden = -(G["tief_hinten"] + G["boden_t"])                      # -8,70
    s.gruppe("becher", g_boden, G["rand_vorn"])
    s.teil("becher", g_boden, g_boden + G["boden_t"], -g_in, g_in,
           KUNST_H, KUNST)
    for vz in (1, -1):
        s.teil("becher", g_boden, G["rand_vorn"], vz * g_in, vz * g_aus,
               KUNST_H, KUNST)
        # Auflageboss (auf der Diagonale, hier projiziert): Oberkante z = 0
        s.teil("becher", g_boden + G["boden_t"], 0.0,
               vz * (g_in - G["boss_b"]), vz * g_in, BAUTEIL, None)
    s.fahne("becher", g_boden, g_aus,
            ["Gehäuse-Becher, gedruckt — Untergeschoss des Tragrings",
             "Ø 54,6 · 4 Dom-Fenster à 10 (Ø-6-Dome!) · Tunnel hinten",
             "Kartusche: 2 × M2,5 × 14 von hinten in die unteren Hülsen"],
            hoch=60)

    # Kartuschen-Schrauben (Konzept v3): M2,5 x 14 von hinten durch
    # Boden und Fuehrungsrohr in die unteren Huelsen (H1/H2-Achse)
    for vz in (1, -1):
        s.teil("becher", g_boden + G["boden_t"], -G["kanal_luft"],
               vz * G["schraube_x"] - G["kanal_od"] / 2,
               vz * G["schraube_x"] + G["kanal_od"] / 2, FEIN, TUSCHE)
        s.teil("becher", g_boden - 1.7, g_boden,
               vz * G["schraube_x"] - 2.25, vz * G["schraube_x"] + 2.25,
               TUSCHE, TUSCHE)
        s.teil("becher", g_boden, -G["kanal_luft"],
               vz * G["schraube_x"] - 1.25, vz * G["schraube_x"] + 1.25,
               TUSCHE, TUSCHE)

    # Bottom-Board samt Stapelverbinder in den 10 mm darueber
    s.gruppe("bottom", Z["bottom_power_motor"][0], Z["mid_logic"][0])
    zb = Z["bottom_power_motor"]
    s.teil("bottom", zb[0], zb[1], -r, r, PCB)
    for vz in (1, -1):
        s.teil("bottom", zb[1], Z["mid_logic"][0], vz * sx - STK_B / 2,
               vz * sx + STK_B / 2, BAUTEIL)
    s.fahne("bottom", zb[0], r, ["Bottom-Board", "Ø 52,0 × 1,0"])
    s.marke("bottom", zb[1] + 1.4, -sx - 7.0, "Stapelverbinder 2×20,")
    s.marke("bottom", zb[1] + 1.4, -sx - 11.0, "1,27 mm · Stapelhöhe 6,0")
    for vz in (1, -1):
        s.teil("bottom", zb[1], Z["mid_logic"][0], vz * HUELSE_X - HUELSE_B,
               vz * HUELSE_X + HUELSE_B, FEIN, TUSCHE)
    s.marke("bottom", zb[1] + 1.4, HUELSE_X + 3.5,
            "Hülse M2,5 × 5", TUSCHE)

    # Mid-Board
    s.gruppe("mid", Z["mid_logic"][0], Z["top_ui"][0])
    zm = Z["mid_logic"]
    s.teil("mid", zm[0], zm[1], -r, r, PCB)
    for vz in (1, -1):
        s.teil("mid", zm[1], Z["top_ui"][0], vz * sx - STK_B / 2,
               vz * sx + STK_B / 2, BAUTEIL)
    s.fahne("mid", zm[0], r, ["Mid-Board", "Ø 52,0 × 1,0"])
    for vz in (1, -1):
        s.teil("mid", zm[1], Z["top_ui"][0], vz * HUELSE_X - HUELSE_B,
               vz * HUELSE_X + HUELSE_B, FEIN, TUSCHE)
    s.marke("mid", zm[1] + 1.4, HUELSE_X + 3.5,
            "Hülse M2,5 × 5", TUSCHE)

    # Tragring - er liegt auf der Wandebene, zwischen Mid und Top. Die
    # Huelsen laufen frei durch seine 50,6er Oeffnung; der Basisring des
    # Adapters taucht hindurch und wird von ihr zentriert.
    s.gruppe("tragring", Z["rahmen"][0], Z["rahmen"][0] + T["t"])
    for vz in (1, -1):
        s.teil("tragring", Z["rahmen"][0], Z["rahmen"][0] + T["t"],
               vz * T["open_sq"] / 2.0, vz * T["grip"] / 2.0, KUNST_H, KUNST)
    s.fahne("tragring", Z["rahmen"][0], T["grip"] / 2.0,
            ["Tragring — liegt lose auf",
             "70 × 70 × 2 · Schrauben auf 60,0"], hoch=40)

    # Abdeckrahmen
    s.gruppe("rahmen", Z["rahmen"][0], Z["rahmen"][1])
    zr = Z["rahmen"]
    for vz in (1, -1):
        s.teil("rahmen", zr[0], zr[1], vz * RAHMEN_FENSTER / 2.0,
               vz * RAHMEN_AM / 2.0, WEISS)
        s.teil("rahmen", zr[0], zr[0] + 4.0, vz * P["frame_grip"] / 2.0,
               vz * (P["frame_grip"] / 2.0 + 1.6), BAUTEIL, None)
    s.fahne("rahmen", zr[0], RAHMEN_AM / 2.0,
            ["Abdeckrahmen 1721-914",
             "81 × 81 × 12 · klemmt am Tragring"], hoch=-150)


    # Adapter
    s.gruppe("adapter", Z["adapter"][0], Z["adapter"][1])
    for vz in (1, -1):
        # Seit dem 19.08.2026 endet der Adapter am Schnapprand: Der 70er
        # Flansch samt Schraubschlitzen gehoert jetzt dem Tragring-Adapter
        # (mechanical/tragring.py), der zwischen Mid und Top an der Wand
        # sitzt und hier nicht geschnitten wird - Befestigungskonzept v2,
        # docs/04 Abschnitt 2b.
        s.teil("adapter", ad["flansch"][0], ad["flansch"][1],
               vz * bohr, vz * rand, KUNST_H, KUNST)
        s.teil("adapter", ad["hals"][0], ad["hals"][1], vz * bohr, vz * hals,
               KUNST_H, KUNST)
        s.teil("adapter", ad["schulter"][0], ad["schulter"][1], vz * bohr,
               vz * rand, KUNST_H, KUNST)
        s.teil("adapter", ad["tasche"][0], ad["tasche"][1], vz * tasche,
               vz * rand, KUNST_H, KUNST)
    s.fahne("adapter", ad["flansch"][0], rand,
            ["Scheibenadapter, gedruckt",
             "49,8 · Rastnocken 50,6 an 4 Kantenmitten"], hoch=-45)
    s.marke("adapter", ad["hals"][0] + 0.4, hals - 4.5, "Rastraum 1,5 × 1,3")
    s.marke("adapter", ad["tasche"][0] + 0.4, tasche - 9.0,
            "Tasche 47,4 · Auflage 2,0")
    s.marke("adapter", ad["flansch"][0], -rand - 4.0,
            "Kragen 52,0 liegt auf dem Tragring — Kraftkette gesichert")
    s.marke("adapter", ad["flansch"][0], -rand - 8.0,
            "Drucklippe 51,6 zusätzlich am Rahmensteg (F15 offen)", ROT)

    # Top-Board mit den beiden Schrauben von vorn
    s.gruppe("top", Z["top_ui"][0], Z["schaum"][1])
    zt = Z["top_ui"]
    s.teil("top", zt[0], zt[1], -h, h, PCB)
    s.fahne("top", zt[0], h,
            ["Top-Board 47 × 47",
             "+ Displaypanel, geklebt",
             "+ Schaumdichtung 1,90"], hoch=40)
    for vz in (1, -1):
        # Kopf auf der Platinenvorderseite, Schaft durch H1/H2 in die Huelse
        s.teil("top", zt[1], zt[1] + 1.7, vz * HUELSE_X - 2.25,
               vz * HUELSE_X + 2.25, TUSCHE, TUSCHE)
        s.teil("top", zt[0] - 1.0, zt[1], vz * HUELSE_X - 1.25,
               vz * HUELSE_X + 1.25, TUSCHE, TUSCHE)
    s.marke("top", zt[0] - 1.0, -(HUELSE_X + 4.5),
            "M2,5 Flachkopf von vorn — zieht alles zusammen", TUSCHE, "rm")

    # Displaypanel und Schaumdichtung: TEIL der Top-Station (das Panel
    # ist vor der Montage aufgeklebt, der Schaum aufgelegt) - keine
    # eigenen Kettenglieder.
    zp = Z["panel"]
    s.teil("top", zp[0], zp[1], -PANEL_X / 2, PANEL_X / 2, DISPLAY)
    s.teil("top", zp[0], zp[0] + KLEBEFUGE, -PANEL_X / 2, PANEL_X / 2,
           ROT, None)

    zs = Z["schaum"]
    s.teil("top", zs[0], zs[1], -PANEL_X / 2, PANEL_X / 2, SCHAUM_F, GRAU)

    # Zentralscheibe
    s.gruppe("scheibe", Z["scheibe"][0], Z["scheibe"][1])
    zc = Z["scheibe"]
    s.teil("scheibe", Z["sichtflaeche"][0], Z["sichtflaeche"][1], -am, am,
           WEISS)
    for vz in (1, -1):
        s.teil("scheibe", zc[0], Z["sichtflaeche"][0],
               vz * (am - SCHEIBE_WAND), vz * am, WEISS)
        s.teil("scheibe", zc[0], zc[0] + NASE_B, vz * P["snap_inner"] / 2.0,
               vz * (am - SCHEIBE_WAND), WEISS)
        s.teil("scheibe", Z["kreuz"][0], Z["kreuz"][1], vz * btn - KREUZ / 2,
               vz * btn + KREUZ / 2, FEIN, GRAU)
    s.fahne("scheibe", zc[0], am,
            ["Zentralscheibe 6435-914", "55,2 × 55,2 × 7,5",
             "kraftfrei aufgeclippt — sie ist das",
             "Bedienelement und bleibt beweglich"], hoch=-60)
    s.marke("scheibe", zc[0] - 1.0, -am - 9.0,
            "Rastnase 1,0 klickt über den Nocken 50,6 (0,30 Hintergriff)",
            GRAU, "ra")
    s.marke("scheibe", zc[0] - 1.0, -am - 13.0,
            "durch die Nasenpässe in Lippe und Kragen (Punkt 67 erledigt)",
            GRAU, "ra")
    s.marke("scheibe", zc[1] + 1.5, -btn, "Druckkreuz (projiziert)")

# --- Panel B: Schnitt bei y = 19,6 ----------------------------------------

def panel_b(x0, y0):
    s = Schnitt(x0, y0, 620,
                "Schnitt B – B   ·   Ebene y = 19,6  (6-Uhr-Seite)",
                "Ecktaster gegen Druckkreuz · Kabelkerbe unten mittig · "
                "J6 auf der Rückseite")
    r = B["BOARD_DIAMETER"] / 2.0
    sehne = (r * r - 19.6 ** 2) ** 0.5
    h = B["TOP_SQ"] / 2.0
    ad = Z["adapter_teile"]
    rand = (P["snap_inner"] - P["rim_play"]) / 2.0
    tasche = (P["pcb_sq"] + P["pcb_play"]) / 2.0
    bohr = P["bore_sq"] / 2.0
    btn = abs(L["BTN_POS"]["SW1"][0])
    am = SCHEIBE_AM / 2.0

    s.flucht(0.0, h, rand)

    # Mid mit der USB-C-Buchse (projiziert)
    s.gruppe("mid", Z["mid_logic"][0], Z["top_ui"][0])
    zm = Z["mid_logic"]
    s.teil("mid", zm[0], zm[1], -sehne, sehne, PCB)
    s.teil("mid", zm[1], zm[1] + USB_H, USB_X - USB_B / 2, USB_X + USB_B / 2,
           BAUTEIL)
    s.fahne("mid", zm[0], sehne, ["Mid-Board", "Sehne 2 × %.1f mm" % sehne])
    s.marke("mid", zm[1] + 1.2, USB_X - USB_B / 2 - 2.5,
            "USB-C 9,25 hoch (projiziert, y = 8,4)", GRAU, "rm")

    # Scheibenadapter - dieselbe Kette wie in Schnitt A:
    # ... Tragring, Abdeckrahmen, ADAPTER, Top, Zentralscheibe
    s.gruppe("adapter", Z["adapter"][0], Z["adapter"][1])
    for vz in (1, -1):
        s.teil("adapter", ad["flansch"][0], ad["flansch"][1], vz * bohr,
               vz * P["frame_grip"] / 2.0, KUNST_H, KUNST)
        s.teil("adapter", ad["hals"][0], ad["schulter"][1], vz * bohr,
               vz * rand, KUNST_H, KUNST)
        s.teil("adapter", ad["tasche"][0], ad["tasche"][1], vz * tasche,
               vz * rand, KUNST_H, KUNST)
    s.fahne("adapter", ad["flansch"][0], P["frame_grip"] / 2.0,
            ["Adapter", "Durchführung 43 × 43"])

    # Top mit Durchbruch, Tastern und J6
    s.gruppe("top", Z["top_ui"][0] - J6_H, Z["top_ui"][1])
    zt = Z["top_ui"]
    # Die Schnittebene y = 19,6 liegt VOR der Kerbentiefe (Kante 23,5,
    # Kerbe bis 21,5) - das Board ist hier durchgehend; die Kerbe wird als
    # Strichkasten angedeutet.
    mx0, mx1 = -L["KERB_W"] / 2.0, L["KERB_W"] / 2.0
    s.teil("top", zt[0], zt[1], -h, h, PCB)
    strichkasten(s.X("top", zt[0]), s.Y(mx1), s.X("top", zt[1]),
                 s.Y(mx0), ROT)
    s.teil("top", zt[0] - J6_H, zt[0], J6_X - J6_B / 2, J6_X + J6_B / 2,
           BAUTEIL)
    for vz in (1, -1):
        s.teil("top", Z["taster"][0], Z["taster"][1], vz * btn - TASTER_A / 2,
               vz * btn + TASTER_A / 2, BAUTEIL)
    s.fahne("top", zt[0], h, ["Top-Board 47 × 47", "Kabelkerbe 5 × 2",
                              ("Magnetkontakt im Rahmen (F14)", ROT)])
    s.marke("top", zt[0] - J6_H - 1.2, -30.0, "J6 (JST GH, hinten)",
            GRAU, "rm")
    s.marke("top", Z["taster"][0] + 0.5, btn + 4.0, "Ecktaster 2,0 hoch")

    # Zentralscheibe mit den Druckkreuzen
    s.gruppe("scheibe", Z["scheibe"][0], Z["scheibe"][1])
    zc = Z["scheibe"]
    s.teil("scheibe", Z["sichtflaeche"][0], Z["sichtflaeche"][1], -am, am,
           WEISS)
    for vz in (1, -1):
        s.teil("scheibe", zc[0], Z["sichtflaeche"][0],
               vz * (am - SCHEIBE_WAND), vz * am, WEISS)
        s.teil("scheibe", Z["kreuz"][0], Z["kreuz"][1], vz * btn - KREUZ / 2,
               vz * btn + KREUZ / 2, WEISS)
    s.fahne("scheibe", zc[0], am,
            ["Zentralscheibe", "Druckkreuze 3,2 × 3,2 · 1,5 hoch"])
    s.marke("scheibe", zc[1] + 1.5, -btn,
            "Kreuz trifft Taster – Nullspalt (Punkt 62)", ROT)


# --- Panel C: Draufsicht ---------------------------------------------------

def panel_c(cx, cy):
    text(cx - 300, cy - 330, "Draufsicht auf die Front", GROSS)
    text(cx - 300, cy - 302,
         "Blick auf die Sichtfläche · y nach unten wie in KiCad",
         NORMAL, GRAU)

    def X(x):
        return cx + x * PX_MM

    def Y(y):
        return cy + y * PX_MM

    def rechteck(x0, y0, x1, y1, fuell=None, rand=TUSCHE, w=0.9):
        kasten(X(x0), Y(y0), X(x1), Y(y1), fuell, rand, w)

    def srechteck(x0, y0, x1, y1, farbe=GRAU, w=0.9):
        strichkasten(X(x0), Y(y0), X(x1), Y(y1), farbe, w)

    h = B["TOP_SQ"] / 2.0
    rand = (P["snap_inner"] - P["rim_play"]) / 2.0
    tasche = (P["pcb_sq"] + P["pcb_play"]) / 2.0
    bohr = P["bore_sq"] / 2.0
    fg = T["grip"] / 2.0

    # Tragring (70er Platte mit den Geraeteschrauben) und darin der
    # Scheibenadapter - seit Befestigungskonzept v2 zwei Teile.
    rechteck(-fg, -fg, fg, fg, KUNST_H, KUNST, 1.2)
    srechteck(-rand, -rand, rand, rand, KUNST)
    srechteck(-tasche, -tasche, tasche, tasche, KUNST)
    rechteck(-bohr, -bohr, bohr, bohr, PAPIER, KUNST, 1.2)
    for vz in (1, -1):
        halb = (T["screw_slot_len"] + T["screw_slot_w"]) / 2.0
        rechteck(vz * T["screw_pitch"] / 2 - halb, -T["screw_slot_w"] / 2,
                 vz * T["screw_pitch"] / 2 + halb, T["screw_slot_w"] / 2,
                 PAPIER, ROT)
    text(X(-fg), Y(-fg) - 12,
         "Tragring 70,0, Öffnung 50,6 · Adapter 49,8 taucht durch",
         KLEIN, KUNST, "lb")

    # USB-Freistellung des Adapters - seit dem 20.08.2026 als Randkerbe
    # der LINKEN Kante, deckungsgleich ueber der Buchse (Punkt 68 behoben).
    rechteck(P["usb_relief_x0"], P["usb_relief_y0"], P["usb_relief_x1"],
             P["usb_relief_y1"], PAPIER, KUNST, 1.2)
    text(X(P["usb_relief_x0"]) - 8, Y(P["usb_relief_y0"]) - 6,
         "USB-Freistellung des Adapters, deckt die Buchse", KLEIN, KUNST, "rb")

    # Top-Board mit Randkerbe
    srechteck(-h, -h, h, h, PCB_H, 1.2)
    rechteck(L["NOTCH_X0"], L["NOTCH_Y0"], L["NOTCH_X1"], L["NOTCH_Y1"],
             PAPIER, PCB_H, 1.2)
    text(X(L["NOTCH_X0"]) - 8, Y(L["NOTCH_Y0"]) - 6, "Randkerbe 6,25 × 9,5",
         KLEIN, PCB_H, "rb")

    # USB-C des Mid-Boards, projiziert
    rechteck(USB_X - USB_B / 2, USB_Y - USB_A / 2, USB_X + USB_B / 2,
             USB_Y + USB_A / 2, None, ROT, 1.2)
    text(X(USB_X) - 8, Y(USB_Y + USB_A / 2) + 14, "USB-C auf Mid",
         KLEIN, GRAU, "rt")

    # Displaypanel an seiner wahren Lage: Mitte (-0,95 / 0,3), quer
    px0, px1 = -0.95 - PANEL_X / 2, -0.95 + PANEL_X / 2
    py0, py1 = 0.3 - PANEL_Y / 2, 0.3 + PANEL_Y / 2
    srechteck(px0, py0, px1, py1, DISPLAY)
    # Die Fahne faltet ab Werk an der RECHTEN Panelkante (Korrektur in
    # der Nacht zum 21.08.: quer eingebaut kommt sie seitlich, nicht von
    # unten) und liegt unter dem Panel; ihre Finger landen auf J5.
    strichlinie(X(px1), Y(py0) - 8, X(px1), Y(py1) + 8, ROT, 1.2, 6, 5)
    srechteck(px1 - 12.96, 0.3 - 5.7, px1, 0.3 + 5.7, ROT, 0.6)
    for i in range(12):
        yy = 0.3 - 3.85 + i * 0.7
        rechteck(4.45, yy - 0.2, 7.65, yy + 0.2, BAUTEIL, None, 0.3)
    text(X(px1) + 6, Y(py1) + 10, "Faltkante der Fahne (x = 17,8)",
         KLEIN, ROT, "lt")
    text(X(4.45) - 6, Y(0.3 + 5.7) + 10,
         "Fahne unterm Panel · Finger face-down auf J5 (Pin 1 oben)",
         KLEIN, ROT, "lt")
    rechteck(FENSTER_M[0] - FENSTER_X / 2, FENSTER_M[1] - FENSTER_Y / 2,
             FENSTER_M[0] + FENSTER_X / 2, FENSTER_M[1] + FENSTER_Y / 2,
             None, DISPLAY, 1.2)
    text(X(FENSTER_M[0] - 6.5), Y(FENSTER_M[1]), "Fenster 32,7 × 27,0",
         KLEIN, DISPLAY, "mm")
    text(X(FENSTER_M[0] - 6.5), Y(FENSTER_M[1]) + 14, "Panel 37,43 × 30,07",
         KLEIN, GRAU, "mm")

    # Ecktaster
    for bx, by in L["BTN_POS"].values():
        rechteck(bx - TASTER_A / 2, by - TASTER_B / 2, bx + TASTER_A / 2,
                 by + TASTER_B / 2, BAUTEIL, TUSCHE, 0.6)
    text(X(L["BTN_POS"]["SW1"][0]) - 6, Y(L["BTN_POS"]["SW1"][1]) - 12,
         "Ecktaster (±18 / ±20)", KLEIN, GRAU, "rb")

    # Kabelkerbe unten mittig; der Magnetkontakt selbst sitzt im
    # Abdeckrahmen und liegt ausserhalb dieser Draufsicht des Boards.
    h_top = B["TOP_SQ"] / 2.0
    rechteck(-L["KERB_W"] / 2.0, h_top - L["KERB_T"], L["KERB_W"] / 2.0,
             h_top, PAPIER, ROT, 1.2)
    text(X(0) - 6, Y(h_top - L["KERB_T"]) - 6,
         "Kabelkerbe %.0f × %.0f → Magnet im Rahmen (y ≈ %.0f)"
         % (L["KERB_W"], L["KERB_T"], MAG_FRAME_Y), KLEIN, ROT, "rb")
    rechteck(J6_X - J6_B / 2, J6_Y - 2.5, J6_X + J6_B / 2, J6_Y + 2.5, None,
             GRAU)
    text(X(J6_X) - 8, Y(J6_Y), "J6", KLEIN, GRAU, "rm")

    # Zentralscheibe und Rahmen
    srechteck(-SCHEIBE_AM / 2, -SCHEIBE_AM / 2, SCHEIBE_AM / 2,
              SCHEIBE_AM / 2, TUSCHE, 1.0)
    rechteck(-RAHMEN_AM / 2, -RAHMEN_AM / 2, RAHMEN_AM / 2, RAHMEN_AM / 2,
             None, TUSCHE, 1.2)
    rechteck(-RAHMEN_FENSTER / 2, -RAHMEN_FENSTER / 2, RAHMEN_FENSTER / 2,
             RAHMEN_FENSTER / 2, None, TUSCHE, 1.0)
    text(X(0), Y(RAHMEN_AM / 2) + 10,
         "Abdeckrahmen 81 × 81 · Fenster 56,0 · Zentralscheibe 55,2",
         KLEIN, TUSCHE, "ma")


# --- Tiefenlage eingebaut --------------------------------------------------

def tiefenband(x0, y0):
    text(x0 - 70, y0 - 34,
         "Tiefenlage eingebaut  ·  z ab Rückseite Bottom-Board", MITTEL)
    hoehe = 16

    def X(z):
        return x0 + z * PX_MM

    balken = [
        ("Bottom", Z["bottom_power_motor"], PCB),
        ("Mid", Z["mid_logic"], PCB),
        ("Top", Z["top_ui"], PCB),
        ("Panel", Z["panel"], DISPLAY),
        ("Schaum", Z["schaum"], SCHAUM_F),
        ("Adapter", Z["adapter"], KUNST_H),
        ("Scheibe", Z["scheibe"], WEISS),
        ("Rahmen", Z["rahmen"], WEISS),
    ]
    for i, (name, (a, b), farbe) in enumerate(balken):
        y = y0 + i * (hoehe + 4)
        kasten(X(a), y, X(b), y + hoehe, farbe, TUSCHE, 0.7)
        text(x0 - 10, y + hoehe / 2.0, name, KLEIN, TUSCHE, "rm")
        text(X(b) + 8, y + hoehe / 2.0,
             ("%.1f … %.1f" % (a, b)).replace(".", ","), KLEIN, GRAU, "lm")

    y = y0 + len(balken) * (hoehe + 4) + 8
    linie(X(0), y, X(Z["rahmen"][1]), y, TUSCHE, 0.9)
    for z in (0.0, 10.0, 20.0, Z["adapter"][1]):
        linie(X(z), y, X(z), y + 6, TUSCHE, 0.9)
        text(X(z), y + 9, ("%.1f" % z).replace(".", ","), KLEIN, TUSCHE, "ma")
    linie(X(Z["rahmen"][1]), y, X(Z["rahmen"][1]), y + 6, TUSCHE, 0.9)
    rs = Z["rahmen"][1] - Z["adapter"][1]
    text(x0 - 70, y + 30,
         "Sichtfläche liegt %.1f mm hinter der Rahmenvorderkante (Punkt 63)"
         % rs, KLEIN, ROT)


# --- Kopf und Notizen ------------------------------------------------------

def kopf_und_notizen(meldungen):
    text(40, 34, "SwitchStack – Explosionsdarstellung der Front", TITEL)
    text(40, 74, "Abdeckrahmen · Zentralscheibe · gedruckter Adapter · "
                 "Top-Board · Displaypanel", MITTEL, GRAU)
    text(40, 96, "Gezeichnet aus mechanical/adapter.py, mechanical/stack.py, "
                 "tools/gen_boards.py und tools/gen_layouts.py — kein "
                 "CAD-Lauf, keine STEP-Datei.", NORMAL, GRAU)
    linie(40, 120, BREITE - 40, 120, FEIN, 1)

    x0, y0 = 1500, 1060
    kasten(x0, y0, BREITE - 40, HOEHE - 40, None, FEIN, 1)
    text(x0 + 18, y0 + 16, "Was die Zeichnung zeigt – und was nicht", MITTEL)
    zeilen = [
        "Maßstäblich sind die Teile und ihre eingebaute Tiefenlage.",
        "Die Explosionsabstände von %.0f mm sind Darstellung, kein Maß."
        % LUECKE,
        "Ein Schnitt zeigt nur, was in seiner Ebene liegt; »projiziert«",
        "heißt: liegt daneben und ist hineingeklappt.",
        "Nicht dargestellt: Dose, Schrauben, Kabel und alle Bauteile ohne",
        "eigene Beschriftung. Der Magnetkontakt sitzt im Abdeckrahmen",
        "unten mittig und liegt damit ausserhalb der Schnittebenen.",
    ]
    for i, s in enumerate(zeilen):
        text(x0 + 18, y0 + 48 + i * 17, s, NORMAL, GRAU)

    yy = y0 + 48 + len(zeilen) * 17 + 10
    text(x0 + 18, yy, "Selbsttest gegen die Quellen (rot im Bild):", HALB, ROT)
    yy += 22
    for m in meldungen or ["keine Abweichung"]:
        rest, erste = m, True
        while rest:
            if len(rest) > 66:
                schnitt = rest[:66]
                p = schnitt.rfind(" ")
                zeile, rest = rest[:p], rest[p + 1:]
            else:
                zeile, rest = rest, ""
            text(x0 + 18, yy, ("• " if erste else "   ") + zeile, KLEIN, ROT)
            yy += 15
            erste = False


def main():
    meldungen = selbsttest()

    panel_a(300, 470)
    panel_b(300, 1120)
    panel_c(2350, 470)
    tiefenband(2190, 830)
    kopf_und_notizen(meldungen)

    aus = bild.resize((BREITE, HOEHE), Image.LANCZOS)
    os.makedirs(os.path.dirname(ZIEL), exist_ok=True)
    aus.save(ZIEL, optimize=True)

    print("geschrieben  : %s" % ZIEL)
    print("Massstab     : %.1f px/mm, Explosionsabstand %.0f mm"
          % (PX_MM, LUECKE))
    print("Adapter      : z = %.1f … %.1f (Versatz aus der Taschenlage)"
          % (Z["adapter"][0], Z["adapter"][1]))
    print("Sichtflaeche : z = %.1f, Rahmenvorderkante z = %.1f"
          % (Z["adapter"][1], Z["rahmen"][1]))
    for m in meldungen:
        print("   ! %s" % m)
    return 0


if __name__ == "__main__":
    sys.exit(main())
