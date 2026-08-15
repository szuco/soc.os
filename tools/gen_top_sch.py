#!/usr/bin/env python3
"""
Erzeugt den Schaltplan des Top-Boards (USB-C, Taster, Sensorik, Display, Stern).

    python3 tools/gen_top_sch.py

Wie bei Bottom und Mid: Konnektivitaet als Quelltext, Netzlisten-Rueckvergleich
mit kicad-cli, keine Schaltungsreview.

Besonderheiten:
  * USB-C haengt am NATIVEN USB des ESP32-S3 auf dem Mid-Board. D+/D- laufen
    ueber J_STK_A 34/36 durch den Stack (siehe stack_pinout.py, v0.3).
  * Der Stern-Ausgang sitzt hier (Frontanschluss laut Frontplatte) und wird
    per High-Side-P-FET geschaltet; STAR_EN kommt vom I2C-Expander des
    Mid-Boards ueber den Stack.
  * Vier Ecktaster unter den Druckkreuzen der Zentralscheibe 6435-914, bei
    (+/-18,0 / +/-20,0) mm. Jede Bedienrichtung ist ein Paar benachbarter
    Ecken - die Aufloesung macht die Firmware.
  * Displaymodul ueber Steckerleiste - Footprint ist PLATZHALTER, bis das
    reale ST77916-Modul mit seinem FPC vermessen ist.
"""

import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kisch import Schematic, symbol_pins                       # noqa: E402
from stack_pinout import connect_stack                         # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "hardware", "top_ui", "top_ui.kicad_sch")

R0603 = "Resistor_SMD:R_0603_1608Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"

NC_ALLOWED = {
    ("J1", "A8"), ("J1", "B8"),      # SBU1/SBU2 - bei USB 2.0 unbenutzt
    ("J6", "TN"),                    # Schaltkontakt der Klinke, absichtlich offen
    ("U3", "8"),                     # VL53L1X DNC - laut Datenblatt offen lassen
}


