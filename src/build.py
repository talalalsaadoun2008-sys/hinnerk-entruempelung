#!/usr/bin/env python3
"""Baut die statische Website von Hinnerk – Entrümpelung Hamburg.

Aufruf:  python3 src/build.py            -> schreibt ins Hauptverzeichnis (= live über GitHub Pages)
         python3 src/build.py --out DIR  -> schreibt in einen anderen Ordner (Vorschau)
Daten:   src/site.json (Firma), src/stadtteile.json (Ortsseiten), src/leistungen.json (Leistungsseiten),
         src/bilder.json (historische Fotos mit Bildnachweis)
Gestaltung: „Hamburger Reederei-Plakat um 1900“ (Schrift Chivo, Farben aus dem Logo).
"""
import json, html, re, sys, hashlib, shutil
from pathlib import Path
from datetime import date
from urllib.parse import quote

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent
OUT = ROOT
if "--out" in sys.argv:
    OUT = Path(sys.argv[sys.argv.index("--out") + 1]).resolve()
    OUT.mkdir(parents=True, exist_ok=True)

SITE = json.loads((SRC / "site.json").read_text(encoding="utf-8"))
F = SITE["firma"]
BASE = SITE["base_url"]
ORTE = json.loads((SRC / "stadtteile.json").read_text(encoding="utf-8"))
LEIST = json.loads((SRC / "leistungen.json").read_text(encoding="utf-8"))
BILDER = json.loads((SRC / "bilder.json").read_text(encoding="utf-8"))
_KURZ = {l["slug"]: l for l in SITE["leistungen"]}
for _l in LEIST:
    _l["kurz"] = _KURZ[_l["slug"]]["kurz"]
    _l["plakat"] = _KURZ[_l["slug"]].get("plakat", _l["name"])
HEUTE = date.today().isoformat()
E = html.escape
BEZIRKE = ["Hamburg-Mitte", "Altona", "Eimsbüttel", "Hamburg-Nord", "Wandsbek", "Bergedorf", "Harburg"]


def slugify(s):
    s = s.lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss"), (".", ""), ("–", "-")):
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def ortslug(name):
    return "entruempelung-hamburg-" + slugify(name.replace("Hamburg-", ""))


for o in ORTE:
    o["slug"] = ortslug(o["name"])
SLUG_BY_NAME = {o["name"]: o["slug"] for o in ORTE}


def pick(key, options):
    h = int(hashlib.md5(key.encode()).hexdigest(), 16)
    return options[h % len(options)]


def mascot(size=40, label=None):
    a = f'role="img" aria-label="{E(label)}"' if label else 'aria-hidden="true"'
    return (f'<svg viewBox="0 0 120 120" width="{size}" height="{size}" {a}>'
            '<circle cx="60" cy="70" r="36" fill="#FBF6EA" stroke="#121A2E" stroke-width="6"/>'
            '<path d="M22 56 Q24 26 60 24 Q96 26 98 56 Z" fill="#121A2E"/>'
            '<path d="M18 57 Q60 69 102 57 L102 63 Q60 77 18 63 Z" fill="#121A2E"/>'
            '<circle cx="60" cy="37" r="5" fill="#F2C230"/>'
            '<circle cx="47" cy="81" r="4.5" fill="#121A2E"/><circle cx="73" cy="81" r="4.5" fill="#121A2E"/>'
            '<path d="M46 92 Q60 103 74 92" fill="none" stroke="#121A2E" stroke-width="5" stroke-linecap="round"/></svg>')


PFEIL = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12h14M12 5l7 7-7 7" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="square"/></svg>'


def bild(key, cls="", lazy=True, drift=False):
    b = BILDER[key]
    c = ' class="drift"' if drift else (f' class="{cls}"' if cls else "")
    return (f'<img src="img/{b["datei"]}" width="{b["w"]}" height="{b["h"]}" alt="{E(b["alt"])}"'
            f'{c}{" loading=\"lazy\"" if lazy else ""} decoding="async">')


def firma_schema():
    s = {"@type": "HomeAndConstructionBusiness", "@id": BASE + "#firma", "name": F["name"], "url": BASE,
         "email": F["email"], "logo": BASE + "logo.png", "image": BASE + "logo.png", "description": F["beschreibung"],
         "priceRange": "Festpreis nach kostenloser Besichtigung",
         "address": {"@type": "PostalAddress", "streetAddress": F["strasse"], "postalCode": F["plz"],
                     "addressLocality": F["ort"], "addressCountry": "DE"},
         "areaServed": [{"@type": "City", "name": "Hamburg"}]}
    if F["telefon"]:
        s["telephone"] = F["telefon_link"]
    return s


def head(title, desc, path, schema=None, robots="index,follow", preload=None):
    graph = [firma_schema()] + (schema or [])
    ld = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False)
    canon = BASE + ("" if path == "index.html" else path)
    pre = f'<link rel="preload" href="img/{BILDER[preload]["datei"]}" as="image">\n' if preload else ""
    return f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{canon}">
