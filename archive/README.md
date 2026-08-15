# Archiv

Altbestand aus der früheren Nutzung dieses Repositories. **Nicht Teil des laufenden
KiCad-SwitchStack-Entwurfs** — aber die Quelle, aus der die Funktionsanforderungen
stammen. Die Auswertung steht in [`../docs/12-legacy-socos.md`](../docs/12-legacy-socos.md);
was hier liegt, sind die Belege dazu.

## `socos-esp32-firmware/`

Lauffähige MicroPython-Firmware für ESP32 aus dem Vorgängerprojekt SoC OS
(2023/24). Ein Modul je Funktionsblock, Pinout zentral in `socos/esp32.py`,
kooperatives Task-Modell mit `uasyncio`.

| Modul | Inhalt |
|---|---|
| `socos/window.py` | **Zwei** Kontakte je Fenster: Verschluss und **Sabotage** — die Sabotageüberwachung fehlt im aktuellen Entwurf, siehe Punkt 34 in [`../docs/06-open-decisions.md`](../docs/06-open-decisions.md) |
| `socos/temperature.py` | DS18X20 über 1-Wire: Bus-Scan, mehrere Fühler an einer Leitung, Anzeige je Geräte-ID, Wiederverbindung bei Verlust |
| `socos/exhaust.py` | Schaltausgang zur Dunstabzugshaube — heute PhotoMOS `RELAY_CTL` |
| `socos/buzzer.py` | Tontabelle B0–DS8, Songabspielung und **BIST** beim Hochlauf |
| `socos/menu.py` | Menü über vier Taster (OK/Hoch/Runter/Home), 50 ms Entprellung, SSD1306 128×64 |
| `socos/watchdog.py` | Heartbeat-LED im 500-ms-Takt |

Nicht direkt weiterverwendbar — die Zielhardware ist eine andere (ESP32-S3, Runddisplay,
PCF8574-Expander) und der Firmwarepfad ist C++/ESPHome. Der Wert liegt im Verhalten,
nicht im Code; die vier weiterhin gültigen Regeln stehen in
[`../firmware/README.md`](../firmware/README.md).

Historischer Inbetriebnahmeweg, falls der MicroPython-Pfad je wieder gebraucht wird:

```bash
pip3 install esptool
ls /dev/tty.u*
python3 -m esptool --chip esp32 --port /dev/tty.usbserial-0001 erase_flash
python3 -m esptool --chip esp32 --port /dev/tty.usbserial-0001 --baud 460800 \
    write_flash -z 0x1000 ESP32_GENERIC-<version>.bin
screen /dev/tty.usbserial-0001 115200      # beenden: CTRL-A, CTRL-\
```

## `socos-kicad/`

Schaltpläne der drei Vorgängerrevisionen, ohne Backups, Caches und Layouts.

| Ordner | Revision | Wofür es aufgehoben wird |
|---|---|---|
| `v0-arduino/` | 2022, Arduino Pro Mini | **Die wichtigste Quelle.** `SocMain.kicad_sch` enthält das vollständige Feld-Interface an zwei 10-poligen Schraubklemmen: Verschluss- *und* Sabotageüberwachung je Seite, externer Thermistor, RS-485, fünf Taster inkl. RESET, dazu die verworfene 230-V-Variante. `SocTemperature`/`SocCommunicaton` nennen konkrete Bauteile |
| `v2-rp2040/` | 2023, RP2040 + W25Q128 | Zwischenschritt ohne Feldperipherie; nur der Vollständigkeit halber |
| `v3-esp32c3/` | 2023/24, ESP32-C3 | Erste ESP32-Fassung, 85 Symbole. Benannte Funktionsblöcke: Ambient light detection, Internal Temperature, System ALARM, RS-485, Sternversorgung mit **6 V / I_max 300 mA**. `TopSheet.pdf` ist der gedruckte Hauptplan |

Acht der v0-Blätter sind leer angelegt (`Heizungssteuerung`, `Umgebungssensor` u. a.) —
benannte Absichten ohne Inhalt. Einordnung in
[`../docs/12-legacy-socos.md`](../docs/12-legacy-socos.md) Abschnitt 3.5.

Die Revision v4 lag ebenfalls im Altbestand, war aber eine frühere Fassung genau
dieses Projekts und in jedem Punkt vom aktuellen Stand überholt. Sie wurde nicht
archiviert.

## `pico-prototype/`

MicroPython-Prototyp für den Raspberry Pi Pico (RP2040) aus 2021/2022. Im Wesentlichen
ein LED-Blinkskript (`Watchdog.toggle()` auf Pin 25) plus zwei leere Klassengerüste
(`Button`, `Monitor`). Dazu die pico-go-/VS-Code-Konfiguration und zwei
UF2-Firmware-Dateien (Pico MicroPython v1.17 vom 02.09.2021, `flash_nuke`).

Der Code wurde hierher verschoben statt gelöscht, damit die Historie erhalten bleibt und
nichts unbeabsichtigt verlorengeht. Er hat inhaltlich nichts mit dem ESP32-Projekt zu
tun und kann jederzeit entfernt werden.

Hinweise, falls jemand ihn doch noch verwenden will:

- `socos/__init__ .py` hat ein **Leerzeichen vor der Dateiendung**. Der Package-Import
  in `test.py` funktioniert damit nicht zuverlässig.
- Die UF2-Firmware ist von 2021 und inzwischen deutlich veraltet.
