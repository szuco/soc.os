#!/usr/bin/env python3
"""
Erzeugt die Layouts der drei SwitchStack-Boards aus den Schaltplan-Generatoren.

    python3 tools/gen_layouts.py [bottom|mid|top]

Was dieses Skript leistet - und was nicht:
  * Board-Mechanik (Outline Ø52, Bohrbild, Frontmarkierung, Antennen-Keepout)
  * alle Footprints geladen, Referenz/Wert gesetzt, JEDES Pad mit dem Netz aus
    dem Schaltplan-Generator verbunden
  * mechanisch gebundene Teile exakt platziert (Stackverbinder deckungsgleich
    auf allen Boards, Taster unter den Druckkreuzen der Zentralscheibe,
    ESP32-Antenne an der Frontkante, ...)
  * uebrige Teile kollisionsfrei per Spiralsuche platziert, Hinweisposition =
    das bereits platzierte Bauteil mit den meisten gemeinsamen Netzen
  * PGND-Flaechen auf beiden Lagen, gefuellt
  * DRC mit kicad-cli; Platzierungsfehler (Courtyard/Rand) gelten als Fehler,
    unverbundene Netze sind erwartet

  NICHT enthalten: das Routing der Signale. Die Boards sind route-fertig
  (Ratsnest vollstaendig), aber Leiterbahnen sind Handarbeit in KiCad.
"""

import json
import math
import re as _re2
import os
import subprocess
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_bottom_sch, gen_mid_sch, gen_top_sch                # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def _fpdir():
    """Footprintbibliothek finden - Linux, macOS oder per KICAD_FOOTPRINT_DIR."""
    for d in (os.environ.get("KICAD_FOOTPRINT_DIR"),
              "/usr/share/kicad/footprints",
              "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"):
        if d and os.path.isdir(d):
            return d
    return "/usr/share/kicad/footprints"


FPDIR = _fpdir()

BOARD_R = 26.0
EDGE_CLEAR = 0.5
HOLE_R = 21.5

# Das TOP-Board ist als einziges NICHT rund. Grund: Die Zentralscheibe
# Busch-Jaeger 6435-914 gibt ihren Tastendruck ueber vier Kreuze an den ECKEN
# weiter, gemessen bei (+/-18,0 / +/-20,0) - das ist r = 26,91 und liegt damit
# ausserhalb einer Oe52-Platine. Ein Kreis hat keine Ecken; das BJ-System ist um
# einen quadratischen Einsatz von 54 x 54 gebaut. Das Top-Board wird deshalb ein
# abgerundetes Quadrat und sitzt VOR der Dose, so wie der BJ-Einsatz auch.
# 47,0 und nicht mehr, weil der Schnapprand des Adapters HINTER der Platine
# liegt und sie zugleich traegt: Die Scheibe rastet auf 50,0, der Rand ist
# aussen 49,8, und bei 1,4 mm Wand bleiben innen genau 47,0. Nach unten
# begrenzen die Taster - ihre Ausdehnung reicht bis 22,2, mit 0,5 mm
# Randabstand braucht es mindestens 45,4. Herleitung der Tiefenkette in
# mechanical/adapter.py und docs/04-mechanical.md Abschnitt 1e.
TOP_SQ = 47.0          # Kantenlaenge - siehe Tiefenkette unten
TOP_CR = 4.0           # Eckradius
# Bohrbild v2: ZWEI Bohrungen bei 0/180 Grad. Die alten Winkel 120/240
# kollidierten mit den Sicheltasten-Stoesseln (117/243 Grad, nur ~2 mm
# daneben), und bei r21,5 blockieren Stackverbinder (um 45/135/225/315),
# ESP32-Antenne (um 90) und Leistungsstecker (um 270) alle uebrigen
# Kandidaten. Verdrehsicherung uebernehmen die beiden Stackverbinder.
HOLES = [(HOLE_R, 0.0), (-HOLE_R, 0.0)]

# Footprint-Pads, deren Nummern nicht den Symbolpins entsprechen.
# PowerPAK SO-8: Pads 1-3 = Source, 4 = Gate, 5 = Drain;
# Symbol Q_NMOS_GDS: 1 = G, 2 = D, 3 = S.
PAD_MAP = {
    "Package_SO:PowerPAK_SO-8_Single": {"1": "3", "2": "3", "3": "3",
                                        "4": "1", "5": "2"},
}
# Q_PMOS_GSD: 1 = G, 2 = S, 3 = D -> PowerPAK 1-3 = S, 4 = G, 5 = D
PAD_MAP_REF = {
    "bottom_power_motor": {
        "Q1": {"1": "2", "2": "2", "3": "2", "4": "1", "5": "3"},
    },
}