<meta property="og:type" content="website">
<meta property="og:locale" content="de_DE">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{BASE}logo.png">
<meta name="theme-color" content="#F2C230">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="logo.png">
<link rel="preload" href="assets/fonts/chivo-latin-900-normal.woff2" as="font" type="font/woff2" crossorigin>
{pre}<link rel="stylesheet" href="assets/site.css">
<script type="application/ld+json">{ld}</script>
</head>
<body>
<a class="skip" href="#inhalt">Zum Inhalt springen</a>
"""


def bar():
    return f"""<header class="bar">
<a class="wort" href="./" aria-label="Hinnerk – Entrümpelung Hamburg, zur Startseite">{mascot(40)}Hinnerk</a>
<nav aria-label="Hauptmenü"><a href="./#leistungen">Leistungen</a><a href="einsatzgebiet.html">Stadtteile</a><a href="./#kontakt">Kontakt</a></nav>
</header>
<main id="inhalt">
"""


def mailto(betreff, text):
    return f"mailto:{F['email']}?subject={quote(betreff)}&body={quote(text)}"


ANFRAGE_TEXT = "Moin Hinnerk,\n\nich möchte eine kostenlose Besichtigung.\nWas soll geräumt werden: \nStadtteil: \nWunschtermin: \nRückrufnummer: \n"


def held(h1, satz, aktion_text, aktion_href, foto, lang=False, size=None):
    st = f' style="font-size:clamp(2.6rem,{size}vw,9rem)"' if size else ""
    return f"""<section class="held{' klein' if lang else ''}" aria-labelledby="h1">
<div class="held-feld">
<h1 id="h1" class="{'lang' if lang else ''}"{st}>{h1}</h1>
<div class="bogen">{bild(foto, lazy=False)}</div>
</div>
<div class="held-band">
<p>{E(satz)}</p>
<a class="knopf knopf-gelb" href="{aktion_href}">{E(aktion_text)}</a>
</div>
</section>
"""


def kontakt_zeilen():
    return f"""<section id="kontakt" class="dunkel" aria-label="Kontakt">
<ul class="zeilen">
<li data-auf>Hinnerk</li>
<li data-auf><a href="https://www.openstreetmap.org/search?query={quote(F['strasse'] + ', ' + F['plz'] + ' ' + F['ort'])}" rel="noopener">{E(F['strasse'])}</a></li>
<li data-auf>{F['plz']} {E(F['ort'])}</li>
<li data-auf>Besichtigung kostenlos</li>
{f'<li data-auf><a href="tel:{F["telefon_link"]}">{E(F["telefon"])}</a></li>' if F['telefon'] else f'<li data-auf><a href="mailto:{F["email"]}">E-Mail schreiben</a></li>'}
<li class="gruss" data-auf>Moin <a class="pfeil" href="{mailto('Anfrage Entrümpelung', ANFRAGE_TEXT)}" aria-label="Anfrage per E-Mail an Hinnerk">{PFEIL}</a></li>
</ul>
</section>
"""


def fuss():
    leist = "".join(f'<li><a href="{l["slug"]}.html">{E(l["name"])}</a></li>' for l in LEIST)
    bez = "".join(f'<li><a href="einsatzgebiet.html#{slugify(b)}">{E(b)}</a></li>' for b in BEZIRKE)
    credits = "; ".join(f'<a href="{E(b["quelle"])}" rel="nofollow noopener">{E(b["titel"])}</a> ({E(b["lizenz"])})' for b in BILDER.values())
    leiste = (f'<a class="knopf knopf-gelb" href="tel:{F["telefon_link"]}">Anrufen</a>' if F["telefon"]
              else f'<a class="knopf knopf-gelb" href="{mailto("Anfrage Entrümpelung", ANFRAGE_TEXT)}">Kostenlos anfragen</a>')
    return f"""</main>
