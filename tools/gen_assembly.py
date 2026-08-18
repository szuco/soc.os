#!/usr/bin/env python3
"""
Bestueckungsunterlagen fuer die drei SwitchStack-Boards und den Nutzen.

    python3 tools/gen_assembly.py

Erzeugt je Board und fuer den Nutzen:

  <name>-bom-jlcpcb.csv   Stueckliste im JLCPCB-Format
                          (Comment, Designator, Footprint, LCSC Part #)
  <name>-cpl-jlcpcb.csv   Bestueckungsdatei im JLCPCB-Format
                          (Designator, Mid X, Mid Y, Layer, Rotation)
  <name>-bestueckung.pdf  Bestueckungsplan zum Ausdrucken, Ober- und
                          Unterseite getrennt

ABGRENZUNG ZU gen_fab.py
------------------------
gen_fab.py schreibt die eigentlichen Fertigungsdaten (Gerber, Bohrdaten,
ZIP) und haelt dafuer ein DRC-Gate: Solange auch nur eine Verbindung offen
ist, entsteht keine Datei. Das ist richtig so - eine unvollstaendige Platine
darf man nicht versehentlich bestellen.

Die Unterlagen HIER entstehen trotzdem. Sie sind Vorbereitung und Pruefmittel:
Man braucht den Bestueckungsplan, um Bauteile zu kontrollieren, und die
JLCPCB-Listen, um Verfuegbarkeit und Preise zu klaeren - beides lange bevor
das Layout fertig ist. Wer sie mit einer Bestellung verwechselt, merkt es
spaetestens daran, dass gen_fab.py kein ZIP herausgibt.

DREHWINKEL
----------
JLCPCB rechnet Bauteildrehungen gegen die Lage im eigenen Bauteilkatalog,
nicht gegen KiCads Footprint. Fuer viele Bauformen stimmt beides ueberein,
fuer etliche ICs und Steckverbinder nicht. Die hier ausgegebenen Winkel sind
die aus KiCad - sie sind vor der ersten Bestellung anhand der Vorschau im
Bestellportal zu pruefen, Bauteil fuer Bauteil.
"""

import csv
import os
import re
import shutil
import subprocess
import sys

if not os.environ.get("DISPLAY") and shutil.which("xvfb-run"):
    os.execvp("xvfb-run", ["xvfb-run", "-a", sys.executable] + sys.argv)

import pcbnew  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "hardware", "fab", "bestueckung")

QUELLEN = [
    ("bottom_power_motor", "hardware/bottom_power_motor/bottom_power_motor.kicad_pcb"),
    ("mid_logic",          "hardware/mid_logic/mid_logic.kicad_pcb"),
    ("top_ui",             "hardware/top_ui/top_ui.kicad_pcb"),
    ("switchstack_panel",  "hardware/fab/panel/switchstack_panel.kicad_pcb"),
]

# Was nicht bestueckt wird: Bohrungen, Passermarken, Mausbisse, Werkzeug.
KEINE_BAUTEILE = ("H", "MB", "FID", "TOOL", "REF**")

LCSC = re.compile(r'\bC\d{4,}\b')


def ist_bauteil(fp):
    ref = fp.GetReference()
    if not ref or ref in KEINE_BAUTEILE:
        return False
    if re.match(r'^(H|MB|FID|TOOL)\d*$', ref):
        return False
    if re.match(r'^[BMT]_(H|MB|FID|TOOL)\d*$', ref):
        return False
    return len(list(fp.Pads())) > 0


def lcsc_aus(fp):
    """LCSC-Nummer aus den Feldern des Footprints, falls vorhanden."""
    for feld in ("LCSC", "MPN", "Hersteller-Nr"):
        try:
            wert = fp.GetFieldText(feld)
        except Exception:
            wert = ""
        if wert:
            m = LCSC.search(wert)
            if m:
                return m.group(0)
    return ""


def sammeln(pcb):
    board = pcbnew.LoadBoard(pcb)
    mm = pcbnew.ToMM
    zeilen = []
    for fp in board.GetFootprints():
        if not ist_bauteil(fp):
            continue
        p = fp.GetPosition()
        zeilen.append(dict(
            ref=fp.GetReference(),
            wert=fp.GetValue(),
            fp=fp.GetFPIDAsString().split(":")[-1],
            x=mm(p.x),
            y=-mm(p.y),                      # CPL zaehlt y nach oben
            lage="Bottom" if fp.IsFlipped() else "Top",
            rot=fp.GetOrientationDegrees() % 360.0,
            lcsc=lcsc_aus(fp),
        ))
    zeilen.sort(key=lambda z: (z["lage"], z["ref"]))
    return zeilen


def bom_schreiben(pfad, zeilen):
    """Gleiche Bauteile zusammenfassen - JLCPCB erwartet eine Zeile je Typ."""
    gruppen = {}
    for z in zeilen:
        key = (z["wert"], z["fp"], z["lcsc"])
        gruppen.setdefault(key, []).append(z["ref"])
    with open(pfad, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for (wert, fp, lcsc), refs in sorted(gruppen.items()):
            w.writerow([wert, ",".join(sorted(refs)), fp, lcsc])
    return len(gruppen)


def cpl_schreiben(pfad, zeilen):
    with open(pfad, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for z in zeilen:
            w.writerow([z["ref"], "%.4f" % z["x"], "%.4f" % z["y"],
                        z["lage"], "%.1f" % z["rot"]])
    return len(zeilen)


def plan_schreiben(pcb, pfad):
    """Bestueckungsplan als PDF: Umriss, Bestueckungsdruck, Bauteilkoerper."""
    lagen = "F.SilkS,F.Fab,Edge.Cuts,B.SilkS,B.Fab"
    r = subprocess.run(
        ["kicad-cli", "pcb", "export", "pdf", "-o", pfad,
         "--layers", lagen, "--include-border-title", pcb],
        capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        # aeltere kicad-cli kennen --include-border-title nicht
        r = subprocess.run(
            ["kicad-cli", "pcb", "export", "pdf", "-o", pfad,
             "--layers", lagen, pcb],
            capture_output=True, text=True, timeout=300)
    return r.returncode == 0


def main():
    os.makedirs(OUT, exist_ok=True)
    fehlend_gesamt = 0
    for name, rel in QUELLEN:
        pcb = os.path.join(ROOT, rel)
        if not os.path.exists(pcb):
            print("%-20s fehlt" % name)
            continue
        zeilen = sammeln(pcb)
        n_bom = bom_schreiben(os.path.join(OUT, name + "-bom-jlcpcb.csv"), zeilen)
        n_cpl = cpl_schreiben(os.path.join(OUT, name + "-cpl-jlcpcb.csv"), zeilen)
        ok = plan_schreiben(pcb, os.path.join(OUT, name + "-bestueckung.pdf"))
        fehlend = sum(1 for z in zeilen if not z["lcsc"])
        fehlend_gesamt += fehlend
        print("%-20s %3d Bauteile, %2d BOM-Zeilen, Plan %s, ohne LCSC-Nummer: %d"
              % (name, n_cpl, n_bom, "ok" if ok else "FEHLER", fehlend))
    print()
    print("Ausgabe     : %s" % os.path.relpath(OUT, ROOT))
    print("ACHTUNG     : %d Positionen ohne LCSC-Nummer - die muessen vor der "
          "Bestellung ergaenzt werden." % fehlend_gesamt)
    print("ACHTUNG     : Drehwinkel stammen aus KiCad und sind gegen die "
          "Vorschau im Bestellportal zu pruefen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