# Stackverbinder - MUESSEN auf allen drei Boards identisch liegen
# x = +/-14,9: weiter innen als urspruenglich geplant, weil die Buchsen
# sonst mit den frueheren Sicheltastern des Top-Boards ueberlappten.
STACK_POS = {"J2": (-14.2, -2.0, 0), "J3": (14.2, -2.0, 0)}


def mm(v):
    return pcbnew.FromMM(float(v))


def load_fp(fpid):
    lib, name = fpid.split(":")
    fp = pcbnew.FootprintLoad(os.path.join(FPDIR, lib + ".pretty"), name)
    if fp is None:
        raise RuntimeError("Footprint %s nicht ladbar" % fpid)
    return fp


def fp_bbox_mm(fp):
    """BBox aus Courtyard und Pads - die rohe BoundingBox enthaelt bei
    manchen Bibliotheks-Footprints (ESP32-Modul!) riesige Zeichnungslagen."""
    lo_x = lo_y = float("inf")
    hi_x = hi_y = float("-inf")

    def take(b):
        nonlocal lo_x, lo_y, hi_x, hi_y
        lo_x = min(lo_x, pcbnew.ToMM(b.GetLeft()))
        lo_y = min(lo_y, pcbnew.ToMM(b.GetTop()))
        hi_x = max(hi_x, pcbnew.ToMM(b.GetRight()))
        hi_y = max(hi_y, pcbnew.ToMM(b.GetBottom()))

    for item in fp.GraphicalItems():
        if item.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
            take(item.GetBoundingBox())
    for pad in fp.Pads():
        take(pad.GetBoundingBox())
    if lo_x == float("inf"):
        take(fp.GetBoundingBox(False, False))
    return (lo_x, lo_y, hi_x, hi_y)


def pads_bbox_mm(fp):
    lo_x = lo_y = float("inf")
    hi_x = hi_y = float("-inf")
    for pad in fp.Pads():
        b = pad.GetBoundingBox()
        lo_x = min(lo_x, pcbnew.ToMM(b.GetLeft()))
        lo_y = min(lo_y, pcbnew.ToMM(b.GetTop()))
        hi_x = max(hi_x, pcbnew.ToMM(b.GetRight()))
        hi_y = max(hi_y, pcbnew.ToMM(b.GetBottom()))
    return (lo_x, lo_y, hi_x, hi_y)


def inside_outline(x, y, square, margin=0.0):
    """Liegt der Punkt in der Platinenkontur, mit margin Abstand zum Rand?"""
    if square:
        h = TOP_SQ / 2.0 - margin
        ax, ay = abs(x), abs(y)
        if ax > h or ay > h:
            return False
        dx, dy = ax - (h - TOP_CR), ay - (h - TOP_CR)
        if dx > 0 and dy > 0:
            return math.hypot(dx, dy) <= TOP_CR
        return True
    return math.hypot(x, y) <= BOARD_R - margin


class Occupancy:
    """Belegtflaechen je Seite; Loecher und THT blockieren beide Seiten."""

    def __init__(self, blocks=None, square=False):
        self.rects = {"F": [], "B": []}
        self.circles = [(x, y, 3.2) for x, y in HOLES]
        self.square = square
        for r in (blocks or []):
            self.block(*r)

    def block(self, x1, y1, x2, y2, side=None):
        for s in ([side] if side else ["F", "B"]):
            self.rects[s].append((x1, y1, x2, y2))

    def free(self, x1, y1, x2, y2, side, margin=0.3, check_edge=True):
        # innerhalb der runden Platine? (AABB - fuer rotierte Teile am Rand
        # zu pessimistisch, deshalb bei Fixplatzierungen abschaltbar; dort
        # urteilt die echte DRC)
        if check_edge:
            for cx, cy in ((x1, y1), (x2, y1), (x1, y2), (x2, y2)):
                if not inside_outline(cx, cy, self.square, EDGE_CLEAR + 0.2):
                    return False
        for (a1, b1, a2, b2) in self.rects[side]:
            if not (x2 + margin < a1 or a2 + margin < x1
                    or y2 + margin < b1 or b2 + margin < y1):
                return False
        for (cx, cy, r) in self.circles:
            nx = min(max(cx, x1), x2)
            ny = min(max(cy, y1), y2)
            if math.hypot(cx - nx, cy - ny) < r + margin - 0.2:
                return False
        return True


