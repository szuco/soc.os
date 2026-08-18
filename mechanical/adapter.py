#!/usr/bin/env python3
"""
KiCad SwitchStack - Adapter fuer die Busch-Jaeger Zentralscheibe 6435-914.

Ersetzt die frueher hier erzeugte Frontplatte mit Sicheltasten. Die Sichtflaeche
ist jetzt ein Serienteil: Zentralscheibe 6435-914 (2CKA006430A0402) im Rahmen
1721-914, beide Busch-balance SI. Dieses Teil ist das Bindeglied dazwischen -
es bietet der Scheibe an, worauf sie rastet, dem Rahmen, worauf er klemmt, und
der Top-Leiterplatte, worauf sie sitzt.

EIN TEIL STATT ZWEI (Festlegung 16.08.2026)
-------------------------------------------
Zwischenzeitlich stand die Ueberlegung, einen fertigen Blech-Tragring zu
verwenden und den Adapter nur darauf zu setzen. Verworfen: Der Blechring baut
zusaetzlich auf, und seine Krallen werden nicht gebraucht - das Geraet haengt
an den zwei Geraeteschrauben, wie jeder Serieneinsatz auch. Dieses gedruckte
Teil uebernimmt daher ALLE drei Aufgaben:

    1. Tragring   - wird mit zwei Schrauben auf 60 mm in die Dose geschraubt
    2. Rahmenhalt - der Abdeckrahmen klemmt auf seinen 70,0 mm
    3. Traeger    - Leiterplatte in der Tasche, Zentralscheibe rastet auf

Montagereihenfolge: Adapter anschrauben, Rahmen aufsetzen, Zentralscheibe
aufstecken. Die Scheibe ist damit das einzige Teil, das man ohne Werkzeug
abnimmt - und darunter liegt der USB-Anschluss (Punkt 45).

VORBEHALT: Das Teil traegt die Schraubkraefte in gedrucktem Kunststoff. Die
Schraubaugen sind der Schwachpunkt; ob 2,5 mm Flansch reichen, zeigt der erste
Druck. Ein Blechring bleibt der Rueckfallweg, falls sie ausreissen.

    python3 mechanical/adapter.py

Erzeugt:
    export/adapter.step / .stl

DIE TIEFENKETTE - sie bestimmt alles Uebrige
--------------------------------------------
z zaehlt von der Sichtflaeche der Scheibe nach HINTEN:

    0,0 .. 1,0   Zentralscheibe, Sichtflaeche (gemessen F1)
    1,0 .. 2,5   Druckkreuz auf ihrer Rueckseite (F10: 1,5 hoch)
    2,5 .. 4,5   SMD-Taster ueber der Leiterplatte
    4,5 .. 5,5   Leiterplatte (1,0 dick)
           7,5   Rastebene und hinterer Rand der Scheibe (F2)

Daraus folgen zwei Dinge, die nicht verhandelbar sind:

  * Die Rastebene liegt HINTER der Leiterplatte. Der Schnapprand steht also
    hinter ihr und traegt sie zugleich - er ist Rastglied und Auflage in einem.
  * Die Scheibe rastet auf lichte 50,0 (F8). Bei 1,4 mm Wand bleiben innen
    genau 47,0 - das ist die Kantenlaenge des Top-Boards. Nach unten begrenzen
    die Taster: Sie stehen auf (+/-18 / +/-20), reichen mit Footprint bis 22,2,
    und mit Randabstand braucht es mindestens 45,4.

Alle Masse in mm. Aenderungen ausschliesslich im PARAMS-Block.
"""

from pathlib import Path

from build123d import (
    BuildPart, BuildSketch, Plane, Rectangle, Locations, SlotOverall,
    extrude, fillet, Mode, export_step, export_stl, Pos, Box, Compound,
)

# ---------------------------------------------------------------------------
# PARAMETER
# ---------------------------------------------------------------------------

