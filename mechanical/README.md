# Frontplatte

3D-druckbare Zentralplatte für die Rahmen gängiger **55er-Schalterprogramme**
(Gira System 55, Jung A/AS, Berker S.1/B.x, Merten M-Smart und die 55er-Linien von
Busch-Jaeger). Version 2: rundes 1,46"-Display in der Mitte, vier **sichelförmige
Tastenkappen** als Ringsegmente um das Fenster.

## Dateien

| Datei | Zweck |
|---|---|
| `frontplate.py` | Parametrisches Modell (build123d). **Referenz** — erzeugt alle Exporte und prüft sich selbst |
| `Frontplate_SwitchStack.FCMacro` | Native FreeCAD-Variante (Objekte `Frontplate` + `ButtonCaps`) |
| `export/frontplate.step/.stl` | Platte |
| `export/frontplate_caps.step/.stl` | Die vier Tastenkappen |
| `export/frontplate_assembly.stl` | Platte + Kappen in Einbaulage (Ansicht/Viewer) |

```bash
pip install build123d
python3 mechanical/frontplate.py
```

Alle Parameter stehen im `PARAMS`-Block am Dateianfang. Nach jeder Änderung neu laufen
lassen — die Selbsttests prüfen Durchbrüche, Stege, Blendring, Solid-Anzahl **und die
Kollisionsfreiheit der Kappen in Einbaulage**.

## Geometrie

| Merkmal | Wert |
|---|---|
| Sichtfläche | 54,6 × 54,6 mm, Ecken R2, Fase 0,5 mm |
| Gesamtabmessung | 76,0 × 54,6 × 8,0 mm (Kappenstößel bis −5,0) |
| Geräteschrauben | Langlöcher 3,9 mm auf **60 mm** Achsabstand (DIN 49073) |
| Displayfenster | Ø 37,8 mm (ST77916 1,46", aktiv Ø 37,25), Modulfreiraum Ø 42,5 mm |
| Sicheltasten | 4 Ringsegmente r 22,0–26,2 mm, je ≈ 68°, 0,8 mm Überstand |
| Tastenstößel | je Kappe 2 × Ø 2,2 mm bei r = 23,2 mm, ±18° um die Diagonalen |
| Kabelausgang Stern | Ø 4,5 mm im unteren Steg (kerbt bewusst den Zentrierkragen) |
| Zentrierkragen | 50 × 50 mm, 2 mm Wand, 3 mm tief |

Displaywechsel: `disp_active_d` und `disp_module_d` im `PARAMS`-Block setzen und
neu erzeugen. Fünf Zwangsbedingungen werden dabei geprüft — unter anderem, dass der
Rückhaltekragen der Kappen das Displaymodul nicht berührt. Verletzt eine Änderung
eine Bedingung, bricht das Skript mit einer konkreten Ansage ab.

## Funktionsprinzip der Sicheltasten

Die Kappen sind **separate Druckteile**, werden von hinten eingesetzt und von einem
umlaufenden Rückhaltekragen gehalten. Je zwei Stößel drücken auf SMD-Taster der
Top-Leiterplatte (8 Taster, elektrisch paarweise parallel → weiterhin 4 Eingänge).
Die Federung kommt vom Taster, nicht vom Kunststoff — gedruckte Federscharniere
ermüden über Jahre, Metallkuppel-Taster nicht. `key_post_len` (Stößellänge, Startwert
4,0 mm) ist an den realen Abstand Platte→Leiterplatte anzupassen.

## Druckhinweise

- **Platte:** Sichtfläche nach unten, keine Stützen nötig.
- **Kappen:** Bedienfläche nach unten (im Slicer um 180° drehen), keine Stützen.
- **Material:** ASA oder PETG. PLA kriecht bei Dauerlast und vergilbt im Sonnenlicht.
- **Layer:** 0,15 mm für saubere Sichtflächen.
- **Toleranz:** Platte 0,4 mm untermaßig (54,6), Kappenspalt 0,25 mm je Seite.
  Klemmt eine Kappe, `key_gap` erhöhen — nicht nachschleifen.

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