class BoardBuilder:
    def __init__(self, name, schematic, antenna=False, square=False):
        self.square = square
        self.name = name
        self.sch = schematic
        self.board = pcbnew.CreateEmptyBoard()
        # VIER LAGEN, seit 17.08.2026.
        #
        # Zweilagig kam der Autorouter nicht durch: Auf Top blieben 14
        # Signalnetze offen, auf Mid 18, auf Bottom 43, und Freerouting
        # meldete nach 180 wirkungslosen Passes selbst, es koenne "not improve
        # the result much further". Nicht die Masseflaechen waren schuld - die
        # stehen gar nicht im DSN, der Router sieht sie nie -, sondern schlicht
        # der Platz: zwei Lagen, ein dicht bestuecktes Rund von 52 mm, und die
        # Taster in den vier Ecken, deren Netze quer ueber das Board muessen.
        #
        # Vier Lagen verdoppeln den Routingraum. Die Masseflaechen liegen auf
        # allen vier Lagen und werden wie bisher nach dem Routing gefuellt -
        # KEINE durchgehende Massefl. auf einer eigenen Lage. Das waere fuer
        # die EMV besser, kostet aber eine der vier Routinglagen; erst
        # Vollstaendigkeit, EMV danach (docs/06, Punkt 60).
        self.board.SetCopperLayerCount(4)
        ds = self.board.GetDesignSettings()
        ds.SetBoardThickness(mm(1.0))
        ds.m_CopperEdgeClearance = mm(EDGE_CLEAR)
        ds.m_MinThroughDrill = mm(0.2)
        try:
            ds.m_NetSettings.m_DefaultNetClass.SetClearance(mm(0.15))
        except Exception:
            pass
        self._outline()
        self._holes()
        self._marker()
        if antenna:
            self._antenna_keepout()
        self._nets()
        self.pin2net = {}
        for net, pins in self.sch.nets.items():
            for p in pins:
                self.pin2net[p] = net
        self.fps = {}
        self.loose = set()
        self.errors = []
        self.occ = Occupancy(square=square)
        self.antenna = antenna

    # -- Mechanik ---------------------------------------------------------

    def _outline(self):
        if not self.square:
            c = pcbnew.PCB_SHAPE(self.board)
            c.SetShape(pcbnew.SHAPE_T_CIRCLE)
            c.SetLayer(pcbnew.Edge_Cuts)
            c.SetCenter(pcbnew.VECTOR2I(0, 0))
            c.SetEnd(pcbnew.VECTOR2I(mm(BOARD_R), 0))
            c.SetWidth(mm(0.1))
            self.board.Add(c)
            return
        # Abgerundetes Quadrat: vier Geraden, vier Eckboegen
        h, cr = TOP_SQ / 2.0, TOP_CR
        k = 0.7071067811865476
        for a, b in (((-(h - cr), -h), ((h - cr), -h)),
                     (((h - cr), h), (-(h - cr), h)),
                     ((-h, (h - cr)), (-h, -(h - cr))),
                     ((h, -(h - cr)), (h, (h - cr)))):
            seg = pcbnew.PCB_SHAPE(self.board)
            seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
            seg.SetLayer(pcbnew.Edge_Cuts)
            seg.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1])))
            seg.SetEnd(pcbnew.VECTOR2I(mm(b[0]), mm(b[1])))
            seg.SetWidth(mm(0.1))
            self.board.Add(seg)
        for sx, sy in ((1, -1), (1, 1), (-1, 1), (-1, -1)):
            cx, cy = sx * (h - cr), sy * (h - cr)
            p1 = (sx * (h - cr), sy * h)
            p2 = (sx * h, sy * (h - cr))
            pm = (cx + sx * k * cr, cy + sy * k * cr)
            arc = pcbnew.PCB_SHAPE(self.board)
            arc.SetShape(pcbnew.SHAPE_T_ARC)
            arc.SetLayer(pcbnew.Edge_Cuts)
            arc.SetArcGeometry(pcbnew.VECTOR2I(mm(p1[0]), mm(p1[1])),
                               pcbnew.VECTOR2I(mm(pm[0]), mm(pm[1])),
                               pcbnew.VECTOR2I(mm(p2[0]), mm(p2[1])))
            arc.SetWidth(mm(0.1))
            self.board.Add(arc)

    def _holes(self):
        for i, (x, y) in enumerate(HOLES):
            fp = load_fp("MountingHole:MountingHole_2.7mm_M2.5")
            fp.SetReference("H%d" % (i + 1))
            fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
            self.board.Add(fp)

    def _marker(self):
        r = (TOP_SQ / 2.0 if self.square else BOARD_R) - 2.0
        pts = [((0, -r), (-1.6, -(r - 2.2))),
               ((-1.6, -(r - 2.2)), (1.6, -(r - 2.2))),
               ((1.6, -(r - 2.2)), (0, -r))]
        for a, b in pts:
            seg = pcbnew.PCB_SHAPE(self.board)
            seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
            seg.SetLayer(pcbnew.F_SilkS)
            seg.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1])))
            seg.SetEnd(pcbnew.VECTOR2I(mm(b[0]), mm(b[1])))
            seg.SetWidth(mm(0.15))
            self.board.Add(seg)

    def _antenna_keepout(self):
        zone = pcbnew.ZONE(self.board)
        zone.SetIsRuleArea(True)
        # KiCad 10: SetDoNotAllowCopperPour heisst jetzt SetDoNotAllowZoneFills
        if hasattr(zone, "SetDoNotAllowCopperPour"):
            zone.SetDoNotAllowCopperPour(True)
        else:
            zone.SetDoNotAllowZoneFills(True)
        zone.SetDoNotAllowTracks(True)
        zone.SetDoNotAllowVias(True)
        zone.SetDoNotAllowPads(False)
        # Das ESP32-Modul selbst DARF hier liegen - nur Kupfer ist verboten.
        zone.SetDoNotAllowFootprints(False)
        lset = pcbnew.LSET()
        for lay in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
            lset.addLayer(lay)
        zone.SetLayerSet(lset)
        # Nur der echte Antennenabschnitt: Das WROOM-Modul (25,5 mm lang,
        # Mitte y=-16,27) ragt 3 mm ueber die Boardkante - die Antenne
        # (oberste 6,5 mm des Moduls) beginnt bei y=-22,5. Die fruehere
        # Flaeche bis y=-15 hat 9 Signalpads des Moduls eingeschlossen
        # und sie damit unroutbar gemacht (Freerouting-Plateau, 11 offen).
        o = zone.Outline()
        o.NewOutline()
        for x, y in ((-9, -26.2), (9, -26.2), (9, -22.6), (-9, -22.6)):
            o.Append(mm(x), mm(y))
        zone.SetZoneName("ESP32_ANTENNA_KEEPOUT")
        self.board.Add(zone)

    # -- Netze und Footprints --------------------------------------------

    def _nets(self):
        self.nets = {}
        for name in sorted(self.sch.nets):
            n = pcbnew.NETINFO_ITEM(self.board, name)
            self.board.Add(n)
            self.nets[name] = n

    def add_component(self, comp):
        fp = load_fp(comp.footprint)
        fp.SetReference(comp.ref)
        fp.SetValue(comp.value)
        padmap = PAD_MAP_REF.get(self.name, {}).get(
            comp.ref, PAD_MAP.get(comp.footprint, {}))
        for pad in fp.Pads():
            num = pad.GetNumber()
            if not num:
                continue
            pin = padmap.get(num, num)
            net = self.pin2net.get((comp.ref, pin))
            if net:
                pad.SetNet(self.nets[net])
        self.board.Add(fp)
        self.fps[comp.ref] = fp
        return fp

    def is_tht(self, fp):
        for pad in fp.Pads():
            if pad.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH,
                                      pcbnew.PAD_ATTRIB_NPTH):
                return True
        return False

    def place(self, ref, x, y, rot=0, side="F", register=True,
              pads_only=False):
        fp = self.fps[ref]
        on_back = fp.GetLayer() == pcbnew.B_Cu
        if (side == "B") != on_back:
            fp.Flip(fp.GetPosition(), False)
        fp.SetOrientationDegrees(rot)
        fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        # Position so korrigieren, dass die BBOX-MITTE auf (x, y) liegt
        bbox = pads_bbox_mm if pads_only else fp_bbox_mm
        x1, y1, x2, y2 = bbox(fp)
        dx, dy = x - (x1 + x2) / 2, y - (y1 + y2) / 2
        fp.SetPosition(pcbnew.VECTOR2I(mm(x + dx), mm(y + dy)))
        if register:
            x1, y1, x2, y2 = bbox(fp)
            self.occ.block(x1, y1, x2, y2,
                           None if self.is_tht(fp) else side)
        return fp

    def place_fixed(self, ref, x, y, rot=0, side="F"):
        """Platziert und PRUEFT gegen alles bisher Platzierte."""
        fp = self.fps[ref]
        self.place(ref, x, y, rot, side, register=False,
                   pads_only=ref in self.loose)
        x1, y1, x2, y2 = (pads_bbox_mm(fp) if ref in self.loose
                          else fp_bbox_mm(fp))
        sides = ["F", "B"] if self.is_tht(fp) else [side]
        for sd in sides:
            if not self.occ.free(x1, y1, x2, y2, sd, check_edge=False):
                self.errors.append(
                    "Fixplatzierung %s kollidiert (Seite %s, bbox %.1f,%.1f..%.1f,%.1f)"
                    % (ref, sd, x1, y1, x2, y2))
        self.occ.block(x1, y1, x2, y2, None if self.is_tht(fp) else side)

    def place_auto(self, ref, hx, hy, sides=("F", "B")):
        """Spiralsuche um die Hinweisposition, Rotation 0 oder 90."""
        fp = self.fps[ref]
        for radius in [x * 0.5 for x in range(0, 110)]:
            steps = max(1, int(radius * 8))
            for k in range(steps):
                a = 2 * math.pi * k / steps
                x = hx + radius * math.cos(a)
                y = hy + radius * math.sin(a)
                for side in sides:
                    for rot in (0, 90):
                        self.place(ref, x, y, rot, side, register=False)
                        x1, y1, x2, y2 = fp_bbox_mm(fp)
                        s = None if self.is_tht(fp) else side
                        ok = all(self.occ.free(x1, y1, x2, y2, sd)
                                 for sd in (["F", "B"] if s is None else [s]))
                        if ok:
                            self.occ.block(x1, y1, x2, y2, s)
                            return
        raise RuntimeError("kein Platz fuer %s" % ref)

    def hint_from_nets(self, comp):
        """Position des bereits platzierten Bauteils mit den meisten
        gemeinsamen Netzen (Versorgungsnetze zaehlen nicht)."""
        boring = {"PGND", "AGND", "3V3_SYS", "5V_SYS", "24V_PROT", "12V_GATE"}
        mynets = {self.pin2net.get((comp.ref, p))
                  for p in [pad.GetNumber() for pad in self.fps[comp.ref].Pads()]}
        mynets = {n for n in mynets if n and n not in boring}
        best, score = (0.0, 0.0), -1
        for ref, fp in self.fps.items():
            if ref == comp.ref or ref not in self.placed:
                continue
            nets = {pad.GetNetname() for pad in fp.Pads()}
            sc = len(mynets & nets)
            if sc > score:
                score = sc
                p = fp.GetPosition()
                best = (pcbnew.ToMM(p.x), pcbnew.ToMM(p.y))
        return best

    # -- Flaechen ---------------------------------------------------------

    def gnd_zones(self, net="PGND"):
        for layer in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
            zone = pcbnew.ZONE(self.board)
            zone.SetLayer(layer)
            zone.SetNet(self.nets[net])
            o = zone.Outline()
            o.NewOutline()
            if self.square:
                # Das Top-Board ist ein abgerundetes Quadrat. Ein Kreis als
                # Zonenumriss haette die vier Ecken ausgespart - und genau
                # dort sitzen die Taster.
                h = TOP_SQ / 2.0 - 0.6
                r = max(TOP_CR - 0.6, 0.1)
                for cx, cy, a0 in ((h - r, h - r, 0.0), (-(h - r), h - r, 90.0),
                                   (-(h - r), -(h - r), 180.0), (h - r, -(h - r), 270.0)):
                    for k in range(7):
                        a = math.radians(a0 + 90.0 * k / 6.0)
                        o.Append(mm(cx + r * math.cos(a)), mm(cy + r * math.sin(a)))
            else:
                n = 48
                for k in range(n):
                    a = 2 * math.pi * k / n
                    o.Append(mm((BOARD_R - 0.6) * math.cos(a)),
                             mm((BOARD_R - 0.6) * math.sin(a)))
            zone.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
            zone.SetLocalClearance(mm(0.3))
            zone.SetMinThickness(mm(0.25))
            self.board.Add(zone)
        # Zonen sofort fuellen.
        #
        # Hier stand jahrelang, ZONE_FILLER.Fill() stuerze in der headless
        # pcbnew-API ab (Segfault, 7.0.11, isoliert getestet) - die Zonen
        # blieben deshalb leer, und KiCad sollte sie beim Oeffnen mit "B"
        # fuellen. Das ist nie passiert: Am 17.08.2026 hatten Mid und Top
        # NULL filled_polygon-Bloecke, und allein daraus stammten 76 der 209
        # gemeldeten offenen Verbindungen.
        #
        # Mit KiCad 10 laeuft der Filler headless durch. Also fuellen wir
        # selbst - und zwar VOR dem DSN-Export, denn was der Autorouter als
        # gefuellte Flaeche sieht, muss er nicht als Netz routen.
        filler = pcbnew.ZONE_FILLER(self.board)
        filler.Fill(self.board.Zones())

    def save(self, path):
        pcbnew.SaveBoard(path, self.board)


