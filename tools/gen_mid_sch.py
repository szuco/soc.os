#!/usr/bin/env python3
"""
Erzeugt den Schaltplan des Mid-Boards (ESP32-S3, RS-485, Expander, Piezo).

    python3 tools/gen_mid_sch.py

Wie beim Bottom-Board: Konnektivitaet als Quelltext, danach Netzlisten-
Rueckvergleich mit kicad-cli. Gleiche Vorbehalte - netzlistenkorrekt,
aber keine Schaltungsreview; IC-Pinbelegungen vor Fertigung gegen die
Datenblaetter pruefen.

GPIO-Zuordnung ESP32-S3-WROOM-1-N16R8 (muss mit firmware/esphome/switchstack.yaml
uebereinstimmen - die YAML ist daraus abgeleitet):

  IO1  I_SENSE1 (ADC)     IO13 QSPI_D1           IO40 M2_INA
  IO2  I_SENSE2 (ADC)     IO14 QSPI_D2           IO41 UART_RADAR_RX
  IO4  BTN1               IO15 AUDIO_PWM         IO42 UART_RADAR_TX
  IO5  BTN2               IO16 DISP_RST          IO43 (TXD0) DISP_BL
  IO6  BTN3               IO17 UART485_TX        IO47 M2_INB
  IO7  BTN4               IO18 UART485_RX        IO48 RS485_DIR (DE + /RE)
  IO8  I2C_SDA            IO19 USB_DN
  IO9  I2C_SCL            IO20 USB_DP
  IO10 DISP_CS            IO21 QSPI_D3
  IO11 QSPI_D0            IO38 M1_INA
  IO12 QSPI_CLK           IO39 M1_INB

  Frei/NC: IO0 (BOOT-Taster), IO3, IO45, IO46 (Strapping), IO35-37 (PSRAM!),
  RXD0/IO44. IO35-37 duerfen bei der R8-Variante NICHT beschaltet werden.
"""

import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kisch import Schematic, symbol_pins                       # noqa: E402
from stack_pinout import connect_stack                         # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "hardware", "mid_logic", "mid_logic.kicad_sch")

R0603 = "Resistor_SMD:R_0603_1608Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"

# Absichtlich unbeschaltete Pins (Referenz, Pinnummer im Symbol)
NC_ALLOWED = {
    ("U1", "15"),   # IO3   Strapping, ungenutzt
    ("U1", "16"),   # IO46  Strapping
    ("U1", "26"),   # IO45  Strapping
    ("U1", "28"),   # IO35  PSRAM - MUSS offen bleiben (N16R8)
    ("U1", "29"),   # IO36  PSRAM
    ("U1", "30"),   # IO37  PSRAM
    ("U1", "36"),   # RXD0/IO44 ungenutzt
    ("U3", "13"),   # PCF8574 ~INT - optional, ESPHome pollt
}


