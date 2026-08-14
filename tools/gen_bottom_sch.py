#!/usr/bin/env python3
"""
Erzeugt den Schaltplan des Bottom-Boards (24 V, DC/DC, 2 x H-Bruecke).

    python3 tools/gen_bottom_sch.py

Die Konnektivitaet steht hier als Quelltext und wird nach dem Erzeugen mit
kicad-cli als Netzliste zurueckgelesen und gegen genau diese Vorgabe geprueft.

WICHTIG - was dieser Schaltplan ist und was nicht:
  * Er ist netzlistenkorrekt und in KiCad oeffenbar.
  * Er ist NICHT geprueft im Sinne einer Schaltungsreview. Bauteilwerte sind
    berechnet, aber Referenzdesigns der Hersteller sind noch nicht abgeglichen.
  * Vor Fertigung: Pinbelegung jedes ICs gegen das Datenblatt pruefen, die
    Regler nach Hersteller-Referenzlayout aufbauen.

Auslegung nach docs/11-motor-data.md Abschnitt 5: 25 A Blockierstrom
angenommen. Messabhaengig sind nur R_TRIP*, das Software-Soft-Limit und die
Sicherung F1.
"""

import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kisch import Schematic                                    # noqa: E402
from stack_pinout import connect_stack                         # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "hardware", "bottom_power_motor", "bottom_power_motor.kicad_sch")

R0603 = "Resistor_SMD:R_0603_1608Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C1210 = "Capacitor_SMD:C_1210_3225Metric"
SOT23 = "Package_TO_SOT_SMD:SOT-23"
SOIC8 = "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"


