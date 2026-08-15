#!/usr/bin/env python3
"""
KiCad SwitchStack - Frontplatte fuer 55x55-Schalterprogramme, Version 2.

  ACHTUNG: DIESES KONZEPT IST SEIT DEM 15.08.2026 UEBERHOLT.
  Die Sichtflaeche wird die Busch-Jaeger Zentralscheibe 6435-914
  (2CKA006430A0402) - eine Serien-Zentralscheibe mit dem Aufdruck "Pfeile und
  OK", die zum Bedienelement 6456-101 gehoert (54 x 54 x 23 mm, 1,68"-Display,
  vier Tasten). Damit entfallen die vier Sicheltasten und diese Platte; an ihre
  Stelle tritt ein gedruckter Adapter, der den BJ-Korpus nachbildet.
  Siehe docs/06-open-decisions.md, Punkte 41 bis 47, und docs/04 Abschnitt 1c.

  Diese Datei bleibt lauffaehig und erzeugt weiter die alte Platte - sie ist die
  Grundlage fuer den Adapter (Ohren, Zentrierkragen, Schraubenabstand und die
  geprueften Zwangsbedingungen sind uebernehmbar). Nicht mehr gueltig sind
  Sicheltasten, Stoessel, Blendring und das runde Displayfenster.

Design: rundes Display in der Mitte, vier SICHELFOERMIGE Tasten, die sich als
Ringsegmente um das Displayfenster legen. Die Tastenkappen sind separate
Druckteile, die von hinten eingesetzt werden und auf SMD-Taster der
Top-Leiterplatte druecken - die Federung kommt vom Taster, nicht vom Kunststoff.

Erzeugt:
    export/frontplate.step / .stl          Platte
    export/frontplate_caps.step / .stl     4 Tastenkappen
    export/frontplate_assembly.stl         Platte + Kappen in Einbaulage (Viewer)

    python3 mechanical/frontplate.py

Alle Masse in mm. Aenderungen ausschliesslich im PARAMS-Block.
"""

from pathlib import Path
import math

from build123d import (
    BuildPart, BuildSketch, Plane, Rectangle, Circle, SlotOverall, Locations,
    extrude, fillet, chamfer, loft, Mode, export_step, export_stl, Axis,
    Cylinder, Pos, Compound,
)

# ---------------------------------------------------------------------------
# PARAMETER
# ---------------------------------------------------------------------------

