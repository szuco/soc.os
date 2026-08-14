#!/usr/bin/env python3
"""
Iteriert die Masse-Verdrahtung eines Boards bis zur Vollstaendigkeit.

    xvfb-run -a python3 tools/gnd_iterate.py <board> [max_runden]

Je Runde: DSN-Export mit bestehender Verdrahtung (type route, Freerouting
darf alles umlegen), plane-Bloecke entfernen (PGND/AGND werden als Netz
geroutet statt nur ueber die Flaechenfuellung), Freerouting, SES-Merge
(Netze im SES ersetzen ihre alten Bahnen), Zonen fuellen, DRC. Abbruch,
sobald keine Verbindung mehr offen ist oder sich nichts mehr verbessert.
"""

import os
import re
import subprocess
import sys

if not os.environ.get("DISPLAY"):
    os.execvp("xvfb-run", ["xvfb-run", "-a", sys.executable] + sys.argv)

import pcbnew  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_layouts import run_drc                                 # noqa: E402
from route_boards import (patch_dsn, import_ses, classify_unrouted,  # noqa
                          _sexpr, _walk, CLASSES, JAR, SCRATCH)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def strip_planes(path):
    src = open(path, encoding="utf-8").read()
    out, i = [], 0
    while True:
        m = re.search(r'\(plane ', src[i:])
        if not m:
            out.append(src[i:])
            break
        start = i + m.start()
        out.append(src[i:start])
        depth = 0
        for j in range(start, len(src)):
            if src[j] == "(":
                depth += 1
            elif src[j] == ")":
                depth -= 1
                if depth == 0:
                    break
        i = j + 1
    open(path, "w", encoding="utf-8").write("".join(out))


def open_count(name, pcb):
    res, errs = run_drc(pcb)
    if errs:
        raise RuntimeError(errs[0])
    un = classify_unrouted("/tmp/drc_%s.rpt" % name)
    return sum(un.values()), un


def iterate(name, max_rounds=3):
    pcb = os.path.join(ROOT, "hardware", name, name + ".kicad_pcb")
    slit = (257.0, 283.0) if name == "top_ui" else None
    best, un = open_count(name, pcb)
    print("Start: %d offen %s" % (best, un))
    for rnd in range(1, max_rounds + 1):
        if best == 0:
            break
        board = pcbnew.LoadBoard(pcb)
        dsn = os.path.join(SCRATCH, "%s_it%d.dsn" % (name, rnd))
        ses = os.path.join(SCRATCH, "%s_it%d.ses" % (name, rnd))
        pcbnew.ExportSpecctraDSN(board, dsn)
        patch_dsn(dsn, CLASSES.get(name, {}), slit=slit)
        strip_planes(dsn)
        log = os.path.join(SCRATCH, "%s_it%d.log" % (name, rnd))
        with open(log, "w") as lf:
            subprocess.run(
                ["xvfb-run", "-a", "java", "-jar", JAR, "-de", dsn,
                 "-do", ses, "-mp", "300", "-dct", "0", "-oit", "1.0"],
                stdout=lf, stderr=subprocess.STDOUT, timeout=4800)
        if not os.path.exists(ses):
            print("Runde %d: kein SES - Abbruch" % rnd)
            break
        tree = _sexpr(open(ses, encoding="utf-8").read())
        nets = {blk[1] for blk in
                _walk(next(_walk(tree, "network_out")), "net")}
        for t in list(board.GetTracks()):
            if t.GetNetname() in nets:
                board.Remove(t)
        w, v = import_ses(board, ses)
        pcbnew.SaveBoard(pcb, board)
        filler = pcbnew.ZONE_FILLER(board)
        filler.Fill(board.Zones())
        pcbnew.SaveBoard(pcb, board)
        cnt, un = open_count(name, pcb)
        print("Runde %d: %d Netze umgelegt (%d Wires/%d Vias) -> %d offen %s"
              % (rnd, len(nets), w, v, cnt, un))
        if cnt >= best:
            print("keine Verbesserung mehr - Ende")
            break
        best = cnt
    return 0 if best == 0 else 1


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "mid_logic"
    rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    sys.exit(iterate(name, rounds))
