#!/usr/bin/env python3
"""
Minimaler Generator fuer KiCad-Schaltplaene (.kicad_sch).

Erzeugt netzlistenkorrekte Schaltplaene: jedes Bauteil wird platziert, an jeden
Pin kommt ein kurzer Draht mit einem globalen Label. Das ergibt keinen huebsch
gezeichneten Plan, aber einen *nachweislich korrekten* - und KiCad kann ihn
oeffnen und danach frei umarrangieren.

Der Sinn: Bauteilauswahl, Werte, Footprints und die komplette Konnektivitaet
entstehen aus einer pruefbaren Quelle statt aus Klickarbeit. Die Netzliste wird
anschliessend mit kicad-cli exportiert und gegen die Vorgabe verglichen.

Kein Ersatz fuer die Layoutarbeit in KiCad - eine Vorstufe.
"""

import hashlib
import math
import os
import re

def _symdir():
    """Symbolbibliothek finden - Linux, macOS oder per KICAD_SYMBOL_DIR."""
    for p in (os.environ.get("KICAD_SYMBOL_DIR"),
              "/usr/share/kicad/symbols",
              "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols"):
        if p and os.path.isdir(p):
            return p
    return "/usr/share/kicad/symbols"


SYMDIR = _symdir()
GRID = 1.27
STUB = 5.08   # Laenge der Drahtstummel zum Label


# ---------------------------------------------------------------------------
# S-Expression-Hilfen
# ---------------------------------------------------------------------------

def _balanced(s, start):
    """Gibt den balancierten Klammerausdruck ab Position start zurueck."""
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(s)):
        c = s[i]
        if esc:
            esc = False
            continue
        if c == '\\':
            esc = True
            continue
        if c == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return s[start:i + 1]
    raise ValueError("unbalancierte Klammern")


_libcache = {}


# KiCad 10 hat einige Symbole umbenannt bzw. in Gehaeusevarianten aufgeteilt.
# Gleiche Pinbelegung, nur anderer Name - deshalb hier eine Ersatzliste, damit
# die Generatoren mit KiCad 9 und 10 laufen. Netzlistengleichheit ist geprueft.
# Nur aufnehmen, was NACHWEISLICH dieselben Pinnummern hat.
# NICHT aufnehmen: Q_NPN_BCE -> Q_NPN. KiCad 10 nummeriert dessen Pins mit
# B/C/E statt 1/2/3 - ein stiller Alias wuerde die Anschluesse vertauschen.
SYM_ALIAS = {
    "Interface_Expansion:PCF8574": "Interface_Expansion:PCF8574T",  # SOIC-16, Pins 1..16
}


# Projekteigene Bibliothek. Sie enthaelt die generischen Transistorsymbole mit
# den Pinnummern 1/2/3. KiCad 10 hat die Stockvarianten auf G/D/S bzw. B/C/E
# umgestellt - das passt nicht zu SOT-23-Footprints (Pads 1/2/3) und wuerde die
# Netzliste still veraendern. Deshalb liegen sie hier im Projekt.
PROJDIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "hardware", "lib")


def load_symbol(lib_id):
    """Holt die Symboldefinition aus der Projekt- oder KiCad-Bibliothek."""
    if lib_id in _libcache:
        return _libcache[lib_id]
    lib, name = lib_id.split(":", 1)
    path = os.path.join(PROJDIR, lib + ".kicad_sym")
    if not os.path.exists(path):
        path = os.path.join(SYMDIR, lib + ".kicad_sym")
    src = open(path, encoding="utf-8").read()
    m = re.search(r'\(symbol "%s"[\s(]' % re.escape(name), src)
    if not m and lib_id in SYM_ALIAS:
        alt_lib, alt_name = SYM_ALIAS[lib_id].split(":", 1)
        alt_path = os.path.join(SYMDIR, alt_lib + ".kicad_sym")
        if os.path.exists(alt_path):
            src = open(alt_path, encoding="utf-8").read()
            m = re.search(r'\(symbol "%s"[\s(]' % re.escape(alt_name), src)
    if not m:
        raise KeyError("Symbol %s nicht in %s gefunden" % (lib_id, path))
    body = _balanced(src, m.start())
    _libcache[lib_id] = body
    return body


