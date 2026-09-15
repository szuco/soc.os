#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Schliesst die letzten offenen Verbindungen automatisch - und behaelt nur,
was nachweislich schliesst.

Was Freerouting liegen laesst, sind fast immer drei Sorten: eine Bahn endet
exakt auf einem Pad der ANDEREN Lage (es fehlt ein Via), zwei Pads liegen
wenige Millimeter auseinander (es fehlt ein gerader Zug oder ein Knick), und
ein Pad erreicht die Massefläche nicht (es fehlt ein Via mit kurzem Stich).

Drei Regeln, die hier hart gelten - die ersten beiden hatte der Vorgaenger
auch, die dritte fehlte ihm und hat ihm sechs Vias auf dieselbe Bohrung und
Dutzende Duplikat-Segmente eingebracht (22.08.):

  1. VOR dem Setzen wird jeder Weg gegen fremdes Kupfer und jedes Via gegen
     ALLE Bohrungen geprueft, auch die des eigenen Netzes.
  2. NACH dem Setzen laeuft die volle DRC. Jede neue Verletzung an einem
     gesetzten Element wird rueckabgewickelt.
  3. Ein gesetzter Kandidat bleibt nur, wenn die Zahl der offenen
     Verbindungen SEINES Netzes danach kleiner ist. Was nichts bringt,
     fliegt wieder raus - und der naechste Kandidat kommt dran.

    <kicad-python> tools/rest_schliessen.py [board ...]