def build():
    s = Schematic("bottom_power_motor",
                  "SwitchStack BOTTOM - Power & Motor", paper="A2")

    # =====================================================================
    # 1. Leistungseingang und Schutz
    # =====================================================================
    s.add("J1", "Connector_Generic:Conn_02x03_Odd_Even", "Power/Motor 6p",
          "Connector_Molex:Molex_Micro-Fit_3.0_43045-0600_2x03_P3.00mm_Vertical",
          MPN="Micro-Fit 3.0 2x3 - Strombelastbarkeit pruefen")
    s.connect("24V_IN",  ("J1", "1"))
    s.connect("PGND",    ("J1", "2"))
    s.connect("M1_A",    ("J1", "3"))
    s.connect("M1_B",    ("J1", "4"))
    s.connect("M2_A",    ("J1", "5"))
    s.connect("M2_B",    ("J1", "6"))

    # Sicherung - Wert messabhaengig
    s.add("F1", "Device:Fuse", "15A traege",
          "Fuse:Fuse_Bourns_MF-RG300", MPN="messabhaengig, siehe docs/11")
    s.connect("24V_IN", ("F1", "1"))
    s.connect("24V_F",  ("F1", "2"))

    # TVS gegen Transienten
    s.add("D1", "Device:D_TVS", "SMBJ30A", "Diode_SMD:D_SMB")
    s.connect("24V_F", ("D1", "1"))
    s.connect("PGND",  ("D1", "2"))

    # Verpolschutz: P-MOSFET high-side, Gate ueber R gegen GND, Zener begrenzt Ugs
    s.add("Q1", "Device:Q_PMOS_GSD", "P-FET 60V 60A",
          "Package_TO_SOT_SMD:TO-263-2", MPN="z.B. IRF4905S - bestaetigen")
    s.connect("24V_GATE_P", ("Q1", "1"))
    s.connect("24V_F",      ("Q1", "2"))
    s.connect("24V_PROT",   ("Q1", "3"))
    s.add("R1", "Device:R", "100k", R0603)
    s.connect("24V_GATE_P", ("R1", "1"))
    s.connect("PGND",       ("R1", "2"))
    s.add("D2", "Device:D_Zener", "12V", "Diode_SMD:D_SOD-123")
    s.connect("24V_F",      ("D2", "1"))
    s.connect("24V_GATE_P", ("D2", "2"))

    # Eingangs- und Bulkkondensatoren
    for ref, val, fp in (("C1", "100n", C0603), ("C2", "10u", C1210),
                         ("C3", "470u/35V", "Capacitor_SMD:CP_Elec_10x10.5"),
                         ("C4", "470u/35V", "Capacitor_SMD:CP_Elec_10x10.5")):
        s.add(ref, "Device:C", val, fp)
        s.connect("24V_PROT", (ref, "1"))
        s.connect("PGND",     (ref, "2"))

    # =====================================================================
    # 2. Gate-Versorgung 12 V (IR2104 braucht >= 10 V)
    # =====================================================================
    s.add("R2", "Device:R", "100R", R0603,
          MPN="begrenzt Strom in D3 bei TVS-Ereignis")
    s.connect("24V_PROT", ("R2", "1"))
    s.connect("12V_RAW",  ("R2", "2"))
    s.add("D3", "Device:D_Zener", "27V", "Diode_SMD:D_SOD-123")
    s.connect("12V_RAW", ("D3", "1"))
    s.connect("PGND",    ("D3", "2"))
    s.add("U1", "Regulator_Linear:L78L12_SOT89", "L78L12",
          "Package_TO_SOT_SMD:SOT-89-3", MPN="30 mA Gate-Ladestrom")
    s.connect("12V_RAW", ("U1", "1"))
    s.connect("PGND",    ("U1", "2"))
    s.connect("12V_GATE", ("U1", "3"))
    for ref, net in (("C5", "12V_RAW"), ("C6", "12V_GATE")):
        s.add(ref, "Device:C", "1u", C0603)
        s.connect(net,  (ref, "1"))
        s.connect("PGND", (ref, "2"))

    # =====================================================================
    # 3. DC/DC-Wandler
    # =====================================================================
    def buck_tps54360(u, rail, r_hi, r_lo, l_val, cout, cout_fp):
        """TPS54360: 60 V Eingang, Vref 0,8 V."""
        s.add(u, "Regulator_Switching:TPS54360DDA", "TPS54360",
              "Package_SO:HSOP-8-1EP_3.9x4.9mm_P1.27mm_EP2.4x3.2mm")
        s.connect("24V_PROT", (u, "2"))
        s.connect("PGND",     (u, "7"), (u, "9"))
        s.connect(u + "_SW",   (u, "8"))
        s.connect(u + "_BOOT", (u, "1"))
        s.connect(u + "_FB",   (u, "5"))
        s.connect(u + "_COMP", (u, "6"))
        s.connect(u + "_RT",   (u, "4"))
        s.connect("24V_EN",    (u, "3"))
        # Bootstrap
        s.add(u + "_CB", "Device:C", "100n", C0603)
        s.connect(u + "_BOOT", (u + "_CB", "1"))
        s.connect(u + "_SW",   (u + "_CB", "2"))
        # Speicherdrossel und Freilaufdiode
        s.add(u + "_L", "Device:L", l_val, "Inductor_SMD:L_Bourns-SRP7028A")
        s.connect(u + "_SW", (u + "_L", "1"))
        s.connect(rail,      (u + "_L", "2"))
        s.add(u + "_D", "Device:D_Schottky", "60V 3A", "Diode_SMD:D_SMB")
        s.connect("PGND",    (u + "_D", "1"))
        s.connect(u + "_SW", (u + "_D", "2"))
        # Rueckkopplung
        s.add(u + "_RH", "Device:R", r_hi, R0603)
        s.connect(rail,      (u + "_RH", "1"))
        s.connect(u + "_FB", (u + "_RH", "2"))
        s.add(u + "_RL", "Device:R", r_lo, R0603)
        s.connect(u + "_FB", (u + "_RL", "1"))
        s.connect("PGND",    (u + "_RL", "2"))
        # Frequenz und Kompensation
        s.add(u + "_RT_R", "Device:R", "100k", R0603,
              MPN="fsw ca. 500 kHz - gegen Datenblatt pruefen")
        s.connect(u + "_RT", (u + "_RT_R", "1"))
        s.connect("PGND",    (u + "_RT_R", "2"))
        s.add(u + "_RC", "Device:R", "10k", R0603)
        s.connect(u + "_COMP", (u + "_RC", "1"))
        s.connect(u + "_CZ_N", (u + "_RC", "2"))
        s.add(u + "_CZ", "Device:C", "3n3", C0603)
        s.connect(u + "_CZ_N", (u + "_CZ", "1"))
        s.connect("PGND",      (u + "_CZ", "2"))
        # Ausgangskondensator
        s.add(u + "_CO", "Device:C", cout, cout_fp)
        s.connect(rail,   (u + "_CO", "1"))
        s.connect("PGND", (u + "_CO", "2"))

    # UVLO-Teiler, gemeinsam fuer beide 24-V-Wandler (Start ab ca. 18 V)
    s.add("R3", "Device:R", "392k", R0603)
    s.connect("24V_PROT", ("R3", "1"))
    s.connect("24V_EN",   ("R3", "2"))
    s.add("R4", "Device:R", "88k7", R0603)
    s.connect("24V_EN", ("R4", "1"))
    s.connect("PGND",   ("R4", "2"))

    # 24 V -> 5 V : 0,8 x (1 + 53k6/10k2) = 5,00 V
    buck_tps54360("U2", "5V_BUCK", "53k6", "10k2", "10u", "47u", C1210)
    # 24 V -> 6,2 V : 0,8 x (1 + 68k1/10k0) = 6,25 V
    buck_tps54360("U4", "6V2_STAR", "68k1", "10k0", "33u", "22u", C1210)

    # 5 V -> 3,3 V : TLV62569, Vref 0,6 V -> 0,6 x (1 + 180k/40k2) = 3,29 V
    s.add("U3", "Regulator_Switching:TLV62569DBV", "TLV62569",
          "Package_TO_SOT_SMD:SOT-23-5")
    s.connect("5V_SYS", ("U3", "4"), ("U3", "1"))
    s.connect("PGND",   ("U3", "2"))
    s.connect("U3_SW",  ("U3", "3"))
    s.connect("U3_FB",  ("U3", "5"))
    s.add("L1", "Device:L", "2u2", "Inductor_SMD:L_Bourns-SRP5030T")
    s.connect("U3_SW",   ("L1", "1"))
    s.connect("3V3_SYS", ("L1", "2"))
    s.add("R5", "Device:R", "180k", R0603)
    s.connect("3V3_SYS", ("R5", "1"))
    s.connect("U3_FB",   ("R5", "2"))
    s.add("R6", "Device:R", "40k2", R0603)
    s.connect("U3_FB", ("R6", "1"))
    s.connect("PGND",  ("R6", "2"))
    s.add("C7", "Device:C", "22u", C1210)
    s.connect("3V3_SYS", ("C7", "1"))
    s.connect("PGND",    ("C7", "2"))

    # USB-ORing: 5V_BUCK und USB_VBUS speisen 5V_SYS, keine Rueckspeisung
    for ref, src in (("D4", "5V_BUCK"), ("D5", "USB_VBUS")):
        s.add(ref, "Device:D_Schottky", "40V 3A", "Diode_SMD:D_SMA",
              MPN="Vf klein waehlen - Verlust siehe docs/01")
        s.connect(src,      (ref, "1"))
        s.connect("5V_SYS", (ref, "2"))
    s.add("C8", "Device:C", "22u", C1210)
    s.connect("5V_SYS", ("C8", "1"))
    s.connect("PGND",   ("C8", "2"))

    # Stern-Ausgang mit eigener Absicherung
    s.add("F2", "Device:Polyfuse", "0.5A", "Fuse:Fuse_1812_4532Metric")
    s.connect("6V2_STAR",   ("F2", "1"))
    s.connect("6V2_STAR_F", ("F2", "2"))
    s.add("C9", "Device:C", "22u", C1210)
    s.connect("6V2_STAR_F", ("C9", "1"))
    s.connect("PGND",       ("C9", "2"))
    # Sternstecker sitzt auf dem TOP-Board (Frontanschluss); hier bleibt nur
    # die abgesicherte Schiene 6V2_STAR_F, die ueber J_STK_A nach oben geht.

    # =====================================================================
    # 4. Motorkanaele
    # =====================================================================
    def motor_channel(n, out_a, out_b):
        """Vollbruecke aus 2 x IR2104 + 4 N-FET, Inline-Strommessung,
        Comparator-Fenster und Latch fuer den Hardware-Trip."""
        p = "M%d" % n
        sd = p + "_SD"                       # aktiv low: Endstufe aus

        for leg, (inp, sw) in enumerate((("%s_INA" % p, "%s_SWA" % p),
                                         ("%s_INB" % p, "%s_SWB" % p))):
            tag = "%s%s" % (p, "AB"[leg])
            drv = "U%s_DRV" % tag
            s.add(drv, "Driver_FET:IR2104", "IR2104", SOIC8)
            s.connect("12V_GATE", (drv, "1"))
            s.connect(inp,        (drv, "2"))
            s.connect(sd,         (drv, "3"))
            s.connect("PGND",     (drv, "4"))
            s.connect(tag + "_LO_G", (drv, "5"))
            s.connect(sw,            (drv, "6"))
            s.connect(tag + "_HO_G", (drv, "7"))
            s.connect(tag + "_VB",   (drv, "8"))
            # Bootstrap
            s.add("D_%s_B" % tag, "Device:D_Schottky", "100V 1A",
                  "Diode_SMD:D_SOD-123")
            s.connect("12V_GATE", ("D_%s_B" % tag, "1"))
            s.connect(tag + "_VB", ("D_%s_B" % tag, "2"))
            s.add("C_%s_B" % tag, "Device:C", "100n", C0603)
            s.connect(tag + "_VB", ("C_%s_B" % tag, "1"))
            s.connect(sw,          ("C_%s_B" % tag, "2"))
            # Gate-Widerstaende
            for side in ("HO", "LO"):
                s.add("R_%s_%s" % (tag, side), "Device:R", "10R", R0603)
                s.connect("%s_%s_G" % (tag, side), ("R_%s_%s" % (tag, side), "1"))
                s.connect("%s_%s_GT" % (tag, side), ("R_%s_%s" % (tag, side), "2"))
            # High-Side- und Low-Side-FET
            s.add("Q_%s_H" % tag, "Device:Q_NMOS_GDS", "N-FET 40V 60A",
                  "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
                  MPN="PowerPAK SO-8, Rds<5mOhm - Footprint bestaetigen")
            s.connect("%s_HO_GT" % tag, ("Q_%s_H" % tag, "1"))
            s.connect("24V_PROT",       ("Q_%s_H" % tag, "2"))
            s.connect(sw,               ("Q_%s_H" % tag, "3"))
            s.add("Q_%s_L" % tag, "Device:Q_NMOS_GDS", "N-FET 40V 60A",
                  "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
                  MPN="PowerPAK SO-8, Rds<5mOhm - Footprint bestaetigen")
            s.connect("%s_LO_GT" % tag, ("Q_%s_L" % tag, "1"))
            s.connect(sw,               ("Q_%s_L" % tag, "2"))
            s.connect("PGND",           ("Q_%s_L" % tag, "3"))

        # Inline-Shunt im Zweig A - misst in JEDEM PWM-Zustand
        s.add("R_%s_SH" % p, "Device:R_Shunt", "1m0 1W",
              "Resistor_SMD:R_2512_6332Metric",
              MPN="4-Terminal, Kelvin - Pflicht")
        s.connect(p + "_SWA", ("R_%s_SH" % p, "1"), ("R_%s_SH" % p, "3"))
        s.connect(out_a,      ("R_%s_SH" % p, "2"), ("R_%s_SH" % p, "4"))
        # Zweig B ohne Shunt direkt an den Steckverbinder
        s.add("R_%s_LNK" % p, "Device:R", "0R", R0603,
              MPN="Bruecke, erlaubt spaeteres Auftrennen zur Messung")
        s.connect(p + "_SWB", ("R_%s_LNK" % p, "1"))
        s.connect(out_b,      ("R_%s_LNK" % p, "2"))

        # Strommessverstaerker, bidirektional, aus 3,3 V -> ADC-sicher
        amp = "U%s_CS" % p
        s.add(amp, "Amplifier_Current:INA240A2D", "INA240A2", SOIC8,
              MPN="Pinbelegung gegen Datenblatt pruefen")
        s.connect(p + "_SWA",  (amp, "8"))
        s.connect(out_a,       (amp, "1"))
        s.connect("AGND",      (amp, "2"), (amp, "4"))
        s.connect("3V3_SYS",   (amp, "6"), (amp, "7"))
        s.connect("AGND",      (amp, "3"))
        s.connect(p + "_ISNS", (amp, "5"))
        s.add("C_%s_CS" % p, "Device:C", "100n", C0603)
        s.connect("3V3_SYS", ("C_%s_CS" % p, "1"))
        s.connect("AGND",    ("C_%s_CS" % p, "2"))
        # RC-Filter zum ADC
        s.add("R_%s_F" % p, "Device:R", "1k", R0603)
        s.connect(p + "_ISNS", ("R_%s_F" % p, "1"))
        s.connect("I_SENSE%d" % n, ("R_%s_F" % p, "2"))
        s.add("C_%s_F" % p, "Device:C", "1n", C0603)
        s.connect("I_SENSE%d" % n, ("C_%s_F" % p, "1"))
        s.connect("AGND",          ("C_%s_F" % p, "2"))

        # Fensterkomparator: Trip in beide Stromrichtungen, Ausgaenge offen
        # -> Wire-OR auf eine aktiv-low Leitung
        cmp_ = "U%s_CMP" % p
        s.add(cmp_, "Comparator:LM393", "LM393", SOIC8)
        s.connect("3V3_SYS", (cmp_, "8"))
        s.connect("AGND",    (cmp_, "4"))
        s.connect("V_TRIP_HI", (cmp_, "3"))
        s.connect(p + "_ISNS", (cmp_, "2"))
        s.connect(p + "_TRIP", (cmp_, "1"))
        s.connect(p + "_ISNS", (cmp_, "5"))
        s.connect("V_TRIP_LO", (cmp_, "6"))
        s.connect(p + "_TRIP", (cmp_, "7"))
        s.add("R_%s_PU" % p, "Device:R", "10k", R0603)
        s.connect("3V3_SYS",   ("R_%s_PU" % p, "1"))
        s.connect(p + "_TRIP", ("R_%s_PU" % p, "2"))

        # Latch: Trip setzt asynchron, Reset ueber TRIP_RST und Power-On-RC
        ff = "U%s_FF" % p
        s.add(ff, "74xGxx:74AUP1G74", "74AUP1G74",
              "Package_TO_SOT_SMD:SOT-353_SC-70-5", MPN="D-FF mit PRE und CLR")
        s.connect("AGND",      (ff, "1"), (ff, "2"), (ff, "4"))
        s.connect("3V3_SYS",   (ff, "8"))
        s.connect(p + "_TRIP", (ff, "7"))     # ~PRE, aktiv low
        s.connect("TRIP_CLR",  (ff, "6"))     # ~CLR, aktiv low
        s.connect("HW_TRIP%d" % n, (ff, "5"))
        s.connect(sd,              (ff, "3"))  # ~Q -> SD der Treiber

    motor_channel(1, "M1_A", "M1_B")
    motor_channel(2, "M2_A", "M2_B")

    # Gemeinsame Trip-Schwellen. DIES SIND DIE MESSABHAENGIGEN WERTE.
    # 3,3 V ueber 10k / 40k2 / 10k  ->  HI = 2,75 V, LO = 0,55 V
    # Mit 1 mOhm Shunt und Verstaerkung 50 entspricht das ca. +/- 22 A.
    s.add("R7", "Device:R", "10k0", R0603, MPN="Trip-Schwelle - messabhaengig")
    s.connect("3V3_SYS",   ("R7", "1"))
    s.connect("V_TRIP_HI", ("R7", "2"))
    s.add("R8", "Device:R", "40k2", R0603, MPN="Trip-Schwelle - messabhaengig")
    s.connect("V_TRIP_HI", ("R8", "1"))
    s.connect("V_TRIP_LO", ("R8", "2"))
    s.add("R9", "Device:R", "10k0", R0603, MPN="Trip-Schwelle - messabhaengig")
    s.connect("V_TRIP_LO", ("R9", "1"))
    s.connect("AGND",      ("R9", "2"))

    # Power-On-Reset des Latches
    s.add("R10", "Device:R", "100k", R0603)
    s.connect("3V3_SYS", ("R10", "1"))
    s.connect("TRIP_CLR", ("R10", "2"))
    s.add("C10", "Device:C", "100n", C0603)
    s.connect("TRIP_CLR", ("C10", "1"))
    s.connect("AGND",     ("C10", "2"))
    s.add("R11", "Device:R", "1k", R0603, MPN="Reset vom I2C-Expander")
    s.connect("TRIP_RST", ("R11", "1"))
    s.connect("TRIP_CLR", ("R11", "2"))

    # Sternpunkt AGND / PGND
    s.add("R12", "Device:R", "0R", R0603,
          MPN="einziger Verbindungspunkt Signal- und Leistungsmasse")
    s.connect("AGND", ("R12", "1"))
    s.connect("PGND", ("R12", "2"))

    # =====================================================================
    # 5. Stackverbinder
    # =====================================================================
    connect_stack(s)

    return s


