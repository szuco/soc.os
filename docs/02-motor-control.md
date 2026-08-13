# 02 – Motorsteuerung, Strommessung, Überstromschutz

## 1. Anforderung

Beide Jalousiemotoren werden durch **Umpolung** vorwärts/rückwärts betrieben. Pro Motor
wird deshalb eine vollständige H-Bridge benötigt.

Auslegungsziel pro Kanal, gültig bis reale Motorwerte gemessen oder aus dem Datenblatt
bekannt sind:

- **≥ 5 A Dauerstrom**
- **≈ 10–15 A kurzzeitige Peak-Fähigkeit**

Nominal fließen ≈ 4,17 A (100 W / 24 V). Anlauf- und Blockierstrom sind unbekannt und
bei Bürsten-DC-Motoren typischerweise ein Vielfaches des Nennstroms.

## 2. Architektur

Zwei gleichwertige Optionen, Entscheidung offen:

- **Diskret:** vier N-Kanal-MOSFETs pro Brücke plus High-/Low-Side-Gate-Driver.
  Mehr Fläche, aber bessere Kontrolle über RDS(on), Verlustleistung und Sense-Topologie.
- **Integriert:** ein ausreichend dimensionierter Motor-Treiber-IC.
  Deutlich platzsparender auf Ø 52 mm und mit fertigem Schutzkonzept — die entscheidende
  Prüffrage ist die thermische Belastbarkeit im geschlossenen Unterputzgehäuse ohne
  Luftstrom.

Auf einer runden Ø-52-mm-Platine mit zwei Kanälen, DC/DC-Wandlern und Steckverbinder
ist der Platz knapp. Die integrierte Variante sollte deshalb zuerst geprüft werden.

**Vorgehen:** Kanal 1 vollständig entwickeln und prüfen, danach identisch für Kanal 2
duplizieren. In KiCad über hierarchische Sheets mit demselben Sheet-File, damit beide
Kanäle zwangsläufig identisch bleiben.

## 3. Ansteuerung

- **PWM** ermöglicht softwareseitige Geschwindigkeitsreduzierung.
- **Richtungswechsel nur nach definierter Stop-/Deadtime.** Zwei getrennte Zeiten nicht
  verwechseln:
  - *Elektrische Deadtime* zwischen High- und Low-FET eines Zweigs — Größenordnung
    hunderte Nanosekunden, wird vom Gate-Driver bzw. Treiber-IC geliefert.
  - *Mechanische Stopzeit* vor der Umpolung, damit der Motor wirklich steht.
    Startwert ≥ 300 ms, empirisch zu bestimmen.
- Signale je Kanal: `Mx_PWM`, `Mx_DIR`, `Mx_EN`, `Mx_FAULT`.
- **Maximale Laufzeit einer Bewegung: 60 s**, danach zwingend Abschaltung.
- Positionsfeedback erfolgt ausschließlich über Stromverlauf und Timeout. **Keine
  Endschalter.**

## 4. Strommessung

Die eigentliche Last- und Widerstandserkennung erfolgt in Software. Dafür erhält jeder
Motor eine **getrennte** analoge Strommessung.

**Startpunkt:** Low-Side-Shunt ≈ **10 mΩ**, Kelvin-Anschluss, ausreichend leistungsfähig
(≥ 2 W), plus Current-Sense-Amplifier. Verlustleistung am Shunt:

| Strom | P am 10-mΩ-Shunt | Sense-Spannung |
|---|---|---|
| 4,17 A nominal | 0,17 W | 41,7 mV |
| 5 A | 0,25 W | 50 mV |
| 13 A Hard-Trip | 1,69 W | 130 mV |

Die 2-W-Vorgabe ist damit für den Trip-Punkt richtig dimensioniert; bei häufigen
Blockierereignissen ist 3 W die sicherere Wahl.

Sense-Ausgänge `I_SENSE1` und `I_SENSE2` gehen an den ESP32 bzw. optional an einen
externen ADC. Optionales RC-Filter am ADC-Eingang reduziert PWM-Ripple.

