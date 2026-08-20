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

    # --- Basisbauteile, abgeglichen gegen die JLCPCB-Basisliste (Werte-
    # und MPN-genau, z. B. 0603WAF4022T5E = 40,2 k). Quelle: Community-
    # Scrapes der Basisliste; das Portal prueft jede Nummer beim Upload
    # ohnehin gegen den Lagerbestand. E96-Sonderwerte (10k2, 39R, 53k6,
    # 68k1, 88k7, 392k) und 1210-Kondensatoren sind KEINE Basisteile und
    # bleiben bewusst offen - Extended-Suche im Portal.
    ("0R", "R_0603"): "C21189",
    ("100k", "R_0603"): "C25803",
    ("10k", "R_0603"): "C25804",
    ("10k0", "R_0603"): "C25804",
    ("120R", "R_0603"): "C22787",
    ("180k", "R_0603"): "C22827",
    ("1M", "R_0603"): "C22935",
    ("1k", "R_0603"): "C21190",
    ("330R", "R_0603"): "C23138",
    ("33k0", "R_0603"): "C4216",
    ("40k2", "R_0603"): "C12447",
    ("4k7", "R_0603"): "C23162",
    ("560R", "R_0603"): "C23204",
    ("5k1", "R_0603"): "C23186",
    ("100n", "C_0603"): "C14663",
    ("1n", "C_0603"): "C1588",
    ("1u", "C_0603"): "C15849",
    ("3n3", "C_0603"): "C1613",
    ("4u7", "C_0603"): "C19666",
    ("10u", "C_0805"): "C15850",
    ("40V 3A", "D_SMA"): "C84635",    # SS34
    ("40V", "D_SOD-123"): "C8598",    # B5819W, Schottky-Freilauf am Piezo
    ("ER-TFT1.69-3", "TE_1-1734839-2"): "C3169233",   # Display-FPC-Buchse
    ("10u", "SRP7028A"): "C2687402",  # Bourns SRP7028A-100M
    ("33u", "SRP7028A"): "C2046760",  # Bourns SRP7028A-330M
    ("BC847", "SOT-23"): "C181141",   # BC847C
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
