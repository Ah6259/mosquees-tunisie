# -*- coding: utf-8 -*-
"""Mosquées et salles de prière de Tunisie (site « Mosquées en Tunisie », idée d'Ahmed du 09/10/2026).
Relu TOUS LES 3 MOIS par le robot GitHub (workflow donnees.yml). Sources, toutes libres et citées sur le site :
  - OpenStreetMap (ODbL) : tous les lieux de prière musulmans de Tunisie (position, nom) + villes et villages
    (pour la recherche « par ville ») ;
  - Wikidata (CC0) : noms en 8 langues, date de fondation, patrimoine, photo, articles Wikipédia ;
  - Wikimedia Commons : la photo (auteur + licence affichés sous chaque photo ; licence libre exigée) ;
  - Wikipédia (CC BY-SA 4.0) : le résumé de l'article dans chaque langue (lien vers l'article, licence citée).
Règles de propreté (09/10/2026) :
  - les noms génériques (« Mosque », « Mosquée », « مسجد »…) ne sont pas des noms : le lieu est dit « Mosquée » + sa ville ;
  - une fiche Wikidata rejoint un lieu OpenStreetMap par son étiquette wikidata, sinon le plus proche à moins de 120 m
    SEULEMENT si les noms se ressemblent (ou si le lieu OSM n'a pas de nom) ; sinon elle devient un lieu à part ;
  - les noms de la fiche Wikidata passent avant ceux d'OpenStreetMap ;
  - une année de fondation avant 670 (arrivée de l'islam en Ifriqiya) ou dans le futur est ignorée.
Panne ou réponse suspecte : l'ancien fichier est gardé (code 1 → alerte).
Sortie : donnees/mosquees.json (lu par tools/construire.py, qui fabrique la carte et les pages).
Usage : python tools/mosquees_donnees.py"""
import json, math, re, sys, time, unicodedata, urllib.parse, urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SORTIE = ROOT / "donnees" / "mosquees.json"
UA = {"User-Agent": "mosquees-tunisie/1.0 (+https://mosquees.clicvia.com/; site non commercial)"}
LANGUES = ["fr", "ar", "en", "tr", "id", "ur", "de", "es"]
SERVEURS = ["https://maps.mail.ru/osm/tools/overpass/api/interpreter", "https://overpass-api.de/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter", "https://overpass.private.coffee/api/interpreter",
            "https://overpass.openstreetmap.fr/api/interpreter"]   # 5 copies d'OpenStreetMap (règle commune § 4)
MIN_OSM, MIN_WD, MIN_VILLES = 1500, 100, 500
ZONE = 'area["ISO3166-1"="TN"][admin_level=2]->.a;'
# noms qui ne désignent pas un lieu précis
GENERIQUES = {"mosque", "mosquee", "mosquée", "masjid", "mescit", "cami", "camii", "moschee", "mezquita", "masjid", "مسجد", "جامع", "مصلى",
              "great mosque", "grande mosquée", "grande mosquee", "salle de prière", "salle de priere", "prayer room", "musalla",
              "الجامع", "المسجد", "mosquee", "jamaa", "jemaa", "jamii", "jami"}


def http(url, data=None, entetes=None, delai=200):
    req = urllib.request.Request(url, data=data, headers={**UA, **(entetes or {})})
    with urllib.request.urlopen(req, timeout=delai) as r:
        return json.loads(r.read())


def overpass(q, minimum, essais=10):
    dernier = None
    for i in range(essais):
        url = SERVEURS[i % len(SERVEURS)]
        try:
            d = http(url, urllib.parse.urlencode({"data": q}).encode())
            rem = str(d.get("remark", ""))
            if "error" in rem.lower() or "timed out" in rem.lower():      # réponse vide + erreur cachée : serveur suivant
                raise RuntimeError(f"{url} : {rem[:80]}")
            if len(d.get("elements", [])) < minimum:
                raise RuntimeError(f"{url} : seulement {len(d.get('elements', []))} éléments")
            return d
        except Exception as e:
            dernier = e
            time.sleep(10 * (i + 1))
    raise RuntimeError(f"Overpass indisponible : {dernier}")


