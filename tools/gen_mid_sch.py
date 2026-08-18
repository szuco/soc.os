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
  IO2  I_SENSE2 (ADC)     IO14 QSPI_D2           IO41 UART_AUX_RX
  IO4  BTN1               IO15 AUDIO_PWM         IO42 UART_AUX_TX
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
    ("J7", "A8"), ("J7", "B8"),   # SBU1/SBU2 - bei USB 2.0 unbenutzt
    ("U1", "15"),   # IO3   Strapping, ungenutzt
    ("U1", "16"),   # IO46  Strapping
    ("U1", "26"),   # IO45  Strapping
    ("U1", "28"),   # IO35  PSRAM - MUSS offen bleiben (N16R8)
    ("U1", "29"),   # IO36  PSRAM
    ("U1", "30"),   # IO37  PSRAM
    ("U1", "36"),   # RXD0/IO44 ungenutzt
    ("U3", "1"),    # PCF8575 ~INT - optional, ESPHome pollt
    ("U3", "15"), ("U3", "16"), ("U3", "17"),   # P12..P17 Reserve
    ("U3", "18"), ("U3", "19"), ("U3", "20"),
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
    # =====================================================================
    #    USB-C - seit dem 18.08.2026 auf DIESEM Board
    # =====================================================================
    # Sie sass bis dahin auf dem Top-Board und passte dort nicht: Zwischen
    # Top-Platine und Zentralscheibe sind 3,5 mm frei, eine stehende
    # USB-C-Buchse baut 7 bis 9,25 mm. Zwischen Mids Oberseite und Tops
    # Oberseite liegen dagegen 10,0 mm (docs/04, Tiefenbudget) - die Buchse
    # steht hier und greift durch eine Randkerbe des Top-Boards nach vorn.
    # Gesteckt wird weiterhin von vorn, sobald die Zentralscheibe ab ist.
    #
    # Zwei Dinge werden dadurch besser: Der native USB des ESP32-S3 sitzt auf
    # DIESEM Board, die Datenleitungen muessen also nicht mehr ueber zwei
    # Steckkontakte des Stapels - J_STK_A 34/36 sind frei geworden. Und das
    # Top-Board verliert acht offene Netze samt aller Randabstandsfehler.
    s.add("J7", "Connector:USB_C_Receptacle_USB2.0_16P", "USB-C",
          "Connector_USB:USB_C_Receptacle_G-Switch_GT-USB-7051x",
          MPN="G-Switch GT-USB-7051A/B, vertikal SMT (LCSC C2843970)")
    s.connect("USB_VBUS", ("J7", "A4"), ("J7", "B4"), ("J7", "A9"), ("J7", "B9"))
    # Schirm: KiCad 9 nannte den Pin S1, KiCad 10 nennt ihn SH.
    shield = "SH" if "SH" in symbol_pins("Connector:USB_C_Receptacle_USB2.0_16P") else "S1"
    s.connect("PGND",     ("J7", "A1"), ("J7", "B1"), ("J7", "A12"), ("J7", "B12"),
              ("J7", shield))
    s.connect("USB_CC1",  ("J7", "A5"))
    s.connect("USB_CC2",  ("J7", "B5"))
    s.connect("USB_DP_C", ("J7", "A6"), ("J7", "B6"))
    s.connect("USB_DN_C", ("J7", "A7"), ("J7", "B7"))

    # CC: je 5,1 k einzeln nach GND -> UFP/Device
    s.add("R18", "Device:R", "5k1", R0603)
    s.connect("USB_CC1", ("R18", "1"))
    s.connect("PGND",    ("R18", "2"))
    s.add("R19", "Device:R", "5k1", R0603)
    s.connect("USB_CC2", ("R19", "1"))
    s.connect("PGND",    ("R19", "2"))

    # ESD direkt an der Buchse, danach an den Prozessor
    s.add("U5", "Power_Protection:USBLC6-2SC6", "USBLC6-2SC6",
          "Package_TO_SOT_SMD:SOT-23-6")
    s.connect("USB_DN_C", ("U5", "1"))
    s.connect("PGND",     ("U5", "2"))
    s.connect("USB_DP_C", ("U5", "3"))
    s.connect("USB_DP",   ("U5", "4"))
    s.connect("USB_VBUS", ("U5", "5"))
    s.connect("USB_DN",   ("U5", "6"))

    # Motor
    s.connect("M1_INA", ("U1", "31"))         # IO38
    s.connect("M1_INB", ("U1", "32"))         # IO39
    s.connect("M2_INA", ("U1", "33"))         # IO40
    s.connect("M2_INB", ("U1", "24"))         # IO47
    # Reserve-UART (frueher Radar, siehe Stack-Pinout v0.4)
    s.connect("UART_AUX_RX", ("U1", "34"))  # IO41
    s.connect("UART_AUX_TX", ("U1", "35"))  # IO42
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

    # PCF8575 statt PCF8574: Der 8-Bit-Expander war mit P0..P7 restlos
    # belegt, und die Sabotageueberwachung beider Fenster (Punkt 34, am
    # 16.08.2026 entschieden) braucht ZWEI weitere Eingaenge. Ein zweiter
    # PCF8574 auf eigener Adresse waere die Alternative gewesen - der
    # 16-Bit-Typ ist derselbe Treiber, dieselbe Adresse, ein Bauteil statt
    # zwei und im SSOP-24 (5,3 x 8,2) kaum groesser als das alte SOIC-16
    # (3,9 x 9,9). ESPHome kennt ihn als pcf8574 mit pcf8575: true.
    s.add("U3", "Interface_Expansion:PCF8575DBR", "PCF8575",
          "Package_SO:SSOP-24_5.3x8.2mm_P0.65mm",
          MPN="Adresse 0x20: A0=A1=A2=GND - muss zur YAML passen")
    s.connect("PGND",     ("U3", "2"), ("U3", "3"), ("U3", "12"), ("U3", "21"))
    s.connect("3V3_SYS",  ("U3", "24"))
    s.connect("I2C_SCL",  ("U3", "22"))
    s.connect("I2C_SDA",  ("U3", "23"))
    # Portbelegung == YAML: P0/P1 Trip-Eingaenge, P2 Reset, P3 Stern,
    # P4 Praesenz, P5 Haubenkontakt, P6/P7 Verschlusskontakte,
    # P10/P11 (= ESPHome 8/9) Sabotagekontakte. P12..P17 sind Reserve.
    s.connect("HW_TRIP1",  ("U3", "4"))
    s.connect("HW_TRIP2",  ("U3", "5"))
    s.connect("TRIP_RST",  ("U3", "6"))
    s.connect("STAR_EN",   ("U3", "7"))
    s.connect("PRESENCE_INT", ("U3", "8"))
    s.connect("RELAY_CTL", ("U3", "9"))
    s.connect("EXP_P6",    ("U3", "10"))
    s.connect("EXP_P7",    ("U3", "11"))
    s.connect("EXP_P8",    ("U3", "13"))
    s.connect("EXP_P9",    ("U3", "14"))
    s.add("C6", "Device:C", "100n", C0603)
    s.connect("3V3_SYS", ("C6", "1"))
    s.connect("PGND",    ("C6", "2"))

    # =====================================================================
    # 3b. Feldsignale: 2 Reed-Kontakte (Fenster) + Haubenkontakt
    #
    # Reed: Schliesser gegen PGND. Externer 10k-Pullup, weil die
    # Stromquelle im PCF8574 (~100 uA) fuer mehrere Meter Leitung zu
    # schwach ist. 1k Serie + 100n gibt tau = 100 us gegen Prellen und
    # Einstreuung; bei geschlossenem Kontakt liegen 0,3 V am Eingang,
    # also sicher unter VIL = 0,3 x VCC. TVS gegen ESD am Steckverbinder.
    #
    # Haube: PhotoMOS statt Relais - potentialfrei, lautlos, kein
    # Spulenstrom, 4,4 x 2,6 mm statt Relaisbauhoehe im 9-mm-Stapelspalt.
    # NUR FUER SELV. Bei Netzspannung am Haubeneingang gehoert das
    # Schaltglied nicht in diese Dose (siehe docs/06, Punkt 21).
    # PCF8574-Ausgaenge senken kraeftig, sourcen aber kaum: die LED
    # haengt an 3V3 und wird von P5 gegen Masse gezogen -> LOW = EIN,
    # in der YAML als inverted zu fuehren.
    # =====================================================================
    for i, (net_in, net_exp, rp, rs, cc, dd) in enumerate(
            [("REED1_IN", "EXP_P6", "R9", "R11", "C7", "D2"),
             ("REED2_IN", "EXP_P7", "R10", "R12", "C8", "D3"),
             ("SAB1_IN", "EXP_P8", "R14", "R16", "C9", "D5"),
             ("SAB2_IN", "EXP_P9", "R15", "R17", "C10", "D6")], start=1):
        s.add(rp, "Device:R", "10k", R0603, MPN="Pullup Reed %d" % i)
        s.connect("3V3_SYS", (rp, "1"))
        s.connect(net_exp,   (rp, "2"))
        s.add(rs, "Device:R", "1k", R0603, MPN="Serie Reed %d" % i)
        s.connect(net_in,  (rs, "1"))
        s.connect(net_exp, (rs, "2"))
        s.add(cc, "Device:C", "100n", C0603)
        s.connect(net_exp, (cc, "1"))
        s.connect("PGND",  (cc, "2"))
        s.add(dd, "Device:D_TVS", "5V6", "Diode_SMD:D_SOD-123",
              MPN="ESD am Feldstecker")
        s.connect(net_in, (dd, "1"))
        s.connect("PGND", (dd, "2"))

    s.add("U4", "Relay_SolidState:AQY282GS", "PhotoMOS 60V",
          "Package_SO:SOP-4_4.4x2.6mm_P1.27mm",
          MPN="1 Form A, SELV - NICHT fuer Netzspannung")
    s.add("R13", "Device:R", "330R", R0603, MPN="LED-Strom PhotoMOS, ca. 6 mA")
    s.connect("3V3_SYS",   ("R13", "1"))
    s.connect("RELAY_LED", ("R13", "2"))
    s.connect("RELAY_LED", ("U4", "1"))
    s.connect("RELAY_CTL", ("U4", "2"))
    s.connect("HOOD_A",    ("U4", "4"))
    s.connect("HOOD_B",    ("U4", "3"))
    s.add("D4", "Device:D_TVS", "33V", "Diode_SMD:D_SOD-123",
          MPN="Klemmung am Haubenausgang")
    s.connect("HOOD_A", ("D4", "1"))
    s.connect("HOOD_B", ("D4", "2"))

    # Feldstecker: Reed 1/2 mit je eigener Masse, danach der Haubenkontakt
    # JST-SH statt PH: fuer einen PH-Stecker (15 x 5,5 mm) ist auf dem
    # Mid-Board weder vorn noch hinten Platz - nachgerechnet gegen die
    # Courtyards aller anderen Bauteile. Der SH sitzt auf der RUECKSEITE,
    # das Kabel wird wie bei J4 vor dem Stapeln gesteckt.
    # PRUEFPUNKT: 1-mm-Raster ist fuer mehrere Meter Feldleitung filigran;
    # Alternative waere ein Stecker auf dem Bottom-Board ueber RSV_A2/RSV_A4.
    # Belegung fensterweise gruppiert, damit eine falsch aufgelegte Ader
    # nicht zwei Fenster durcheinanderbringt: je Fenster Verschluss,
    # Sabotage und die gemeinsame Masse nebeneinander.
    # ZWEI Stecker statt einem: Ein 8-poliger JST-SH ist 11,9 mm lang, und
    # dafuer ist auf dem Mid-Board nachweislich kein Platz (nachgerechnet
    # gegen alle Courtyards). Zwei kleinere finden beide einen - und die
    # Trennung ist ohnehin sauberer: J5 sind Eingaenge, J6 ist ein
    # potentialfreier Schaltausgang.
    s.add("J5", "Connector_Generic:Conn_01x06", "Feld: 4 Reed",
          "Connector_JST:JST_SH_BM06B-SRSS-TB_1x06-1MP_P1.00mm_Vertical",
          MPN="1 REED1 2 SAB1 3 GND | 4 REED2 5 SAB2 6 GND")
    s.connect("REED1_IN", ("J5", "1"))
    s.connect("SAB1_IN",  ("J5", "2"))
    s.connect("PGND",     ("J5", "3"), ("J5", "6"))
    s.connect("REED2_IN", ("J5", "4"))
    s.connect("SAB2_IN",  ("J5", "5"))

    s.add("J6", "Connector_Generic:Conn_01x02", "Haubenkontakt",
          "Connector_JST:JST_SH_BM02B-SRSS-TB_1x02-1MP_P1.00mm_Vertical",
          MPN="potentialfrei ueber den PhotoMOS - NUR SELV")
    s.connect("HOOD_A",   ("J6", "1"))
    s.connect("HOOD_B",   ("J6", "2"))

    # =====================================================================
    # 4. Piezo-Treiber (passiver Signalgeber an 5V_SYS)
    # =====================================================================
    s.add("Q2", "SwitchStack:Q_NPN_BCE", "BC847", "Package_TO_SOT_SMD:SOT-23")
    s.add("R8", "Device:R", "1k", R0603)
    s.connect("AUDIO_PWM", ("R8", "1"))
    s.connect("AUDIO_B",   ("R8", "2"))
    s.connect("AUDIO_B",   ("Q2", "1"))
    s.connect("AUDIO_LOW", ("Q2", "2"))
    s.connect("PGND",      ("Q2", "3"))
    s.add("BZ1", "Device:Buzzer", "Piezo passiv SMD",
          "Buzzer_Beeper:Buzzer_Murata_PKMCS0909E",
          MPN="Murata PKMCS0909E o.ae., 9 x 9 x 3 mm SMD - passiv, ein "
              "aktiver Summer kann keine rtttl-Melodien. SMD statt des "
              "frueheren THT-Typs (12 x 9,5): der blockierte beide "
              "Platinenseiten, und auf der Rueckseite fehlte danach der "
              "Platz fuer den 16-Bit-Expander")
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
