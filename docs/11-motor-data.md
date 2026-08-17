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

> **Gemessen am 17.08.2026 — der Blockierstrom ist geklärt, dreifach.**
>
> | Messung | Verfahren | Ergebnis | daraus R |
> |---|---|---:|---:|
> | M7 | 2 V anlegen, Strom messen | 0,116 A | 17,2 Ω |
> | M3 | 24 V, Abtrieb blockiert | **1,6 A** | **15,0 Ω** |
> | M6 | Multimeter direkt an den Motoradern | — | **14 … 20 Ω** |
>
> Drei völlig verschiedene Verfahren, Spannungen zwölffach auseinander, und alle
> landen zwischen 14 und 20 Ω. Damit ist die Sache entschieden.
>
> Für die Auslegung zählt der **kleinste** Wert, denn er ergibt den größten
> Strom: **R = 14 Ω, I_Blockier = 1,7 A.** Ausgelegt wird auf **2 A**.
>
> (M6 streut mit 14, 16,5 und 20 Ω sichtbar — genau das erwartet man, denn der
> Bürstenübergang macht den Widerstand von der Läuferstellung abhängig. **Alle
> Streuung liegt nach oben**, und höher heißt weniger Strom. Der Nullpunkt der
> Messleitungen liegt bei 0,2 Ω und ist damit unter 1,5 %; die Warnung weiter
> unten galt für die früher erwarteten 1 Ω.)
>
> **Das ist ein Sechzehntel der zuvor angenommenen 25 A.** Abschnitt 5 ist
> daraufhin komplett neu gerechnet.
>
> Und das Typenschild? 24 V an 14 Ω sind **maximal 41 W** — der Motor *kann*
> keine 100 W aufnehmen, in keinem Zustand. Zwei Motoren blockiert ergeben
> 76 W, plus Reserve rund 100 W. Die Zahl auf dem Schild ist mit hoher
> Wahrscheinlichkeit die **empfohlene Netzteilgröße der Anlage**, nicht die
> Aufnahme eines einzelnen Motors. Damit ist der Widerspruch aufgelöst, an dem
> sich die Auswertung zuerst festgefahren hatte.

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

## 2. Laufstrom niedrig, Blockierstrom gemessen

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

**Der Laufstrom liegt also bei etwa 0,3–1,0 A.**

Der Blockierstrom folgt aus `I = U / R_Anker` — ohne interne Elektronik begrenzt
ihn nichts anderes. Gemessen sind 14 Ω, also **1,7 A**. Damit ergibt sich das
vollständige Strombild eines Motors:

| Zustand | Strom bei 24 V | Herkunft |
|---|---:|---|
| Leerlauf, nur Getriebereibung | ≈ 0,12 A | gemessen (0,116 A bei 2 V) |
| Fahrt unter Last | 0,3–1,0 A | aus Moment und Drehzahl gerechnet |
| **Anschlag / blockiert** | **1,7 A** | **gemessen** |
| theoretisches Maximum | 1,7 A | `24 V / 14 Ω` — mehr geht physikalisch nicht |

> **Die kleine Spreizung ist die eigentliche Nachricht — und sie geht in die
> unangenehme Richtung.** Die erste Fassung dieses Abschnitts rechnete mit
> Laufstrom 0,5 A gegen Blockierstrom 20 A, einem **Faktor 40**, und nannte das
> „für die Lasterkennung ideal". Tatsächlich stehen 0,3–1,0 A gegen 1,7 A —
> **Faktor 1,6 bis 5**, im ungünstigen Fall also gerade einmal 60 % Anstieg.
>
> Für die **Leistungsauslegung** ist das eine große Erleichterung: Sicherung,
> Leiterbahnen, Steckverbinder und Endstufe werden alle unkritisch.
>
> Für die **Endlagenerkennung**, die ohne Reed-Kontakte allein auf Fahrzeit und
> Strom beruht, ist es eine Verschärfung. Sie ist trotzdem machbar, und zwar aus
> zwei Gründen: Der Shunt ist deshalb von 1 auf **5 mΩ** vergrößert worden, was
> die Auflösung verfünffacht (Abschnitt 5). Und der Original-Controller K0000230
> löst dieselbe Aufgabe am selben Motor mit derselben Physik — es ist also
> nachweislich möglich.

