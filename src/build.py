#!/usr/bin/env python3
"""Baut die statische Website von Hinnerk – Entrümpelung Hamburg.

Aufruf:  python3 src/build.py            -> schreibt ins Hauptverzeichnis (= live über GitHub Pages)
         python3 src/build.py --out DIR  -> schreibt in einen anderen Ordner (Vorschau)
Daten:   src/site.json (Firma), src/stadtteile.json (Ortsseiten), src/leistungen.json (Leistungsseiten),
         src/fotos.json (Fotos)
Gestaltung: warm und weich – heller Sandgrund, Nachtblau, Gelb aus dem Logo, runde Karten (Schrift Figtree).
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
FOTOS = json.loads((SRC / "fotos.json").read_text(encoding="utf-8"))
RAT = json.loads((SRC / "ratgeber.json").read_text(encoding="utf-8"))
_KURZ = {l["slug"]: l for l in SITE["leistungen"]}
for _l in LEIST:
    _l["kurz"] = _KURZ[_l["slug"]]["kurz"]
    _l["plakat"] = _KURZ[_l["slug"]].get("plakat", _l["name"])
HEUTE = date.today().isoformat()
E = html.escape
BEZIRKE = ["Hamburg-Mitte", "Altona", "Eimsbüttel", "Hamburg-Nord", "Wandsbek", "Bergedorf", "Harburg"]

# Foto und Icon je Leistung
L_FOTO = {"hausaufloesung-hamburg": "hero", "dachboden-entruempeln-hamburg": "speicher", "garage-entruempeln-hamburg": "keller",
          "firmenaufloesung-hamburg": "transporter", "entruempelung-fuer-vermieter-hamburg": "kartons","haushaltsaufloesung-hamburg": "haushalt", "wohnungsaufloesung-hamburg": "wohnung",
          "keller-entruempeln-hamburg": "keller", "nachlassaufloesung-hamburg": "nachlass",
          "messie-wohnung-raeumen-hamburg": "messie", "bueroaufloesung-hamburg": "buero",
          "sperrmuell-abholen-hamburg": "sperrmuell"}
L_ICON = {"hausaufloesung-hamburg": "haus", "dachboden-entruempeln-hamburg": "dach", "garage-entruempeln-hamburg": "rad",
          "firmenaufloesung-hamburg": "kisten", "entruempelung-fuer-vermieter-hamburg": "schluessel","haushaltsaufloesung-hamburg": "lampe", "wohnungsaufloesung-hamburg": "haus",
          "keller-entruempeln-hamburg": "treppe", "nachlassaufloesung-hamburg": "rahmen",
          "messie-wohnung-raeumen-hamburg": "kisten", "bueroaufloesung-hamburg": "koffer",
          "sperrmuell-abholen-hamburg": "sofa"}
# Talal (27.10.2026): alle 99 Stadtteile bei Google lassen. True = alle indexierbar.
# False = nur KERN_ORTE indexierbar (Schutz gegen Googles Doorway-Regel, siehe Obsidian „Google-Leitfaden – was Google mag“).
ALLE_ORTE_INDEXIEREN = True
KERN_ORTE = ["Altona-Altstadt", "Altona-Nord", "Ottensen", "Bahrenfeld", "Sternschanze", "St. Pauli", "Eimsbüttel", "Eppendorf",
             "Winterhude", "Barmbek-Nord", "Wandsbek", "Rahlstedt", "Blankenese", "Harburg", "Bergedorf"]
ORT_FOTOS = ["hero", "wohnung", "kartons", "haushalt", "transporter", "speicher"]


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


# ---------------------------------------------------------------- kleine Bausteine
def mascot(size=40, label=None):
    a = f'role="img" aria-label="{E(label)}"' if label else 'aria-hidden="true"'
    return (f'<svg viewBox="0 0 120 120" width="{size}" height="{size}" {a}>'
            '<circle cx="60" cy="70" r="36" fill="#FBF6EA" stroke="#1F2A44" stroke-width="6"/>'
            '<path d="M22 56 Q24 26 60 24 Q96 26 98 56 Z" fill="#1F2A44"/>'
            '<path d="M18 57 Q60 69 102 57 L102 63 Q60 77 18 63 Z" fill="#1F2A44"/>'
            '<circle cx="60" cy="37" r="5" fill="#F2C230"/>'
            '<circle cx="47" cy="81" r="4.5" fill="#1F2A44"/><circle cx="73" cy="81" r="4.5" fill="#1F2A44"/>'
            '<path d="M46 92 Q60 103 74 92" fill="none" stroke="#1F2A44" stroke-width="5" stroke-linecap="round"/></svg>')


ICONS = {
    "haus": "M3 11l9-7 9 7v9a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1z",
    "lampe": "M8 3h8l3 8H5zM12 11v8M8 21h8",
    "treppe": "M3 20h4v-4h4v-4h4V8h4V4h2",
    "dach": "M2 20L12 4l10 16M7 20v-5h10v5",
    "rahmen": "M4 4h16v16H4zM4 16l5-5 4 4 3-3 4 4M15 8.5a1 1 0 1 0 0 .01",
    "kisten": "M3 13h8v8H3zM13 13h8v8h-8zM8 4h8v9H8zM6 16h2M16 16h2M11 7h2",
    "koffer": "M3 8h18v12H3zM8 8V5h8v3M3 13h18M11 13v2h2v-2",
    "sofa": "M5 10V8a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v2M3 12a2 2 0 0 1 4 0v2h10v-2a2 2 0 0 1 4 0v5H3zM5 17v2M19 17v2",
    "auge": "M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12zM12 9.5a2.5 2.5 0 1 0 0 5a2.5 2.5 0 1 0 0-5",
    "euro": "M17 6.5A7 7 0 1 0 17 17.5M4 10h9M4 14h9",
    "pin": "M12 21s-7-6-7-11a7 7 0 0 1 14 0c0 5-7 11-7 11zM12 8a2 2 0 1 0 0 4a2 2 0 1 0 0-4",
    "kreis": "M20 12a8 8 0 0 1-14.3 5M4 12a8 8 0 0 1 14.3-5M18 3v4h-4M6 21v-4h4",
    "tv": "M3 6h18v12H3zM8 21h8M12 18v3",
    "bett": "M2 11h20v6H2zM2 17v3M22 17v3M5 11V8h6v3",
    "akten": "M3 8h18v12H3zM3 8l2-4h14l2 4M9 13h6",
    "rolle": "M5 5h11v14H5zM16 5a2.5 7 0 0 1 0 14M5 9h11M5 15h11",
    "stuhl": "M7 3v18M7 13h10v8M17 13l1-5H7",
    "shirt": "M8 3L3 6l2 4 3-1v12h8V9l3 1 2-4-5-3a4 4 0 0 1-8 0z",
    "tasse": "M4 9h13v6a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5zM17 10h2a2.5 2.5 0 0 1 0 5h-2M8 3v3M12 3v3",
    "rad": "M5.5 14a3.5 3.5 0 1 0 0 7a3.5 3.5 0 1 0 0-7M18.5 14a3.5 3.5 0 1 0 0 7a3.5 3.5 0 1 0 0-7M5.5 17.5L9 10h7l2.5 7.5M8 7h3M16 10l-4.5 7.5",
    "schluessel": "M15 3a5 5 0 1 0 0 10a5 5 0 1 0 0-10M11.5 11.5L3 20M6 17l2 2M8.5 14.5l2 2",
    "kalender": "M3 5h18v16H3zM3 10h18M8 3v4M16 3v4",
    "post": "M3 5h18v14H3zM3 6l9 7 9-7",
    "besen": "M14 3l-4 10M6 13h8l2 8H4zM8 17v4M12 17v4",
    "telefon": "M5 3h4l2 5-2.5 1.5a12 12 0 0 0 6 6L16 13l5 2v4a2 2 0 0 1-2 2A17 17 0 0 1 3 5a2 2 0 0 1 2-2z",
}


def icon(name, size=28, cls="ic"):
    return (f'<svg class="{cls}" viewBox="0 0 24 24" width="{size}" height="{size}" aria-hidden="true">'
            f'<path d="{ICONS[name]}" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>')


HAKEN = '<svg viewBox="0 0 24 24" width="26" height="26" aria-hidden="true"><circle cx="12" cy="12" r="11" fill="#1F2A44"/><path d="M7 12.5l3.2 3L17 9" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
KREUZ = '<svg viewBox="0 0 24 24" width="26" height="26" aria-hidden="true"><circle cx="12" cy="12" r="10.2" fill="none" stroke="#1F2A44" stroke-width="1.6"/><path d="M8.5 8.5l7 7M15.5 8.5l-7 7" stroke="#1F2A44" stroke-width="1.6" stroke-linecap="round"/></svg>'
PFEIL = '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path d="M5 12h13M13 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'


def foto(key, cls="", lazy=True, sizes="100vw"):
    b = FOTOS[key]
    c = f' class="{cls}"' if cls else ""
    return (f'<img src="img/{b["datei"]}" width="{b["w"]}" height="{b["h"]}" alt="{E(b["alt"])}"'
            f'{c}{" loading=\"lazy\"" if lazy else " fetchpriority=\"high\""} decoding="async">')


def tel_link(text=None):
    return f'<a href="tel:{F["telefon_link"]}">{E(text or F["telefon"])}</a>' if F["telefon"] else ""


def mailto(betreff, text):
    return f"mailto:{F['email']}?subject={quote(betreff)}&body={quote(text)}"


ANFRAGE_TEXT = "Moin Hinnerk,\n\nich möchte eine kostenlose Besichtigung.\nWas soll geräumt werden: \nStadtteil: \nWunschtermin: \nRückrufnummer: \n"


def firma_schema():
    s = {"@type": "HomeAndConstructionBusiness", "@id": BASE + "#firma", "name": "Hinnerk Entrümpelung", "alternateName": F["name"], "url": BASE,
         "email": F["email"], "logo": BASE + "logo.png", "image": BASE + "img/" + FOTOS["hero"]["datei"], "description": F["beschreibung"],
         "priceRange": "Festpreis nach kostenloser Besichtigung",
         "address": {"@type": "PostalAddress", "streetAddress": F["strasse"], "postalCode": F["plz"],
                     "addressLocality": F["ort"], "addressCountry": "DE"},
         "areaServed": [{"@type": "City", "name": "Hamburg"}] + [{"@type": "AdministrativeArea", "name": f"Bezirk {b}"} for b in BEZIRKE],
         "knowsAbout": ["Entrümpelung", "Haushaltsauflösung", "Wohnungsauflösung", "Nachlassauflösung", "Messie-Wohnung räumen",
                        "Büroauflösung", "Keller entrümpeln", "Sperrmüll abholen", "Recyclinghöfe Hamburg"],
         "makesOffer": [{"@type": "Offer", "itemOffered": {"@type": "Service", "name": l["name"], "url": BASE + l["slug"] + ".html"}} for l in LEIST],
         "slogan": "Erst kostenlos besichtigen, dann ein fester Preis."}
    if F["telefon"]:
        s["telephone"] = F["telefon_link"]
    if SITE.get("profile"):
        s["sameAs"] = SITE["profile"]
    return s


def head(title, desc, path, schema=None, robots="index,follow", preload=None):
    graph = [firma_schema()] + (schema or [])
    ld = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False)
    canon = BASE + ("" if path == "index.html" else path)
    pre = f'<link rel="preload" href="img/{FOTOS[preload]["datei"]}" as="image">\n' if preload else ""
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
<meta property="og:image" content="{BASE}img/{FOTOS[preload or 'hero']['datei']}">
<meta name="theme-color" content="#1F2A44">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="logo.png">
<link rel="preload" href="assets/fonts/figtree-latin-600-normal.woff2" as="font" type="font/woff2" crossorigin>
{pre}<link rel="stylesheet" href="assets/site.css">
<script type="application/ld+json">{ld}</script>
</head>
<body>
<a class="skip" href="#inhalt">Zum Inhalt springen</a>
"""