# -------------------------------------------------------------------------
# Verifikation
# -------------------------------------------------------------------------

def _sexpr(src):
    """Minimaler S-Expression-Parser."""
    tok = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', src)
    stack, cur = [], []
    for t in tok:
        if t == '(':
            stack.append(cur)
            cur = []
        elif t == ')':
            done, cur = cur, stack.pop()
            cur.append(done)
        elif t.startswith('"'):
            cur.append(t[1:-1].replace('\\"', '"'))
        else:
            cur.append(t)
    return cur[0] if len(cur) == 1 else cur


def _walk(node, tag):
    """Alle Unterlisten mit dem gegebenen Kopf-Tag."""
    if isinstance(node, list):
        if node and node[0] == tag:
            yield node
        for x in node:
            yield from _walk(x, tag)


def read_netlist(path):
    """{Netzname: {(ref, pin), ...}} aus der von KiCad exportierten Netzliste."""
    tree = _sexpr(open(path, encoding="utf-8").read())
    nets = {}
    for net in _walk(tree, "net"):
        name = None
        for f in net:
            if isinstance(f, list) and f and f[0] == "name":
                name = f[1]
        if name is None:
            continue
        nodes = set()
        for nd in _walk(net, "node"):
            ref = pin = None
            for f in nd:
                if isinstance(f, list) and f:
                    if f[0] == "ref":
                        ref = f[1]
                    elif f[0] == "pin":
                        pin = f[1]
            if ref and pin:
                nodes.add((ref, pin))
        nets[name] = nodes
    return nets