## 3. Was die Korrektur zurückholt

Die erste Fassung hatte drei Vereinfachungen in Aussicht gestellt. Alle drei sind
hinfällig:

| erste Fassung (falsch) | tatsächlich |
|---|---|
| PWM vermutlich verboten | **PWM ist erlaubt** — nichts im Motor, das gestört werden könnte. Geschwindigkeitsreduzierung bleibt möglich |
| Stall-Erkennung redundant | **Stall-Erkennung ist Kernfunktion.** Ohne sie fährt der Antrieb gegen ein Hindernis, bis der Timeout greift |
| PWM-synchrone Messung entfällt | **Bleibt in voller Schärfe** — samt Konflikt mit ESPHomes Polling-Modell und dem Bedarf an einer C++-Komponente |
| Hard-Trip evtl. 6–7 A ausreichend | seit der Messung: **4,4 A** genügt und ergibt sich ohne Bauteiländerung |
| Steckverbinder-Engpass entschärft | **stimmt wieder** — der Blockierstrom ist mit 1,7 A je Motor unkritisch |

Damit gelten [`02-motor-control.md`](02-motor-control.md) und
[`09-display-and-mcu.md`](09-display-and-mcu.md) Abschnitt 4 wieder unverändert.

**Sicherheitsrelevant:** Klemmt ein Laden, steht der Motor unter voller
Blockierspannung, bis etwas abschaltet. Es gibt keine Selbsthilfe im Motor. Die
Kette Software-Soft-Limit → Hardware-Hard-Trip → Sicherung ist damit nicht Komfort,
sondern **die einzige Schutzebene**. Sie muss auch bei nicht geladener Firmware
wirken — deshalb bleibt der Comparator-plus-Latch pro Kanal zwingend.

> **Was die Messung an dieser Stelle verschiebt: die Gefahr ist mechanisch, nicht
> elektrisch.** Bei der Blockiermessung am 17.08.2026 wurde am Antrieb etwas
> verbogen — bei 1,7 A. Das Getriebe macht aus einem elektrisch harmlosen Strom
> ein Moment, das Beschläge verformt.
>
> Daraus folgt unmittelbar: **Sicherung und Hardware-Trip schützen die Mechanik
> nicht und können es nicht.** Sie liegen bei 6,3 A und 4,4 A, also weit über
> dem, was zum Verbiegen reicht. Der Schutz der Mechanik ist **allein** Aufgabe
> der Software — Soft-Limit auf den Strom, Fahrzeit-Timeout und vor allem die
> Verlangsamung vor der vermuteten Endlage. Bei 50 % PWM liegen nur noch 0,8 A
> und entsprechend halbes Moment am Anschlag an; die Drehzahlreduzierung ist
> damit keine Komfortfunktion, sondern die wirksamste Kraftbegrenzung, die das
> Gerät hat.
>
> Elektrisch bleibt der Dauerblockierfall dagegen entspannt: 41 W im Motor, für
> die Elektronik ein Nichtereignis. Nur der Motor selbst wird auf Dauer heiß —
> deshalb der Timeout.

## 4. Messprotokoll

Drei Messungen, ohne Elektronik dieses Projekts — Labornetzteil und Strommessung.

**Aufbau:** Labornetzteil 24 V mit einstellbarer Strombegrenzung und Anzeige, besser
Stromzange oder Shunt am Oszilloskop. Für den Anlaufstrom reicht ein Multimeter
**nicht** — er ist zu kurz.

