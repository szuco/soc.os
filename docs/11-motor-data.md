# 11 – Motordaten und Messprotokoll

Quelle: Herstellerdatenblatt des Klappladen-Antriebs (Drehflügelmotor für
Fensterläden), vom Nutzer bereitgestellt.

## 1. Was das Datenblatt liefert

| Angabe | Wert | Bedeutung fürs Design |
|---|---|---|
| Spannung | **24 V DC ±10 %** (21,6–26,4 V) | bestätigt den Power-Tree |
| Leistung | **100 W** | Auslegungsgrenze — siehe Abschnitt 2 |
| Motormoment | **25 Nm** | |
| Drehzahl | **1,9 U/min** | |
| Öffnungs-/Schließzeit | **18 s** | ≈ 205° Schwenk — **Timeout kann von 60 s auf ~30 s** |
| **Art des Endschalters** | **dynamisch, stoppt bei Hindernissen** | **ändert die Architektur — Abschnitt 3** |
| Betriebstemperatur | −20 … +60 °C | Außenanwendung, unkritisch für die Elektronik in der Dose |
| Höchstgewicht je Flügel | 50 kg | mechanisch, keine Auswirkung |

## 2. Die 100 W sind fast sicher **nicht** die Laufleistung

Nachgerechnet aus Moment und Drehzahl:

```
P_mech = 25 Nm × (1,9 U/min × 2π/60) = 25 × 0,199 rad/s ≈ 4,97 W
```

Das Typenschild nennt **100 W — das Zwanzigfache der mechanischen Abtriebsleistung.**
Selbst mit einem sehr schlechten Schneckengetriebe geht die Rechnung nicht auf:

| Getriebewirkungsgrad | elektrische Aufnahme | Strom bei 24 V |
|---:|---:|---:|
| 70 % | 7,1 W | 0,30 A |
| 50 % | 9,9 W | 0,41 A |
| 30 % | 16,6 W | 0,69 A |
| 20 % | 24,9 W | 1,04 A |

**Schlussfolgerung:** Die 100 W sind die **Maximal- bzw. Blockierleistung**, nicht der
Dauerbetrieb. Der reale Laufstrom liegt vermutlich bei **0,3–1,0 A**, nicht bei 4,17 A.

Falls das stimmt — und das ist eine Schlussfolgerung, keine Messung — hätte es
angenehme Folgen:

| Größe | bisher angenommen | mit 100 W als Obergrenze |
|---|---:|---:|
| Strom je Motor, Dauer | 4,17 A | ≈ 0,3–1,0 A |
| Strom je Motor, Maximum | unbekannt, evtl. 25 A | **4,63 A** (bei 21,6 V) |
| Eingangsstrom, beide Motoren | ≈ 9,0 A | **≈ 10 A Spitze, ≈ 2 A Dauer** |
| Hardware-Hard-Trip | 13 A | vermutlich **6–7 A** je Kanal ausreichend |

Ein Bürsten-DC-Motor **ohne** Elektronik hätte einen Blockierstrom von U/R_Wicklung —
leicht 20–30 A. Dass das Datenblatt 100 W als harte Grenze nennt, passt nur zusammen,
wenn im Motor eine **strombegrenzende Elektronik** sitzt. Genau darauf deutet auch
Abschnitt 3.

## 3. Der wichtigste Fund: „Dynamischer Endschalter"

> **„Art des Endschalters: Dynamisch (stoppt bei Hindernissen)"**

Der Motor bringt **eigene Elektronik mit Hinderniserkennung** mit. Das ist kein
Detail, sondern greift die Architektur an drei Stellen an:

### 3.1 PWM ist damit vermutlich verboten

Motoren mit interner Auswertung erwarten **saubere Gleichspannung**. Wird die
Versorgung zerhackt, misst die interne Elektronik einen falschen Strom- bzw.
Gegen-EMK-Verlauf und die Hinderniserkennung wird unzuverlässig — im schlimmsten Fall
löst sie ständig aus oder gar nicht mehr.

**Konsequenz, wenn bestätigt:** Die geplante PWM-Geschwindigkeitsregelung entfällt.
Die H-Brücke schaltet dann nur noch **voll ein / Richtung / aus**. Das ist eine
deutliche Vereinfachung:

- kein PWM-Timing, keine Schaltverluste, kein 20-kHz-Störspektrum in der Dose
- **die PWM-synchrone Strommessung aus [`02`](02-motor-control.md) und [`09`](09-display-and-mcu.md)
  entfällt komplett** — damit auch der Konflikt mit ESPHomes Polling-Modell und der
  Zwang zur C++-External-Component für die Motorregelung
