# 14 – Der Original-Controller, aufgeschraubt

Am 18.08.2026 lag der mitgelieferte Controller **K0000230** offen auf dem
Tisch. Er steuert heute die Klappläden und ist damit die einzige Quelle, die
zeigt, wie der Hersteller selbst diese Aufgabe gelöst hat. Was hier steht,
stammt aus Fotos beider Platinenseiten und den Datenblättern der lesbaren
Bauteile.

Die Platine ist ein **Achteck** von etwa 55 mm Schlüsselweite, zweiseitig
bestückt, mit Schraubklemmen (5-polig und 3-polig), einem 6-poligen
Programmierstecker, einem Taster und einer LED. Aufkleber: `V610 FA`,
`T 19|2022 PT`.

## 1. Was verbaut ist

| Bauteil | Aufdruck | Funktion |
|---|---|---|
| **2 × Infineon BTM7700G** | `TRILITHIC BTM7700G` | **integrierte H-Brücke, eine je Motor** |
| **2 × Shunt 50 mΩ** | `R050` | Strommessung, einer je Motorkanal |
| Mikrocontroller | `PIC16F2…K22` | 8-Bit-PIC, 28-polig SOIC |
| Quarz | `MC-306` o. ä. | Taktquelle |
| Elko | `47 µF 50 V` | **die gesamte Bulk-Kapazität** |
| 2 × Optokoppler | `D223 051S` | galvanische Trennung |
| Diode | `S5+ 1B` | Gleichrichter/Schutz |

## 2. Was das für unsere Auslegung bedeutet

### 2.1 Der Blockierstrom ist jetzt vierfach bestätigt

Bisher stützten ihn drei eigene Messungen (docs/11): 17,2 Ω über die
Kleinspannungsmethode, 15,0 Ω über den blockierten Abtrieb, 14 bis 20 Ω mit
dem Multimeter. Der Original-Controller bestätigt sie ein viertes Mal, ohne
dass man etwas messen muss — allein durch seine Bauteilwahl:

**Der Shunt.** 50 mΩ je Kanal. Bei 1,7 A fallen dort 85 mV ab und 0,14 W an —
ein sauberes Messsignal in einem gewöhnlichen Widerstand. Bei den ursprünglich
angenommenen 20 A wären es **20 Watt** in einem Bauteil von wenigen
Millimetern. Niemand baut das.

**Die Brücke.** Der BTM7700G hat laut Datenblatt der Baureihe rund 70 mΩ
high-side und 40 mΩ low-side, zusammen also **110 mΩ im Strompfad**. Bei 1,7 A
sind das 0,32 W. Bei 20 A wären es 44 W in einem SO-28-Gehäuse.

**Der Elko.** 47 µF für zwei Motoren. Wer 20-A-Impulse abfangen will, baut
Hunderte von Mikrofarad ein.

Drei unabhängige Bauteilentscheidungen, alle nur mit einem Motorstrom im
Bereich von ein bis zwei Ampere vereinbar.

### 2.2 Die diskrete H-Brücke ist überdimensioniert

Unser Bottom-Board fährt zwei Kanäle mit **acht MOSFETs und vier
Gate-Treibern**. Der Hersteller nimmt dafür **zwei ICs**. Das war die
Rückfallposition aus [`06-open-decisions.md`](06-open-decisions.md) Punkt 55,
verworfen mit dem Argument, die Platine sei bereits geroutet — das Argument
steht, aber die Sachlage ist jetzt belegt statt vermutet.

Der BTM7700G selbst ist für uns übrigens grenzwertig: Seine
Kurzschlussfestigkeit ist bis **28 V** spezifiziert, unsere Schiene liegt bei
24 V +10 % = 26,4 V. Der Hersteller nutzt ihn also nahe seiner Grenze. Ein
moderner Treiber mit mehr Spannungsreserve wäre die bessere Wahl.

### 2.3 Der Bulk-Kondensator darf schrumpfen — und das schafft Platz

[`01-power-tree.md`](01-power-tree.md) sieht **470 bis 1000 µF** vor, bei
maximal 10 mm Bauhöhe. Das stammt aus der Zeit der 25-A-Annahme. Der
Original-Controller kommt mit **47 µF** aus, also einem Zehntel.

Das ist die praktisch wertvollste Erkenntnis dieser Seite, denn der
Bulk-Kondensator ist eines der größten Bauteile auf der Kabelseite des
Bottom-Boards — und genau dort fehlt der Platz für einen zusammengefassten
Feldstecker (siehe unten). Ein kleinerer Elko baut niedriger und kürzer.

**Nicht blind übernehmen:** 47 µF ist die Wahl des Herstellers für seine
Topologie mit integrierter Brücke und weichem Anlauf über den Analogeingang
der Low-Side. Unsere PWM-Brücke hat andere Stromspitzen. 100 bis 220 µF sind
die naheliegende Größenordnung, zu bestätigen, wenn die Endstufe steht.

### 2.4 Was der Hersteller trennt, trennen wir nicht

Zwei Optokoppler sitzen auf der Platine. Wofür genau, lässt sich am Foto nicht
sicher sagen — naheliegend sind die Eingänge der Wandtaster. Unser Gerät führt
alle Eingänge direkt auf den Portexpander. Das ist bei reiner SELV-Verkabelung
zulässig, aber es ist ein Unterschied im Konzept, den man kennen sollte.

### 2.5 Ein 8-Bit-PIC reicht für die Aufgabe

Die gesamte Steuerung — zwei Motoren, Endlagenerkennung über Strom und Zeit,
Flügelversatz, Einlernfahrt — läuft auf einem PIC16F2xK22 mit ein paar
Kilobyte Programmspeicher. Das relativiert nichts an unserem ESP32-S3, dessen
Aufgabe Display, WLAN und Home Assistant sind, aber es zeigt: **Die
Motorsteuerung selbst ist nicht das Schwierige.**

## 3. Offene Fragen an das Original

- **Wie misst er den Strom?** 50 mΩ ergeben bei 1,7 A nur 85 mV. Ein
  PIC-ADC-Eingang direkt daran hätte wenig Auflösung; wahrscheinlich sitzt ein
  Verstärker dazwischen, der auf den Fotos nicht eindeutig zu identifizieren
  ist.
- **Wozu die Optokoppler?** Eingänge, Ausgänge oder eine Bus-Schnittstelle.
- **Was liegt auf der 5-poligen Klemme?** Vermutlich die beiden Motoren und
  Masse, die 3-polige wäre dann Versorgung und Steuereingang.

Diese Fragen ändern nichts an den Schlüssen oben — die tragen sich allein aus
Shunt, Brücke und Elko.