<footer class="fuss">
<div class="spalten">
<ul><li>Hinnerk – Entrümpelung Hamburg</li><li>Inh. {E(F['inhaber'])}</li><li>{E(F['strasse'])}</li><li>{F['plz']} {E(F['ort'])}</li><li><a href="mailto:{F['email']}">{F['email']}</a></li></ul>
<ul><li>Leistungen</li><li><a href="./">Entrümpelung Hamburg</a></li>{leist}</ul>
<ul><li>Bezirke</li>{bez}<li><a href="einsatzgebiet.html">Alle 99 Stadtteile</a></li></ul>
<ul><li>Rechtliches</li><li><a href="impressum.html">Impressum</a></li><li><a href="datenschutz.html">Datenschutz</a></li></ul>
</div>
<div></div>
<div>
<svg class="riesig" viewBox="0 0 1000 178" role="img" aria-label="Hinnerk"><text x="-6" y="168" textLength="1012" lengthAdjust="spacingAndGlyphs" font-family="Chivo" font-weight="900" font-size="228" fill="#121A2E">HINNERK</text></svg>
<p class="recht">© {date.today().year} Hinnerk – Entrümpelung Hamburg. Historische Fotos: {credits}.</p>
</div>
</footer>
<script src="assets/site.js" defer></script>
</body>
</html>
"""


def krumen(items):
    lis, ld = [], []
    for i, (name, url) in enumerate(items, 1):
        lis.append(f'<li><a href="{url}">{E(name)}</a></li>' if url else f'<li aria-current="page">{E(name)}</li>')
        it = {"@type": "ListItem", "position": i, "name": name}
        if url:
            it["item"] = BASE + ("" if url == "./" else url)
        ld.append(it)
    return (f'<nav class="quellen" aria-label="Brotkrumen" style="margin-bottom:40px"><ol style="list-style:none;display:flex;flex-wrap:wrap;gap:6px;padding:0;margin:0">{"".join(lis)}</ol></nav>',
            {"@type": "BreadcrumbList", "itemListElement": ld})


def faq_schema(faq):
    return {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q["q"],
            "acceptedAnswer": {"@type": "Answer", "text": q["a"]}} for q in faq]}


def faq_karten(titel, faq):
    karten = []
    for i, q in enumerate(faq[:6]):
        reiter = q.get("reiter") or pick(q["q"], ["Gut zu wissen", "Frage", "Ablauf", "Vor Ort"])
        karten.append(f'<details name="faq"{" open" if i == 0 else ""}>'
                      f'<summary><span class="reiter">{E(reiter)}</span>{E(q["q"])}</summary><p>{E(q["a"])}</p></details>')
    return f"""<section class="abschnitt fragen" aria-labelledby="faq-h">
<div class="fragen-wrap">
<h2 id="faq-h" data-auf>{E(titel)}</h2>
<div class="karten" data-auf style="--d:80ms">{''.join(karten)}</div>
</div>
</section>
"""


ABLAUF = [
    ("Anfrage", "Sie schreiben kurz, was raus soll: Wohnung, Haus, Keller oder ein paar Möbel. Ein Foto hilft, ist aber kein Muss.", "hafen"),
    ("Besichtigung", "Hinnerk kommt vorbei und sieht sich Räume, Treppen und den Weg zum Wagen an. Das kostet nichts und verpflichtet zu nichts.", "hollaendischer_brook"),
    ("Festpreis", "Sie bekommen einen festen Preis, bevor wir anfangen. Was wir bei der Besichtigung gesehen haben, ist darin enthalten.", "dovenfleet"),
    ("Räumung", "Am vereinbarten Tag räumen wir. Was Sie behalten möchten, bleibt stehen – vorher klar abgesprochen.", "landungsbruecken"),
    ("Entsorgung", "Sperrmüll, Holz, Metall und Elektrogeräte gehen getrennt zu den Recyclinghöfen der Stadtreinigung.", "speicherstadt"),
]


def ablauf(titel, text):
    lis = []
    for i, (name, txt, foto) in enumerate(ABLAUF):
        lis.append(f'<li class="{"offen" if i == 0 else ""}"><button type="button" aria-expanded="{"true" if i == 0 else "false"}" aria-label="{E(name)} öffnen"></button>'
                   f'<span class="senk">{E(name)}</span><div class="inhalt"><div><h3>{E(name)}</h3><p>{E(txt)}</p></div>{bild(foto)}</div></li>')
    return f"""<section class="abschnitt" id="ablauf" aria-labelledby="ablauf-h">
