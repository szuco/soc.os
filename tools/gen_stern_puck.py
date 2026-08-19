#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Die Loetscheibe fuer den Weihnachtsstern - Ø 14 mm, zwei Netze.

Antwort auf die Frage vom 19.08.2026, wie die Steckseite des DCX-909
"qualitativ hochwertig" an die Litzen des Sterns kommt. Die Steckseite ist
ein Platinenbauteil: drei Loetstifte Ø 0,8 (Mitte plus, aussen zweimal
minus, Stiftabstand 3,70 laut Masszeichnung). Litzen direkt an solche
Stifte zu loeten haelt mechanisch nichts aus - jede Bewegung arbeitet in
der Loetstelle.

Diese Scheibe ist der Zwischentraeger:

    DCX-909-Stifte  ->  drei Durchsteckloecher, verloetet
    Litzen          ->  zwei Loetaugen Ø 2,6 mit Fesselbohrungen davor:
                        Litze von hinten durchfaedeln, umschlagen, loeten -
                        die Zugentlastung ist die Bohrung, nicht das Zinn
    danach          ->  Schrumpfschlauch mit Innenkleber ueber alles

Sie wird im selben Fertigungsauftrag mitbestellt - eine Position mehr im
Nutzen, praktisch kostenlos.
"""

import os
import sys

import pcbnew

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "hardware", "stern_puck")

R = 8.0             # Scheibenradius; Ø 14 war zu knapp - die Loetaugen
                    # verletzten den Randabstand
PIN_ABST = 3.70     # Stiftabstand des DCX-909 laut Masszeichnung
PIN_LOCH = 1.1      # Bohrung fuer Stift Ø 0,8
PIN_PAD = 1.6       # nicht groesser: bei 1,85 Stiftabstand beruehren sich
                    # 2,0er Pads bereits - die erste Fassung hatte so drei
                    # Kurzschluesse zwischen Plus und Minus
LITZE_Y = 5.0       # Loetaugen fuer die Litzen
LITZE_X = 2.6
LITZE_LOCH = 1.3
LITZE_PAD = 2.6
# Die Fesselbohrungen sitzen SEITLICH der Bahnfuehrung. Zwischen den Pads
# und den Stiften war fuer ein 1,6er Loch plus 0,25 Lochabstand plus Bahn
# schlicht kein Platz - drei Anlaeufe, drei DRC-Verletzungen.
FESSEL_X = 5.2
FESSEL_Y = 3.4      # Fesselbohrungen: Litze durchfaedeln, dann loeten
FESSEL_LOCH = 1.6


def mm(v):
    return pcbnew.FromMM(float(v))


def pad_tht(fp, nr, x, y, loch, kupfer, net):
    p = pcbnew.PAD(fp)
    p.SetNumber(str(nr))
    p.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
    p.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
    p.SetSize(pcbnew.VECTOR2I(mm(kupfer), mm(kupfer)))
    p.SetDrillSize(pcbnew.VECTOR2I(mm(loch), mm(loch)))
    p.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    p.SetLayerSet(pcbnew.LSET.AllCuMask())
    p.SetNet(net)
    fp.Add(p)
    return p


def main():
    os.makedirs(OUT, exist_ok=True)
    pcb = pcbnew.CreateEmptyBoard()

    plus = pcbnew.NETINFO_ITEM(pcb, "STAR_PLUS")
    minus = pcbnew.NETINFO_ITEM(pcb, "STAR_MINUS")
    pcb.Add(plus)
    pcb.Add(minus)

    # Umriss
    kreis = pcbnew.PCB_SHAPE(pcb)
    kreis.SetShape(pcbnew.SHAPE_T_CIRCLE)
    kreis.SetLayer(pcbnew.Edge_Cuts)
    kreis.SetCenter(pcbnew.VECTOR2I(0, 0))
    kreis.SetEnd(pcbnew.VECTOR2I(mm(R), 0))
    kreis.SetWidth(mm(0.1))
    pcb.Add(kreis)

    fp = pcbnew.FOOTPRINT(pcb)
    fp.SetReference("X1")
    fp.SetValue("DCX-909 + Litzen")
    fp.Reference().SetVisible(False)
    pcb.Add(fp)

    # Stifte des DCX-909: Mitte plus, aussen minus
    pad_tht(fp, 1, 0.0, 0.0, PIN_LOCH, PIN_PAD, plus)
    pad_tht(fp, 2, -PIN_ABST / 2.0, 0.0, PIN_LOCH, PIN_PAD, minus)
    pad_tht(fp, 3, PIN_ABST / 2.0, 0.0, PIN_LOCH, PIN_PAD, minus)

    # Loetaugen fuer die Litzen und die Fesselbohrungen davor
    pad_tht(fp, 4, -LITZE_X, LITZE_Y, LITZE_LOCH, LITZE_PAD, plus)
    pad_tht(fp, 5, LITZE_X, LITZE_Y, LITZE_LOCH, LITZE_PAD, minus)
    for x in (-FESSEL_X, FESSEL_X):
        f = pcbnew.PAD(fp)
        f.SetNumber("")
        f.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        f.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
        f.SetSize(pcbnew.VECTOR2I(mm(FESSEL_LOCH), mm(FESSEL_LOCH)))
        f.SetDrillSize(pcbnew.VECTOR2I(mm(FESSEL_LOCH), mm(FESSEL_LOCH)))
        f.SetPosition(pcbnew.VECTOR2I(mm(x), mm(FESSEL_Y)))
        fp.Add(f)

    # Verbindungen. Die Minus-Brueke zwischen den Aussenstiften laeuft als
    # Bogen UNTER dem Zentralpad hindurch (y = -2,2; die direkte Linie ging
    # mitten durch das Plus-Pad - der Kurzschluss der ersten Fassung).
    # Danach direkte Wege zu den Loetaugen; die Fesselbohrungen liegen
    # seitlich ausserhalb aller Bahnen.
    zuege = [
        ((0.0, 0.0), (-LITZE_X, LITZE_Y), pcbnew.F_Cu, plus),
        ((-PIN_ABST / 2.0, 0.0), (0.0, -2.2), pcbnew.B_Cu, minus),
        ((0.0, -2.2), (PIN_ABST / 2.0, 0.0), pcbnew.B_Cu, minus),
        ((PIN_ABST / 2.0, 0.0), (LITZE_X, LITZE_Y), pcbnew.B_Cu, minus),
    ]
    for (x0, y0), (x1, y1), lage, net in zuege:
        t = pcbnew.PCB_TRACK(pcb)
        t.SetStart(pcbnew.VECTOR2I(mm(x0), mm(y0)))
        t.SetEnd(pcbnew.VECTOR2I(mm(x1), mm(y1)))
        t.SetLayer(lage)
        t.SetWidth(mm(0.8))
        t.SetNet(net)
        pcb.Add(t)

    # Beschriftung: Polung sichtbar, bevor geloetet wird
    for txt, x, y in (("+", -LITZE_X, LITZE_Y + 1.6), ("-", LITZE_X, LITZE_Y + 1.6)):
        t = pcbnew.PCB_TEXT(pcb)
        t.SetText(txt)
        t.SetLayer(pcbnew.F_SilkS)
        t.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        t.SetTextSize(pcbnew.VECTOR2I(mm(1.2), mm(1.2)))
        t.SetTextThickness(mm(0.2))
        pcb.Add(t)

    ziel = os.path.join(OUT, "stern_puck.kicad_pcb")
    pcbnew.SaveBoard(ziel, pcb)
    print("geschrieben : %s" % ziel)
    print("Scheibe     : Ø %.0f mm, 2 Netze, 5 Loetaugen, 2 Fesselbohrungen" % (2 * R))
    return 0


if __name__ == "__main__":
    sys.exit(main())
