# Frontplatte

3D-druckbare Zentralplatte für die Rahmen gängiger **55er-Schalterprogramme**
(Gira System 55, Jung A/AS, Berker S.1/B.x, Merten M-Smart und die 55er-Linien von
Busch-Jaeger).

## Dateien

| Datei | Zweck |
|---|---|
| `frontplate.py` | Parametrisches Modell (build123d). **Referenz** — erzeugt STEP + STL und prüft sich selbst |
| `Frontplate_SwitchStack.FCMacro` | Native FreeCAD-Variante zum interaktiven Weiterkonstruieren |
| `export/frontplate.step` | Für FreeCAD, KiCad-3D-Ansicht, CAD-Weiterverarbeitung |
| `export/frontplate.stl` | Direkt für den Slicer |

```bash
pip install build123d
python3 mechanical/frontplate.py
```

Alle Parameter stehen im `PARAMS`-Block am Dateianfang. Nach jeder Änderung neu laufen
lassen — die Selbsttests prüfen, dass Displayfenster, Taster, Kabelausgang und
Schraublöcher durchgängig frei sind und das Teil ein einziges Solid bleibt.

## Geometrie

| Merkmal | Wert |
|---|---|
| Sichtfläche | 54,6 × 54,6 mm, Ecken R2, Fase 0,5 mm |
| Gesamtabmessung | 76,0 × 54,6 × 8,0 mm |
| Geräteschrauben | Langlöcher 3,9 mm auf **60 mm** Achsabstand (DIN 49073) |
| Displayfenster | Ø 32,0 mm, dahinter Ø 37,0 mm Freiraum |
| Taster | 4 × Ø 7,0 mm auf Teilkreis r = 22,5 mm, bei 45/135/225/315° |
| Kabelausgang Stern | Ø 4,5 mm, unten mittig |
| Zentrierkragen | 50 × 50 mm, 2 mm Wand, 3 mm tief |

Die vier Taster sitzen auf den Ecken, das runde Display in der Mitte — die Anordnung
folgt der runden Leiterplatte darunter.

## Druckhinweise

- **Lage:** Sichtfläche nach unten auf das Druckbett. Alle Durchbrüche sind dann
  senkrecht, es braucht keine Stützen.
- **Material:** ASA oder PETG. PLA kriecht bei Dauerlast und vergilbt im Sonnenlicht —
  an einer Wand über Jahre ein reales Problem.
- **Layer:** 0,15 mm für eine saubere Sichtfläche.
- **Toleranz:** Die Platte ist mit 54,6 mm um 0,4 mm untermaßig, weil FDM-Drucker
  typischerweise nach außen bauen. Sitzt sie zu stramm oder zu lose, `plate_size`
  anpassen — nicht nachschleifen.

## Vor dem ersten echten Druck

> Der Rahmen wird bei den Herstellern unterschiedlich befestigt: teils Rastnasen am
> Tragring, teils Klemmung an der Zentralplatte. Diese Platte kombiniert Tragring und
> Zentralplatte in einem Teil — das funktioniert nicht bei jedem Programm gleich gut.
>
> **Erst einen Testdruck nur der Platte** (ohne Elektronik) in den vorhandenen Rahmen
> einsetzen und prüfen, ob er sauber sitzt. Erst danach die Ausschnitte für die
> tatsächlich gekauften Bauteile festziehen.

Ebenfalls noch zu bestätigen:

- Die Ausschnittmaße gelten für ein 1,28"-GC9A01-Modul der gängigen Bauform. Das real
  gekaufte Modul vermessen — die Modulränder variieren zwischen Anbietern.
- Ob der Kabelausgang für den Weihnachtsstern vorne sitzen soll, ist eine
  Gestaltungsentscheidung. `star_exit = False` entfernt ihn.
- USB-C ist bewusst **nicht** von vorn zugänglich (`usb_slot = False`). Programmiert
  wird bei abgenommener Blende, im Betrieb per OTA.
