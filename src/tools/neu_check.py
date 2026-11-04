"""Prüft neue Leistungsseiten (Liste im Format von src/leistungen.json, mit kurz/plakat/quellen).

Aufruf: python3 src/tools/neu_check.py src/leistungen_neu.json
"""
import json, re, sys, glob
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bz_check as bz  # noqa: E402

ROOT, SRC = bz.ROOT, bz.SRC
VERBOTEN = bz.VERBOTEN + ["Nr. 1", "N°1", "Nummer 1", "24 Stunden", "Hammer", "Desinfektion übernehmen wir", "streichen wir", "Malerarbeiten übernehmen"]
NEU = {"tapeten-teppich-entfernen-hamburg", "endreinigung-hamburg", "umzug-hamburg", "einlagerung-hamburg"}


def main(pfad):
    p = Path(pfad)
    daten = json.loads(p.read_text(encoding="utf-8"))
    probleme = 0

    def fehler(msg):
        nonlocal probleme
        probleme += 1
        print("PROBLEM:", msg)

    erlaubt = set(bz.ERLAUBT) | {Path(x).name for x in glob.glob(str(ROOT / "*.html"))} | {s + ".html" for s in NEU}
    if {e.get("slug") for e in daten} != NEU:
        fehler(f"slugs müssen genau {sorted(NEU)} sein")
    for e in daten:
        n = e.get("slug", "?")
        for k in ("slug", "name", "title", "description", "h1", "lead", "kurz", "plakat", "sections", "faq", "quellen"):
            if k not in e:
                fehler(f"{n}: Feld {k} fehlt")
        if len(e.get("title", "")) > 70:
            fehler(f"{n}: title zu lang ({len(e['title'])})")
        if len(e.get("description", "")) > 160:
            fehler(f"{n}: description zu lang ({len(e['description'])})")
        for f_ in e.get("faq", []):
            if "<" in f_.get("q", "") + f_.get("a", ""):
                fehler(f"{e.get('slug')}: FAQ ohne HTML/Links schreiben (wird als Text angezeigt)")
        if len(e.get("kurz", "")) > 120:
            fehler(f"{n}: kurz zu lang")
        if not (4 <= len(e.get("sections", [])) <= 6):
            fehler(f"{n}: 4–6 Abschnitte nötig")
        if not (4 <= len(e.get("faq", [])) <= 5):
            fehler(f"{n}: 4–5 FAQ nötig")
        w = len(re.findall(r"\w+", re.sub(r"<[^>]+>", " ", " ".join(s["html"] for s in e.get("sections", [])))))
        if not (450 <= w <= 750):
            fehler(f"{n}: Abschnitte haben {w} Wörter (450–750)")
        alles = " ".join([e.get("title", ""), e.get("description", ""), e.get("lead", ""), e.get("kurz", "")] + [s["html"] for s in e.get("sections", [])] + [f["q"] + " " + f["a"] for f in e.get("faq", [])])
        for v in VERBOTEN:
            if v in alles:
                fehler(f"{n}: verbotenes Wort/Angabe „{v}“")
        if re.search(r"\bab \d[\d.]* ?€", re.sub(r"<[^>]+>", "", alles)):
            fehler(f"{n}: Ab-Preis gefunden – für neue Leistungen keine Hinnerk-Preise")
        if '"' in re.sub(r"<[^>]+>", "", alles):
            fehler(f"{n}: gerade Anführungszeichen im Text")
        for href in re.findall(r'href="([^"]+)"', alles):
            if not href.startswith("http") and href not in erlaubt and href.split("#")[0] not in erlaubt:
                fehler(f"{n}: Link-Ziel gibt es nicht: {href}")

    fremd = {}
    for l in bz.LEIST:
        for s in bz.saetze(" ".join(x["html"] for x in l["sections"]) + " " + " ".join(f["a"] for f in l["faq"])):
            fremd.setdefault(s, "Leistung " + l["slug"])
    for r in bz.RAT:
        for s in bz.saetze(" ".join(a.get("html", "") for a in r["abschnitte"])):
            fremd.setdefault(s, "Ratgeber " + r["slug"])
    for f in sorted((SRC / "bezirke").glob("*.json")):
        for e in json.loads(f.read_text(encoding="utf-8")):
            for s in bz.saetze(bz.text(e)):
                fremd.setdefault(s, "Bezirk " + f.name)
    eigen = {}
    for e in daten:
        for s in bz.saetze(" ".join(x["html"] for x in e.get("sections", [])) + " " + " ".join(f["a"] for f in e.get("faq", []))):
            if s in fremd:
                fehler(f"{e.get('slug')}: Satz kommt schon vor in {fremd[s]}: {s[:80]}")
            if s in eigen and eigen[s] != e.get("slug"):
                fehler(f"{e.get('slug')}: Satz doppelt mit {eigen[s]}: {s[:80]}")
            eigen.setdefault(s, e.get("slug"))
    print("ok" if probleme == 0 else f"{probleme} Probleme")
    return probleme


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1]) else 0)
