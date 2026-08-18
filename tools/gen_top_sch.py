#!/usr/bin/env python3
"""
Erzeugt den Schaltplan des Top-Boards (Taster, Sensorik, Display, Stern).

    python3 tools/gen_top_sch.py

Wie bei Bottom und Mid: Konnektivitaet als Quelltext, Netzlisten-Rueckvergleich
mit kicad-cli, keine Schaltungsreview.

Besonderheiten:
  * KEIN USB auf diesem Board. Die Buchse sitzt seit dem 18.08.2026 stehend
    auf dem Mid-Board und greift durch eine Randkerbe dieses Boards nach vorn
    (Begruendung unten im Rumpf).
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
    ("J5", "1"),    # TE des Displays - wir werten ihn nicht aus
    ("J6", "TN"),                    # Schaltkontakt der Klinke, absichtlich offen
    ("U3", "8"),                     # VL53L1X DNC - laut Datenblatt offen lassen
}


def build():
    s = Schematic("top_ui", "SwitchStack TOP - Front / UI", paper="A2")

    # =====================================================================
    # 1. Kein USB auf diesem Board mehr
    # =====================================================================
    # Die USB-C-Buchse sass bis zum 18.08.2026 hier. Sie musste weg, weil sie
    # nicht passte: Ueber der Top-Platine sind bis zur Zentralscheibe 3,5 mm
    # frei, eine stehende USB-C-Buchse baut 7 bis 9,25 mm. Sie haette die
    # Scheibe durchstossen - und liegend haette sie radial nach aussen gegen
    # die Adapterwand gezeigt.
    #
    # Sie sitzt jetzt STEHEND AUF DEM MID-BOARD und greift durch eine
    # Randkerbe dieses Boards nach vorn. Zwischen Mids Oberseite und Tops
    # Oberseite liegen 10,0 mm - dort passt sie bequem, und der Stecker
    # kommt weiterhin von vorn, sobald die Zentralscheibe ab ist.
    #
    # Mitgewandert sind die ESD-Diode und die beiden CC-Widerstaende. Damit
    # verschwinden acht offene Netze und alle Randabstandsfehler von diesem
    # Board, und USB_DP/USB_DN muessen nicht mehr durch den Stackverbinder.

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
    # DISPLAY: ER-TFT1.69-3 (EastRising/buydisplay), 18.08.2026 gewaehlt.
    #
    #   aktive Flaeche   27,97 x 32,63 mm
    #   sichtbar         28,97 x 33,63 mm
    #   Aussenmass       30,07 x 37,43 x 1,6 mm (FPC gefaltet)
    #   Treiber          ST7789V, 4-Draht-SPI
    #   Anschluss        12-polige FPC, STECKBAR (Variante -3; die -1 hat
    #                    eine Fahne zum Anloeten)
    #
    # QUER EINGEBAUT. Die aktive Flaeche misst dann 32,63 x 27,97 gegen ein
    # Fenster von 32,70 x 27,00: In der Breite bleiben 0,07 mm Luft, in der
    # Hoehe verdeckt die Zentralscheibe oben und unten je 0,49 mm - rund
    # 8 Pixel je Seite. Bewusst in Kauf genommen (Entscheidung 18.08.2026);
    # die Firmware darf in den obersten und untersten acht Zeilen nichts
    # Wichtiges zeichnen.
    #
    # ZWEI ZAHLEN FEHLEN NOCH, beide nur aus dem Datenblatt zu holen:
    # buydisplay.com/download/manual/ER-TFT1.69-3_Datasheet.pdf - im Browser
    # oeffnen, automatische Downloads blockt der Anbieter mit HTTP 403.
    #
    #   1. DAS RASTER DER FAHNE. Die Loetvariante ist mit 0,7 mm angegeben.
    #      KiCad bringt fuer 0,7 mm KEIN einziges FPC-Footprint mit - nur 0,5
    #      und 1,0. Ist es wirklich 0,7, muss eines in die Projektbibliothek
    #      gezeichnet werden. Bis dahin steht hier ein 0,5-mm-Footprint mit
    #      der richtigen Polzahl.
    #   2. DIE PINBELEGUNG. Zwoelf Pole sind gesichert, welches Signal auf
    #      welchem liegt nicht. Die Zuordnung unten ist die des bisherigen
    #      Platzhalters und mit hoher Wahrscheinlichkeit FALSCH.
    #
    # Solange beides offen ist, darf dieses Board NICHT bestellt werden.
    s.add("J5", "Connector_Generic:Conn_01x12", "ER-TFT1.69-3",
          "Connector_FFC-FPC:TE_1-1734839-2_1x12-1MP_P0.5mm_Horizontal",
          MPN="Panel ER-TFT1.69-3, 12-pol FPC 0,50 mm steckbar - "
              "Raster und Belegung aus dem Datenblatt bestaetigt")
    # Belegung nach Datenblatt Abschnitt 4.1, gesichert in
    # docs/datasheets/ER-TFT1.69-3.md
    s.connect("DISP_TE",   ("J5", "1"))    # Tearing Effect, wird nicht genutzt
    s.connect("PGND",      ("J5", "2"), ("J5", "12"))
    s.connect("QSPI_D1",   ("J5", "3"))    # RS = Daten/Befehl
    s.connect("DISP_RST",  ("J5", "4"))
    s.connect("QSPI_D0",   ("J5", "5"))    # SDA
    s.connect("QSPI_CLK",  ("J5", "6"))    # SCL
    s.connect("DISP_CS",   ("J5", "7"))
    s.connect("3V3_SYS",   ("J5", "8"), ("J5", "9"))   # VCC und IOVCC
    s.connect("DISP_LEDA", ("J5", "10"))
    s.connect("DISP_LEDK", ("J5", "11"))

    # --- Hintergrundbeleuchtung: sie braucht einen Treiber ----------------
    # Das Datenblatt nennt 45 mA typisch und 60 mA maximal bei Vf = 3,0 bis
    # 3,2 V, drei LEDs parallel. Bis zum 18.08.2026 hing LEDA hier direkt an
    # DISP_BL - also an einem GPIO des ESP32, ueber zwei Steckkontakte des
    # Stapels hinweg. Das haette den Pin ueberlastet.
    #
    # Aus 3,3 V geht es auch mit Vorwiderstand nicht: Bei Vf = 3,0 bis 3,2 V
    # blieben 0,1 bis 0,3 V uebrig, der Strom schwankte um den Faktor drei
    # ueber die Bauteiltoleranz allein. Deshalb die 5-V-Schiene, die ohnehin
    # ueber J_STK_A heraufkommt:
    #
    #     (5,0 - 3,1) V / 45 mA = 42 Ohm  ->  39 Ohm, 86 mW
    #
    # Gedimmt wird an der KATHODE mit einem Low-Side-FET. Der Gate-Pulldown
    # haelt die Beleuchtung aus, solange der ESP32 nicht bootet - sonst
    # leuchtet das Display beim Einschalten unkontrolliert auf.
    s.add("R_BL", "Device:R", "39R", R0603,
          MPN="Vorwiderstand Hintergrundbeleuchtung, 86 mW bei 45 mA")
    s.connect("5V_SYS",    ("R_BL", "1"))
    s.connect("DISP_LEDA", ("R_BL", "2"))

    s.add("Q_BL", "SwitchStack:Q_NMOS_GDS", "N-FET 30V 1A",
          "Package_TO_SOT_SMD:SOT-23",
          MPN="Logic-Level, Vgs(th) < 2 V - 2N7002 reicht bei 60 mA")
    s.connect("DISP_BL",   ("Q_BL", "1"))
    s.connect("DISP_LEDK", ("Q_BL", "2"))
    s.connect("PGND",      ("Q_BL", "3"))

    s.add("R_BLG", "Device:R", "100k", R0603,
          MPN="Gate-Pulldown: Beleuchtung aus, solange der ESP32 nicht bootet")
    s.connect("DISP_BL", ("R_BLG", "1"))
    s.connect("PGND",    ("R_BLG", "2"))

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

    # STERNANSCHLUSS: JST GH statt Klinkenbuchse, 18.08.2026.
    #
    # Es war eine 3,5-mm-Klinke, 9,0 x 12,48 mm gross und 12 mm hoch. Mit dem
    # Displaypanel (30,07 x 37,43, mittig ueber dem Scheibenfenster) bleibt
    # unter ihm nur ein Streifen von 8,16 mm - die Klinke braucht selbst
    # quergelegt 9,0 mm. Sie passte schlicht nicht mehr.
    #
    # Fuer zwei Litzen bei 80 mA war sie ohnehin ueberdimensioniert. Gewaehlt
    # ist die kleinste zweipolige Bauform mit VERRIEGELUNG, die es mit
    # 3D-Modell gibt:
    #
    #   JST GH BM02B-GHS-TBT   5,75 x 4,95 mm, 4,20 mm hoch, 1,25 mm Raster
    #
    # Sie steht 0,7 mm hoeher als die 3,50 mm, die bis zur Scheibeninnenseite
    # frei sind - deshalb bekommt die Zentralscheibe unten links eine kleine
    # Oeffnung von rund 6 x 5 mm. Dafuer kommt man ohne Abnehmen der Scheibe
    # an den Stecker, und die Verriegelung haelt ihn fest.
    #
    # Die einzige Bauform, die ganz unter die Scheibe passt, waere die
    # LIEGENDE JST SH mit 2,96 mm - verworfen, weil das Kabel dann seitlich
    # abgeht und der 1,0-mm-Raster fuer einen Steckverbinder, den man in die
    # Hand nimmt, zu zierlich ist.
    s.add("J6", "Connector_Generic:Conn_01x02", "Stern",
          "Connector_JST:JST_GH_BM02B-GHS-TBT_1x02-1MP_P1.25mm_Vertical",
          MPN="JST GH BM02B-GHS-TBT, 2-polig stehend mit Verriegelung")
    s.connect("STAR_OUT", ("J6", "1"))
    s.connect("PGND",     ("J6", "2"))

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
    # DER RESERVE-UART IST AM 18.08.2026 ENTFALLEN.
    #
    # Er war als DNP-Steckplatz fuer eine spaetere serielle Erweiterung
    # gedacht. Auf einem Board von 47 x 47 mm, das inzwischen Display, vier
    # Ecktaster, zwei Stackverbinder mit je 40 Kontakten, die mittige
    # Klinkenbuchse, ToF, Raumsensor und die USB-Randkerbe traegt, findet der
    # Platzierer fuer ihn keine Stelle mehr - weder fest noch automatisch.
    #
    # Reserve gibt es weiterhin, nur an anderer Stelle: J_STK_A haelt nach
    # der Umwidmung fuer die Feldsignale keine freien Kontakte mehr, aber die
    # Signale UART_AUX_TX/RX liegen unveraendert auf J_STK_B 18/20 und sind
    # vom Mid-Board aus erreichbar.


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