| # | Messung | Wie | Status |
|---|---|---|---|
| **M1** | **Laufstrom** | Laden komplett auf und zu fahren, montiert | 🟡 offen — gerechnet 0,3–1,0 A, misst später das Gerät selbst |
| **M2** | **Anlaufstrom** | Einschaltmoment | ✅ **erledigt durch M3.** Beim Einschalten steht der Läufer, es fließt also genau der Blockierstrom. Mehr als 1,7 A kann nie fließen — ein Einschaltstoß existiert bei diesem Motor nicht |
| **M3** | **Blockierstrom** | Abtrieb blockieren, U und I **gleichzeitig** ablesen, `R = U/I`. **Bei 2–4 V, nicht bei 24 V** — siehe Warnung unten | ✅ **1,6 A bei 24 V** (17.08.2026) |
| **M6** | **Ankerwiderstand** | Motor **stromlos**, Multimeter an die zwei Adern. Welle **nicht** von Hand drehbar (Schneckengetriebe selbsthemmend) — stattdessen: messen, Motor kurz ein Stück fahren, erneut messen, **10×** wiederholen | ✅ **16,5 Ω** (17.08.2026, erste Messung) |
| **M7** | **Kleinspannungsmethode** | Labornetzteil auf **2 V**, Strom messen. Der Motor dreht dabei mit 0,16 U/min noch minimal weiter, der Fehler ist aber klein | ✅ **0,116 A bei 2 V** (16.08.2026) |

> **Korrektur zu M6:** In der ersten Fassung stand „Welle langsam von Hand drehen".
> Das geht bei einem selbsthemmenden Schneckengetriebe nicht. Der Bürstenübergang
> macht den Messwert trotzdem winkelabhängig — deshalb mehrfach messen und den
> Motor dazwischen mit eigener Kraft ein Stück versetzen.

> **Nullpunkt nicht vergessen — sonst ist M6 wertlos.** Diese Warnung galt, als
> rund **1 Ω** erwartet wurde: Messleitungen und Messgerät bringen selbst
> 0,2–0,5 Ω mit, also bis zur Hälfte des Messwerts. Deshalb **zuerst die
> Messspitzen gegeneinander halten** und diesen Wert abziehen.
>
> Bei den tatsächlich gemessenen **14 bis 20 Ω** fällt das nicht ins Gewicht — die
> Zuleitungen machen keine 3 % aus. M6 wäre also einfacher gewesen als gedacht,
> ist durch M3 und M7 aber ohnehin erledigt.

> **M7 und M3, 17.08.2026 — beide Messungen liegen vor und stimmen überein.**
>
> | Messung | Spannung | Strom | daraus R |
> |---|---:|---:|---:|
> | M7 | 2 V | 0,116 A | 17,2 Ω |
> | M3 | 24 V, Abtrieb blockiert | **1,6 A** | **15,0 Ω** |
>
> Zwei Betriebspunkte, Faktor zwölf in der Spannung, dasselbe Ergebnis. Das
> Netzteil kann 5 A, war bei 1,6 A also nicht in der Begrenzung.
>
> **Ergebnis: R_Anker 14 … 20 Ω je nach Läuferstellung.** Weil eine unbemerkte
> Restdrehung `U/I` immer nach oben verfälscht, ist der M3-Wert eine Obergrenze
> und sein Strom eine Untergrenze. Maßgeblich ist das Minimum aus allen drei
> Verfahren: **14 Ω, also 1,7 A.** Ausgelegt wird auf 2 A.
>
> **Zwischendurch stand hier, die M7-Messung sei unbrauchbar.** Begründung war
> der Widerspruch zum Typenschild: 100 W / 24 V = 4,17 A, und ein Motor, der
> blockiert weniger zieht als im Nennbetrieb, ist unmöglich. Der Schluss war
> falsch — nicht die Messung. Die 100 W sind nicht die Aufnahme dieses Motors,
> sondern die Netzteilempfehlung für die Anlage. M3 hat M7 bestätigt.
>
> Richtig an der damaligen Analyse bleibt der physikalische Teil: Bei 2 V dreht
> der Abtrieb tatsächlich mit 0,16 U/min weiter, eine Umdrehung in gut sechs
> Minuten. Deshalb sind die 0,116 A etwas kleiner als die 0,133 A, die 2 V an
> 15 Ω blockiert ergäben (0,133 A) — die Differenz ist die Gegenspannung. Der Effekt ist
> nur klein, nicht groß, und ändert die Größenordnung nicht.
>
> **Der Leerlaufstrom ist damit ebenfalls bekannt:** ≈ 0,12 A, die reine Reibung
> des Schneckengetriebes. Er gehört als Untergrenze in die Lasterkennung.
>
> ⚠️ **Bei der Blockiermessung wurde am Antrieb etwas verbogen.** 1,7 A sind
> elektrisch harmlos, das Getriebe macht daraus aber ein Moment, das Beschläge
> verformt. Wer die Messung wiederholt, tut das bei **2 bis 4 V**, nicht bei
> 24 V — die Auswertung über `R = U/I` funktioniert bei jeder Spannung gleich
> gut, solange U und I **gleichzeitig** abgelesen werden.

