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
     nach Netz klassifiziert.

WICHTIG - die Zonen muessen VOR dem Export gefuellt sein. Bis zum 17.08.2026
liefen die Boards ungefuellt in den Router, weil ZONE_FILLER headless
angeblich abstuerzte (galt fuer pcbnew 7, unter KiCad 10 nicht mehr). Der
Router musste PGND deshalb als gewoehnliches Netz mit Leiterbahnen aufloesen
statt es der Flaeche zu ueberlassen - und verbrauchte einen Grossteil seines
Aufwands dafuer. gen_layouts.py fuellt jetzt selbst.

Freerouting ist ein Autorouter: Das Ergebnis ist elektrisch korrekt und
DRC-sauber, aber KEIN handoptimiertes Leistungslayout. Vor der Fertigung
gehoeren die Motorpfade und die Buck-Schleifen von Hand nachgezogen
(docs/05, Pruefliste).
"""

import os
import re
import shutil
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
JAR = os.environ.get("FREEROUTING_JAR", "")

# Freerouting braucht ein X-Display. Unter Linux loest das xvfb-run, auf macOS
# gibt es kein Xvfb - dort uebernimmt ein Container. Beide Wege rufen dasselbe
# Jar mit denselben Argumenten auf; der Unterschied ist nur die Huelle.
DOCKER_IMAGE = os.environ.get("SWITCHSTACK_FR_IMAGE", "switchstack-freerouting")


def freerouting_cmd(dsn, ses, passes):
    """Aufrufkommando fuer Freerouting - lokal oder im Container.

    Vorrang hat ein lokales Jar mit xvfb-run (so lief die Pipeline unter
    Linux). Fehlt eines von beiden, wird der Container benutzt; dann muessen
    die Pfade in dessen Sicht umgeschrieben werden, weil SCRATCH dort unter
    /work haengt.

    Gebaut wird das Image mit
        docker build -f tools/freerouting.Dockerfile -t switchstack-freerouting tools/
    """
    lokal = JAR and os.path.exists(JAR) and shutil.which("xvfb-run")
    if lokal:
        return ["xvfb-run", "-a", "java", "-jar", JAR,
                "-de", dsn, "-do", ses, "-mp", str(passes),
                "-dct", "0", "-oit", "0.5"], "lokal (xvfb-run)"

    if not shutil.which("docker"):
        raise RuntimeError(
            "Weder ein lokales Freerouting-Jar mit xvfb-run noch Docker "
            "gefunden. Entweder FREEROUTING_JAR setzen (Linux mit xvfb-run) "
            "oder das Image bauen:\n"
            "  docker build -f tools/freerouting.Dockerfile -t %s tools/"
            % DOCKER_IMAGE)

    return (["docker", "run", "--rm",
             "-v", "%s:/work" % os.path.abspath(SCRATCH),
             DOCKER_IMAGE,
             "-de", "/work/" + os.path.basename(dsn),
             "-do", "/work/" + os.path.basename(ses),
             "-mp", str(passes), "-dct", "0", "-oit", "0.5"],
            "Container %s" % DOCKER_IMAGE)

# Netzklassen: (Breite um, Clearance um, Vianame)
# Die Namen der Via-Padstacks tragen den Lagenbereich: zweilagig "Via[0-1]",
# vierlagig "Via[0-3]". Seit der Umstellung auf vier Lagen (17.08.2026) darf
# das nicht mehr fest verdrahtet sein - patch_dsn liest den Bereich aus dem
# erzeugten DSN und setzt die beiden Namen daraus zusammen.
VIA_STD = 'Via[0-1]_600:300_um'
VIA_PWR = 'Via[0-1]_800:400_um'


def _via_names(src):
    """Via-Padstacknamen aus dem DSN, unabhaengig von der Lagenzahl."""
    m = re.search(r'padstack "Via\[(\d+)-(\d+)\]_600:300_um"', src)
    if not m:
        raise RuntimeError("Standard-Via nicht im DSN gefunden")
    span = "Via[%s-%s]" % (m.group(1), m.group(2))
    return span + "_600:300_um", span + "_800:400_um"

CLASSES = {
    "bottom_power_motor": {
        # 0,8 mm / 0,2 mm statt 1,0 / 0,25: Mit den breiteren Regeln
        # liess Freerouting nach 200 Passes (62 min) noch 58 Verbindungen
        # offen - die 1,0-mm-Bahnen passen nicht ueberall zwischen die
        # FET-Pads. 0,8 mm traegt bei 35-um-Kupfer ~3 A dauerhaft und
        # deckt Laufstrom (<= 1 A) wie Trip-Transienten ab; die
        # Leistungspfade werden vor der Fertigung ohnehin von Hand
        # nachgezogen (docs/05).
        # Vias 0,6/0,3 und Standard-Clearance: Die 0,8er-Vias mit 0,2er-
        # Clearance passen nicht in die Schluchten zwischen den FET-Pads;
        # die letzten ~50 Verbindungen blieben damit dauerhaft offen.
        # 0,6er-Vias tragen 2-3 A - fuer Laufstrom und kurze Transienten
        # ausreichend; Leistungspfade werden vor der Fertigung ohnehin
        # von Hand nachgezogen (docs/05).
        #
        # CLEARANCE MIT RESERVE. Freerouting unterschreitet die Vorgabe: Bei
        # 150 um Anweisung kamen auf In1.Cu real 114 bis 144 um heraus - fuenf
        # Verletzungen gegen die 150-um-Regel. Deshalb steht hier 200 um, damit
        # auch das Ergebnis ueber 150 bleibt. Die Bahnbreiten sind davon
        # unberuehrt.
        "PWR": (800, 200, VIA_STD, [
            "24V_IN", "24V_F", "24V_PROT", "M1_A", "M1_B", "M2_A", "M2_B",
            "M1_SWA", "M1_SWB", "M2_SWA", "M2_SWB",
        ]),
        "RAIL": (500, 200, VIA_STD, [
            "5V_BUCK", "5V_SYS", "3V3_SYS", "6V2_STAR", "6V2_STAR_F",
            "12V_RAW", "12V_GATE", "U2_SW", "U3_SW", "U4_SW", "USB_VBUS",
        ]),
    },
    "mid_logic": {
        "RAIL": (500, 250, VIA_PWR, ["3V3_SYS", "5V_SYS", "6V2_STAR_F"]),
    },
    "top_ui": {
        "RAIL": (500, 250, VIA_PWR, ["3V3_SYS", "6V2_STAR_F", "USB_VBUS",
                                     "STAR_OUT"]),
    },
}


RING_RI = 25.6      # mm; Kupfer bleibt unter ~25,45 -> Randabstand > 0,5
RING_RO = 26.4


def _ring_polygon(a0, a1, step=3.0):
    """Annulus-Sektor von a0 bis a1 Grad (DSN-Koordinaten, Y nach oben)."""
    import math
    pts = []
    a = a0
    while a < a1:
        pts.append((RING_RO * math.cos(math.radians(a)),
                    RING_RO * math.sin(math.radians(a))))
        a += step
    pts.append((RING_RO * math.cos(math.radians(a1)),
                RING_RO * math.sin(math.radians(a1))))
    a = a1
    while a > a0:
        pts.append((RING_RI * math.cos(math.radians(a)),
                    RING_RI * math.sin(math.radians(a))))
        a -= step
    pts.append((RING_RI * math.cos(math.radians(a0)),
                RING_RI * math.sin(math.radians(a0))))
    return " ".join("%.1f %.1f" % (x * 1000, y * 1000) for x, y in pts)


def _edge_ring(src, slit=None):
    """Ring-Keepout am Boardrand in den DSN-Structure-Block einfuegen.

    KiCad exportiert die Kante ohne den Kupfer-Randabstand, und Freerouting
    routet sonst bis fast an die Kante (gemessen: 0,28 mm statt 0,5 mm).
    Ein Boundary-Shrink hat sich als falscher Weg erwiesen: Er sperrt
    ueberhaengende Steckerpads komplett aus und wuergt die Randkorridore
    zwischen den Tastern ab. Der Annulus-Keepout laesst Pads und Korridore
    intakt; `slit` (Winkelpaar) laesst einen Sektor frei - beim Top-Board
    der USB-C-Stecker bei 270 Grad, dessen Pads ueber die Kante ragen.
    Zwei ueberlappende Halbringe, weil ein geschlossener Ring kein
    einfaches Polygon ist.
    """
    if slit is None:
        arcs = [(0.0, 185.0), (180.0, 365.0)]
    else:
        s0, s1 = slit
        arcs = [(s1, (s0 + 360.0 + s1) / 2.0 + 2.5),
                ((s0 + 360.0 + s1) / 2.0 - 2.5, s0 + 360.0)]
    # Alle Kupferlagen aus dem DSN, nicht nur F/B. Bis zum 17.08.2026 stand
    # hier ("F.Cu", "B.Cu") fest - mit der Umstellung auf vier Lagen routete
    # Freerouting auf In1/In2 bis an die Kante und erzeugte vier
    # copper_edge_clearance-Verletzungen, die es auf den Aussenlagen nicht gab.
    layers = re.findall(r'\(layer (\S+)\s*\n\s*\(type signal\)', src)
    if not layers:
        layers = ["F.Cu", "B.Cu"]
    blocks = []
    for i, (a0, a1) in enumerate(arcs):
        for layer in layers:
            blocks.append('    (keepout "ring_%d_%s" (polygon %s 0 %s))'
                          % (i, layer, layer, _ring_polygon(a0, a1)))
    m = re.search(r'\(boundary', src)
    depth = 0
    for i in range(m.start(), len(src)):
        if src[i] == "(":
            depth += 1
        elif src[i] == ")":
            depth -= 1
            if depth == 0:
                break
    return src[:i + 1] + "\n" + "\n".join(blocks) + src[i + 1:]


def patch_dsn(path, classes, slit=None):
    src = open(path, encoding="utf-8").read()
    src = _edge_ring(src, slit=slit)

    via_std, via_pwr = _via_names(src)

    # 1. Groessere Via-Definition ergaenzen (Kopie der Standarddefinition)
    m = re.search(r'\(padstack "%s"' % re.escape(via_std), src)
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
    src = src.replace('(via "%s")' % via_std,
                      '(via "%s" "%s")' % (via_std, via_pwr), 1)

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
        # Die CLASSES-Tabelle nennt die Vias mit den zweilagigen Namen; hier
        # auf den tatsaechlichen Lagenbereich des DSN umschreiben.
        via = {VIA_STD: via_std, VIA_PWR: via_pwr}.get(via, via)
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


# Seit der Umstellung auf vier Lagen (17.08.2026) liefert die SES auch
# In1.Cu und In2.Cu. Fehlten sie hier, brach der Import mit KeyError ab -
# nach zwoelf Minuten Rechenzeit und mit fertiger SES auf der Platte.
LAYERS = {"F.Cu": pcbnew.F_Cu, "In1.Cu": pcbnew.In1_Cu,
          "In2.Cu": pcbnew.In2_Cu, "B.Cu": pcbnew.B_Cu}


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


# Zeitgrenzen sind ueber die Umgebung uebersteuerbar - im Container laeuft
# alles langsamer, und ein abgelaufener Timeout kostet den ganzen Lauf: Der
# Client wird abgeraeumt, der Container laeuft weiter, und Java stirbt beim
# Aufraeumen. Das Zwischenergebnis ist dann verloren.
def route(name, passes=None, timeout=None):
    passes = passes or int(os.environ.get("SWITCHSTACK_ROUTE_PASSES", 200))
    timeout = timeout or int(os.environ.get("SWITCHSTACK_ROUTE_TIMEOUT", 2400))
    os.makedirs(SCRATCH, exist_ok=True)
    pcb = os.path.join(ROOT, "hardware", name, name + ".kicad_pcb")
    dsn = os.path.join(SCRATCH, name + ".dsn")
    ses = os.path.join(SCRATCH, name + ".ses")

    board = pcbnew.LoadBoard(pcb)
    # vorhandene Leiterbahnen/Vias entfernen - der Lauf ist reproduzierbar
    for t in list(board.GetTracks()):
        board.Remove(t)
    pcbnew.ExportSpecctraDSN(board, dsn)
    # Top: Schlitz im Ring-Keepout am USB-C-Sektor (270 Grad), dessen
    # Pads beabsichtigt ueber die Boardkante ragen
    patch_dsn(dsn, CLASSES.get(name, {}),
              slit=(257.0, 283.0) if name == "top_ui" else None)
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
    cmd, wie = freerouting_cmd(dsn, ses, passes)
    print("%-20s Freerouting %s, %d Passes" % (name, wie, passes))
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

    # Zonen fuellen - der fehlende Schritt bis zum 17.08.2026.
    #
    # KiCads Specctra-Export kennt keine Kupferflaechen (im DSN steht kein
    # einziges "plane"), der Router loest PGND also mit Leiterbahnen auf. Was
    # er dabei nicht schafft, faengt die Flaeche auf - aber nur, wenn sie
    # gefuellt wird. Ungefuellt meldet die DRC jede Masseverbindung als offen,
    # und genau so sahen Mid und Top monatelang aus: 76 der 209 gemeldeten
    # offenen Verbindungen waren nur diese fehlende Fuellung.
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    pcbnew.SaveBoard(pcb, board)

    # board.GetTracks() liefert nach SaveBoard gelegentlich ein nicht
    # iterierbares SWIG-Objekt - die Zaehlung kommt daher aus import_ses
    print("%-20s geroutet: %d Bahnsegmente, %d Vias"
          % (name, n_wires, n_vias))
    return pcb


def classify_unrouted(rpt_path):
    """Unverbundene Paare nach Netz zaehlen (ein Eintrag je Verletzung)."""
    txt = open(rpt_path, encoding="utf-8").read()
    counts = {}
    for block in txt.split("[unconnected_items]")[1:]:
        m = re.search(r'@\([^)]*\): [^\[]*\[(\w+)\]', block)
        net = m.group(1) if m else "?"
        counts[net] = counts.get(net, 0) + 1
    return counts


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    fail = 0
    for name in ("bottom_power_motor", "mid_logic", "top_ui"):
        key = name.split("_")[0] if name != "top_ui" else "top"
        if which not in ("all", key):
            continue
        # Bottom: 102 Bauteile und breite Leistungsbahnen - braucht laenger
        pcb = route(name,
                    timeout=int(os.environ.get(
                        "SWITCHSTACK_ROUTE_TIMEOUT",
                        7200 if name == "bottom_power_motor" else 2400)))
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
        # USB-Steckerueberhang am Top-Board ist beabsichtigt: J1-Pads
        # ragen ueber die Kante, und ihre Anschluss-Stubs in der
        # Steckerzunge (|x| <= 5,3, y >= 23,8) koennen den Randabstand
        # strukturell nicht einhalten.
        if name == "top_ui" and "copper_edge_clearance" in vio:
            waived = 0
            rpt_txt = open("/tmp/drc_%s.rpt" % name, encoding="utf-8").read()
            for m in re.finditer(
                    r'\[copper_edge_clearance\][^\n]*\n[^\n]*\n[^\n]*\n'
                    r'\s*@\(([-0-9.]+) mm, ([-0-9.]+) mm\)', rpt_txt):
                if abs(float(m.group(1))) <= 5.3 and float(m.group(2)) >= 23.8:
                    waived += 1
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