<div class="einleitung"><h2 id="ablauf-h" data-auf>{E(titel)}</h2><p data-auf style="--d:80ms">{E(text)}</p></div>
<ol class="akk" data-auf style="--d:160ms">{''.join(lis)}</ol>
</section>
"""


START_FAQ = [
    {"reiter": "Preis", "q": "Was kostet eine Entrümpelung in Hamburg?", "a": "Das hängt davon ab, wie viel raus muss, in welchem Stockwerk und wie weit der Weg zum Wagen ist. Darum besichtigt Hinnerk kostenlos und nennt Ihnen danach einen festen Preis."},
    {"reiter": "Dabei sein", "q": "Muss ich bei der Räumung dabei sein?", "a": "Nein. Wichtig ist, dass vorher klar ist, was bleiben soll. Den Schlüssel können Sie uns übergeben."},
    {"reiter": "Entsorgung", "q": "Wohin kommen die Sachen?", "a": "Sperrmüll, Holz, Metall, Elektrogeräte und andere Abfälle bringen wir getrennt zur Entsorgung, zum Beispiel zu den Recyclinghöfen der Stadtreinigung Hamburg."},
    {"reiter": "Gebiet", "q": "In welchen Stadtteilen ist Hinnerk unterwegs?", "a": "In allen 99 bewohnten Hamburger Stadtteilen. Jeder hat eine eigene Seite mit Infos vor Ort und einem Recyclinghof in der Nähe."},
    {"reiter": "Begriffe", "q": "Haushaltsauflösung oder Wohnungsauflösung – was ist der Unterschied?", "a": "Bei einer Haushaltsauflösung wird ein ganzer Hausstand aufgelöst, oft nach einem Todesfall. Bei einer Wohnungsauflösung geht es darum, die Räume leer zu bekommen, zum Beispiel für die Übergabe."},
    {"reiter": "Papiere", "q": "Was passiert mit Dokumenten und Fotos?", "a": "Wichtige Papiere nehmen Sie am besten vorher an sich. Was wir beim Räumen finden und wichtig aussieht, legen wir für Sie zur Seite."},
]

RECYCLINGHOEFE = [
    ("West", [("St. Pauli", "Feldstraße 69"), ("Bahrenfeld", "Rondenbarg 52 a"), ("Osdorf", "Brandstücken 36"), ("Niendorf", "Krähenweg 22")]),
    ("Nord und Ost", [("Hummelsbüttel", "Lademannbogen 32"), ("Steilshoop", "Schwarzer Weg 10"), ("Sasel", "Volksdorfer Weg 196"), ("Wandsbek", "Wilma-Witte-Stieg 6")]),
    ("Süd und Südost", [("Billbrook", "Liebigstraße 66"), ("Bergedorf", "Kampweg 9"), ("Harburg", "Neuländer Kamp 6"), ("Neugraben-Fischbek", "Am Aschenland 11")]),
]


def finder_und_blatt():
    daten = {o["name"]: {"b": o["bezirk"], "r": f'{o["recyclinghof"]["ort"]}, {o["recyclinghof"]["adresse"]}', "s": o["slug"]} for o in ORTE}
    opts = []
    for b in BEZIRKE:
        os_ = "".join(f'<option>{E(o["name"])}</option>' for o in sorted([o for o in ORTE if o["bezirk"] == b], key=lambda x: x["name"]))
        opts.append(f'<optgroup label="Bezirk {E(b)}">{os_}</optgroup>')
    gruppen = "".join(f'<h3>{E(g)}</h3><ul>' + "".join(f'<li><span>{E(n)}</span>{E(a)}</li>' for n, a in items) + '</ul>' for g, items in RECYCLINGHOEFE)
    return f"""<section class="karte" id="stadtteile" aria-label="Stadtteile und Recyclinghöfe">
{bild("plan")}
<div class="karte-raster">
<div class="finder" id="finder" data-mail="{F['email']}" data-auf>
<h2>Wo wohnen Sie?</h2>
<label for="ort-wahl">Ihr Stadtteil</label>
<select id="ort-wahl"><option value="">Bitte wählen …</option>{''.join(opts)}</select>
<div class="ergebnis" aria-live="polite"><noscript><p><a href="einsatzgebiet.html">Alle Stadtteile ansehen</a></p></noscript></div>
</div>
<div class="bogenblatt" data-auf style="--d:120ms">
<h2>Die zwölf Recyclinghöfe</h2>
<p class="notiz">Hier landet, was Hinnerk aus Hamburger Wohnungen trägt.</p>
{gruppen}
<p class="fuss-notiz">Quelle: Stadtreinigung Hamburg, INFO 2026<br>Sperrmüll, Holz, Metall und Elektrogeräte getrennt</p>
</div>
</div>
<script type="application/json" id="finder-daten">{json.dumps(daten, ensure_ascii=False)}</script>
</section>
"""


def write(path, text):
    (OUT / path).write_text(text, encoding="utf-8")


# ---------------------------------------------------------------- Startseite
def startseite():
    t = "Entrümpelung Hamburg ✓ Haushaltsauflösung ✓ Festpreis | Hinnerk"
    d = "Entrümpelung in Hamburg: Wohnung, Haus, Keller, Nachlass, Messie-Wohnung, Büro. ✓ Kostenlose Besichtigung ✓ Festpreis ✓ In allen 99 Stadtteilen. Hinnerk aus Altona."
    page = head(t, d, "index.html", [faq_schema(START_FAQ), {"@type": "WebSite", "url": BASE, "name": "Hinnerk – Entrümpelung Hamburg", "inLanguage": "de"}], preload="speicherstadt")
    page += bar()
    page += held("Hinnerk räumt.", "Entrümpelung in allen 99 Hamburger Stadtteilen. Erst kostenlos besichtigen, dann ein fester Preis.",
                 "Besichtigung anfragen", "#stadtteile", "speicherstadt")
    rows = ['<p class="name kopf" data-auf>Was raus muss:</p><p class="text" data-auf>Von einem Sofa bis zum ganzen Haus. Jede Leistung hat ihre eigene Seite.</p>']
    for i, l in enumerate(LEIST):
        rows.append(f'<p class="name" data-auf style="--d:{60 + i * 60}ms"><a href="{l["slug"]}.html">{E(l["plakat"])}</a></p>'
                    f'<p class="text" data-auf style="--d:{90 + i * 60}ms">{E(l["kurz"])}</p>')
    page += f"""<section class="abschnitt" id="leistungen" aria-label="Leistungen">
<div class="plakat">{''.join(rows)}</div>
</section>
"""
    page += f"""<section class="speicher" aria-label="Speicher">