PARAMS = dict(
    # --- Gemessen an der Zentralscheibe 6435-914 (docs/04, F1..F10) --------
    plate_face_t      = 1.0,    # Dicke der Sichtflaeche
    plate_depth       = 7.5,    # Gesamttiefe bis zur hintersten Kante
    cross_h           = 1.5,    # Hoehe der vier Druckkreuze
    snap_inner        = 50.0,   # lichtes Mass zwischen den vier Rastnasen

    # --- Gemessen am Abdeckrahmen 1721-914 (F11, F13) ---------------------
    frame_grip        = 70.0,   # darauf klemmen die Doppelstege des Rahmens
    frame_depth       = 12.0,   # Bautiefe des Rahmens - der Adapter muss
                                # vollstaendig darunter verschwinden

    # --- Leiterplatte und Bestueckung -------------------------------------
    pcb_sq            = 47.0,   # Kantenlaenge Top-Board (= TOP_SQ)
    pcb_corner_r      = 4.0,    # Eckradius (= TOP_CR)
    pcb_t             = 1.0,
    pcb_play          = 0.4,    # Spiel in der Tasche, gesamt
    switch_h          = 2.0,    # SMD-Taster ueber der Platine
    btn_x             = 18.0,   # Tasterposition = Kreuzposition
    btn_y             = 20.0,
    btn_reach         = 22.2,   # groesste Ausdehnung eines Tasters vom Zentrum

    # --- Schnapprand -------------------------------------------------------
    rim_wall          = 1.4,    # Wandstaerke -> bestimmt pcb_sq
    rim_play          = 0.2,    # Untermass gegen snap_inner
    neck_depth        = 1.3,    # Hoehe des Rastraums hinter der Schulter
    neck_relief       = 1.5,    # wie weit der Rastraum zurueckspringt
    seat_w            = 2.0,    # Auflagebreite fuer die Platine

    # --- Tragring-Flansch --------------------------------------------------
    flange_t          = 2.5,
    screw_pitch       = 60.0,   # DIN 49073
    screw_slot_w      = 3.9,
    screw_slot_len    = 4.0,

    # --- Zentrale Durchfuehrung -------------------------------------------
    # Muss die beiden Stackverbinder durchlassen: sie stehen bei x = +/-14,2,
    # sind 4,1 breit und 26,4 lang -> bis (16,25 / 13,2).
    bore_sq           = 43.0,

    # --- Freistellung fuer die USB-C-Buchse, 18.08.2026 -------------------
    # Die Buchse steht seit heute auf dem MID-Board und greift durch eine
    # Randkerbe des Top-Boards nach vorn. Ihr Koerper reicht in KiCad-
    # Koordinaten bis (7,65 / 22,45) - die zentrale Durchfuehrung endet aber
    # schon bei 21,5. Ohne diese Freistellung stiesse die Buchse gegen den
    # Auflagesteg des Adapters.
    #
    # ORIENTIERUNG: y waechst hier wie in KiCad nach UNTEN, also zur
    # 6-Uhr-Seite - dort sitzen Klinkenbuchse, USB-Kerbe und diese
    # Freistellung. Der Adapter ist dadurch nicht mehr punktsymmetrisch und
    # kann nur in einer Lage montiert werden; die Kerbe des Top-Boards zeigt
    # dieselbe Richtung und macht es beim Zusammenbau sichtbar.
    usb_relief_x0     = -1.2,   # Koerper -0,65 minus Spiel
    usb_relief_x1     = 8.2,    # Koerper  7,65 plus Spiel
    usb_relief_y      = 24.0,   # bis hinter die Boardkante (23,5)
)


def _z(p):
    """Tiefenkette -> Modellhoehen. Im Modell waechst z nach VORN, damit das
    Teil auf dem Flansch steht; die Doku zaehlt von der Sichtflaeche nach
    hinten. Rueckgabe: (flansch, hals, auflage, tasche) als Oberkanten."""
    z_pcb_back = (p["plate_face_t"] + p["cross_h"]
                  + p["switch_h"] + p["pcb_t"])          # 5,5
    total = p["plate_depth"] + p["flange_t"]             # 10,0
    return dict(
        flange=p["flange_t"],                            # 0 .. 2,5
        neck=p["flange_t"] + p["neck_depth"],            # .. 3,8
        seat=total - z_pcb_back,                         # .. 4,5
        pocket=total - z_pcb_back + p["pcb_t"],          # .. 5,5
        z_pcb_back=z_pcb_back,
        total=total,
    )


