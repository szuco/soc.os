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
    BuildPart, BuildSketch, Plane, Rectangle, Circle, Locations, SlotOverall,
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
    # 1,5 statt 2,0 seit dem Tasterwechsel SKRK -> SKQG (20.08.2026,
    # Punkt 69 - das SKRK ist abgekuendigt). Die Tiefenkette rechnet sich
    # daraus neu: Die Platine rueckt 0,5 mm nach vorn, die Auflage wird
    # entsprechend tiefer.
    switch_h          = 1.5,    # SMD-Taster ueber der Platine (SKQG)
    btn_x             = 18.0,   # Tasterposition = Kreuzposition
    btn_y             = 20.0,
    btn_reach         = 22.3,   # SKQG: 19,7 + 5,2/2 in y (Taster 0,3 innen)

    # --- Schnapprand -------------------------------------------------------
    rim_wall          = 1.4,    # Wandstaerke -> bestimmt pcb_sq
    rim_play          = 0.2,    # Untermass gegen snap_inner
    neck_depth        = 1.3,    # Hoehe des Rastraums hinter der Schulter
    neck_relief       = 1.5,    # wie weit der Rastraum zurueckspringt
    seat_w            = 2.0,    # Auflagebreite fuer die Platine

    # --- Basisring ---------------------------------------------------------
    # Bis zum 19.08.2026 trug hier ein 70er Flansch den Abdeckrahmen und
    # zwei Schraubschlitze die Dosenbefestigung. Beides ist an den
    # TRAGRING-ADAPTER (mechanical/tragring.py) gewandert: Der Rahmen klemmt
    # dort, die Dose haelt dort. Dieses Teil ist seither nur noch der
    # SCHEIBENTRAEGER - es muss durch die Fensteroeffnung des Rahmens
    # (Steg ~50) passen und darf deshalb nirgends breiter sein als der
    # Schnapprand. Die Tiefenkette bleibt unveraendert; aus dem Flansch
    # wurde ein gleich dicker Basisring in Randbreite.
    # 2,0 statt 2,5 seit der Einbaupruefung gegen die GEMESSENE Dose
    # (21.08.2026, mechanical/pruefe_einbau.py): Mit 2,5 endete der
    # Adapter bei z = 15,0 - also 0,5 UNTER der Wandebene (15,5). Dort
    # ist die Oeffnung aber rund (Dose r 29), und die Ecken des 49,8er
    # Quadrats (Eckradius 35,2) drueckten auf Dosenrand und Putz
    # (44 mm3 Kollision). Hinten gekuerzt endet er buendig auf der
    # Wandebene; Rastraum, Auflage und Tasche bleiben im Raum exakt, wo
    # sie waren - nur die Flanschrueckseite wandert 0,5 nach vorn.
    flange_t          = 2.0,
    # KEIN schmaler Fuss - der Gedanke war falsch: Um die 43er Durchfuehrung
    # herum kann kein 34er Fuss existieren. Stattdessen ist die OEFFNUNG des
    # Tragrings 50,6 breit (tragring.py): Der ganze 49,8er Adapter taucht
    # hindurch, und die Oeffnung zentriert ihn mit 0,4 mm Spiel je Seite.
    # Aufgefallen beim Einbau des Tragrings in die Gesamtbaugruppe am
    # 19.08.2026 - Basisring und Platte wollten dasselbe Tiefenband.

    # --- Verschraubung Top <-> Mid ------------------------------------------
    # M2,5-Schrauben von vorn durch H1/H2 des Top-Boards in 10-mm-Huelsen
    # zum Mid-Board. Die Schraube laeuft NICHT durch dieses Teil - aber die
    # Huelse muss von hinten an die Platinenrueckseite heran, und dort steht
    # die Auflage im Weg. Je eine Tasche schafft Platz.
    huelse_x          = 21.5,   # wie H1/H2
    huelse_tasche_d   = 5.8,    # Sechskant SW 4,5 -> Eckenmass 5,2 + Spiel

    # --- Drucklippe (20.08.2026) ------------------------------------------
    # DIE ZENTRALSCHEIBE KANN NICHT KLEMMEN. Sie ist bei der 6435-914 das
    # Bedienelement - die ganze Scheibe bewegt sich, um die Ecktaster zu
    # druecken. Ein bewegliches Teil traegt keine Klemmkraft. Deshalb
    # presst der ADAPTER SELBST den Rahmensteg gegen den Tragring: mit
    # dieser Lippe an seiner Vorderkante, die ueber das Steg-Innenmass des
    # Rahmens greift.
    #
    # Die Lippe ist an den vier KANTENMITTEN unterbrochen - dort muessen
    # die Rastnasen der Scheibe (lichte 50,0) vorbei, und 51,6 liesse sie
    # nicht durch. Gedrueckt wird an den vier Ecken; der Steg ist
    # umlaufend, ihm ist das gleich.
    #
    # ZWEI MASSE SIND PLATZHALTER (Messpunkt F15): das Steg-Innenmass des
    # Rahmens (Lippe muss DARUEBER greifen, angenommen ~50,5) und das
    # Innenmass des Scheibenkorpus (Lippe muss DARUNTER bleiben,
    # angenommen ~52,5). lip_sq liegt dazwischen.
    lip_sq            = 51.6,   # PLATZHALTER - F15 messen
    lip_gap           = 14.0,   # Unterbrechung je Kantenmitte (Nasenpass)

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
    # BEHOBEN am 20.08.2026 (Punkt 68): Die Freistellung sass an der
    # 6-Uhr-Kante (x -1,2..8,2) - der Planungsstand VOR dem Umzug der
    # Buchse. Real steht sie links auf dem Mid-Board und greift durch die
    # Randkerbe des Top-Boards bei x -23,2..-16,8, y 3,4..13,4 nach vorn.
    # Zwei Tage lang stand der Widerspruch als roter Selbsttest-Punkt in
    # der Explosionszeichnung. Jetzt ist die Freistellung eine RANDKERBE
    # der linken Adapterkante, offen nach aussen - so findet auch der
    # breitere USB-Stecker von vorn hinein.
    usb_relief_x0     = -25.5,  # ueber die Aussenkante (24,9) hinaus
    usb_relief_x1     = -16.0,  # Koerper endet bei -16,8, plus Spiel
    usb_relief_y0     = 2.4,
    usb_relief_y1     = 14.4,

    # --- Halter fuer den Magnetkontakt des Sterns, 18.08.2026 -------------
    # Der Stern wird nicht mehr gesteckt, sondern magnetisch angelegt. Der
    # Kontakt sitzt in einem Loch der Zentralscheibe - dort, wo bis heute die
    # 6x5-Oeffnung fuer die JST-GH-Buchse vorgesehen war (docs/04, Durchbruch
    # unten links). Die Scheibe ist ein Kaufteil und kann den Kontakt nicht
    # halten; das uebernimmt dieser Halter.
    #
    # Aufbau: eine Huelse direkt hinter der Scheibeninnenseite, getragen von
    # zwei Stuetzen, die auf der Taschenwand stehen. Zwischen den Stuetzen
    # laeuft eine radiale Nut - durch sie geht das Kabel an der Boardkante
    # vorbei nach HINTEN zu J6, das seit heute auf der Rueckseite sitzt.
    # Deshalb braucht die Platine kein Loch und keine Kerbe.
    #
    # ACHTUNG - magnet_d und magnet_h sind PLATZHALTER. Sie muessen am
    # gekauften Teil (Elsaybro, ASIN B0H9Y9NVSV) mit dem Messschieber
    # genommen werden; ein Datenblatt gibt es zu dieser Handelsmarke nicht.
    # check_adapter() prueft, ob die gemessenen Werte in die Tiefe passen.
    magnet_x          = -10.0,  # wie der bisherige Durchbruch unten links
    magnet_y          = 19.4,
    # Der freie Streifen zwischen Displaypanel (endet bei y = 15,9) und
    # Platinenkante (23,5) ist nur 7,6 mm hoch. Mehr als rund 4,8 mm
    # Aussendurchmesser passen dort mit Huelsenwand nicht hinein - der
    # Selbsttest rechnet das nach.
    panel_y1          = 15.9,   # Vorderkante des Panels, aus gen_layouts
    #
    # ABGESCHALTET (magnet_d = None), und zwar aus einem guten Grund: Der
    # Magnetkontakt steckt seit dem 18.08.2026 in einem DURCHBRUCH des
    # Top-Boards (gen_layouts MAG_X/MAG_Y/MAG_D). Sein Koerper taucht damit
    # nach hinten in die 10 mm zwischen Top und Mid, und die Platine haelt
    # ihn - der Adapter muss nichts mehr tragen. Vorn liegt der Durchbruch
    # innerhalb der zentralen Durchfuehrung, also ohnehin frei.
    #
    # Der Halter bleibt als Bauteil erhalten. Er wird gebraucht, sobald ein
    # FLACHER Kontakt zum Einsatz kaeme (Bauhoehe <= 3,5 mm), der ohne
    # Durchbruch vor der Platine sitzen kann. Dann genuegt es, hier einen
    # Durchmesser einzutragen.
    magnet_d          = None,   # aus; Wert = Aussendurchmesser in mm
    magnet_h          = 3.0,    # PLATZHALTER - Bauhoehe messen
    magnet_wall       = 1.2,    # Wandstaerke der Huelse
    magnet_slot_w     = 2.4,    # Breite der Kabelnut
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
        # -- Basisring: taucht KOMPLETT durch die Tragring-Oeffnung ---------
        with BuildSketch(Plane.XY) as s:
            Rectangle(rim_out, rim_out)
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

        # -- Tasche fuer die Leiterplatte, aussen mit der Drucklippe --------
        with BuildSketch(Plane.XY.offset(z["seat"])) as s:
            # Volle Lippe, dann die Kantenmitten herausschneiden
            # (Nasenpass), dann das Grundband in Randbreite wieder
            # auffuellen, zuletzt die Tasche.
            Rectangle(p["lip_sq"], p["lip_sq"])
            Rectangle(p["lip_gap"], p["lip_sq"], mode=Mode.SUBTRACT)
            Rectangle(p["lip_sq"], p["lip_gap"], mode=Mode.SUBTRACT)
            Rectangle(rim_out, rim_out, mode=Mode.ADD)
            Rectangle(pocket_in, pocket_in, mode=Mode.SUBTRACT)
        extrude(amount=z["pocket"] - z["seat"])

        # -- Zentrale Durchfuehrung fuer Stackverbinder und Display-FPC -----
        with BuildSketch(Plane.XY) as s:
            Rectangle(p["bore_sq"], p["bore_sq"])
            fillet(s.vertices(), 2.0)
        extrude(amount=z["total"], mode=Mode.SUBTRACT)

        # -- Freistellung fuer die USB-C-Buchse: Kerbe der linken Kante ----
        with BuildSketch(Plane.XY) as u:
            with Locations(((p["usb_relief_x0"] + p["usb_relief_x1"]) / 2.0,
                            (p["usb_relief_y0"] + p["usb_relief_y1"]) / 2.0)):
                Rectangle(p["usb_relief_x1"] - p["usb_relief_x0"],
                          p["usb_relief_y1"] - p["usb_relief_y0"])
        extrude(amount=z["total"], mode=Mode.SUBTRACT)

        # -- Halter fuer den Magnetkontakt des Sterns -----------------------
        # Huelse + zwei Stuetzen + Kabelnut. Siehe Parameterblock.
        if p.get("magnet_d"):
            z_face = z["total"] - p["plate_face_t"]   # Innenseite der Scheibe
            z_m0 = z_face - p["magnet_h"]             # Rueckseite des Magneten
            d_out = p["magnet_d"] + 2 * p["magnet_wall"]
            y_in = pocket_in / 2.0                    # 23,7
            y_out = rim_out / 2.0                     # 24,9

            # Huelse
            with BuildSketch(Plane.XY.offset(z_m0)):
                with Locations((p["magnet_x"], p["magnet_y"])):
                    Circle(d_out / 2.0)
                    Circle(p["magnet_d"] / 2.0, mode=Mode.SUBTRACT)
            extrude(amount=z_face - z_m0)

            # Zwei Stuetzen links und rechts der Kabelnut, von der
            # Taschenwand nach vorn, und je eine Rippe zur Huelse.
            for sx in (p["magnet_x"] - d_out / 2.0, p["magnet_x"] + d_out / 2.0):
                with BuildSketch(Plane.XY.offset(z["pocket"])):
                    with Locations((sx, (y_in + y_out) / 2.0)):
                        Rectangle(2.0 * p["magnet_wall"], y_out - y_in)
                extrude(amount=z_face - z["pocket"])

                with BuildSketch(Plane.XY.offset(z_m0)):
                    with Locations((sx, (p["magnet_y"] + y_out) / 2.0)):
                        Rectangle(2.0 * p["magnet_wall"], y_out - p["magnet_y"])
                extrude(amount=z_face - z_m0)

            # Kabelnut: radial durch Auflage und Taschenwand, damit die
            # Litzen an der Boardkante vorbei nach hinten zu J6 kommen.
            with BuildSketch(Plane.XY.offset(z["neck"])):
                with Locations((p["magnet_x"],
                                (p["bore_sq"] / 2.0 + y_out) / 2.0)):
                    Rectangle(p["magnet_slot_w"], y_out - p["bore_sq"] / 2.0)
            extrude(amount=z["pocket"] - z["neck"], mode=Mode.SUBTRACT)

        # -- Huelsentaschen: die Huelse muss an die Platinenrueckseite ------
        for sx in (p["huelse_x"], -p["huelse_x"]):
            with BuildSketch(Plane.XY):
                with Locations((sx, 0)):
                    Circle(p["huelse_tasche_d"] / 2.0)
            extrude(amount=z["pocket"], mode=Mode.SUBTRACT)

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
    # Die USB-Freistellung muss den Buchsenkoerper aufnehmen: links auf dem
    # Mid-Board, KiCad-Koordinaten x -23,2..-16,8, y 3,4..13,4.
    if not (p["usb_relief_x0"] <= -23.2 and p["usb_relief_x1"] >= -16.8):
        errs.append("USB-Freistellung %.1f..%.1f deckt den Buchsenkoerper "
                    "-23,2..-16,8 nicht ab"
                    % (p["usb_relief_x0"], p["usb_relief_x1"]))
    if not (p["usb_relief_y0"] <= 3.4 and p["usb_relief_y1"] >= 13.4):
        errs.append("USB-Freistellung y %.1f..%.1f deckt 3,4..13,4 nicht ab"
                    % (p["usb_relief_y0"], p["usb_relief_y1"]))
    hoehe = p["usb_relief_y1"] - p["usb_relief_y0"]
    if hoehe > p["pcb_sq"] * 0.3:
        errs.append("USB-Freistellung %.1f mm nimmt mehr als 30 %% der "
                    "Auflagekante (%.1f mm)" % (hoehe, p["pcb_sq"]))
    # Seit dem 19.08.2026 gilt das UMGEKEHRTE des alten Flansch-Kriteriums:
    # Das Teil muss durch die Fensteroeffnung des Rahmens (Steg ~50), darf
    # also nirgends breiter sein als der Schnapprand.
    if p["huelse_x"] + p["huelse_tasche_d"] / 2.0 > p["pcb_sq"] / 2.0 + 1.0:
        errs.append("Huelsentasche ragt ueber die Platinenkante hinaus")
    if p["huelse_x"] - p["huelse_tasche_d"] / 2.0 > p["bore_sq"] / 2.0:
        errs.append("Huelsentasche erreicht die Durchfuehrung nicht - die "
                    "Huelse stuende auf massivem Material")
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
    #
    # Die Probe endet bei der Vorderkante des Displaypanels. Der Streifen
    # dahinter (y = 15,9 bis zur Boardkante) ist KEIN Durchgang, sondern der
    # Platz, in dem der Magnethalter steht - er wird eigens geprueft. Vor dem
    # 18.08.2026 lief die Probe ueber die volle Bohrung und meldete den
    # Halter als Fehler.
    y_lo, y_hi = -(p["bore_sq"] - 8) / 2.0, p["panel_y1"] - 0.5
    clear(Pos(0, (y_lo + y_hi) / 2.0, z["total"] / 2)
          * Box(p["bore_sq"] - 8, y_hi - y_lo, z["total"] - 0.2),
          "zentrale Durchfuehrung")

    # -- Magnethalter ---------------------------------------------------
    if p.get("magnet_d"):
        d_out = p["magnet_d"] + 2 * p["magnet_wall"]
        y_vorn = p["magnet_y"] - d_out / 2.0
        y_hinten = p["magnet_y"] + d_out / 2.0
        if y_vorn < p["panel_y1"]:
            errs.append("Magnethuelse reicht bis y=%.1f und damit unter das "
                        "Displaypanel (Vorderkante %.1f) - Durchmesser %.1f "
                        "ist zu gross fuer den freien Streifen"
                        % (y_vorn, p["panel_y1"], p["magnet_d"]))
        if y_hinten > p["pcb_sq"] / 2.0:
            errs.append("Magnethuelse reicht bis y=%.1f, ueber die "
                        "Platinenkante %.1f hinaus"
                        % (y_hinten, p["pcb_sq"] / 2.0))
        z_m0 = z["total"] - p["plate_face_t"] - p["magnet_h"]
        if z_m0 < z["pocket"]:
            errs.append("Magnet baut %.1f mm und stoesst gegen die Platine - "
                        "frei sind nur %.2f mm"
                        % (p["magnet_h"],
                           z["total"] - p["plate_face_t"] - z["pocket"]))
        solid(Pos(p["magnet_x"], p["magnet_y"] + (p["magnet_d"] + d_out) / 4.0,
                  z["total"] - p["plate_face_t"] - p["magnet_h"] / 2.0)
              * Box(0.4, 0.4, 0.4), "Magnethuelse")
    # Probe an der 12-Uhr-Kante: an 3 und 9 Uhr sitzt die Huelsentasche,
    # an 6 Uhr die USB-Freistellung.
    solid(Pos(0, -(p["bore_sq"] / 2 + 0.6), (z["neck"] + z["seat"]) / 2)
          * Box(0.6, 0.6, 0.4), "Auflage der Leiterplatte")

    # Die Platine muss in die Tasche passen, die Taschenwand muss stehen.
    clear(Pos(0, 0, (z["seat"] + z["pocket"]) / 2)
          * Box(p["pcb_sq"] - 0.2, p["pcb_sq"] - 0.2, 0.4), "Platinentasche")
    solid(Pos(rim_out / 2 - 0.3, 0, (z["seat"] + z["pocket"]) / 2)
          * Box(0.4, 0.6, 0.4), "Taschenwand")

    # Huelsentaschen frei bis zur Platinenrueckseite.
    for sx in (p["huelse_x"], -p["huelse_x"]):
        clear(Pos(sx, 0, z["pocket"] / 2) * Box(2.0, 2.0, z["pocket"] - 0.2),
              "Huelsentasche x=%+.0f" % sx)
    # Drucklippe: an den Ecken vorhanden, an den Kantenmitten unterbrochen.
    if p["lip_sq"] <= rim_out:
        errs.append("Drucklippe %.1f greift nicht ueber den Rand %.1f - "
                    "sie wuerde den Rahmensteg nie beruehren"
                    % (p["lip_sq"], rim_out))
    if p["lip_sq"] >= p["snap_inner"] + 2.4:
        errs.append("Drucklippe %.1f vermutlich groesser als der "
                    "Scheibenkorpus innen (F15 messen!)" % p["lip_sq"])
    ecke = p["lip_sq"] / 2.0 - 0.4
    solid(Pos(ecke, ecke, (z["seat"] + z["pocket"]) / 2) * Box(0.5, 0.5, 0.4),
          "Drucklippe Ecke")
    clear(Pos(0, (rim_out + p["lip_sq"]) / 4.0 + rim_out / 4.0,
              (z["seat"] + z["pocket"]) / 2) * Box(1.0, 0.4, 0.4)
          if False else
          Pos(0, p["lip_sq"] / 2.0 - 0.3, (z["seat"] + z["pocket"]) / 2)
          * Box(1.0, 0.4, 0.4), "Nasenpass Kantenmitte")

    # Basisringecke massiv (der Ring liegt zwischen Durchfuehrung und Rand).
    solid(Pos(rim_out / 2 - 1.0, rim_out / 2 - 1.0, z["flange"] / 2)
          * Box(0.8, 0.8, 0.4), "Basisringecke")

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

    print("Basisring    : %.1f x %.1f x %.1f mm, taucht durch den Tragring"
          % (rim_out, rim_out, p["flange_t"]))
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