<figure class="gross" data-auf style="margin:0">{bild("hollaendischer_brook", drift=True)}<figcaption>{E(BILDER["hollaendischer_brook"]["unterschrift"])}</figcaption></figure>
<div class="seite"><blockquote data-auf style="--d:90ms;margin-bottom:32px">In Hamburg heißt der Dachboden Speicher. Irgendwann ist jeder voll.</blockquote>
<figure data-auf style="margin:0;--d:160ms">{bild("dovenfleet")}<figcaption>{E(BILDER["dovenfleet"]["unterschrift"])}</figcaption></figure></div>
</section>
"""
    page += ablauf("So läuft’s", "Fünf Schritte vom ersten Satz bis zum leeren Raum. Den Preis kennen Sie, bevor jemand eine Kiste anfasst.")
    page += finder_und_blatt()
    page += faq_karten("Gut zu wissen", START_FAQ)
    page += kontakt_zeilen()
    page += fuss()
    write("index.html", page)


# ---------------------------------------------------------------- Unterseiten-Bausteine
def h1_groesse(zeilen):
    n = max(len(z) for z in zeilen)
    return round(min(9.0, 150 / (0.68 * n)), 2)


def anfrage(seite, ort=""):
    return f"""<section class="abschnitt dunkel" id="anfrage" aria-labelledby="anfrage-h">
<div class="anfrage">
<div class="links"><h2 id="anfrage-h" data-auf>Anfrage an Hinnerk</h2>
<p data-auf style="--d:80ms;margin-top:24px">Schreiben Sie kurz, was geräumt werden soll. Wir melden uns, besichtigen kostenlos und nennen Ihnen einen festen Preis.</p>
<p data-auf style="--d:140ms">E-Mail: <a href="mailto:{F['email']}">{F['email']}</a></p></div>
<form id="anfrage-form" data-mail="{F['email']}" data-seite="{E(seite)}" data-auf style="--d:120ms">
<label>Was soll geräumt werden?<select name="was"><option>Ganze Wohnung</option><option>Ganzes Haus</option><option>Haushaltsauflösung</option><option>Nachlass</option><option>Messie-Wohnung</option><option>Büro oder Firma</option><option>Keller, Dachboden oder Garage</option><option>Sperrmüll</option></select></label>
<label>Ort oder Stadtteil<input name="ort" value="{E(ort)}" autocomplete="address-level2"></label>
<label>Wunschtermin<input name="termin" placeholder="z. B. Ende November"></label>
<label>Kurze Beschreibung<textarea name="nachricht" placeholder="Wie viele Zimmer? Welches Stockwerk? Gibt es einen Aufzug?"></textarea></label>
<label>Ihr Name<input name="name" autocomplete="name" required></label>
<label>Telefon für Rückruf<input name="telefon" type="tel" autocomplete="tel"></label>
<button class="knopf knopf-gelb" type="submit">Anfrage per E-Mail senden</button>
<p style="font-size:15px;margin:0">Das Formular öffnet Ihr E-Mail-Programm. Auf dieser Website wird nichts gespeichert.</p>
</form>
</div>
</section>
"""


def rand_bild(key, schluessel):
    b = BILDER[key]
    return f'<figure class="rand" data-auf style="margin:0">{bild(key)}<figcaption>{E(b["unterschrift"])}</figcaption></figure>'


FOTOS = ["hafen", "hollaendischer_brook", "dovenfleet", "landungsbruecken", "speicherstadt"]


def leistungsseite(l):
    k, ld = krumen([("Startseite", "./"), (l["name"], None)])
    schema = [ld, faq_schema(l["faq"]), {"@type": "Service", "name": l["h1"], "serviceType": l["name"],
              "provider": {"@id": BASE + "#firma"}, "areaServed": {"@type": "City", "name": "Hamburg"}}]
    foto = pick(l["slug"], FOTOS)
    page = head(l["title"], l["description"], l["slug"] + ".html", schema, preload=foto) + bar()
    zeilen = [l["name"], "in Hamburg"]
    page += held(f'{E(zeilen[0])}<br>{E(zeilen[1])}', l["lead"], "Kostenlos besichtigen lassen", "#anfrage", foto, lang=True, size=h1_groesse(zeilen))
    secs = "".join(f'<h2 data-auf>{E(s["h2"])}</h2><div data-auf style="--d:80ms">{s["html"]}</div>' for s in l["sections"])
    andere = "".join(f'<li><a href="{x["slug"]}.html">{E(x["name"])}</a></li>' for x in LEIST if x["slug"] != l["slug"])
    page += f"""<section class="abschnitt" aria-label="{E(l['name'])}">