def build_board(name, module, fixed, auto_sides=("F", "B"),
                antenna=False, block_f=None, loose=(), square=False):
    sch = module.build()
    bb = BoardBuilder(name, sch, antenna=antenna, square=square)
    bb.loose = set(loose)
    for c in sch.components:
        bb.add_component(c)
    bb.placed = set()
    # 1. Stackverbinder - identisch auf allen Boards
    for ref, (x, y, rot) in STACK_POS.items():
        bb.place_fixed(ref, x, y, rot, "F")
        bb.placed.add(ref)
    # 2. mechanisch gebundene Teile, mit Kollisionspruefung
    for ref, (x, y, rot, side) in fixed.items():
        if rot == "AUTO_TANGENTIAL":
            # Rotation waehlen, bei der die Pads dem Rand am fernsten bleiben
            best, best_r = 0, 1e9
            for cand in range(0, 360, 90):
                bb.place(ref, x, y, cand, side, register=False)
                rmax = max(math.hypot(pcbnew.ToMM(p_.GetPosition().x),
                                      pcbnew.ToMM(p_.GetPosition().y))
                           for p_ in bb.fps[ref].Pads())
                if rmax < best_r:
                    best, best_r = cand, rmax
            rot = best
        bb.place_fixed(ref, x, y, rot, side)
        bb.placed.add(ref)
    # Antennenbereich fuer die Autoplatzierung sperren (das ESP-Modul
    # selbst wurde oben fix platziert und darf dort liegen)
    if antenna:
        bb.occ.block(-9.5, -26.5, 9.5, -22.1)
    if block_f:
        bb.occ.block(*block_f, side="F")
    # 3. Rest: grosse zuerst, Hinweis = bester Netznachbar
    rest = [c for c in sch.components if c.ref not in bb.placed]
    def area(c):
        x1, y1, x2, y2 = fp_bbox_mm(bb.fps[c.ref])
        return (x2 - x1) * (y2 - y1)
    for c in sorted(rest, key=area, reverse=True):
        hx, hy = bb.hint_from_nets(c)
        bb.place_auto(c.ref, hx, hy, auto_sides)
        bb.placed.add(c.ref)
    bb.gnd_zones()
    out = os.path.join(ROOT, "hardware", name, name + ".kicad_pcb")
    bb.save(out)
    return out, len(sch.components), bb.errors


