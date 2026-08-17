# 11 – Motordaten und Messprotokoll

Quelle: Herstellerdatenblatt des Klappladen-Antriebs (Drehflügelmotor für
Fensterläden), ergänzt um Angaben des Nutzers zum realen Motor.

> **Korrektur gegenüber der ersten Fassung dieses Dokuments.**
> Ich hatte aus der Zeile „Art des Endschalters: dynamisch" geschlossen, der Motor
> bringe eigene Elektronik mit Hinderniserkennung mit, und daraus zwei angenehme
> Folgerungen gezogen: PWM sei vermutlich verboten, und die interne Strombegrenzung
> deckele den Blockierstrom auf ≈ 4,6 A.
>
> **Beides war falsch.** Der Motor hat **keine eigene Elektronik**. Die dynamische
> Hinderniserkennung leistet der externe Controller — also genau das Gerät, das
> dieses Projekt ersetzt. Der Motor ist ein **blanker Bürsten-DC-Getriebemotor mit
> zwei Adern**. Die Konsequenzen stehen in Abschnitt 3 und gehen in die
> unangenehme Richtung.

## 0. Das Original ist identifiziert

Der Antrieb ist ein **MANTION SMT „URANUS"**, der Steuerung liegt der Controller
**K0000230** bei (24 V DC, Made in France, Klemmen `1A/1B` = Motor 1,
`2A/2B` = Motor 2, dazu ein Prog-Taster). Das Datenblatt bestätigt die bisher
angenommenen Werte — 24 V DC ±10 %, 100 W, 25 Nm, 1,9 U/min, 18 s Fahrzeit,
−20/+60 °C, 50 kg je Flügel — und liefert zwei Angaben, die vorher fehlten:

**„Type de fin de course: Dynamique (arrêt sur obstacle)."** Der Hersteller
selbst kennt keine Endschalter, sondern erkennt den Anschlag am Widerstand.
Das ist die externe Bestätigung für den ganzen Ansatz dieses Projekts: Die
Endlage über Fahrzeit und Stromverlauf zu bestimmen ist nicht der Notbehelf,
für den es aussehen könnte, sondern genau das, was das Original auch tut.

**Beim Schließen fährt Flügel 2 um 6 Sekunden versetzt.** Wörtlich aus der
Anleitung: *„Lors de la fermeture le battant 2 démarre avec un décalage de 6 s."*
Zweiflügelige Klappläden überlappen im geschlossenen Zustand — der überdeckende
Flügel muss zuletzt schließen und zuerst öffnen, sonst schlagen sie aufeinander.
Das ist **keine Komfortfunktion, sondern eine Kollisionsvermeidung**, und in
dieser Firmware fehlt sie: `taste_runter` schließt heute beide gleichzeitig.
Aufgenommen als Punkt 53.

Der Controller lernt seine Fahrzeiten übrigens selbst — ein Zyklus „ganz auf,
dann zu" auf Knopfdruck. Das ist das Vorbild für eine spätere Einlernfunktion.

## 1. Gesicherte Daten

| Angabe | Wert | Bedeutung fürs Design |
|---|---|---|
| Spannung | **24 V DC ±10 %** (21,6–26,4 V) | bestätigt den Power-Tree |
| Leistung (Typenschild) | **100 W** | siehe Abschnitt 2 — **keine harte Obergrenze** |
| Motormoment | **25 Nm** | |
| Drehzahl | **1,9 U/min** | |
| Fahrzeit | **18 s** (≈ 205° Schwenk) | Timeout **30 s** |
| **Adern je Motor** | **2** | **Umpolung ⇒ H-Brücke zwingend** |
| Eigene Elektronik | **keine** | Hinderniserkennung ist Aufgabe **dieses** Geräts |
| Betriebstemperatur | −20 … +60 °C | betrifft nur den Motor, nicht die Elektronik in der Dose |
| Höchstgewicht je Flügel | 50 kg | mechanisch |

Anschluss am unteren Steckverbinder: 2 × 24 V-Versorgung + 4 Motoradern = **6 Pins**.
Das bestätigt das bestehende Pinout in [`04-mechanical.md`](04-mechanical.md).

## 2. Laufstrom niedrig, Blockierstrom offen

Die Rechnung aus Moment und Drehzahl gilt unverändert — sie ist reine Physik und
hängt nicht an der Elektronikfrage:

```
P_mech = 25 Nm × (1,9 U/min × 2π/60) = 25 × 0,199 rad/s ≈ 4,97 W
```