def symbol_parent(lib_id):
    """Bei abgeleiteten Symbolen die lib_id des Basissymbols, sonst None."""
    m = re.search(r'\(extends\s+"([^"]+)"', load_symbol(lib_id))
    if not m:
        return None
    return lib_id.split(":", 1)[0] + ":" + m.group(1)


def symbol_chain(lib_id):
    """[Basis, ..., lib_id] - alles, was in lib_symbols stehen muss."""
    chain = [lib_id]
    seen = {lib_id}
    p = symbol_parent(lib_id)
    while p:
        if p in seen:
            raise ValueError("Zyklische Vererbung bei %s" % lib_id)
        chain.insert(0, p)
        seen.add(p)
        p = symbol_parent(p)
    return chain


def flatten_symbol(lib_id):
    """Eigenstaendige Symboldefinition unter dem Namen lib_id.

    KiCad-Bibliotheken leiten viele Symbole ueber (extends "Basis") ab. In die
    lib_symbols eines Schaltplans laesst sich diese Vererbung nicht zuverlaessig
    uebernehmen - getestet, KiCad 7 lehnt die Datei ab. Deshalb wird die Grafik
    des Basissymbols unter dem Namen des abgeleiteten Symbols eingesetzt und die
    eigenen Eigenschaften (Value, Datasheet, ...) darueber gelegt.
    """
    chain = symbol_chain(lib_id)
    base, leaf_name = chain[0], lib_id.split(":", 1)[1]
    base_name = base.split(":", 1)[1]
    body = load_symbol(base)

    if base != lib_id:
        # Untersymbole (BASIS_0_1, BASIS_1_1, ...) mitbenennen
        body = body.replace('(symbol "%s_' % base_name, '(symbol "%s_' % leaf_name)
        # eigene Eigenschaften der Ableitung uebernehmen
        leaf = load_symbol(lib_id)
        for prop in ("Value", "Datasheet", "ki_description", "ki_keywords", "ki_fp_filters"):
            m = re.search(r'\(property "%s" ' % prop, leaf)
            if not m:
                continue
            new = _balanced(leaf, m.start())
            m2 = re.search(r'\(property "%s" ' % prop, body)
            if m2:
                body = body.replace(_balanced(body, m2.start()), new, 1)
            else:
                body = body[:body.index("\n")] + "\n    " + new + body[body.index("\n"):]

    body = body.replace('(symbol "%s"' % base_name, '(symbol "%s"' % lib_id, 1)
    return body


def symbol_units(lib_id):
    """{Einheit: {Pinnummer: (x, y)}} in Bibliothekskoordinaten (Y nach oben).

    KiCad legt die Grafik in Untersymbolen "NAME_<unit>_<style>" ab. Einheit 0
    gilt fuer alle Einheiten (typischerweise die Versorgungspins). Mehrfach-
    symbole wie LM393 muessen einzeln platziert werden - sonst landen Pins
    nicht platzierter Einheiten als lose Labels im Schaltplan und verbinden
    ungewollt Netze.
    """
    parent = symbol_parent(lib_id)
    if parent:
        return symbol_units(parent)
    body = load_symbol(lib_id)
    name = lib_id.split(":", 1)[1]
    units = {}
    for m in re.finditer(r'\(symbol "%s_(\d+)_\d+"' % re.escape(name), body):
        unit = int(m.group(1))
        sub = _balanced(body, m.start())
        for pm in re.finditer(r'\(pin\s+\w+\s+\w+\s+\(at\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\)',
                              sub):
            seg = _balanced(sub, pm.start())
            num = re.search(r'\(number\s+"([^"]*)"', seg)
            if num:
                # (x, y, Winkel). Der Winkel zeigt vom Anschlusspunkt zum
                # Symbolkoerper; der Drahtstummel muss also entgegengesetzt
                # laufen, sonst endet er auf einem Nachbarpin.
                units.setdefault(unit, {})[num.group(1)] = (
                    float(pm.group(1)), float(pm.group(2)), float(pm.group(3)))
    if not units:
        return {1: {}}
    # Einheit 0 gehoert zu jeder echten Einheit
    common = units.pop(0, {})
    if not units:
        return {1: common}
    for u in units:
        units[u].update(common)
    return units


