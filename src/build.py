#!/usr/bin/env python3
"""Baut die statische Website von Hinnerk – Entrümpelung Hamburg.

Aufruf:  python3 src/build.py            -> schreibt ins Hauptverzeichnis (= live über GitHub Pages)
         python3 src/build.py --out DIR  -> schreibt in einen anderen Ordner (Vorschau)
Daten:   src/site.json (Firma), src/stadtteile.json (Ortsseiten), src/leistungen.json (Leistungsseiten)
"""
import json, html, re, sys, hashlib, shutil
from pathlib import Path
from datetime import date

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
_KURZ = {l["slug"]: l["kurz"] for l in SITE["leistungen"]}
for _l in LEIST:
    _l["kurz"] = _KURZ[_l["slug"]]
HEUTE = date.today().isoformat()
E = html.escape


def slugify(s):
    s = s.lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss"), (".", ""), ("–", "-")):
        s = s.replace(a, b)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def ortslug(name):
    return "entruempelung-hamburg-" + slugify(name.replace("Hamburg-", ""))


for o in ORTE:
    o["slug"] = ortslug(o["name"])
SLUG_BY_NAME = {o["name"]: o["slug"] for o in ORTE}


def pick(key, options):
    """Wählt stabil eine Variante pro Seite (gleiche Seite = gleiche Variante)."""
    h = int(hashlib.md5(key.encode()).hexdigest(), 16)
    return options[h % len(options)]


def mascot(size=46, label=None):
    a = f'role="img" aria-label="{E(label)}"' if label else 'aria-hidden="true"'
    return (f'<svg viewBox="0 0 120 120" width="{size}" height="{size}" {a}>'
            '<circle cx="60" cy="70" r="36" fill="#FBF6EA" stroke="#1F2A44" stroke-width="5"/>'
            '<path d="M22 56 Q24 26 60 24 Q96 26 98 56 Z" fill="#1F2A44"/>'
            '<rect x="21" y="48" width="78" height="9" fill="#121A2E"/>'
            '<path d="M18 57 Q60 69 102 57 L102 62 Q60 76 18 62 Z" fill="#121A2E"/>'
            '<circle cx="60" cy="37" r="5" fill="#F2C230"/>'
            '<circle cx="47" cy="81" r="4" fill="#1F2A44"/><circle cx="73" cy="81" r="4" fill="#1F2A44"/>'
            '<path d="M46 92 Q60 103 74 92" fill="none" stroke="#1F2A44" stroke-width="5" stroke-linecap="round"/>'
            '</svg>')


def firma_schema():
    s = {
        "@type": "HomeAndConstructionBusiness",
        "@id": BASE + "#firma",
        "name": F["name"],
        "url": BASE,
        "email": F["email"],
        "logo": BASE + "logo.png",
        "image": BASE + "logo.png",
        "description": F["beschreibung"],
        "address": {"@type": "PostalAddress", "streetAddress": F["strasse"], "postalCode": F["plz"],
                    "addressLocality": F["ort"], "addressCountry": "DE"},
        "areaServed": [{"@type": "City", "name": "Hamburg"}],
    }
    if F["telefon"]:
        s["telephone"] = F["telefon_link"]
    return s


def head(title, desc, path, schema=None, robots="index,follow"):
    graph = [firma_schema()] + (schema or [])
    ld = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False)
    canon = BASE + ("" if path == "index.html" else path)
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
<meta name="theme-color" content="#1F2A44">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="logo.png">
<link rel="preload" href="assets/fonts/zilla-slab-latin-700-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="assets/site.css">
<script type="application/ld+json">{ld}</script>
</head>
<body>
<a class="skip" href="#inhalt">Zum Inhalt springen</a>
"""


def kopf():
    return f"""<header class="kopf">
