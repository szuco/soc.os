# 10 – Firmware-Strategie: Unabhängigkeit von ESPHome

## 0. Der Fehler, der dieses Dokument nötig macht

In [`09-display-and-mcu.md`](09-display-and-mcu.md) wurde die Displayauswahl am
ESPHome-Treiberkatalog ausgerichtet: Panels ohne eingebauten Treiber (ST77916,
ST77903) galten als ausgeschieden, und deshalb fiel die Wahl auf ein AMOLED mit
Einbrenn-Auflagen statt auf das technisch bessere LCD.

**Das war die falsche Abhängigkeitsrichtung.** Hardware wird nach Datenblatt,
Verfügbarkeit und Physik ausgewählt. Ein fehlender Treiber in einem
Anwendungsframework ist ein Arbeitspaket mit bezifferbarem Aufwand — kein
K.-o.-Kriterium. Dieses Dokument zieht die Trennlinie neu.

## 1. Was „ESPHome" eigentlich bündelt

Die Abhängigkeit wirkt nur deshalb total, weil Stock-ESPHome drei Schichten in
einem Paket liefert. Getrennt betrachtet ist keine davon exklusiv:

| Schicht | Was dort passiert | Frameworkunabhängige Quelle |
|---|---|---|
| **L1 – Hardwaretreiber** | Display-Controller, Sensoren, ADC | **Espressif Component Registry** (`esp_lcd_*`, offiziell gepflegt) — z. B. [`espressif/esp_lcd_st77916`](https://components.espressif.com/components/espressif/esp_lcd_st77916), SPI + QSPI |
| **L2 – Regel-/Gerätelogik** | Motorregelung, Stall-Erkennung, UI-Verhalten | **eigenes C++** — war ohnehin schon beschlossen ([`09`](09-display-and-mcu.md), Abschnitt 4: die PWM-synchrone Strommessung kann Stock-ESPHome nicht) |
| **L3 – Home-Assistant-Integration** | Entitäten, Transport, OTA, Provisioning | **offene Protokolle:** MQTT Discovery, Modbus RTU — beides HA-nativ |

Bemerkenswert: **Schicht 2 hat den Stock-ESPHome-Rahmen längst verlassen.** Die
Motorregelung war von Anfang an als External Component (eigenes C++) geplant. Die
Frage „dürfen wir ESPHome verlassen?" war also schon beantwortet — nur bei der
Displaywahl wurde sie nicht angewendet.

## 2. Die RS-485-Wahrheit

Ein Punkt, der bisher unausgesprochen blieb: **ESPHomes native HA-Anbindung läuft
über IP, also WLAN.** Das Projekt definiert aber RS-485 als primäre Kommunikation
und WLAN als sekundär. Konsequenz:

- Im **WLAN-Betrieb** liefert ESPHome die HA-Integration geschenkt (native API,
  Verschlüsselung, OTA, Autodiscovery).
- Im **reinen RS-485-Betrieb** ist die HA-Anbindung so oder so ein offenes
  Protokoll: **Modbus RTU**. Home Assistant spricht Modbus nativ (seriell über
  einen RS-485-Dongle am HA-Host). Verifiziert am installierten ESPHome 2026.6.5:
  eine `modbus_server`-Komponente ist enthalten — ESPHome kann also als
  Modbus-Slave am Bus hängen. Ein Eigenbau-Firmware könnte dasselbe mit
  Espressifs offiziellem `esp-modbus` tun.

Der harte Lock-in-Kern von ESPHome schrumpft damit auf: Komfort. YAML-Konfiguration,
fertiges Entity-Modell, OTA, Provisioning. Das ist viel wert — aber es ist
Bequemlichkeit, nicht Architektur.

## 3. Die Optionen, mit ehrlichen Kosten

| | Pfad | Hardware-Freiheit | HA-Anbindung | Aufwand | Risiko |
|---|---|---|---|---|---|
| A | **Stock-ESPHome pur** (Status quo bis gestern) | ⚠️ auf Treiberkatalog beschränkt | native API (WLAN) | ~0 | Hardwarewahl folgt dem Katalog — genau das Problem |
| B | **ESPHome + External Components** | ✅ voll — fehlende Treiber werden als dünner Wrapper um `esp_lcd_*` geschrieben | native API (WLAN) und/oder `modbus_server` (RS-485) | Tage je Treiber, einmalig | gering; External Components sind dokumentierter, offizieller Mechanismus |
| C | **Pure ESP-IDF + MQTT Discovery** | ✅ voll | MQTT (IP) | **Wochen**: OTA, Provisioning, Verschlüsselung, Entity-Modell, Config-Handling alles selbst | volle Eigenverantwortung, dafür null Framework-Bindung |
| D | **Pure ESP-IDF/Arduino + Modbus RTU** | ✅ voll | Modbus über RS-485, ganz ohne WLAN | Wochen (wie C, plus Registerkarte definieren) | HA-seitig etwas spröder (Polling, keine Push-Events) |
| E | **Tasmota** | teils; Shutter-Logik stark, QSPI-Rundpanels ungewiss | MQTT | gering–mittel | Display-Support für die runden QSPI-Panels nicht belegt; eigene Stall-Logik nur via Berry-Scripting |
| F | **Matter (esp-matter)** | ✅ | ökosystemoffen (HA, Apple, Google) | hoch | WLAN-gebunden auf dem S3; Custom-Funktionen (Lasterkennung, Stern) passen schlecht in Standard-Cluster |

## 4. Entscheidung

> **Pfad B: ESPHome bleibt Integrationsrahmen, verliert aber jedes Vetorecht über
> die Hardware.** Fehlende Treiber werden als External Component um den offiziellen
> Espressif-Treiber gewickelt. Für den RS-485-Primärbetrieb wird zusätzlich
> `modbus_server` mit einer festen Registerkarte vorgesehen — damit ist die
> HA-Anbindung auch ohne WLAN frameworkneutral.

Begründung: „ESPHome-ready" ist eine Anforderung an dieses Projekt und bleibt
erfüllt. B kostet pro fehlendem Treiber einige Tage einmalig; C/D kosten Wochen
und ersetzen Dinge, die nicht kaputt sind. Und B lässt sich jederzeit zu C/D
weiterentwickeln — **wenn die folgende Architekturregel eingehalten wird.**

### Architekturregel: frameworkfreier Kern

> Sämtliche Gerätelogik — Motorregelung, Lasterkennung, Trip-Handling,
> Display-Zustandsmaschine — wird als **reine C++-Klassen ohne jede
> ESPHome-Abhängigkeit** geschrieben (kein `esphome::`-Include im Kern). ESPHome
> sieht nur dünne Glue-Komponenten, die Kernmethoden aufrufen und Entitäten
> spiegeln. Gleiches gilt für die Modbus-Registerkarte: sie spricht mit dem Kern,
> nicht mit ESPHome.

Damit ist ein späterer Wechsel zu IDF+MQTT oder Modbus-only ein Austausch der
Glue-Schicht — kein Rewrite. Das ist die eigentliche Absicherung gegen
Framework-Risiko (Projektpolitik, Lizenzänderungen, Bruch-Releases): nicht der
Verzicht auf das Framework, sondern seine Quarantäne in einer dünnen Schicht.

## 5. Konsequenz für die Displaywahl (Revision 3)

Mit der Katalog-Fessel fällt der Grund für den AMOLED-Kompromiss:

> **Neue Primärempfehlung: 1,46"/1,5"-Rund-LCD mit ST77916 (360×360, SPI/QSPI),
> aktive Fläche Ø ≈ 37,25 mm.** Treiber: External-Component-Wrapper um
> [`espressif/esp_lcd_st77916`](https://components.espressif.com/components/espressif/esp_lcd_st77916)
> (offiziell, Apache-2.0). **Kein Einbrennen, keine Betriebsauflagen.**

- Die aktive Fläche (Ø 37,25) ist praktisch identisch mit dem AMOLED (Ø 36,3) —
  die Sichel-Geometrie deckelt ohnehin bei ~Ø 40. Der Größengewinn von „noch
  größeren" Panels ist mit vier Tasten nicht abholbar; das 1,6"-Panel (Ø 40,6)
  passt geometrisch nicht mehr.
- **Die Frontplatte v2 passt unverändert:** Fenster Ø 37,4 > aktiv Ø 37,25. Nur
  `disp_rebate_d` nach Vermessung des realen Moduls nachführen.
- Das **1,43"-AMOLED (CO5300) bleibt Plan B** mit null Treiberaufwand — samt der
  in [`09`](09-display-and-mcu.md) dokumentierten Einbrenn-Auflagen. Die
  eingecheckte YAML fährt bis zum ST77916-Wrapper auf diesem Plan B und ist
  validiert.
- Das 2,0"-Rechteck (ST7789V) bleibt die Option für maximale Fläche unter
  Aufgabe der runden Formensprache.

## 6. Arbeitsposten aus dieser Entscheidung

1. External Component `st77916_display`: Wrapper um `esp_lcd_st77916`,
   Anbindung an ESPHomes Display-Puffer-API. (Tage, nicht Wochen — der
   Controller-Teil existiert fertig.)
2. Motorregelungs-Kern als frameworkfreie Klasse anlegen (war ohnehin geplant,
   jetzt mit expliziter Regel).
3. Modbus-Registerkarte entwerfen (Coils/Register für 2 Covers, Sensorik,
   Stern, Trip-Status) und als `modbus_server`-Konfiguration hinterlegen.
4. `secrets`/Provisioning unverändert ESPHome.

Offene Punkte dazu in [`06-open-decisions.md`](06-open-decisions.md).