VORTEILE_BAND = ["Kostenlose Besichtigung", "Festpreis vor Beginn", "In allen 99 Hamburger Stadtteilen", "Getrennte Entsorgung"]


def bar():
    band = "".join(f'<span>✓ {E(v)}</span><i aria-hidden="true">•</i>' for v in VORTEILE_BAND)
    nav = (f'<a href="./#leistungen">Leistungen</a><a href="./#ablauf">So läuft’s</a>'
           f'<a href="einsatzgebiet.html">Stadtteile</a><a href="ratgeber.html">Ratgeber</a>')
    kopf = (f'<a class="kopf-knopf" href="tel:{F["telefon_link"]}" aria-label="Hinnerk anrufen: {F["telefon"]}">{icon("telefon", 22)}<span>{F["telefon"]}</span></a>'
            if F["telefon"] else f'<a class="kopf-knopf" href="#anfrage" aria-label="Anfrage an Hinnerk">{icon("post", 22)}<span>Anfrage</span></a>')
    menue_tel = f'<a class="knopf knopf-gelb" href="tel:{F["telefon_link"]}">Anrufen: {F["telefon"]}</a>' if F["telefon"] else ""
    menue_leist = "".join(f'<a href="{l["slug"]}.html">{E(l["name"])}</a>' for l in LEIST)
    return f"""<div class="laufband" aria-label="Unsere Versprechen"><div class="lauf">{band}{band.replace('<span>', '<span aria-hidden="true">')}</div></div>
<header class="kopf">
<details class="menue"><summary aria-label="Menü öffnen"><span></span><span></span><span></span></summary>
<nav aria-label="Menü">{nav}<a href="ueber-hinnerk.html">Über Hinnerk</a><a href="kontakt.html">Kontakt</a><hr>{menue_leist}<a class="knopf" href="{mailto('Anfrage Entrümpelung', ANFRAGE_TEXT)}">Kostenlos anfragen</a>{menue_tel}</nav></details>
<nav class="haupt" aria-label="Hauptmenü">{nav}</nav>
<a class="wort" href="./" aria-label="Hinnerk – Entrümpelung Hamburg, zur Startseite">{mascot(34)}<span>HINNERK</span></a>
{kopf}
</header>
<main id="inhalt">
"""


def held(h1, satz, knopf, href, bild_key, eyebrow=None, klein=False):
    eb = f'<p class="eyebrow hell">{E(eyebrow)}</p>' if eyebrow else ""
    return f"""<section class="held{' held-klein' if klein else ''}" aria-labelledby="h1">
<div class="held-karte">
{foto(bild_key, lazy=False)}
<div class="held-text">{eb}<h1 id="h1">{h1}</h1><p>{E(satz)}</p><a class="knopf knopf-weiss" href="{href}">{E(knopf)}</a></div>
</div>
</section>
"""


def zwei_karten(items):
    k = "".join(f'<a class="bildkarte" href="{href}">{foto(f, sizes="50vw")}<span class="oben">{E(o)}</span><span class="unten">{E(u)}</span></a>'
                for href, f, o, u in items)
    return f'<section class="zwei" aria-label="Beliebte Leistungen">{k}</section>\n'


def vorteile():
    v = [("auge", "Kostenlose Besichtigung", "Hinnerk sieht sich alles vor Ort an. Das kostet nichts und verpflichtet zu nichts."),
         ("euro", "Fester Preis vorher", "Sie kennen den Preis, bevor jemand eine Kiste anfasst."),
         ("kreis", "Getrennt entsorgt", "Sperrmüll, Holz, Metall und Elektrogeräte gehen getrennt zu den Recyclinghöfen."),
         ("pin", "Ganz Hamburg", "In allen 99 Stadtteilen und 7 Bezirken unterwegs.")]
    k = "".join(f'<li data-auf style="--d:{i * 70}ms"><span class="kreisicon">{icon(ic, 46)}</span><h3>{E(t)}</h3><p>{E(p)}</p></li>' for i, (ic, t, p) in enumerate(v))
    return f'<section class="abschnitt vorteile" aria-labelledby="vorteile-h"><h2 id="vorteile-h" class="sr">Was Sie bei Hinnerk bekommen</h2><ul>{k}</ul></section>\n'


