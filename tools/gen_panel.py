#!/usr/bin/env python3
"""
Setzt die drei SwitchStack-Platinen zu EINEM Fertigungsnutzen zusammen.

    python3 tools/gen_panel.py            (mit der Python-Umgebung von KiCad)

Warum erzeugt statt gezeichnet: Die drei Projekte bleiben die Quelle. Der
Nutzen ist ein Build-Ergebnis wie die Gerber - er wird jederzeit neu erzeugt
und nie von Hand bearbeitet. Damit behalten die Boards ihre eigenen
Revisionen und ihre Referenzbezeichner; nur IM Nutzen bekommen Bauteile und
Netze ein Praefix, weil beides dort eindeutig sein muss.

Aufbau
------
Drei Kreise Ø52 nebeneinander, Rahmen ringsum, Trennstege mit Mausbissen.
Die Reihe ist die flaechenguenstigste Anordnung: 172 x 62 mm = 107 cm2
gegenueber 117 x 110 mm = 129 cm2 beim Dreieck (2 oben, 1 unten). Unter
100 x 100 mm ist ohnehin nichts zu holen - drei Kreise Ø52 brauchen
mathematisch mindestens ein Quadrat von 102 mm Kantenlaenge, ohne
Trennfugen.

Trennen
-------
Runde Platinen lassen sich nicht ritzen. Jede Platine haengt an vier
Stegen von 4 mm Breite, jeder mit fuenf Bohrungen Ø0,6 mm perforiert. Nach
dem Ausbrechen bleibt ein Grat von wenigen Zehnteln stehen, der zu
verputzen ist - bei 1,5-2,5 mm Luft zur Dosenwand ist dafuer Platz, aber
es ist Handarbeit und gehoert in die Fertigungsanweisung.
"""

import copy
import json
import math
import os
import subprocess
import sys

import pcbnew

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "hardware", "fab", "panel", "switchstack_panel.kicad_pcb")

BOARD_R = 26.0          # Radius der Einzelplatine
SLOT = 2.2              # Breite der Fraesfuge (Fraeser 2,0 mm + Toleranz)
RAIL = 4.0              # Rahmenbreite
TAB_W = 4.0             # Stegbreite
# Diagonalen: 0/180 Grad sind die Befestigungsbohrungen, 90 Grad ist beim
# Top-Board der ueberstehende USB-C-Stecker und 270 Grad beim Mid-Board der
# Antennen-Keepout. Die Diagonalen sind auf allen drei Platinen frei.
TAB_ANGLES = (45, 135, 225, 315)
MB_D = 0.6              # Mausbiss-Bohrung
MB_N = 5                # Bohrungen je Steg
# Die Perforation liegt knapp AUSSERHALB der Platinenkante. Genau auf der
# Kante wuerde jede Bohrung in den Randabstand des Kupfers ragen - das waren
# im ersten Versuch 480 zusaetzliche Clearance-Fehler. Der Preis: der Grat
# steht rund 0,5 mm ueber und muss verputzt werden.
MB_OFF = 0.45

SOURCES = [
    ("hardware/bottom_power_motor/bottom_power_motor.kicad_pcb", "B_", "BOT_"),
    ("hardware/mid_logic/mid_logic.kicad_pcb",                   "M_", "MID_"),
    ("hardware/top_ui/top_ui.kicad_pcb",                         "T_", "TOP_"),
]


def mm(v):
    return pcbnew.FromMM(v)


