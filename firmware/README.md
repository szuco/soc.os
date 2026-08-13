# Firmware

ESP32-Firmware für KiCad SwitchStack. Die Implementierung beginnt nach dem
Hardware-Freeze. Dieses Dokument hält das bereits festgelegte Konzept fest, damit es
die Hardwareauslegung mitbestimmen kann.

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

## Weitere Funktionsbereiche

Noch nicht spezifiziert, aus der Hardware abgeleitet:

- RS-485 als primäres Protokoll — Protokollwahl offen
- Radar-Auswertung über UART
- OLED-Anzeige und Bedienung über vier Taster
- Temperatur- und Feuchtemessung
- Alarmierung über Piezo
- Ansteuerung des Stern-Ausgangs und des Mini-Relais
- WLAN sekundär
