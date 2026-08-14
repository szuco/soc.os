#!/usr/bin/env python3
"""
Routet die drei SwitchStack-Boards mit Freerouting.

    python3 tools/route_boards.py [bottom|mid|top]

Pipeline je Board:
  1. .kicad_pcb -> Specctra-DSN (pcbnew.ExportSpecctraDSN)
  2. DSN-Nachbearbeitung: Leistungsnetze bekommen eigene Klassen mit
     breiteren Bahnen und groesseren Vias (PWR 1,0 mm / RAIL 0,5 mm).
     KiCad 7 kann Netzklassen nicht scriptbar zuweisen, deshalb auf
     DSN-Textebene - dort ist das Format vollstaendig dokumentiert.
  3. Freerouting headless (Java), begrenzte Passzahl
  4. SES-Import zurueck ins Board, speichern
  5. DRC: Clearance-Verletzungen muessen 0 sein; unverbundene Reste werden
     nach Netz klassifiziert - PGND-Reste sind erwartet, weil die
     Masseflaechen erst beim Oeffnen in KiCad gefuellt werden
     (ZONE_FILLER stuerzt headless ab, dokumentiert in gen_layouts.py).

Freerouting ist ein Autorouter: Das Ergebnis ist elektrisch korrekt und
DRC-sauber, aber KEIN handoptimiertes Leistungslayout. Vor der Fertigung
gehoeren die Motorpfade und die Buck-Schleifen von Hand nachgezogen
(docs/05, Pruefliste).
"""

import os
import re
import subprocess
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_layouts import run_drc                                 # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRATCH = os.environ.get("SWITCHSTACK_SCRATCH", "/tmp/switchstack_route")
# Freerouting 2.1.0 headless hat sich als unbrauchbar erwiesen: -mp wird
# ignoriert, Float-Optionen sind per CLI nicht setzbar, und die SES stammt
# von einem aelteren Zwischenstand statt vom Endergebnis (6 Netze fehlten,
# obwohl das Log 0 unrouted meldete). Version 1.9.0 routet klassisch und
# exportiert die SES vollstaendig - braucht aber ein X-Display, daher
# xvfb-run.
JAR = os.environ.get(
    "FREEROUTING_JAR",
    "/tmp/claude-0/-home-user-soc-os/65292af4-35bb-586e-b8d7-4f67d74efa42/"
    "scratchpad/freerouting-1.9.0.jar")

# Netzklassen: (Breite um, Clearance um, Vianame)
VIA_STD = 'Via[0-1]_600:300_um'
VIA_PWR = 'Via[0-1]_800:400_um'

CLASSES = {
    "bottom_power_motor": {
        "PWR": (1000, 250, VIA_PWR, [
            "24V_IN", "24V_F", "24V_PROT", "M1_A", "M1_B", "M2_A", "M2_B",
            "M1_SWA", "M1_SWB", "M2_SWA", "M2_SWB",
        ]),
        "RAIL": (500, 200, VIA_PWR, [
            "5V_BUCK", "5V_SYS", "3V3_SYS", "6V2_STAR", "6V2_STAR_F",
            "12V_RAW", "12V_GATE", "U2_SW", "U3_SW", "U4_SW", "USB_VBUS",
        ]),
    },
    "mid_logic": {
        "RAIL": (500, 200, VIA_PWR, ["3V3_SYS", "5V_SYS", "6V2_STAR_F"]),
    },
    "top_ui": {
        "RAIL": (500, 200, VIA_PWR, ["3V3_SYS", "6V2_STAR_F", "USB_VBUS",
                                     "STAR_OUT"]),
    },
}


def _shrink_boundary(src, delta_mm=0.5):
    """Board-Outline im DSN nach innen skalieren.

    KiCad exportiert die Kante ohne den Kupfer-Randabstand; Freerouting
    routet dann bis (fast) an die Kante und verletzt die 0,5-mm-Regel.
    Die Outline ist ein Kreis um (0,0), deshalb genuegt es, alle
    Boundary-Koordinaten radial zu skalieren.
    """
    m = re.search(r'\(boundary', src)
    depth, i = 0, m.start()
    for i in range(m.start(), len(src)):
        if src[i] == "(":
            depth += 1
        elif src[i] == ")":
            depth -= 1
            if depth == 0:
                break
    block = src[m.start():i + 1]
    nums = re.findall(r'-?\d+(?:\.\d+)?', block)
    coords = [float(n) for n in nums[1:]]        # erster Wert: Breite 0
    rmax = max(abs(c) for c in coords)
    f = (rmax - delta_mm * 1000.0) / rmax

    def scale(mo):
        v = float(mo.group(0))
        return "%.2f" % (v * f)
    # nur die Koordinaten skalieren, nicht die Aperturbreite "0"
    head, tail = block.split(None, 3)[:3], block.split(None, 3)[3]
    new_block = " ".join(head) + " " + re.sub(r'-?\d+(?:\.\d+)?', scale, tail)
    return src[:m.start()] + new_block + src[i + 1:]