def leistungs_reihe(titel="Was Hinnerk räumt", ausser=None):
    karten = []
    for l in LEIST:
        if l["slug"] == ausser:
            continue
        karten.append(f'<li><a class="karte" href="{l["slug"]}.html">{foto(L_FOTO[l["slug"]], sizes="300px")}'
                      f'<span class="karte-text"><b>{E(l["name"])}</b><span>{E(l["kurz"])}</span><em>Mehr erfahren {PFEIL}</em></span></a></li>')
    return f"""<section class="abschnitt" id="leistungen" aria-labelledby="leist-h">
<div class="kopfzeile"><h2 id="leist-h" data-auf>{E(titel)}</h2><div class="pfeile" aria-hidden="true"><button type="button" data-schieb="-1">‹</button><button type="button" data-schieb="1">›</button></div></div>
<ul class="reihe" data-reihe>{''.join(karten)}</ul>
</section>
"""


AUSWAHL = [("haus", "Ganze Wohnung", "wohnungsaufloesung-hamburg"), ("haus", "Ganzes Haus", "hausaufloesung-hamburg"),
           ("lampe", "Haushalt", "haushaltsaufloesung-hamburg"), ("rahmen", "Nachlass", "nachlassaufloesung-hamburg"),
           ("treppe", "Keller", "keller-entruempeln-hamburg"), ("dach", "Dachboden", "dachboden-entruempeln-hamburg"),
           ("rad", "Garage", "garage-entruempeln-hamburg"), ("kisten", "Messie-Wohnung", "messie-wohnung-raeumen-hamburg"),
           ("koffer", "Büro", "bueroaufloesung-hamburg"), ("akten", "Laden & Lager", "firmenaufloesung-hamburg"),
           ("sofa", "Sperrmüll", "sperrmuell-abholen-hamburg"), ("schluessel", "Für Vermieter", "entruempelung-fuer-vermieter-hamburg")]


def auswahl():
    k = "".join(f'<a href="{s}.html">{icon(ic, 34)}<span>{E(t)}</span></a>' for ic, t, s in AUSWAHL)
    return f"""<section class="abschnitt" aria-labelledby="wahl-h">
<div class="wahl">{foto("kartons")}<div class="wahl-innen"><h2 id="wahl-h" data-auf>Was soll raus?</h2><p data-auf>Wählen Sie eins aus</p>
<div class="wahl-knoepfe" data-auf style="--d:100ms">{k}</div></div></div>
</section>
"""


DINGE = [("sofa", "Möbel"), ("tv", "Elektrogeräte"), ("bett", "Matratzen"), ("akten", "Akten & Kartons"), ("rolle", "Teppiche"),
         ("stuhl", "Gartenmöbel"), ("shirt", "Kleidung"), ("tasse", "Hausrat"), ("rad", "Fahrräder")]


def dinge():
    k = "".join(f'<li data-auf style="--d:{i * 40}ms"><span class="kreisicon">{icon(ic, 44)}</span>{E(t)}</li>' for i, (ic, t) in enumerate(DINGE))
    return f"""<section class="abschnitt dinge" aria-labelledby="dinge-h">
<p class="eyebrow">Hinnerk nimmt mit</p><h2 id="dinge-h" data-auf>Vom Sofa bis zur letzten Kiste</h2>
<ul>{k}</ul>
</section>
"""


ABLAUF = [("post", "Anfrage", "Sie schreiben kurz, was raus soll: Wohnung, Haus, Keller oder ein paar Möbel. Ein Foto hilft, ist aber kein Muss."),
          ("auge", "Besichtigung", "Hinnerk kommt vorbei und sieht sich Räume, Treppen und den Weg zum Wagen an. Kostenlos und unverbindlich."),
          ("euro", "Festpreis", "Sie bekommen einen festen Preis, bevor wir anfangen. Was wir gesehen haben, ist darin enthalten."),
          ("kisten", "Räumung", "Am vereinbarten Tag räumen wir. Was Sie behalten möchten, bleibt stehen – vorher klar abgesprochen."),
          ("kreis", "Entsorgung", "Sperrmüll, Holz, Metall und Elektrogeräte gehen getrennt zu den Recyclinghöfen der Stadtreinigung.")]


def ablauf(titel, text):
    k = "".join(f'<li data-auf style="--d:{i * 60}ms"><span class="nr">{i + 1}</span><span class="kreisicon klein">{icon(ic, 30)}</span><h3>{E(n)}</h3><p>{E(t)}</p></li>'
                for i, (ic, n, t) in enumerate(ABLAUF))
    return f"""<section class="abschnitt" id="ablauf" aria-labelledby="ablauf-h">
<div class="ablauf-kopf"><div><p class="eyebrow">So läuft’s</p><h2 id="ablauf-h" data-auf>{E(titel)}</h2></div><p data-auf>{E(text)}</p></div>
<ol class="schritte">{k}</ol>
</section>
"""


VERGLEICH = ["Kein Transporter mieten", "Kein Schleppen durchs Treppenhaus", "Keine Fahrten zum Recyclinghof",
             "Kosten vorher klar", "Ein Termin, dann ist es leer"]


def vergleich():
    rows = "".join(f'<tr><th scope="row">{E(r)}</th><td class="wir">{HAKEN}<span class="sr">Ja</span></td><td>{KREUZ}<span class="sr">Nein</span></td></tr>' for r in VERGLEICH)
    return f"""<section class="abschnitt vergleich" aria-labelledby="vgl-h">
<div class="vgl-kopf"><h2 id="vgl-h" data-auf>Hinnerk oder selbst machen?</h2><p data-auf>Selbst räumen klingt günstig – bis man Wagen, Helfer und Fahrten zusammenrechnet.</p>
<a class="knopf" href="#anfrage">Kostenlos besichtigen lassen</a></div>
<div class="tabelle" data-auf><table>
<thead><tr><td></td><th scope="col" class="wir"><span class="wort klein">{mascot(26)}HINNERK</span></th><th scope="col">Selbst machen</th></tr></thead>
<tbody>{rows}</tbody></table></div>
</section>
"""


RECYCLINGHOEFE = [
    ("West", [("St. Pauli", "Feldstraße 69"), ("Bahrenfeld", "Rondenbarg 52 a"), ("Osdorf", "Brandstücken 36"), ("Niendorf", "Krähenweg 22")]),
    ("Nord und Ost", [("Hummelsbüttel", "Lademannbogen 32"), ("Steilshoop", "Schwarzer Weg 10"), ("Sasel", "Volksdorfer Weg 196"), ("Wandsbek", "Wilma-Witte-Stieg 6")]),
    ("Süd und Südost", [("Billbrook", "Liebigstraße 66"), ("Bergedorf", "Kampweg 9"), ("Harburg", "Neuländer Kamp 6"), ("Neugraben-Fischbek", "Am Aschenland 11")]),
]


def finder():
    daten = {o["name"]: {"b": o["bezirk"], "r": f'{o["recyclinghof"]["ort"]}, {o["recyclinghof"]["adresse"]}', "s": o["slug"]} for o in ORTE}
    opts = []
    for b in BEZIRKE:
        os_ = "".join(f'<option>{E(o["name"])}</option>' for o in sorted([o for o in ORTE if o["bezirk"] == b], key=lambda x: x["name"]))
        opts.append(f'<optgroup label="Bezirk {E(b)}">{os_}</optgroup>')
    gruppen = "".join(f'<div><h3>{E(g)}</h3><ul>' + "".join(f'<li><b>{E(n)}</b>{E(a)}</li>' for n, a in items) + '</ul></div>' for g, items in RECYCLINGHOEFE)
    return f"""<section class="abschnitt" id="stadtteile" aria-labelledby="finder-h">
<div class="finder-raster">
<div class="finder" id="finder" data-mail="{F['email']}" data-auf>
<span class="kreisicon">{icon('pin', 40)}</span>
<h2 id="finder-h">Wo wohnen Sie?</h2>
<p>Hinnerk ist in allen 99 Hamburger Stadtteilen unterwegs.</p>
<label for="ort-wahl" class="sr">Ihr Stadtteil</label>
<select id="ort-wahl"><option value="">Stadtteil wählen …</option>{''.join(opts)}</select>
<div class="ergebnis" aria-live="polite"><noscript><p><a href="einsatzgebiet.html">Alle Stadtteile ansehen</a></p></noscript></div>
</div>
<div class="hoefe" data-auf style="--d:100ms">
<p class="eyebrow">Hier landet, was Hinnerk trägt</p>
<h2>Die zwölf Recyclinghöfe</h2>
<div class="hoefe-spalten">{gruppen}</div>
<p class="klein">Quelle: Stadtreinigung Hamburg, INFO 2026</p>
</div>
</div>
<script type="application/json" id="finder-daten">{json.dumps(daten, ensure_ascii=False)}</script>
</section>
"""


