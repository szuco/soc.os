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
| **M6** | **Ankerwiderstand** | Motor **stromlos**, Multimeter an die zwei Adern, Welle langsam von Hand drehen | kleinster abgelesener Wert → `I_Blockier ≈ 24 V / R` |

> **M6 ist die sichere Alternative zu M3** und braucht nur ein Multimeter. Der
> Bürstenübergang macht den Messwert winkelabhängig — deshalb drehen und den
> **kleinsten** Wert nehmen. Ein Wert von z. B. 1,2 Ω bedeutet 20 A Blockierstrom.
> Wenn du nur eine Messung machen willst, mach diese.

> **Zu M3, Sicherheit:** nur kurz, nur mit Strombegrenzung, und den Motor danach
> abkühlen lassen. Ein dauerhaft blockierter DC-Motor brennt durch.

### Was jede Messung freischaltet

| Messung | Schaltet frei |
|---|---|
| M1 | Leiterbahnbreiten für den Dauerbetrieb, Kühlkonzept, Shunt-Verlustleistung |
| M2 | Bulk-Kondensatoren, Sicherungscharakteristik, Soft-Limit-Schwelle |
| M3 / M6 | **Hard-Trip-Schwelle, MOSFET-/Treiberauswahl, Steckverbinder, Sicherung** |

## 5. Trotzdem weiterarbeiten: die defensive Auslegung

Der Schaltplan muss nicht auf die Messung warten. Er muss nur so ausgelegt werden,
dass er den **ungünstigsten plausiblen Fall** übersteht — und dass die wenigen
messabhängigen Größen als **Widerstandswerte** ausgeführt sind, die sich nachträglich
ändern lassen, ohne das Layout anzufassen.

**Auslegungsannahme bis zur Messung: 25 A Blockierstrom je Kanal, 1 s lang.**

| Bauteil | Auslegung | Messabhängig? |
|---|---|---|
| H-Brücke / MOSFETs | ≥ 30 A Peak, ≥ 10 A Dauer, R_DS(on) klein | nein — Reserve |
| Shunt | 10 mΩ, ≥ 3 W, Kelvin | nein |
| Current-Sense-Amp | Messbereich bis 30 A | nein |
| **Comparator-Referenz** | **Widerstandsteiler** | **ja — ein Wert** |
| **Soft-Limit** | Firmware-Konstante | **ja — eine Zahl** |
| **Sicherung** | steckbar oder Lötsicherung | **ja — ein Bauteil** |
| Bulk-Kondensator | 470–1000 µF, niedrig bauend | nein |
| Steckverbinder | für 25 A kurzzeitig auswählen | nein |

Damit hängen an der Messung genau **drei Werte**, keiner davon layoutrelevant. Der
Bottom-Schaltplan kann also sofort beginnen; die Messung muss lediglich **vor der
Bestellung** vorliegen.

Umgekehrt gilt: Fällt der gemessene Blockierstrom deutlich unter 25 A, lassen sich
Treiber und Steckverbinder später verkleinern. Zu klein anzufangen und nach der
Messung neu zu layouten wäre der teurere Weg.