> **Prüfpunkt — Shunt-Position und PWM.**
> Ein einzelner Shunt im gemeinsamen Low-Side-Rückpfad der Vollbrücke sieht den
> Motorstrom nur in bestimmten PWM-Zuständen. Während der Rückspeise-/Freilaufphase über
> die beiden Low-Side-FETs zirkuliert der Strom in der Brücke, ohne den Shunt zu
> passieren. Bei reduzierter PWM misst man dann systematisch zu wenig — genau in dem
> Betriebsfall, in dem die Lasterkennung gebraucht wird.
>
> Zwei saubere Auswege:
> - **Sampling mit der PWM synchronisieren** und ausschließlich in der aktiven Phase
>   messen. Erfordert einen ADC, dessen Trigger an das PWM-Timing gekoppelt ist — beim
>   ESP32-eigenen ADC unbequem und ein weiteres Argument für einen externen ADC.
> - **Inline-Messung im Motorzweig** mit bidirektionalem Current-Sense-Amplifier mit
>   ausreichendem Gleichtaktbereich. Misst in jedem PWM-Zustand und liefert zusätzlich
>   das Vorzeichen, kostet aber einen teureren CSA.
>
> Die Entscheidung fällt zusammen mit der Wahl von H-Bridge und CSA und ist in
> [`06-open-decisions.md`](06-open-decisions.md) offen geführt.

> **Prüfpunkt — ADC-Qualität.** Der interne ESP32-ADC ist nichtlinear und rauscht
> merklich. Für eine Lasterkennung, die auf *relativen* Änderungen beruht, kann er
> ausreichen; für reproduzierbare Absolutwerte und PWM-synchrones Sampling ist ein
> externer ADC auf dem Mid-Board die belastbarere Lösung.

## 5. Hardwareseitiger Überstromschutz

Zusätzlich zur Software ist ein hardwareseitiger Notaus vorgesehen: **Comparator + Latch
pro Motor** → Disable/Shutdown des Gate-Drivers. Dieser Schutz arbeitet **unabhängig von
ESP32 und Firmware** und muss auch bei abgestürzter oder nicht geladener Firmware wirken.

**Hardware-Trip pro Motor, nicht global** — ein Fehler an einem Kanal darf nicht
zwangsläufig beide Kanäle abschalten.

| Grenze | Startwert | Wirkung |
|---|---|---|
| Software-Soft-Limit | ≈ 9 A | PWM reduzieren, dann abschalten |
| Hardware-Hard-Trip | ≈ 13 A | Gate-Driver-Shutdown, **latched** |

Diese Werte sind vorläufig und müssen nach Messung der realen Anlauf- und Blockierströme
angepasst werden. Der Latch braucht einen definierten Reset-Pfad vom ESP32 (`TRIP_RST`)
und einen Zustand, den die Firmware lesen kann (`HW_TRIP1`/`HW_TRIP2`).

Auslegungsregel für die Reihenfolge der Schwellen:

```
Nennstrom  <  Anlaufstrom  <  Soft-Limit  <  Hard-Trip  <  Sicherung  <  FET-/Treiber-Grenze
 4,17 A         (unbekannt)      ~9 A          ~13 A
```

Der noch unbekannte Anlaufstrom sitzt mitten in dieser Kette. Übersteigt er 9 A, löst
das Soft-Limit bei jedem Start aus — deshalb ist die Messung der realen Anlaufströme der
kritische Pfad für die gesamte Schutzauslegung.

## 6. Software-Konzept

Ausgelagert nach [`../firmware/README.md`](../firmware/README.md). Kurzfassung:

- Maximale Bewegung 60 s, danach Abschaltung.
- Anlaufstrom in der Lastanalyse zunächst ausblenden, Startwert **≈ 600 ms** Blanking.
- Schnellen Strommittelwert gegen eine langsamere Baseline vergleichen und dadurch einen
  **relativen** Lastanstieg erkennen.
- Bei Lastanstieg PWM reduzieren; bei weiterem Anstieg bzw. Stall abschalten.
- Der Hardware-Hard-Trip bleibt davon vollständig unabhängig.