def run_drc(path):
    """DRC ueber die pcbnew-API - kicad-cli kann das erst ab KiCad 8."""
    import re as _re
    rpt = "/tmp/drc_%s.rpt" % os.path.basename(path).split(".")[0]
    # WriteDRCReport braucht ab KiCad 10 eine initialisierte wxApp und bricht
    # im blanken Python ab. kicad-cli macht dasselbe aus einem eigenen Prozess
    # und ist versionsstabil.
    r = subprocess.run(["kicad-cli", "pcb", "drc", "--format", "report",
                        "--exit-code-violations",
                        "-o", rpt, path],
                       capture_output=True, text=True)
    if not os.path.exists(rpt):
        return {"violations": {}, "unconnected": 0,
                "details": []}, ["kicad-cli drc: " + (r.stdout + r.stderr).strip()[:200]]
    txt = open(rpt, encoding="utf-8").read()
    counts = {}
    unconnected = 0
    section = None
    for line in txt.splitlines():
        if "DRC violations" in line:
            section = "v"
        elif "unconnected pads" in line:
            section = "u"
        elif "Footprint errors" in line:
            section = "f"
        m = _re.match(r'\[(\w+)\]:', line.strip())
        if m:
            if section == "u":
                unconnected += 1
            else:
                t = m.group(1)
                counts[t] = counts.get(t, 0) + 1
    # Paare der harten Klassen fuer die Diagnose sammeln
    details = []
    lines = txt.splitlines()
    for i, line in enumerate(lines):
        m = _re.match(r'\[(\w+)\]:', line.strip())
        if m and m.group(1) in ("courtyards_overlap", "clearance",
                                "hole_clearance", "copper_edge_clearance",
                                "items_not_allowed", "drill_out_of_range"):
            items = [l.strip()[l.find("):") + 2:].strip() if False else
                     l.strip() for l in lines[i + 2:i + 4]
                     if l.strip().startswith("@")]
            details.append("%s: %s" % (m.group(1), " | ".join(items)))
    return {"violations": counts, "unconnected": unconnected,
            "details": details}, []