<div class="wrap">
<a class="marke" href="./" aria-label="Hinnerk – Entrümpelung Hamburg, zur Startseite">{mascot(46)}<span><b>Hinnerk</b><small>Entrümpelung Hamburg</small></span></a>
<nav class="nav" aria-label="Hauptmenü">
<a href="./#leistungen">Leistungen</a>
<a href="./#ablauf">Ablauf</a>
<a href="einsatzgebiet.html">Einsatzgebiet</a>
<a href="./#fragen">Fragen</a>
<a class="btn btn-gelb" href="#anfrage">Anfrage stellen</a>
</nav>
</div>
</header>
<main id="inhalt">
"""


def kontakt_knoepfe(klasse_haupt="btn btn-gelb", klasse_neben="btn btn-hell", wa_text="Hallo Hinnerk, ich möchte eine Entrümpelung anfragen."):
    if F["telefon"]:
        nr = F["telefon_link"].lstrip("+")
        from urllib.parse import quote
        return (f'<a class="{klasse_haupt}" href="tel:{F["telefon_link"]}">Anrufen: {E(F["telefon"])}</a>'
                f'<a class="{klasse_neben}" href="https://wa.me/{nr}?text={quote(wa_text)}">WhatsApp</a>')
    return (f'<a class="{klasse_haupt}" href="#anfrage">Kostenlos anfragen</a>'
            f'<a class="{klasse_neben}" href="mailto:{F["email"]}">E-Mail schreiben</a>')


def anfrage(seite, ort=""):
    return f"""<section class="band band-blau" id="anfrage" aria-labelledby="anfrage-h">
<div class="wrap anfrage">
<div>
<h2 id="anfrage-h">Anfrage an Hinnerk</h2>
<p>Schreiben Sie kurz, was geräumt werden soll. Wir melden uns und vereinbaren einen Termin für die kostenlose Besichtigung. Danach bekommen Sie einen festen Preis.</p>
<p>E-Mail: <a href="mailto:{F['email']}">{F['email']}</a></p>
<p class="klein">Das Formular öffnet Ihr E-Mail-Programm mit einer fertigen Nachricht. Es werden keine Daten auf dieser Website gespeichert.</p>
</div>
<form id="anfrage-form" data-mail="{F['email']}" data-seite="{E(seite)}">
<label>Was soll geräumt werden?
<select name="was"><option>Ganze Wohnung</option><option>Ganzes Haus</option><option>Haushaltsauflösung</option><option>Keller</option><option>Dachboden</option><option>Garage</option><option>Etwas anderes</option></select>
</label>
<label>Ort oder Stadtteil<input name="ort" value="{E(ort)}" autocomplete="address-level2"></label>
<label>Wunschtermin<input name="termin" placeholder="z. B. Ende November"></label>
<label>Kurze Beschreibung<textarea name="nachricht" placeholder="Wie viele Zimmer? Welches Stockwerk? Gibt es einen Aufzug?"></textarea></label>
<label>Ihr Name<input name="name" autocomplete="name" required></label>
<label>Telefon für Rückruf<input name="telefon" type="tel" autocomplete="tel"></label>
<button class="btn btn-gelb" type="submit">Anfrage per E-Mail senden</button>
</form>
</div>
</section>
"""


def fuss():
    leist = "".join(f'<li><a href="{l["slug"]}.html">{E(l["name"])} Hamburg</a></li>' for l in LEIST)
    bez = []
    for b in ["Hamburg-Mitte", "Altona", "Eimsbüttel", "Hamburg-Nord", "Wandsbek", "Bergedorf", "Harburg"]:
        bez.append(f'<li><a href="einsatzgebiet.html#{slugify(b)}">Bezirk {E(b)}</a></li>')
    tel = f'<li>Telefon: <a href="tel:{F["telefon_link"]}">{E(F["telefon"])}</a></li>' if F["telefon"] else ""
    leiste = (f'<a class="btn btn-gelb" href="tel:{F["telefon_link"]}">Anrufen</a><a class="btn btn-dunkel" href="#anfrage" style="border-color:#F2C230">Anfrage</a>'
              if F["telefon"] else
              f'<a class="btn btn-gelb" href="#anfrage">Anfrage</a><a class="btn btn-dunkel" href="mailto:{F["email"]}" style="border-color:#F2C230">E-Mail</a>')
    return f"""</main>