def patch_dsn(path, classes):
    src = open(path, encoding="utf-8").read()
    src = _shrink_boundary(src)

    # 1. Groessere Via-Definition ergaenzen (Kopie der Standarddefinition)
    m = re.search(r'\(padstack "%s"' % re.escape(VIA_STD), src)
    if not m:
        raise RuntimeError("Standard-Via nicht im DSN gefunden")
    depth = 0
    for i in range(m.start(), len(src)):
        if src[i] == "(":
            depth += 1
        elif src[i] == ")":
            depth -= 1
            if depth == 0:
                break
    block = src[m.start():i + 1]
    big = block.replace("600", "800").replace("300", "400")
    src = src[:i + 1] + "\n    " + big + src[i + 1:]

    # 2. Grosses Via nutzbar machen
    src = src.replace('(via "%s")' % VIA_STD,
                      '(via "%s" "%s")' % (VIA_STD, VIA_PWR), 1)

    # 3. Netze aus kicad_default entfernen und eigene Klassen anhaengen
    all_nets = [n for spec in classes.values() for n in spec[3]]
    cm = re.search(r'\(class kicad_default', src)
    depth = 0
    for i in range(cm.start(), len(src)):
        if src[i] == "(":
            depth += 1
        elif src[i] == ")":
            depth -= 1
            if depth == 0:
                break
    cblock = src[cm.start():i + 1]
    nblock = cblock
    for net in all_nets:
        nblock = re.sub(r'(?<=[\s"])%s(?=[\s"])' % re.escape(net), "", nblock)
    extra = []
    for cname, (width, clear, via, nets) in classes.items():
        listed = " ".join('"%s"' % n for n in nets)
        extra.append(
            '    (class %s %s\n'
            '      (circuit\n        (use_via "%s")\n      )\n'
            '      (rule\n        (width %d)\n        (clearance %d)\n      )\n'
            '    )' % (cname, listed, via, width, clear))
    src = src.replace(cblock, nblock + "\n" + "\n".join(extra), 1)
    open(path, "w", encoding="utf-8").write(src)


def _sexpr(txt):
    """Minimaler S-Expression-Parser (Tokens: Klammern, Atome, Strings)."""
    toks = re.findall(r'"[^"]*"|\(|\)|[^\s()]+', txt)
    pos = [0]

    def parse():
        out = []
        while pos[0] < len(toks):
            t = toks[pos[0]]
            pos[0] += 1
            if t == "(":
                out.append(parse())
            elif t == ")":
                return out
            else:
                out.append(t[1:-1] if t.startswith('"') else t)
        return out
    return parse()


def _walk(node, name):
    if isinstance(node, list):
        if node and node[0] == name:
            yield node
        for ch in node:
            yield from _walk(ch, name)


LAYERS = {"F.Cu": pcbnew.F_Cu, "B.Cu": pcbnew.B_Cu}


def import_ses(board, ses_path):
    """SES-Routen in das Board uebernehmen (Wires und Vias)."""
    tree = _sexpr(open(ses_path, encoding="utf-8").read())

    res = next(_walk(tree, "resolution"))       # z.B. (resolution um 10)
    if res[1] != "um":
        raise RuntimeError("unerwartete SES-Einheit %r" % res[1])
    scale = 1000.0 / float(res[2])              # SES-Einheit -> nm

    def to_vec(x, y):
        # Specctra zaehlt Y mathematisch nach oben, KiCad nach unten
        return pcbnew.VECTOR2I(int(float(x) * scale), -int(float(y) * scale))

    n_wires = n_vias = 0
    for netblk in _walk(next(_walk(tree, "network_out")), "net"):
        net = board.FindNet(netblk[1])
        if net is None:
            raise RuntimeError("SES-Netz %r nicht im Board" % netblk[1])
        for wire in _walk(netblk, "wire"):
            for path in _walk(wire, "path"):
                layer, width = LAYERS[path[1]], float(path[2]) * scale
                pts = path[3:]
                for i in range(0, len(pts) - 2, 2):
                    seg = pcbnew.PCB_TRACK(board)
                    seg.SetStart(to_vec(pts[i], pts[i + 1]))
                    seg.SetEnd(to_vec(pts[i + 2], pts[i + 3]))
                    seg.SetLayer(layer)
                    seg.SetWidth(int(width))
                    seg.SetNet(net)
                    board.Add(seg)
                    n_wires += 1
        for via in _walk(netblk, "via"):
            m = re.match(r'Via\[\d+-\d+\]_(\d+):(\d+)_um$', via[1])
            if not m:
                raise RuntimeError("unbekannter Via-Padstack %r" % via[1])
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(to_vec(via[2], via[3]))
            v.SetWidth(int(int(m.group(1)) * 1000))
            v.SetDrill(int(int(m.group(2)) * 1000))
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            v.SetNet(net)
            board.Add(v)
            n_vias += 1
    return n_wires, n_vias