<div class="lesen">
{rand_bild(pick(l['slug'] + 'r', [f for f in FOTOS if f != foto]), l['slug'])}
<div class="spalte">{k}{secs}
<h2 data-auf>Auch das räumt Hinnerk</h2><ul class="schlagworte" data-auf>{andere}</ul>
<h2 data-auf>In Ihrem Stadtteil</h2><p data-auf>Hinnerk ist in allen 99 Hamburger Stadtteilen unterwegs. <a href="einsatzgebiet.html">Hier finden Sie Ihren Stadtteil</a> mit einem Recyclinghof in der Nähe.</p>
</div></div>
</section>
"""
    page += ablauf("So läuft’s", "Erst kostenlos besichtigen, dann ein fester Preis – auch bei einer " + l["name"] + ".")
    page += faq_karten("Fragen zur " + l["name"] if not l["name"].startswith(("Keller", "Sperr", "Büro", "Messie")) else "Häufige Fragen", l["faq"])
    page += anfrage(l["name"])
    page += fuss()
    write(l["slug"] + ".html", page)


LEAD_VARIANTEN = [
    "Wohnung, Haus oder Keller in {o} soll leer werden? Hinnerk besichtigt kostenlos und räumt zum Festpreis.",
    "Haushaltsauflösung oder Entrümpelung in {o}: erst kostenlos ansehen, dann ein fester Preis.",
    "Ob Keller, Dachboden oder ganze Wohnung – in {o} räumt Hinnerk zum festen Preis.",
    "Platz schaffen in {o}: Hinnerk entrümpelt Wohnungen, Häuser und Keller im Bezirk {b}.",
]
H2_WOHNEN = ["Wohnen in {o}", "So ist {o} gebaut", "Häuser in {o}", "Räumen in {o}"]
H2_KURZ = ["{o} kurz erklärt", "Ein Stück {o}", "Gut zu wissen", "{o} im Bezirk {b}"]


def ortsseite(o, alle_im_bezirk):
    n, b = o["name"], o["bezirk"]
    ort_hh = n if n.startswith("Hamburg") else f"Hamburg-{n}"
    title = f"Entrümpelung {n} ✓ Haushaltsauflösung ✓ Festpreis | Hinnerk"
    if len(title) > 68:
        title = f"Entrümpelung {n} ✓ Festpreis | Hinnerk"
    rh = o["recyclinghof"]
    desc = f"Entrümpelung und Haushaltsauflösung in {ort_hh}: Wohnung, Haus, Keller. ✓ Kostenlose Besichtigung ✓ Festpreis. Recyclinghof in der Nähe: {rh['ort']}."
    k, ld = krumen([("Startseite", "./"), ("Stadtteile", "einsatzgebiet.html"), (n, None)])
    faq = list(o.get("faq", []))[:3]
    faq.append({"reiter": "Ablauf", "q": f"Wie läuft eine Entrümpelung in {n} ab?",
                "a": "Sie stellen eine Anfrage, wir besichtigen kostenlos und nennen einen festen Preis. Am vereinbarten Tag räumen wir und bringen alles getrennt zur Entsorgung."})
    schema = [ld, faq_schema(faq), {"@type": "Service", "name": f"Entrümpelung {ort_hh}", "serviceType": "Entrümpelung",
              "provider": {"@id": BASE + "#firma"}, "areaServed": {"@type": "Place", "name": ort_hh,
              "containedInPlace": {"@type": "City", "name": "Hamburg"}}}]
    foto = pick(n, FOTOS)
    page = head(title, desc, o["slug"] + ".html", schema, preload=foto) + bar()
    v = {"o": n, "b": b}
    zeilen = ["Entrümpelung", n]
    page += held(f'Entrümpelung<br>{E(n)}', pick(n + "lead", LEAD_VARIANTEN).format(**v),
                 f"Besichtigung in {n}" if len(n) <= 14 else "Kostenlos besichtigen", "#anfrage", foto, lang=True, size=h1_groesse(zeilen))
    quart = o.get("quartiere") or []
    quart_satz = ""
    if quart:
        liste = ", ".join(quart[:-1]) + " und " + quart[-1] if len(quart) > 1 else quart[0]
        quart_satz = f"<p>Zu {E(n)} gehören unter anderem {E(liste)}. Egal in welchem Teil Sie wohnen: Hinnerk kommt zu Ihnen.</p>"
    kurz = (f"<h2 data-auf>{E(pick(n + 'h2b', H2_KURZ).format(**v))}</h2><p data-auf>{E(o['geschichte'])}</p>" if o.get("geschichte") else "")
    nach = "".join(f'<li><a href="{SLUG_BY_NAME[x]}.html">{E(x)}</a></li>' if x in SLUG_BY_NAME else f"<li><span>{E(x)}</span></li>" for x in o.get("nachbarn", []))
    bez = "".join(f'<li><a href="{x["slug"]}.html">{E(x["name"])}</a></li>' for x in alle_im_bezirk if x["slug"] != o["slug"])
    leist = "".join(f'<li><a href="{l["slug"]}.html">{E(l["name"])}</a></li>' for l in LEIST)
    quellen = "".join(f'<li><a href="{E(q["url"])}" rel="nofollow noopener">{E(q["titel"])}</a></li>' for q in o.get("quellen", []))
    quellen += '<li><a href="https://files.stadtreinigung.hamburg/SRH_25_028_Info_Broschuere_2026_Web.pdf" rel="nofollow noopener">Stadtreinigung Hamburg: INFO-Broschüre 2026</a></li>'
    page += f"""<section class="abschnitt" aria-label="Entrümpelung in {E(n)}">
