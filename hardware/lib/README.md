# Gemeinsame Bibliotheken

Projektübergreifende Symbole, Footprints und 3D-Modelle für alle drei Boards.

```
switchstack.kicad_sym     Eigene Symbole
switchstack.pretty/       Eigene Footprints
3dmodels/                 STEP / WRL
```

## Einbindung

Pro KiCad-Projekt unter *Preferences → Manage Symbol Libraries* bzw.
*Manage Footprint Libraries*, Scope **Project**, mit relativem Pfad:

```
${KIPRJMOD}/../lib/switchstack.kicad_sym
${KIPRJMOD}/../lib/switchstack.pretty
```

Über `${KIPRJMOD}` bleiben die Projekte auf jedem Rechner lauffähig, ohne absolute Pfade.

## Regeln

- Eigene Footprints für Steckverbinder und mechanisch kritische Teile **immer gegen das
  Datenblatt prüfen**, nicht aus fremden Projekten übernehmen.
- Datenblattquelle und Revision im Beschreibungsfeld des Footprints vermerken.
- Was in den KiCad-Standardbibliotheken korrekt vorhanden ist, wird nicht dupliziert.
- Änderungen an einem Symbol oder Footprint betreffen potenziell alle drei Boards —
  nach einer Änderung in allen betroffenen Projekten *Update Footprints from Library*
  ausführen und DRC neu laufen lassen.