PARAMS = dict(
    # --- Zentralplatte ------------------------------------------------------
    # Zielrahmen FESTGELEGT: Busch-Jaeger 1721-914, Busch-balance SI, 1-fach
    # (2CKA001725A1555). Fenster 55 x 55 mm, aussen 81 x 81 x 12 mm. Damit
    # bleiben 0,2 mm Luft je Seite, und die 76 mm breiten Ohren verschwinden
    # hinter dem Rahmen. Offen ist, woran seine Klemmbefestigung greift -
    # Messliste in docs/04-mechanical.md Abschnitt 1b.
    plate_size        = 54.6,   # 55er-Norm; 0,4 mm Untermass fuer Druckertoleranz
    plate_thickness   = 2.5,
    plate_corner_r    = 2.0,
    plate_edge_cham   = 0.5,

    # --- Zentrierkragen nach hinten ----------------------------------------
    boss_size         = 50.0,
    boss_wall         = 2.0,
    boss_depth        = 3.0,

    # --- Tragring-Ohren (DIN 49073, 60 mm Schraubenabstand) ----------------
    ear_span          = 76.0,
    ear_width         = 14.0,
    ear_thickness     = 2.5,
    screw_pitch       = 60.0,
    screw_slot_len    = 4.0,
    screw_slot_w      = 3.9,

    # --- Displayfenster -----------------------------------------------------
    # Gewaehlt: ST77916 1,46" rund, 360x360, aktive Flaeche Ø37,25.
    # Alternativen: GC9A01 1,28" -> aktiv 32.4, Modul ~37.5
    #               CO5300 1,43" -> aktiv 36.3, Modul ~41.0
    disp_active_d     = 37.25,  # aktive Flaeche laut Datenblatt
    disp_module_d     = 41.5,   # Modul-Aussendurchmesser - AM REALEN TEIL MESSEN
    disp_clearance    = 0.5,    # Luft rings um das Modul
    disp_window_d     = 37.8,   # Sichtoeffnung, etwas > aktiv fuer Blickwinkel

    # --- Sicheltasten -------------------------------------------------------
    # Vier Ringsegmente zwischen Fenster und Plattenrand, auf den Diagonalen.
    # Zwischen den Segmenten bleiben vier Stege (Spokes) auf 0/90/180/270 Grad.
    #
    # ZWANGSBEDINGUNG (wird in check_plate geprueft):
    #   key_slot_ri - key_lip  >=  disp_module_d/2 + disp_clearance
    # Sonst kollidiert der Rueckhaltekragen der Kappen mit dem Displaymodul.
    key_slot_ri       = 22.0,   # Schlitz im Ring innen ...
    key_slot_ro       = 26.2,   # ... bis aussen
    # Stegbreite: die vier Stege sind die EINZIGEN Stellen, an denen die Platte
    # nach vorn durchbrochen werden darf - innen liegt das Display, im Ring
    # bewegen sich die Kappen. Auf 3 und 9 Uhr sitzen die Befestigungsbohrungen
    # der Platinen, es bleiben also 12 und 6 Uhr. Jeder der beiden traegt jetzt
    # genau EINEN Durchbruch: oben das ToF-Fenster, unten die Klinkenbuchse.
    # _ring_sketch schneidet beide Rechtecke symmetrisch - die Verbreiterung
    # von 9 auf 17 mm gilt ohnehin fuer alle vier Stege, sie wird jetzt nur
    # auch unten gebraucht. Die Sicheln verlieren dadurch je rund 25 Grad.
    key_spoke_hw      = 8.5,    # halbe Stegbreite des Schlitzrings (17 mm Steg)
    key_gap           = 0.25,   # Spaltmass Kappe/Platte je Seite
    key_proud         = 0.8,    # Kappenueberstand vor der Sichtflaeche
    key_lip           = 0.7,    # Rueckhaltekragen der Kappe je Seite
    key_lip_h         = 1.0,
    key_post_d        = 2.2,    # Fuehrungs-/Druckstoessel zur Leiterplatte
    # Radialposition der Stoessel. Begrenzt durch den Platz fuer den SMD-Taster
    # auf dem Ø52-Board: r + halbe Tasterlaenge + Randabstand <= 26 mm.
    key_post_r        = 23.2,
    # Stoesselwinkel: mit dem breiteren Steg sind 18 Grad zu weit aussen, die
    # Taster wuerden den Durchbruechen auf 12 und 6 Uhr im Weg stehen.
    key_post_ang      = 12.0,   # +/- Grad um die Diagonale
    key_post_len      = 4.0,    # Stoessellaenge unter der Kappe - an realen
                                # Abstand Platte->Top-PCB anpassen!

    # --- Kabelausgang Weihnachtsstern --------------------------------------
    # Entfaellt: der Stern wird jetzt gesteckt statt durchgefaedelt.
    star_exit         = False,
    star_exit_d       = 4.5,
    star_exit_y       = -24.0,

    # --- Klinkenbuchse Weihnachtsstern (UNTERER Steg, 6 Uhr) ---------------
    # Zielteil ist eine 2,5-mm-Buchse; Bauhoehe ueber der Top-Platine
    # hoechstens 10,5 mm, sonst stoesst sie an die Sichtflaeche.
    #
    # Der Steckplatz gehoert nach unten: Ein Kabel, das oben aus der Blende
    # kommt, haengt quer ueber der Anzeige. Der ToF muss dagegen nach oben -
    # er soll nach vorn und in die Fensteroeffnung schauen, nicht auf die
    # Fensterbank. Die Buchse steht damit allein im unteren Steg und liegt
    # mittig (x = 0); der obere traegt allein das ToF-Fenster.
    jack_hole         = True,
    jack_hole_d       = 5.6,    # Gewindebund einer 2,5-mm-Buchse
    jack_x            = 0.0,
    jack_y            = -22.5,

    # --- Sichtfenster ToF-Praesenzsensor (OBERER Steg, 12 Uhr) -------------
    # Der VL53L1X sitzt 10,5 mm hinter der Sichtflaeche, die Platte selbst ist
    # an dieser Stelle 5,5 mm dick. Der Sichtkegel von 27 Grad hat am hinteren
    # Ende des Kanals Ø2,4 und an der Sichtflaeche Ø5,0 - der Kanal weitet sich
    # deshalb nach VORN auf. Ø4,5 vorn beschneidet auf rund 24 Grad, das ist
    # gewollt: weniger Streulicht, weniger Uebersprechen.
    tof_window        = True,
    tof_front_d       = 4.5,
    tof_back_d        = 3.0,
    tof_x             = 5.0,
    tof_y             = 22.5,

    # --- USB-C Zugang (aus, Programmierung bei abgenommener Blende) --------
    usb_slot          = False,
    usb_slot_w        = 10.0,
    usb_slot_h        = 4.0,
    usb_slot_y        = 20.5,
)