def vec(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


# --------------------------------------------------------------------------
# Zusammenfuehren
# --------------------------------------------------------------------------

def net_code(panel, cache, name):
    """Netz im Nutzen anlegen bzw. wiederverwenden."""
    if not name:
        return 0
    if name not in cache:
        net = pcbnew.NETINFO_ITEM(panel, name)
        panel.Add(net)
        cache[name] = net.GetNetCode()
    return cache[name]


def merge(panel, cache, path, ref_prefix, net_prefix, dx, dy):
    src = pcbnew.LoadBoard(os.path.join(ROOT, path))
    off = vec(dx, dy)
    counts = {"fp": 0, "track": 0, "zone": 0, "draw": 0}

    def remap(item, src_net_name):
        item.SetNetCode(net_code(panel, cache, net_prefix + src_net_name
                                 if src_net_name else ""))

    for fp in list(src.GetFootprints()):
        new = pcbnew.FOOTPRINT(fp)
        new.SetParent(panel)
        new.Move(off)
        new.SetReference(ref_prefix + fp.GetReference())
        for pad, spad in zip(new.Pads(), fp.Pads()):
            remap(pad, spad.GetNetname())
        panel.Add(new)
        counts["fp"] += 1

    for tr in list(src.GetTracks()):
        new = tr.Duplicate(False) if _dup_takes_arg(tr) else tr.Duplicate()
        new.SetParent(panel)
        new.Move(off)
        remap(new, tr.GetNetname())
        panel.Add(new)
        counts["track"] += 1

    for zone in list(src.Zones()):
        new = pcbnew.ZONE(zone)
        new.SetParent(panel)
        new.Move(off)
        if not zone.GetIsRuleArea():
            remap(new, zone.GetNetname())
        panel.Add(new)
        counts["zone"] += 1

    for dr in list(src.GetDrawings()):
        # Die Kontur der Einzelplatine wird nicht uebernommen - im Nutzen
        # entsteht sie neu, mit Luecken fuer die Stege.
        if dr.GetLayerName() == "Edge.Cuts":
            continue
        new = dr.Duplicate(False) if _dup_takes_arg(dr) else dr.Duplicate()
        new.SetParent(panel)
        new.Move(off)
        panel.Add(new)
        counts["draw"] += 1

    return counts


def _dup_takes_arg(item):
    try:
        item.Duplicate(False)
        return True
    except TypeError:
        return False


# --------------------------------------------------------------------------
# Kontur, Stege, Mausbisse
# --------------------------------------------------------------------------

def add_seg(panel, a, b, layer=None, width=0.1):
    s = pcbnew.PCB_SHAPE(panel)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(vec(*a))
    s.SetEnd(vec(*b))
    s.SetLayer(pcbnew.Edge_Cuts if layer is None else layer)
    s.SetWidth(mm(width))
    panel.Add(s)


def add_arc(panel, cx, cy, r, a0, a1, step=1.5):
    """Bogen als Polylinie - Sehnenfehler bei 1,5 Grad unter 5 um."""
    n = max(2, int(abs(a1 - a0) / step) + 1)
    pts = [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
            cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
           for i in range(n + 1)]
    for p, q in zip(pts, pts[1:]):
        add_seg(panel, p, q)


def add_mousebites(panel, cx, cy, ang):
    """Perforation quer ueber den Steg, auf der Kontur der Platine."""
    half = math.degrees(math.asin((TAB_W / 2) / BOARD_R))
    for i in range(MB_N):
        t = -half + 2 * half * i / (MB_N - 1)
        a = math.radians(ang + t)
        r = BOARD_R + MB_OFF
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        fp = pcbnew.FOOTPRINT(panel)
        fp.SetPosition(vec(x, y))
        pad = pcbnew.PAD(fp)
        pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
        pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetSize(pcbnew.VECTOR2I(mm(MB_D), mm(MB_D)))
        pad.SetDrillSize(pcbnew.VECTOR2I(mm(MB_D), mm(MB_D)))
        pad.SetPosition(vec(x, y))
        pad.SetLayerSet(pad.UnplatedHoleMask())
        fp.Add(pad)
        fp.SetReference("MB")
        fp.Reference().SetVisible(False)
        fp.Value().SetVisible(False)
        panel.Add(fp)


def outline(panel, centers, w, h):
    """Rahmen und Fraesfugen.

    KiCad verlangt GESCHLOSSENE Konturen - ein an den Stegen unterbrochener
    Kreis ist keine gueltige Kontur, sondern 24 offene Enden. Die Fuge wird
    deshalb als das gezeichnet, was der Fraeser wirklich wegnimmt: je Steg-
    zwischenraum ein geschlossener Schlitz aus Innenbogen (r = 26), radialem
    Ende, Aussenbogen (r = 26 + SLOT) und zurueck. Was zwischen zwei
    Schlitzen stehen bleibt, ist der Steg.
    """
    add_seg(panel, (-w / 2, -h / 2), (w / 2, -h / 2))
    add_seg(panel, (w / 2, -h / 2), (w / 2, h / 2))
    add_seg(panel, (w / 2, h / 2), (-w / 2, h / 2))
    add_seg(panel, (-w / 2, h / 2), (-w / 2, -h / 2))

    half = math.degrees(math.asin((TAB_W / 2) / BOARD_R))
    ro = BOARD_R + SLOT
    for cx, cy in centers:
        edges = sorted(TAB_ANGLES)
        for i, a in enumerate(edges):
            start = a + half
            end = edges[(i + 1) % len(edges)] - half
            if end < start:
                end += 360
            p0 = (cx + BOARD_R * math.cos(math.radians(start)),
                  cy + BOARD_R * math.sin(math.radians(start)))
            p1 = (cx + BOARD_R * math.cos(math.radians(end)),
                  cy + BOARD_R * math.sin(math.radians(end)))
            q1 = (cx + ro * math.cos(math.radians(end)),
                  cy + ro * math.sin(math.radians(end)))
            q0 = (cx + ro * math.cos(math.radians(start)),
                  cy + ro * math.sin(math.radians(start)))
            add_arc(panel, cx, cy, BOARD_R, start, end)      # Platinenkante
            add_seg(panel, p1, q1)                           # radiales Ende
            add_arc(panel, cx, cy, ro, end, start)           # Aussenkante
            add_seg(panel, q0, p0)                           # zurueck
        for a in TAB_ANGLES:
            add_mousebites(panel, cx, cy, a)


# --------------------------------------------------------------------------
# Projektdatei: Regeln aus den drei Quellprojekten zusammenfuehren
# --------------------------------------------------------------------------

def write_project(path):
    """Ohne eigene .kicad_pro faellt der Nutzen auf KiCads Standardregeln
    zurueck - im ersten Versuch waren das 480 falsche Clearance-Fehler, weil
    das Bottom-Board mit 0,15 mm geroutet ist und die Vorgabe 0,2 mm lautet.
    Die Regeln werden deshalb aus den Quellprojekten uebernommen: jede
    Ebene behaelt ueber ein Netzklassenmuster ihre eigenen Werte."""
    projects = []
    for src, _, net_prefix in SOURCES:
        pro = os.path.join(ROOT, src).replace(".kicad_pcb", ".kicad_pro")
        with open(pro, encoding="utf-8") as f:
            projects.append((net_prefix, json.load(f)))

    out = copy.deepcopy(projects[0][1])
    out["sheets"], out["boards"] = [], []

    rules = out.setdefault("board", {}).setdefault("design_settings", {}) \
               .setdefault("rules", {})
    for _, pr in projects[1:]:
        other = pr.get("board", {}).get("design_settings", {}).get("rules", {})
        for k, v in other.items():
            if isinstance(v, (int, float)) and isinstance(rules.get(k), (int, float)):
                rules[k] = min(rules[k], v)     # die durchlaessigste Vorgabe
            else:
                rules.setdefault(k, v)

    ns = out.setdefault("net_settings", {})
    default = None
    for c in ns.get("classes", []):
        if c.get("name") == "Default":
            default = c
    classes, patterns = [default] if default else [], []
    for net_prefix, pr in projects:
        src_default = next((c for c in pr.get("net_settings", {}).get("classes", [])
                            if c.get("name") == "Default"), None)
        if not src_default:
            continue
        cls = copy.deepcopy(src_default)
        cls["name"] = net_prefix.rstrip("_").title()
        classes.append(cls)
        patterns.append({"netclass": cls["name"], "pattern": net_prefix + "*"})
        if default:
            for k in ("clearance", "track_width", "via_diameter", "via_drill"):
                if isinstance(cls.get(k), (int, float)):
                    default[k] = min(default.get(k, cls[k]), cls[k])
    ns["classes"] = classes
    ns["netclass_patterns"] = patterns

    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    return [c["name"] for c in classes]


# --------------------------------------------------------------------------

def main():
    # Teilung so, dass sich die Fraesfugen zweier Platinen nicht ueberlappen
    pitch = 2 * (BOARD_R + SLOT) + 0.6
    centers = [(-pitch, 0.0), (0.0, 0.0), (pitch, 0.0)]
    w = 2 * (pitch + BOARD_R + SLOT + RAIL)
    h = 2 * (BOARD_R + SLOT + RAIL)

    panel = pcbnew.BOARD()
    cache = {}
    total = {"fp": 0, "track": 0, "zone": 0, "draw": 0}
    for (path, rp, np_), (dx, dy) in zip(SOURCES, centers):
        c = merge(panel, cache, path, rp, np_, dx, dy)
        for k in total:
            total[k] += c[k]
        print("  %-34s %3d Bauteile, %4d Leiterbahnen, %d Zonen"
              % (os.path.basename(path), c["fp"], c["track"], c["zone"]))

    outline(panel, centers, w, h)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    panel.Save(OUT)
    names = write_project(OUT.replace(".kicad_pcb", ".kicad_pro"))
    print("Nutzen       : %s" % os.path.relpath(OUT, ROOT))
    print("Netzklassen  : %s" % ", ".join(names))
    print("Groesse      : %.1f x %.1f mm = %.0f cm2" % (w, h, w * h / 100))
    print("Bauteile     : %d  Netze: %d  Zonen: %d"
          % (total["fp"], len(cache), total["zone"]))
    print("Stege        : %d x %d, je %.1f mm breit mit %d Mausbissen Ø%.1f"
          % (len(centers), len(TAB_ANGLES), TAB_W, MB_N, MB_D))

    rpt = "/tmp/drc_panel.rpt"
    r = subprocess.run(["kicad-cli", "pcb", "drc", "--format", "report",
                        "-o", rpt, OUT], capture_output=True, text=True)
    if os.path.exists(rpt):
        txt = open(rpt, encoding="utf-8").read()
        import re
        kinds = {}
        for m in re.finditer(r'^\[(\w+)\]', txt, re.M):
            kinds[m.group(1)] = kinds.get(m.group(1), 0) + 1
        print("DRC          : %s" % (", ".join("%s %d" % kv for kv in
                                               sorted(kinds.items())) or "sauber"))
    else:
        print("DRC          : kicad-cli meldet %s"
              % (r.stdout + r.stderr).strip()[:120])
    return 0


if __name__ == "__main__":
    sys.exit(main())