def route(name, passes=200, timeout=2400):
    os.makedirs(SCRATCH, exist_ok=True)
    pcb = os.path.join(ROOT, "hardware", name, name + ".kicad_pcb")
    dsn = os.path.join(SCRATCH, name + ".dsn")
    ses = os.path.join(SCRATCH, name + ".ses")

    board = pcbnew.LoadBoard(pcb)
    # vorhandene Leiterbahnen/Vias entfernen - der Lauf ist reproduzierbar
    for t in list(board.GetTracks()):
        board.Remove(t)
    pcbnew.ExportSpecctraDSN(board, dsn)
    patch_dsn(dsn, CLASSES.get(name, {}))
    print("%-20s DSN exportiert und gepatcht" % name)

    if os.path.exists(ses):
        os.remove(ses)
    log = os.path.join(SCRATCH, name + ".log")
    # optimizer.max_passes=100 (Default) laeuft headless praktisch endlos -
    # der Router selbst ist nach < 5 min fertig, danach begrenzen wir die
    # Optimierung hart. improvement_threshold stoppt zusaetzlich frueher,
    # sobald ein Durchlauf weniger als 1 % Verbesserung bringt.
    # -dct 0: kein Bestaetigungsdialog; -oit 0.5: Optimierung beenden,
    # sobald ein Durchlauf weniger als 0,5 % Verbesserung bringt
    cmd = ["xvfb-run", "-a", "java", "-jar", JAR, "-de", dsn, "-do", ses,
           "-mp", str(passes), "-dct", "0", "-oit", "0.5"]
    with open(log, "w") as lf:
        r = subprocess.run(cmd, stdout=lf, stderr=subprocess.STDOUT,
                           text=True, timeout=timeout)
    if not os.path.exists(ses):
        tail = open(log).read().strip().splitlines()[-6:]
        raise RuntimeError("Freerouting ohne SES beendet:\n" + "\n".join(tail))

    # pcbnew.ImportSpecctraSES braucht den Editor-Kontext und schlaegt
    # standalone fehl - der Import ist deshalb selbst implementiert.
    n_wires, n_vias = import_ses(board, ses)
    if n_wires == 0:
        raise RuntimeError("SES-Import ergab keine Leiterbahnen")
    pcbnew.SaveBoard(pcb, board)

    n_tracks = sum(1 for t in board.GetTracks()
                   if t.GetClass() == "PCB_TRACK")
    n_vias = sum(1 for t in board.GetTracks() if t.GetClass() == "PCB_VIA")
    print("%-20s geroutet: %d Bahnsegmente, %d Vias"
          % (name, n_tracks, n_vias))
    return pcb


def classify_unrouted(rpt_path):
    """Unverbundene Paare nach Netz zaehlen."""
    txt = open(rpt_path, encoding="utf-8").read()
    section = txt.split("unconnected pads")[-1]
    nets = re.findall(r'\[(\w+)\]', section)
    counts = {}
    for i in range(0, len(nets)):
        counts[nets[i]] = counts.get(nets[i], 0) + 1
    return counts


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    fail = 0
    for name in ("bottom_power_motor", "mid_logic", "top_ui"):
        key = name.split("_")[0] if name != "top_ui" else "top"
        if which not in ("all", key):
            continue
        pcb = route(name)
        res, errs = run_drc(pcb)
        if errs:
            print("  DRC-FEHLER:", errs[0])
            fail = 1
            continue
        vio = dict(res["violations"])
        cosmetic = {k: vio.pop(k) for k in list(vio)
                    if k.startswith("silk") or k in
                    ("solder_mask_bridge", "lib_footprint_issues",
                     "lib_footprint_mismatch")}
        # USB-Steckerueberhang am Top-Board ist beabsichtigt
        if name == "top_ui" and "copper_edge_clearance" in vio:
            waived = sum(1 for d in res.get("details", [])
                         if d.startswith("copper_edge_clearance")
                         and d.rstrip().endswith("of J1"))
            if waived:
                vio["copper_edge_clearance"] -= waived
                if vio["copper_edge_clearance"] <= 0:
                    del vio["copper_edge_clearance"]

        rpt = "/tmp/drc_%s.rpt" % name
        unrouted = classify_unrouted(rpt) if os.path.exists(rpt) else {}
        gnd = sum(v for k, v in unrouted.items() if k in ("PGND", "AGND"))
        other = {k: v for k, v in unrouted.items() if k not in ("PGND", "AGND")}
        print("%-20s offen: %d auf PGND/AGND (Flaechenfuellung), %d andere"
              % (name, gnd, sum(other.values())))
        if other:
            fail = 1
            for k, v in sorted(other.items()):
                print("    UNVERBUNDEN %-20s %d" % (k, v))
        if vio:
            fail = 1
            for k, v in sorted(vio.items()):
                print("    DRC %-28s %d" % (k, v))
            for d in res.get("details", [])[:10]:
                print("      > %s" % d[:150])
        else:
            print("    DRC: sauber (kosmetisch: %d)" % sum(cosmetic.values()))
    return fail


if __name__ == "__main__":
    sys.exit(main())
