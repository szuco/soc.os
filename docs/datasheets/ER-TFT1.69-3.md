# ER-TFT1.69-3 — Auszug aus dem Datenblatt

Quelle: EastRising Technology Co., Ltd., „TFT LCD Display Datasheet
ER-TFT1.69-3", Rev. 1.0 vom 24.02.2024, Zeichnung vom 11.06.2024.
`buydisplay.com/download/manual/ER-TFT1.69-3_Datasheet.pdf`

> Diese Seite ist ein **Auszug**, kein Ersatz. Sie hält die Zahlen fest, die
> das Layout bestimmen, damit sie nicht wieder gesucht werden müssen. Das
> vollständige PDF gehört daneben in dieses Verzeichnis — der Anbieter
> blockiert automatische Downloads (HTTP 403), es muss von Hand abgelegt
> werden.

## Bestellnummer

**ER-TFT1.69-3** — 1,69" TFT LCD 240×280 Display Panel, **ohne** Touch.
Variante mit **steckbarer** FPC (die `-1` hat eine Fahne zum Anlöten).

## Mechanik

| | |
|---|---|
| Außenmaß, FPC gefaltet | **30,07 (B) × 37,43 (H) × 1,60 ±0,1 (T) mm** |
| Glas (LCD) | 29,77 × 37,13 |
| Polarisator | 29,37 × 34,13 |
| **Aktive Fläche (AA)** | **27,97 × 32,63** |
| Sichtbare Fläche (VA) | 28,97 × 33,63 |
| Punktraster | 0,11 × 0,11 |

**Die aktive Fläche liegt nicht mittig.** Die Zeichnung nennt an der langen
Achse die Randmaße **1,20** und **1,07** — ein Versatz von rund 0,065 mm.
Beim Einbau ist das die Zahl, die entscheidet, ob das Bild mittig im Fenster
der Zentralscheibe steht.

## FPC

| | |
|---|---|
| Pole | **12** |
| **Raster** | **0,50 mm** (P0.50) |
| Leiterbreite | 0,30 mm (W0.30) |
| Dicke | 0,30 ±0,05 mm |
| Fahnenmaße | 18,15 ±0,5 lang, 8,47 ±0,5 und 6,50 breit, Abgang 1,70 ±0,3 |

## Pinbelegung

| Pin | Name | Bedeutung |
|---:|---|---|
| 1 | **TE** | Tearing Effect, Synchronisation auf die Bildrate |
| 2 | GND | Masse |
| 3 | **RS** | Daten/Befehl-Umschaltung (oft D/C genannt) |
| 4 | **RESET** | aktiv low |
| 5 | **SDA** | SPI-Datenleitung |
| 6 | **SCL** | SPI-Takt |
| 7 | **CS** | Chip Select, low aktiv |
| 8 | **VCC** | Versorgung |
| 9 | **IOVCC** | Versorgung der Ein-/Ausgänge |
| 10 | **LEDA** | Anode der Hintergrundbeleuchtung |
| 11 | **LEDK** | Kathode der Hintergrundbeleuchtung |
| 12 | GND | Masse |

## Elektrisch

| | Min | Typ | Max |
|---|---|---|---|
| VCC | 2,5 | 2,8 | 3,3 V |
| IOVCC | 1,8 | 2,8 | 3,3 V |
| Eingang H | 0,7 × IOVCC | | IOVCC |
| Eingang L | VSS | | 0,3 × IOVCC |

Beide Versorgungen vertragen 3,3 V — die Schiene des Geräts passt direkt.

## Hintergrundbeleuchtung — die Stelle, an der es klemmt

| | Min | Typ | Max |
|---|---|---|---|
| Flussspannung Vf bei 60 mA | — | 3,0 | 3,2 V |
| **Flussstrom** | — | **45** | **60 mA** |
| Lebensdauer bei 45 mA, 25 °C | 30 000 h | | |

Drei LEDs **parallel**. Das sind bis zu 60 mA bei rund 3,1 V — **kein
GPIO-Pin kann das treiben**, schon gar nicht über zwei Steckkontakte des
Stapels hinweg.

Und aus 3,3 V lässt sich das auch nicht mit einem Vorwiderstand machen: Bei
Vf = 3,0…3,2 V blieben 0,1 bis 0,3 V Reserve, der Strom schwankte damit um
den Faktor drei. **Die Beleuchtung braucht die 5-V-Schiene** und eine
Stromquelle oder wenigstens einen Vorwiderstand mit brauchbarem Abstand:

```
5,0 V − 3,1 V = 1,9 V   bei 45 mA  ->  42 Ω, 86 mW
```

Gedimmt wird über die Kathode mit einem Low-Side-Transistor, angesteuert von
`DISP_BL`.

## Was das Datenblatt nicht sagt

- **Kein 3D-Modell.** Für die Baugruppe wird ein Hüllkörper aus diesen Maßen
  erzeugt (`mechanical/connector_models.py`).
- **Keine Aussage zur Befestigung.** Das Panel wird geklebt; die Zeichnung
  zeigt keine Löcher. Die Klebefläche und ihre Dicke gehen in das
  Tiefenbudget ein.