- ein einfacher Low-Side-Shunt reicht, weil es keine Freilaufphase mit
  zerhacktem Strom mehr gibt

### 3.2 Die Stall-Erkennung ist weitgehend redundant

Das aufwendige Konzept aus [`02`](02-motor-control.md) Abschnitt 6 — schneller
Mittelwert gegen langsame Baseline, PWM absenken, dann abschalten — löst ein Problem,
das der Motor bereits selbst löst.

Was **bleibt** sinnvoll:
- Strommessung zur **Diagnose** (Lastanstieg über Monate → Scharnier trocken)
- **Timeout** als Backstop, jetzt auf ~30 s statt 60 s
- **Hardware-Hard-Trip** als Schutz gegen Kurzschluss und Elektronikfehler im Motor —
  der bleibt uneingeschränkt nötig, unabhängig von jeder Motorintelligenz

### 3.3 Umpolung könnte trotzdem nötig bleiben

Manche solcher Antriebe haben drei Adern (gemeinsam + auf + zu), andere zwei mit
Umpolung. Das Datenblatt sagt es nicht. **Die Aderzahl am realen Motor bestimmt, ob
überhaupt eine H-Brücke gebraucht wird** oder nur zwei Relais/Halbbrücken.

## 4. Messprotokoll

Drei Messungen, alle ohne Elektronik dieses Projekts — nur Labornetzteil und
Strommessung. Danach ist der komplette Leistungsteil auslegbar.

**Aufbau:** Labornetzteil 24 V mit Strombegrenzung auf 8 A und Stromanzeige, oder
Netzteil plus Stromzange/Shunt am Oszilloskop. Ein einfaches Multimeter reicht **nicht**
für den Anlaufstrom — der ist zu kurz.

| # | Messung | Wie | Notieren |
|---|---|---|---|
| **M1** | **Laufstrom** | Motor unbelastet und mit montiertem Laden komplett auf/zu fahren | Mittelwert, Maximum, Verlauf über die 18 s |
| **M2** | **Anlaufstrom** | Einschaltmoment, Oszilloskop oder Netzteil mit Peak-Hold | Spitzenwert, Dauer bis zum Einschwingen |
| **M3** | **Blockierstrom** | Antrieb im Lauf **von Hand oder mechanisch blockieren** | Spitzenwert, ob und nach welcher Zeit die interne Abschaltung greift |
| **M4** | **Verhalten mit PWM** | falls möglich: mit ~10 kHz PWM bei 50 % speisen | läuft er? reagiert die Hinderniserkennung noch korrekt? |
| **M5** | **Aderzahl** | am Motorkabel abzählen | 2 Adern (Umpolung) oder 3 (gemeinsam/auf/zu)? |

> **Zu M3, Sicherheitshinweis:** Blockieren nur kurz und mit Strombegrenzung am
> Netzteil. Wenn die interne Elektronik abschaltet, ist das genau das gesuchte
> Ergebnis — dann ist der Motor selbst der Begrenzer.

### Was jede Messung freischaltet

| Messung | Schaltet frei |
|---|---|
| M1 | Leiterbahnbreiten, Dauerstromauslegung, Kühlkonzept |
| M2 | Bulk-Kondensatoren, Sicherungscharakteristik (träge/flink), Soft-Limit |
| M3 | **Hard-Trip-Schwelle, MOSFET-/Treiberauswahl, Steckverbinder** |
| M4 | H-Brücke mit PWM **oder** einfache Vollansteuerung — Architekturentscheidung |
| M5 | H-Brücke **oder** nur zwei Schaltausgänge |

## 5. Was sich schon jetzt ändert

Unabhängig vom Messergebnis:

- **Timeout 60 s → 30 s** (18 s Fahrzeit + Reserve). Alter Wert war eine Annahme ohne
  Datenbasis, siehe [`02-motor-control.md`](02-motor-control.md).
- **Der Steckverbinder-Engpass entschärft sich.** Statt 9 A Dauer sind es nach der
  Rechnung in Abschnitt 2 eher 2 A Dauer und 10 A kurzzeitig. Micro-Fit 3.0 kommt damit
  wieder ernsthaft in Frage — bestätigen nach M1/M2.
- **Der Software-Interlock** (nie beide Motoren gleichzeitig) verliert seine
  Dringlichkeit, bleibt aber sinnvoll.
- **Betriebstemperatur −20 °C** betrifft nur den Motor, nicht die Elektronik in der
  beheizten Innenwand. Kein Bauteil muss deshalb im erweiterten Temperaturbereich
  gewählt werden.