def distance_m(a, b):
    r = 6371000
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(b[1] - a[1]) / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def propre(s, n=90):
    return re.sub(r"\s+", " ", re.sub(r"[<>\"`]", "", s or "")).strip()[:n]


def generique(nom):
    return propre(nom).lower().strip(" .-") in GENERIQUES


def mots(s):
    """Mots significatifs d'un nom (sans accents ni mots « mosquée », « sidi », articles)."""
    s = unicodedata.normalize("NFD", (s or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"\b(el|al|ال)", " ", s)
    vides = {"mosquee", "mosque", "grande", "great", "of", "de", "du", "des", "la", "le", "jamaa", "jemaa", "masjid", "sidi", "مسجد", "جامع",
             "سيدي", "camii", "moschee", "mezquita", "d", "l", "ibn", "ben", "بن", "the"}
    return {m for m in re.findall(r"\w{3,}", s) if m not in vides}


def lire_osm():
    q = ('[out:json][timeout:180];' + ZONE +
         '(nwr["amenity"="place_of_worship"]["religion"="muslim"](area.a););out center tags;')
    lieux = []
    for e in overpass(q, MIN_OSM)["elements"]:
        t = e.get("tags", {})
        lat = e.get("lat", (e.get("center") or {}).get("lat")); lon = e.get("lon", (e.get("center") or {}).get("lon"))
        if lat is None or lon is None:
            continue
        texte = (t.get("name", "") + " " + t.get("name:fr", "")).lower()
        salle = t.get("place_of_worship") in ("musalla", "prayer_room", "prayer_hall") or "salle de pri" in texte or "مصلى" in t.get("name", "") \
            or t.get("building") in ("room",) or t.get("indoor") == "room"
        noms = {l: propre(t.get("name:" + l)) for l in LANGUES if t.get("name:" + l) and not generique(t.get("name:" + l))}
        nom = propre(t.get("name"))
        if nom and not generique(nom):
            if re.search(r"[؀-ۿ]", nom): noms.setdefault("ar", nom)
            else: noms.setdefault("fr", nom)
        lieux.append({"id": f"osm-{e['type'][0]}{e['id']}", "lat": round(lat, 6), "lon": round(lon, 6), "type": "salle" if salle else "mosquee",
                      "noms": noms, "ville": {}, "wikidata": t.get("wikidata", ""),
                      "rite": {"sunni": "sunnite", "ibadi": "ibadite"}.get(t.get("denomination"), "")})
    return lieux


def lire_villes():
    """Villes, bourgs et villages de Tunisie (nom en français et en arabe) : la recherche « par ville »."""
    q = '[out:json][timeout:120];' + ZONE + '(node["place"~"^(city|town|village|suburb)$"](area.a););out body;'
    villes = []
    for e in overpass(q, MIN_VILLES)["elements"]:
        t = e.get("tags", {})
        fr = propre(t.get("name:fr") or (t.get("name") if not re.search(r"[؀-ۿ]", t.get("name", "")) else "") or t.get("name:en") or "", 40)
        ar = propre(t.get("name:ar") or (t.get("name") if re.search(r"[؀-ۿ]", t.get("name", "")) else ""), 40)
        if fr or ar:
            villes.append({"lat": e["lat"], "lon": e["lon"], "rang": {"city": 3, "town": 2, "suburb": 1, "village": 1}[t["place"]], "fr": fr, "ar": ar})
    return villes


def ville_proche(lieu, villes):
    """La localité la plus proche (ville/bourg à moins de 12 km de préférence, sinon village ou quartier à moins de 6 km)."""
    p = (lieu["lat"], lieu["lon"])
    def proche(liste, maxi):
        m = min(((distance_m(p, (v["lat"], v["lon"])), v) for v in liste), key=lambda x: x[0], default=(9e9, None))
        return m[1] if m[0] <= maxi else None
    pres = [v for v in villes if abs(v["lat"] - p[0]) < 0.2 and abs(v["lon"] - p[1]) < 0.2]
    petit = proche(pres, 2500)
    grand = proche([v for v in pres if v["rang"] >= 2], 12000)
    v = petit or grand or proche(pres, 6000)
    if not v:
        return {}
    out = {k: v[k] for k in ("fr", "ar") if v[k]}
    if grand and v is not grand:
        out["region_fr"], out["region_ar"] = grand["fr"], grand["ar"]
    return {k: x for k, x in out.items() if x}


def lire_wikidata():
    champs = " ".join(f"?l_{l}" for l in LANGUES) + " " + " ".join(f"?w_{l}" for l in LANGUES)
    labels = "".join(f'OPTIONAL{{?m rdfs:label ?l_{l} FILTER(lang(?l_{l})="{l}")}}' for l in LANGUES)
    liens = "".join(f'OPTIONAL{{?w_{l} schema:about ?m; schema:isPartOf <https://{l}.wikipedia.org/>}}' for l in LANGUES)
    q = f"""SELECT ?m ?coord ?img ?debut ?patrimoine {champs} WHERE {{
      ?m wdt:P31/wdt:P279* wd:Q32815; wdt:P17 wd:Q948.
      OPTIONAL{{?m wdt:P625 ?coord}} OPTIONAL{{?m wdt:P18 ?img}} OPTIONAL{{?m wdt:P571 ?debut}} OPTIONAL{{?m wdt:P1435 ?patrimoine}}
      {labels} {liens} }}"""
    d = http("https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": q}), entetes={"Accept": "application/sparql-results+json"})
    fiches, an = {}, date.today().year
    for b in d["results"]["bindings"]:
        qid = b["m"]["value"].rsplit("/", 1)[1]
        f = fiches.setdefault(qid, {"qid": qid, "noms": {}, "wiki": {}, "image": "", "annee": None, "patrimoine": False, "coord": None})
        for l in LANGUES:
            if f"l_{l}" in b and not generique(b[f"l_{l}"]["value"]): f["noms"][l] = propre(b[f"l_{l}"]["value"])
            if f"w_{l}" in b: f["wiki"][l] = urllib.parse.unquote(b[f"w_{l}"]["value"].rsplit("/wiki/", 1)[1])
        if "img" in b and not f["image"]: f["image"] = urllib.parse.unquote(b["img"]["value"].rsplit("/", 1)[1])
        if "debut" in b:
            m = re.match(r"(-?\d{1,4})-", b["debut"]["value"])
            if m and 670 <= int(m.group(1)) <= an: f["annee"] = min(int(m.group(1)), f["annee"] or 9999)
        if "patrimoine" in b: f["patrimoine"] = True
        if "coord" in b and not f["coord"]:
            m = re.match(r"Point\(([-\d.]+) ([-\d.]+)\)", b["coord"]["value"])
            if m: f["coord"] = [round(float(m.group(2)), 6), round(float(m.group(1)), 6)]
    return fiches