def faq_schema(faq):
    return {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q["q"],
            "acceptedAnswer": {"@type": "Answer", "text": q["a"]}} for q in faq]}


def fragen(titel, faq):
    k = "".join(f'<details name="faq"{" open" if i == 0 else ""}><summary>{E(q["q"])}<span class="plus" aria-hidden="true"></span></summary><p>{E(q["a"])}</p></details>'
                for i, q in enumerate(faq[:6]))
    return f"""<section class="abschnitt" id="fragen" aria-labelledby="faq-h">
<div class="fragen"><div><p class="eyebrow">Gut zu wissen</p><h2 id="faq-h" data-auf>{E(titel)}</h2>
<p>Ihre Frage ist nicht dabei? <a href="mailto:{F['email']}">Schreiben Sie uns.</a></p></div>
<div class="faq" data-auf>{k}</div></div>
</section>
"""


def anfrage(seite, ort=""):
    return f"""<section class="abschnitt" id="anfrage" aria-labelledby="anfrage-h">
<div class="anfrage">
<div class="anfrage-links">
<span class="kreisicon">{mascot(64)}</span>
<h2 id="anfrage-h" data-auf>Erst ansehen, dann Festpreis.</h2>
<p data-auf>Schreiben Sie kurz, was geräumt werden soll. Hinnerk meldet sich, besichtigt kostenlos und nennt Ihnen einen festen Preis.</p>
<ul class="haken"><li>{HAKEN}Kostenlose Besichtigung</li><li>{HAKEN}Festpreis vor Beginn</li><li>{HAKEN}Getrennte Entsorgung</li></ul>
<p class="klein">{('Telefon: ' + tel_link() + '<br>') if F['telefon'] else ''}E-Mail: <a href="mailto:{F['email']}">{F['email']}</a></p>
</div>
<form id="anfrage-form" data-mail="{F['email']}" data-seite="{E(seite)}">
<label>Was soll geräumt werden?<select name="was"><option>Ganze Wohnung</option><option>Ganzes Haus</option><option>Haushaltsauflösung</option><option>Nachlass</option><option>Messie-Wohnung</option><option>Büro</option><option>Laden, Lager oder Werkstatt</option><option>Keller</option><option>Dachboden</option><option>Garage oder Schuppen</option><option>Sperrmüll</option></select></label>
<label>Ort oder Stadtteil<input name="ort" value="{E(ort)}" autocomplete="address-level2"></label>
<label>Wunschtermin<input name="termin" placeholder="z. B. Ende November"></label>
<label class="breit">Kurze Beschreibung<textarea name="nachricht" placeholder="Wie viele Zimmer? Welches Stockwerk? Gibt es einen Aufzug?"></textarea></label>
<label>Ihr Name<input name="name" autocomplete="name" required></label>
<label>Telefon für Rückruf<input name="telefon" type="tel" autocomplete="tel"></label>
<button class="knopf breit" type="submit">Anfrage per E-Mail senden</button>
<p class="klein breit">Das Formular öffnet Ihr E-Mail-Programm. Auf dieser Website wird nichts gespeichert.</p>
</form>
</div>
</section>
"""


def fuss():
    leist = "".join(f'<li><a href="{l["slug"]}.html">{E(l["name"])}</a></li>' for l in LEIST)
    bez = "".join(f'<li><a href="einsatzgebiet.html#{slugify(b)}">{E(b)}</a></li>' for b in BEZIRKE)
    rat = "".join(f'<li><a href="{r["slug"]}.html">{E(r["kurz_titel"])}</a></li>' for r in RAT[:5]) + '<li><a href="ratgeber.html">Alle Fragen</a></li>'
    return f"""</main>
<footer class="fuss">
<div class="fuss-oben">
<div class="fuss-marke"><span class="wort">{mascot(34)}HINNERK</span><p>Entrümpelung in Hamburg. Erst kostenlos besichtigen, dann ein fester Preis.</p>
<a class="knopf knopf-gelb" href="{mailto('Anfrage Entrümpelung', ANFRAGE_TEXT)}">Kostenlos anfragen</a></div>
<ul><li class="titel">Leistungen</li><li><a href="./">Entrümpelung Hamburg</a></li>{leist}</ul>
<ul><li class="titel">Bezirke</li>{bez}<li><a href="einsatzgebiet.html">Alle 99 Stadtteile</a></li></ul>
<ul><li class="titel">Ratgeber</li>{rat}</ul>
<ul><li class="titel">Kontakt</li><li>Inh. {E(F['inhaber'])}</li><li>{E(F['strasse'])}</li><li>{F['plz']} {E(F['ort'])}</li>{('<li>' + tel_link() + '</li>') if F['telefon'] else ''}<li><a href="mailto:{F['email']}">{F['email']}</a></li></ul>
</div>
<div class="fuss-unten"><span>© {date.today().year} Hinnerk – Entrümpelung Hamburg{''.join(f' · {E(x["text"])}: <a href="{E(x["url"])}">{E(x["name"])}</a>' for x in SITE.get("partner", []))}</span><span><a href="ueber-hinnerk.html">Über Hinnerk</a> · <a href="kontakt.html">Kontakt</a> · <a href="impressum.html">Impressum</a> · <a href="datenschutz.html">Datenschutz</a></span></div>
</footer>
{handy_leiste()}<script src="assets/site.js" defer></script>
</body>
</html>
"""


def handy_leiste():
    if not F["telefon"]:
        return ""
    return (f'<nav class="handy-leiste" aria-label="Schnellkontakt"><a href="tel:{F["telefon_link"]}">{icon("telefon", 20)}Anrufen</a>'
            f'<a href="kontakt.html#anfrage">{icon("post", 20)}Anfrage</a></nav>\n')


def krumen(items):
    lis, ld = [], []
    for i, (name, url) in enumerate(items, 1):
        lis.append(f'<li><a href="{url}">{E(name)}</a></li>' if url else f'<li aria-current="page">{E(name)}</li>')
        it = {"@type": "ListItem", "position": i, "name": name}
        if url:
            it["item"] = BASE + ("" if url == "./" else url)
        ld.append(it)
    return (f'<nav class="krumen" aria-label="Brotkrumen"><ol>{"".join(lis)}</ol></nav>',
            {"@type": "BreadcrumbList", "itemListElement": ld})


def seitenkasten(titel, knopf):
    return f"""<aside class="kasten" aria-label="Kostenlose Besichtigung">
<p class="kasten-titel">{E(titel)}</p>
<ul class="haken"><li>{HAKEN}Besichtigung kostenlos</li><li>{HAKEN}Festpreis vor Beginn</li><li>{HAKEN}Getrennte Entsorgung</li></ul>
<a class="knopf breit" href="#anfrage">{E(knopf)}</a>
<p class="klein">{('oder anrufen: ' + tel_link() + '<br>') if F['telefon'] else ''}oder per E-Mail: <a href="mailto:{F['email']}">{F['email']}</a></p>
</aside>"""


def write(path, text):
    (OUT / path).write_text(text, encoding="utf-8")


START_FAQ = [
    {"q": "Was kostet eine Entrümpelung in Hamburg?", "a": "Das hängt davon ab, wie viel raus muss, in welchem Stockwerk und wie weit der Weg zum Wagen ist. Darum besichtigt Hinnerk kostenlos und nennt Ihnen danach einen festen Preis."},
    {"q": "Muss ich bei der Räumung dabei sein?", "a": "Nein. Wichtig ist, dass vorher klar ist, was bleiben soll. Den Schlüssel können Sie uns übergeben."},
    {"q": "Wohin kommen die Sachen?", "a": "Sperrmüll, Holz, Metall, Elektrogeräte und andere Abfälle bringen wir getrennt zur Entsorgung, zum Beispiel zu den Recyclinghöfen der Stadtreinigung Hamburg."},
    {"q": "In welchen Stadtteilen ist Hinnerk unterwegs?", "a": "In allen 99 bewohnten Hamburger Stadtteilen. Jeder hat eine eigene Seite mit Infos vor Ort und einem Recyclinghof in der Nähe."},
    {"q": "Haushaltsauflösung oder Wohnungsauflösung – was ist der Unterschied?", "a": "Bei einer Haushaltsauflösung wird ein ganzer Hausstand aufgelöst, oft nach einem Todesfall. Bei einer Wohnungsauflösung geht es darum, die Räume leer zu bekommen, zum Beispiel für die Übergabe."},
    {"q": "Was passiert mit Dokumenten und Fotos?", "a": "Wichtige Papiere nehmen Sie am besten vorher an sich. Was wir beim Räumen finden und wichtig aussieht, legen wir für Sie zur Seite."},
]