> **M7 war die verlässlichste einfache Messung** und ist es geblieben. Sie
> umgeht das Bürstenproblem vollständig, weil der Strom über mehrere Lamellen
> mittelt, braucht kein Oszilloskop und gefährdet die Mechanik nicht.

### Was jede Messung freischaltet

| Messung | Schaltet frei |
|---|---|
| M1 | Leiterbahnbreiten für den Dauerbetrieb, Kühlkonzept, Shunt-Verlustleistung — alle drei durch M3 bereits entschärft |
| M2 | ✅ durch M3 miterledigt |
| M3 / M7 | ✅ **Hard-Trip-Schwelle (R7/R8/R9), Shunt, Sicherung F1, Steckverbinder, MOSFET-Auswahl — alles entschieden**, siehe Abschnitt 5 |

## 5. Die Auslegung nach der Messung

Bis zum 17.08.2026 war dieser Abschnitt eine defensive Annahme: **25 A
Blockierstrom je Kanal, 1 s lang**. Die Annahme hat ihren Zweck erfüllt — der
Schaltplan konnte fertig werden, ohne auf die Messung zu warten, und die
messabhängigen Größen waren bewusst als tauschbare Widerstände ausgeführt.

Jetzt liegt die Messung vor, und sie ist um den Faktor 16 günstiger als die
Annahme. Geändert wurde daraufhin genau das, was ohne Layoutänderung geht:

| Bauteil | vorher (Annahme 25 A) | jetzt (gemessen 1,7 A) | Layout betroffen? |
|---|---|---|---|
| **Shunt** `R_M1_SH` / `R_M2_SH` | 1 mΩ, 1 W, 2512 Kelvin | **5 mΩ**, sonst gleich | nein — gleicher Footprint |
| **Trip-Teiler** `R7`/`R8`/`R9` | 10k0/40k2/10k0 → ± 22 A | **unverändert → ± 4,4 A** | nein — der Shunt verschiebt die Schwelle mit |
| **Trip-Teiler** `R7` / `R9` | 10k0 | 10k0, unverändert | nein |
| **Sicherung F1** | 15 A träge | **6,3 A träge** | nein — Wertfrage |
| **Firmware-Skalierung** | 20 A/V | **4 A/V**, weiter zur Laufzeit einstellbar | — |
| H-Brücke / MOSFETs | ≥ 30 A Peak | unverändert, jetzt reichlich überdimensioniert | nein |
| Current-Sense-Amp | INA240A2, Verstärkung 50 | unverändert | nein |
| Steckverbinder | für 25 A kurzzeitig | Anforderung entfällt | nein |
| Bulk-Kondensator | 470–1000 µF | unverändert | nein |

### Warum der Shunt größer wird und nicht kleiner

Das ist die einzige Änderung, die kontraintuitiv wirkt. Bei kleinerem Strom
liegt der Reflex nahe, den Shunt ebenfalls zu verkleinern — tatsächlich ist das
Gegenteil richtig, denn der Shunt bestimmt nicht die Belastbarkeit, sondern die
**Auflösung**.

```
1 mΩ:  1,7 A → 1,7 mV am Shunt → 85 mV am INA240-Ausgang
5 mΩ:  1,7 A → 8,5 mV am Shunt → 425 mV am INA240-Ausgang
```

Der Unterschied zwischen Fahrt (0,3–1,0 A) und Anschlag (1,7 A) beträgt am alten
Shunt nur 30–65 mV — in der Größenordnung des ADC-Rauschens des ESP32. Am neuen
Shunt sind es 150–325 mV, und genau daran hängt die Endlagenerkennung.

