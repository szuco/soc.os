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

Auslegung nach docs/11-motor-data.md Abschnitt 5. Der Blockierstrom ist seit
dem 17.08.2026 gemessen: 1,7 A je Motor (24 V an 14 Ohm Ankerwiderstand), nicht
die zuvor angenommenen 25 A. Shunt und Trip-Teiler sind entsprechend neu
gerechnet - siehe die Kommentare bei R_*_SH und R7/R8/R9.
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
    # EIN Steckverbinder fuer die gesamte Feldverdrahtung, 18.08.2026.
    #
    # Bisher verteilten sich die Anschluesse auf vier Stecker an zwei
    # Platinen: Leistung und Motoren hier, RS485, vier Reed-Kontakte und der
    # Haubenkontakt auf dem Mid-Board mitten im Stapel. Die Feldkabel zerrten
    # damit an drei Leiterplatten, und der Stapel liess sich nicht als Ganzes
    # ein- und ausbauen.
    #
    # Moeglich wurde die Zusammenfassung erst dadurch, dass die diskrete
    # H-Bruecke der integrierten gewichen ist - die acht MOSFETs belegten
    # genau die Flaeche, die dieser Stecker braucht (docs/14).
    #
    #   1  24V_IN       9  RS485_B
    #   2  PGND        10  REED1_IN
    #   3  M1_A        11  SAB1_IN
    #   4  M1_B        12  REED2_IN
    #   5  M2_A        13  SAB2_IN
    #   6  M2_B        14  HOOD_A
    #   7  PGND        15  HOOD_B
    #   8  RS485_A     16  PGND
    #
    # Kontakt 7 trennt die PWM-fuehrenden Motorleitungen von RS485 und den
    # Reed-Eingaengen. Micro-Fit 3.0 traegt 5 A je Kontakt, der Summenstrom
    # betraegt im unguenstigsten Fall 4,1 A - das traegt der eine 24-V-Kontakt.
    #
    # ALLES SELV. Der Haubenkontakt ist ueber den PhotoMOS auf dem Mid-Board
    # potentialfrei, darf aber nur Kleinspannung schalten - im selben Gehaeuse
    # wie die 24-V-Zufuehrung ist alles andere unzulaessig.
    s.add("J1", "Connector_Generic:Conn_02x08_Odd_Even", "Feld 16p",
          "Connector_Molex:Molex_Micro-Fit_3.0_43045-1612_2x08_P3.00mm_Vertical",
          MPN="Molex 43045-1612, 2x8, stehend - EIN Stecker fuer alles, SELV")
    s.connect("24V_IN",   ("J1", "1"))
    s.connect("PGND",     ("J1", "2"), ("J1", "7"), ("J1", "16"))
    s.connect("M1_A",     ("J1", "3"))
    s.connect("M1_B",     ("J1", "4"))
    s.connect("M2_A",     ("J1", "5"))
    s.connect("M2_B",     ("J1", "6"))
    s.connect("RS485_A",  ("J1", "8"))
    s.connect("RS485_B",  ("J1", "9"))
    s.connect("REED1_IN", ("J1", "10"))
    s.connect("SAB1_IN",  ("J1", "11"))
    s.connect("REED2_IN", ("J1", "12"))
    s.connect("SAB2_IN",  ("J1", "13"))
    s.connect("HOOD_A",   ("J1", "14"))
    s.connect("HOOD_B",   ("J1", "15"))

    # Sicherung - Wert messabhaengig
    s.add("F1", "Device:Fuse", "15A traege",
          "Fuse:Fuse_Littelfuse-NANO2-451_453",
          MPN="SMD NANO2, messabhaengig - siehe docs/11")
    s.connect("24V_IN", ("F1", "1"))
    s.connect("24V_F",  ("F1", "2"))

    # TVS gegen Transienten
    s.add("D1", "Device:D_TVS", "SMBJ30A", "Diode_SMD:D_SMB")
    s.connect("24V_F", ("D1", "1"))
    s.connect("PGND",  ("D1", "2"))

    # Verpolschutz: P-MOSFET high-side, Gate ueber R gegen GND, Zener begrenzt Ugs
    s.add("Q1", "SwitchStack:Q_PMOS_GSD", "P-FET 40V 30A",
          "Package_SO:PowerPAK_SO-8_Single",
          MPN="z.B. SiR429DP; Pad-Zuordnung siehe PAD_MAP in gen_layouts")
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
    # Bulk niedrigbauend: Hoehenbudget Bottom-Oberseite ist ~10 mm
    # (docs/04). Polymer-Typen, Wert nach Messung M2 ggf. anheben.
    for ref, val, fp in (("C1", "100n", C0603), ("C2", "10u", C1210),
                         ("C3", "220u/35V Polymer", "Capacitor_SMD:CP_Elec_8x6.5"),
                         ("C4", "220u/35V Polymer", "Capacitor_SMD:CP_Elec_8x6.5")):
        s.add(ref, "Device:C", val, fp)
        s.connect("24V_PROT", (ref, "1"))
        s.connect("PGND",     (ref, "2"))

    # =====================================================================
    # 2. Die 12-V-Gatespannung ist am 18.08.2026 entfallen
    # =====================================================================
    # Sie versorgte ausschliesslich die Bootstrap-Treiber IR2104 der diskreten
    # H-Bruecke. Mit dem Wechsel auf die integrierte Bruecke DRV8871 braucht
    # niemand mehr eine eigene Gatespannung - der Treiber erzeugt sie intern.
    #
    # Entfallen sind damit der Vorwiderstand, die Z-Diode, der Regler L78L12
    # im SOT-89 und seine beiden Kondensatoren: fuenf Bauteile und eine ganze
    # Spannungsschiene weniger.

    # =====================================================================
    # 3. DC/DC-Wandler
    # =====================================================================
    def buck_tps54360(u, rail, r_hi, r_lo, l_val, cout, cout_fp):
        """TPS54360: 60 V Eingang, Vref 0,8 V."""
        s.add(u, "Regulator_Switching:TPS54360DDA", "TPS54360",
              "Package_SO:HSOP-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.1mm")
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
        s.add(u + "_L", "Device:L", l_val, "Inductor_SMD:L_Bourns_SRP7028A_7.3x6.6mm")
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
    s.add("L1", "Device:L", "2u2", "Inductor_SMD:L_Bourns_SRP5030T")
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
        """Integrierte Vollbruecke DRV8871, Inline-Strommessung,
        Comparator-Fenster und Latch fuer den Hardware-Trip.

        BIS ZUM 18.08.2026 STAND HIER EINE DISKRETE BRUECKE aus zwei IR2104
        und vier N-FETs je Kanal - acht FETs und vier Treiber insgesamt. Sie
        war so gewaehlt worden, weil der Blockierstrom unbekannt war und ein
        integrierter Treiber ihn moeglicherweise nicht ausgehalten haette.

        Inzwischen ist der Blockierstrom vierfach belegt: drei eigene
        Messungen und die Bauteilwahl des Original-Controllers, der genau
        diesen Weg geht - zwei integrierte Bruecken (Infineon BTM7700G), je
        eine pro Motor (docs/14). Bei 1,7 A ist die diskrete Bruecke aus
        60-A-FETs schlicht ueberdimensioniert.

        Der DRV8871 statt des BTM7700G des Originals, aus einem Grund:
        Spannungsreserve. Der BTM7700G ist bis 28 V kurzschlussfest, unsere
        Schiene liegt bei 24 V +10 % = 26,4 V - das ist zu knapp. Der DRV8871
        vertraegt 45 V und 3,6 A Spitze.

        WAS DADURCH ENTFAELLT, je Kanal:
          4 N-FET PowerPAK SO-8, 2 IR2104, 4 Gate-Widerstaende,
          2 Bootstrap-Dioden, 2 Bootstrap-Kondensatoren
        und einmal fuer das ganze Board die 12-V-Gatespannung samt Regler.

        WAS BLEIBT: Shunt, INA240A2, Fensterkomparator und Latch. Der DRV8871
        bringt zwar eigene Strombegrenzung, Uebertemperatur- und
        Unterspannungsabschaltung mit, aber keine davon meldet sich nach
        aussen und keine schuetzt die Mechanik. Die eigene Messkette bleibt
        also - sie liefert den Messwert fuer die Endlagenerkennung, und der
        Latch bleibt die firmwareunabhaengige Notbremse.

        WIE DER LATCH JETZT ABSCHALTET: Der DRV8871 hat keinen Enable-Pin.
        Statt auf ~SD zu wirken, sperrt der Latch die beiden Eingaenge ueber
        ein UND-Gatter je Leitung; mit IN1 = IN2 = 0 geht die Bruecke in den
        hochohmigen Zustand.
        """
        p = "M%d" % n
        sd = p + "_SD"                       # aktiv low: Endstufe aus

        s.add("U%s_BR" % p, "Driver_Motor:DRV8871DDA", "DRV8871",
              "Package_SO:HSOP-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.1mm_ThermalVias",
              MPN="45 V, 3,6 A Spitze, Strombegrenzung ueber ILIM - "
                  "Thermalpad an PGND anbinden")
        s.connect("PGND",      ("U%s_BR" % p, "1"), ("U%s_BR" % p, "7"),
                  ("U%s_BR" % p, "9"))
        s.connect(p + "_GB",   ("U%s_BR" % p, "2"))    # IN2, ueber UND-Gatter
        s.connect(p + "_GA",   ("U%s_BR" % p, "3"))    # IN1, ueber UND-Gatter
        s.connect(p + "_ILIM", ("U%s_BR" % p, "4"))
        s.connect("24V_PROT",  ("U%s_BR" % p, "5"))
        s.connect(p + "_SWA",  ("U%s_BR" % p, "6"))    # OUT1 -> Shunt
        s.connect(out_b,       ("U%s_BR" % p, "8"))    # OUT2 direkt

        # Strombegrenzung des Treibers. Sie ist die INNERE Grenze und liegt
        # bewusst UEBER dem Blockierstrom von 1,7 A, damit der Anschlag - ein
        # normaler Betriebszustand - sie nicht dauernd anspricht. 2,7 A nach
        # der Datenblattformel I = V_ILIM / (K * R); Wert vor der Bestellung
        # gegen das Datenblatt nachrechnen.
        s.add("R_%s_IL" % p, "Device:R", "33k0", R0603,
              MPN="Strombegrenzung DRV8871 - Wert gegen Datenblatt pruefen")
        s.connect(p + "_ILIM", ("R_%s_IL" % p, "1"))
        s.connect("PGND",      ("R_%s_IL" % p, "2"))

        # Bulk direkt an der Bruecke
        s.add("C_%s_BR" % p, "Device:C", "100u 50V",
              "Capacitor_SMD:C_1210_3225Metric",
              MPN="Bulk je Bruecke. Das Original kommt mit 47 uF fuer BEIDE "
                  "Motoren aus (docs/14) - 100 uF je Kanal ist reichlich")
        s.connect("24V_PROT", ("C_%s_BR" % p, "1"))
        s.connect("PGND",     ("C_%s_BR" % p, "2"))

        # UND-Gatter: Der Latch sperrt beide Eingaenge gleichzeitig.
        for leg, inp in (("A", "%s_INA" % p), ("B", "%s_INB" % p)):
            g = "U%s_G%s" % (p, leg)
            s.add(g, "74xGxx:74AHC1G08", "74AHC1G08",
                  "Package_TO_SOT_SMD:SOT-353_SC-70-5")
            s.connect(inp,            (g, "1"))
            s.connect(sd,             (g, "2"))
            s.connect("PGND",         (g, "3"))
            s.connect("%s_G%s" % (p, leg), (g, "4"))
            s.connect("3V3_SYS",      (g, "5"))

        # Inline-Shunt im Zweig A - misst in JEDEM PWM-Zustand.
        # 5 mOhm, nicht 1 mOhm: Der gemessene Blockierstrom von 1,7 A haette
        # am 1-mOhm-Shunt nur 1,6 mV erzeugt, verstaerkt 80 mV - zu wenig, um
        # Lauf (0,3-1,0 A) von Anschlag (1,7 A) zu trennen. Mit 5 mOhm und
        # INA240A2 (Verstaerkung 50) sind es 0,25 V/A, Messbereich +/-6,6 A,
        # Verlustleistung bei 2 A nur 20 mW.
        s.add("R_%s_SH" % p, "Device:R_Shunt", "5m0 1W",
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
        # KEIN LM393 - der Gleichtakt-Eingangsbereich reicht bei 3,3 V nicht.
        #
        # Der klassische LM393 ist fuer 0 bis V+ minus 1,5 V spezifiziert, an
        # 3,3 V also bis 1,8 V. V_TRIP_HI liegt bei 2,752 V, der Sensepegel im
        # Trip-Fall ebenso: Die obere Haelfte des Fensterkomparators arbeitete
        # ausserhalb ihres Bereichs, der Hardware-Trip haette nur in EINER
        # Stromrichtung gewirkt. Gefunden am 17.08.2026; der Fehler war aelter
        # als die Strommessung, die alte Schwelle lag genauso hoch.
        #
        # Verlangt wird deshalb ein Komparator mit Rail-to-Rail-Eingang. Die
        # Alternative - Versorgung aus 5V_SYS - scheiterte an der Geometrie:
        # Das Netz liegt 27 bzw. 36 mm entfernt auf der anderen Boardhaelfte.
        #
        # ANFORDERUNG an den bestellten Typ, gegen das Datenblatt zu pruefen:
        #   dual, SOIC-8, Standard-Pinout (1=OUT_A 2=IN_A- 3=IN_A+ 4=V-
        #                                  5=IN_B+ 6=IN_B- 7=OUT_B 8=V+)
        #   OPEN-DRAIN-Ausgang  - das Wire-OR auf Mx_TRIP haengt daran,
        #                         ein Push-Pull-Typ zerstoert die Verknuepfung
        #   Gleichtaktbereich bis mindestens 2,9 V bei 3,3 V Versorgung
        #
        # Kandidat TLV3702: Rail-to-Rail-Eingang, Open-Drain, SOIC-8. Mit rund
        # 5 us ist er LANGSAMER als der LM393 (1,3 us) - hier ein Vorteil, denn
        # der Komparator sieht das ungefilterte Sense-Signal und haengt an
        # einem Latch (Punkt 59). Wer Geschwindigkeit braucht, nimmt den
        # TLV1702 (560 ns), handelt sich dafuer aber mehr Stoerempfindlichkeit
        # ein. Fuer einen Kurzschluss-Trip sind 5 us reichlich schnell.
        #
        # Das Symbol liegt in der Projektbibliothek: KiCad 10 bringt fuer den
        # TLV3702 keines mit, und ein Schaltplan mit lib_id "LM393" und Wert
        # "TLV3702" waere eine Falle fuer den naechsten Leser. Erzeugt aus dem
        # geometrisch identischen LM393-Symbol, Pinbelegung also nachweislich
        # das Standard-Pinout. Siehe hardware/lib/SwitchStack.kicad_sym.
        s.add(cmp_, "SwitchStack:TLV3702", "TLV3702", SOIC8,
              MPN="Rail-to-Rail-Eingang + Open-Drain PFLICHT - kein LM393")
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

    # Gemeinsame Trip-Schwellen.
    # 3,3 V ueber 10k / 40k2 / 10k  ->  HI = 2,752 V, LO = 0,548 V
    # Mit 5 mOhm Shunt und Verstaerkung 50 entspricht das +/- 4,4 A.
    # (Mit dem alten 1-mOhm-Shunt waren es +/- 22 A - der Teiler ist
    # unveraendert, der Shunt hat die Schwelle mitgenommen.)
    #
    # Die Schwelle muss ueber dem Blockierstrom liegen, denn der Anschlag ist
    # hier ein NORMALER Betriebszustand - ohne Endschalter faehrt der Laden bei
    # jeder Fahrt kurz dagegen. 1,7 A gemessen, 4,4 A Trip: Faktor 2,75.
    # Die Reserve ist bewusst grosszuegig, weil sie NICHTS kostet: Zwischen
    # 4 und 5 A ist auf dieser Platine nichts gefaehrdet (FETs >60 A, Shunt
    # 1 W). Ein hoeherer Trip schuetzt also genauso gut vor dem Einzigen,
    # was er ueberhaupt abfangen kann - einem echten Kurzschluss - und
    # vertraegt zugleich einen Messfehler beim Blockierstrom von Faktor 2,5.
    # Ein echter Kurzschluss liegt um Groessenordnungen darueber und loest
    # sofort aus.
    #
    # Nuetzliche Eigenschaft: Teiler und INA240-Referenz haengen beide an
    # 3V3_SYS. Driftet die Versorgung, driften Nullpunkt und Schwelle
    # gemeinsam - die Schwelle bleibt ratiometrisch stabil.
    s.add("R7", "Device:R", "10k0", R0603, MPN="Trip-Schwelle 4,4 A")
    s.connect("3V3_SYS",   ("R7", "1"))
    s.connect("V_TRIP_HI", ("R7", "2"))
    s.add("R8", "Device:R", "40k2", R0603, MPN="Trip-Schwelle 4,4 A")
    s.connect("V_TRIP_HI", ("R8", "1"))
    s.connect("V_TRIP_LO", ("R8", "2"))
    s.add("R9", "Device:R", "10k0", R0603, MPN="Trip-Schwelle 4,4 A")
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