<footer class="fuss">
<div class="wrap">
<div>
<h3>Hinnerk – Entrümpelung Hamburg</h3>
<ul>
<li>Inh. {E(F['inhaber'])}</li>
<li>{E(F['strasse'])}, {F['plz']} {E(F['ort'])}</li>
{tel}<li>E-Mail: <a href="mailto:{F['email']}">{F['email']}</a></li>
</ul>
</div>
<div>
<h3>Leistungen</h3>
<ul><li><a href="./">Entrümpelung Hamburg</a></li>{leist}</ul>
</div>
<div>
<h3>Einsatzgebiet</h3>
<ul>{''.join(bez)}<li><a href="einsatzgebiet.html">Alle Stadtteile</a></li></ul>
<p style="margin-top:18px"><a href="impressum.html">Impressum</a> · <a href="datenschutz.html">Datenschutz</a></p>
</div>
</div>
</footer>
<nav class="leiste" aria-label="Schnellkontakt">{leiste}</nav>
<script src="assets/site.js" defer></script>
</body>
</html>
"""


def krumen(items):
    lis = []
    ld = []
    for i, (name, url) in enumerate(items, 1):
        lis.append(f'<li><a href="{url}">{E(name)}</a></li>' if url else f'<li aria-current="page">{E(name)}</li>')
        ld.append({"@type": "ListItem", "position": i, "name": name, **({"item": BASE + ("" if url == "./" else url)} if url else {})})
    return (f'<nav class="krumen wrap" aria-label="Brotkrumen"><ol>{"".join(lis)}</ol></nav>',
            {"@type": "BreadcrumbList", "itemListElement": ld})


def faq_html(faq):
    out = ['<div class="faq">']
    for q in faq:
        out.append(f'<details><summary>{E(q["q"])}</summary><p>{E(q["a"])}</p></details>')
    out.append("</div>")
    return "\n".join(out)


def faq_schema(faq):
    return {"@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q["q"], "acceptedAnswer": {"@type": "Answer", "text": q["a"]}} for q in faq]}


def quellen_html(qs):
    if not qs:
        return ""
    li = "".join(f'<li><a href="{E(q["url"])}" rel="nofollow noopener">{E(q["titel"])}</a></li>' for q in qs)
    return f'<div class="quellen"><h3 style="font-size:18px">Quellen</h3><ul>{li}</ul></div>'


def write(path, text):
    (OUT / path).write_text(text, encoding="utf-8")


ABLAUF_VARIANTEN = [
    [("Anfragen", "Sie schreiben uns, was geräumt werden soll – am einfachsten über das Formular unten."),
     ("Besichtigen", "Wir schauen uns alles vor Ort an. Die Besichtigung ist kostenlos und unverbindlich."),
     ("Festpreis und Räumung", "Sie bekommen einen festen Preis. Am vereinbarten Tag räumen wir und bringen alles zur Entsorgung.")],
    [("Kurz melden", "Ein paar Sätze genügen: Was soll raus, wie viele Zimmer, welches Stockwerk?"),
     ("Gemeinsam ansehen", "Wir kommen vorbei und sehen uns Räume, Treppen und Wege an – kostenlos."),
     ("Räumen zum Festpreis", "Sie erhalten einen festen Preis. Am Räumungstag tragen wir alles raus und entsorgen es getrennt.")],
    [("Anfrage stellen", "Über das Formular, per E-Mail oder telefonisch – sagen Sie uns, worum es geht."),
     ("Vor Ort besichtigen", "Wir klären mit Ihnen, was bleibt und was weg kann. Das kostet nichts."),
     ("Termin und Räumung", "Mit dem festen Preis vereinbaren wir einen Termin. Danach ist der Raum leer.")],
]
ABLAUF = ABLAUF_VARIANTEN[0]


def ablauf_html(titel="So läuft es ab", key=None):
    schritte = pick(key, ABLAUF_VARIANTEN) if key else ABLAUF
    li = "".join(f"<li><b>{E(t)}</b>{E(x)}</li>" for t, x in schritte)
    return f"""<section class="band band-blau" id="ablauf" aria-labelledby="ablauf-h">