def credits_photos(fichiers):
    """Auteur, licence et vignette de chaque photo (Wikimedia Commons), 40 par appel. Licence libre exigée."""
    sortie, fichiers = {}, sorted(set(f for f in fichiers if f))
    for i in range(0, len(fichiers), 40):
        titres = "|".join("File:" + f for f in fichiers[i:i + 40])
        d = http("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
            "action": "query", "titles": titres, "prop": "imageinfo", "iiprop": "url|extmetadata", "iiurlwidth": 800, "format": "json"}))
        norm = {n["to"]: n["from"] for n in d["query"].get("normalized", [])}
        for p in d["query"]["pages"].values():
            ii = (p.get("imageinfo") or [{}])[0]
            em = ii.get("extmetadata", {})
            licence = (em.get("LicenseShortName") or {}).get("value", "")
            if not ii.get("thumburl") or not re.search(r"CC|Public domain|domaine public|PD", licence, re.I) or re.search(r"\bNC\b|\bND\b|fair use", licence, re.I):
                continue                                                   # licence inconnue ou non libre : photo non utilisée
            nom = norm.get(p["title"], p["title"])[5:]
            sortie[nom.replace("_", " ")] = {"url": ii["thumburl"].split("?")[0], "page": ii.get("descriptionurl", ""), "licence": propre(licence, 40),
                                             "auteur": propre(re.sub(r"<[^>]+>", "", (em.get("Artist") or {}).get("value", "")), 80) or "Wikimedia Commons"}
        time.sleep(0.5)
    return sortie