| Getriebewirkungsgrad | elektrische Aufnahme | Strom bei 24 V |
|---:|---:|---:|
| 70 % | 7,1 W | 0,30 A |
| 50 % | 9,9 W | 0,41 A |
| 30 % | 16,6 W | 0,69 A |
| 20 % | 24,9 W | 1,04 A |

**Der Laufstrom liegt also weiterhin bei etwa 0,3–1,0 A.** Das Typenschild nennt
100 W — das Zwanzigfache der Abtriebsleistung.

**Was sich geändert hat:** Ohne interne Elektronik gibt es **nichts, was den Strom
begrenzt.** Bei blockiertem Läufer gilt schlicht

```
I_Blockier = U / R_Anker
```

und dieser Wert kann ein Vielfaches der 4,17 A betragen, die sich aus den 100 W
ergeben. Bei Bürsten-DC-Motoren dieser Klasse sind **8–30 A** plausibel. Die 100 W
sind dann eher die Nennaufnahme oder die empfohlene Netzteilgröße, keine Schranke.

> **Die Spreizung ist die eigentliche Nachricht:** Laufstrom ≈ 0,5 A, Blockierstrom
> vielleicht 20 A — ein Faktor 40. Für die **Lasterkennung ist das ideal**, weil das
> Nutzsignal riesig ist. Für die **Leistungsauslegung ist es unangenehm**, weil die
> Endstufe einen Strom überstehen muss, der weit über allem liegt, was im
> Normalbetrieb je fließt.

## 3. Was die Korrektur zurückholt

Die erste Fassung hatte drei Vereinfachungen in Aussicht gestellt. Alle drei sind
hinfällig:

| erste Fassung (falsch) | tatsächlich |
|---|---|
| PWM vermutlich verboten | **PWM ist erlaubt** — nichts im Motor, das gestört werden könnte. Geschwindigkeitsreduzierung bleibt möglich |
| Stall-Erkennung redundant | **Stall-Erkennung ist Kernfunktion.** Ohne sie fährt der Antrieb gegen ein Hindernis, bis der Timeout greift |
| PWM-synchrone Messung entfällt | **Bleibt in voller Schärfe** — samt Konflikt mit ESPHomes Polling-Modell und dem Bedarf an einer C++-Komponente |
| Hard-Trip evtl. 6–7 A ausreichend | **Muss den vollen Blockierstrom abkönnen**, Größenordnung 15–25 A |
| Steckverbinder-Engpass entschärft | Dauerstrom klein, aber **Blockierstrom über den Steckverbinder** muss er aushalten |

Damit gelten [`02-motor-control.md`](02-motor-control.md) und
[`09-display-and-mcu.md`](09-display-and-mcu.md) Abschnitt 4 wieder unverändert.

**Sicherheitsrelevant:** Klemmt ein Laden, steht der Motor unter voller
Blockierspannung, bis etwas abschaltet. Es gibt keine Selbsthilfe im Motor. Die
Kette Software-Soft-Limit → Hardware-Hard-Trip → Sicherung ist damit nicht Komfort,
sondern **die einzige Schutzebene**. Sie muss auch bei nicht geladener Firmware
wirken — deshalb bleibt der Comparator-plus-Latch pro Kanal zwingend.

## 4. Messprotokoll

Drei Messungen, ohne Elektronik dieses Projekts — Labornetzteil und Strommessung.

**Aufbau:** Labornetzteil 24 V mit einstellbarer Strombegrenzung und Anzeige, besser
Stromzange oder Shunt am Oszilloskop. Für den Anlaufstrom reicht ein Multimeter
**nicht** — er ist zu kurz.

| # | Messung | Wie | Notieren |
|---|---|---|---|
| **M1** | **Laufstrom** | Laden komplett auf und zu fahren, montiert | Mittelwert, Maximum, Verlauf über 18 s |
| **M2** | **Anlaufstrom** | Einschaltmoment | Spitzenwert, Dauer bis zum Einschwingen |
| **M3** | **Blockierstrom** | **Strombegrenzung am Netzteil auf 10 A**, Abtrieb blockieren, **maximal 1–2 s** | Strom bei Blockade; falls das Netzteil in die Begrenzung geht: Begrenzung schrittweise anheben |
| **M6** | **Ankerwiderstand** | Motor **stromlos**, Multimeter an die zwei Adern. Welle **nicht** von Hand drehbar (Schneckengetriebe selbsthemmend) — stattdessen: messen, Motor kurz ein Stück fahren, erneut messen, **10×** wiederholen | **kleinsten** aller Werte nehmen → `I_Blockier ≈ 24 V / R` |
| **M7** | **Kleinspannungsmethode** | Labornetzteil auf **2 V**, Strom messen. Bei so wenig Spannung überwindet der Motor die Haftreibung des Schneckengetriebes nicht und steht | `I_Blockier ≈ 24 V × I_gemessen / 2 V` |