<div class="wrap">
<h2 id="ablauf-h">{E(titel)}</h2>
<ol class="schritte">{li}</ol>
</div>
</section>
"""


SRH_QUELLE = {"titel": "Stadtreinigung Hamburg: INFO-Broschüre 2026 (Recyclinghöfe, Sperrmüll)",
              "url": "https://files.stadtreinigung.hamburg/SRH_25_028_Info_Broschuere_2026_Web.pdf"}

# ---------------------------------------------------------------- Startseite
START_FAQ = [
    {"q": "Was kostet eine Entrümpelung in Hamburg?",
     "a": "Das hängt vor allem davon ab, wie viel geräumt werden muss, in welchem Stockwerk und wie weit der Weg bis zum Wagen ist. Deshalb schauen wir uns alles kostenlos an und nennen Ihnen danach einen festen Preis."},
    {"q": "Muss ich bei der Räumung dabei sein?",
     "a": "Nein, nicht unbedingt. Wichtig ist, dass vorher klar ist, was bleiben soll und was weg kann. Den Schlüssel können Sie uns übergeben."},
    {"q": "Wohin kommen die Sachen?",
     "a": "Sperrmüll, Holz, Metall, Elektrogeräte und andere Abfälle bringen wir getrennt zur Entsorgung, zum Beispiel zu den Recyclinghöfen der Stadtreinigung Hamburg."},
    {"q": "In welchen Stadtteilen sind Sie unterwegs?",
     "a": "In ganz Hamburg. Für jeden Stadtteil gibt es eine eigene Seite mit Infos vor Ort, zum Beispiel zu Recyclinghöfen in der Nähe."},
    {"q": "Was ist der Unterschied zwischen Haushaltsauflösung und Wohnungsauflösung?",
     "a": "Bei einer Haushaltsauflösung wird der ganze Hausstand aufgelöst, oft nach einem Todesfall oder vor einem Umzug ins Heim. Bei einer Wohnungsauflösung geht es darum, die Räume leer zu bekommen, zum Beispiel für die Übergabe an den Vermieter."},
]


def startseite():
    leist = "".join(f'<div class="karte"><h3><a href="{l["slug"]}.html">{E(l["name"])}</a></h3><p>{E(l["kurz"])}</p></div>' for l in LEIST)
    bez_pills = "".join(f'<li><a href="einsatzgebiet.html#{slugify(b)}">{E(b)}</a></li>' for b in
                        ["Hamburg-Mitte", "Altona", "Eimsbüttel", "Hamburg-Nord", "Wandsbek", "Bergedorf", "Harburg"])
    haken = "".join(f"<li>{E(v)}</li>" for v in SITE["versprechen"])
    t = "Entrümpelung Hamburg ✓ Haushaltsauflösung ✓ Festpreis | Hinnerk"
    d = "Entrümpelung in Hamburg: Wohnung, Haus, Keller und Haushaltsauflösung. ✓ Kostenlose Besichtigung ✓ Festpreis ✓ In allen 7 Bezirken. Hinnerk aus Altona."
    page = head(t, d, "index.html", [faq_schema(START_FAQ),
                                       {"@type": "WebSite", "url": BASE, "name": "Hinnerk – Entrümpelung Hamburg", "inLanguage": "de"}])
    page += kopf()
    page += f"""<section class="hero">