def _ring_sketch(ri, ro, spoke_hw):
    """Ring von ri..ro, unterbrochen von 4 Stegen auf den Achsen.
    Ergibt vier Ringsegmente auf den Diagonalen."""
    Circle(ro)
    Circle(ri, mode=Mode.SUBTRACT)
    Rectangle(2 * (ro + 2), 2 * spoke_hw, mode=Mode.SUBTRACT)
    Rectangle(2 * spoke_hw, 2 * (ro + 2), mode=Mode.SUBTRACT)


def build_plate(p=PARAMS):
    with BuildPart() as fp:
        # -- Sichtplatte ----------------------------------------------------
        with BuildSketch(Plane.XY) as s:
            Rectangle(p["plate_size"], p["plate_size"])
            fillet(s.vertices(), p["plate_corner_r"])
        extrude(amount=p["plate_thickness"])

        # -- Tragring-Ohren -------------------------------------------------
        with BuildSketch(Plane.XY):
            Rectangle(p["ear_span"], p["ear_width"])
        extrude(amount=-p["ear_thickness"], mode=Mode.ADD)

        # -- Zentrierkragen (umlaufender Rahmen) ----------------------------
        with BuildSketch(Plane.XY.offset(-p["ear_thickness"])):
            Rectangle(p["boss_size"], p["boss_size"])
            Rectangle(p["boss_size"] - 2 * p["boss_wall"],
                      p["boss_size"] - 2 * p["boss_wall"], mode=Mode.SUBTRACT)
        extrude(amount=-p["boss_depth"], mode=Mode.ADD)

        back = p["ear_thickness"] + p["boss_depth"]

        # -- Freiraum fuers Displaymodul hinter der Platte ------------------
        with BuildSketch(Plane.XY):
            Circle(p["disp_module_d"] / 2 + p["disp_clearance"])
        extrude(amount=-back, mode=Mode.SUBTRACT)

        # -- Displayfenster --------------------------------------------------
        with BuildSketch(Plane.XY):
            Circle(p["disp_window_d"] / 2)
        extrude(amount=p["plate_thickness"], mode=Mode.SUBTRACT)

        # -- Sicheltasten-Schlitze -------------------------------------------
        with BuildSketch(Plane.XY):
            _ring_sketch(p["key_slot_ri"], p["key_slot_ro"], p["key_spoke_hw"])
        extrude(amount=p["plate_thickness"], mode=Mode.SUBTRACT)

        # -- Freidrehung fuer die Rueckhaltekragen der Kappen ----------------
        # Die Ohren liegen direkt hinter der Platte; im Ringbereich der
        # Kappenkragen wird ihre Oberseite flach ausgeraeumt (Resttiefe der
        # Ohren dort ~1,3 mm, bleiben tragfaehig).
        with BuildSketch(Plane.XY):
            Circle(p["key_slot_ro"] + p["key_lip"] + 0.6)
            Circle(p["key_slot_ri"] - p["key_lip"] - 0.6, mode=Mode.SUBTRACT)
        extrude(amount=-(p["key_lip_h"] + 0.2), mode=Mode.SUBTRACT)

        # -- Geraeteschrauben-Langloecher ------------------------------------
        with BuildSketch(Plane.XY):
            with Locations((p["screw_pitch"] / 2, 0), (-p["screw_pitch"] / 2, 0)):
                SlotOverall(p["screw_slot_len"] + p["screw_slot_w"],
                            p["screw_slot_w"], rotation=90)
        extrude(amount=-p["ear_thickness"], mode=Mode.SUBTRACT)

        # -- Kabelausgang Stern (durch den unteren Steg, volle Tiefe;
        #    kerbt bewusst den Zentrierkragen - Kabeldurchfuehrung) ----------
        if p["star_exit"]:
            with BuildSketch(Plane.XY.offset(p["plate_thickness"])):
                with Locations((0, p["star_exit_y"])):
                    Circle(p["star_exit_d"] / 2)
            extrude(amount=-(p["plate_thickness"] + back), mode=Mode.SUBTRACT)

        # -- Klinkenbuchse Stern (oberer Steg, volle Tiefe) -------------------
        if p["jack_hole"]:
            with BuildSketch(Plane.XY.offset(p["plate_thickness"])):
                with Locations((p["jack_x"], p["jack_y"])):
                    Circle(p["jack_hole_d"] / 2)
            extrude(amount=-(p["plate_thickness"] + back), mode=Mode.SUBTRACT)

        # -- ToF-Fenster: vorn zylindrisch, hinten konisch aufgeweitet -------
        if p["tof_window"]:
            with BuildSketch(Plane.XY.offset(p["plate_thickness"])):
                with Locations((p["tof_x"], p["tof_y"])):
                    Circle(p["tof_front_d"] / 2)
            with BuildSketch(Plane.XY.offset(-back)):
                with Locations((p["tof_x"], p["tof_y"])):
                    Circle(p["tof_back_d"] / 2)
            loft(mode=Mode.SUBTRACT)

        # -- optionaler USB-C-Schlitz ----------------------------------------
        if p["usb_slot"]:
            with BuildSketch(Plane.XY.offset(p["plate_thickness"])):
                with Locations((0, p["usb_slot_y"])):
                    SlotOverall(p["usb_slot_w"], p["usb_slot_h"])
            extrude(amount=-(p["plate_thickness"] + back), mode=Mode.SUBTRACT)

        # -- Sichtkanten brechen ---------------------------------------------
        try:
            top = fp.faces().sort_by(Axis.Z)[-1].edges()
            chamfer(top, p["plate_edge_cham"])
        except Exception:                       # pragma: no cover
            pass                                # Fase ist rein kosmetisch

    return fp.part