# --------------------------------------------------------------------------
# Platzierungsplaene (KiCad-Koordinaten: +y = nach unten = von der Front weg)
# --------------------------------------------------------------------------

# Vier Ecktaster, exakt unter den Druckkreuzen der Zentralscheibe 6435-914.
# Gemessen am realen Teil (docs/04, Messprotokoll F10): Kreuzmitten 7,6 mm von
# der oberen bzw. unteren und 9,6 mm von der linken bzw. rechten Kante der
# 55,2er Platte -> (+/-18,0 / +/-20,0) um die Plattenmitte. Ein Kreuz ist
# 3,2 x 3,2 mm gross und trifft genau EINEN Taster; die frueheren acht
# parallelen Taster der Sichelkappen sind entfallen.
# KiCad zaehlt Y nach unten, deshalb hier das Vorzeichen gedreht.
BTN_POS = {"SW1": (18.0, -20.0),      # oben rechts
           "SW2": (-18.0, -20.0),     # oben links
           "SW3": (-18.0, 20.0),      # unten links
           "SW4": (18.0, 20.0)}       # unten rechts

# FET-Raster Bottom: 4 Spalten (M1-A, M1-B, M2-B, M2-A), oben High-, unten
# Low-Side. PowerPAK quer (5,5 x 7,5) -> Spaltenteilung 6,1 mm.
_FET_COLS = {"M1A": -8.85, "M1B": -2.95, "M2B": 2.95, "M2A": 8.85}
_FET_GRID = {}
for _leg, _x in _FET_COLS.items():
    _FET_GRID["Q_%s_H" % _leg] = (_x, -6.2, 90, "F")
    _FET_GRID["Q_%s_L" % _leg] = (_x, 1.9, 90, "F")

