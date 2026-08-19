#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Baut die HTML-Uebersicht des Projekts - mit eingebetteten Bildern.

Die Seite ist bewusst KEINE zweite Dokumentation neben docs/*.md, sondern
deren Schaufenster: Explosionszeichnung, die drei Ebenen, die harten Zahlen
und die Belegung des einen Feldsteckers.

Alle Zahlen werden beim Bauen aus den echten Boarddateien gelesen, nicht
eingetippt. Eine Doku, die ihre Zahlen selbst zaehlt, kann nicht veralten -
und beim Stapelbild hatte genau das schon einmal nicht geklappt.

Bilder werden als data:-URI eingebettet, weil die veroeffentlichte Seite
keine fremden Hosts laden darf. Sie werden dafuer verkleinert und auf 256
Farben reduziert; die Renderings haben einen transparenten Hintergrund und
sitzen so in beiden Themes auf dem Seitengrund statt auf einer weissen
Kachel.
"""

import base64
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDERS = os.path.join(ROOT, "docs", "renders")
ZIEL = os.path.join(ROOT, "docs", "switchstack.html")

BOARDS = [
    ("bottom_power_motor", "Bottom", "Leistung und Motoren", "rund, Ø 52,0 mm",
     "Zwei DRV8871-Vollbrücken treiben die beiden 24-V-Motoren. Hier sitzt "
     "auch der eine Feldstecker, über den die gesamte Verdrahtung der Dose "
     "läuft — auf der Unterseite, nach hinten aus dem Stapel heraus."),
    ("mid_logic", "Mid", "Logik und Kommunikation", "rund, Ø 52,0 mm",
     "ESP32 mit RS485 und der USB-C-Buchse fürs Flashen. Die Antenne zeigt "
     "nach unten in die Mitte, die Fläche dahinter ist ausgespart — die "
     "Dose hat mit Schrauben nur 54 mm lichte Weite."),
    ("top_ui", "Top", "Bedienung und Sensorik", "quadratisch, 47 × 47 mm",
     "Vier Ecktaster, ein 1,69-Zoll-Display, Abstands- und Raumtemperatur"
     "sensor hinter zwei symmetrischen Löchern der Zentralscheibe — und der "
     "Hauptschalter: Ohne aufgestecktes Top-Board oder mit Schalter aus "
     "bleibt das ganze Gerät stromlos. Quadratisch, weil die Druckkreuze "
     "der Zentralscheibe auf r = 26,9 mm liegen — ein Kreis reicht dort "
     "nicht hin."),
]

# Beschriftung der beiden Ansichten je Board: (F.Cu, B.Cu) - nach Funktion
# im eingebauten Zustand, nicht nach KiCads Lagennamen. Siehe Kommentar
# weiter unten bei den Ansichten.
SEITEN = {
    "bottom_power_motor": ("Nach hinten, in die Dose", "Zum Mid-Board"),
    "mid_logic": ("Zum Top-Board", "Zum Bottom-Board"),
    "top_ui": ("Nach vorn, zur Zentralscheibe", "Zum Mid-Board"),
}

# Der eine Feldstecker: Molex Micro-Fit 43045-1612, 2x8, stehend.
FELD = [
    ("1", "24V_IN", "Versorgung", "24 V DC ±10 %"),
    ("2", "PGND", "Versorgung", "Leistungsmasse"),
    ("3", "M1_A", "Motor 1", "Klappladen 1, Ader A"),
    ("4", "M1_B", "Motor 1", "Klappladen 1, Ader B"),
    ("5", "M2_A", "Motor 2", "Klappladen 2, Ader A"),
    ("6", "M2_B", "Motor 2", "Klappladen 2, Ader B"),
    ("7", "PGND", "Versorgung", "Leistungsmasse"),
    ("8", "RS485_A", "Bus", "Feldbus A"),
    ("9", "RS485_B", "Bus", "Feldbus B"),
    ("10", "REED1_IN", "Endlage", "Reed Klappladen 1"),
    ("11", "SAB1_IN", "Endlage", "Sabotage 1"),
    ("12", "REED2_IN", "Endlage", "Reed Klappladen 2"),
    ("13", "SAB2_IN", "Endlage", "Sabotage 2"),
    ("14", "HOOD_A", "Haube", "Haubenkontakt"),
    ("15", "HOOD_B", "Haube", "Haubenkontakt"),
    ("16", "PGND", "Versorgung", "Leistungsmasse"),
]


def zahlen(name):
    """Segmente, Vias und Bauteile direkt aus der Boarddatei zaehlen."""
    p = os.path.join(ROOT, "hardware", name, name + ".kicad_pcb")
    if not os.path.exists(p):
        return None
    s = open(p, encoding="utf-8").read()
    return {
        "segmente": len(re.findall(r"\(segment\b", s)),
        "vias": len(re.findall(r"\(via\b", s)),
        "bauteile": len(re.findall(r"\(footprint\b", s)),
        "lagen": len(re.findall(r"\(type signal\)", s)) or 4,
    }


def bild(datei, breite):
    """PNG verkleinern, Farben reduzieren, als data:-URI zurueckgeben."""
    pfad = os.path.join(RENDERS, datei)
    if not os.path.exists(pfad):
        return None
    from PIL import Image
    im = Image.open(pfad).convert("RGBA")
    if im.width > breite:
        h = round(im.height * breite / im.width)
        im = im.resize((breite, h), Image.LANCZOS)
    im = im.quantize(colors=256, method=Image.FASTOCTREE)
    puf = io.BytesIO()
    im.save(puf, format="PNG", optimize=True)
    roh = base64.b64encode(puf.getvalue()).decode("ascii")
    return "data:image/png;base64," + roh


def zelle(x):
    return "" if x is None else str(x)


def main():
    daten = {n: zahlen(n) for n, _, _, _, _ in BOARDS}
    fehlend = [n for n, d in daten.items() if d is None]
    if fehlend:
        print("Boarddateien fehlen: %s" % ", ".join(fehlend))
        return 1

    stapel = bild("stack.png", 1400)
    front = bild("front-explosion.png", 1900)
    ansichten = {}
    for n, _, _, _, _ in BOARDS:
        ansichten[n] = (bild("%s_top.png" % n, 760),
                        bild("%s_bottom.png" % n, 760))

    ges = {k: sum(d[k] for d in daten.values())
           for k in ("segmente", "vias", "bauteile")}

    h = []
    a = h.append
    a('<title>SwitchStack</title>')
    a('<link rel="preconnect" href="https://fonts.googleapis.com">')
    a('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>')
    a('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
      'family=IBM+Plex+Mono:wght@400;500&'
      'family=IBM+Plex+Sans+Condensed:wght@500;600;700&'
      'family=IBM+Plex+Sans:wght@400;500;600&display=swap">')
    a("<style>%s</style>" % CSS)

    a('<div class="seite">')

    # Kopf
    a('<header class="kopf">')
    a('<p class="marke">Unterputz-Klappladensteuerung</p>')
    a('<h1>SwitchStack</h1>')
    a('<p class="lead">Drei gestapelte Leiterplatten in einer 61 mm tiefen '
      'Schalterdose. Sie fahren zwei 24-V-Klappläden, erkennen Hindernisse '
      'ohne Motorelektronik und tragen vorne eine Busch-Jaeger-Zentralscheibe '
      'mit Display und vier Tastern.</p>')
    a('<dl class="kennzahlen">')
    for wert, was in (("3", "Platinen"), ("4", "Kupferlagen"),
                      (str(ges["bauteile"]), "Bauteile"),
                      ("1", "Feldstecker"), ("61 mm", "Einbautiefe")):
        a('<div><dt>%s</dt><dd>%s</dd></div>' % (wert, was))
    a('</dl>')
    a('</header>')

    # Explosionszeichnung
    a('<section class="block">')
    a('<h2>Der Stapel</h2>')
    a('<p class="mass">Von unten nach oben: Leistung, Logik, Bedienung. '
      'Die beiden runden Platinen sitzen <em>in</em> der Dose, die '
      'quadratische davor im gedruckten Adapter. Zwischen den Ebenen '
      'jeweils 10 mm.</p>')
    if stapel:
        a('<figure class="explosion">')
        a('<img src="%s" alt="Explosionszeichnung der drei Platinen '
          'übereinander">' % stapel)
        a('<figcaption>Explosionsdarstellung aus den echten Boarddateien '
          'gerendert — kein Handaufbau, sondern drei Einzelansichten '
          'versetzt übereinandergelegt.</figcaption>')
        a('</figure>')
    else:
        a('<p class="warnung">Stapelbild fehlt — erst '
          '<code>tools/render_all.py</code> laufen lassen.</p>')
    if front:
        a('<figure class="explosion">')
        a('<img src="%s" alt="Maßstäbliche Schnitte durch Abdeckrahmen, '
          'Zentralscheibe, Adapter, Top-Board und Displaypanel">' % front)
        a('<figcaption>Die Front im Schnitt — zwei maßstäbliche '
          'Schnittebenen, die Draufsicht und die eingebaute Tiefenlage. '
          'Gezeichnet aus den Parametern von <code>adapter.py</code> und '
          'den Layoutkonstanten, nicht gerendert; rot markiert sind die '
          'offenen Punkte. Erzeugt von '
          '<code>tools/gen_explosion.py</code>.</figcaption>')
        a('</figure>')
        a('<div class="halten">')
        a('<h3>Wer hält wen</h3>')
        a('<p>Der Abdeckrahmen hält nicht von allein — er wird geklemmt. '
          'Die Kette, von hinten nach vorn:</p>')
        a('<ol>')
        a('<li><b>Bottom und Mid verschrauben:</b> untere Hülsen '
          'Buchse/Buchse von hinten an Bottom, Mid auflegen, obere Hülsen '
          'Stift/Buchse von vorn durch Mid — der Stift klemmt Mid zwischen '
          'den Hülsen. Alle M2,5 × 9.</li>')
        a('<li>Die in der Dose vorverdrahtete <b>Feldstecker-Leiste</b> '
          'hinten an Bottom klicken, die Einheit in die Leerdose '
          'schieben.</li>')
        a('<li>Erst jetzt den <b>Tragring</b> aufsetzen — er fädelt über '
          'Hülsen und USB-Buchse — und mit den Geräteschrauben (60 mm) '
          'festschrauben. Andersherum ginge es nicht: Die Ø-52-Boards '
          'passen nicht durch seine 50,6er Öffnung.</li>')
        a('<li>Den <b>Abdeckrahmen</b> auf den Tragring klemmen — noch '
          'lose — und das Kabel des Magnetkontakts durch den '
          'Kabeldurchlass in J6 auf der Top-Rückseite stecken.</li>')
        a('<li>Das <b>Top-Board</b> im Scheibenadapter aufsetzen, zwei '
          'Schrauben von vorn in die Hülsen. Die <b>Drucklippe</b> an der '
          'Adapter-Vorderkante presst dabei den Rahmensteg gegen den '
          'Tragring — jetzt sitzt der Rahmen fest.</li>')
        a('<li>Die <b>Zentralscheibe</b> nur noch aufrasten. Sie hält '
          'nichts und presst nichts — sie ist das bewegliche '
          'Bedienelement, das die vier Ecktaster drückt, und muss dafür '
          'kraftfrei bleiben.</li>')
        a('</ol>')
        a('<p>Kraftfluss: Schraubenkopf → Top-Board → Adaptertasche → '
          'Drucklippe → Rahmensteg → Tragring → Dose. '
          'Reset und Boot des Mid-Boards liegen unter zwei Ø-3,2-Löchern '
          'im Top-Board — bei abgenommener Scheibe mit einem Stift '
          'drückbar, im Betrieb unsichtbar.</p>')
        a('</div>')
    a('<aside class="offen">')
    a('<p class="offen-titel">Offen: der Stapelverbinder</p>')
    a('<p>Alle drei Platinen tragen denselben Footprint einer '
      '2×20-Buchsenleiste im 1,27-mm-Raster — und drei Buchsen stecken '
      'nicht ineinander. Der Footprint ist ein Platzhalter für die '
      'Mechanik. Gesucht ist ein durchsteckbarer Stapelverbinder: ein '
      'Buchsenkörper mit verlängerten Schwänzen, die in die Buchse '
      'darunter greifen, Stapelhöhe 10 mm. Dasselbe Teil auf allen drei '
      'Boards, damit es keine Buchse/Stecker-Zuordnung und keine zweite '
      'Bestellnummer gibt. Die Teilenummer steht noch aus.</p>')
    a('</aside>')
    a('</section>')

    # Die drei Ebenen
    a('<section class="block">')
    a('<h2>Die drei Ebenen</h2>')
    a('<p class="mass">Die Reihenfolge ist keine Gliederung, sondern der '
      'physische Aufbau: Ebene 1 liegt zuunterst in der Dose, Ebene 3 zeigt '
      'in den Raum.</p>')
    a('<div class="ebenen">')
    for i, (n, kurz, rolle, form, text) in enumerate(BOARDS, 1):
        d = daten[n]
        oben, unten = ansichten[n]
        a('<article class="ebene">')
        a('<div class="ebene-kopf"><span class="ordnung">%d</span>'
          '<div><h3>%s</h3><p class="rolle">%s</p></div></div>' %
          (i, kurz, rolle))
        a('<p>%s</p>' % text)
        a('<ul class="fakten">')
        a('<li><span>Form</span><b>%s</b></li>' % form)
        a('<li><span>Bauteile</span><b>%d</b></li>' % d["bauteile"])
        a('<li><span>Segmente</span><b>%d</b></li>' % d["segmente"])
        a('<li><span>Vias</span><b>%d</b></li>' % d["vias"])
        a('</ul>')
        if oben or unten:
            a('<div class="ansichten">')
            # NICHT "Oberseite/Unterseite" beschriften. KiCads F.Cu ist nicht
            # verlaesslich die im Geraet obenliegende Seite: Auf Bottom traegt
            # F.Cu den Feldstecker und zeigt damit nach HINTEN in die Dose,
            # waehrend die Stapelbuchsen auf B.Cu nach oben weisen. Wer die
            # Bilder "Oberseite/Unterseite" nennt, dreht das Board fuer den
            # Leser um - genau darueber bin ich am 18.08.2026 selbst
            # gestolpert. Beschriftet wird deshalb nach Funktion.
            for img, lab in ((oben, SEITEN[n][0]), (unten, SEITEN[n][1])):
                if img:
                    a('<figure><img src="%s" alt="%s, %s"><figcaption>%s'
                      '</figcaption></figure>' % (img, kurz, lab, lab))
            a('</div>')
        a('</article>')
    a('</div>')
    a('</section>')

    # Feldstecker
    a('<section class="block">')
    a('<h2>Ein Stecker für alles</h2>')
    a('<p class="mass">Die gesamte Verdrahtung der Dose läuft über '
      'einen einzigen Molex Micro-Fit 43045-1612 auf der Unterseite des '
      'Bottom-Boards. Die Leiste wird in der Dose vorbereitet und der Stapel '
      'dann aufgesteckt — vorher waren es vier Steckverbinder auf zwei '
      'Ebenen.</p>')
    a('<div class="tabelle-rahmen"><table class="pins">')
    a('<thead><tr><th>Pin</th><th>Netz</th><th>Gruppe</th>'
      '<th>Bedeutung</th></tr></thead><tbody>')
    for pin, netz, gruppe, bed in FELD:
        a('<tr><td class="num">%s</td><td class="netz">%s</td>'
          '<td><span class="gruppe">%s</span></td><td>%s</td></tr>'
          % (pin, netz, gruppe, bed))
    a('</tbody></table></div>')
    a('</section>')

    # Zahlen
    a('<section class="block">')
    a('<h2>Zahlen</h2>')
    a('<p class="mass">Gezählt beim Bauen dieser Seite, direkt aus den '
      'Boarddateien.</p>')
    a('<div class="tabelle-rahmen"><table class="zahlen">')
    a('<thead><tr><th>Platine</th><th>Form</th><th>Lagen</th>'
      '<th>Bauteile</th><th>Segmente</th><th>Vias</th></tr></thead><tbody>')
    for n, kurz, _, form, _ in BOARDS:
        d = daten[n]
        a('<tr><td><b>%s</b></td><td>%s</td><td class="num">%d</td>'
          '<td class="num">%d</td><td class="num">%d</td>'
          '<td class="num">%d</td></tr>'
          % (kurz, form, d["lagen"], d["bauteile"], d["segmente"], d["vias"]))
    a('<tr class="summe"><td><b>Summe</b></td><td></td><td></td>'
      '<td class="num">%d</td><td class="num">%d</td><td class="num">%d</td>'
      '</tr>' % (ges["bauteile"], ges["segmente"], ges["vias"]))
    a('</tbody></table></div>')
    a('</section>')

    a('<footer class="fuss">')
    a('<p>Erzeugt aus den Boarddateien mit <code>tools/gen_doku_html.py</code>. '
      'Die ausführliche Dokumentation liegt in <code>docs/</code>, '
      'die Bestellhinweise in <code>docs/15-bestellung.md</code>.</p>')
    a('</footer>')

    a('</div>')

    open(ZIEL, "w", encoding="utf-8").write("\n".join(h))
    kb = os.path.getsize(ZIEL) / 1024.0
    print("geschrieben : %s (%.0f kB)" % (ZIEL, kb))
    print("Bauteile    : %d" % ges["bauteile"])
    print("Segmente    : %d" % ges["segmente"])
    print("Vias        : %d" % ges["vias"])
    return 0


CSS = """
:root{
  --grund:#f1f4f2; --flaeche:#fbfcfb; --tinte:#121a17; --matt:#5d6d67;
  --akzent:#a9541f; --linie:#d4dbd7; --raster:#e6ebe8;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --grund:#0d1311; --flaeche:#141c19; --tinte:#e2e9e5; --matt:#8c9d96;
    --akzent:#dd8a50; --linie:#222d28; --raster:#1a231f;
  }
}
:root[data-theme="dark"]{
  --grund:#0d1311; --flaeche:#141c19; --tinte:#e2e9e5; --matt:#8c9d96;
  --akzent:#dd8a50; --linie:#222d28; --raster:#1a231f;
}
*{box-sizing:border-box;}
body{
  margin:0; background:var(--grund); color:var(--tinte);
  font-family:"IBM Plex Sans","Helvetica Neue",Arial,sans-serif;
  font-size:17px; line-height:1.65;
  -webkit-font-smoothing:antialiased;
}
.seite{max-width:1080px; margin:0 auto; padding:clamp(2rem,5vw,4.5rem) 1.5rem 4rem;
  display:flex; flex-direction:column; gap:clamp(3rem,6vw,5rem);}
h1,h2,h3{font-family:"IBM Plex Sans Condensed","IBM Plex Sans",sans-serif;
  text-wrap:balance; margin:0;}
h1{font-size:clamp(3rem,9vw,5.5rem); font-weight:700; letter-spacing:-.02em;
  line-height:.98;}
h2{font-size:clamp(1.5rem,3.4vw,2.1rem); font-weight:600; letter-spacing:-.01em;}
h3{font-size:1.35rem; font-weight:600;}
p{margin:0;}
code{font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:.88em;
  background:var(--raster); padding:.1em .35em; border-radius:2px;}

.marke{font-family:"IBM Plex Mono",monospace; font-size:.75rem;
  text-transform:uppercase; letter-spacing:.18em; color:var(--akzent);
  margin-bottom:1rem;}
.kopf{display:flex; flex-direction:column; gap:1.5rem;}
.lead{font-size:clamp(1.05rem,2vw,1.25rem); max-width:62ch; color:var(--matt);}

.kennzahlen{display:flex; flex-wrap:wrap; gap:0; margin:1rem 0 0;
  border-top:1px solid var(--linie); border-bottom:1px solid var(--linie);}
.kennzahlen>div{flex:1 1 auto; min-width:8.5rem; padding:1.1rem 1.2rem 1.1rem 0;}
.kennzahlen dt{font-family:"IBM Plex Sans Condensed",sans-serif;
  font-size:2rem; font-weight:700; font-variant-numeric:tabular-nums;
  line-height:1;}
.kennzahlen dd{margin:.35rem 0 0; font-size:.8rem; color:var(--matt);
  text-transform:uppercase; letter-spacing:.1em;}

.block{display:flex; flex-direction:column; gap:1.25rem;}
.mass{max-width:66ch; color:var(--matt);}
.warnung{color:var(--akzent);}

.explosion{margin:0; display:flex; flex-direction:column; gap:.9rem;}
.explosion img{width:100%; height:auto; display:block;}
figcaption{font-size:.85rem; color:var(--matt); max-width:60ch;}

.ebenen{display:flex; flex-direction:column; gap:2.5rem;}
.ebene{display:flex; flex-direction:column; gap:1rem;
  padding-top:1.75rem; border-top:1px solid var(--linie);}
.ebene>p{max-width:64ch;}
.ebene-kopf{display:flex; align-items:baseline; gap:1rem;}
.ordnung{font-family:"IBM Plex Mono",monospace; font-size:.9rem;
  color:var(--akzent); border:1px solid var(--akzent); border-radius:50%;
  width:2rem; height:2rem; display:inline-flex; align-items:center;
  justify-content:center; flex:none;}
.rolle{font-size:.9rem; color:var(--matt);}

.fakten{list-style:none; margin:0; padding:0; display:flex; flex-wrap:wrap;
  gap:0 2.5rem;}
.fakten li{display:flex; flex-direction:column; padding:.4rem 0;}
.fakten span{font-size:.72rem; text-transform:uppercase; letter-spacing:.1em;
  color:var(--matt);}
.fakten b{font-family:"IBM Plex Mono",monospace; font-weight:500;
  font-variant-numeric:tabular-nums;}

.ansichten{display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr));
  gap:1.25rem;}
.ansichten figure{margin:0; display:flex; flex-direction:column; gap:.5rem;}
.ansichten img{width:100%; height:auto; display:block;}

.tabelle-rahmen{overflow-x:auto;}
table{border-collapse:collapse; width:100%; min-width:34rem; font-size:.92rem;}
th{font-family:"IBM Plex Sans Condensed",sans-serif; text-align:left;
  font-weight:600; font-size:.78rem; text-transform:uppercase;
  letter-spacing:.09em; color:var(--matt); padding:.6rem .8rem .6rem 0;
  border-bottom:1px solid var(--linie); white-space:nowrap;}
td{padding:.55rem .8rem .55rem 0; border-bottom:1px solid var(--raster);
  vertical-align:top;}
.num{font-family:"IBM Plex Mono",monospace; font-variant-numeric:tabular-nums;
  white-space:nowrap;}
.netz{font-family:"IBM Plex Mono",monospace; color:var(--akzent);
  white-space:nowrap;}
.gruppe{font-size:.75rem; text-transform:uppercase; letter-spacing:.07em;
  color:var(--matt); white-space:nowrap;}
.summe td{border-bottom:none; border-top:1px solid var(--linie);
  padding-top:.7rem;}

.halten{display:flex; flex-direction:column; gap:.6rem; max-width:66ch;}
.halten h3{font-size:1.1rem;}
.halten ol{margin:0; padding-left:1.4rem; display:flex;
  flex-direction:column; gap:.45rem;}
.halten p:last-child{color:var(--matt); font-size:.95rem;}

.offen{border-left:3px solid var(--akzent); padding:.2rem 0 .2rem 1.1rem;
  display:flex; flex-direction:column; gap:.5rem; max-width:66ch;}
.offen-titel{font-family:"IBM Plex Sans Condensed",sans-serif; font-weight:600;
  font-size:.78rem; text-transform:uppercase; letter-spacing:.1em;
  color:var(--akzent);}
.offen p:last-child{color:var(--matt); font-size:.95rem;}

.fuss{border-top:1px solid var(--linie); padding-top:1.5rem;
  font-size:.85rem; color:var(--matt);}

a:focus-visible,img:focus-visible{outline:2px solid var(--akzent);
  outline-offset:3px;}
@media (prefers-reduced-motion: reduce){*{animation:none!important;
  transition:none!important;}}
"""


if __name__ == "__main__":
    sys.exit(main())