def weitere_fragen(ausser=None, titel="Weitere Fragen"):
    k = "".join(f'<li><a href="{r["slug"]}.html"><span>{E(r["frage"])}</span>{PFEIL}</a></li>' for r in RAT if r["slug"] != ausser)
    return f"""<section class="abschnitt" aria-labelledby="wf-h">
<div class="weitere"><div><p class="eyebrow">Ratgeber</p><h2 id="wf-h" data-auf>{E(titel)}</h2></div><ul class="frageliste" data-auf>{k}</ul></div>
</section>
"""


def kontakt_karte(frage):
    tel = (f'<a class="kontakt-zeile" href="tel:{F["telefon_link"]}">{icon("telefon", 24)}<span><b>Telefon</b>{E(F["telefon"])}</span></a>' if F["telefon"] else "")
    return f"""<section class="abschnitt" aria-labelledby="kk-h">
<div class="kontakt-karte">
<div><span class="kreisicon">{mascot(64)}</span><h2 id="kk-h">Fragen Sie Hinnerk direkt</h2>
<p>Sie möchten wissen, was es bei Ihnen kostet? Schreiben Sie uns kurz, was geräumt werden soll. Die Besichtigung ist kostenlos, danach bekommen Sie einen festen Preis.</p></div>
<div class="kontakt-wege">
{tel}<a class="kontakt-zeile" href="{mailto('Frage: ' + frage, ANFRAGE_TEXT)}">{icon("post", 24)}<span><b>E-Mail</b>{F['email']}</span></a>
<a class="kontakt-zeile" href="#anfrage">{icon("kalender", 24)}<span><b>Besichtigung anfragen</b>Formular ausfüllen</span></a>
<div class="kontakt-zeile">{icon("pin", 24)}<span><b>Hinnerk – Entrümpelung Hamburg</b>{E(F['strasse'])}, {F['plz']} {E(F['ort'])}</span></div>
</div>
</div>
</section>
"""


def ratgeberseite(r):
    k, ld = krumen([("Startseite", "./"), (r["kurz_titel"], None)])
    text_kurz = r["kurz"]
    schema = [ld, {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": r["frage"],
              "acceptedAnswer": {"@type": "Answer", "text": text_kurz}}]},
              {"@type": "Article", "headline": r["frage"], "inLanguage": "de", "dateModified": HEUTE,
               "author": {"@type": "Person", "name": F["inhaber"], "jobTitle": "Inhaber", "worksFor": {"@id": BASE + "#firma"}, "url": BASE + "ueber-hinnerk.html"},
               "publisher": {"@id": BASE + "#firma"}, "image": BASE + "img/" + FOTOS[r["foto"]]["datei"]}]
    page = head(r["title"], r["description"], r["slug"] + ".html", schema, preload=r["foto"]) + bar()
    page += held(E(r["frage"]), "Die kurze Antwort, Hamburger Fakten und wie Sie bei Hinnerk zu einem festen Preis kommen.",
                 "Kostenlos besichtigen lassen", "#anfrage", r["foto"], eyebrow="Ratgeber", klein=True)
    secs = "".join(f'<h2>{E(a["h2"])}</h2>{a["html"]}' for a in r["abschnitte"])
    quellen = ("<details class=\"quellen\"><summary>Quellen</summary><ul>" + "".join(f'<li><a href="{E(q["url"])}" rel="nofollow noopener">{E(q["titel"])}</a></li>' for q in r["quellen"]) + "</ul></details>") if r["quellen"] else ""
    page += f"""<section class="abschnitt" aria-label="Antwort">
<div class="lesen"><article class="text">{k}
<p class="autor">Von <a href="ueber-hinnerk.html">{E(F['inhaber'])}</a>, Inhaber von Hinnerk · Stand {date.today().strftime('%m/%Y')}</p>
<div class="antwort"><p class="eyebrow">Kurz gesagt</p><p>{E(text_kurz)}</p><p class="antwort-cta"><a href="#anfrage">Kostenlose Besichtigung anfragen</a>{(' · ' + tel_link()) if F['telefon'] else ''} · <a href="mailto:{F['email']}">{F['email']}</a></p></div>
{secs}
<p class="stand">Stand: {date.today().strftime('%m/%Y')}</p>
{quellen}
</article>{seitenkasten('Kostenlose Besichtigung', 'Besichtigung anfragen')}</div>
</section>
"""
    page += kontakt_karte(r["frage"])
    page += leistungs_reihe("Passende Leistungen")
    page += weitere_fragen(ausser=r["slug"])
    page += anfrage("Ratgeber: " + r["frage"])
    page += fuss()
    write(r["slug"] + ".html", page)


def ueber_uns():
    k, ld = krumen([("Startseite", "./"), ("Über Hinnerk", None)])
    t = "Über Hinnerk – Entrümpelung aus Hamburg-Altona | Hinnerk"
    d = "Wer hinter Hinnerk steht: ein Entrümpelungsbetrieb aus Hamburg-Altona. Unsere Grundsätze: kostenlose Besichtigung, fester Preis, getrennte Entsorgung, Diskretion."
    schema = [ld, {"@type": "AboutPage", "url": BASE + "ueber-hinnerk.html", "name": t, "about": {"@id": BASE + "#firma"}}]
    page = head(t, d, "ueber-hinnerk.html", schema, preload="hero") + bar()
    page += held("Moin, wir sind Hinnerk.", "Ein Entrümpelungsbetrieb aus Hamburg-Altona – für ganz Hamburg.", "Kostenlos besichtigen lassen", "#anfrage", "hero", eyebrow="Über uns", klein=True)
    page += f"""<section class="abschnitt" aria-label="Über Hinnerk">
<div class="lesen"><div class="text">{k}
<h2>Wer hinter Hinnerk steht</h2>
<p>Hinnerk ist ein Entrümpelungsbetrieb aus Hamburg. Inhaber ist {E(F['inhaber'])}, der Betrieb sitzt in der {E(F['strasse'])} in Altona. Von hier aus räumen wir in allen sieben Bezirken und allen 99 Hamburger Stadtteilen.</p>
<h2>Warum „Hinnerk“?</h2>
<p>Hinnerk ist Plattdeutsch für Heinrich – ein alter norddeutscher Name, so hamburgisch wie Speicher und Fleet. Der freundliche Kerl mit der Schiffermütze in unserem Logo ist unser Maskottchen.</p>
<h2>Woran wir uns halten</h2>
<ul>
<li><b>Erst ansehen:</b> Jede Räumung beginnt mit einer kostenlosen Besichtigung.</li>
<li><b>Fester Preis:</b> Sie kennen den Preis, bevor wir anfangen. Was vereinbart ist, gilt.</li>
<li><b>Getrennt entsorgt:</b> Sperrmüll, Holz, Metall und Elektrogeräte gehen getrennt zu den Recyclinghöfen.</li>
<li><b>Diskret und ohne Vorwürfe:</b> Ob Todesfall, Pflegeheim oder Messie-Wohnung – wir reden nicht darüber und urteilen nicht.</li>
<li><b>Sorgfältig:</b> Papiere, Fotos und Dinge, die wichtig aussehen, legen wir für Sie zur Seite.</li>
</ul>
<h2>Was wir machen</h2>
<ul class="chips">{''.join(f'<li><a href="{l["slug"]}.html">{E(l["name"])}</a></li>' for l in LEIST)}</ul>
<h2>Fragen?</h2>
<p>Viele Antworten finden Sie in unserem <a href="ratgeber.html">Ratgeber</a>. Oder schreiben Sie uns direkt: <a href="kontakt.html">Kontakt</a>.</p>
</div>{seitenkasten('Kostenlose Besichtigung', 'Besichtigung anfragen')}</div>
</section>
"""
    page += vorteile() + anfrage("Über Hinnerk") + fuss()
    write("ueber-hinnerk.html", page)


