# -*- coding: utf-8 -*-
"""Gouvernorat de chaque lieu de prière de la carte (28/11/2026, plan VIS.3 point 5 d'Ahmed : « les mosquées sur la carte en chiffres »).
Les données de la carte (OpenStreetMap + Wikidata) n'ont PAS de champ « gouvernorat ». On le calcule d'après la POSITION du point :
il est dans le contour officiel d'un seul des 24 gouvernorats (tools/gouvernorats_tn.json). Rien n'est deviné d'après un nom de ville.
  - Contours : geoBoundaries « TUN ADM1 » (tirés d'OpenStreetMap, licence ODbL comme nos lieux), simplifiés à ~20 m.
    Le 28/11/2026, avec les contours complets ET simplifiés, chacun des 2 256 lieux est dans un et un seul gouvernorat.
  - Un point hors de tous les contours (bord de mer, île) : le gouvernorat le plus proche s'il est à moins de PROCHE_KM km,
    sinon « non classé » (ligne affichée seulement s'il y en a). Le compte rendu de la construction le dit.
Refaire le fichier des contours (rare : les gouvernorats ne changent pas) :
  python tools/gouvernorats.py <geoBoundaries-TUN-ADM1.geojson>"""
import json, math, os, sys

ICI = os.path.dirname(os.path.abspath(__file__))
FICHIER = os.path.join(ICI, "gouvernorats_tn.json")
PROCHE_KM = 3
TOLERANCE = 0.0002          # degrés (~20 m) : simplification des contours

# les 24 gouvernorats (code ISO 3166-2, nom officiel en lettres latines, nom arabe) — même liste que le moteur des annuaires
GOUVERNORATS = [
    ("TN-12", "Ariana", "أريانة"), ("TN-31", "Béja", "باجة"), ("TN-13", "Ben Arous", "بن عروس"), ("TN-23", "Bizerte", "بنزرت"),
    ("TN-81", "Gabès", "قابس"), ("TN-71", "Gafsa", "قفصة"), ("TN-32", "Jendouba", "جندوبة"), ("TN-41", "Kairouan", "القيروان"),
    ("TN-42", "Kasserine", "القصرين"), ("TN-73", "Kébili", "قبلي"), ("TN-33", "Le Kef", "الكاف"), ("TN-53", "Mahdia", "المهدية"),
    ("TN-14", "La Manouba", "منوبة"), ("TN-82", "Médenine", "مدنين"), ("TN-52", "Monastir", "المنستير"), ("TN-21", "Nabeul", "نابل"),
    ("TN-61", "Sfax", "صفاقس"), ("TN-43", "Sidi Bouzid", "سيدي بوزيد"), ("TN-34", "Siliana", "سليانة"), ("TN-51", "Sousse", "سوسة"),
    ("TN-83", "Tataouine", "تطاوين"), ("TN-72", "Tozeur", "توزر"), ("TN-11", "Tunis", "تونس"), ("TN-22", "Zaghouan", "زغوان"),
]
_CONTOURS = []


def _dans(x, y, anneau):
    c, j = False, len(anneau) - 1
    for i in range(len(anneau)):
        xi, yi = anneau[i]; xj, yj = anneau[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            c = not c
        j = i
    return c


def _dist_km(lat, lon, anneau):
    """Distance (km, approchée) du point au bord d'un anneau."""
    k = math.cos(math.radians(lat)) * 111.32
    best = float("inf")
    for (ax, ay), (bx, by) in zip(anneau, anneau[1:]):
        ax, bx, px = ax * k, bx * k, lon * k
        ay, by, py = ay * 110.57, by * 110.57, lat * 110.57
        dx, dy = bx - ax, by - ay
        t = 0 if dx == dy == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(px - ax - t * dx, py - ay - t * dy))
    return best


def charger():
    if not _CONTOURS:
        d = json.load(open(FICHIER, encoding="utf-8"))
        _CONTOURS.extend((g["iso"], g["polygones"]) for g in d["gouvernorats"])
    return _CONTOURS


def gouvernorat(lat, lon):
    """Code ISO du gouvernorat qui contient le point ; le plus proche à moins de PROCHE_KM km ; sinon None."""
    trouves = [iso for iso, ps in charger() if any(_dans(lon, lat, p[0]) and not any(_dans(lon, lat, h) for h in p[1:]) for p in ps)]
    if trouves:
        return sorted(trouves)[0]
    d, iso = min((min(_dist_km(lat, lon, p[0]) for p in ps), iso) for iso, ps in charger())
    return iso if d <= PROCHE_KM else None


def _simplifier(pts, tol):
    if len(pts) < 3:
        return pts
    garder = [False] * len(pts); garder[0] = garder[-1] = True
    pile = [(0, len(pts) - 1)]
    while pile:
        a, b = pile.pop(); (ax, ay), (bx, by) = pts[a], pts[b]; dx, dy = bx - ax, by - ay; n2 = dx * dx + dy * dy
        m, im = -1, -1
        for i in range(a + 1, b):
            px, py = pts[i]
            t = 0 if n2 == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / n2))
            e = (px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2
            if e > m:
                m, im = e, i
        if m > tol * tol:
            garder[im] = True; pile += [(a, im), (im, b)]
    return [p for p, g in zip(pts, garder) if g]


def refaire(geojson):
    d = json.load(open(geojson, encoding="utf-8"))
    sortie = []
    for f in d["features"]:
        g = f["geometry"]; ps = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        q = [[[[round(x, 5), round(y, 5)] for x, y in _simplifier(r, TOLERANCE)] for r in p] for p in ps]
        q = [p for p in ([r for r in p if len(r) >= 4] for p in q) if p]
        sortie.append({"iso": f["properties"]["shapeISO"], "polygones": q})
    if sorted(g["iso"] for g in sortie) != sorted(g[0] for g in GOUVERNORATS):
        raise SystemExit("le fichier n'a pas les 24 gouvernorats attendus")
    texte = json.dumps({"source": "geoBoundaries TUN ADM1 (OpenStreetMap, ODbL) — https://www.geoboundaries.org/", "tolerance_degres": TOLERANCE,
                        "gouvernorats": sorted(sortie, key=lambda g: g["iso"])}, ensure_ascii=False, separators=(",", ":"))
    open(FICHIER, "w", encoding="utf-8", newline="\n").write(texte + "\n")
    print(f"{FICHIER} : {len(sortie)} gouvernorats, {len(texte) // 1024} Ko")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        refaire(sys.argv[1])
    else:
        print(__doc__)