def build_adapter(p=PARAMS):
    z = _z(p)
    rim_out = p["snap_inner"] - p["rim_play"]            # 49,8
    pocket_in = p["pcb_sq"] + p["pcb_play"]              # 47,4
    neck_out = rim_out - p["neck_relief"]                # 48,3 ... 46,8

    with BuildPart() as fp:
        # -- Tragring-Flansch: darauf klemmt der Rahmen ---------------------
        with BuildSketch(Plane.XY) as s:
            Rectangle(p["frame_grip"], p["frame_grip"])
            fillet(s.vertices(), 2.0)
        extrude(amount=z["flange"])

        # -- Rastraum: hier sitzen die vier Nasen der Scheibe ---------------
        with BuildSketch(Plane.XY.offset(z["flange"])):
            Rectangle(neck_out, neck_out)
        extrude(amount=z["neck"] - z["flange"])

        # -- Schulter + Auflage: der Rand, ueber den die Nasen schnappen ----
        with BuildSketch(Plane.XY.offset(z["neck"])):
            Rectangle(rim_out, rim_out)
        extrude(amount=z["seat"] - z["neck"])

        # -- Tasche fuer die Leiterplatte -----------------------------------
        with BuildSketch(Plane.XY.offset(z["seat"])) as s:
            Rectangle(rim_out, rim_out)
            Rectangle(pocket_in, pocket_in, mode=Mode.SUBTRACT)
        extrude(amount=z["pocket"] - z["seat"])

        # -- Zentrale Durchfuehrung fuer Stackverbinder und Display-FPC -----
        with BuildSketch(Plane.XY) as s:
            Rectangle(p["bore_sq"], p["bore_sq"])
            fillet(s.vertices(), 2.0)
        extrude(amount=z["total"], mode=Mode.SUBTRACT)

        # -- Freistellung fuer die USB-C-Buchse ----------------------------
        # Verlaengert die zentrale Durchfuehrung an einer Stelle bis hinter
        # die Boardkante, damit der Buchsenkoerper vom Mid-Board hindurchgreift.
        with BuildSketch(Plane.XY) as u:
            with Locations(((p["usb_relief_x0"] + p["usb_relief_x1"]) / 2.0,
                            (p["bore_sq"] / 2.0 + p["usb_relief_y"]) / 2.0)):
                Rectangle(p["usb_relief_x1"] - p["usb_relief_x0"],
                          p["usb_relief_y"] - p["bore_sq"] / 2.0)
        extrude(amount=z["total"], mode=Mode.SUBTRACT)

        # -- Schraubschlitze auf 60 mm --------------------------------------
        for sx in (p["screw_pitch"] / 2, -p["screw_pitch"] / 2):
            with BuildSketch(Plane.XY):
                with Locations((sx, 0)):
                    SlotOverall(p["screw_slot_len"] + p["screw_slot_w"],
                                p["screw_slot_w"])
            extrude(amount=z["flange"], mode=Mode.SUBTRACT)

    return fp.part


# ---------------------------------------------------------------------------
# SELBSTTEST
# ---------------------------------------------------------------------------