<div class="wrap">
<div>
<p class="ober">Entrümpelung · Hamburg &amp; Umgebung</p>
<h1>Entrümpelung in Hamburg – Hinnerk packt an.</h1>
<p class="lead">Wohnung, Haus, Keller oder ein ganzer Haushalt: Hinnerk räumt in allen Hamburger Stadtteilen leer und bringt alles ordentlich zur Entsorgung.</p>
<ul class="haken">{haken}</ul>
<div class="knoepfe">{kontakt_knoepfe()}</div>
</div>
<div class="hero-bild">{mascot(240, "Hinnerk, das Maskottchen mit Schiffermütze")}<p>Moin, ich bin Hinnerk.</p><small>Ihr Ansprechpartner für Entrümpelung in Hamburg.</small></div>
</div>
</section>
<section class="band band-weiss" id="leistungen" aria-labelledby="leist-h">
<div class="wrap">
<h2 id="leist-h">Leistungen rund um die Entrümpelung</h2>
<div class="raster">{leist}</div>
</div>
</section>
{ablauf_html("So läuft eine Entrümpelung mit Hinnerk ab")}
<section class="band" aria-labelledby="ratgeber-h">
<div class="wrap text">
<h2 id="ratgeber-h">Entrümpelung in Hamburg: Das sollten Sie wissen</h2>
<p>Eine Entrümpelung ist mehr als „alles raus“. Vor dem Termin wird geklärt, was bleiben soll: Papiere, Fotos, Erinnerungsstücke und Dinge, die verkauft oder verschenkt werden sollen. Alles andere räumen wir, tragen es zum Wagen und bringen es getrennt zur Entsorgung.</p>
<h3>Altbau, Hochhaus oder Einfamilienhaus</h3>
<p>Hamburg ist sehr unterschiedlich gebaut. In Gründerzeit-Vierteln wie Eimsbüttel oder Ottensen geht es oft über enge Treppenhäuser ohne Aufzug. In Großsiedlungen gibt es Aufzüge, dafür lange Wege. In Stadtteilen mit vielen Einfamilienhäusern kommen Keller, Dachboden, Garage und Garten dazu. Das alles fließt in den Festpreis ein, deshalb besichtigen wir vorher.</p>
<h3>Entsorgung in Hamburg</h3>
<p>Die Stadtreinigung Hamburg betreibt zwölf Recyclinghöfe. Welcher in Ihrer Nähe liegt, steht auf der Seite Ihres Stadtteils. Sperrmüll, Elektrogeräte, Holz und Metall werden dort getrennt angenommen.</p>
</div>
</section>
<section class="band band-weiss" aria-labelledby="gebiet-h">
<div class="wrap">
<h2 id="gebiet-h">Entrümpelung in allen Hamburger Bezirken</h2>
<p>Für jeden der {len(ORTE)} Stadtteile gibt es eine eigene Seite mit Infos vor Ort.</p>
<ul class="pillen">{bez_pills}<li><a href="einsatzgebiet.html">Alle Stadtteile ansehen</a></li></ul>
</div>
</section>
<section class="band" id="fragen" aria-labelledby="fragen-h">
<div class="wrap text">
<h2 id="fragen-h">Häufige Fragen</h2>
{faq_html(START_FAQ)}
</div>
</section>
{anfrage("Startseite")}
"""
    page += fuss()
    write("index.html", page)


# ---------------------------------------------------------------- Leistungsseiten
def leistungsseite(l):
    k, ld = krumen([("Startseite", "./"), (l["name"], None)])
    schema = [ld, faq_schema(l["faq"]), {"@type": "Service", "name": l["h1"], "serviceType": l["name"],
              "provider": {"@id": BASE + "#firma"}, "areaServed": {"@type": "City", "name": "Hamburg"}}]
    page = head(l["title"], l["description"], l["slug"] + ".html", schema)
    page += kopf() + k
    secs = "".join(f'<h2>{E(s["h2"])}</h2>{s["html"]}' for s in l["sections"])
    page += f"""<section class="hero"><div class="wrap">