def build():
    s = Schematic("top_ui", "SwitchStack TOP - Front / UI", paper="A2")

    # =====================================================================
    # 1. USB-C (Device/UFP, nur USB 2.0)
    # =====================================================================
    s.add("J1", "Connector:USB_C_Receptacle_USB2.0_16P", "USB-C",
          "Connector_USB:USB_C_Receptacle_GCT_USB4085",
          MPN="16-Pin-Typ, nur USB 2.0")
    s.connect("USB_VBUS", ("J1", "A4"), ("J1", "B4"), ("J1", "A9"), ("J1", "B9"))
    # Schirm: KiCad 9 nannte den Pin S1, KiCad 10 nennt ihn SH - Symbol und
    # Footprint sind innerhalb einer Version konsistent, deshalb hier abfragen.
    shield = "SH" if "SH" in symbol_pins("Connector:USB_C_Receptacle_USB2.0_16P") else "S1"
    s.connect("PGND",     ("J1", "A1"), ("J1", "B1"), ("J1", "A12"), ("J1", "B12"),
              ("J1", shield))
    s.connect("USB_CC1",  ("J1", "A5"))
    s.connect("USB_CC2",  ("J1", "B5"))
    s.connect("USB_DP_C", ("J1", "A6"), ("J1", "B6"))
    s.connect("USB_DN_C", ("J1", "A7"), ("J1", "B7"))

    # CC: je 5,1 k einzeln nach GND -> UFP/Device
    s.add("R1", "Device:R", "5k1", R0603)
    s.connect("USB_CC1", ("R1", "1"))
    s.connect("PGND",    ("R1", "2"))
    s.add("R2", "Device:R", "5k1", R0603)
    s.connect("USB_CC2", ("R2", "1"))
    s.connect("PGND",    ("R2", "2"))

    # ESD direkt an der Buchse; danach in den Stack
    s.add("U1", "Power_Protection:USBLC6-2SC6", "USBLC6-2SC6",
          "Package_TO_SOT_SMD:SOT-23-6")
    s.connect("USB_DN_C", ("U1", "1"))
    s.connect("PGND",     ("U1", "2"))
    s.connect("USB_DP_C", ("U1", "3"))
    s.connect("USB_DP",   ("U1", "4"))
    s.connect("USB_VBUS", ("U1", "5"))
    s.connect("USB_DN",   ("U1", "6"))

    # =====================================================================
    # 2. Vier Ecktaster unter den Druckkreuzen der Zentralscheibe
    # =====================================================================
    # Die Busch-Jaeger Zentralscheibe 6435-914 traegt die Symbole auf den
    # ACHSEN, gibt den Druck aber ueber vier Kreuze an den ECKEN weiter
    # (gemessen: +/-18,0 / +/-20,0 mm von der Plattenmitte). Ein Kreuz ist
    # 3,2 mm gross und trifft genau EINEN Taster - die frueheren acht
    # parallelgeschalteten Taster der Sichelkappen sind damit hinfaellig.
    #
    # Jede Bedienrichtung ist ein PAAR benachbarter Ecken; die Aufloesung
    # macht die Firmware:
    #     hoch   = BTN1 + BTN2      runter = BTN3 + BTN4
    #     links  = BTN2 + BTN3      OK     = BTN1 + BTN4
    # Siehe docs/04-mechanical.md Abschnitt 1d und firmware/README.md.
    for n, ecke in ((1, "oben rechts"), (2, "oben links"),
                    (3, "unten links"), (4, "unten rechts")):
        ref = "SW%d" % n
        s.add(ref, "Switch:SW_Push", "BTN%d" % n,
              "Button_Switch_SMD:SW_Push_SPST_NO_Alps_SKRK",
              MPN="Alps SKRK o.ae., 3,9x2,9 - Ecke %s, unter dem Druckkreuz "
                  "der Zentralscheibe" % ecke)
        s.connect("BTN%d" % n, (ref, "1"))
        s.connect("PGND",      (ref, "2"))

    # =====================================================================
    # 3. Temperatur/Feuchte SHT4x
    # =====================================================================
    s.add("U2", "Sensor_Humidity:SHT4x", "SHT40-AD1B",
          "Sensor_Humidity:Sensirion_DFN-4_1.5x1.5mm_P0.8mm_SHT4x_NoCentralPad",
          MPN="Adresse 0x44 - muss zur YAML passen; thermisch vom Board entkoppeln (Schlitze)")
    s.connect("I2C_SDA", ("U2", "1"))
    s.connect("I2C_SCL", ("U2", "2"))
    s.connect("3V3_SYS", ("U2", "3"))
    s.connect("PGND",    ("U2", "4"))
    s.add("C1", "Device:C", "100n", C0603)
    s.connect("3V3_SYS", ("C1", "1"))
    s.connect("PGND",    ("C1", "2"))

    # =====================================================================
    # 4. Displayanschluss ST77916 (PLATZHALTER-Footprint)
    # =====================================================================
    # Display: 1,69" 240x280 (ST7789), QUER eingebaut. Der Fensterausschnitt der
    # Zentralscheibe misst gemessene 32,70 x 27,00 mm; die aktive Flaeche des
    # Panels ist 32,63 x 27,97 - in der Breite bleiben 0,07 mm, in der Hoehe
    # verdeckt das Fenster einen halben Millimeter je Seite. Punkt 43.
    #
    # Der ST7789 ist ein 4-Draht-SPI-Display, kein QSPI. Die Netznamen am Stack
    # bleiben trotzdem QSPI_*: Sie laufen ueber J_STK_B durch ALLE drei Boards,
    # und eine Umbenennung wuerde auch den Bottom-Schaltplan aendern - dessen
    # Layout traegt 985 Leiterbahnen. Belegung deshalb per Kommentar:
    #     QSPI_CLK -> SCK      QSPI_D0 -> MOSI/SDA     QSPI_D1 -> DC
    #     QSPI_D2, QSPI_D3 -> frei (Reserve am Stack)
    s.add("J5", "Connector_Generic:Conn_01x10", "ST7789 240x280",
          "Connector_PinHeader_1.27mm:PinHeader_1x10_P1.27mm_Vertical",
          MPN="PLATZHALTER - reales Modul mit FPC vermessen, dann Footprint "
              "und Pinzahl tauschen (Module haben meist 8 Pins)")
    s.connect("3V3_SYS",  ("J5", "1"))
    s.connect("PGND",     ("J5", "2"))
    s.connect("QSPI_CLK", ("J5", "3"))    # SCK
    s.connect("QSPI_D0",  ("J5", "4"))    # MOSI / SDA
    s.connect("QSPI_D1",  ("J5", "5"))    # DC
    s.connect("QSPI_D2",  ("J5", "6"))    # frei
    s.connect("QSPI_D3",  ("J5", "7"))    # frei
    s.connect("DISP_CS",  ("J5", "8"))
    s.connect("DISP_RST", ("J5", "9"))
    s.connect("DISP_BL",  ("J5", "10"))

    # =====================================================================
    # 5. Stern-Ausgang: High-Side-P-FET, geschaltet ueber STAR_EN
    # =====================================================================
    s.add("Q1", "SwitchStack:Q_NPN_BCE", "BC847", "Package_TO_SOT_SMD:SOT-23")
    s.add("R3", "Device:R", "10k", R0603)
    s.connect("STAR_EN", ("R3", "1"))
    s.connect("STAR_B",  ("R3", "2"))
    s.connect("STAR_B",  ("Q1", "1"))
    s.connect("STAR_G",  ("Q1", "2"))
    s.connect("PGND",    ("Q1", "3"))
    s.add("Q2", "SwitchStack:Q_PMOS_GSD", "P-FET 20V 1A", "Package_TO_SOT_SMD:SOT-23",
          MPN="z.B. AO3401 - 80 mA Last, unkritisch")
    s.connect("STAR_G",      ("Q2", "1"))
    s.connect("6V2_STAR_F",  ("Q2", "2"))
    s.connect("STAR_OUT",    ("Q2", "3"))
    s.add("R4", "Device:R", "100k", R0603, MPN="Gate-Pull-up: aus ohne Ansteuerung")
    s.connect("6V2_STAR_F", ("R4", "1"))
    s.connect("STAR_G",     ("R4", "2"))
    # Bulk vor der Sicherung: die Ladestromspitze soll nicht durch den PTC
    s.add("C2", "Device:C", "22u", "Capacitor_SMD:C_1210_3225Metric")
    s.connect("STAR_SW", ("C2", "1"))
    s.connect("PGND",    ("C2", "2"))
    # Eine Klinkenbuchse schliesst beim Stecken kurz Tip gegen Sleeve. F2 unten
    # auf dem Bottom-Board loest dafuer zu langsam aus, deshalb ein PTC direkt
    # an der Buchse.
    s.add("F1", "Device:Polyfuse", "0,2 A PTC", "Fuse:Fuse_1206_3216Metric",
          MPN="Haltestrom > 100 mA, Ausloesestrom < 400 mA")
    s.connect("STAR_SW",  ("F1", "1"))
    s.connect("STAR_OUT", ("F1", "2"))

    # Klinkenbuchse in der Frontplatte, 6 Uhr. Der Schaltkontakt TN bleibt
    # offen - "Stern gesteckt" waere ein zusaetzlicher Stackpin und ein GPIO,
    # dafuer ist die Funktion zu klein.
    s.add("J6", "Connector_Audio:AudioJack2_SwitchT", "Stern Klinke",
          "Connector_Audio:Jack_3.5mm_QingPu_WQP-PJ398SM_Vertical_CircularHoles",
          MPN="PLATZHALTER 3,5 mm vertikal - Zielteil 2,5 mm, Bauhoehe max 10,5 mm "
              "ueber der Platine, Footprint aus dem Datenblatt uebernehmen")
    s.connect("STAR_OUT", ("J6", "T"))
    s.connect("PGND",     ("J6", "S"))

    # =====================================================================
    # 6. Praesenz: VL53L1X (ToF) und Reserveanschluss fuer ein Satellitenmodul
    #
    # Der Sensor sitzt auf 12 Uhr am Boardrand und schaut durch ein konisches
    # Loch in der Frontplatte. In der Fensterlaibung montiert misst er quer
    # durch die Oeffnung: Baseline = gegenueberliegende Laibung, alles Naehere
    # steht in der Oeffnung. Damit deckt ein Bauteil zwei Funktionen ab -
    # Display aufwecken und Durchstieg melden.
    # =====================================================================
    s.add("U3", "Sensor_Distance:VL53L1CXV0FY1", "VL53L1X",
          "Sensor_Distance:ST_VL53L1x",
          MPN="Optikfenster freihalten, Uebersprechen: Loch konisch aufweiten")
    s.connect("3V3_SYS", ("U3", "1"), ("U3", "11"))          # AVDDVCSEL, AVDD
    s.connect("PGND",    ("U3", "2"), ("U3", "3"), ("U3", "4"),
              ("U3", "6"), ("U3", "12"))
    s.connect("TOF_XSHUT",   ("U3", "5"))
    s.connect("PRESENCE_INT", ("U3", "7"))                   # GPIO1
    s.connect("I2C_SDA", ("U3", "9"))
    s.connect("I2C_SCL", ("U3", "10"))
    s.add("R5", "Device:R", "10k", R0603, MPN="XSHUT-Pullup: Sensor immer aktiv")
    s.connect("3V3_SYS",   ("R5", "1"))
    s.connect("TOF_XSHUT", ("R5", "2"))
    s.add("C3", "Device:C", "100n", C0603)
    s.connect("3V3_SYS", ("C3", "1"))
    s.connect("PGND",    ("C3", "2"))
    s.add("C4", "Device:C", "4u7", C0603)
    s.connect("3V3_SYS", ("C4", "1"))
    s.connect("PGND",    ("C4", "2"))

    # J7 bleibt als unbestueckter Reserveanschluss stehen: UART und Interrupt
    # liegen ohnehin auf dem Stack, damit bleibt ein Satellitensensor moeglich,
    # ohne das Pinout zu aendern.
    s.add("J7", "Connector_Generic:Conn_01x05", "Reserve UART",
          "Connector_JST:JST_PH_B5B-PH-K_1x05_P2.00mm_Vertical",
          MPN="DNP - Reserve fuer ein Satellitenmodul")
    s.connect("3V3_SYS",      ("J7", "1"))
    s.connect("PGND",         ("J7", "2"))
    s.connect("UART_AUX_TX",  ("J7", "3"))
    s.connect("UART_AUX_RX",  ("J7", "4"))
    s.connect("PRESENCE_INT", ("J7", "5"))

    # =====================================================================
    # 7. Stackverbinder - identische Quelle wie Bottom/Mid
    # =====================================================================
    connect_stack(s)

    return s