def check_adapter(part, p=PARAMS):
    """Geometrische Zwangsbedingungen und Materialproben."""
    z = _z(p)
    errs = []
    rim_out = p["snap_inner"] - p["rim_play"]

    # -- rechnerische Bedingungen --------------------------------------
    if rim_out >= p["snap_inner"]:
        errs.append("Schnapprand %.1f passt nicht in das Rastmass %.1f"
                    % (rim_out, p["snap_inner"]))
    soll_pcb = rim_out - 2 * p["rim_wall"]
    if abs(soll_pcb - p["pcb_sq"]) > 0.01:
        errs.append("pcb_sq %.1f passt nicht zu Rand %.1f und Wand %.1f "
                    "(rechnerisch %.1f)"
                    % (p["pcb_sq"], rim_out, p["rim_wall"], soll_pcb))
    if p["btn_reach"] + 0.5 > p["pcb_sq"] / 2:
        errs.append("Taster reicht bis %.1f, Platinenhalbmass ist nur %.1f"
                    % (p["btn_reach"], p["pcb_sq"] / 2))
    if p["bore_sq"] > p["pcb_sq"] - 2 * p["seat_w"] + 1e-9:
        errs.append("Durchfuehrung %.1f laesst der Platine nur %.2f mm Auflage, "
                    "gefordert sind %.1f"
                    % (p["bore_sq"], (p["pcb_sq"] - p["bore_sq"]) / 2,
                       p["seat_w"]))
    # Die USB-Freistellung muss den Buchsenkoerper aufnehmen (Koerper laut
    # KiCad-Footprint -0,65..7,65 in x, bis 22,45 in y) und darf der Platine
    # nicht zu viel Auflage nehmen.
    if not (p["usb_relief_x0"] <= -0.65 and p["usb_relief_x1"] >= 7.65):
        errs.append("USB-Freistellung %.1f..%.1f deckt den Buchsenkoerper "
                    "-0,65..7,65 nicht ab"
                    % (p["usb_relief_x0"], p["usb_relief_x1"]))
    if p["usb_relief_y"] < 22.45:
        errs.append("USB-Freistellung reicht nur bis %.1f, der Buchsenkoerper "
                    "bis 22,45" % p["usb_relief_y"])
    breite = p["usb_relief_x1"] - p["usb_relief_x0"]
    if breite > p["pcb_sq"] * 0.3:
        errs.append("USB-Freistellung %.1f mm nimmt mehr als 30 %% der "
                    "Auflagekante (%.1f mm)" % (breite, p["pcb_sq"]))
    if p["frame_grip"] <= rim_out:
        errs.append("Flansch %.1f ist nicht breiter als der Schnapprand"
                    % p["frame_grip"])
    # Der Adapter baut vor der Wand - aber der Rahmen muss ihn verdecken.
    if z["total"] > p["frame_depth"]:
        errs.append("Bauhoehe %.1f ueberragt den Rahmen (%.1f tief)"
                    % (z["total"], p["frame_depth"]))
    if abs(z["total"] - (p["plate_depth"] + p["flange_t"])) > 0.01:
        errs.append("Tiefenkette inkonsistent")

    # -- Materialproben -------------------------------------------------
    def solid(probe, what):
        if (part & probe).volume < 1e-6:
            errs.append("kein Material: %s" % what)

    def clear(probe, what):
        if (part & probe).volume > 1e-6:
            errs.append("nicht frei: %s" % what)

    half = rim_out / 2
    # Der Rand traegt an allen vier Kantenmitten - dort rasten die Nasen.
    for name, (x, y) in (("rechts", (half - 0.5, 0)), ("links", (-half + 0.5, 0)),
                         ("oben", (0, half - 0.5)), ("unten", (0, -half + 0.5))):
        solid(Pos(x, y, (z["neck"] + z["seat"]) / 2) * Box(0.6, 0.6, 0.4),
              "Schnapprand %s" % name)

    # Der Rastraum springt zurueck, sonst kann nichts einrasten.
    for name, x in (("rechts", half - 0.4), ("links", -half + 0.4)):
        clear(Pos(x, 0, (z["flange"] + z["neck"]) / 2) * Box(0.4, 0.6, 0.4),
              "Rastraum %s" % name)

    # Durchfuehrung frei, Auflage vorhanden.
    # Probe deutlich kleiner als die Bohrung - deren Ecken sind verrundet.
    clear(Pos(0, 0, z["total"] / 2) * Box(p["bore_sq"] - 8, p["bore_sq"] - 8,
                                          z["total"] - 0.2),
          "zentrale Durchfuehrung")
    solid(Pos(p["bore_sq"] / 2 + 0.6, 0, (z["neck"] + z["seat"]) / 2)
          * Box(0.6, 0.6, 0.4), "Auflage der Leiterplatte")

    # Die Platine muss in die Tasche passen, die Taschenwand muss stehen.
    clear(Pos(0, 0, (z["seat"] + z["pocket"]) / 2)
          * Box(p["pcb_sq"] - 0.2, p["pcb_sq"] - 0.2, 0.4), "Platinentasche")
    solid(Pos(rim_out / 2 - 0.3, 0, (z["seat"] + z["pocket"]) / 2)
          * Box(0.4, 0.6, 0.4), "Taschenwand")

    # Schraubschlitze frei, Flansch aussen massiv.
    for sx in (p["screw_pitch"] / 2, -p["screw_pitch"] / 2):
        clear(Pos(sx, 0, z["flange"] / 2) * Box(1.0, 1.0, z["flange"] - 0.2),
              "Schraubschlitz x=%+.0f" % sx)
    solid(Pos(p["frame_grip"] / 2 - 1.0, p["frame_grip"] / 2 - 1.0,
              z["flange"] / 2) * Box(0.8, 0.8, 0.4), "Flanschecke")

    return errs


def main():
    p = PARAMS
    part = build_adapter(p)
    errs = check_adapter(part, p)
    z = _z(p)
    rim_out = p["snap_inner"] - p["rim_play"]

    print("Selbsttest   : %s" % ("BESTANDEN" if not errs else "FEHLGESCHLAGEN"))
    for e in errs:
        print("   ! %s" % e)

    out = Path(__file__).parent / "export"
    out.mkdir(exist_ok=True)
    export_step(part, str(out / "adapter.step"))
    export_stl(part, str(out / "adapter.stl"))

    print("Flansch      : %.1f x %.1f x %.1f mm (Rahmen klemmt darauf)"
          % (p["frame_grip"], p["frame_grip"], p["flange_t"]))
    print("Schnapprand  : %.1f aussen, Rastmass der Scheibe %.1f"
          % (rim_out, p["snap_inner"]))
    print("Platine      : %.1f x %.1f, Tasche %.1f, Auflage %.1f mm breit"
          % (p["pcb_sq"], p["pcb_sq"], p["pcb_sq"] + p["pcb_play"],
             (p["pcb_sq"] - p["bore_sq"]) / 2))
    print("Bauhoehe     : %.1f mm; Platinenrueckseite %.1f hinter der Sichtflaeche"
          % (z["total"], z["z_pcb_back"]))
    print("Export       : %s" % out)
    return 1 if errs else 0


if __name__ == "__main__":
    raise SystemExit(main())