def symbol_pins(lib_id):
    """{Pinnummer: (x, y)} ueber alle Einheiten - fuer Plausibilitaetspruefungen."""
    all_pins = {}
    for pins in symbol_units(lib_id).values():
        for num, v in pins.items():
            all_pins[num] = (v[0], v[1])
    return all_pins


def _uuid(*parts):
    """Deterministische UUID - damit zwei Laeufe identische Dateien erzeugen."""
    h = hashlib.sha1("|".join(str(p) for p in parts).encode()).hexdigest()
    return "%s-%s-%s-%s-%s" % (h[0:8], h[8:12], h[12:16], h[16:20], h[20:32])


# ---------------------------------------------------------------------------
# Schaltplan
# ---------------------------------------------------------------------------

class Component:
    def __init__(self, ref, lib_id, value, footprint="", fields=None):
        self.ref = ref
        self.lib_id = lib_id
        self.value = value
        self.footprint = footprint
        self.fields = fields or {}
        self.pos = (0.0, 0.0)


class Schematic:
    def __init__(self, project, title="", paper="A2"):
        self.project = project
        self.title = title
        self.paper = paper
        self.components = []
        self.nets = {}          # netname -> [(ref, pin), ...]

    def add(self, ref, lib_id, value, footprint="", **fields):
        c = Component(ref, lib_id, value, footprint, fields)
        self.components.append(c)
        return c

    def connect(self, net, *pins):
        """connect("VBUS", ("R1","1"), ("C3","2"))"""
        self.nets.setdefault(net, []).extend(pins)

    # -- Platzierung --------------------------------------------------------

    def _layout(self, cols=9, dx=50.8, dy=44.45, x0=25.4, y0=25.4):
        """Je Einheit ein Platz im Raster. Grosszuegig, damit die Label-Stummel
        verschiedener Bauteile sich nicht beruehren."""
        slots = []
        for c in self.components:
            c.units = sorted(symbol_units(c.lib_id))
            for u in c.units:
                slots.append((c, u))
        self.placements = {}
        for i, (c, u) in enumerate(slots):
            self.placements[(c.ref, u)] = (x0 + (i % cols) * dx,
                                           y0 + (i // cols) * dy)

    # -- Ausgabe ------------------------------------------------------------

    def write(self, path):
        self._layout()
        by_ref = {c.ref: c for c in self.components}
        pinpos = {}     # (ref, pin) -> (Anschlusspunkt, Stummelende)
        for c in self.components:
            for u, pins in symbol_units(c.lib_id).items():
                ox, oy = self.placements[(c.ref, u)]
                for num, (px, py, ang) in pins.items():
                    a = math.radians(ang)
                    # nach aussen = entgegen der Pinrichtung, Y im Blatt invertiert
                    ux, uy = -math.cos(a), math.sin(a)
                    at = (round(ox + px, 4), round(oy - py, 4))
                    end = (round(at[0] + STUB * ux, 4), round(at[1] + STUB * uy, 4))
                    pinpos[(c.ref, num)] = (at, end)

        # Welches Netz haengt an welchem Pin?
        net_of = {}
        for net, pins in self.nets.items():
            for pin in pins:
                if pin in net_of and net_of[pin] != net:
                    raise ValueError("Pin %s.%s liegt auf zwei Netzen: %s und %s"
                                     % (pin[0], pin[1], net_of[pin], net))
                net_of[pin] = net

        # Zwei Pins duerfen sich eine Koordinate nur teilen, wenn sie auf
        # demselben Netz liegen - KiCad stapelt intern verbundene Pins
        # (z. B. die beiden GND des INA240) absichtlich uebereinander.
        # Andernfalls wuerden fremde Netze stillschweigend verbunden.
        at_point = {}
        for key, (at, end) in pinpos.items():
            at_point.setdefault(at, []).append(key)
        for key, (at, end) in pinpos.items():
            # Ein Stummelende darf nicht auf einem fremden Pin landen
            if end in at_point and key not in at_point[end]:
                other = at_point[end][0]
                if net_of.get(key) != net_of.get(other):
                    raise ValueError(
                        "Stummel von %s.%s endet auf %s.%s (%s vs %s)"
                        % (key[0], key[1], other[0], other[1],
                           net_of.get(key), net_of.get(other)))
        for pt, keys in sorted(at_point.items()):
            nets = {net_of.get(k) for k in keys}
            if len(nets) > 1:
                raise ValueError(
                    "Koordinatenkollision bei %s: %s liegen auf verschiedenen Netzen (%s)"
                    % (pt, ", ".join("%s.%s" % k for k in keys),
                       ", ".join(str(n) for n in sorted(nets, key=str))))

        sheet_uuid = _uuid(self.project, "sheet")
        out = []
        out.append('(kicad_sch (version 20230121) (generator switchstack)')
        out.append('  (uuid %s)' % sheet_uuid)
        out.append('  (paper "%s")' % self.paper)
        if self.title:
            out.append('  (title_block (title "%s"))' % self.title)

        # -- Bibliothekssymbole --
        out.append('  (lib_symbols')
        seen = []
        for c in self.components:
            if c.lib_id in seen:
                continue
            seen.append(c.lib_id)
            out.append("    " + flatten_symbol(c.lib_id))
        out.append('  )')

        # -- Bauteile, je Einheit eine Instanz --
        for c in self.components:
            units = symbol_units(c.lib_id)
            for unit in sorted(units):
                x, y = self.placements[(c.ref, unit)]
                out.append('  (symbol (lib_id "%s") (at %.4f %.4f 0) (unit %d)'
                           % (c.lib_id, x, y, unit))
                out.append('    (in_bom yes) (on_board yes) (dnp no)')
                out.append('    (uuid %s)' % _uuid(self.project, c.ref, "u", unit))
                out.append('    (property "Reference" "%s" (at %.4f %.4f 0)'
                           % (c.ref, x + 6.35, y - 7.62))
                out.append('      (effects (font (size 1.27 1.27)) (justify left)))')
                out.append('    (property "Value" "%s" (at %.4f %.4f 0)'
                           % (c.value, x + 6.35, y - 5.08))
                out.append('      (effects (font (size 1.27 1.27)) (justify left)))')
                out.append('    (property "Footprint" "%s" (at %.4f %.4f 0)'
                           % (c.footprint, x, y))
                out.append('      (effects (font (size 1.27 1.27)) hide))')
                n = 0
                for k, v in c.fields.items():
                    out.append('    (property "%s" "%s" (at %.4f %.4f 0)'
                               % (k, v, x, y + 2.54 * (n + 1)))
                    out.append('      (effects (font (size 1.27 1.27)) hide))')
                    n += 1
                for num in sorted(units[unit]):
                    out.append('    (pin "%s" (uuid %s))'
                               % (num, _uuid(self.project, c.ref, unit, num)))
                out.append('    (instances (project "%s" (path "/%s"'
                           % (self.project, sheet_uuid))
                out.append('      (reference "%s") (unit %d))))' % (c.ref, unit))
                out.append('  )')

        # -- Draehte und globale Labels --
        # Je Koordinate genau ein Stummel, sonst entstehen bei gestapelten
        # Pins doppelte Labels an derselben Stelle.
        done_pts = set()
        for net, pins in sorted(self.nets.items()):
            for ref, pin in pins:
                if ref not in by_ref:
                    raise KeyError("Netz %s: Bauteil %s existiert nicht" % (net, ref))
                if (ref, pin) not in pinpos:
                    raise KeyError("Netz %s: %s hat keinen Pin %s" % (net, ref, pin))
                (px, py), (ex, ey) = pinpos[(ref, pin)]
                if (px, py) in done_pts:
                    continue
                done_pts.add((px, py))
                out.append('  (wire (pts (xy %.4f %.4f) (xy %.4f %.4f))' % (px, py, ex, ey))
                out.append('    (stroke (width 0) (type default)) (uuid %s))'
                           % _uuid(self.project, "w", ref, pin))
                out.append('  (global_label "%s" (shape bidirectional) (at %.4f %.4f 0)'
                           % (net, ex, ey))
                out.append('    (effects (font (size 1.27 1.27)) (justify left)) (uuid %s)'
                           % _uuid(self.project, "l", ref, pin))
                out.append('    (property "Intersheetrefs" "${INTERSHEET_REFS}" '
                           '(at %.4f %.4f 0) (effects (font (size 1.27 1.27)) hide)))'
                           % (ex, ey))

        out.append('  (sheet_instances (path "/" (page "1")))')
        out.append(')')
        open(path, "w", encoding="utf-8").write("\n".join(out) + "\n")
        return path