def resumes(fiches):
    """Résumé (introduction) de l'article Wikipédia, dans chaque langue où il existe."""
    for f in fiches.values():
        f["resume"] = {}
        for l, titre in f["wiki"].items():
            try:
                d = http(f"https://{l}.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(titre.replace(' ', '_'), safe='')}", delai=60)
                txt = propre(d.get("extract", ""), 1200)
                if len(txt) > 60: f["resume"][l] = txt
            except Exception:
                pass
            time.sleep(0.15)


def rattacher(lieux, fiches, photos):
    """Chaque fiche Wikidata rejoint son lieu OpenStreetMap (étiquette wikidata, sinon proche ET même nom), sinon devient un lieu à part."""
    par_qid = {l["wikidata"]: l for l in lieux if l["wikidata"]}
    for f in fiches.values():
        lieu = par_qid.get(f["qid"])
        if lieu and lieu.get("fiche"):
            lieu = None
        if not lieu and f["coord"]:
            mf = set().union(*[mots(n) for n in f["noms"].values()]) if f["noms"] else set()
            cand = sorted(((distance_m(f["coord"], (l["lat"], l["lon"])), l) for l in lieux
                           if not l.get("fiche") and not l["wikidata"] and abs(l["lat"] - f["coord"][0]) < 0.01 and abs(l["lon"] - f["coord"][1]) < 0.01),
                          key=lambda x: x[0])
            for dist, l in cand:
                if dist > 120: break
                ml = set().union(*[mots(n) for n in l["noms"].values()]) if l["noms"] else set()
                if not ml or (mf & ml):
                    lieu = l; break
        if not lieu:
            if not f["coord"]: continue
            lieu = {"id": "wd-" + f["qid"], "lat": f["coord"][0], "lon": f["coord"][1], "type": "mosquee", "noms": {}, "ville": {}, "wikidata": f["qid"], "rite": ""}
            lieux.append(lieu)
        lieu["fiche"] = {"qid": f["qid"], "annee": f["annee"], "patrimoine": f["patrimoine"], "wiki": f["wiki"], "resume": f["resume"],
                         "photo": photos.get(f["image"].replace("_", " "))}
        lieu["noms"] = {**lieu["noms"], **f["noms"]}            # les noms de Wikidata passent avant ceux d'OpenStreetMap
        lieu["type"] = "mosquee"
    return lieux


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    try:
        lieux = lire_osm()
        villes = lire_villes()
        fiches = lire_wikidata()
    except Exception as e:
        print("Échec, ancien fichier gardé :", e); return 1
    if len(lieux) < MIN_OSM or len(fiches) < MIN_WD or len(villes) < MIN_VILLES:
        print(f"Réponse suspecte ({len(lieux)} lieux, {len(fiches)} fiches, {len(villes)} villes), ancien fichier gardé."); return 1
    photos = credits_photos([f["image"] for f in fiches.values()])
    resumes(fiches)
    lieux = rattacher(lieux, fiches, photos)
    for l in lieux:
        l["ville"] = ville_proche(l, villes)
    SORTIE.write_text(json.dumps({"maj": date.today().isoformat(), "lieux": sorted(lieux, key=lambda l: l["id"])},
                                 ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    nb_f = sum(1 for l in lieux if l.get("fiche"))
    print(f"{len(lieux)} lieux de prière ({sum(1 for l in lieux if l['type'] == 'salle')} salles), {nb_f} fiches Wikidata, "
          f"{sum(1 for l in lieux if (l.get('fiche') or {}).get('photo'))} photos, "
          f"{sum(len((l.get('fiche') or {}).get('resume', {})) for l in lieux)} résumés Wikipédia, "
          f"{sum(1 for l in lieux if l['ville'])} avec leur ville")
    return 0


if __name__ == "__main__":
    sys.exit(main())