def build_caps(p=PARAMS):
    """Vier Tastenkappen in Einbaulage (gleiches Koordinatensystem wie Platte)."""
    body_ri = p["key_slot_ri"] + p["key_gap"]
    body_ro = p["key_slot_ro"] - p["key_gap"]
    body_hw = p["key_spoke_hw"] + 2 * p["key_gap"]     # schmalere Boegen
    lip_ri  = p["key_slot_ri"] - p["key_lip"]
    lip_ro  = p["key_slot_ro"] + p["key_lip"]
    lip_hw  = p["key_spoke_hw"] - p["key_lip"]         # breitere Boegen
    top_z   = p["plate_thickness"] + p["key_proud"]

    with BuildPart() as caps:
        # Koerper: fuellt den Schlitz und steht vorn ueber
        with BuildSketch(Plane.XY):
            _ring_sketch(body_ri, body_ro, body_hw)
        extrude(amount=top_z)

        # Rueckhaltekragen hinter der Platte
        with BuildSketch(Plane.XY):
            _ring_sketch(lip_ri, lip_ro, lip_hw)
        extrude(amount=-p["key_lip_h"], mode=Mode.ADD)

        # Druckstoessel Richtung Leiterplatte, zwei je Kappe
        pts = []
        for q in range(4):
            for da in (-p["key_post_ang"], p["key_post_ang"]):
                a = math.radians(45 + 90 * q + da)
                pts.append((p["key_post_r"] * math.cos(a),
                            p["key_post_r"] * math.sin(a)))
        with BuildSketch(Plane.XY.offset(-p["key_lip_h"])):
            with Locations(*pts):
                Circle(p["key_post_d"] / 2)
        extrude(amount=-p["key_post_len"], mode=Mode.ADD)

        # Bedienkante brechen
        try:
            top = caps.faces().sort_by(Axis.Z)[-1].edges()
            chamfer(top, 0.4)
        except Exception:                       # pragma: no cover
            pass

    return caps.part