> **Korrektur zu M6:** In der ersten Fassung stand „Welle langsam von Hand drehen".
> Das geht bei einem selbsthemmenden Schneckengetriebe nicht. Der Bürstenübergang
> macht den Messwert trotzdem winkelabhängig — deshalb mehrfach messen und den
> Motor dazwischen mit eigener Kraft ein Stück versetzen.

> **Nullpunkt nicht vergessen — sonst ist M6 wertlos.** Erwartet werden rund
> **1 Ω** (24 V / 25 A). Messleitungen und Messgerät bringen selbst 0,2–0,5 Ω
> mit, also bis zur Hälfte des Messwerts. Deshalb **zuerst die Messspitzen
> gegeneinander halten**, diesen Wert notieren und vom Ergebnis abziehen. Wer
> das auslässt, misst den doppelten Widerstand und damit den halben
> Blockierstrom — und legt die Sicherung zu klein aus.

> **M7 ist die verlässlichste einfache Messung.** Sie umgeht das Bürstenproblem
> vollständig, weil der Strom über mehrere Lamellen mittelt, und braucht kein
> Oszilloskop. Wenn du nur eine Messung machst, mach diese.

### Was jede Messung freischaltet

| Messung | Schaltet frei |
|---|---|
| M1 | Leiterbahnbreiten für den Dauerbetrieb, Kühlkonzept, Shunt-Verlustleistung |
| M2 | Bulk-Kondensatoren, Sicherungscharakteristik, Soft-Limit-Schwelle |
| M3 / M6 / M7 | **Hard-Trip-Schwelle (R7/R8/R9), MOSFET-/Treiberauswahl, Steckverbinder, Sicherung F1** |

## 5. Trotzdem weiterarbeiten: die defensive Auslegung

Der Schaltplan muss nicht auf die Messung warten. Er muss nur so ausgelegt werden,
dass er den **ungünstigsten plausiblen Fall** übersteht — und dass die wenigen
messabhängigen Größen als **Widerstandswerte** ausgeführt sind, die sich nachträglich
ändern lassen, ohne das Layout anzufassen.

**Auslegungsannahme bis zur Messung: 25 A Blockierstrom je Kanal, 1 s lang.**

| Bauteil | Auslegung | Messabhängig? |
|---|---|---|
| H-Brücke / MOSFETs | ≥ 30 A Peak, ≥ 10 A Dauer, R_DS(on) klein | nein — Reserve |
| Shunt | **1 mΩ**, 1 W, 4-Terminal/Kelvin | nein |
| Current-Sense-Amp | INA240A2, Verstärkung 50, aus 3,3 V → ADC-sicher | nein |
| **Comparator-Referenz** | Widerstandsteiler **R7/R8/R9** | **ja — drei Widerstände** |
| **Soft-Limit** | Firmware-Konstante | **ja — eine Zahl** |
| **Sicherung** | **F1**, aktuell 15 A träge | **ja — ein Bauteil** |
| Bulk-Kondensator | 470–1000 µF, niedrig bauend | nein |
| Steckverbinder | für 25 A kurzzeitig auswählen | nein |

Damit hängen an der Messung genau **drei Positionen**, keine davon layoutrelevant.
Der Bottom-Schaltplan ist auf dieser Basis **fertig** — siehe
[`../hardware/bottom_power_motor/`](../hardware/bottom_power_motor/). Die Messung
muss lediglich **vor der Bestellung** vorliegen.

Konkret im erzeugten Schaltplan: Mit **1 mΩ Shunt** und **INA240A2 (Verstärkung 50)**
liegt der Messbereich bei ±33 A, die Trip-Schwelle über R7/R8/R9 bei **±22 A**.
Ergibt die Messung deutlich weniger, werden nur diese drei Widerstände getauscht.

Umgekehrt gilt: Fällt der gemessene Blockierstrom deutlich unter 25 A, lassen sich
Treiber und Steckverbinder später verkleinern. Zu klein anzufangen und nach der
Messung neu zu layouten wäre der teurere Weg.
