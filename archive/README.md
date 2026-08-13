# Archiv

Altbestand aus der früheren Nutzung dieses Repositories. **Nicht Teil des
KiCad-SwitchStack-Projekts.**

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
