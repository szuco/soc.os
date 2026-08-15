#!/usr/bin/env python3
"""
Stack-Pinout v0.3 - die EINZIGE Quelle fuer J_STK_A und J_STK_B.

Alle drei Schaltplan-Generatoren importieren diese Tabellen; docs/03 wird
daraus erzeugt. Damit koennen die Boards nicht auseinanderlaufen.

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
    1: "PGND", 2: "PGND", 3: "5V_SYS", 4: "5V_SYS", 5: "5V_SYS", 6: "5V_SYS",
    7: "PGND", 8: "PGND", 9: "3V3_SYS", 10: "3V3_SYS", 11: "PGND", 12: "PGND",
    13: "6V2_STAR_F", 14: "PGND", 15: "PGND", 16: "M1_INA", 17: "M1_INB",
    18: "USB_VBUS", 19: "PGND", 20: "M2_INA", 21: "PGND", 22: "M2_INB",
    23: "STAR_EN", 24: "RSV_A2", 25: "PGND", 26: "I_SENSE1", 27: "AGND",
    28: "I_SENSE2", 29: "AGND", 30: "HW_TRIP1", 31: "HW_TRIP2",
    32: "TRIP_RST", 33: "RELAY_CTL", 34: "USB_DP", 35: "RSV_A4",
    36: "USB_DN", 37: "RSV_A6", 38: "PGND", 39: "PGND", 40: "PGND",
}

# J_STK_B - UI und Kommunikation
STK_B = {
    1: "PGND", 2: "PGND", 3: "3V3_SYS", 4: "3V3_SYS", 5: "PGND",
    6: "I2C_SCL", 7: "PGND", 8: "I2C_SDA", 9: "PGND", 10: "I2C_INT",
    11: "PGND", 12: "UART485_TX", 13: "PGND", 14: "UART485_RX",
    15: "RS485_DIR", 16: "RS485_DIR", 17: "PGND", 18: "UART_AUX_TX",
    19: "PGND", 20: "UART_AUX_RX", 21: "PRESENCE_INT", 22: "PGND",
    23: "AUDIO_PWM", 24: "QSPI_CLK", 25: "PGND", 26: "BTN1", 27: "BTN2",
    28: "BTN3", 29: "BTN4", 30: "PGND", 31: "QSPI_D0", 32: "QSPI_D1",
    33: "PGND", 34: "QSPI_D2", 35: "QSPI_D3", 36: "DISP_CS",
    37: "DISP_RST", 38: "DISP_BL", 39: "PGND", 40: "PGND",
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
