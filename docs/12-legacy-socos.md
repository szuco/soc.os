# 12 – Vorgängerprojekt „SoC OS": übernommene Anforderungen

Dieses Dokument wertet den Altbestand **SoC OS v1.0.0** aus (2021–2024, zuletzt als
loser Ordner `soc-os-orig/` neben dem Repository).

Zweck: **SwitchStack ist der vierte Anlauf desselben Geräts.** Die
Funktionsanforderungen stammen aus SoC OS, nicht aus dem aktuellen Repository —
und zwei davon sind auf dem Weg verlorengegangen. Dieses Dokument macht sie
wieder sichtbar und markiert, was bewusst entfallen ist.

> **Die Dateien selbst sind gelöscht.** Sie lagen zuletzt unter `archive/` und
> sind ausschließlich über die Git-Historie erreichbar — der Commit *„Altbestand
> vollständig eingecheckt"* enthält sie unverändert
> (`git log --diff-filter=D -- archive/`, dann `git show <commit>:archive/…`).
> Dieses Dokument ist damit **die** Quelle: Es ist so geschrieben, dass die
> Dateien nicht mehr gebraucht werden. Was hier nicht steht, ist bewusst
> verworfen — die Prüfung dazu steht in Abschnitt 8.

## 1. Die Revisionskette

| Revision | Zeitraum | MCU | Zustand im Altbestand |
|---|---|---|---|
| **v0** | 2022 | Arduino Pro Mini | Schaltplan mit dem **vollständigen Feld-Interface** — die inhaltlich wertvollste Quelle |
| **v1** | 2022 | RP2040 | nur Projektdatei, kein Schaltplan |
| **v2** | 2023 | RP2040 + W25Q128 | Schaltplan, 148 kB, ohne Feldperipherie |
| **v3** | 2023/24 | **ESP32-C3** | Schaltplan mit 85 Symbolen, 3 × DRV8874, Funktionsblöcke benannt |
| **v4** | 2026 | ESP32-S3 | frühe Fassung **dieses** Projekts (`top_ui`/`mid_logic`/`bottom_power_motor`) — vollständig durch den aktuellen Stand überholt, nichts zu übernehmen |

Dazu MicroPython-Firmware für ESP32 (`socos/`) mit Modulen für Temperatur,
Fensterkontakte, Abzugshaube, Buzzer, Menü und Heartbeat — zum tatsächlichen
Reifegrad siehe Abschnitt 4.

Erhalten war davon (Stand der Löschung, 736 Zeilen Python und 13 Schaltplanblätter):

| Ablage | Inhalt |
|---|---|
| `socos-esp32-firmware/` | `boot.py`, `main.py`, `pymakr.conf` und sechs Module unter `socos/` |
| `socos-kicad/v0-arduino/` | 16 Blätter, davon 8 mit Inhalt — `SocMain` (38 Symbole) ist das Feld-Interface |
| `socos-kicad/v2-rp2040/` | ein Blatt, 57 Symbole, RP2040 + W25Q128 + 12-MHz-Quarz |
| `socos-kicad/v3-esp32c3/` | ein Blatt, 35 Symbole, plus `TopSheet.pdf` |
| `pico-prototype/` | RP2040-Versuch: `button.py`, `monitor.py`, `watchdog.py` und zwei MicroPython-`.uf2`-Images (v1.17, 2021) |

## 2. Das ursprüngliche Feld-Interface (v0)

Der v0-Schaltplan legt an **zwei 10-poligen Schraubklemmen** fest, was das Gerät
nach außen können muss:

