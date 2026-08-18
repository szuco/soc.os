#!/usr/bin/env python3
"""
Stack-Pinout v0.5 - die EINZIGE Quelle fuer J_STK_A und J_STK_B.

Alle drei Schaltplan-Generatoren importieren diese Tabellen; docs/03 wird
daraus erzeugt. Damit koennen die Boards nicht auseinanderlaufen.

Aenderung v0.4 -> v0.5 (18.08.2026):
  * TASTEN UND I2C AUF DIE AUSSENREIHE, und die Tasten auf BEIDE Verbinder
    verteilt. Bis v0.4 lagen BTN1..BTN4 auf B26..B29 - vier benachbarten
    Kontakten der INNENreihe des RECHTEN Verbinders. Ihre Taster sitzen aber
    in allen vier Ecken des Top-Boards: zwei davon links. Zwei Bahnen mussten
    also quer ueber ein Board, auf dem 80 Steckkontakte im 1,27-mm-Raster
    stehen, und alle vier mussten zuerst aus der Innenreihe heraus.

    Zwei Autorouter (Freerouting 1.9.0 und 2.3.0) und zwei Lagenzahlen haben
    daran nichts geaendert - es blieben exakt dieselben elf offenen Netze.
    Das ist kein Werkzeugproblem, sondern die Pinbelegung.

    Neu liegt jedes Tastennetz auf der AUSSENreihe des Verbinders, der seiner
    Ecke am naechsten ist. Von dort geht es direkt nach aussen und am
    Boardrand entlang zum Taster:

      BTN1  B1   aussen, y = -14,06  ->  SW1 (+18 / -20)
      BTN2  A2   aussen, y = -14,06  ->  SW2 (-18 / -20)
      BTN3  A40  aussen, y = +10,07  ->  SW3 (-18 / +20)
      BTN4  B39  aussen, y = +10,07  ->  SW4 (+18 / +20)

    I2C_SCL/SDA wandern von B6/B8 (innen) auf B5/B7 (aussen) - beide
    I2C-Teilnehmer auf Top, SHT4x und ToF, sitzen an der oberen Kante.

    Die freigewordenen Kontakte B6, B8, B26..B29 werden PGND. Vier PGND-Pins
    sind dafuer weggefallen (A2, A40, B1, B39); es bleiben ueber beide
    Verbinder immer noch 25.

Aenderung v0.3 -> v0.4 (18.08.2026):
  * USB_DP/USB_DN sind von A34/A36 VERSCHWUNDEN und heissen jetzt RSV_A3/RSV_A5.
    Die USB-C-Buchse ist auf das Mid-Board gewandert, wo auch der ESP32-S3
    sitzt - die Datenleitungen bleiben damit auf einer Platine und muessen
    ueberhaupt nicht mehr durch den Stapel. Grund fuer den Umzug war die
    Bauhoehe: Ueber dem Top-Board sind bis zur Zentralscheibe 3,5 mm frei,
    eine stehende USB-C-Buchse baut 7 bis 9,25 mm. Zwischen Mid und Top sind
    es 10,0 mm. Die Buchse greift durch eine Randkerbe des Top-Boards.
  * USB_VBUS bleibt auf A18 - es wird weiterhin nach unten zum Power-Mux auf
    dem Bottom-Board gefuehrt, kommt jetzt nur von Mid statt von Top.

Aenderungen v0.2 -> v0.3:
  * USB_DP/USB_DN neu auf J_STK_A 34/36 (benachbart in Reihe B, PGND daneben).
    Grund: Der ESP32-S3 nutzt seinen NATIVEN USB - es gibt keinen
    USB-UART-Baustein mehr, dessen UART man durch den Stack fuehren koennte.
    Die alte Regel "USB-Daten nie durch den Stack" stammte aus der Zeit mit
    USB-UART auf dem Top-Board und ist damit gegenstandslos. Full-Speed-USB
    (12 MHz) ueber zwei benachbarte 1,27-mm-Kontakte mit Massenachbarn ist
    unkritisch.
  * STAR_EN neu (A23): schaltet den Stern-Ausgang. Der zweipolige
    Sternstecker sitzt laut Frontplatten-Design auf dem TOP-Board - der
    fruehere J4 auf dem Bottom-Board war ein Fehler und ist entfernt.
    Geschaltet wird vorn per High-Side-P-FET, angesteuert vom I2C-Expander
    auf dem Mid-Board.
"""

VERSION = "0.3"

# J_STK_A - Power und Motor
STK_A = {
    1: "PGND", 2: "BTN2", 3: "5V_SYS", 4: "5V_SYS", 5: "5V_SYS", 6: "5V_SYS",
    7: "PGND", 8: "PGND", 9: "3V3_SYS", 10: "3V3_SYS", 11: "PGND", 12: "PGND",
    13: "6V2_STAR_F", 14: "PGND", 15: "PGND", 16: "M1_INA", 17: "M1_INB",
    18: "USB_VBUS", 19: "PGND", 20: "M2_INA", 21: "PGND", 22: "M2_INB",
    23: "STAR_EN", 24: "RSV_A2", 25: "PGND", 26: "I_SENSE1", 27: "AGND",
    28: "I_SENSE2", 29: "AGND", 30: "HW_TRIP1", 31: "HW_TRIP2",
    32: "TRIP_RST", 33: "RELAY_CTL", 34: "RSV_A3", 35: "RSV_A4",
    36: "RSV_A5", 37: "RSV_A6", 38: "PGND", 39: "PGND", 40: "BTN3",
}

# J_STK_B - UI und Kommunikation
STK_B = {
    1: "BTN1", 2: "PGND", 3: "3V3_SYS", 4: "3V3_SYS", 5: "I2C_SCL",
    6: "PGND", 7: "I2C_SDA", 8: "PGND", 9: "PGND", 10: "I2C_INT",
    11: "PGND", 12: "UART485_TX", 13: "PGND", 14: "UART485_RX",
    15: "RS485_DIR", 16: "RS485_DIR", 17: "PGND", 18: "UART_AUX_TX",
    19: "PGND", 20: "UART_AUX_RX", 21: "PRESENCE_INT", 22: "PGND",
    23: "AUDIO_PWM", 24: "QSPI_CLK", 25: "PGND", 26: "PGND", 27: "PGND",
    28: "PGND", 29: "PGND", 30: "PGND", 31: "QSPI_D0", 32: "QSPI_D1",
    33: "PGND", 34: "QSPI_D2", 35: "QSPI_D3", 36: "DISP_CS",
    37: "DISP_RST", 38: "DISP_BL", 39: "BTN4", 40: "PGND",
}


def connect_stack(s, ref_a="J2", ref_b="J3",
                  fp="Connector_PinSocket_1.27mm:PinSocket_2x20_P1.27mm_Vertical"):
    """Fuegt beide Stackverbinder hinzu und verbindet alle 80 Pins."""
    s.add(ref_a, "Connector_Generic:Conn_02x20_Odd_Even", "J_STK_A", fp)
    for pin, net in STK_A.items():
        s.connect(net, (ref_a, str(pin)))
    s.add(ref_b, "Connector_Generic:Conn_02x20_Odd_Even", "J_STK_B", fp)
    for pin, net in STK_B.items():
        s.connect(net, (ref_b, str(pin)))
