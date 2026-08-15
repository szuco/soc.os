# MID – Logic

KiCad-Projekt `mid_logic`. Logik- und Kommunikationsebene des Stacks.

## Umfang

Bestückt sind 37 Bauteile, 57 Netze (`bom_mid.csv`):

- **ESP32-S3-WROOM-1-N16R8** als zentrale Steuerung, RESET- und BOOT-Taster
- **MAX3485** als **primäre** Kommunikation: `RS485_DIR` schaltet DE und /RE
  gemeinsam, Fail-Safe-Bias 2 × 560 R, Terminierung 120 R als **DNP** (nur am
  Busende bestücken), JST-XH 3-polig
- **PCF8574** (0x20) als GPIO-Expander für die langsamen Signale: `HW_TRIP1/2`,
  `TRIP_RST`, `STAR_EN`, `PRESENCE_INT`, `RELAY_CTL`, `REED1/2` — **P0–P7 sind
  damit restlos belegt** (relevant für Punkt 34)
- **Piezo passiv** mit Treiberstufe — ein aktiver Summer kann keine Melodien
- **PhotoMOS AQY282GS** als potentialfreier Meldekontakt zur Dunstabzugshaube,
  **ausschließlich SELV**, mit 33-V-Klemmdiode
- **Feldstecker JST-SH 6-polig** für zwei Verschlusskontakte und die Haube,
  je Reed 10k Pull-up, 1k Serie und 5V6-ESD-Diode
- Stackverbinder `J_STK_A` und `J_STK_B` nach unten und nach oben

Ein externer ADC ist **nicht** bestückt — die Strommessung hängt am internen ADC
des S3 (offener Punkt 18). Die frühere Radar-Schnittstelle ist entfallen; der
Präsenzsensor sitzt als VL53L1X auf dem Top-Board.

## Kernregeln

- **Antennen-Keepout:** ESP32-Antennenbereich kupfer- und bauteilfrei auf **allen** Lagen,
  Antenne möglichst zur Front orientiert. WLAN ist sekundär — in einer massiven
  Unterputzdose ist die Performance realistisch schwach, deshalb RS-485 als primäre
  Kommunikation.
- Keine Motorströme, keine USB-Datenleitungen auf diesem Board.
- Durchgehende GND-Referenzlage, 4 Lagen empfohlen.

## Mechanik

- Ø 52,0 mm, 1,0 mm Dicke
- Bohrbild und Stackverbinder-Positionen **deckungsgleich** mit BOTTOM und TOP
- Abstand nach unten ≈ 10 mm, nach oben ≈ 8–10 mm

Exakte Koordinaten: [`../../docs/04-mechanical.md`](../../docs/04-mechanical.md)

## Referenzdokumente

- [`docs/03-stack-pinout.md`](../../docs/03-stack-pinout.md) – Pinmapping beider Verbinder
- [`docs/00-system-overview.md`](../../docs/00-system-overview.md) – Peripherieübersicht
- [`docs/06-open-decisions.md`](../../docs/06-open-decisions.md) – ESP32-Modul, Transceiver, ADC, Feldstecker
- [`docs/13-funktionsstatus.md`](../../docs/13-funktionsstatus.md) – Gesamtstand

## Status

**Schaltplan erzeugt und netzlistengeprüft** (`tools/gen_mid_sch.py`, 37 Bauteile,
57 Netze, Netzlistenvergleich bestanden). Stückliste `bom_mid.csv` aus derselben
Quelle.

**Layout:** platziert, Zonen angelegt — **aber ohne eine einzige Leiterbahn.**
Es gab einmal einen vollständig gerouteten Stand (655 Segmente, 73 Vias); der
Umbau auf Reed-Kontakte und Haubenkontakt am 15.08.2026 hat das Layout neu
erzeugt und die Verdrahtung damit verworfen. Sie ist neu zu ziehen — Pipeline:
`tools/route_boards.py`, Massenacharbeit mit `tools/gnd_*.py`.

**Nicht geprüft:** Schaltungsreview gegen Datenblätter (MAX3485-Pinbelegung,
PhotoMOS-LED-Strom). Die Netzliste stimmt mit der Sollvorgabe überein — mehr sagt
sie nicht.

**Offen und layoutrelevant:** Punkt 29 (der Feldstecker sitzt 0,4 mm neben einem
Keepout) und Punkt 34 (Sabotagekontakte hätten hier keinen Expanderpin mehr).