def write_bom(s, path):
    """Stueckliste aus derselben Quelle wie der Schaltplan."""
    import csv
    from collections import defaultdict
    groups = defaultdict(list)
    for c in s.components:
        groups[(c.value, c.footprint, c.fields.get("MPN", ""))].append(c.ref)

    def sortkey(ref):
        m = re.match(r'^([A-Za-z_]+)(\d*)', ref)
        return (m.group(1), int(m.group(2)) if m.group(2) else 0)

    rows = []
    for (val, fp, mpn), refs in groups.items():
        rows.append((len(refs), ",".join(sorted(refs, key=sortkey)), val, fp, mpn))
    rows.sort(key=lambda r: sortkey(r[1].split(",")[0]))
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Menge", "Designator", "Wert", "Footprint", "Hinweis"])
        w.writerows(rows)
    return len(rows)


def main():
    s = build()
    s.write(OUT)
    bom = os.path.join(os.path.dirname(OUT), "bom_bottom.csv")
    n_lines = write_bom(s, bom)
    print("Stueckliste  : %s (%d Positionen)"
          % (os.path.relpath(bom, ROOT), n_lines))
    print("Schaltplan   : %s" % os.path.relpath(OUT, ROOT))
    print("Bauteile     : %d" % len(s.components))
    print("Netze        : %d" % len(s.nets))

    netfile = "/tmp/bottom.net"
    r = subprocess.run(["kicad-cli", "sch", "export", "netlist",
                        "-o", netfile, OUT],
                       capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(netfile):
        print("FEHLER beim Netzlistenexport:", (r.stdout + r.stderr).strip()[:300])
        return 1
    print("kicad-cli    : Netzliste exportiert (Datei ist gueltig)")

    got = read_netlist(netfile)
    want = {n: set(p) for n, p in s.nets.items() if p}

    errs = []
    for net, pins in sorted(want.items()):
        if net not in got:
            errs.append("Netz %s fehlt in der Netzliste" % net)
            continue
        if got[net] != pins:
            miss = pins - got[net]
            extra = got[net] - pins
            errs.append("Netz %s weicht ab: fehlt %s, zusaetzlich %s"
                        % (net, sorted(miss) or "-", sorted(extra) or "-"))
    for net in sorted(got):
        if net not in want and not net.startswith("unconnected-"):
            errs.append("unerwartetes Netz %s" % net)

    # Kein Pin darf mehrfach in verschiedenen Netzen haengen
    seen = {}
    for net, pins in want.items():
        for pin in pins:
            if pin in seen:
                errs.append("Pin %s.%s in zwei Netzen: %s und %s"
                            % (pin[0], pin[1], seen[pin], net))
            seen[pin] = net

    for e in errs:
        print("  FEHLER: %s" % e)
    print("Netzlistenvergleich: %s"
          % ("BESTANDEN" if not errs else "%d Abweichungen" % len(errs)))
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
