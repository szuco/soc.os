# Adapter für die Busch-Jaeger Zentralscheibe

Die Sichtfläche dieses Geräts wird **nicht** mehr selbst gestaltet. Sie ist ein
Serienteil:

| Teil | Bestellnummer |
|---|---|
| Zentralscheibe 6435-914, Aufdruck „Pfeile und OK", Busch-balance SI | 2CKA006430A0402 |
| Abdeckrahmen 1721-914, 1-fach, Busch-balance SI | 2CKA001725A1555 |

Erzeugt wird nur noch das **Bindeglied** dazwischen: ein 3D-gedruckter Adapter.
Er bietet der Scheibe an, worauf sie rastet, dem Rahmen, worauf er klemmt, und
der Top-Leiterplatte, worauf sie sitzt.

> Die frühere Frontplatte mit vier **Sicheltasten** ist am 16.08.2026 gelöscht
> worden. Sie war eine vollständige Eigenentwicklung samt Tastenkappen und
> Druckstößeln; mit dem Wechsel auf die Zentralscheibe hat sie ihren Gegenstand
> verloren. Modell und Exporte liegen in der Git-Historie.

## Dateien

| Datei | Zweck |
|---|---|
| `adapter.py` | Parametrisches Modell (build123d). **Referenz** — erzeugt die Exporte und prüft sich selbst |
| `export/adapter.step/.stl` | Adapter |

```bash
pip install build123d
python3 mechanical/adapter.py
```

Alle Parameter stehen im `PARAMS`-Block. Nach jeder Änderung neu laufen lassen —
der Selbsttest prüft die rechnerischen Zwangsbedingungen (Rastmaß, Wandstärke,
Tasterausdehnung, Auflagebreite) **und** nimmt Materialproben an Schnapprand,
Rastraum, Platinenauflage, Taschenwand und Schraubschlitzen.

## Die Tiefenkette

Sie bestimmt alles Übrige. z zählt von der Sichtfläche der Scheibe nach hinten:

| von … bis | was |
|---|---|
| 0,0 … 1,0 | Zentralscheibe, Sichtfläche |
| 1,0 … 2,5 | Druckkreuz auf ihrer Rückseite |
| 2,5 … 4,5 | SMD-Taster über der Leiterplatte |
| 4,5 … 5,5 | Top-Leiterplatte |
| 7,5 | Rastebene und hinterer Rand der Scheibe |

**Die Rastebene liegt hinter der Leiterplatte.** Der Schnapprand steht deshalb
hinter ihr und trägt sie zugleich — Rastglied und Auflage in einem.

## Geometrie

| Merkmal | Wert |
|---|---|
| Tragring-Flansch | 70,0 × 70,0 × 2,5 mm — darauf klemmen die Doppelstege des Rahmens |
| Geräteschrauben | Langlöcher 3,9 mm auf **60 mm** Achsabstand (DIN 49073) |
| Schnapprand | außen 49,8 mm; die Scheibe rastet auf lichte 50,0 |
| Rastraum | springt 1,5 mm zurück, 1,3 mm tief — dort sitzen die vier Nasen |
| Platinentasche | 47,4 mm für das Top-Board 47,0 × 47,0 |
| Auflage | 2,0 mm ringsum |
| Zentrale Durchführung | 43 × 43 mm für die beiden Stackverbinder |
| Gesamthöhe | 10,0 mm |

**Das Maß 47,0 ist keine gewählte Zahl**, sondern liegt zwischen zwei harten
Grenzen: Nach oben begrenzt der Schnapprand (49,8 außen, 1,4 mm Wand), nach
unten die Taster — sie stehen auf (±18 · ±20) und reichen mit Footprint bis
22,2, mit Randabstand also mindestens 45,4.

## Was noch fehlt

- **Bauhöhe des realen Displaymoduls** (Punkt 15c). Zwischen Platinenoberfläche
  und Innenseite der Scheibe stehen 4,5 mm; ein typisches 1,69″-Modul baut
  2,5–3,0 mm. Ob es die Scheibe berührt oder eine Unterlage braucht,
  entscheidet das reale Teil.
- **Lichtkanal für den ToF.** Die vier Durchbrüche der Scheibe liegen bei
  (±9 · ±19) und damit innerhalb der zentralen Durchführung — der Adapter steht
  ihnen nicht im Weg. Ob der Sensor einen eigenen Kanal gegen Streulicht
  braucht, zeigt der reale Aufbau.
- **Sicherung der Platine gegen Herausfallen.** Heute hält sie die Scheibe, die
  über die Taster auf sie drückt. Ob das reicht, zeigt der erste Druck.

Herleitung und Messprotokoll: [`../docs/04-mechanical.md`](../docs/04-mechanical.md),
Abschnitte 1b bis 1e.