<div class="lesen">
{rand_bild(pick(n + 'r', [f for f in FOTOS if f != foto]), n)}
<div class="spalte">{k}
<h2 data-auf>{E(pick(n + 'h2a', H2_WOHNEN).format(**v))}</h2>
<p data-auf>{E(o['bebauung'])}</p>
<p data-auf>{E(o['raeumung'])}</p>
{quart_satz}
{kurz}
<h2 data-auf>Recyclinghof {E(rh['ort'])}</h2>
<p data-auf>Ein Recyclinghof der Stadtreinigung Hamburg in der Nähe von {E(n)} ist <b>{E(rh['ort'])}, {E(rh['adresse'])}</b>. Dort werden Sperrmüll, Holz, Metall und Elektrogeräte getrennt angenommen. Wenn Hinnerk für Sie räumt, kümmern wir uns um den Transport.</p>
<h2 data-auf>Was Hinnerk in {E(n)} räumt</h2>
<ul class="schlagworte" data-auf>{leist}</ul>
</div></div>
</section>
"""
    page += ablauf(f"Entrümpelung in {n}", "Fünf Schritte, ein fester Preis. Sie wissen vorher, was es kostet.")
    page += faq_karten(f"Fragen zu {n}", faq)
    page += f"""<section class="abschnitt papier" aria-label="Umgebung">
<div class="lesen"><div class="rand"></div><div class="spalte">
<h2 data-auf>In der Nähe</h2><ul class="schlagworte" data-auf>{nach}</ul>
<h2 data-auf>Bezirk {E(b)}</h2><ul class="schlagworte" data-auf>{bez}</ul>
<div class="quellen" style="margin-top:56px"><h3>Quellen</h3><ul>{quellen}</ul></div>
</div></div>
</section>
"""
    page += anfrage(n, n)
    page += fuss()
    write(o["slug"] + ".html", page)


def einsatzgebiet():
    k, ld = krumen([("Startseite", "./"), ("Stadtteile", None)])
    t = "Entrümpelung in allen 99 Hamburger Stadtteilen | Hinnerk"
    d = "Hinnerk entrümpelt in allen 7 Hamburger Bezirken. Übersicht über 99 Stadtteile mit eigener Seite und einem Recyclinghof in der Nähe."
    page = head(t, d, "einsatzgebiet.html", [ld], preload="landungsbruecken") + bar()
    page += held("99 Stadtteile.", "Hinnerk ist in allen sieben Bezirken unterwegs. Wählen Sie Ihren Stadtteil.", "Stadtteil wählen", "#liste", "landungsbruecken")
    rows = []
    for i, b in enumerate(BEZIRKE):
        li = "".join(f'<li><a href="{o["slug"]}.html">{E(o["name"])}</a></li>' for o in sorted([o for o in ORTE if o["bezirk"] == b], key=lambda x: x["name"]))
        rows.append(f'<h2 id="{slugify(b)}" data-auf style="margin-top:{"0" if i == 0 else "72px"}">{E(b)}</h2><ul class="schlagworte" data-auf>{li}</ul>')
    page += f"""<section class="abschnitt" id="liste" aria-label="Alle Stadtteile">
<div class="lesen">{rand_bild('plan', 'plan')}<div class="spalte">{k}{''.join(rows)}</div></div>
</section>
"""
    page += kontakt_zeilen() + fuss()
    write("einsatzgebiet.html", page)


def rechtliches():
    tel = f"Telefon: {E(F['telefon'])}<br>" if F["telefon"] else ""
    def seite(path, titel, inhalt):
        p = head(f"{titel} | Hinnerk", f"{titel} von Hinnerk – Entrümpelung Hamburg.", path, robots="noindex,follow") + bar()
        p += f'<section class="abschnitt" style="padding-top:160px"><div class="lesen"><div class="rand"></div><div class="spalte"><h1 style="font-size:var(--step-head);margin-bottom:40px">{titel}</h1>{inhalt}</div></div></section>'
        write(path, p + fuss())
    seite("impressum.html", "Impressum", f"""<h2>Angaben gemäß § 5 DDG</h2>
<p>Hinnerk – Entrümpelung Hamburg<br>Inhaber: {E(F['inhaber'])}<br>{E(F['strasse'])}<br>{F['plz']} {E(F['ort'])}</p>
<h2>Kontakt</h2><p>{tel}E-Mail: <a href="mailto:{F['email']}">{F['email']}</a></p>
<h2>Verbraucherstreitbeilegung</h2><p>Wir sind nicht bereit und nicht verpflichtet, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.</p>
<h2>Bildnachweis</h2><ul>{''.join(f'<li><a href="{E(b["quelle"])}" rel="nofollow noopener">{E(b["titel"])}</a> – {E(b["urheber"])}, {E(b["lizenz"])}</li>' for b in BILDER.values())}</ul>""")
    seite("datenschutz.html", "Datenschutz", f"""<h2>1. Verantwortlicher</h2>
