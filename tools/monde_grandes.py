# -*- coding: utf-8 -*-
"""Grandes mosquées du monde (page grandes-mosquees-du-monde/, demande d'Ahmed du 23/10/2026) : les mosquées les plus connues
du monde selon Wikidata (nombre d'articles Wikipédia), avec leur nom dans les 21 langues du site, leur pays, l'année de
construction (P571, la plus ancienne date), une photo (Wikimedia Commons), leur position et l'article Wikipédia de chaque langue.
Écrit donnees/monde_grandes.json (la construction du site n'utilise pas le réseau). Relancé avec le robot des données
(tous les 3 mois) ; à la main : python tools/monde_grandes.py"""
import json, os, re, sys, time, urllib.parse

ICI = os.path.dirname(os.path.abspath(__file__)); RACINE = os.path.dirname(ICI)
sys.path.insert(0, ICI)
from mosquees_donnees import http, vignette  # noqa: E402
from pages_nouvelles import LIEUX_SAINTS, PAS_MOSQUEES  # noqa: E402

LANGUES = ["fr", "ar", "en", "tr", "id", "ur", "de", "es", "it", "pt", "nl", "zh", "ja", "ko", "hi", "ru", "vi", "th", "tl", "sv", "ro"]
MINI_ARTICLES = 25          # au moins 25 articles Wikipédia : les mosquées vraiment connues
MAXI = 160
REQUETE = """SELECT ?item ?liens WHERE {
  { ?item wdt:P31 wd:Q32815 } UNION { ?item wdt:P31 wd:Q1454820 ; wdt:P140 wd:Q432 }
  ?item wikibase:sitelinks ?liens . FILTER(?liens >= %d)
} ORDER BY DESC(?liens) LIMIT %d"""


def entites(qids, props):
    out = {}
    for i in range(0, len(qids), 50):
        d = http("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({
            "action": "wbgetentities", "ids": "|".join(qids[i:i + 50]), "props": props, "format": "json",
            "languages": "|".join(LANGUES), "sitefilter": "|".join(l + "wiki" for l in LANGUES)}))
        out.update(d.get("entities", {}))
        time.sleep(0.5)
    return out


def valeurs(e, p):
    return [c["mainsnak"].get("datavalue", {}).get("value") for c in e.get("claims", {}).get(p, []) if c.get("rank") != "deprecated"]


