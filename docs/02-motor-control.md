# 02 – Motorsteuerung, Strommessung, Überstromschutz

> **Motordaten liegen vor — dieses Dokument gilt unverändert.**
> Siehe [`11-motor-data.md`](11-motor-data.md): Der Antrieb ist ein **blanker
> Bürsten-DC-Getriebemotor mit zwei Adern und ohne eigene Elektronik**. Damit ist die
> H-Brücke zwingend, PWM ist erlaubt, und die **Hinderniserkennung ist Aufgabe dieses
> Geräts** — es gibt keine Selbsthilfe im Motor.
>
> Geändert hat sich nur: Fahrzeit real **18 s**, Timeout deshalb **30 s** statt 60 s.
> Der Laufstrom liegt bei ≈ 0,3–1,0 A, der **Blockierstrom ist unbegrenzt und
> unbekannt** (Größenordnung 8–30 A). Die Schwellenwerte in Abschnitt 5 sind bis zur
> Messung provisorisch.

## 1. Anforderung

Beide Jalousiemotoren werden durch **Umpolung** vorwärts/rückwärts betrieben. Pro Motor
wird deshalb eine vollständige H-Bridge benötigt.

Auslegungsziel pro Kanal, gültig bis reale Motorwerte gemessen oder aus dem Datenblatt
bekannt sind:

- **≥ 5 A Dauerstrom**
- **≈ 10–15 A kurzzeitige Peak-Fähigkeit**

Die 100 W des Datenblatts sind die **Maximalleistung** (≈ 4,63 A bei 21,6 V), nicht der
Dauerbetrieb — der liegt nach der Rechnung in [`11-motor-data.md`](11-motor-data.md)
bei ≈ 0,3–1,0 A. Anlauf- und Blockierstrom nennt das Datenblatt **nicht**; sie sind zu
messen (Protokoll M1–M3).

## 2. Architektur

**Entschieden: diskret.** Je Brücke zwei **IR2104**-Halbbrückentreiber und vier
N-Kanal-MOSFETs. Ausschlaggebend war der unbekannte Blockierstrom — ein integrierter
Treiber legt seine Stromgrenze fest, bevor sie gemessen ist. Mit diskreten FETs
bestimmt die FET-Auswahl die Grenze, und die lässt sich nach der Messung ändern,
ohne die Topologie anzufassen.

Der IR2104 bringt zudem einen `~SD`-Eingang mit, über den der Hardware-Latch die
Endstufe direkt abschaltet — ohne Umweg über Logik oder Firmware.

Preis dafür: acht FETs und vier Treiber auf Ø 52 mm. Das Board wird dicht und
beidseitig bestückt.

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
- Signale je Kanal: **`Mx_INA`, `Mx_INB`** — je ein PWM-faehiger Ausgang pro
  Bruueckenzweig. Vorwaerts = INA moduliert, INB low; rueckwaerts umgekehrt; beide
  low = bremsen. Das spart die frueher vorgesehenen `DIR`/`EN`-Leitungen und die
  externe Verknuepfungslogik. `~SD` der Treiber gehoert allein dem Hardware-Trip.
- **Maximale Laufzeit einer Bewegung: 30 s** (Fahrzeit real 18 s + Reserve),
  danach zwingend Abschaltung.
- Positionsfeedback erfolgt ausschließlich über Stromverlauf und Timeout. **Keine
  Endschalter, keine Motorelektronik** — die Hinderniserkennung ist vollständig
  Aufgabe dieses Geräts, siehe [`11-motor-data.md`](11-motor-data.md).

## 4. Strommessung

Die eigentliche Last- und Widerstandserkennung erfolgt in Software. Dafür erhält jeder
Motor eine **getrennte** analoge Strommessung.

**Umgesetzt im Schaltplan:** **Inline-Shunt 1 mΩ**, 4-Terminal (Kelvin), 1 W, im
Zweig A jeder Brücke — plus **INA240A2** (Verstärkung 50, bidirektional). Die
Inline-Position löst das Freilaufproblem im Prüfpunkt unten; INA240 ist genau für
diesen Fall gebaut und unterdrückt PWM-Gleichtaktsprünge.

| Strom | P am 1-mΩ-Shunt | Shuntspannung | INA240-Ausgang (Offset 1,65 V) |
|---|---|---|---|
| 0,5 A Lauf | 0,25 mW | 0,5 mV | 1,68 V |
| 4,17 A | 17 mW | 4,2 mV | 1,86 V |
| 22 A Trip | 0,48 W | 22 mV | 2,75 V |
| 33 A Vollausschlag | 1,09 W | 33 mV | 3,30 V |