<p>Hinnerk – Entrümpelung Hamburg, Inhaber {E(F['inhaber'])}, {E(F['strasse'])}, {F['plz']} {E(F['ort'])}<br>{tel}E-Mail: <a href="mailto:{F['email']}">{F['email']}</a></p>
<h2>2. Hosting</h2><p>Diese Website wird bei GitHub Pages gehostet, einem Dienst der GitHub Inc., 88 Colin P. Kelly Jr. Street, San Francisco, CA 94107, USA. Beim Aufruf der Seite verarbeitet GitHub technisch notwendige Daten wie Ihre IP-Adresse, Datum und Uhrzeit des Abrufs sowie Browser-Informationen, um die Seite auszuliefern und vor Angriffen zu schützen. Rechtsgrundlage ist unser berechtigtes Interesse an einer sicheren und zuverlässigen Bereitstellung der Website (Art. 6 Abs. 1 lit. f DSGVO). GitHub ist eine Tochter der Microsoft Corporation; Microsoft ist nach dem EU-US Data Privacy Framework zertifiziert, auf dessen Grundlage Daten in die USA übermittelt werden dürfen.</p>
<h2>3. Schriftarten und Bilder</h2><p>Schriftarten und Bilder dieser Website sind lokal eingebunden. Beim Aufruf werden keine Verbindungen zu Google oder anderen Anbietern aufgebaut.</p>
<h2>4. Anfrageformular, E-Mail und Telefon</h2><p>Das Anfrageformular speichert keine Daten auf dieser Website, sondern öffnet Ihr E-Mail-Programm mit einer vorbereiteten Nachricht. Wenn Sie uns per E-Mail oder Telefon kontaktieren, verarbeiten wir Ihre Angaben (z. B. Name, Telefonnummer, Beschreibung des Auftrags, Wunschtermin), um Ihre Anfrage zu bearbeiten und ein Angebot zu erstellen. Rechtsgrundlage ist die Anbahnung oder Erfüllung eines Vertrags (Art. 6 Abs. 1 lit. b DSGVO). Wir löschen die Daten, wenn sie nicht mehr benötigt werden und keine gesetzlichen Aufbewahrungspflichten bestehen.</p>
<h2>5. Cookies</h2><p>Diese Website setzt keine Cookies und verwendet keine Analyse- oder Werbedienste.</p>
<h2>6. Ihre Rechte</h2><p>Sie haben das Recht auf Auskunft, Berichtigung, Löschung, Einschränkung der Verarbeitung, Datenübertragbarkeit und Widerspruch. Außerdem können Sie sich bei einer Datenschutz-Aufsichtsbehörde beschweren, in Hamburg beim Hamburgischen Beauftragten für Datenschutz und Informationsfreiheit.</p>""")
    p = head("Seite nicht gefunden | Hinnerk", "Diese Seite gibt es nicht.", "404.html", robots="noindex,follow") + bar()
    p += held("Leer geräumt.", "Diese Seite gibt es nicht (mehr). Zurück zur Startseite oder zu allen Stadtteilen.", "Zur Startseite", "./", "hafen")
    p += fuss()
    for a, b in (('href="assets/', 'href="/assets/'), ('src="assets/', 'src="/assets/'), ('src="img/', 'src="/img/'),
                 ('href="img/', 'href="/img/'), ('href="favicon', 'href="/favicon'), ('href="logo', 'href="/logo'),
                 ('href="./', 'href="/'), ('href="einsatzgebiet', 'href="/einsatzgebiet'), ('href="impressum', 'href="/impressum'),
                 ('href="datenschutz', 'href="/datenschutz')):
        p = p.replace(a, b)
    for l in LEIST:
        p = p.replace(f'href="{l["slug"]}', f'href="/{l["slug"]}')
    write("404.html", p)


def sitemap(pfade):
    urls = "".join(f"<url><loc>{BASE}{'' if p == 'index.html' else p}</loc><lastmod>{HEUTE}</lastmod></url>" for p in pfade)
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE}sitemap.xml\n")
    write("CNAME", "hinnerk-entruempelung.de\n")


def favicon():
    write("favicon.svg", mascot(64).replace('width="64" height="64" aria-hidden="true"', 'xmlns="http://www.w3.org/2000/svg" width="64" height="64"') + "\n")


if __name__ == "__main__":
    if OUT != ROOT:
        for d in ("assets", "img"):
            if (OUT / d).exists():
                shutil.rmtree(OUT / d)
            shutil.copytree(ROOT / d, OUT / d)
        if (ROOT / "logo.png").exists():
            shutil.copy(ROOT / "logo.png", OUT / "logo.png")
    startseite()
    for l in LEIST:
        leistungsseite(l)
    for o in ORTE:
        ortsseite(o, [x for x in ORTE if x["bezirk"] == o["bezirk"]])
    einsatzgebiet()
    rechtliches()
    favicon()
    pfade = ["index.html"] + [l["slug"] + ".html" for l in LEIST] + ["einsatzgebiet.html"] + [o["slug"] + ".html" for o in ORTE]
    sitemap(pfade)
    print(f"Fertig: {len(pfade)} Seiten in der Sitemap, Ausgabe: {OUT}")