<div><p class="ober">{E(l['name'])} · Hamburg</p><h1>{E(l['h1'])}</h1><p class="lead">{E(l['lead'])}</p>
<div class="knoepfe">{kontakt_knoepfe()}</div></div>
<div class="hero-bild">{mascot(200)}<p>{E(l['name'])}</p><small>In allen Hamburger Stadtteilen</small></div>
</div></section>
<section class="band band-weiss"><div class="wrap text">{secs}</div></section>
{ablauf_html()}
<section class="band"><div class="wrap text"><h2>Häufige Fragen: {E(l['name'])}</h2>{faq_html(l['faq'])}</div></section>
{anfrage(l['name'])}
"""
    page += fuss()
    write(l["slug"] + ".html", page)


# ---------------------------------------------------------------- Ortsseiten
LEAD_VARIANTEN = [
    "Wohnung, Haus oder Keller in {o} soll leer werden? Hinnerk räumt in {o} und im ganzen Bezirk {b} – nach kostenloser Besichtigung zum Festpreis.",
    "Haushaltsauflösung oder Entrümpelung in {o}: Hinnerk kommt vorbei, schaut sich alles an und nennt Ihnen einen festen Preis.",
    "Ob Keller, Dachboden oder ganze Wohnung – in {o} ist Hinnerk für Ihre Entrümpelung da. Erst kostenlos besichtigen, dann Festpreis.",
    "Sie brauchen in {o} Platz? Hinnerk entrümpelt Wohnungen, Häuser und Keller im Bezirk {b} und bringt alles zur Entsorgung.",
]
H2_WOHNEN = ["Wohnen in {o}: worauf es bei der Räumung ankommt", "So ist {o} gebaut – und das heißt das für Ihre Entrümpelung",
             "Häuser und Wohnungen in {o}", "Was eine Entrümpelung in {o} ausmacht"]
H2_KURZ = ["{o} kurz erklärt", "Ein bisschen {o}", "Gut zu wissen über {o}", "{o} im Bezirk {b}"]


def ortsseite(o, alle_im_bezirk):
    n, b = o["name"], o["bezirk"]
    ort_hh = n if n.startswith("Hamburg") else f"Hamburg-{n}"
    title = f"Entrümpelung {n} ✓ Haushaltsauflösung ✓ Festpreis | Hinnerk"
    if len(title) > 68:
        title = f"Entrümpelung {n} ✓ Festpreis | Hinnerk"
    desc = f"Entrümpelung und Haushaltsauflösung in {ort_hh}: Wohnung, Haus, Keller. ✓ Kostenlose Besichtigung ✓ Festpreis. Recyclinghof in der Nähe: {o['recyclinghof']['ort']}."
    k, ld = krumen([("Startseite", "./"), ("Einsatzgebiet", "einsatzgebiet.html"), (n, None)])
    faq = list(o.get("faq", []))[:3]
    faq.append({"q": f"Wie läuft eine Entrümpelung in {n} ab?",
                "a": "Sie stellen eine Anfrage, wir besichtigen kostenlos und nennen einen festen Preis. Am vereinbarten Tag räumen wir und bringen alles getrennt zur Entsorgung."})
    schema = [ld, faq_schema(faq), {"@type": "Service", "name": f"Entrümpelung {ort_hh}", "serviceType": "Entrümpelung",
              "provider": {"@id": BASE + "#firma"}, "areaServed": {"@type": "Place", "name": ort_hh,
              "containedInPlace": {"@type": "City", "name": "Hamburg"}}}]
    page = head(title, desc, o["slug"] + ".html", schema)
    page += kopf() + k
    v = {"o": n, "b": b}
    quart = o.get("quartiere") or []
    quart_satz = ""
    if quart:
        quart_satz = f"<p>Zu {E(n)} gehören unter anderem {E(', '.join(quart[:-1]) + ' und ' + quart[-1] if len(quart) > 1 else quart[0])}. Egal in welchem Teil Sie wohnen: Wir kommen zu Ihnen.</p>"
    nachbar_links = []
    for x in o.get("nachbarn", []):
        if x in SLUG_BY_NAME:
            nachbar_links.append(f'<li><a href="{SLUG_BY_NAME[x]}.html">Entrümpelung {E(x)}</a></li>')
        else:
            nachbar_links.append(f"<li><span>{E(x)}</span></li>")
    bez_links = "".join(f'<li><a href="{x["slug"]}.html">{E(x["name"])}</a></li>' for x in alle_im_bezirk if x["slug"] != o["slug"])
    rh = o["recyclinghof"]
    kurz_block = (f"<h2>{E(pick(n + 'h2b', H2_KURZ).format(**v))}</h2>\n<p>{E(o['geschichte'])}</p>" if o.get("geschichte") else "")
    leist = "".join(f'<li><a href="{l["slug"]}.html">{E(l["name"])}</a></li>' for l in LEIST)
    page += f"""<section class="hero"><div class="wrap">