def annee(e):
    ans = []
    for v in valeurs(e, "P571"):
        if isinstance(v, dict) and v.get("time"):
            m = re.match(r"([+-])(\d+)-", v["time"])
            if m and int(v.get("precision", 9)) >= 7:          # au moins le siècle
                a = int(m.group(2)) * (-1 if m.group(1) == "-" else 1)
                if int(v.get("precision", 9)) == 7:            # siècle : milieu du siècle
                    a = (a // 100) * 100 - 50 if a % 100 == 0 else (a // 100) * 100 + 50
                ans.append(a)
    return min(ans) if ans else None


def telecharger_vignettes(ms):
    import urllib.request
    dossier = os.path.join(RACINE, "assets", "monde")
    os.makedirs(dossier, exist_ok=True)
    garder = set()
    for x in ms:
        f = os.path.join(dossier, x["q"] + ".jpg")
        garder.add(x["q"] + ".jpg")
        if not os.path.exists(f) or x["photo"].get("source") != x["photo"]["url"]:
            for essai in range(4):
                try:
                    req = urllib.request.Request(x["photo"]["url"], headers={"User-Agent": "MosqueesTunisie/1.0 (https://mosquees.clicvia.com/)"})
                    data = urllib.request.urlopen(req, timeout=60).read()
                    open(f, "wb").write(data)
                    break
                except Exception:
                    time.sleep(5 * (essai + 1))
            time.sleep(0.4)
        if os.path.exists(f):
            x["photo"]["source"] = x["photo"]["url"]
            x["photo"]["fichier"] = "assets/monde/" + x["q"] + ".jpg"
    for n in os.listdir(dossier):                                  # photos de mosquées sorties de la liste : retirées
        if n not in garder:
            os.remove(os.path.join(dossier, n))


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    d = http("https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": REQUETE % (MINI_ARTICLES, MAXI * 2), "format": "json"}))
    vus, ordre = set(), []
    for b in d["results"]["bindings"]:
        q = b["item"]["value"].rsplit("/", 1)[1]
        if q not in vus:
            vus.add(q); ordre.append((q, int(b["liens"]["value"])))
    ordre = ordre[:MAXI]
    # toujours dans la liste : les mosquées qui ont des histoires sur notre site (ex. al-Qarawiyyin, Cordoue), même moins connues
    from pages_nouvelles import HISTOIRES_MONDE, QID_GROUPES
    for q in list(HISTOIRES_MONDE) + list(QID_GROUPES.values()):
        if q not in {x for x, _ in ordre}:
            e = entites([q], "sitelinks").get(q, {})
            ordre.append((q, len(e.get("sitelinks", {})) or 1))
    ordre.sort(key=lambda x: -x[1])
    ents = entites([q for q, _ in ordre], "labels|descriptions|sitelinks|claims")
    pays_q = sorted({v["id"] for e in ents.values() for v in valeurs(e, "P17")[:1] if isinstance(v, dict)})
    pays = {q: {l: x["value"] for l, x in e.get("labels", {}).items()} for q, e in entites(pays_q, "labels").items()}
    fichiers = {}
    sortie = []
    for q, n in ordre:
        e = ents.get(q, {})
        noms = {l: x["value"] for l, x in e.get("labels", {}).items() if l in LANGUES}
        mosquee = any(isinstance(v, dict) and v.get("id") == "Q32815" for v in valeurs(e, "P31"))
        if not (noms.get("en") or noms.get("fr")) or not (mosquee or q in LIEUX_SAINTS or q in HISTOIRES_MONDE) or q in PAS_MOSQUEES:
            continue                                   # pas une mosquée (mont du Temple, mausolée, monument…)
        p = next((v["id"] for v in valeurs(e, "P17") if isinstance(v, dict)), None)
        img = next((v for v in valeurs(e, "P18") if isinstance(v, str)), None)
        pos = next((v for v in valeurs(e, "P625") if isinstance(v, dict)), None)
        x = {"q": q, "n": n, "noms": noms, "pays": pays.get(p, {}), "an": annee(e),
             "desc": {l: v["value"] for l, v in e.get("descriptions", {}).items() if l in LANGUES},
             "wiki": {l: e["sitelinks"][l + "wiki"]["title"] for l in LANGUES if l + "wiki" in e.get("sitelinks", {})}}
        if pos:
            x["pos"] = [round(pos["latitude"], 5), round(pos["longitude"], 5)]
        if img:
            fichiers[img] = x
        sortie.append(x)
    # description : résumé (introduction) de l'article Wikipédia de chaque langue (demande d'Ahmed du 23/10/2026 : une
    # description pour chaque mosquée du monde) ; CC BY-SA 4.0, cité avec son lien sur la page
    for x in sortie:
        x["resume"] = {}
        for l, titre in x["wiki"].items():
            try:
                r = http(f"https://{l}.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(titre.replace(' ', '_'), safe='')}", delai=60)
                txt = re.sub(r"\s+", " ", r.get("extract", "")).strip()
                if len(txt) > 60:
                    x["resume"][l] = txt[:900]
            except Exception:
                pass
            time.sleep(0.1)
    # photos : vignette 330 px sur thumb.wikimedia.org, auteur et licence (licence libre exigée, sinon pas de photo)
    noms_f = list(fichiers)
    for i in range(0, len(noms_f), 40):
        r = http("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
            "action": "query", "titles": "|".join("File:" + f for f in noms_f[i:i + 40]), "prop": "imageinfo",
            "iiprop": "url|size|extmetadata", "format": "json"}))
        norm = {m["to"]: m["from"] for m in r["query"].get("normalized", [])}
        for pg in r["query"]["pages"].values():
            ii = (pg.get("imageinfo") or [{}])[0]; em = ii.get("extmetadata", {})
            lic = (em.get("LicenseShortName") or {}).get("value", "")
            if not ii.get("url") or not re.search(r"CC|Public domain|domaine public|PD", lic, re.I) or re.search(r"\bNC\b|\bND\b|fair use", lic, re.I):
                continue
            f = norm.get(pg["title"], pg["title"])[5:]
            x = fichiers.get(f) or fichiers.get(f.replace(" ", "_"))
            if not x:
                continue
            u = vignette(ii["url"], min(ii.get("width", 0), 330))
            if "thumb.wikimedia.org" not in u:
                continue
            x["photo"] = {"url": u, "page": ii.get("descriptionurl", ""), "licence": lic[:40],
                          "auteur": re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", (em.get("Artist") or {}).get("value", ""))).strip()[:80] or "Wikimedia Commons"}
        time.sleep(0.5)
    # vignettes gardées sur le site (assets/monde/<QID>.jpg) : Wikimedia refuse les demandes trop nombreuses d'une même machine
    # (robot des tests, 23/10/2026 : 3 photos « cassées » sur 128) ; une vignette déjà là n'est pas redemandée
    telecharger_vignettes([x for x in sortie if x.get("photo")])
    dest = os.path.join(RACINE, "donnees", "monde_grandes.json")
    open(dest, "w", encoding="utf-8", newline="\n").write(json.dumps({"maj": time.strftime("%Y-%m-%d"), "mosquees": sortie}, ensure_ascii=False, indent=0) + "\n")
    print(sum(1 for x in sortie if x["resume"]), "avec un résumé Wikipédia ;", len(sortie), "mosquées,", sum(1 for x in sortie if x.get("an") is not None), "avec une année,", sum(1 for x in sortie if x.get("photo")), "avec photo ->", dest)


if __name__ == "__main__":
    main()
