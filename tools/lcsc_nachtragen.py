#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Traegt verifizierte LCSC-Nummern in FERTIG geroutete Boards nach.

Dasselbe Muster wie modelle_nachtragen.py: Die Schaltplan-Generatoren
tragen die Nummern fuer kuenftige Neuerzeugungen, dieses Werkzeug bringt
sie auf Boards, deren Routing man nicht opfern will. gen_assembly liest
das Feld "LCSC" zuerst.

NUR VERIFIZIERTE NUMMERN - jede stammt aus einer nachgeschlagenen
LCSC-Produktseite (20.08.2026). Was hier nicht steht, bleibt bewusst
leer: Eine falsche Nummer bestueckt ein falsches Bauteil.
"""

import os
import sys

import pcbnew

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOARDS = ("bottom_power_motor", "mid_logic", "top_ui")

# (Wert, Footprint-Teilstring) -> LCSC
NUMMERN = {
    ("DRV8871", "HSOP-8"): "C75864",          # DRV8871DDAR
    ("TPS54360", "HSOP-8"): "C44377",         # TPS54360DDAR
    ("TLV62569", "SOT-23-5"): "C141836",      # TLV62569DBVR
    ("INA240A2", "SOIC-8"): "C2060768",       # INA240A2DR
    ("74AHC1G08", "SOT-353"): "C12490",       # 74AHC1G08GW,125
    ("74AUP1G74", "VSSOP-8"): "C140267",      # SN74AUP1G74DCUR
    ("ESP32-S3-WROOM-1-N16R8", "ESP32"): "C2913202",
    ("MAX3485", "SOIC-8"): "C18148",          # MAX3485ESA+T
    ("PCF8575", "SSOP-24"): "C12251",         # PCF8575TS/1,118
    ("USBLC6-2SC6", "SOT-23-6"): "C7519",
    ("SHT40-AD1B", "SHT4x"): "C2909890",      # SHT40-AD1B-R2
    ("USB-C", "GT-USB-7051x"): "C2843970",
    ("Stern (intern)", "SM02B-GHS-TB"): "C189893",
}


def main():
    for name in BOARDS:
        pfad = os.path.join(ROOT, "hardware", name, name + ".kicad_pcb")
        if not os.path.exists(pfad):
            continue
        board = pcbnew.LoadBoard(pfad)
        gesetzt = 0
        for fp in board.GetFootprints():
            wert = fp.GetValue()
            fpn = str(fp.GetFPID().GetLibItemName())
            for (w, teil), nummer in NUMMERN.items():
                if wert == w and teil in fpn:
                    try:
                        alt = fp.GetFieldText("LCSC")
                    except Exception:
                        alt = ""
                    if alt == nummer:
                        break
                    fp.SetField("LCSC", nummer)
                    # UNSICHTBAR: SetField legt sichtbaren Text an - auf
                    # dem Nutzen standen ploetzlich sieben ungespiegelte
                    # C-Nummern im Bestueckungsdruck der Rueckseite.
                    for feld in fp.GetFields():
                        if feld.GetName() == "LCSC":
                            feld.SetVisible(False)
                    gesetzt += 1
                    break
        if gesetzt:
            pcbnew.SaveBoard(pfad, board)
        print("%-20s %d LCSC-Felder gesetzt" % (name, gesetzt))
    return 0


if __name__ == "__main__":
    sys.exit(main())