| Größe | Wert mit 5 mΩ |
|---|---|
| Empfindlichkeit | **0,25 V/A** (5 mΩ × 50) |
| Messbereich | **± 6,6 A** (Nullpunkt 1,65 V ± 1,65 V) |
| Auflösung ESP32-ADC | ≈ 3 mA je LSB |
| Verlustleistung bei 2 A | 20 mW — im 1-W-Bauteil ein Nichts |
| Verlustleistung bei 6,6 A | 0,22 W |
| Spannungsabfall bei 1,7 A | 9 mV |

### Warum der Hardware-Trip bei 4 A liegt

Die Schwelle muss **über** dem Blockierstrom liegen, denn der Anschlag ist bei
diesem Gerät ein völlig normaler Betriebszustand: Ohne Endschalter fährt der
Laden bei jeder Fahrt kurz gegen den Anschlag. Ein Trip bei 2 A würde bei jedem
Schließen auslösen.

```
Leerlauf   Fahrt      Anschlag    Soft-Limit   HW-Trip    Sicherung   FET-Grenze
 0,12 A   0,3-1,0 A    1,7 A       ~2,0 A      4,4 A      6,3 A traege  >30 A
```

Mit `R7 = R9 = 10k0` und `R8 = 40k2` an 3,3 V ergibt sich `V_TRIP_HI = 2,752 V`
und `V_TRIP_LO = 0,548 V`, gegen den Nullpunkt von 1,65 V also **± 4,41 A**. Der
Teiler ist damit **unverändert** — der größere Shunt hat die Schwelle von selbst
von 22 A auf 4,4 A mitgenommen.

Die Reserve von Faktor 2,75 über dem Blockierstrom ist bewusst großzügig, denn
sie kostet nichts: Zwischen 4 und 5 A ist auf dieser Platine nichts gefährdet
(MOSFETs > 60 A, Shunt 1 W, Messbereich ± 6,6 A). Ein höherer Trip schützt
genauso gut vor dem Einzigen, was er überhaupt abfangen kann — einem echten
Kurzschluss — und verträgt zugleich einen Messfehler beim Blockierstrom von
Faktor 2,5.
Nützlich dabei: Teiler und INA240-Referenz hängen beide an `3V3_SYS`. Driftet die
Versorgung, driften Nullpunkt und Schwelle gemeinsam — die Schwelle ist
ratiometrisch stabil.

Ein echter Kurzschluss an den Motorklemmen liegt um Größenordnungen über 4 A und
löst sofort aus. Genau dafür ist der Trip noch da; die Mechanik schützt er nicht
(siehe den Kasten in Abschnitt 3).

### Was bewusst *nicht* geändert wurde

**Die diskrete H-Brücke bleibt.** Sie wurde nur deshalb diskret aufgebaut, weil
der Blockierstrom unbekannt war — bei 1,7 A wäre ein monolithischer Treiber wie
der DRV8871 (3,6 A Spitze) heute die naheliegende Wahl und würde die
Bottom-Platine erheblich entlasten. Dagegen steht, dass die Platine bereits
geroutet ist. Der Umbau wäre ein vollständiges Neulayout, der Gewinn nur Fläche,
die ohnehin schon vergeben ist. Aufgenommen als Option in
[`06-open-decisions.md`](06-open-decisions.md), nicht als Aufgabe.

**Die 2-oz-Frage ist erledigt, nicht geändert:** Bei 4,1 A Summenstrom im
ungünstigsten Fall reicht Standard-1-oz-Kupfer, die vorhandenen breiten Bahnen
schaden nicht. Siehe [`05-manufacturing.md`](05-manufacturing.md).

## 6. Wie sicher ist die Zahl — und was macht der Wind?

Zwei Zweifel bleiben nach der Messung berechtigt: Könnte der Blockierstrom in
Wirklichkeit höher sein? Und was passiert bei Wind, wenn eine Klappladenfläche
von rund einem Quadratmeter am Motor hängt?