FIXED_BOTTOM = dict(_FET_GRID,
    J1=(0.0, 19.5, 0, "F"),            # Leistungsstecker unten
    F1=(0.0, 8.4, 0, "F"),             # SMD-Sicherung mittig
    U2=(-4.0, -21.0, 0, "F"),          # Buck 5 V
    U2_L=(-7.3, -13.8, 0, "F"),
    U4=(4.0, -21.0, 0, "F"),           # Buck 6,2 V
    U4_L=(7.3, -13.8, 0, "F"),
    R_M1_SH=(9.6, 18.0, 90, "F"),      # Shunt M1 nahe am Stecker
    C3=(-6.5, 5.6, 0, "B"),            # Bulk, niedrigbauend, Rueckseite
    C4=(6.5, 5.6, 0, "B"),
    # Treiber unter ihren FETs, in zwei Zeilen gestaffelt
    UM1A_DRV=(-8.85, -4.6, 90, "B"),
    UM1B_DRV=(-2.95, -12.2, 90, "B"),
    UM2B_DRV=(2.95, -12.2, 90, "B"),
    UM2A_DRV=(8.85, -4.6, 90, "B"),
)

FIXED_MID = {
    "U1":  (0.0, -12.5, 0, "F"),       # ESP32, Antenne zur Frontkante
    "J4":  (0.0, 20.5, 0, "F"),        # RS485-Anschluss unten
    # Feldstecker, seit dem 16.08.2026 GETEILT: Mit vier Reed-Kontakten
    # (Verschluss und Sabotage je Fenster, Punkt 34) waere ein 8-poliger
    # JST-SH 11,9 mm lang - dafuer ist auf dem Mid-Board nachweislich kein
    # Platz mehr. Zwei Stecker finden dagegen beide einen: die Sensoren
    # zusammen, der potentialfreie Haubenkontakt getrennt. Das trennt
    # nebenbei Eingaenge und Schaltausgang sauber.
    "J5":  (-9.0, 3.8, 90, "B"),       # 6-pol: 4 Reed + 2 GND
    "J6":  (-20.8, 6.6, 90, "B"),      # 2-pol: Haubenkontakt
    "U4":  (12.0, 17.5, 0, "F"),       # PhotoMOS, freie Flaeche rechts unten
    "BZ1": (5.5, 8.0, 0, "F"),         # Piezo
    # PCF8575 auf die RUECKSEITE: Der 16-Bit-Typ im SSOP-24 findet vorn
    # keinen Platz mehr - dort sitzen ESP32, MAX3485, PhotoMOS und Piezo.
    # Hinten ist ausser den Stackverbindern nichts, und I2C mit ein paar
    # hundert Kilohertz ist der unkritischste Bus auf diesem Board.
    # Der Platz auf der Rueckseite entstand erst dadurch, dass der Piezo von
    # THT auf SMD gewechselt ist - vorher blockierte er beide Seiten und der
    # 16-Bit-Expander fand auf dem ganzen Board keine Stelle. Nach oben
    # begrenzt das ESP32-Modul, das als THT-Teil ebenfalls durchblockiert.
    "U3":  (0.0, 1.8, 0, "B"),         # PCF8575
    "U2":  (-8.0, 12.0, 0, "F"),       # MAX3485
}