<div><p class="ober">Stadtteil {E(n)} · Bezirk {E(b)}</p>
<h1>Entrümpelung in {E(ort_hh)}</h1>
<p class="lead">{E(pick(n + 'lead', LEAD_VARIANTEN).format(**v))}</p>
<ul class="haken">{''.join(f'<li>{E(x)}</li>' for x in SITE['versprechen'][:2])}<li>Recyclinghof in der Nähe: {E(rh['ort'])}</li></ul>
<div class="knoepfe">{kontakt_knoepfe(wa_text=f'Hallo Hinnerk, ich komme von der Seite {n} und möchte eine Entrümpelung anfragen.')}</div></div>
<div class="hero-bild">{mascot(200)}<p>Hinnerk in {E(n)}</p><small>Bezirk {E(b)}</small></div>
</div></section>
<section class="band band-weiss"><div class="wrap text">
<h2>{E(pick(n + 'h2a', H2_WOHNEN).format(**v))}</h2>
<p>{E(o['bebauung'])}</p>
<p>{E(o['raeumung'])}</p>
{quart_satz}
{kurz_block}
<h2>Entsorgung: Recyclinghof {E(rh['ort'])}</h2>
<p>Ein Recyclinghof der Stadtreinigung Hamburg in der Nähe von {E(n)} ist <b>{E(rh['ort'])}, {E(rh['adresse'])}</b>. Dort werden Sperrmüll, Holz, Metall und Elektrogeräte getrennt angenommen. Wenn Hinnerk für Sie räumt, kümmern wir uns um den Transport.</p>
<h2>Was Hinnerk in {E(n)} räumt</h2>
<ul class="pillen">{leist}</ul>
</div></section>
{ablauf_html(f'Entrümpelung in {n}: so läuft es ab', n + 'ablauf')}
<section class="band"><div class="wrap text">
<h2>Häufige Fragen zu {E(n)}</h2>
{faq_html(faq)}
</div></section>
<section class="band band-weiss"><div class="wrap">
<h2>Auch in der Nähe von {E(n)}</h2>
<ul class="pillen">{''.join(nachbar_links)}</ul>
<h3 style="margin-top:28px">Weitere Stadtteile im Bezirk {E(b)}</h3>
<ul class="pillen">{bez_links}</ul>
<div style="margin-top:28px">{quellen_html(o.get('quellen', []) + [SRH_QUELLE])}</div>
</div></section>
{anfrage(n, n)}
"""
    page += fuss()
    write(o["slug"] + ".html", page)


BEZIRKE = ["Hamburg-Mitte", "Altona", "Eimsbüttel", "Hamburg-Nord", "Wandsbek", "Bergedorf", "Harburg"]


def einsatzgebiet():
    k, ld = krumen([("Startseite", "./"), ("Einsatzgebiet", None)])
    t = "Einsatzgebiet: Entrümpelung in allen Hamburger Stadtteilen | Hinnerk"
    d = f"Hinnerk entrümpelt in allen 7 Hamburger Bezirken. Übersicht über {len(ORTE)} Stadtteile mit eigener Seite und einem Recyclinghof in der Nähe."
    page = head(t, d, "einsatzgebiet.html", [ld]) + kopf() + k
    cols = []
    for b in BEZIRKE:
        li = "".join(f'<li><a href="{o["slug"]}.html">{E(o["name"])}</a></li>' for o in ORTE if o["bezirk"] == b)
        cols.append(f'<div id="{slugify(b)}"><h3>Bezirk {E(b)}</h3><ul>{li}</ul></div>')
    page += f"""<section class="hero"><div class="wrap"><div>
<p class="ober">Einsatzgebiet</p><h1>Entrümpelung in ganz Hamburg</h1>
<p class="lead">Hinnerk ist in allen sieben Bezirken unterwegs. Wählen Sie Ihren Stadtteil – dort finden Sie Infos vor Ort und einen Recyclinghof in der Nähe.</p></div>
<div class="hero-bild">{mascot(200)}<p>{len(ORTE)} Stadtteile</p><small>7 Bezirke</small></div></div></section>
<section class="band band-weiss"><div class="wrap"><div class="bezirke">{''.join(cols)}</div></div></section>
{anfrage('Einsatzgebiet')}
"""
    page += fuss()
    write("einsatzgebiet.html", page)


def rechtliches():
    tel = f"Telefon: {E(F['telefon'])}<br>" if F["telefon"] else ""
    imp = f"""<section class="band"><div class="wrap text">
<h1>Impressum</h1>
<h2>Angaben gemäß § 5 DDG</h2>
<p>Hinnerk – Entrümpelung Hamburg<br>Inhaber: {E(F['inhaber'])}<br>{E(F['strasse'])}<br>{F['plz']} {E(F['ort'])}</p>
<h2>Kontakt</h2>
<p>{tel}E-Mail: <a href="mailto:{F['email']}">{F['email']}</a></p>
<h2>Verbraucherstreitbeilegung</h2>
<p>Wir sind nicht bereit und nicht verpflichtet, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.</p>
</div></section>
"""
    write("impressum.html", head("Impressum | Hinnerk", "Impressum von Hinnerk – Entrümpelung Hamburg.", "impressum.html", robots="noindex,follow") + kopf() + imp + fuss())
    ds = f"""<section class="band"><div class="wrap text">
