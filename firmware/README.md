# Firmware

ESP32-Firmware für KiCad SwitchStack. Dieses Dokument hält das festgelegte Konzept
fest, damit es die Hardwareauslegung mitbestimmen kann.

## Was heute läuft — und was nicht

`esphome/switchstack.yaml` ist mit `esphome config` validiert und deckt die
Grundfunktionen ab: Display mit Init-Sequenz, Backlight mit Präsenz-Dunkeltastung,
SHT4x, Expander, Hard-Trip-Meldung und -Reset, Verschlusskontakte, Stern,
Haubenkontakt, zwei Cover und vier Tasten.

**Die vier größten Lücken**, jede mit einem Grund:

| Fehlt | Warum |
|---|---|
| **Lasterkennung / Stall** | Braucht PWM-synchrones ADC-Sampling; ESPHomes Polling-Modell kann das nicht. Die Cover fahren deshalb **auf Zeit**. |
| **ToF-Distanz, ROI, Blendung** | ESPHome hat nur `vl53l0x` nativ; heute wird nur der Interrupt-Pin gelesen („da / nicht da"). |
| **Bedienmenü** | Die vier Tasten sind fest auf Auf/Zu verdrahtet. Die Belegung unten ist Anforderung, nicht Implementierung. |
| **RS-485-Protokoll** | UART ist konfiguriert, aber ungenutzt; `RS485_DIR` unbelegt. Das ist der *primäre* Kommunikationsweg. |

> **Die Konfiguration ist seit dem Displaywechsel nicht mehr mit `esphome config`
> geprüft** — auf dem Rechner, auf dem er entstand, war ESPHome nicht
> installiert. Vor dem ersten Flash validieren, besonders die Offsets des
> 240×280-Panels (0/20) und die Tastenpaar-Templates.

Die ersten beiden fallen in **dieselbe** External Component. Vollständige
Gegenüberstellung: [`../docs/13-funktionsstatus.md`](../docs/13-funktionsstatus.md).

## Architekturregel (verbindlich)

Aus [`../docs/10-firmware-strategy.md`](../docs/10-firmware-strategy.md):
**Gerätelogik frameworkfrei, Glue dünn.** Motorregelung, Lasterkennung,
Trip-Handling und Display-Zustandsmaschine sind reine C++-Klassen ohne
`esphome::`-Abhängigkeit. ESPHome (und eine spätere Modbus-Registerkarte)
docken über dünne Adapter an. ESPHome ist Integrationsrahmen — es hat kein
Vetorecht über die Hardwareauswahl; fehlende Treiber werden als External
Component um die offiziellen Espressif-Treiber (`esp_lcd_*`) gewickelt.

## Motor-Softwarekonzept

### Harte Grenzen

| Regel | Wert |
|---|---|
| Maximale Laufzeit einer Bewegung | **30 s** (Fahrzeit real 18 s + Reserve) |
| Blanking des Anlaufstroms in der Lastanalyse | **≈ 600 ms** (Startwert) |
| Mechanische Stopzeit vor Richtungswechsel | ≥ 300 ms (Startwert) |
| Software-Soft-Limit | ≈ 9 A (vorläufig) |
| Beginn des Sanftauslaufs | ab **≈ 80 %** der erwarteten Fahrzeit (Startwert) |
| PWM im Sanftauslauf | von 100 % auf ≈ **40 %** rampen (Startwert) |

### Endlagen: Zeitkonstante, Strom — und Sanftauslauf

**Die Endlage wird ausschließlich aus der Fahrzeit und dem Stromverlauf
bestimmt.** Es gibt keine Endschalter, und die Reed-Kontakte gehören nicht dazu
(Abschnitt unten).

Daraus folgt eine dritte Anforderung, die über reines Erkennen hinausgeht:
**Die Läden müssen langsamer werden, wenn sie sich der vermuteten Endlage
nähern.** Der Grund ist mechanisch — bei voller Drehzahl in den Anschlag zu
fahren belastet Getriebe, Beschlag und Mauerwerk, und der Stromanstieg beim
Auflaufen ist bei voller Fahrt so steil, dass die Abschaltung erst nach dem
Schlag kommt. Mit reduzierter Drehzahl wird der Anstieg flacher und früher
auswertbar, und der Anschlag wird weich.

Ablauf einer Fahrt:

1. **Anlauf**, die ersten ≈ 600 ms in der Lastanalyse ausgeblendet.
2. **Fahrt** mit voller PWM, Lastüberwachung nach dem Verfahren unten.
3. **Sanftauslauf** ab ≈ 80 % der erwarteten Fahrzeit: PWM linear auf ≈ 40 %
   rampen. Die Schwellwerte der Lastanalyse müssen dabei mitgeführt werden —
   bei halber PWM ist auch der Normalstrom kleiner.
4. **Abschaltung** beim Stromanstieg des Anschlags, spätestens nach 30 s.

Die erwartete Fahrzeit ist keine Konstante für die Ewigkeit: Sie ist je Laden
und Richtung zu führen und nach jeder sauber beendeten Fahrt nachzuziehen —
sonst wandert der Umschaltpunkt mit Temperatur und Verschleiß aus dem Fenster.
Startwert ist die Datenblatt-Fahrzeit von 18 s.

### Lasterkennung

Positionsfeedback erfolgt ausschließlich über **Stromverlauf und Timeout**. Es gibt
keine Endschalter.

Verfahren:

1. Beim Start des Motors die ersten ≈ 600 ms in der Lastanalyse ausblenden, damit der
   Anlaufstrom nicht als Blockade gewertet wird.
2. Danach einen **schnellen Strommittelwert** gegen eine **langsamere Baseline**
   vergleichen. Bewertet wird der **relative** Anstieg, nicht der Absolutwert — dadurch
   ist das Verfahren unempfindlich gegen Exemplarstreuung, Temperatur und
   Versorgungstoleranz.
3. Bei erkanntem Lastanstieg zunächst die PWM reduzieren.
4. Bei weiterem Anstieg bzw. Stall abschalten.
5. Nach 30 s in jedem Fall abschalten.

Der **Hardware-Hard-Trip bleibt davon vollständig unabhängig** und wirkt auch bei
abgestürzter oder nicht geladener Firmware. Die Firmware darf sich niemals darauf
verlassen, alleiniger Schutz zu sein — und umgekehrt darf der Hardware-Trip nicht als
regulärer Betriebszustand eingeplant werden.

### Abhängigkeiten zur Hardware

Diese Punkte müssen vor der Implementierung geklärt sein:

- **Sense-Topologie.** Bei Low-Side-Shunt muss das ADC-Sampling PWM-synchron erfolgen,
  sonst misst die Lasterkennung bei reduzierter PWM systematisch zu wenig — genau im
  Betriebsfall aus Schritt 3. Siehe [`../docs/02-motor-control.md`](../docs/02-motor-control.md).
- **ADC-Quelle.** Interner ESP32-ADC oder externer ADC. Der interne ADC ist nichtlinear
  und für relative Auswertung grenzwertig brauchbar, für PWM-synchrones Sampling aber
  unbequem.
- **Reale Anlaufströme.** Bestimmen das Blanking-Fenster und das Soft-Limit.
- **Gleichzeitiger Motorbetrieb.** Falls ein Interlock entschieden wird, ist er in der
  Firmware als harte, nicht umgehbare Regel zu implementieren — die
  Steckverbinder- und Sicherungsauslegung hängt dann davon ab. Siehe
  [`../docs/01-power-tree.md`](../docs/01-power-tree.md).

## Verhaltensregeln aus dem Vorgängerprojekt

Vier Festlegungen stammen aus der SoC-OS-Firmware und gelten sprachunabhängig
weiter. Sie sind **als Anforderung übernommen, nicht als Code** — die Altfirmware
war ein Laboraufbau, in dem Watchdog, Buzzer, BIST und Menü auskommentiert waren.
Herleitung und ehrliche Einordnung: [`../docs/12-legacy-socos.md`](../docs/12-legacy-socos.md)
Abschnitt 4.

| Regel | Inhalt |
|---|---|
| **BIST beim Hochlauf** | Vor dem Start der Regeltasks ein definierter Selbsttest mit hörbarer und sichtbarer Quittung (Piezo-Ton, Displaybild). In einer zugeschraubten Unterputzdose ist das der einzige Funktionsnachweis der Peripherie ohne Bus. |
| **Heartbeat** | Ein Lebenszeichen im festen Takt (Original: LED alle 500 ms), unabhängig von Bus und Display. Trennt „Firmware hängt" von „Kommunikation gestört" — zwei Fehlerbilder, die sonst identisch aussehen. |
| **Tastenbelegung** | Vier Tasten. **Achtung, die Hardware liefert sie nicht direkt:** Die Zentralscheibe trägt die Symbole ↑ ▷ ↓ OK auf den Achsen, überträgt den Druck aber auf vier Taster an den **Ecken**. Jede Richtung ist ein *Paar*: ↑ = oben links + oben rechts, ↓ = unten links + unten rechts, ▷ = links oben + links unten, OK = rechts oben + rechts unten. Die Zuordnung Paar → Funktion gehört in die Eingabeschicht, bevor das Menü sie sieht. Ursprüngliche Belegung aus dem Vorgängerprojekt: **OK / Hoch / Runter / Home**. `Home` führt aus *jeder* Menütiefe direkt zur Hauptansicht zurück; das Original hatte dafür zusätzlich einen eigenen RESET-Taster, den diese Hardware nicht mehr hat. Entprellung 50 ms, flankengetriggert. Offen als Punkt 37 in [`../docs/06-open-decisions.md`](../docs/06-open-decisions.md). |
| **Eine Task je Funktionsblock** | Kooperatives Modell mit eigener Periode je Block (Motor, Sensorik, UI, Kontakte) statt einer Sammelschleife. Deckt sich mit der frameworkfreien Kernregel oben. |

### Die Reed-Kontakte sichern das Fenster, nicht den Laden

**Festgelegt am 15.08.2026, und zwar gegen die Herleitung aus dem Vorgängerprojekt.**
`REED1_IN`/`REED2_IN` überwachen **das Fenster** — geschlossen oder offen. Mit der
Endlage der Klappläden haben sie **nichts** zu tun, und die Motorlogik darf sie
dafür auch nicht heranziehen.

Das korrigiert eine frühere Fassung dieses Abschnitts. Sie schloss aus den
Blattnamen des Vorgängerentwurfs („Verschlussüberwachung Links/Rechts") auf eine
Endlagenmeldung und nannte die Kontakte den „einzigen absoluten Positionsbezug im
System". Das war eine Übernahme aus alten Unterlagen, keine Festlegung für dieses
Gerät. Der Einordnung in [`../docs/12-legacy-socos.md`](../docs/12-legacy-socos.md)
ist damit die Grundlage entzogen.

Praktische Folge: **Es gibt keinerlei absolute Positionsrückmeldung der Läden.**
Die Endlagenbestimmung ruht vollständig auf den zwei Verfahren im nächsten
Abschnitt, und der Sicherheitsfall „Laden fährt gegen ein Hindernis" wird
ausschließlich vom Strom erkannt.

## Weitere Funktionsbereiche

Noch nicht spezifiziert, aus der Hardware abgeleitet:

- RS-485 als primäres Protokoll — Protokollwahl offen
- Präsenzauswertung über den ToF-Sensor VL53L1X (ersetzt den früheren Radar)
- Runddisplay-Anzeige und Bedienung über vier Taster
- Temperatur- und Feuchtemessung — Zuordnung Innen-/Außenmessung offen, Punkt 35
- Alarmierung über Piezo
- Ansteuerung des Stern-Ausgangs und des Haubenkontakts (PhotoMOS)
- Sabotagekontakte, falls Punkt 34 dafür entschieden wird
- WLAN sekundär
