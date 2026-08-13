# 08 – KiCad-Workflow und Repo-Konventionen

KiCad-Version: **9.0.7**. Alle Beteiligten sollten dieselbe Minor-Version verwenden,
sonst schreibt KiCad die Dateien beim Öffnen um und erzeugt unnötige Diffs.

## 1. Projekte nativ anlegen

Frühere automatisch erzeugte Skeleton-Dateien (`.kicad_pro`, `.kicad_sch`) ließen sich in
KiCad 9.0.7 nicht zuverlässig öffnen, und die `.kicad_pcb` war weitgehend leer. Deshalb
gilt für dieses Projekt:

> **KiCad-Projektdateien werden ausschließlich von KiCad selbst erzeugt.**
> Keine handgeschriebenen oder skriptgenerierten `.kicad_pro`, `.kicad_sch` oder
> `.kicad_pcb`. Das Repository liefert nur Verzeichnisse und Dokumentation.

Vorgehen je Board:

1. In KiCad 9.0.7 *File → New Project* wählen.
2. Als Speicherort das bereits vorhandene Verzeichnis wählen:
   - `hardware/bottom_power_motor/` → Projektname `bottom_power_motor`
   - `hardware/mid_logic/` → Projektname `mid_logic`
   - `hardware/top_ui/` → Projektname `top_ui`
3. KiCad legt `<name>.kicad_pro`, `<name>.kicad_sch` und `<name>.kicad_pcb` an.
4. Projekt schließen, dann committen.

## 2. Koordinaten statt Optik

Der Punkt (0,0) liegt standardmäßig **nicht** optisch in der Blattmitte. Das Verschieben
eines Grid- oder Drill-&-Place-Ursprungs verschiebt **nicht das Board**, sondern ändert
nur den Bezugspunkt. *Zoom to Fit* zentriert lediglich die Ansicht.

> **Regel:** Nicht versuchen, das Board an eine optische Blattmitte zu koppeln.
> Entscheidend sind konsistente Koordinaten und identische Mechanik auf allen drei
> Boards. Der Boardmittelpunkt ist per Definition (0,0) — siehe
> [`04-mechanical.md`](04-mechanical.md).

Beim Übertragen von Koordinaten die **Y-Richtung** beachten: KiCad zählt Y im PCB-Editor
nach unten. Die Tabelle in `04-mechanical.md` führt beide Vorzeichen.

## 3. Bedienhinweise

- **`E`** öffnet die Eigenschaften des Objekts unter dem Cursor bzw. des gewählten
  Objekts. Alternativ Doppelklick oder Rechtsklick → *Properties*.
- Board-Dicke: *Board Setup → Physical Stackup*.
- Kreisförmige Outline: Kreis-Werkzeug auf Layer `Edge.Cuts`, danach mit `E` exakte
  Werte für Mittelpunkt und Radius eintragen — nicht per Maus positionieren.
- Bohrungen exakt setzen: Footprint platzieren, dann mit `E` die Koordinaten aus
  `04-mechanical.md` eintippen.

## 4. Wiederholte Kanäle

Motor-Kanal 1 und 2 sollen identisch sein. Statt zu kopieren: **hierarchische Sheets, die
auf dieselbe Sheet-Datei zeigen.** Änderungen wirken dann automatisch auf beide Kanäle,
und ein Auseinanderdriften ist ausgeschlossen. Die Zuordnung der Kanalnummer erfolgt über
Sheet-Instanzen.

## 5. Gemeinsame Bibliotheken

`hardware/lib/` nimmt projektübergreifende Symbole, Footprints und 3D-Modelle auf:

```
hardware/lib/
  switchstack.kicad_sym          Eigene Symbole
  switchstack.pretty/            Eigene Footprints
  3dmodels/                      STEP/WRL
```

Einbindung pro Projekt über *Preferences → Manage Symbol/Footprint Libraries*, Scope
**Project**, mit relativem Pfad über die Variable `${KIPRJMOD}`, damit die Projekte auf
jedem Rechner funktionieren:

```
${KIPRJMOD}/../lib/switchstack.kicad_sym
${KIPRJMOD}/../lib/switchstack.pretty
```

Selbst erstellte Footprints für Steckverbinder und mechanisch kritische Teile immer
gegen das Datenblatt prüfen und die Quelle im Footprint-Beschreibungsfeld vermerken.

## 6. Was ins Repository gehört

**Eingecheckt:**
`.kicad_pro`, `.kicad_sch`, `.kicad_pcb`, `.kicad_dru`, eigene Bibliotheken,
Dokumentation, `fp-lib-table` und `sym-lib-table`.

**Nicht eingecheckt** (siehe `.gitignore`):
`*-backups/`, `*.kicad_prl` (nutzerlokale Einstellungen), `fp-info-cache`,
Autosave-Dateien, `production/`.

Fertigungsdaten werden bewusst mit `git add -f` und einem Tag eingecheckt, nicht laufend.

## 7. Commit-Konventionen

KiCad-Dateien sind Textdateien, aber die Diffs sind schwer lesbar. Deshalb:

- **Kleine, thematische Commits.** Ein Commit pro abgeschlossenem Schritt, nicht ein
  Sammelcommit am Tagesende.
- **Aussagekräftige Nachricht**, die beschreibt *was fachlich* passiert ist, z. B.
  `bottom: 24V-Eingangsschutz mit Sicherung, TVS und Verpolschutz`.
- Präfix `bottom:`, `mid:`, `top:`, `docs:` oder `lib:` zur schnellen Zuordnung.
- KiCad vor dem Commit **schließen**, damit keine halb geschriebenen Dateien oder
  Lock-Dateien erfasst werden.
- Nach dem Verschieben vieler Bauteile nicht gleichzeitig die Schaltung ändern — sonst
  ist der Diff nicht mehr auswertbar.