def kontakt():
    k, ld = krumen([("Startseite", "./"), ("Kontakt", None)])
    t = "Kontakt – Entrümpelung Hamburg anfragen | Hinnerk"
    d = "Entrümpelung in Hamburg anfragen: Schreiben Sie Hinnerk per E-Mail oder über das Formular. Kostenlose Besichtigung, danach ein fester Preis."
    schema = [ld, {"@type": "ContactPage", "url": BASE + "kontakt.html", "name": t, "about": {"@id": BASE + "#firma"}}]
    page = head(t, d, "kontakt.html", schema, preload="wohnung") + bar()
    page += held("Kontakt", "Schreiben Sie kurz, was geräumt werden soll. Hinnerk meldet sich, besichtigt kostenlos und nennt einen festen Preis.", "Zum Formular", "#anfrage", "wohnung", eyebrow="Hinnerk anfragen", klein=True)
    page += f'<section class="abschnitt" aria-label="Kontaktwege">{k}</section>'
    page += kontakt_karte("Kontakt").replace('<section class="abschnitt"', '<section class="abschnitt" style="padding-top:24px"', 1)
    page += f"""<section class="abschnitt" aria-label="Gut zu wissen">
<div class="lesen"><div class="text">
<h2>Was in Ihre Anfrage gehört</h2>
<ul><li>Was geräumt werden soll: Wohnung, Haus, Keller, Dachboden, Büro …</li><li>Stadtteil und Stockwerk, gibt es einen Aufzug?</li><li>Ihr Wunschtermin oder der Übergabetermin</li><li>Wie wir Sie erreichen</li></ul>
<p>Ein paar Fotos helfen, sind aber kein Muss. Die Besichtigung vor Ort ist kostenlos und unverbindlich.</p>
<h2>Einsatzgebiet</h2>
<p>Ganz Hamburg: alle sieben Bezirke und <a href="einsatzgebiet.html">alle 99 Stadtteile</a>.</p>
</div></div>
</section>
"""
    page += anfrage("Kontakt") + fuss()
    write("kontakt.html", page)


