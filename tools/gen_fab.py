#!/usr/bin/env python3
"""
Erzeugt die Fertigungsdaten fuer die drei SwitchStack-Boards.

    xvfb-run -a python3 tools/gen_fab.py [bottom|mid|top]

Je Board:
  1. Massezonen fuellen (ZONE_FILLER braucht ein X-Display, daher xvfb-run;
     ohne Display startet sich das Skript selbst unter xvfb-run neu)
  2. DRC-Gate: keine Kupferfehler, keine offenen Verbindungen -
     sonst werden KEINE Fertigungsdaten geschrieben
  3. Gerber (9 Lagen), Excellon-Bohrdaten, Positionsdatei (CSV, mm)
  4. ZIP zum Hochladen beim Fertiger: hardware/fab/<board>.zip

Zusaetzlich entstehen die Stuecklisten aller drei Boards neben den
Schaltplaenen (bom_bottom/mid/top.csv) - aus derselben Quelle wie die
Schaltplaene selbst.

Waiver wie in route_boards.py: Randabstandsfehler in der USB-Steckerzunge
des Top-Boards (|x| <= 5,3 mm, y >= 23,8 mm) sind beabsichtigt - die
Steckerpads ragen ueber die Boardkante.
"""

import os
import re
import shutil
import subprocess
import sys
import zipfile

# ZONE_FILLER stuerzt ohne X-Display ab (KiCad 7, headless) - unter
# xvfb-run funktioniert er. Ohne DISPLAY starten wir uns selbst neu.
# Unter KiCad 7 stuerzte ZONE_FILLER ohne X-Display ab, deshalb startete sich
# das Skript unter xvfb-run neu. Mit KiCad 10 laeuft er headless durch, und
# auf macOS gibt es xvfb-run gar nicht. Nur noch versuchen, wenn es da ist.
if not os.environ.get("DISPLAY") and shutil.which("xvfb-run"):
    os.execvp("xvfb-run", ["xvfb-run", "-a", sys.executable] + sys.argv)

import pcbnew  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_layouts import run_drc                                 # noqa: E402
from route_boards import classify_unrouted                      # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAB = os.path.join(ROOT, "hardware", "fab")

# Seit dem 17.08.2026 sind alle Boards VIERLAGIG - In1 und In2 muessen mit,
# sonst fehlen dem Fertiger zwei Kupferlagen und er baut stillschweigend
# etwas anderes, als der Schaltplan sagt.
LAYERS = ("F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,"
          "F.Mask,B.Mask,Edge.Cuts")

BOARDS = ("bottom_power_motor", "mid_logic", "top_ui")

COSMETIC = ("silk_overlap", "silk_over_copper", "silk_edge_clearance",
            "solder_mask_bridge", "lib_footprint_issues",
            "lib_footprint_mismatch")


def fill_zones(pcb_path):
    board = pcbnew.LoadBoard(pcb_path)
    filler = pcbnew.ZONE_FILLER(board)
    if not filler.Fill(board.Zones()):
        raise RuntimeError("Zonenfuellung fehlgeschlagen: %s" % pcb_path)
    pcbnew.SaveBoard(pcb_path, board)


def drc_gate(name, pcb_path):
    """DRC ausfuehren; harte Fehler beenden den Lauf."""
    res, errs = run_drc(pcb_path)
    if errs:
        raise RuntimeError("DRC nicht ausfuehrbar: %s" % errs[0])
    vio = dict(res["violations"])
    for k in COSMETIC:
        vio.pop(k, None)
    # starved_thermal ist eine Warnung der Zonenfuellung (Waermefallen-
    # Speichen), kein Fertigungshindernis - separat melden
    starved = vio.pop("starved_thermal", 0)

    if name == "top_ui" and "copper_edge_clearance" in vio:
        rpt = open("/tmp/drc_%s.rpt" % name, encoding="utf-8").read()
        waived = 0
        for m in re.finditer(
                r'\[copper_edge_clearance\][^\n]*\n[^\n]*\n[^\n]*\n'
                r'\s*@\(([-0-9.]+) mm, ([-0-9.]+) mm\)', rpt):
            if abs(float(m.group(1))) <= 5.3 and float(m.group(2)) >= 23.8:
                waived += 1
        vio["copper_edge_clearance"] -= waived
        if vio["copper_edge_clearance"] <= 0:
            del vio["copper_edge_clearance"]

    unrouted = classify_unrouted("/tmp/drc_%s.rpt" % name)
    if vio or unrouted:
        raise RuntimeError(
            "%s: DRC nicht sauber - keine Fertigungsdaten. "
            "Verletzungen: %s, offen: %s" % (name, vio, unrouted))
    return starved


def kicad_cli(*args):
    r = subprocess.run(["kicad-cli"] + list(args),
                       capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError("kicad-cli %s:\n%s" % (" ".join(args[:3]),
                                                  r.stderr.strip()[-500:]))


def export_board(name):
    pcb = os.path.join(ROOT, "hardware", name, name + ".kicad_pcb")
    out = os.path.join(FAB, name)
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        os.remove(os.path.join(out, f))

    fill_zones(pcb)
    starved = drc_gate(name, pcb)

    kicad_cli("pcb", "export", "gerbers", "-o", out + "/",
              "--layers", LAYERS, pcb)
    kicad_cli("pcb", "export", "drill", "-o", out + "/",
              "--format", "excellon", "--excellon-units", "mm",
              "--generate-map", "--map-format", "pdf", pcb)
    kicad_cli("pcb", "export", "pos", "-o",
              os.path.join(out, name + "-pos.csv"),
              "--format", "csv", "--units", "mm", "--side", "both", pcb)

    zpath = os.path.join(FAB, name + ".zip")
    if os.path.exists(zpath):
        os.remove(zpath)
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(out)):
            z.write(os.path.join(out, f), f)
    n = len(os.listdir(out))
    print("%-20s %2d Dateien -> %s%s"
          % (name, n, os.path.relpath(zpath, ROOT),
             "  (Warnung: %d starved_thermal)" % starved if starved else ""))


def write_boms():
    from gen_bottom_sch import write_bom
    import gen_bottom_sch, gen_mid_sch, gen_top_sch
    for mod, slug, csvname in (
            (gen_bottom_sch, "bottom_power_motor", "bom_bottom.csv"),
            (gen_mid_sch, "mid_logic", "bom_mid.csv"),
            (gen_top_sch, "top_ui", "bom_top.csv")):
        s = mod.build()
        path = os.path.join(ROOT, "hardware", slug, csvname)
        n = write_bom(s, path)
        print("%-20s %2d Positionen, %3d Bauteile -> %s"
              % (slug, n, len(s.components), os.path.relpath(path, ROOT)))


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    os.makedirs(FAB, exist_ok=True)
    for name in BOARDS:
        key = name.split("_")[0] if name != "top_ui" else "top"
        if which in ("all", key):
            export_board(name)
    if which == "all":
        write_boms()
    return 0


if __name__ == "__main__":
    sys.exit(main())
