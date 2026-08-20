#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Die lebende Arbeitsliste fuer die Handarbeit nach docs/16.

Laeuft die DRC und druckt je Board jede offene Verbindung als Zeile:
Netz, von-Pad, nach-Pad, Koordinaten, Luftlinie. Waehrend der Handarbeit
in KiCad einfach nach jedem Speichern erneut aufrufen - die Liste
schrumpft mit. Bei Null: weiter mit gen_panel/gen_fab/gen_assembly.

    tools/handarbeit_liste.py [board ...]
"""

import json
import math
import re
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
BOARDS = ("top_ui", "mid_logic", "bottom_power_motor")


def pruefe(name):
    pfad = os.path.join(ROOT, "hardware", name, name + ".kicad_pcb")
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        ziel = f.name
    subprocess.run([CLI, "pcb", "drc", "--format", "json", "-o", ziel, pfad],
                   capture_output=True)
    d = json.load(open(ziel))
    os.unlink(ziel)

    err = [v for v in d.get("violations", []) if v.get("severity") == "error"]
    unc = d.get("unconnected_items", [])
    print("=" * 74)
    print("%s   —   Kupferfehler: %d,  offene Verbindungen: %d"
          % (name, len(err), len(unc)))
    for v in err:
        it = v.get("items", [{}])[0]
        pos = it.get("pos", {})
        print("  KUPFERFEHLER %-22s @ %7.2f/%7.2f  %s"
              % (v["type"], pos.get("x", 0), pos.get("y", 0),
                 v["description"][:40]))

    zeilen = []
    for u in unc:
        its = u.get("items", [])
        if len(its) < 2:
            continue
        a, b = its[0], its[1]
        pa, pb = a.get("pos", {}), b.get("pos", {})
        d_mm = math.hypot(pa.get("x", 0) - pb.get("x", 0),
                          pa.get("y", 0) - pb.get("y", 0))
        m = (re.search(r"\[([^\]]+)\]", a.get("description", ""))
             or re.search(r"\[([^\]]+)\]", b.get("description", "")))
        netz = m.group(1) if m else "?"
        zeilen.append((netz, d_mm, a, b))
    zeilen.sort(key=lambda z: (z[0], z[1]))
    for netz, d_mm, a, b in zeilen:
        pa, pb = a.get("pos", {}), b.get("pos", {})
        print("  %-12s %5.1f mm   %-26s (%7.2f/%7.2f) -> %-26s (%7.2f/%7.2f)"
              % (netz, d_mm,
                 a.get("description", "?")[:26], pa.get("x", 0), pa.get("y", 0),
                 b.get("description", "?")[:26], pb.get("x", 0), pb.get("y", 0)))
    return len(err) + len(unc)


def main():
    boards = [b for b in sys.argv[1:] if not b.startswith("-")] or BOARDS
    rest = 0
    for b in boards:
        rest += pruefe(b)
    print("=" * 74)
    if rest == 0:
        print("ALLES ZU — weiter mit: gen_panel.py, gen_fab.py, gen_assembly.py")
    else:
        print("noch offen gesamt: %d  (nach dem Routen einfach erneut aufrufen)" % rest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
