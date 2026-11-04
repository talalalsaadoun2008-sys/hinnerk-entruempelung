"""Prüft eine Umland-Datei src/umland/<datei>.json.

Aufruf: python3 src/tools/um_check.py src/umland/pinneberg.json
Format, Längen, verbotene Angaben, Link-Ziele und doppelte Sätze (ab 10 Wörtern)
gegenüber allen anderen Texten der Seite. Ende: "ok" oder Anzahl der Probleme.
"""
import json, re, sys, glob
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bz_check as bz  # noqa: E402

SRC = bz.SRC
UMLAND_NAMEN = ["Norderstedt", "Pinneberg", "Ahrensburg", "Wedel", "Elmshorn", "Buxtehude", "Geesthacht", "Winsen (Luhe)", "Winsen",
                "Buchholz in der Nordheide", "Buchholz", "Kreis Pinneberg", "Kreis Segeberg", "Kreis Stormarn", "Kreis Herzogtum Lauenburg",
                "Landkreis Stade", "Landkreis Harburg", "Schleswig-Holstein", "Niedersachsen"]
bz.namen.extend(UMLAND_NAMEN)
bz.namen.sort(key=len, reverse=True)
ROOT = bz.ROOT
VERBOTEN = bz.VERBOTEN + ["Nr. 1", "N°1", "Nummer 1", "Minuten", "ab 290", "ab 690", "ab 129", "ab 1.890", "ab 2.490", "Hammer", "Gründung"]
ERLAUBT = set(bz.ERLAUBT) | {Path(p).name for p in glob.glob(str(ROOT / "*.html"))}
ORTSNAMEN = {o["name"] for o in bz.ORTE}


def text(e):
    return e["lead"] + " " + " ".join(a["html"] for a in e["abschnitte"]) + " " + " ".join(f["a"] for f in e["faq"])


def main(pfad):
    p = Path(pfad)
    daten = json.loads(p.read_text(encoding="utf-8"))
    probleme = 0

    def fehler(msg):
        nonlocal probleme
        probleme += 1
        print("PROBLEM:", msg)

    eigene_slugs = {e.get("slug") for e in daten}
    for e in daten:
        n = e.get("ort", "?")
        for k in ("slug", "ort", "kreis", "land", "title", "description", "h1", "lead", "abschnitte", "hoefe", "hh_nachbarn", "faq", "quellen"):
            if k not in e:
                fehler(f"{n}: Feld {k} fehlt")
        if not re.fullmatch(r"entruempelung-[a-z0-9-]+", e.get("slug", "")):
            fehler(f"{n}: slug ungültig")
        if len(e.get("title", "")) > 70:
            fehler(f"{n}: title zu lang ({len(e['title'])})")
        if len(e.get("description", "")) > 160:
            fehler(f"{n}: description zu lang ({len(e['description'])})")
        if not (3 <= len(e.get("abschnitte", [])) <= 4):
            fehler(f"{n}: 3–4 Abschnitte nötig")
        if not (3 <= len(e.get("faq", [])) <= 4):
            fehler(f"{n}: 3–4 FAQ nötig")
        if len(e.get("quellen", [])) < 3:
            fehler(f"{n}: mind. 3 Quellen nötig")
        for f_ in e.get("faq", []):
            if "<" in f_.get("q", "") + f_.get("a", ""):
                fehler(f"{e.get('slug')}: FAQ ohne HTML/Links schreiben (wird als Text angezeigt)")
        if not (1 <= len(e.get("hoefe", [])) <= 3):
            fehler(f"{n}: 1–3 Höfe nötig")
        for x in e.get("hh_nachbarn", []):
            if x not in ORTSNAMEN:
                fehler(f"{n}: hh_nachbarn „{x}“ ist kein Hamburger Stadtteil aus stadtteile.json")
        woerter = len(re.findall(r"\w+", re.sub(r"<[^>]+>", " ", " ".join(a["html"] for a in e.get("abschnitte", [])))))
        if not (350 <= woerter <= 650):
            fehler(f"{n}: Abschnitte haben {woerter} Wörter (350–650)")
        alles = text(e) + " " + e.get("title", "") + " " + e.get("description", "") + " " + e.get("h1", "")
        for v in VERBOTEN:
            if v in alles:
                fehler(f"{n}: verbotenes Wort/Angabe „{v.strip()}“")
        if '"' in re.sub(r"<[^>]+>", "", alles):
            fehler(f"{n}: gerade Anführungszeichen im Text")
        for href in re.findall(r'href="([^"]+)"', text(e)):
            ziel = href.split("#")[0] or href
            if href.startswith("http") or href in ERLAUBT or ziel in ERLAUBT or href.replace(".html", "") in eigene_slugs:
                continue
            fehler(f"{n}: Link-Ziel gibt es nicht: {href}")

    fremd = {}
    for l in bz.LEIST:
        for s in bz.saetze(" ".join(x["html"] for x in l["sections"]) + " " + l.get("lead", "") + " " + " ".join(f["a"] for f in l["faq"])):
            fremd.setdefault(s, "Leistung " + l["slug"])
    for r in bz.RAT:
        for s in bz.saetze(" ".join(a.get("html", "") for a in r["abschnitte"])):
            fremd.setdefault(s, "Ratgeber " + r["slug"])
    for o in bz.ORTE:
        for s in bz.saetze(" ".join(o.get(k, "") for k in ("bebauung", "raeumung", "geschichte")) + " " + " ".join(f["a"] for f in o.get("faq", []))):
            fremd.setdefault(s, "Stadtteil " + o["name"])
    for f in sorted((SRC / "bezirke").glob("*.json")):
        for e in json.loads(f.read_text(encoding="utf-8")):
            for s in bz.saetze(bz.text(e)):
                fremd.setdefault(s, f"Bezirk {f.name}")
    for f in sorted((SRC / "umland").glob("*.json")):
        if f.resolve() == p.resolve():
            continue
        try:
            for e in json.loads(f.read_text(encoding="utf-8")):
                for s in bz.saetze(text(e)):
                    fremd.setdefault(s, f"Umland {f.name} {e.get('ort')}")
        except Exception:
            pass
    eigen = {}
    for e in daten:
        n = e.get("ort", "?")
        for s in bz.saetze(text(e)):
            if s in fremd:
                fehler(f"{n}: Satz kommt schon vor in {fremd[s]}: {s[:80]}")
            if s in eigen and eigen[s] != n:
                fehler(f"{n}: Satz doppelt mit {eigen[s]}: {s[:80]}")
            eigen.setdefault(s, n)
    print("ok" if probleme == 0 else f"{probleme} Probleme")
    return probleme


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1]) else 0)