### 6.1 Der Blockierstrom ist eine harte Obergrenze — nicht eine Annahme

Der entscheidende Punkt ist, dass die Grenze nicht aus einer Lastannahme kommt,
sondern aus dem Ohmschen Gesetz:

```
I = (U - E) / R          E = Gegenspannung, proportional zur Drehzahl
```

Bei blockiertem Läufer ist `E = 0`, also `I = U / R` — das ist das Maximum. **Ein
Drehmoment taucht in dieser Gleichung nicht auf.** Egal wie stark die Last ist,
mehr als `U/R` kann nicht fließen. Wind kann den Motor nur langsamer machen, und
langsamer heißt: näher an 1,7 A, nie darüber.

Es gibt genau drei Wege, die Grenze doch zu überschreiten:

| Weg | Rechnung | Bewertung |
|---|---|---|
| Netzspannung am oberen Toleranzrand | 26,4 V / 14 Ω = **1,89 A** | eingerechnet |
| **Umpolen bei drehendem Motor** — die Gegenspannung addiert sich | bis 2 × 24 V / 14 Ω = **3,4 A** | der eigentliche Worst Case; die Firmware hält 300 ms Stoppause, und das selbsthemmende Schneckengetriebe bremst den Läufer in wenigen Millisekunden |
| Motor wird mechanisch angetrieben (Generatorbetrieb) | — | durch die Selbsthemmung praktisch ausgeschlossen |

**Der Hardware-Trip liegt mit 4,4 A über allen dreien.** Das ist der Grund für
die großzügige Schwelle: Sie muss nicht knapp sitzen, weil zwischen 4 und 5 A auf
dieser Platine ohnehin nichts gefährdet ist.

### 6.2 Was passiert, wenn die Messung um Faktor 2 danebenliegt?

Die Messung ist durch zwei Betriebspunkte gestützt (2 V und 24 V, Faktor zwölf
auseinander, Abweichung 13 %). Trotzdem die Gegenprobe — angenommen, der wahre
Ankerwiderstand wäre nur 7 Ω und der Blockierstrom **3,4 A statt 1,7 A**:

| Bauteil | hält das? |
|---|---|
| MOSFETs (> 60 A), IR2104, Leiterbahnen | ✅ um Größenordnungen |
| Shunt 5 mΩ, 1 W | ✅ 58 mW bei 3,4 A |
| Messbereich ± 6,6 A | ✅ |
| **Hardware-Trip 4,4 A** | ✅ noch 29 % Abstand |
| Steckverbinder Micro-Fit 3.0 (2 × 3,4 A + 0,7 A = 7,5 A) | ⚠️ grenzwertig |
| **Sicherung 6,3 A träge** | ❌ **fliegt beim beidseitigen Anschlag** |

Nur zwei Positionen reagieren überhaupt, und die Sicherung ist dabei kein Risiko,
sondern der **Melder**: Fliegt sie beim ersten beidseitigen Schließen, war die
Messung falsch — ein harmloser, sofort sichtbarer Fehlerfall. Die Auslegung ist
damit gegen einen Faktor-2-Irrtum abgesichert, ohne dass etwas kaputtgeht.

### 6.3 Die billige Gegenprobe: M6, jetzt endlich brauchbar

`M6` — Multimeter direkt an die zwei Motoradern, Motor stromlos — galt bisher als
unzuverlässig, weil bei erwarteten 1 Ω die Messleitungen selbst 0,2–0,5 Ω
beitragen. **Bei 14 bis 20 Ω sind das keine 1,5 %.** Die Messung ist damit auf einen
Schlag aussagekräftig:

1. Motor **abklemmen**, beide Adern frei.
2. Messspitzen gegeneinander halten, diesen Wert notieren (Nullpunkt).
3. An die Motoradern, ablesen, Nullpunkt abziehen.
4. Motor ein Stück verfahren, erneut messen — der Bürstenübergang macht den Wert
   winkelabhängig. **Fünfmal, kleinsten Wert nehmen.**