# ---------------------------------------------------------------------------
# SELBSTTESTS
# ---------------------------------------------------------------------------

def check_plate(part, p=PARAMS):
    errs = []
    back = p["ear_thickness"] + p["boss_depth"]
    full = p["plate_thickness"] + back

    # --- Zwangsbedingungen vor der Geometrie ------------------------------
    # 1. Rueckhaltekragen der Kappen darf das Displaymodul nicht beruehren
    lip_ri = p["key_slot_ri"] - p["key_lip"]
    need = p["disp_module_d"] / 2 + p["disp_clearance"]
    if lip_ri < need:
        errs.append(
            "Kappenkragen kollidiert mit Displaymodul: Kragen-Innenradius "
            f"{lip_ri:.2f} mm < benoetigt {need:.2f} mm "
            f"(key_slot_ri mindestens {need + p['key_lip']:.2f} mm)")

    # 2. Sichtoeffnung muss die aktive Flaeche freigeben, aber im Modul bleiben
    if p["disp_window_d"] < p["disp_active_d"]:
        errs.append(f"Fenster Ø{p['disp_window_d']:.1f} kleiner als aktive "
                    f"Flaeche Ø{p['disp_active_d']:.1f}")
    if p["disp_window_d"] > p["disp_module_d"]:
        errs.append(f"Fenster Ø{p['disp_window_d']:.1f} groesser als Modul "
                    f"Ø{p['disp_module_d']:.1f} - Modulrand waere sichtbar")

    # 3. Blendring zwischen Fenster und Tastenschlitz mindestens 1,2 mm
    bezel = p["key_slot_ri"] - p["disp_window_d"] / 2
    if bezel < 1.2:
        errs.append(f"Blendring nur {bezel:.2f} mm breit, mindestens 1,2 mm noetig")

    # 4. Restwand zwischen Tastenschlitz und Plattenkante (engste Stelle liegt
    #    dort, wo der Schlitz auf den Steg trifft)
    th = math.asin(min(1.0, p["key_spoke_hw"] / p["key_slot_ro"]))
    edge = (p["plate_size"] / 2) / math.cos(th)
    wall = edge - p["key_slot_ro"]
    if wall < 1.2:
        errs.append(f"Restwand Schlitz/Plattenkante nur {wall:.2f} mm, "
                    "mindestens 1,2 mm noetig")

    # 5. Stoessel muss innerhalb der Sichel liegen
    if not (p["key_slot_ri"] + p["key_post_d"] / 2 < p["key_post_r"]
            < p["key_slot_ro"] - p["key_post_d"] / 2):
        errs.append(f"Stoesselradius {p['key_post_r']:.2f} liegt nicht "
                    f"vollstaendig in der Sichel "
                    f"({p['key_slot_ri']:.1f}..{p['key_slot_ro']:.1f})")

    if len(part.solids()) != 1:
        errs.append(f"Platte besteht aus {len(part.solids())} Solids, erwartet 1")

    bb = part.bounding_box()
    for name, got, want in (("Breite", bb.size.X, p["ear_span"]),
                            ("Hoehe", bb.size.Y, p["plate_size"]),
                            ("Tiefe", bb.size.Z, full)):
        if abs(got - want) > 0.01:
            errs.append(f"{name}: {got:.2f} mm, erwartet {want:.2f} mm")

    def clear(probe, label):
        v = (part & probe).volume
        if v > 1e-6:
            errs.append(f"{label}: {v:.1f} mm3 Material im Freiraum")

    def solid(probe, label):
        if (part & probe).volume < 1e-6:
            errs.append(f"{label}: Material fehlt")

    zc = (p["plate_thickness"] - back) / 2

    # Fenster durchgaengig frei
    clear(Pos(0, 0, zc) * Cylinder(p["disp_window_d"] / 2, full), "Displayfenster")

    # Vier Sichel-Schlitze auf den Diagonalen durchgaengig frei
    rmid = (p["key_slot_ri"] + p["key_slot_ro"]) / 2
    for q in range(4):
        a = math.radians(45 + 90 * q)
        clear(Pos(rmid * math.cos(a), rmid * math.sin(a), zc)
              * Cylinder(1.6, full), f"Sichelschlitz Q{q + 1}")

    # Stege auf den Achsen tragen Material. Probe 8 Grad neben der Achse.
    # 90 und 270 Grad sind durchbrochen und werden unten einzeln geprueft.
    for ang in (0, 180):
        a = math.radians(ang + 8)
        solid(Pos(rmid * math.cos(a), rmid * math.sin(a),
                  p["plate_thickness"] / 2)
              * Cylinder(0.35, p["plate_thickness"]), f"Steg {ang} Grad")

    # Die beiden senkrechten Stege sind durchbrochen: oben das ToF-Fenster,
    # unten die Klinkenbuchse. Geprueft werden die verbleibenden
    # Materialbahnen - jede muss mindestens 1,2 mm breit und real vorhanden
    # sein, sonst haengt der Blendring nur noch an drei Stegen. Der Test
    # sortiert die Durchbrueche selbst nach Steg; wandert einer, wandert die
    # Pruefung mit.
    spokes = {90: [], 270: []}
    if p["jack_hole"]:
        spokes[90 if p["jack_y"] > 0 else 270].append(
            (p["jack_x"], p["jack_hole_d"] / 2, "Klinke"))
    if p["tof_window"]:
        spokes[90 if p["tof_y"] > 0 else 270].append(
            (p["tof_x"], max(p["tof_front_d"], p["tof_back_d"]) / 2, "ToF"))

    for ang, holes in spokes.items():
        ymid = rmid if ang == 90 else -rmid
        if not holes:
            a = math.radians(ang + 8)
            solid(Pos(rmid * math.cos(a), rmid * math.sin(a),
                      p["plate_thickness"] / 2)
                  * Cylinder(0.35, p["plate_thickness"]),
                  f"Steg {ang} Grad (ohne Durchbruch)")
            continue
        holes.sort()
        bands, lo = [], -p["key_spoke_hw"]
        for cx, r, _ in holes:
            bands.append((lo, cx - r))
            lo = cx + r
        bands.append((lo, p["key_spoke_hw"]))
        for i, (x0, x1) in enumerate(bands, start=1):
            w = x1 - x0
            if w < 1.2:
                errs.append(f"Steg {ang} Grad: Materialbahn {i} nur "
                            f"{w:.2f} mm breit "
                            f"({', '.join(h[2] for h in holes)})")
            else:
                solid(Pos((x0 + x1) / 2, ymid, p["plate_thickness"] / 2)
                      * Cylinder(0.35, p["plate_thickness"]),
                      f"Steg {ang} Grad, Bahn {i}")

    # Blendring zwischen Fenster und Schlitz intakt
    rb = (p["disp_window_d"] / 2 + p["key_slot_ri"]) / 2
    solid(Pos(rb * math.cos(math.radians(45)), rb * math.sin(math.radians(45)),
              p["plate_thickness"] / 2)
          * Cylinder(0.35, p["plate_thickness"]), "Blendring")

    # Stern-Kabelausgang frei
    if p["star_exit"]:
        clear(Pos(0, p["star_exit_y"], zc)
              * Cylinder(p["star_exit_d"] / 2, full), "Kabelausgang Stern")

    # Durchbrueche in den senkrechten Stegen: frei, und sie duerfen den Steg
    # nicht verlassen - sonst laegen sie im Verfahrweg der Sicheltasten.
    if p["jack_hole"]:
        clear(Pos(p["jack_x"], p["jack_y"], zc)
              * Cylinder(p["jack_hole_d"] / 2, full), "Klinkenbuchse Stern")
    if p["tof_window"]:
        # Der Kanal ist konisch; garantiert frei ist der engste Querschnitt.
        clear(Pos(p["tof_x"], p["tof_y"], zc)
              * Cylinder(min(p["tof_front_d"], p["tof_back_d"]) / 2, full),
              "ToF-Fenster")

    # Schraubenloecher frei
    for sx in (p["screw_pitch"] / 2, -p["screw_pitch"] / 2):
        clear(Pos(sx, 0, -p["ear_thickness"] / 2)
              * Cylinder(p["screw_slot_w"] / 2, p["ear_thickness"]),
              f"Schraubenloch x={sx:+.0f}")

    return errs