def ratgeber_uebersicht():
    k, ld = krumen([("Startseite", "./"), ("Ratgeber", None)])
    t = "Ratgeber Entrümpelung Hamburg: Antworten auf häufige Fragen | Hinnerk"
    d = "Kosten, Fristen, besenreine Übergabe, Todesfall, Pflegeheim: Antworten auf die häufigsten Fragen rund um Entrümpelung und Haushaltsauflösung in Hamburg."
    schema = [ld, {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": BASE + r["slug"] + ".html", "name": r["frage"]} for i, r in enumerate(RAT)]}]
    page = head(t, d, "ratgeber.html", schema, preload="kartons") + bar()
    page += held("Fragen rund ums Entrümpeln", "Kurze, ehrliche Antworten – mit Hamburger Fakten. Und wenn Sie es genau wissen wollen: Hinnerk besichtigt kostenlos.",
                 "Kostenlos besichtigen lassen", "#anfrage", "kartons", eyebrow="Ratgeber", klein=True)
    karten = "".join(f'<li><a class="rat-karte" href="{r["slug"]}.html">{foto(r["foto"])}<span><b>{E(r["frage"])}</b><span>{E(r["kurz"][:150].rsplit(" ", 1)[0])} …</span><em>Antwort lesen {PFEIL}</em></span></a></li>' for r in RAT)
    page += f"""<section class="abschnitt" aria-label="Alle Fragen">{k}<ul class="rat-raster">{karten}</ul></section>
"""
    page += anfrage("Ratgeber") + fuss()
    write("ratgeber.html", page)


def llms_txt():
    zeilen = [f"# {F['name']}", "",
              f"> Entrümpelung, Haushaltsauflösung und Wohnungsauflösung in allen 99 Hamburger Stadtteilen. Erst kostenlose Besichtigung, dann ein fester Preis. Entsorgung getrennt über die Recyclinghöfe der Stadtreinigung Hamburg.", "",
              f"Inhaber: {F['inhaber']}. Anschrift: {F['strasse']}, {F['plz']} {F['ort']} (Altona). E-Mail: {F['email']}." + (f" Telefon: {F['telefon']}." if F['telefon'] else ""),
              "Einsatzgebiet: ganz Hamburg, alle 7 Bezirke (Hamburg-Mitte, Altona, Eimsbüttel, Hamburg-Nord, Wandsbek, Bergedorf, Harburg).",
              "Ablauf: Anfrage, kostenlose Besichtigung vor Ort, fester Preis vor Beginn, Räumung am vereinbarten Tag, getrennte Entsorgung.", "",
              "## Leistungen", ""]
    zeilen += [f"- [{l['name']}]({BASE}{l['slug']}.html): {l['kurz']}" for l in LEIST]
    zeilen += ["", "## Ratgeber", ""]
    zeilen += [f"- [{r['frage']}]({BASE}{r['slug']}.html): {r['kurz']}" for r in RAT]
    zeilen += ["", "## Über uns und Kontakt", "", f"- [Über Hinnerk]({BASE}ueber-hinnerk.html)", f"- [Kontakt]({BASE}kontakt.html)"]
    zeilen += ["", "## Stadtteile", "", f"- [Alle 99 Stadtteile mit Recyclinghof in der Nähe]({BASE}einsatzgebiet.html)", ""]
    write("llms.txt", "\n".join(zeilen))


# ---------------------------------------------------------------- Startseite
def start_ratgeber():
    leist = ", ".join(f'<a href="{l["slug"]}.html">{E(l["name"])}</a>' for l in LEIST[:8])
    bez = ", ".join(f'<a href="einsatzgebiet.html#{slugify(b)}">{E(b)}</a>' for b in BEZIRKE)
    return f"""<section class="abschnitt" aria-labelledby="wissen-h">
<div class="lesen"><div class="text wissen">
<p class="eyebrow">Ratgeber</p>
<h2 id="wissen-h">Entrümpelung in Hamburg: das Wichtigste</h2>
<p>Eine Entrümpelung heißt: Räume werden leer gemacht – vom einzelnen Keller bis zum ganzen Haus. Was bleiben soll, wird vorher abgesprochen. Alles andere wird getragen, verladen und getrennt entsorgt.</p>
<details class="mehr"><summary>Mehr anzeigen</summary>
<h3>Was eine Entrümpelung in Hamburg besonders macht</h3>
<p>In vielen Hamburger Altbauten gibt es keinen Aufzug, dann wird alles durchs Treppenhaus getragen. In Vierteln wie Ottensen, Eimsbüttel oder St. Georg ist Parken schwierig, der Weg zum Wagen wird länger. Und entsorgt wird getrennt: Sperrmüll, Holz, Metall und Elektrogeräte gehen zum Beispiel zu den zwölf Recyclinghöfen der Stadtreinigung Hamburg.</p>
<h3>Entrümpelung, Haushaltsauflösung, Wohnungsauflösung</h3>
<p>Entrümpelung ist der Oberbegriff. Bei einer Haushaltsauflösung wird ein ganzer Hausstand aufgelöst, oft nach einem Todesfall oder vor dem Umzug ins Pflegeheim. Bei einer Wohnungsauflösung geht es darum, die Räume leer zu bekommen, etwa für die Übergabe. Mehr dazu im Ratgeber: <a href="unterschied-wohnungsaufloesung-haushaltsaufloesung.html">Wohnungs- oder Haushaltsauflösung?</a></p>
<h3>Was eine Entrümpelung kostet</h3>
<p>Der Preis hängt von der Menge, dem Stockwerk und dem Weg zum Wagen ab. Darum besichtigt Hinnerk kostenlos und nennt danach einen festen Preis. Für ein paar große Möbel ist oft die Sperrmüllabholung der Stadtreinigung günstiger – das sagen wir Ihnen ehrlich. Mehr dazu: <a href="was-kostet-eine-entruempelung-in-hamburg.html">Was kostet eine Entrümpelung in Hamburg?</a></p>
<h3>So läuft die Entrümpelung ab</h3>
<p>Anfrage, kostenlose Besichtigung, fester Preis, Räumung am vereinbarten Tag, getrennte Entsorgung. Papiere, Fotos und Dinge, die wichtig aussehen, legen wir für Sie zur Seite.</p>
<h3>Leistungen und Einsatzgebiet</h3>
<p>Hinnerk übernimmt {leist} und mehr. Wir entrümpeln in allen sieben Bezirken – {bez} – und in allen 99 Hamburger Stadtteilen.</p>
</details>
</div></div>
</section>
"""


def startseite():
    t = "Entrümpelung Hamburg ✓ Haushaltsauflösung ✓ Festpreis | Hinnerk"
    d = "Entrümpelung in Hamburg: Wohnung, Haus, Keller, Nachlass, Messie-Wohnung, Büro. ✓ Kostenlose Besichtigung ✓ Festpreis ✓ In allen 99 Stadtteilen. Hinnerk aus Altona."
    page = head(t, d, "index.html", [faq_schema(START_FAQ), {"@type": "WebSite", "url": BASE, "name": "Hinnerk – Entrümpelung Hamburg", "inLanguage": "de"}], preload="hero")
    page += bar()
    page += held("Entrümpelung in Hamburg", "Wohnung, Haus, Keller oder Nachlass: Hinnerk besichtigt kostenlos und räumt zum festen Preis.",
                 "Kostenlos besichtigen lassen", "#anfrage", "hero", eyebrow="Platz schaffen")
    page += zwei_karten([("nachlassaufloesung-hamburg.html", "nachlass", "Sorgfältig und mit Ruhe", "Nachlass auflösen"),
                         ("dachboden-entruempeln-hamburg.html", "speicher", "Endlich wieder Platz", "Dachboden & Speicher")])
    page += vorteile()
    page += leistungs_reihe()
    page += auswahl()
    page += dinge()
    page += ablauf("In fünf Schritten leer", "Vom ersten Satz bis zum leeren Raum. Den Preis kennen Sie, bevor jemand eine Kiste anfasst.")
    page += vergleich()
    page += finder()
    page += fragen("Häufige Fragen", START_FAQ)
    page += weitere_fragen(titel="Mehr Antworten")
    page += start_ratgeber()
    page += anfrage("Startseite")
    page += fuss()
    write("index.html", page)


# ---------------------------------------------------------------- Leistungsseiten
def leistungsseite(l):
    k, ld = krumen([("Startseite", "./"), (l["name"], None)])
    schema = [ld, faq_schema(l["faq"]), {"@type": "Service", "name": l["h1"], "serviceType": l["name"],
              "provider": {"@id": BASE + "#firma"}, "areaServed": {"@type": "City", "name": "Hamburg"}}]
    bk = L_FOTO[l["slug"]]
    page = head(l["title"], l["description"], l["slug"] + ".html", schema, preload=bk) + bar()
    page += held(E(l["name"]) + " in Hamburg", l["lead"], "Kostenlos besichtigen lassen", "#anfrage", bk, eyebrow="Hinnerk räumt", klein=True)
    secs = "".join(f'<h2>{E(s["h2"])}</h2>{s["html"]}' for s in l["sections"])
    page += f"""<section class="abschnitt" aria-label="{E(l['name'])}">
<div class="lesen"><div class="text">{k}{secs}</div>{seitenkasten(l['name'] + ' in Hamburg', 'Kostenlos besichtigen lassen')}</div>
</section>
"""
    page += vorteile()
    page += ablauf("So läuft’s", "Erst kostenlos besichtigen, dann ein fester Preis – auch bei einer " + l["name"] + ".")
    page += leistungs_reihe("Auch das räumt Hinnerk", ausser=l["slug"])
    page += fragen("Häufige Fragen", l["faq"])
    page += weitere_fragen()
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
    faq.append({"q": f"Wie läuft eine Entrümpelung in {n} ab?",
                "a": "Sie stellen eine Anfrage, wir besichtigen kostenlos und nennen einen festen Preis. Am vereinbarten Tag räumen wir und bringen alles getrennt zur Entsorgung."})
    schema = [ld, faq_schema(faq), {"@type": "Service", "name": f"Entrümpelung {ort_hh}", "serviceType": "Entrümpelung",
              "provider": {"@id": BASE + "#firma"}, "areaServed": {"@type": "Place", "name": ort_hh,
              "containedInPlace": {"@type": "City", "name": "Hamburg"}}}]
    bk = pick(n, ORT_FOTOS)
    page = head(title, desc, o["slug"] + ".html", schema, preload=bk,
                robots="index,follow" if (ALLE_ORTE_INDEXIEREN or n in KERN_ORTE) else "noindex,follow") + bar()
    v = {"o": n, "b": b}
    page += held(f"Entrümpelung {E(n)}", pick(n + "lead", LEAD_VARIANTEN).format(**v),
                 f"Besichtigung in {n}" if len(n) <= 16 else "Kostenlos besichtigen", "#anfrage", bk, eyebrow=f"Bezirk {b}", klein=True)
    quart = o.get("quartiere") or []
    quart_satz = ""
    if quart:
        liste = ", ".join(quart[:-1]) + " und " + quart[-1] if len(quart) > 1 else quart[0]
        quart_satz = f"<p>Zu {E(n)} gehören unter anderem {E(liste)}. Egal in welchem Teil Sie wohnen: Hinnerk kommt zu Ihnen.</p>"
    kurz = (f"<h2>{E(pick(n + 'h2b', H2_KURZ).format(**v))}</h2><p>{E(o['geschichte'])}</p>" if o.get("geschichte") else "")
    nach = "".join(f'<li><a href="{SLUG_BY_NAME[x]}.html">{E(x)}</a></li>' if x in SLUG_BY_NAME else f"<li><span>{E(x)}</span></li>" for x in o.get("nachbarn", []))
    bez = "".join(f'<li><a href="{x["slug"]}.html">{E(x["name"])}</a></li>' for x in alle_im_bezirk if x["slug"] != o["slug"])
    leist = "".join(f'<li><a href="{l["slug"]}.html">{E(l["name"])}</a></li>' for l in LEIST)
    quellen = "".join(f'<li><a href="{E(q["url"])}" rel="nofollow noopener">{E(q["titel"])}</a></li>' for q in o.get("quellen", []))
    quellen += '<li><a href="https://files.stadtreinigung.hamburg/SRH_25_028_Info_Broschuere_2026_Web.pdf" rel="nofollow noopener">Stadtreinigung Hamburg: INFO-Broschüre 2026</a></li>'
    page += f"""<section class="abschnitt" aria-label="Entrümpelung in {E(n)}">
<div class="lesen"><div class="text">{k}
<h2>{E(pick(n + 'h2a', H2_WOHNEN).format(**v))}</h2>
<p>{E(o['bebauung'])}</p>
<p>{E(o['raeumung'])}</p>
{quart_satz}
{kurz}
<div class="hof">{icon('kreis', 34)}<div><b>Recyclinghof {E(rh['ort'])}</b><p>Ein Recyclinghof der Stadtreinigung Hamburg in der Nähe von {E(n)} ist <b>{E(rh['ort'])}, {E(rh['adresse'])}</b>. Dort werden Sperrmüll, Holz, Metall und Elektrogeräte getrennt angenommen. Wenn Hinnerk für Sie räumt, kümmern wir uns um den Transport.</p></div></div>
<h2>Was Hinnerk in {E(n)} räumt</h2>
<ul class="chips">{leist}</ul>
</div>{seitenkasten('Entrümpelung in ' + n, 'Besichtigung anfragen')}</div>
</section>
"""
    page += ablauf(f"Entrümpelung in {n}", "Fünf Schritte, ein fester Preis. Sie wissen vorher, was es kostet.")
    page += fragen(f"Fragen zu {n}", faq)
    page += f"""<section class="abschnitt" aria-label="Umgebung">
<div class="umgebung">
<div><h2>In der Nähe</h2><ul class="chips">{nach}</ul></div>
<div><h2>Bezirk {E(b)}</h2><ul class="chips">{bez}</ul></div>
<details class="quellen"><summary>Quellen</summary><ul>{quellen}</ul></details>
</div>
</section>
"""
    page += anfrage(n, n)
    page += fuss()
    write(o["slug"] + ".html", page)


def einsatzgebiet():
    k, ld = krumen([("Startseite", "./"), ("Stadtteile", None)])
    t = "Entrümpelung in allen 99 Hamburger Stadtteilen | Hinnerk"
    d = "Hinnerk entrümpelt in allen 7 Hamburger Bezirken. Übersicht über 99 Stadtteile mit eigener Seite und einem Recyclinghof in der Nähe."
    page = head(t, d, "einsatzgebiet.html", [ld], preload="transporter") + bar()
    page += held("99 Stadtteile, 7 Bezirke", "Hinnerk ist in ganz Hamburg unterwegs. Wählen Sie Ihren Stadtteil.", "Stadtteil wählen", "#liste", "transporter", eyebrow="Einsatzgebiet", klein=True)
    rows = []
    for b in BEZIRKE:
        li = "".join(f'<li><a href="{o["slug"]}.html">{E(o["name"])}</a></li>' for o in sorted([o for o in ORTE if o["bezirk"] == b], key=lambda x: x["name"]))
        rows.append(f'<div class="bezirk" id="{slugify(b)}"><h2>{E(b)}</h2><ul class="chips">{li}</ul></div>')
    page += f"""<section class="abschnitt" id="liste" aria-label="Alle Stadtteile">
{k}<div class="bezirke">{''.join(rows)}</div>
</section>
"""
    page += finder() + anfrage("Einsatzgebiet") + fuss()
    write("einsatzgebiet.html", page)


def rechtliches():
    tel = f"Telefon: {E(F['telefon'])}<br>" if F["telefon"] else ""

    def seite(path, titel, inhalt):
        p = head(f"{titel} | Hinnerk", f"{titel} von Hinnerk – Entrümpelung Hamburg.", path, robots="noindex,follow") + bar()
        p += f'<section class="abschnitt"><div class="lesen"><div class="text"><h1 class="seitentitel">{titel}</h1>{inhalt}</div></div></section>'
        write(path, p + fuss())
    seite("impressum.html", "Impressum", f"""<h2>Angaben gemäß § 5 DDG</h2>
<p>Hinnerk – Entrümpelung Hamburg<br>Inhaber: {E(F['inhaber'])}<br>{E(F['strasse'])}<br>{F['plz']} {E(F['ort'])}</p>
<h2>Kontakt</h2><p>{tel}E-Mail: <a href="mailto:{F['email']}">{F['email']}</a></p>
<h2>Verbraucherstreitbeilegung</h2><p>Wir sind nicht bereit und nicht verpflichtet, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.</p>""")
    seite("datenschutz.html", "Datenschutz", f"""<h2>1. Verantwortlicher</h2>
<p>Hinnerk – Entrümpelung Hamburg, Inhaber {E(F['inhaber'])}, {E(F['strasse'])}, {F['plz']} {E(F['ort'])}<br>{tel}E-Mail: <a href="mailto:{F['email']}">{F['email']}</a></p>
<h2>2. Hosting</h2><p>Diese Website wird bei GitHub Pages gehostet, einem Dienst der GitHub Inc., 88 Colin P. Kelly Jr. Street, San Francisco, CA 94107, USA. Beim Aufruf der Seite verarbeitet GitHub technisch notwendige Daten wie Ihre IP-Adresse, Datum und Uhrzeit des Abrufs sowie Browser-Informationen, um die Seite auszuliefern und vor Angriffen zu schützen. Rechtsgrundlage ist unser berechtigtes Interesse an einer sicheren und zuverlässigen Bereitstellung der Website (Art. 6 Abs. 1 lit. f DSGVO). GitHub ist eine Tochter der Microsoft Corporation; Microsoft ist nach dem EU-US Data Privacy Framework zertifiziert, auf dessen Grundlage Daten in die USA übermittelt werden dürfen.</p>
<h2>3. Schriftarten und Bilder</h2><p>Schriftarten und Bilder dieser Website sind lokal eingebunden. Beim Aufruf werden keine Verbindungen zu Google oder anderen Anbietern aufgebaut.</p>
<h2>4. Anfrageformular, E-Mail und Telefon</h2><p>Das Anfrageformular speichert keine Daten auf dieser Website, sondern öffnet Ihr E-Mail-Programm mit einer vorbereiteten Nachricht. Wenn Sie uns per E-Mail oder Telefon kontaktieren, verarbeiten wir Ihre Angaben (z. B. Name, Telefonnummer, Beschreibung des Auftrags, Wunschtermin), um Ihre Anfrage zu bearbeiten und ein Angebot zu erstellen. Rechtsgrundlage ist die Anbahnung oder Erfüllung eines Vertrags (Art. 6 Abs. 1 lit. b DSGVO). Wir löschen die Daten, wenn sie nicht mehr benötigt werden und keine gesetzlichen Aufbewahrungspflichten bestehen.</p>
<h2>5. Cookies</h2><p>Diese Website setzt keine Cookies und verwendet keine Analyse- oder Werbedienste.</p>
<h2>6. Ihre Rechte</h2><p>Sie haben das Recht auf Auskunft, Berichtigung, Löschung, Einschränkung der Verarbeitung, Datenübertragbarkeit und Widerspruch. Außerdem können Sie sich bei einer Datenschutz-Aufsichtsbehörde beschweren, in Hamburg beim Hamburgischen Beauftragten für Datenschutz und Informationsfreiheit.</p>""")
    p = head("Seite nicht gefunden | Hinnerk", "Diese Seite gibt es nicht.", "404.html", robots="noindex,follow") + bar()
    p += held("Leer geräumt.", "Diese Seite gibt es nicht (mehr). Zurück zur Startseite oder zu allen Stadtteilen.", "Zur Startseite", "./", "hero", klein=True)
    p += fuss()
    for a, b in (('href="assets/', 'href="/assets/'), ('src="assets/', 'src="/assets/'), ('src="img/', 'src="/img/'),
                 ('href="img/', 'href="/img/'), ('href="favicon', 'href="/favicon'), ('href="logo', 'href="/logo'),
                 ('href="./', 'href="/'), ('href="einsatzgebiet', 'href="/einsatzgebiet'), ('href="impressum', 'href="/impressum'),
                 ('href="datenschutz', 'href="/datenschutz')):
        p = p.replace(a, b)
    for x in [l["slug"] for l in LEIST] + [r["slug"] for r in RAT] + ["ratgeber", "ueber-hinnerk", "kontakt"]:
        p = p.replace(f'href="{x}', f'href="/{x}')
    write("404.html", p)


def sitemap(pfade):
    urls = "".join(f"<url><loc>{BASE}{'' if p == 'index.html' else p}</loc><lastmod>{HEUTE}</lastmod></url>" for p in pfade)
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    bots = ["Googlebot", "Bingbot", "GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "Claude-User",
            "PerplexityBot", "Perplexity-User", "Google-Extended", "Applebot", "Applebot-Extended", "DuckAssistBot"]
    r = "".join(f"User-agent: {b}\nAllow: /\n\n" for b in bots)
    write("robots.txt", r + f"User-agent: *\nAllow: /\n\nSitemap: {BASE}sitemap.xml\n")
    write("CNAME", "hinnerk-entruempelung.de\n")
    key = (SRC / "indexnow.key").read_text().strip()
    write(f"{key}.txt", key)
    for g in SRC.glob("google*.html"):
        write(g.name, g.read_text())
    if (SRC / "BingSiteAuth.xml").exists():
        write("BingSiteAuth.xml", (SRC / "BingSiteAuth.xml").read_text())


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
    for r in RAT:
        ratgeberseite(r)
    ratgeber_uebersicht()
    ueber_uns()
    kontakt()
    llms_txt()
    for o in ORTE:
        ortsseite(o, [x for x in ORTE if x["bezirk"] == o["bezirk"]])
    einsatzgebiet()
    rechtliches()
    favicon()
    pfade = ["index.html"] + [l["slug"] + ".html" for l in LEIST] + ["ratgeber.html", "ueber-hinnerk.html", "kontakt.html"] + [r["slug"] + ".html" for r in RAT] + ["einsatzgebiet.html"] + [o["slug"] + ".html" for o in ORTE if ALLE_ORTE_INDEXIEREN or o["name"] in KERN_ORTE]
    sitemap(pfade)
    print(f"Fertig: {len(pfade)} Seiten in der Sitemap, Ausgabe: {OUT}")