<h1>Datenschutzerklärung</h1>
<h2>1. Verantwortlicher</h2>
<p>Hinnerk – Entrümpelung Hamburg, Inhaber {E(F['inhaber'])}, {E(F['strasse'])}, {F['plz']} {E(F['ort'])}<br>{tel}E-Mail: <a href="mailto:{F['email']}">{F['email']}</a></p>
<h2>2. Hosting</h2>
<p>Diese Website wird bei GitHub Pages gehostet, einem Dienst der GitHub Inc., 88 Colin P. Kelly Jr. Street, San Francisco, CA 94107, USA. Beim Aufruf der Seite verarbeitet GitHub technisch notwendige Daten wie Ihre IP-Adresse, Datum und Uhrzeit des Abrufs sowie Browser-Informationen, um die Seite auszuliefern und vor Angriffen zu schützen. Rechtsgrundlage ist unser berechtigtes Interesse an einer sicheren und zuverlässigen Bereitstellung der Website (Art. 6 Abs. 1 lit. f DSGVO). GitHub ist eine Tochter der Microsoft Corporation; Microsoft ist nach dem EU-US Data Privacy Framework zertifiziert, auf dessen Grundlage Daten in die USA übermittelt werden dürfen.</p>
<h2>3. Schriftarten</h2>
<p>Die Schriftarten dieser Website sind lokal eingebunden. Beim Aufruf werden keine Verbindungen zu Servern von Google oder anderen Schriftanbietern aufgebaut.</p>
<h2>4. Anfrageformular, E-Mail und Telefon</h2>
<p>Das Anfrageformular speichert keine Daten auf dieser Website, sondern öffnet Ihr E-Mail-Programm mit einer vorbereiteten Nachricht. Wenn Sie uns per E-Mail oder Telefon kontaktieren, verarbeiten wir Ihre Angaben (z. B. Name, Telefonnummer, Beschreibung des Auftrags, Wunschtermin), um Ihre Anfrage zu bearbeiten und ein Angebot zu erstellen. Rechtsgrundlage ist die Anbahnung oder Erfüllung eines Vertrags (Art. 6 Abs. 1 lit. b DSGVO). Wir löschen die Daten, wenn sie nicht mehr benötigt werden und keine gesetzlichen Aufbewahrungspflichten bestehen.</p>
<h2>5. Cookies</h2>
<p>Diese Website setzt keine Cookies und verwendet keine Analyse- oder Werbedienste.</p>
<h2>6. Ihre Rechte</h2>
<p>Sie haben das Recht auf Auskunft, Berichtigung, Löschung, Einschränkung der Verarbeitung, Datenübertragbarkeit und Widerspruch. Außerdem können Sie sich bei einer Datenschutz-Aufsichtsbehörde beschweren, in Hamburg beim Hamburgischen Beauftragten für Datenschutz und Informationsfreiheit.</p>
</div></section>
"""
    write("datenschutz.html", head("Datenschutz | Hinnerk", "Datenschutzerklärung von Hinnerk – Entrümpelung Hamburg.", "datenschutz.html", robots="noindex,follow") + kopf() + ds + fuss())
    nf = f"""<section class="hero"><div class="wrap"><div><p class="ober">Fehler 404</p><h1>Diese Seite gibt es nicht.</h1>
<p class="lead">Vielleicht hilft Ihnen die <a href="./">Startseite</a> oder die <a href="einsatzgebiet.html">Übersicht aller Stadtteile</a>.</p></div>
<div class="hero-bild">{mascot(200)}<p>Hier ist schon leer geräumt.</p></div></div></section>
"""
    page = head("Seite nicht gefunden | Hinnerk", "Diese Seite gibt es nicht.", "404.html", robots="noindex,follow")
    # 404 liegt evtl. in Unterordnern: absolute Pfade
    page = page.replace('href="assets/', 'href="/assets/').replace('href="favicon', 'href="/favicon').replace('href="logo', 'href="/logo')
    body = kopf() + nf + fuss()
    body = body.replace('href="./', 'href="/').replace('href="einsatzgebiet', 'href="/einsatzgebiet').replace('src="assets/', 'src="/assets/')
    write("404.html", page + body)


def sitemap(pfade):
    urls = "".join(f"<url><loc>{BASE}{'' if p == 'index.html' else p}</loc><lastmod>{HEUTE}</lastmod></url>" for p in pfade)
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE}sitemap.xml\n")
    write("CNAME", "hinnerk-entruempelung.de\n")


def favicon():
    svg = mascot(64).replace('width="64" height="64" aria-hidden="true"', 'xmlns="http://www.w3.org/2000/svg" width="64" height="64"')
    write("favicon.svg", svg + "\n")


if __name__ == "__main__":
    if OUT != ROOT:
        for d in ("assets",):
            if (OUT / d).exists():
                shutil.rmtree(OUT / d)
            shutil.copytree(ROOT / d, OUT / d)
        for f in ("logo.png",):
            if (ROOT / f).exists():
                shutil.copy(ROOT / f, OUT / f)
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