def build():
    s = Schematic("mid_logic", "SwitchStack MID - Logic", paper="A2")

    # =====================================================================
    # 1. ESP32-S3-WROOM-1-N16R8
    # =====================================================================
    s.add("U1", "RF_Module:ESP32-S3-WROOM-1", "ESP32-S3-WROOM-1-N16R8",
          "RF_Module:ESP32-S3-WROOM-1",
          MPN="Antenne zeigt zur Front (+Y), Keepout auf allen Lagen")
    s.connect("PGND",    ("U1", "1"), ("U1", "40"), ("U1", "41"))
    s.connect("3V3_SYS", ("U1", "2"))
    s.connect("ESP_EN",  ("U1", "3"))
    # ADC
    s.connect("I_SENSE1", ("U1", "39"))       # IO1
    s.connect("I_SENSE2", ("U1", "38"))       # IO2
    # Taster
    s.connect("BTN1", ("U1", "4"))
    s.connect("BTN2", ("U1", "5"))
    s.connect("BTN3", ("U1", "6"))
    s.connect("BTN4", ("U1", "7"))
    # I2C
    s.connect("I2C_SDA", ("U1", "12"))        # IO8
    s.connect("I2C_SCL", ("U1", "17"))        # IO9
    # Display QSPI
    s.connect("DISP_CS",  ("U1", "18"))       # IO10
    s.connect("QSPI_D0",  ("U1", "19"))       # IO11
    s.connect("QSPI_CLK", ("U1", "20"))       # IO12
    s.connect("QSPI_D1",  ("U1", "21"))       # IO13
    s.connect("QSPI_D2",  ("U1", "22"))       # IO14
    s.connect("QSPI_D3",  ("U1", "23"))       # IO21
    s.connect("DISP_RST", ("U1", "9"))        # IO16
    s.connect("DISP_BL",  ("U1", "37"))       # TXD0 = IO43
    # Audio
    s.connect("AUDIO_PWM", ("U1", "8"))       # IO15
    # RS-485
    s.connect("UART485_TX", ("U1", "10"))     # IO17
    s.connect("UART485_RX", ("U1", "11"))     # IO18
    s.connect("RS485_DIR",  ("U1", "25"))     # IO48
    # Nativer USB
    s.connect("USB_DN", ("U1", "13"))         # IO19
    s.connect("USB_DP", ("U1", "14"))         # IO20
    # Motor
    s.connect("M1_INA", ("U1", "31"))         # IO38
    s.connect("M1_INB", ("U1", "32"))         # IO39
    s.connect("M2_INA", ("U1", "33"))         # IO40
    s.connect("M2_INB", ("U1", "24"))         # IO47
    # Radar-UART
    s.connect("UART_RADAR_RX", ("U1", "34"))  # IO41
    s.connect("UART_RADAR_TX", ("U1", "35"))  # IO42
    # Strapping/Boot
    s.connect("ESP_BOOT", ("U1", "27"))       # IO0

    # Entkopplung direkt am Modul
    for ref, val, fp in (("C1", "10u", C0805), ("C2", "100n", C0603),
                         ("C3", "1u", C0603)):
        s.add(ref, "Device:C", val, fp)
        s.connect("3V3_SYS", (ref, "1"))
        s.connect("PGND",    (ref, "2"))

    # EN: RC-Glied plus Reset-Taster
    s.add("R1", "Device:R", "10k", R0603)
    s.connect("3V3_SYS", ("R1", "1"))
    s.connect("ESP_EN",  ("R1", "2"))
    s.add("C4", "Device:C", "1u", C0603)
    s.connect("ESP_EN", ("C4", "1"))
    s.connect("PGND",   ("C4", "2"))
    s.add("SW1", "Switch:SW_Push", "RESET", "Button_Switch_SMD:SW_SPST_TL3342")
    s.connect("ESP_EN", ("SW1", "1"))
    s.connect("PGND",   ("SW1", "2"))

    # BOOT-Taster (IO0), Pull-up intern vorhanden, extern 10k zur Sicherheit
    s.add("R2", "Device:R", "10k", R0603)
    s.connect("3V3_SYS",  ("R2", "1"))
    s.connect("ESP_BOOT", ("R2", "2"))
    s.add("SW2", "Switch:SW_Push", "BOOT", "Button_Switch_SMD:SW_SPST_TL3342")
    s.connect("ESP_BOOT", ("SW2", "1"))
    s.connect("PGND",     ("SW2", "2"))

    # =====================================================================
    # 2. RS-485 (MAX3485, 3,3 V) mit Fail-Safe-Bias und Anschluss
    # =====================================================================
    s.add("U2", "Interface_UART:MAX3485", "MAX3485",
          "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
          MPN="3,3-V-Typ; Pinbelegung gegen Datenblatt pruefen")
    s.connect("UART485_RX", ("U2", "1"))      # RO -> ESP RX
    s.connect("RS485_DIR",  ("U2", "2"), ("U2", "3"))   # ~RE + DE gemeinsam
    s.connect("UART485_TX", ("U2", "4"))      # DI <- ESP TX
    s.connect("PGND",       ("U2", "5"))
    s.connect("RS485_A",    ("U2", "6"))
    s.connect("RS485_B",    ("U2", "7"))
    s.connect("3V3_SYS",    ("U2", "8"))
    s.add("C5", "Device:C", "100n", C0603)
    s.connect("3V3_SYS", ("C5", "1"))
    s.connect("PGND",    ("C5", "2"))

    # Fail-Safe-Bias: definierter Pegel bei unbelegtem Bus
    s.add("R3", "Device:R", "560R", R0603, MPN="Fail-Safe-Bias A")
    s.connect("3V3_SYS", ("R3", "1"))
    s.connect("RS485_A", ("R3", "2"))
    s.add("R4", "Device:R", "560R", R0603, MPN="Fail-Safe-Bias B")
    s.connect("RS485_B", ("R4", "1"))
    s.connect("PGND",    ("R4", "2"))
    # Terminierung - NUR am Busende bestuecken
    s.add("R5", "Device:R", "120R", R0603,
          MPN="DNP - nur bestuecken, wenn dieses Geraet am Busende sitzt")
    s.connect("RS485_A", ("R5", "1"))
    s.connect("RS485_B", ("R5", "2"))

    # Busanschluss: steckbar, Feldkabel kommt von hinten durch die Dose
    s.add("J4", "Connector_Generic:Conn_01x03", "RS485 A/B/GND",
          "Connector_JST:JST_XH_B3B-XH-A_1x03_P2.50mm_Vertical",
          MPN="Kabel VOR dem Stapeln stecken - Zugaenglichkeit im Review pruefen")
    s.connect("RS485_A", ("J4", "1"))
    s.connect("RS485_B", ("J4", "2"))
    s.connect("PGND",    ("J4", "3"))

    # =====================================================================
    # 3. I2C: Pull-ups und Expander PCF8574 (Adresse 0x20)
    # =====================================================================
    s.add("R6", "Device:R", "4k7", R0603)
    s.connect("3V3_SYS", ("R6", "1"))
    s.connect("I2C_SDA", ("R6", "2"))
    s.add("R7", "Device:R", "4k7", R0603)
    s.connect("3V3_SYS", ("R7", "1"))
    s.connect("I2C_SCL", ("R7", "2"))

    s.add("U3", "Interface_Expansion:PCF8574", "PCF8574",
          "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm",
          MPN="Adresse 0x20: A0=A1=A2=GND - muss zur YAML passen")
    s.connect("PGND",     ("U3", "1"), ("U3", "2"), ("U3", "3"), ("U3", "8"))
    s.connect("3V3_SYS",  ("U3", "16"))
    s.connect("I2C_SCL",  ("U3", "14"))
    s.connect("I2C_SDA",  ("U3", "15"))
    # Portbelegung == YAML: P0/P1 Trip-Eingaenge, P2 Reset, P3 Stern,
    # P4 Radar-Praesenz, P5 Relais, P6/P7 frei auf Loetpads
    s.connect("HW_TRIP1",  ("U3", "4"))
    s.connect("HW_TRIP2",  ("U3", "5"))
    s.connect("TRIP_RST",  ("U3", "6"))
    s.connect("STAR_EN",   ("U3", "7"))
    s.connect("RADAR_INT", ("U3", "9"))
    s.connect("RELAY_CTL", ("U3", "10"))
    s.connect("EXP_P6",    ("U3", "11"))
    s.connect("EXP_P7",    ("U3", "12"))
    s.add("C6", "Device:C", "100n", C0603)
    s.connect("3V3_SYS", ("C6", "1"))
    s.connect("PGND",    ("C6", "2"))
    # Reservepads fuer P6/P7
    s.add("J5", "Connector_Generic:Conn_01x02", "EXP P6/P7",
          "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical")
    s.connect("EXP_P6", ("J5", "1"))
    s.connect("EXP_P7", ("J5", "2"))

    # =====================================================================
    # 4. Piezo-Treiber (passiver Signalgeber an 5V_SYS)
    # =====================================================================
    s.add("Q2", "Device:Q_NPN_BCE", "BC847", "Package_TO_SOT_SMD:SOT-23")
    s.add("R8", "Device:R", "1k", R0603)
    s.connect("AUDIO_PWM", ("R8", "1"))
    s.connect("AUDIO_B",   ("R8", "2"))
    s.connect("AUDIO_B",   ("Q2", "1"))
    s.connect("AUDIO_LOW", ("Q2", "2"))
    s.connect("PGND",      ("Q2", "3"))
    s.add("BZ1", "Device:Buzzer", "Piezo passiv",
          "Buzzer_Beeper:Buzzer_12x9.5RM7.6",
          MPN="passiv - aktiver Summer kann keine rtttl-Melodien")
    s.connect("5V_SYS",   ("BZ1", "1"))
    s.connect("AUDIO_LOW", ("BZ1", "2"))
    # Freilauf ueber dem Piezo (induktive Anteile der Membran)
    s.add("D1", "Device:D_Schottky", "40V", "Diode_SMD:D_SOD-123")
    s.connect("AUDIO_LOW", ("D1", "1"))
    s.connect("5V_SYS",    ("D1", "2"))

    # =====================================================================
    # 5. Stackverbinder - identische Quelle wie Bottom/Top
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
    netfile = "/tmp/mid.net"
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
    # offene Pins gegen die Freigabeliste
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