def check_caps(caps_part, plate_part, p=PARAMS):
    errs = []
    if len(caps_part.solids()) != 4:
        errs.append(f"{len(caps_part.solids())} Kappen-Solids, erwartet 4")

    # Einbaulage: Kappen duerfen die Platte nirgends beruehren
    v = (caps_part & plate_part).volume
    if v > 1e-6:
        errs.append(f"Kappen kollidieren mit Platte: {v:.2f} mm3")

    bb = caps_part.bounding_box()
    want_top = p["plate_thickness"] + p["key_proud"]
    want_bot = -(p["key_lip_h"] + p["key_post_len"])
    if abs(bb.max.Z - want_top) > 0.01:
        errs.append(f"Kappenoberkante {bb.max.Z:.2f}, erwartet {want_top:.2f}")
    if abs(bb.min.Z - want_bot) > 0.01:
        errs.append(f"Stoesselende {bb.min.Z:.2f}, erwartet {want_bot:.2f}")

    return errs


def main():
    out = Path(__file__).parent / "export"
    out.mkdir(exist_ok=True)

    plate = build_plate()
    caps = build_caps()

    errs = check_plate(plate) + check_caps(caps, plate)
    for e in errs:
        print(f"  FEHLER: {e}")
    print(f"Selbsttest   : {'BESTANDEN' if not errs else str(len(errs)) + ' FEHLER'}")

    export_step(plate, str(out / "frontplate.step"))
    export_stl(plate, str(out / "frontplate.stl"))
    export_step(caps, str(out / "frontplate_caps.step"))
    export_stl(caps, str(out / "frontplate_caps.stl"))
    export_stl(Compound([plate, caps]), str(out / "frontplate_assembly.stl"))

    bb = plate.bounding_box()
    print(f"Platte       : {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
          f"{plate.volume / 1000:.2f} cm3")
    print(f"Kappen       : {len(caps.solids())} Stueck, {caps.volume / 1000:.2f} cm3")

    p = PARAMS
    print(f"Fenster      : Ø{p['disp_window_d']:.1f} mm  "
          f"(Sicheln r {p['key_slot_ri']:.1f}..{p['key_slot_ro']:.1f})")
    print("Tasterpos.   : r=%.1f mm, Winkel " % p["key_post_r"] +
          ", ".join("%d/%d" % (45 + 90 * q - p["key_post_ang"],
                               45 + 90 * q + p["key_post_ang"])
                    for q in range(4)) + " Grad")
    print(f"Export       : {out}")

    return 1 if errs else 0


if __name__ == "__main__":
    raise SystemExit(main())