"""

import json
import math
import os
import re
import subprocess
import sys
import tempfile

import pcbnew

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.isdir(os.path.join(ROOT, "hardware")):
    ROOT = "/Users/piotrszegvari/Development/szuco/soc.os"
CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
BOARDS = ("top_ui", "mid_logic", "bottom_power_motor")
CU = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]

BREITE = {"24V_IN": 0.8, "24V_F": 0.8, "24V_PROT": 0.8, "M1_A": 0.8,
          "M1_B": 0.8, "M2_A": 0.8, "M2_B": 0.8, "M1_SWA": 0.8,
          "M1_SWB": 0.8, "M2_SWA": 0.8, "M2_SWB": 0.8,
          "5V_SYS": 0.5, "5V_BUCK": 0.5, "3V3_SYS": 0.5,
          "6V2_STAR": 0.5, "6V2_STAR_F": 0.5, "USB_VBUS": 0.5}
LUFT = 0.22        # Kupferabstand, etwas ueber den 0,15 der Regeln
LOCH = 0.30        # Bohrung-zu-Bohrung, etwas ueber den 0,25 der Regeln
MAX_DIST = 6.0       # laenger geht nur noch der gerade Zug / Knick auf einer Lage
MAX_DIST_LAGE = 12.0 # darueber ist es Handarbeit
RUNDEN = 4


def mm(v):
    return pcbnew.FromMM(float(v))


def drc(pfad):
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        ziel = f.name
    subprocess.run([CLI, "pcb", "drc", "--format", "json", "--severity-all",
                    "-o", ziel, pfad], capture_output=True)
    d = json.load(open(ziel))
    os.unlink(ziel)
    err = [v for v in d.get("violations", []) if v.get("severity") == "error"]
    warn = [v for v in d.get("violations", []) if v.get("type") in
            ("hole_to_hole", "holes_co_located", "via_dangling", "track_dangling")]
    return err, warn, d.get("unconnected_items", [])


def netz_von(it):
    m = re.search(r"\[([^\]]+)\]", it.get("description", ""))
    return m.group(1) if m else (it.get("net") or "")


def lage_aus(desc):
    m = re.search(r"\bon (F\.Cu|In1\.Cu|In2\.Cu|B\.Cu)\b", desc)
    if not m:
        return None
    return {"F.Cu": pcbnew.F_Cu, "In1.Cu": pcbnew.In1_Cu,
            "In2.Cu": pcbnew.In2_Cu, "B.Cu": pcbnew.B_Cu}[m.group(1)]


def lagen_laut(desc):
    """Anschliessbare Lagen eines DRC-Endpunkts - aus der Beschreibung, nicht
    per HitTest: Beim HitTest zaehlt die offen gemeldete Bahn selbst mit, und
    der 'Kandidat' wird ihr Duplikat (so entstanden die Duplikate vom 20.08.)."""
    if desc.startswith("PTH pad") or desc.startswith("Via"):
        return set(CU)
    l = lage_aus(desc)
    return {l} if l is not None else set()


class Board:
    def __init__(self, name):
        self.name = name
        self.pfad = os.path.join(ROOT, "hardware", name, name + ".kicad_pcb")
        self.b = pcbnew.LoadBoard(self.pfad)
        self.umriss = pcbnew.SHAPE_POLY_SET()
        self.b.GetBoardPolygonOutlines(self.umriss, True)
        self.via_b, self.via_d = (0.8, 0.4) if "bottom" in name else (0.6, 0.3)

    def im_umriss(self, x, y):
        if not self.umriss.OutlineCount():
            return True
        return self.umriss.Contains(pcbnew.VECTOR2I(mm(x), mm(y)))

    # ---- Freiheitspruefungen -------------------------------------------
    def _fremd(self, form, lage, eigen):
        for t in self.b.GetTracks():
            if t.GetNetname() == eigen:
                continue
            if t.GetClass() != "PCB_VIA" and t.GetLayer() != lage:
                continue
            if t.GetEffectiveShape(lage).GetClearance(form) / 1e6 < LUFT:
                return True
        for fp in self.b.GetFootprints():
            for pad in fp.Pads():
                if pad.GetNetname() == eigen or not pad.IsOnLayer(lage):
                    continue
                if pad.GetEffectiveShape(lage).GetClearance(form) / 1e6 < LUFT:
                    return True
        return False

    def frei_segment(self, x0, y0, x1, y1, lage, breite, eigen):
        seg = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(mm(x0), mm(y0)),
                                   pcbnew.VECTOR2I(mm(x1), mm(y1)), mm(breite))
        if self._fremd(seg, lage, eigen):
            return False
        n = max(2, int(math.hypot(x1 - x0, y1 - y0) / 0.5))
        return all(self.im_umriss(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n)
                   for i in range(n + 1))

    def loch_frei(self, x, y):
        """Regel 3: Abstand zu JEDER Bohrung, auch des eigenen Netzes."""
        p = (x, y)
        for t in self.b.GetTracks():
            if t.GetClass() != "PCB_VIA":
                continue
            q = t.GetPosition()
            d = math.hypot(pcbnew.ToMM(q.x) - x, pcbnew.ToMM(q.y) - y)
            if d - (pcbnew.ToMM(t.GetDrillValue()) + self.via_d) / 2.0 < LOCH:
                return False
        for fp in self.b.GetFootprints():
            for pad in fp.Pads():
                if pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                    continue
                q = pad.GetPosition()
                dr = pad.GetDrillSize()
                d = math.hypot(pcbnew.ToMM(q.x) - x, pcbnew.ToMM(q.y) - y)
                if d - (pcbnew.ToMM(max(dr.x, dr.y)) + self.via_d) / 2.0 < LOCH:
                    return False
        return True

    def frei_via(self, x, y, eigen):
        if not self.im_umriss(x, y) or not self.loch_frei(x, y):
            return False
        kreis = pcbnew.SHAPE_CIRCLE(pcbnew.VECTOR2I(mm(x), mm(y)), mm(self.via_b / 2.0))
        for lage in CU:
            if self._fremd(kreis, lage, eigen):
                return False
        for z in self.b.Zones():
            if z.GetIsRuleArea() and z.GetDoNotAllowVias() \
                    and z.Outline().Contains(pcbnew.VECTOR2I(mm(x), mm(y))):
                return False
        return True

    def zone_traegt(self, x, y, netz, ohne_lage=None):
        """Liegt der Punkt mit Rand in der gefuellten Flaeche des Netzes -
        auf irgendeiner Lage ausser ohne_lage?"""
        p = pcbnew.VECTOR2I(mm(x), mm(y))
        for z in self.b.Zones():
            if z.GetIsRuleArea() or z.GetNetname() != netz:
                continue
            for lage in CU:
                if lage == ohne_lage or not z.IsOnLayer(lage):
                    continue
                poly = z.GetFilledPolysList(lage)
                if poly.Contains(p) and poly.Contains(p, -1, mm(self.via_b / 2.0 + 0.1)):
                    return True
        return False

    def lagen_von(self, x, y, netz):
        p = pcbnew.VECTOR2I(mm(x), mm(y))
        lagen = set()
        for fp in self.b.GetFootprints():
            for pad in fp.Pads():
                if pad.GetNetname() == netz and pad.HitTest(p):
                    if pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                        lagen.update(l for l in CU if pad.IsOnLayer(l))
                    else:
                        lagen.update(CU)
        for t in self.b.GetTracks():
            if t.GetNetname() != netz or not t.HitTest(p):
                continue
            if t.GetClass() == "PCB_VIA":
                lagen.update(CU)
            else:
                lagen.add(t.GetLayer())
        return lagen

    # ---- Setzen ---------------------------------------------------------
    def via(self, x, y, net):
        v = pcbnew.PCB_VIA(self.b)
        v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        v.SetDrill(mm(self.via_d))
        v.SetWidth(mm(self.via_b))
        v.SetNet(net)
        self.b.Add(v)
        return v

    def seg(self, x0, y0, x1, y1, lage, breite, net):
        t = pcbnew.PCB_TRACK(self.b)
        t.SetStart(pcbnew.VECTOR2I(mm(x0), mm(y0)))
        t.SetEnd(pcbnew.VECTOR2I(mm(x1), mm(y1)))
        t.SetLayer(lage)
        t.SetWidth(mm(breite))
        t.SetNet(net)
        self.b.Add(t)
        return t

    def speichern(self):
        pcbnew.ZONE_FILLER(self.b).Fill(self.b.Zones())
        pcbnew.SaveBoard(self.pfad, self.b)


def ring(x, y, radien, n=8):
    for r in radien:
        for w in range(n):
            a = 2 * math.pi * w / n
            yield x + r * math.cos(a), y + r * math.sin(a)


def kandidaten(bd, u):
    """Liefert fuer eine offene Verbindung eine Liste von Kandidaten; jeder
    Kandidat ist eine Liste von Setz-Anweisungen ('via', x, y) oder
    ('seg', x0, y0, x1, y1, lage). Reihenfolge = Praeferenz."""
    its = u.get("items", [])
    if len(its) < 2:
        return []
    a, b = its[0], its[1]
    da, db = a.get("description", ""), b.get("description", "")
    za, zb = da.startswith("Zone"), db.startswith("Zone")
    if za and zb:
        return []                       # Insel ohne Koordinate: Handarbeit / gnd_stitch
    if zb:                              # Zone immer nach a
        a, b, da, db, za, zb = b, a, db, da, zb, za
    netz = netz_von(a) or netz_von(b)
    ax, ay = a["pos"]["x"], a["pos"]["y"]
    bx, by = b["pos"]["x"], b["pos"]["y"]
    breite = BREITE.get(netz, 0.25)
    out = []

    if za:
        # Pad/Bahn b erreicht die Flaeche nicht: Via mit kurzem Stich von b
        lb = lagen_laut(db) or set(CU)
        zl = lage_aus(da)
        for x, y in ring(bx, by, (0.7, 1.0, 1.4, 1.9, 2.5)):
            if not bd.zone_traegt(x, y, netz, ohne_lage=None):
                continue
            for lage in sorted(lb, key=lambda l: (l != pcbnew.F_Cu, l != pcbnew.B_Cu)):
                out.append([("seg", bx, by, x, y, lage), ("via", x, y)])
                break
        return out

    dist = math.hypot(ax - bx, ay - by)
    if dist > MAX_DIST_LAGE:
        return []
    la = lagen_laut(da)
    lb = lagen_laut(db)
    if not la or not lb:
        return []
    gemeinsam = [l for l in CU if l in la and l in lb]
    # 1. gerader Zug auf gemeinsamer Lage
    for lage in gemeinsam:
        out.append([("seg", ax, ay, bx, by, lage)])
    if dist > MAX_DIST:
        # weiter weg nur noch der Knick auf gemeinsamer Lage (Fall 3)
        mx, my = (ax + bx) / 2.0, (ay + by) / 2.0
        for x, y in ring(mx, my, (1.0, 2.0, 3.0)):
            for lage in gemeinsam:
                out.append([("seg", ax, ay, x, y, lage), ("seg", x, y, bx, by, lage)])
        return out
    # 2. Via zwischen den Lagen, Stiche auf beiden Seiten
    mx, my = (ax + bx) / 2.0, (ay + by) / 2.0
    punkte = [(mx, my)] + list(ring(mx, my, (0.5, 0.9, 1.4, 2.0)))
    punkte.sort(key=lambda p: math.hypot(p[0] - ax, p[1] - ay) + math.hypot(p[0] - bx, p[1] - by))
    for x, y in punkte:
        for l1 in la:
            for l2 in lb:
                if l1 == l2 and gemeinsam:
                    continue
                k = [("via", x, y)]
                if math.hypot(x - ax, y - ay) > 1e-3:
                    k.append(("seg", ax, ay, x, y, l1))
                if math.hypot(x - bx, y - by) > 1e-3:
                    k.append(("seg", x, y, bx, by, l2))
                out.append(k)
    # 3. Knick ohne Via auf gemeinsamer Lage
    for x, y in ring(mx, my, (0.5, 0.9, 1.4, 2.0)):
        for lage in gemeinsam:
            out.append([("seg", ax, ay, x, y, lage), ("seg", x, y, bx, by, lage)])
    return out


def passt(bd, kand, netz):
    breite = BREITE.get(netz, 0.25)
    for s in kand:
        if s[0] == "via":
            if not bd.frei_via(s[1], s[2], netz):
                return False
        else:
            if not bd.frei_segment(s[1], s[2], s[3], s[4], s[5], breite, netz):
                return False
    return True


def setze(bd, kand, netz):
    net = bd.b.FindNet(netz)
    breite = BREITE.get(netz, 0.25)
    items = []
    for s in kand:
        if s[0] == "via":
            items.append(bd.via(s[1], s[2], net))
        else:
            items.append(bd.seg(s[1], s[2], s[3], s[4], s[5], breite, net))
    return items


def schluessel(u):
    its = u.get("items", [])
    anker = []
    for it in its[:2]:
        d = re.sub(r", length [\d.]+ mm", "", it.get("description", ""))
        p = it.get("pos", {})
        anker.append((d, round(p.get("x", 0), 2), round(p.get("y", 0), 2)))
    return (netz_von(its[0]) if its else "", tuple(sorted(anker)))


def je_netz(unc):
    z = {}
    for u in unc:
        n = netz_von(u.get("items", [{}])[0])
        z[n] = z.get(n, 0) + 1
    return z


def schliesse(name):
    bd = Board(name)
    err0, warn0, unc0 = drc(bd.pfad)
    start = len(unc0)
    if err0:
        print("%-20s hat schon %d Kupferfehler - erst die beheben" % (name, len(err0)))
        return
    versuch = {}          # Schluessel -> naechster Kandidatenindex
    aufgegeben = set()
    gesetzt_gesamt = 0
    unc = unc0
    for runde in range(RUNDEN):
        gruppen = []      # (schluessel, netz, items)
        netze_belegt = set()
        for u in unc:
            k = schluessel(u)
            if k in aufgegeben:
                continue
            netz = k[0]
            if netz in netze_belegt or bd.b.FindNet(netz) is None:
                continue
            kands = kandidaten(bd, u)
            i = versuch.get(k, 0)
            while i < len(kands) and not passt(bd, kands[i], netz):
                i += 1
            if i >= len(kands):
                aufgegeben.add(k)
                continue
            items = setze(bd, kands[i], netz)
            versuch[k] = i + 1
            gruppen.append((k, netz, items))
            netze_belegt.add(netz)
        if not gruppen:
            break
        bd.speichern()
        err1, warn1, unc1 = drc(bd.pfad)

        # Regel 2: neue Fehler/Warnungen an unseren Elementen -> Gruppe raus
        schuldig = set()
        for v in err1 + warn1[len(warn0):] if len(warn1) > len(warn0) else err1:
            getroffen = False
            for it in v.get("items", []):
                pos = it.get("pos", {})
                p = pcbnew.VECTOR2I(mm(pos.get("x", 0)), mm(pos.get("y", 0)))
                for k, netz, items in gruppen:
                    if any(g.HitTest(p) for g in items):
                        schuldig.add(k)
                        getroffen = True
            if not getroffen:
                schuldig.update(k for k, _, _ in gruppen)   # unklar -> alles zurueck
        # Regel 3: Netzzaehler muss sinken
        vor, nach = je_netz(unc), je_netz(unc1)
        unwirksam = set(k for k, netz, _ in gruppen
                        if nach.get(netz, 0) >= vor.get(netz, 0))
        raus = schuldig | unwirksam
        behalten = 0
        for k, netz, items in gruppen:
            if k in raus:
                for g in items:
                    bd.b.Remove(g)
            else:
                behalten += 1
                aufgegeben.add(k)          # geschlossen, nicht mehr anfassen
        if raus:
            bd.speichern()
            err1, warn1, unc1 = drc(bd.pfad)
        gesetzt_gesamt += behalten
        print("%-20s Runde %d: %d probiert, %d behalten (%d DRC-Rueckabwicklung, "
              "%d unwirksam), offen %d -> %d" % (name, runde + 1, len(gruppen), behalten,
              len(schuldig), len(unwirksam - schuldig), len(unc), len(unc1)))
        unc = unc1
        if len(err1) > len(err0):
            print("%-20s !!! Kupferfehler trotz Rueckabwicklung: %d - bitte pruefen"
                  % (name, len(err1)))
            break
    err2, warn2, unc2 = drc(bd.pfad)
    print("%-20s offen: %d -> %d, Kupferfehler: %d -> %d, Loch/Dangling: %d -> %d"
          % (name, start, len(unc2), len(err0), len(err2), len(warn0), len(warn2)))


def main():
    for name in sys.argv[1:] or BOARDS:
        schliesse(name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