| Feldsignal | Heute | Status |
|---|---|---|
| 24 V Eingang | `24V_IN±` | ✅ übernommen |
| 24 V Motor Links / Rechts | `M1_A/B`, `M2_A/B` | ✅ übernommen |
| **230 V Stellmotor** (im Plan als Alternative: „Entweder / Oder") | — | ❌ **bewusst entfallen**, siehe Abschnitt 5 |
| A/B RS-485-Bus | `RS485_A/B` | ✅ übernommen |
| **Verschlussüberwachung Links / Rechts** | `REED1_IN` / `REED2_IN` | ✅ übernommen — aber siehe Namensklärung unten |
| **Sabotageüberwachung Links / Rechts** | — | ⚠️ **fehlt**, siehe Abschnitt 3 |
| **Externer Thermistor** | — | ⚠️ **fehlt**, siehe Abschnitt 3 |
| 5 Taster: UP, DOWN, LEFT, RIGHT, **RESET** | `BTN1`–`BTN4` | teilweise, siehe Abschnitt 4 |
| OLED SSD1306 0,96" I2C 128×64 | ST77916 360×360 rund | ✅ ersetzt, bessere Lösung |

> **Namensklärung `REED1/REED2`.** Im aktuellen Stand heißen die beiden Eingänge
> „Fenster 1" und „Fenster 2" ([`../firmware/esphome/switchstack.yaml`](../firmware/esphome/switchstack.yaml)).
> Im Original heißen sie **Verschlussüberwachung Links/Rechts**.
>
> **Diese Übernahme war falsch und ist am 15.08.2026 zurückgenommen worden.** Aus
> dem alten Blattnamen wurde hier geschlossen, die Kontakte meldeten die Endlage
> der Klappläden und seien damit „der einzige absolute Positionsbezug im ganzen
> System". Das ist eine Deutung alter Unterlagen, keine Festlegung für dieses
> Gerät — und die Festlegung lautet anders: **Die Reed-Kontakte sichern das
> Fenster. Mit den Endlagen der Läden haben sie nichts zu tun.** Die Endlage
> wird ausschließlich aus Fahrzeit und Stromverlauf bestimmt, samt Sanftauslauf
> vor dem Anschlag ([`../firmware/README.md`](../firmware/README.md)).
>
> Der Eintrag bleibt als Warnung stehen: Ein Blattname aus einem Vorgängerprojekt
> ist ein Hinweis, kein Nachweis.

### Der Signalsatz, wie ihn v2 und v3 führten

v2 und v3 tragen **denselben** Satz globaler Feldlabels — zwei unabhängige
Revisionen, gleiche Liste. Das ist die belastbarste Fassung des ursprünglichen
Feld-Interfaces, jedes Signal als Aderpaar:

| Label (Altbestand) | Bedeutung | heute |
|---|---|---|
| `POWER_24V_VCC/GND` | Versorgung | ✅ `24V_IN±` |
| `MOTOR_A±`, `MOTOR_B±` | zwei Motoren | ✅ `M1_A/B`, `M2_A/B` |
| `WOPENA±`, `WOPENB±` | **Verschluss**überwachung je Seite | ✅ `REED1_IN`, `REED2_IN` |
| `WPROTECTA±`, `WPROTECTB±` | **Sabotage**überwachung je Seite | ⚠️ fehlt (Punkt 34) |
| `EXT_TEMP±` | externer Fühler | ⚠️ fehlt (Punkt 35) |
| `INT_TEMP±` | Elektroniktemperatur | 🟡 SHT4x, aber als Raumfühler benannt (Punkt 35) |
| `EXHAUST±` | Dunstabzugshaube | ✅ PhotoMOS `RELAY_CTL` |
| `RS485±` | Bus | ✅ `RS485_A/B` |
| `EXT_POWER_6V_VCC/GND` | Sternversorgung | ✅ `6V2_STAR`, jetzt 2,5-mm-Klinke an der Front |
| `BUZZER_VCC/GND` | Signalgeber (bei v3 noch extern geführt) | ✅ Piezo on-board |

**Zwölf Funktionen, 24 Adern** an zwei 10-poligen Schraubklemmen plus
DC-Buchse. Heute sind es sechs Leistungsadern unten und ein 6-poliger JST-SH
für Reed und Haube — und selbst für den ist auf dem Mid-Board kein Platz
(Punkt 29). Das ist die eigentliche Kostenstelle des Ø-52-Formats.

## 3. Verlorene Funktionen — wieder aufgenommen

### 3.1 Sabotageüberwachung (2 zusätzliche Eingänge)

Der v0-Plan hat **je Laden zwei** Kontakte: Verschluss **und Sabotage**. Die
ESP32-Firmware bestätigt das — `socos/window.py` liest zwei getrennte Pins
(`WINDOW_REED_PIN`, `WINDOW_SABOTAGE_PIN`) und meldet die Zustände unabhängig.

Im aktuellen Stand existiert nur die Verschlussüberwachung. Das ist eine echte
Funktionslücke, kein Redesign-Gewinn: [`09-display-and-mcu.md`](09-display-and-mcu.md)
Abschnitt 5 vermerkt ausdrücklich, dass der ToF **keinen** Sabotageschutz liefert
(„Das Loch lässt sich zukleben") — und verweist dabei auf „die Reed-Kontakte", die
diese Funktion aber gar nicht mehr haben.

**Kostenpunkt heute:** Der PCF8574 auf dem Mid-Board ist mit P0–P7 **restlos
belegt**. Zwei weitere Eingänge brauchen einen zweiten Expander (eigene I2C-Adresse,
Platz auf Mid) oder die Reservepins am Stackverbinder. Beides kollidiert mit
Punkt 29 in [`06-open-decisions.md`](06-open-decisions.md) — für die vorhandenen
Kontakte gibt es schon keinen Feldstecker. Aufgenommen als Punkt 34.

### 3.2 Externer Temperaturfühler

Zwei unabhängige Belege: das Feldsignal „Externer Thermistor" in v0 und das eigene
Blatt `SocTemperature` mit **beiden** ausgearbeiteten Varianten —

- **DS18B20/DS18S20** (1-Wire, mit 10k Pull-up). Die Firmware `socos/temperature.py`
  ist dafür fertig: Bus-Scan, **mehrere Fühler an einer Leitung**, Anzeige je
  Geräte-ID, Wiederverbindung bei Verlust, 750 ms Wandlungszeit berücksichtigt.
- **NTC 10k, MF52-103, B = 3435, 1 %** als Analogvariante.

Der aktuelle Stand hat nur den **On-Board**-Sensor SHT4x. Der misst die Temperatur
*in der Unterputzdose*, direkt über einer Endstufe mit bis zu 3,9 A — als Raum- oder
Fensterlaibungstemperatur ist er damit systematisch falsch. Ein externer Fühler ist
keine Zusatzfunktion, sondern die Voraussetzung dafür, dass der Messwert überhaupt
etwas bedeutet. Aufgenommen als Punkt 35.

### 3.3 Umgebungslichtmessung

v3 hat einen benannten Funktionsblock „**Ambient light detection**" mit zwei
Fotodioden; v0 führt eine 5-mm-Fotodiode auf dem Blatt `SocRadar`; die ESP32-Pinout-
Datei hat den Platzhalter `# Ambient light`. Die Funktion war also über drei
Revisionen hinweg gesetzt.

Heute regelt nur der ToF die Displayhelligkeit (Präsenz an → hell). Ein Rundpanel in
einer Fensterlaibung sieht tagsüber direkte Sonne und nachts Dunkelheit — eine feste
Helligkeit ist in beiden Fällen falsch. Aufgenommen als Punkt 36.

### 3.4 Innentemperatur der Elektronik

v3 benennt einen Block „**Internal Temperature**" — getrennt von der Raummessung.
In einer geschlossenen 61-mm-Dose mit zwei H-Brücken ist das eine Schutzfunktion
(Derating, Abschaltung), keine Komfortanzeige. Der SHT4x kann sie faktisch
übernehmen, **wenn** man ihn so benennt und auswertet. Aufgenommen als Punkt 35
gemeinsam mit dem externen Fühler — die beiden Entscheidungen hängen zusammen.

### 3.5 Benannt, aber nie ausgearbeitet

v0 legt acht Funktionsblätter an, von denen vier leer geblieben sind:
`SternVersorgung`, `Umgebungssensor`, `Überwachung` — alle drei sind heute in
anderer Form abgedeckt — und **`Heizungssteuerung`**. Letztere hat im aktuellen
Projekt keine Entsprechung und auch keine Anforderung: kein Schaltausgang, keine
Sollwertlogik, kein Feldsignal. Der Haubenkontakt (PhotoMOS, potentialfrei, SELV)
wäre das nächstliegende Schaltglied, ist aber vergeben.

Hier wird **nichts** aufgenommen. Der Eintrag steht nur, damit ein leerer
Blattname später nicht als vergessene Zusage missverstanden wird: Es gab nie mehr
als die Überschrift.

## 4. Übernommenes Firmware-Konzept

### 4.1 Was die Altfirmware wirklich war

Ehrliche Einordnung, weil sie sonst mehr Gewicht bekommt, als ihr zusteht:
**Das war ein Laboraufbau, kein laufendes Gerät.** In `main.py` sind Watchdog,
Buzzer, BIST und Menü **auskommentiert**; gestartet werden nur die Temperatur-
und die Fensterkontakt-Task, und die Abzugshaube wird im Sekundentakt
umgeschaltet — als Test, nicht als Funktion. `window.py` gibt `open`/`close`
auf die Konsole aus, ohne Entprellung und ohne Zustandsmodell. Das Menü ist der
Demobaum der Fremdbibliothek `umenu` (WiFi / Lights / Main Info) mit
festverdrahteten Beispielwerten.

| Modul | Zeilen | Reifegrad |
|---|---:|---|
| `temperature.py` | 168 | am weitesten: DS18X20-Bus-Scan, mehrere Fühler, Geräte-ID, Wiederverbindung, 750 ms Wandlungszeit |
| `buzzer.py` | 182 | Tontabelle B0–DS8, Songabspielung, `bist()` = 1 s Ton bei 100 Hz — **nie aufgerufen** |
| `menu.py` | 175 | vier IRQ-Handler mit 50 ms Entprellung *im Interrupt* (so nicht übernehmbar), SSD1306 128×64 |
| `window.py` | 37 | zwei Pins mit Pull-up, 5-s-Abfrage, `print()` |
| `watchdog.py` | 31 | LED-Toggle im 500-ms-Takt |
| `exhaust.py` | 27 | ein GPIO, `on`/`off`/`toggle` |

Der Wert liegt deshalb **nicht im Code**, sondern in vier Festlegungen, die
unabhängig von Sprache und Framework gelten. Sie stehen jetzt in
[`../firmware/README.md`](../firmware/README.md):

| Konzept | Original | Warum es bleibt |
|---|---|---|
| **BIST beim Start** | `buzzer.bist()` — definierter Ton beim Hochlauf | Einziger Funktionsnachweis der Peripherie in einer zugeschraubten Dose |
| **Heartbeat** | `Watchdog.toggle()`, LED im 500-ms-Takt | Zeigt „Firmware läuft" ohne Bus und ohne Display |
| **Tastenbelegung** | OK / Hoch / Runter / **Home** (Menü-Reset), IRQ-getriggert, 50 ms Entprellung | Vier Tasten, eine davon muss aus jeder Menütiefe herausführen — v0 hatte dafür sogar einen eigenen RESET-Taster |
| **Kooperatives Task-Modell** | `uasyncio`, je Funktionsblock eine Task mit eigener Periode | Deckt sich mit der frameworkfreien Kernregel aus [`10-firmware-strategy.md`](10-firmware-strategy.md) |

Die Struktur `socos/` — ein Modul je Funktionsblock, Konstruktor bekommt die Pins,
Pinout zentral in einer Datei — ist dieselbe Aufteilung, die
[`10-firmware-strategy.md`](10-firmware-strategy.md) für den C++-Kern fordert.

## 5. Restriktionen aus dem Altbestand

- **230 V ist Vergangenheit, und das muss so bleiben.** v0 sah wahlweise 24-V-Motoren
  *oder* einen 230-V-Stellmotor vor. Der aktuelle Aufbau ist durchgehend SELV —
  Punkt 21 in [`06-open-decisions.md`](06-open-decisions.md) erlaubt den PhotoMOS
  ausdrücklich nur unter dieser Bedingung. **Jeder Rückgriff auf die 230-V-Variante
  wirft die gesamte Board-Aufteilung um** (Isolationsabstände, Kriechstrecken,
  Trennung im 9-mm-Stapelspalt). Die Option gilt als geschlossen, nicht als offen.
- **Sternversorgung: 6 V, I_max 300 mA.** So im v3-Plan beschriftet
  („Power supply for external devices (e.g. Christmas Stars)"). Der aktuelle Stand
  rechnet mit 6,2 V und ≈ 80 mA realer Last bei 0,5 A Buck-Auslegung
  ([`01-power-tree.md`](01-power-tree.md)) — die alte 300-mA-Grenze liegt genau
  dazwischen und bestätigt die Polyfuse-Wahl 0,3–0,5 A als Obergrenze, nicht als
  Reserve.
- **Feldverdrahtung war immer großzügig.** v0, v2 und v3 haben durchgehend
  **zwei** 10-polige Schraubklemmen, dazu eine DC-Buchse. Der Sprung auf Ø 52 mm
  hat diesen Komfort gekostet — Punkt 29 ist die direkte Folge. Beim Abwägen der
  vier Wege dort ist das die historische Referenz: Es waren einmal **zwölf
  Feldfunktionen an 24 Adern** vorgesehen (Liste in Abschnitt 2), heute sind es
  sechs Leistungsadern plus ein 6-poliger JST-SH.

## 6. Bauteilkandidaten aus dem Altbestand

Geprüfte Auswahl früherer Revisionen, verwendbar als Ausgangspunkt für noch offene
Punkte:

| Funktion | Altbestand | Bezug heute |
|---|---|---|
| RS-485-Transceiver | **MAX13450E** (v0, `SocCommunicaton`) | Kandidat für Punkt 16 — Fail-Safe-Bias eingebaut, ±35 kV ESD, 3,3 V |
| Temperatur extern | **DS18B20/DS18S20** (1-Wire, 10k Pull-up) oder **NTC MF52-103, B = 3435, 1 %** mit 10k Teiler | Punkt 35 — beide Varianten waren auf `SocTemperature` fertig gezeichnet |
| Motortreiber integriert | **DRV8874PWPR** (v3, 3 Stück) | Verworfen zugunsten diskret 2 × IR2104 + 4 N-FET, Punkt 7 — die Begründung in [`02-motor-control.md`](02-motor-control.md) Abschnitt 2 gilt weiter |
| High-Side-Schalter | BTS50080-1TEA (v0, `SocMotorControl`, mit 1k/2k-Teiler und ZMDxx-Klemmung) | historisch, für Umpolbetrieb ungeeignet |
| Abwärtsregler | LM2596T-5 (v0, zweimal: Eingang und Sternversorgung) | überholt — TPS54360DDA / TLV62569DBV, Punkte 4–6 |
| 3,3-V-LDO | NCP1117-3.3 SOT-223 (v2, v3) | überholt |
| Umgebungslicht | Fotodiode 5 mm mit 10k (v0 `SocRadar`), 2 × `D_Photo` (v3) | Punkt 36 |
| Anzeige | SSD1306 128×64 I2C, 0,96" (v0, v3) | ersetzt durch ST77916 360×360 rund |
| MCU-Historie | Arduino Pro Mini → RP2040 + W25Q128JVS → ESP32-C3 | heute ESP32-S3-WROOM-1-N16R8 |

## 7. Was nicht übernommen wurde

- **v4** — ältere Fassung dieses Projekts, in jedem Punkt vom aktuellen Stand überholt.
- **Raspberry-Pi-Zero- und Pico-Pfad** samt `micropython-nano-gui`, `encodermenu`,
  `esptool`-Clone, `.venv`, docToolchain/arc42-Gerüst (leer, nur Template-Kopf).
- **PIR-Datenblatt** — die Präsenzerkennung ist mit Punkt 17 auf ToF entschieden.
- Fremdbibliotheken unter `downloads/thirdparty/` — Upstream verfügbar, kein
  Projektinhalt.

## 8. Prüfung vor der Löschung des Archivs (15.08.2026)

Jede Ablage wurde einzeln daraufhin geprüft, ob sie über dieses Dokument hinaus
noch gebraucht wird. Ergebnis: **nein**, deshalb ist `archive/` entfernt.

| Ablage | Wofür sie in Frage kam | Warum sie nicht mehr gebraucht wird |
|---|---|---|
| `socos-esp32-firmware/socos/*.py` | Codeübernahme | Andere Zielhardware (ESP32-S3, Runddisplay, PCF8574) und anderer Firmwarepfad (C++/ESPHome). Von den Modulen ist nur das Verhalten gültig — es steht in Abschnitt 4 und in [`../firmware/README.md`](../firmware/README.md). Der 1-Wire-Ablauf für DS18B20 ist Standard und in jeder Bibliothek enthalten |
| `socos-esp32-firmware/socos/esp32.py` | Pinout | Legacy-Pinout eines ESP32-WROOM-Devkits ohne Bezug zu diesem Board. Verbindlich ist [`03-stack-pinout.md`](03-stack-pinout.md). Erhaltenswert war daraus genau eine Zeile: der Platzhalter `# Ambient light` als dritter Beleg für Punkt 36 |
| `socos-kicad/v0-arduino/` | Feld-Interface, Bauteile | Signalliste in Abschnitt 2, Bauteile in Abschnitt 6. Die Symbole hängen an nicht mitgelieferten Bibliotheken (`WindowShutterLib`, `conn1`, `dc-dc1`) und ließen sich ohnehin nicht fehlerfrei öffnen |
| `socos-kicad/v2-rp2040/` | — | Zwischenschritt ohne Feldperipherie; RP2040-spezifische Hinweise („C10 nah an Pin 44") sind für den ESP32-S3 wertlos |
| `socos-kicad/v3-esp32c3/` | Funktionsblöcke | Blocknamen und die 6-V-/300-mA-Beschriftung sind in den Abschnitten 2, 3 und 5 festgehalten. `TopSheet.pdf` war ein Ausdruck desselben Blattes |
| `pico-prototype/` | — | RP2040-Sackgasse; die beiden `.uf2`-Images sind MicroPython-Releases von 2021 und upstream verfügbar |

Die historische Inbetriebnahme des MicroPython-Pfades, falls sie je wieder
gebraucht wird — mehr als das war an Werkzeugwissen nicht enthalten:

```bash
pip3 install esptool
python3 -m esptool --chip esp32 --port /dev/tty.usbserial-0001 erase_flash
python3 -m esptool --chip esp32 --port /dev/tty.usbserial-0001 --baud 460800 \
    write_flash -z 0x1000 ESP32_GENERIC-<version>.bin
screen /dev/tty.usbserial-0001 115200      # beenden: CTRL-A, CTRL-\
```
