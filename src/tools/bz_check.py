"""Prüft eine Bezirks-Datei src/bezirke/<bezirk>.json.

Aufruf: python3 src/tools/bz_check.py src/bezirke/altona.json
Meldet Format-Fehler, Längen, unbekannte Links und doppelte Sätze (ab 10 Wörtern)
innerhalb der Datei, gegenüber Leistungs-/Stadtteil-Texten und gegenüber anderen Bezirks-Dateien.
Ende: "ok" oder Anzahl der Probleme.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
ORTE = json.loads((SRC / "stadtteile.json").read_text(encoding="utf-8"))
LEIST = json.loads((SRC / "leistungen.json").read_text(encoding="utf-8"))
RAT = json.loads((SRC / "ratgeber.json").read_text(encoding="utf-8"))
BEZIRKE = ["Hamburg-Mitte", "Altona", "Eimsbüttel", "Hamburg-Nord", "Wandsbek", "Bergedorf", "Harburg"]


def slugify(s):
    s = s.lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss"), (".", ""), ("–", "-")):
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


for _o in ORTE:
    _o["slug"] = "entruempelung-hamburg-" + slugify(_o["name"].replace("Hamburg-", ""))
ERLAUBT = {o["slug"] + ".html" for o in ORTE} | {l["slug"] + ".html" for l in LEIST} | {r["slug"] + ".html" for r in RAT} | {
    "./", "preise.html", "preise.html#rechner", "kontakt.html", "ratgeber.html", "einsatzgebiet.html", "ueber-hinnerk.html", "#anfrage"}
VERBOTEN = ["Dosestra", "T&A", "HafenRäumer", "Hafenräumer", "seit Jahren", "jahrelang", "erfahrenes Team", "versichert", "zertifiziert",
            "Bewertung", "Sterne", "aus Altona", "unser Sitz", "unser Büro", "unserem Büro"]
namen = sorted([o["name"] for o in ORTE] + BEZIRKE + [l["name"] for l in LEIST] + ["Hamburg"], key=len, reverse=True)


def saetze(html_):
    t = re.sub(r"<[^>]+>", " ", html_)
    for x in namen:
        t = t.replace(x, "#")
    t = re.sub(r"\d+", "0", t)
    for satz in re.split(r"(?<=[.!?])\s+", t):
        w = re.findall(r"\w+", satz.lower())
        if len(w) >= 10:
            yield " ".join(w)


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

    slugs = {l["slug"] for l in LEIST}
    gesehen_l = set()
    for e in daten:
        name = f'{e.get("leistung")}/{e.get("bezirk")}'
        for k in ("leistung", "bezirk", "title", "description", "h1", "lead", "abschnitte", "faq", "quellen"):
            if k not in e:
                fehler(f"{name}: Feld {k} fehlt")
        if e.get("leistung") not in slugs:
            fehler(f"{name}: unbekannte Leistung")
        if e.get("bezirk") not in BEZIRKE:
            fehler(f"{name}: unbekannter Bezirk")
        gesehen_l.add(e.get("leistung"))
        if len(e.get("title", "")) > 70:
            fehler(f"{name}: title zu lang ({len(e['title'])})")
        if len(e.get("description", "")) > 160:
            fehler(f"{name}: description zu lang ({len(e['description'])})")
        if not (2 <= len(e.get("abschnitte", [])) <= 3):
            fehler(f"{name}: 2–3 Abschnitte nötig")
        if len(e.get("faq", [])) != 3:
            fehler(f"{name}: genau 3 FAQ nötig")
        if len(e.get("quellen", [])) < 2:
            fehler(f"{name}: mind. 2 Quellen nötig")
        woerter = len(re.findall(r"\w+", re.sub(r"<[^>]+>", " ", " ".join(a["html"] for a in e.get("abschnitte", [])))))
        if not (200 <= woerter <= 420):
            fehler(f"{name}: Abschnitte haben {woerter} Wörter (200–420)")
        alles = text(e) + " " + e.get("title", "") + " " + e.get("description", "") + " " + e.get("h1", "")
        for v in VERBOTEN:
            if v in alles:
                fehler(f"{name}: verbotenes Wort/Angabe „{v.strip()}“")
        for href in re.findall(r'href="([^"]+)"', text(e)):
            if not href.startswith("http") and href not in ERLAUBT:
                fehler(f"{name}: Link-Ziel gibt es nicht: {href}")
        for b in BEZIRKE:
            if b != e.get("bezirk") and re.search(rf"Bezirk {re.escape(b)}\b", alles):
                fehler(f"{name}: nennt fremden Bezirk „Bezirk {b}“")
    if len(daten) != 12 or gesehen_l != slugs:
        fehler(f"Datei braucht genau 12 Einträge, je Leistung einer (hat {len(daten)}, fehlend: {sorted(slugs - gesehen_l)})")

    # doppelte Sätze
    fremd = {}
    for l in LEIST:
        for s in saetze(" ".join(x["html"] for x in l["sections"]) + " " + l.get("lead", "")):
            fremd.setdefault(s, "Leistungsseite " + l["slug"])
    for o in ORTE:
        for s in saetze(" ".join(o.get(k, "") for k in ("bebauung", "raeumung", "geschichte"))):
            fremd.setdefault(s, "Stadtteil " + o["slug"])
    for andere in sorted((SRC / "bezirke").glob("*.json")):
        if andere.resolve() == p.resolve():
            continue
        try:
            for e in json.loads(andere.read_text(encoding="utf-8")):
                for s in saetze(text(e)):
                    fremd.setdefault(s, f"{andere.name} {e.get('leistung')}")
        except Exception:
            pass
    eigen = {}
    for e in daten:
        name = f'{e.get("leistung")}/{e.get("bezirk")}'
        for s in saetze(text(e)):
            if s in fremd:
                fehler(f"{name}: Satz kommt schon vor in {fremd[s]}: {s[:80]}")
            if s in eigen and eigen[s] != name:
                fehler(f"{name}: Satz doppelt mit {eigen[s]}: {s[:80]}")
            eigen.setdefault(s, name)
    print("ok" if probleme == 0 else f"{probleme} Probleme")
    return probleme


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1]) else 0)