def _sexpr(src):
    tok = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', src)
    stack, cur = [], []
    for t in tok:
        if t == '(':
            stack.append(cur); cur = []
        elif t == ')':
            done, cur = cur, stack.pop(); cur.append(done)
        elif t.startswith('"'):
            cur.append(t[1:-1].replace('\\"', '"'))
        else:
            cur.append(t)
    return cur[0] if len(cur) == 1 else cur


def _walk(node, tag):
    if isinstance(node, list):
        if node and node[0] == tag:
            yield node
        for x in node:
            yield from _walk(x, tag)


def read_netlist(path):
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


def verify(s, out):
    netfile = "/tmp/top.net"
    r = subprocess.run(["kicad-cli", "sch", "export", "netlist",
                        "-o", netfile, out], capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(netfile):
        return ["kicad-cli: " + (r.stdout + r.stderr).strip()[:200]]
    got = read_netlist(netfile)
    want = {n: set(p) for n, p in s.nets.items() if p}
    errs = []
    for net, pins in sorted(want.items()):
        if net not in got:
            errs.append("Netz %s fehlt" % net)
        elif got[net] != pins:
            errs.append("Netz %s: fehlt %s, zusaetzlich %s"
                        % (net, sorted(pins - got[net]) or "-",
                           sorted(got[net] - pins) or "-"))
    for net in sorted(got):
        if net not in want and not net.startswith("unconnected-"):
            errs.append("unerwartetes Netz %s" % net)
    used = {p for pins in want.values() for p in pins}
    for c in s.components:
        for num in symbol_pins(c.lib_id):
            if (c.ref, num) not in used and (c.ref, num) not in NC_ALLOWED:
                errs.append("offener Pin %s.%s" % (c.ref, num))
    return errs


def main():
    s = build()
    s.write(OUT)
    print("Schaltplan   : %s" % os.path.relpath(OUT, ROOT))
    print("Bauteile     : %d" % len(s.components))
    print("Netze        : %d" % len(s.nets))
    errs = verify(s, OUT)
    for e in errs:
        print("  FEHLER: %s" % e)
    print("Netzlistenvergleich: %s"
          % ("BESTANDEN" if not errs else "%d Abweichungen" % len(errs)))
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