Der Verstärker läuft aus **3,3 V**, damit sein Ausgang den ADC-Eingang bauartbedingt
nicht überfahren kann. Vor dem ADC sitzt ein RC-Filter 1 kΩ / 1 nF.

Sense-Ausgänge `I_SENSE1` und `I_SENSE2` gehen an den ESP32 bzw. optional an einen
externen ADC. Optionales RC-Filter am ADC-Eingang reduziert PWM-Ripple.

> **Prüfpunkt — Shunt-Position und PWM.**
> Ein einzelner Shunt im gemeinsamen Low-Side-Rückpfad der Vollbrücke sieht den
> Motorstrom nur in bestimmten PWM-Zuständen. Während der Rückspeise-/Freilaufphase über
> die beiden Low-Side-FETs zirkuliert der Strom in der Brücke, ohne den Shunt zu
> passieren. Bei reduzierter PWM misst man dann systematisch zu wenig — genau in dem
> Betriebsfall, in dem die Lasterkennung gebraucht wird.
>
> **Entschieden: Inline-Messung.** Der Shunt sitzt im Motorzweig, nicht im
> Low-Side-Rückpfad. Der INA240A2 hat den dafür nötigen Gleichtaktbereich und ist
> ausdrücklich für geschaltete Motorzweige gebaut. Damit misst die Schaltung in
> **jedem** PWM-Zustand und liefert zusätzlich das Vorzeichen des Stroms.

> **Prüfpunkt — ADC-Qualität.** Der interne ESP32-ADC ist nichtlinear und rauscht
> merklich. Für eine Lasterkennung, die auf *relativen* Änderungen beruht, reicht er;
> für reproduzierbare Absolutwerte wäre ein externer ADC besser. Die Entscheidung ist
> offen (Punkt 18) und **layoutneutral**: `I_SENSE1/2` liegen ohnehin auf `J_STK_A`.

## 5. Hardwareseitiger Überstromschutz

Zusätzlich zur Software ist ein hardwareseitiger Notaus vorgesehen: **Comparator + Latch
pro Motor** → Disable/Shutdown des Gate-Drivers. Dieser Schutz arbeitet **unabhängig von
ESP32 und Firmware** und muss auch bei abgestürzter oder nicht geladener Firmware wirken.

**Hardware-Trip pro Motor, nicht global** — ein Fehler an einem Kanal darf nicht
zwangsläufig beide Kanäle abschalten.

| Grenze | Startwert | Wirkung | Realisierung |
|---|---|---|---|
| Software-Soft-Limit | noch offen | PWM reduzieren, dann abschalten | Firmware |
| Hardware-Hard-Trip | **± 22 A** | `~SD` der IR2104 → Endstufe aus, **latched** | LM393-Fensterkomparator + 74AUP1G74, Schwelle über R7/R8/R9 |

Der Fensterkomparator trippt in **beiden** Stromrichtungen — bei Umpolung fließt der
Strom durch den Shunt in die andere Richtung, ein einzelner Komparator würde die
Hälfte der Fälle verpassen. Die beiden Open-Drain-Ausgänge sind auf eine aktiv-low
Leitung verdrahtet, die den Latch asynchron über `~PRE` setzt.

Der Latch (74AUP1G74) wird beim Einschalten über ein RC-Glied gelöscht und lässt sich
vom ESP32 über `TRIP_RST` zurücksetzen; sein Zustand geht als `HW_TRIP1`/`HW_TRIP2`
zurück an die Firmware.

Auslegungsregel für die Reihenfolge der Schwellen:

```
Laufstrom  <  Anlaufstrom  <  Soft-Limit  <  Hard-Trip  <  Sicherung  <  FET-/Treiber-Grenze
 0,3-1,0 A     (zu messen)    (zu messen)    ±22 A       15 A traege     >30 A
```

Anlaufstrom und Soft-Limit sind die einzigen noch offenen Glieder. Bis zur Messung
gilt die defensive Auslegung aus [`11-motor-data.md`](11-motor-data.md) Abschnitt 5.

## 6. Software-Konzept

Ausgelagert nach [`../firmware/README.md`](../firmware/README.md). Kurzfassung:

- Maximale Bewegung 30 s, danach Abschaltung.
- Anlaufstrom in der Lastanalyse zunächst ausblenden, Startwert **≈ 600 ms** Blanking.
- Schnellen Strommittelwert gegen eine langsamere Baseline vergleichen und dadurch einen
  **relativen** Lastanstieg erkennen.
- Bei Lastanstieg PWM reduzieren; bei weiterem Anstieg bzw. Stall abschalten.
- Der Hardware-Hard-Trip bleibt davon vollständig unabhängig.