**Erwartet waren 14–17 Ω — gemessen wurden 14, 16,5 und 20 Ω.** Damit ist die Auslegung
dreifach bestätigt und der Faktor-2-Irrtum aus Abschnitt 6.2 ausgeschlossen. Die
Sicherung bleibt bei 6,3 A, der Steckverbinder bei Micro-Fit 3.0.

Die Streuung zwischen 14 und 20 Ω ist kein Widerspruch, sondern der erwartete
Bürsteneffekt: Je nach Läuferstellung liegen unterschiedlich viele Lamellen im
Strompfad. **Für die Auslegung zählt das Minimum**, und das sind die **14 Ω**
der letzten M6-Messung — knapp unter den 15,0 Ω, die M3 als Strommessung bei
voller Spannung ergeben hat. Auf diesen 14 Ω steht die Auslegung.

Selbst wenn eine noch ungünstigere Stellung 15 % darunter läge — 12 Ω, 2,0 A —
bliebe bis zum Trip bei 4,4 A ein Faktor 2,2.

### 6.4 Wind: das Problem ist mechanisch, nicht elektrisch

Für eine Überschlagsrechnung ein Flügel von 0,6 × 1,4 m (0,84 m²), Hebelarm
0,3 m ab Band, Formbeiwert 1,2:

| Windgeschwindigkeit | Kraft auf den Flügel | Moment am Band |
|---|---:|---:|
| 40 km/h | 78 N | **23 Nm** |
| 60 km/h | 176 N | **53 Nm** |
| 90 km/h | 394 N | **118 Nm** |

Das Motormoment beträgt **25 Nm**. Schon bei rund 40 km/h ist der Antrieb also am
Anschlag seines Vermögens, bei 90 km/h steht ihm das Fünffache entgegen.

Elektrisch ändert das nichts — der Strom bleibt bei 1,7 A gedeckelt. **Das Gerät
merkt vom Wind nur, dass der Motor langsamer wird.** Und genau daraus entstehen
die beiden realen Fehlerbilder:

**Gegenwind** bremst den Flügel, der Strom steigt Richtung 1,7 A, und die
Lasterkennung hält das für den Anschlag. Der Laden bleibt auf halbem Weg stehen,
das Gerät meldet „geschlossen".

**Rückenwind** treibt den Flügel schneller als erwartet und schlägt ihn gegen den
Anschlag — mit Windkraft statt Motorkraft. Der Strom ist dabei sogar *niedriger*
als normal, die Lasterkennung sieht nichts. Das ist der gefährlichere Fall, und
es ist derselbe Mechanismus, der am 17.08.2026 beim Blockierversuch etwas verbogen
hat.

**Was das Gerät dagegen tun kann:**

1. **Strom und Zeit gemeinsam auswerten, nicht nur den Strom.** Ein Stromanstieg
   bei 20 % der Fahrzeit ist ein Hindernis oder Wind, kein Anschlag. Nur innerhalb
   eines plausiblen Zeitfensters — Vorschlag ab 70 % der gelernten Fahrzeit — darf
   ein Stromanstieg als Endlage gelten. Außerhalb: anhalten und melden, aber die
   Positionsanzeige **nicht** auf „zu" setzen.
2. **Verlangsamung vor der Endlage.** Bei 50 % PWM halbiert sich das Moment. Gegen
   Rückenwind hilft das nicht, gegen alles andere schon.
3. **Windsperre über Home Assistant.** Das ist die einzige Maßnahme, die gegen
   Rückenwind wirklich hilft, und sie gehört nicht ins Gerät, sondern in die
   Automatisierung: Oberhalb einer Schwelle — nach dieser Rechnung sinnvoll bei
   etwa 40 km/h — wird nicht mehr gefahren. Eine Wetterstation oder der
   Wind-Sensor der Wetterintegration reicht dafür.

**Was das Gerät nicht kann:** einen Flügel gegen 90 km/h Wind halten. Das ist
Sache der Beschläge, nicht der Elektronik. Der Motor ist mit 25 Nm dafür nicht
ausgelegt und wird es durch keine Firmware.

Aufgenommen als Punkt 58 in [`06-open-decisions.md`](06-open-decisions.md).