FIXED_TOP = dict(
    {ref: (x, y, 0, "F") for ref, (x, y) in BTN_POS.items()},
    # Displayanschluss unter dem Modul. Das Fenster der Zentralscheibe misst
    # 32,7 x 27,0 mm (Eckradius 0,7) und liegt bei (-0,95 / +0,3) mathematisch,
    # also praktisch mittig - dafuer ist ein 1,69"-Panel 240x280 quer der
    # Kandidat (Punkt 43).
    J5=(0.0, 3.0, 0, "F"),
    # Die vier Durchbrueche der Zentralscheibe liegen in den Diagonalfeldern
    # zwischen Pfeil und Ecktaster, bei (+/-9 / +/-19) mathematisch. Das haelt
    # rund 8 mm Abstand zu Kreuz und Symbol und liegt sicher auf der Platine.
    # Links oben ToF, links unten Klinke; rechts zweimal Lueftung - dort sitzt
    # deshalb der SHT4x (Punkt 46, Raummessung).
    J6=(-9.0, 19.0, 180, "F"),         # Klinkenbuchse Stern, unten links
    U3=(-9.0, -19.0, 0, "F"),          # VL53L1X, oben links
    U2=(9.0, -19.0, 0, "F"),           # SHT4x unter dem oberen Lueftungsschlitz
    # USB-C mittig oben, vollstaendig von der Zentralscheibe verdeckt und erst
    # nach deren Abnahme erreichbar (Punkt 45). Die Buchse steht jetzt - der
    # Stecker geht nach vorn, nicht radial gegen die Dosenwand.
    J1=(0.0, -19.0, 0, "F"),
    # F1 (PTC) hat keine mechanische Bindung mehr - auf dem quadratischen Board
    # ist jede feste Position entweder unter dem Stackverbinder oder unter dem
    # Klinken-Platzhalter. Die Automatik findet ihn.
    J7=(5.2, 8.0, 90, "F"),            # Reserve-UART, DNP
)


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    plans = {
        "bottom": dict(name="bottom_power_motor", module=gen_bottom_sch,
                       fixed=FIXED_BOTTOM, auto_sides=("B", "F")),
        "mid":    dict(name="mid_logic", module=gen_mid_sch,
                       fixed=FIXED_MID, auto_sides=("F", "B"), antenna=True,
                       loose=("U1",)),
        # Top: Vorderseite innerhalb r21 gehoert dem Displaymodul
        # Top: quadratisch (siehe TOP_SQ). Die Vorderseite unter dem
        # Displaymodul bleibt frei - das Fenster misst 32,7 x 27,0, das Modul
        # ist groesser; 36 x 31 als Sperrflaeche ist der vorlaeufige Ansatz.
        "top":    dict(name="top_ui", module=gen_top_sch, square=True,
                       fixed=FIXED_TOP, auto_sides=("B", "F"),
                       block_f=(-18, -15.5, 17, 15.5), edge_ok=("J1", "J6")),
    }
    fail = 0
    for key, plan in plans.items():
        if which not in ("all", key):
            continue
        out, n, perrs = build_board(**{k: v for k, v in plan.items()
                                       if k != "edge_ok"})
        res, errs = run_drc(out)
        line = "%-20s %3d Bauteile" % (plan["name"], n)
        for e in perrs:
            print("    PLATZIERUNG: %s" % e)
            fail = 1
        if errs:
            print(line, "DRC-FEHLER:", errs[0])
            fail = 1
            continue
        vio = dict(res["violations"])
        # beabsichtigte Randverletzungen (z. B. USB-C-Steckerueberhang)
        edge_ok = plan.get("edge_ok", ())

        def _only(detail, refs):
            """Betrifft die Meldung ausschliesslich Bauteile aus refs?

            KiCad nennt in der Zeile jedes beteiligte Element mit "of <REF>".
            Gewaivert wird nur, wenn ALLE Beteiligten in refs stehen - sonst
            wuerde ein Waiver fuer J1 auch eine Kollision J1 gegen U3
            verschlucken."""
            found = _re2.findall(r'\bof ([A-Z]+\d+[A-Z]?)\b', detail)
            return bool(found) and all(f in refs for f in found)

        if edge_ok and "copper_edge_clearance" in vio:
            waived = sum(1 for d in res.get("details", [])
                         if d.startswith("copper_edge_clearance")
                         and _only(d, edge_ok))
            if waived:
                vio["copper_edge_clearance"] -= waived
                if vio["copper_edge_clearance"] <= 0:
                    del vio["copper_edge_clearance"]
                print("    beabsichtigt (Steckerueberhang): %d Randverletzungen von %s"
                      % (waived, "/".join(edge_ok)))
            res["details"] = [d for d in res.get("details", [])
                              if not (d.startswith("copper_edge_clearance")
                                      and _only(d, edge_ok))]
        # kosmetische Klassen getrennt ausweisen
        cosmetic = {k: vio.pop(k) for k in list(vio)
                    if k.startswith("silk") or k in
                    ("solder_mask_bridge", "lib_footprint_issues",
                     "lib_footprint_mismatch")}
        print("%s  unrouted: %d   kosmetisch: %d"
              % (line, res["unconnected"], sum(cosmetic.values())))
        if vio:
            fail = 1
            for k, v in sorted(vio.items()):
                print("    DRC %-28s %d" % (k, v))
            for d in res.get("details", [])[:14]:
                print("      > %s" % d[:150])
        else:
            print("    DRC: keine Platzierungsfehler")
    return fail


if __name__ == "__main__":
    sys.exit(main())
