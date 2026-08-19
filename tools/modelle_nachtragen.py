#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Traegt Projekt-3D-Modelle in FERTIG geroutete Boards nach.

gen_layouts haengt die Huellkoerper aus hardware/lib/3dmodels beim ERZEUGEN
eines Boards an (_eigenes_modell). Kommt ein Modell spaeter dazu, muesste
das Board neu erzeugt werden - und verloere sein Routing. Dieses Werkzeug
macht dieselbe Verknuepfung nachtraeglich: Fuer jedes Footprint, zu dessen
Namen eine STEP-Datei im Projektordner liegt, wird das Modell gesetzt.

Idempotent; laeuft nach jedem Modell-Neubau (connector_models.py).
"""

import os
import sys

import pcbnew

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELLE = os.path.join(ROOT, "hardware", "lib", "3dmodels")
BOARDS = ("bottom_power_motor", "mid_logic", "top_ui")


def main():
    for name in BOARDS:
        pfad = os.path.join(ROOT, "hardware", name, name + ".kicad_pcb")
        board = pcbnew.LoadBoard(pfad)
        gesetzt = 0
        for fp in board.GetFootprints():
            fpname = str(fp.GetFPID().GetLibItemName())
            step = os.path.join(MODELLE, fpname + ".step")
            if not os.path.exists(step):
                continue
            soll = "${KIPRJMOD}/../lib/3dmodels/" + fpname + ".step"
            models = list(fp.Models())
            if len(models) == 1 and models[0].m_Filename == soll:
                continue
            fp.Models().clear()
            m = pcbnew.FP_3DMODEL()
            m.m_Filename = soll
            m.m_Show = True
            fp.Models().push_back(m)
            gesetzt += 1
        if gesetzt:
            pcbnew.SaveBoard(pfad, board)
        print("%-20s %d Modelle nachgetragen" % (name, gesetzt))
    return 0


if __name__ == "__main__":
    sys.exit(main())
