# -*- coding: utf-8 -*-
"""Mosquées et salles de prière signalées par les visiteurs (site Mosquées en Tunisie, 09/10/2026) — appelé par
tools/signalements_lieux.py toutes les 2 h : publication AUTOMATIQUE avec garde-fous (même logique que tools/points_eau.py du site
Points d'eau Tunisie).

Même Google Forms que les prix du site Prix des Eaux (aucun nouveau formulaire), avec un FORMAT PROPRE à ce site :
  - nouveau lieu   : format = LIEU-PRIERE,    marque = « type|nom » (type = mosquee ou salle),  lieu = « lat,lon|jeton »
  - c'est vrai     : format = LIEU-PRIERE-OK, marque = id du lieu,                            lieu = « |jeton »
  - n'existe plus  : format = LIEU-PRIERE-KO, marque = id du lieu,                            lieu = « |jeton »
  (jeton = identifiant anonyme du navigateur « lp:… » : une voix par navigateur et par lieu, la dernière compte)
Le robot des prix (site Prix des Eaux) et celui des points d'eau ignorent ce format.

Garde-fous (un robot ne peut pas prouver qu'une mosquée existe, il écarte l'invraisemblable) :
  - type connu, position EN TUNISIE, jeton présent ;
  - nom nettoyé : 60 caractères, sans lien internet ni numéro de téléphone (pas de publicité, pas de données personnelles) ;
  - 10 lieux au plus par navigateur ;
  - un lieu signalé à moins de 40 m d'un lieu connu (OpenStreetMap ou déjà signalé) = une confirmation de celui-ci (pas de doublon) ;
  - statut : « signalé » (1 personne), « confirmé » (2 personnes ou plus) ; retiré de la carte si au moins 2 personnes disent
    « n'existe plus » et qu'elles sont plus nombreuses que les confirmations (3 pour un lieu OpenStreetMap / Wikidata).
Sortie : donnees/signales.js (window.MOSQUEES_SIGNALES : points des visiteurs, votes sur les lieux connus, lieux retirés)."""
import hashlib, json, math, re
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "donnees" / "mosquees.json"
SORTIE = ROOT / "donnees" / "signales.js"
TYPES = ("mosquee", "salle")
FORMATS = ("LIEU-PRIERE", "LIEU-PRIERE-OK", "LIEU-PRIERE-KO")
TUNISIE = (30.1, 37.6, 7.4, 11.7)          # sud, nord, ouest, est
MAX_PAR_JETON = 10
RAYON_M = 40


def distance_m(a, b):
    r = 6371000
    p1, p2 = math.radians(a["lat"]), math.radians(b["lat"])
    dp, dl = p2 - p1, math.radians(b["lon"] - a["lon"])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def nettoyer_nom(s):
    s = re.sub(r"https?://\S+|www\.\S+|\S+@\S+", "", s or "")
    s = re.sub(r"(?:\+?216)?[\s.-]*\d(?:[\s.-]*\d){5,}", "", s)        # numéros de téléphone (6 chiffres ou plus)
    s = re.sub(r"[<>\"`|]", "", s)
    return re.sub(r"\s+", " ", s).strip()[:60]


def lire_lieu(r):
    """Ligne LIEU-PRIERE → dict, ou (None, raison)."""
    t, _, nom = (r.get("marque") or "").partition("|")
    pos, _, jeton = (r.get("lieu") or "").partition("|")
    t = t.strip().lower()
    if t not in TYPES:
        return None, f"type inconnu « {t} »"
    if not re.fullmatch(r"lp:[a-z0-9]{6,40}", jeton.strip()):
        return None, "jeton absent"
    m = re.fullmatch(r"\s*(-?\d{1,2}\.\d+)\s*,\s*(-?\d{1,2}\.\d+)\s*", pos)
    if not m:
        return None, "position illisible"
    lat, lon = float(m.group(1)), float(m.group(2))
    if not (TUNISIE[0] <= lat <= TUNISIE[1] and TUNISIE[2] <= lon <= TUNISIE[3]):
        return None, "position hors de Tunisie"
    pid = "sig-" + hashlib.sha1(f"{t}|{lat:.5f}|{lon:.5f}".encode()).hexdigest()[:10]
    return {"id": pid, "type": t, "lat": round(lat, 6), "lon": round(lon, 6), "nom": nettoyer_nom(nom),
            "date": (r.get("date") or r.get("horodateur") or "")[:10], "jeton": jeton.strip()}, None


def calculer(reponses, connus):
    """reponses : lignes du tableau ; connus : lieux OpenStreetMap / Wikidata [{id, lat, lon}].
    Renvoie (points des visiteurs, votes {id: [ok, ko]} sur les lieux connus, ids retirés, rejets)."""
    lieux = {c["id"]: {"id": c["id"], "lat": c["lat"], "lon": c["lon"], "connu": True, "ok": set(), "ko": set()} for c in connus}
    grille = {}
    for c in lieux.values():
        grille.setdefault((round(c["lat"], 2), round(c["lon"], 2)), []).append(c)

    def proche(p):
        k = (round(p["lat"], 2), round(p["lon"], 2))
        for dla in (-0.01, 0, 0.01):
            for dlo in (-0.01, 0, 0.01):
                for q in grille.get((round(k[0] + dla, 2), round(k[1] + dlo, 2)), []):
                    if distance_m(p, q) <= RAYON_M:
                        return q
        return None

    par_jeton, rejets = {}, []
    for r in reponses:                                   # 1. nouveaux lieux, dans l'ordre d'arrivée
        if (r.get("format") or "").strip().upper() != "LIEU-PRIERE":
            continue
        p, raison = lire_lieu(r)
        if not p:
            rejets.append(raison); continue
        j = p.pop("jeton")
        q = proche(p)
        if q:
            q["ok"].add(j); q["ko"].discard(j)
            if not q.get("connu") and not q.get("nom") and p["nom"]:
                q["nom"] = p["nom"]
            continue
        if par_jeton.get(j, 0) >= MAX_PAR_JETON:
            rejets.append("trop de lieux pour ce navigateur"); continue
        par_jeton[j] = par_jeton.get(j, 0) + 1
        nouveau = dict(p, ok={j}, ko=set())
        lieux[p["id"]] = nouveau
        grille.setdefault((round(p["lat"], 2), round(p["lon"], 2)), []).append(nouveau)
    for r in reponses:                                   # 2. « c'est vrai » / « n'existe plus » (la dernière voix compte)
        f = (r.get("format") or "").strip().upper()
        if f not in ("LIEU-PRIERE-OK", "LIEU-PRIERE-KO"):
            continue
        q = lieux.get((r.get("marque") or "").strip())
        j = (r.get("lieu") or "").partition("|")[2].strip()
        if not q or not re.fullmatch(r"lp:[a-z0-9]{6,40}", j):
            continue
        (q["ok"] if f.endswith("-OK") else q["ko"]).add(j)
        (q["ko"] if f.endswith("-OK") else q["ok"]).discard(j)
    points, votes, retires = [], {}, []                  # 3. statut
    for q in lieux.values():
        ok, ko = len(q["ok"]), len(q["ko"])
        seuil = 3 if q.get("connu") else 2
        if ko >= seuil and ko > ok:
            retires.append(q["id"]); continue
        if q.get("connu"):
            if ok or ko:
                votes[q["id"]] = [ok, ko]
            continue
        points.append({"id": q["id"], "type": q["type"], "lat": q["lat"], "lon": q["lon"], "nom": q.get("nom", ""), "date": q["date"],
                       "ok": ok, "ko": ko, "statut": "confirme" if ok >= 2 else "signale"})
    return sorted(points, key=lambda p: p["id"]), votes, sorted(retires), rejets


# ---------- Prière du vendredi et lectures du Coran (24/11/2026, demande d'Ahmed) ----------
# Même Google Forms, format commençant par « LIEU-PRIERE » (le robot du site Prix des Eaux ignore tout ce qui commence ainsi) :
#   - information : format = LIEU-PRIERE-INFO,    marque = « id du lieu|clé|valeur », lieu = « |jeton »
#   - c'est vrai  : format = LIEU-PRIERE-INFO-OK, même marque ;  n'est plus vrai : LIEU-PRIERE-INFO-KO
# Valeurs choisies dans une LISTE (aucun texte libre) ; une voix par navigateur, par lieu et par clé (la dernière compte).
# Statut : « confirmé » (2 voix ou plus), « signalé » (1) ; une valeur est écartée si au moins 2 personnes disent
# « n'est plus vrai » et qu'elles sont plus nombreuses que les confirmations. Une source publique (donnees/infos_sources.json)
# compte comme une confirmation de départ, avec son lien.
FORMATS_INFO = ("LIEU-PRIERE-INFO", "LIEU-PRIERE-INFO-OK", "LIEU-PRIERE-INFO-KO")
SOURCES = ROOT / "donnees" / "infos_sources.json"
JOURS = ("lun", "mar", "mer", "jeu", "ven", "sam", "dim")
PRIERES = ("fajr", "dhohr", "asr", "maghreb", "icha")
MAX_INFOS_PAR_JETON = 30
AUJOURDHUI = None          # tests : date du jour imposée (sinon date.today())


def valeur_valide(cle, v):
    v = (v or "").strip().lower()
    if cle == "joumoua":
        if v in ("13h00", "asr", "non"):
            return v
        m = re.fullmatch(r"(\d{1,2})[:h](\d{2})", v)
        if m and 11 <= int(m.group(1)) <= 16 and int(m.group(2)) < 60 and int(m.group(2)) % 5 == 0:
            return f"{int(m.group(1)):02d}:{m.group(2)}"
        return None
    if cle == "coran-jour":
        return v if v in PRIERES + ("non",) else None
    if cle == "coran-mois":
        return v if v == "non" or re.fullmatch(r"(%s)(-premier|-dernier)?" % "|".join(JOURS), v) else None
    if cle == "coran-date":      # khatma à une date précise (24/11/2026) : de aujourd'hui à 2 ans ; une date passée disparaît seule
        try:
            d = date.fromisoformat(v)
        except ValueError:
            return None
        auj = AUJOURDHUI or date.today()
        return v if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v) and auj <= d <= auj + timedelta(days=731) else None
    return None


def calculer_infos(reponses, ids_connus, sources=()):
    """Renvoie ({id du lieu: {clé: [valeur, statut, nombre de confirmations, lien de la source ou ""]}}, rejets)."""
    voix, rejets, par_jeton = {}, [], {}            # (lieu, clé) -> {jeton: (valeur, +1 / -1)}
    for s in sources:
        v = valeur_valide(s.get("cle"), s.get("valeur"))
        if v and s.get("lieu") in ids_connus:
            voix.setdefault((s["lieu"], s["cle"]), {})["source:" + s["lieu"]] = (v, 1, s.get("source", ""))
    for r in reponses:
        f = (r.get("format") or "").strip().upper()
        if f not in FORMATS_INFO:
            continue
        lid, _, reste = (r.get("marque") or "").strip().partition("|")
        cle, _, val = reste.partition("|")
        j = (r.get("lieu") or "").partition("|")[2].strip()
        if not re.fullmatch(r"lp:[a-z0-9]{6,40}", j):
            rejets.append("jeton absent"); continue
        if lid not in ids_connus:
            rejets.append("lieu inconnu"); continue
        v = valeur_valide(cle, val)
        if not v:
            rejets.append(f"valeur refusée « {cle}|{val[:20]} »"); continue
        if f == "LIEU-PRIERE-INFO":
            if (lid, cle) not in {k for k, d in voix.items() if j in d}:
                if par_jeton.get(j, 0) >= MAX_INFOS_PAR_JETON:
                    rejets.append("trop d'informations pour ce navigateur"); continue
                par_jeton[j] = par_jeton.get(j, 0) + 1
            voix.setdefault((lid, cle), {})[j] = (v, 1, "")
        else:
            voix.setdefault((lid, cle), {})[j] = (v, 1 if f.endswith("-OK") else -1, "")
    infos = {}
    for (lid, cle), d in voix.items():
        par_valeur = {}
        for v, s, src in d.values():
            pv = par_valeur.setdefault(v, {"ok": 0, "ko": 0, "src": ""})
            pv["ok" if s > 0 else "ko"] += 1
            pv["src"] = pv["src"] or src
        garde = {v: x for v, x in par_valeur.items() if x["ok"] and not (x["ko"] >= 2 and x["ko"] > x["ok"])}
        if not garde:
            continue
        v = max(garde, key=lambda k: (garde[k]["ok"] - garde[k]["ko"], garde[k]["ok"]))
        x = garde[v]
        infos.setdefault(lid, {})[cle] = [v, "confirme" if x["ok"] >= 2 else ("source" if x["src"] else "signale"), x["ok"], x["src"]]
    return infos, rejets


def sources():
    try:
        return json.loads(SOURCES.read_text(encoding="utf-8")).get("infos", [])
    except (FileNotFoundError, ValueError):
        return []


def connus():
    if not BASE.exists():
        return []
    d = json.loads(BASE.read_text(encoding="utf-8"))
    return [{"id": l["id"], "lat": l["lat"], "lon": l["lon"]} for l in d.get("lieux", [])]


JOURS_RAFRAICHIR = 7   # « maj » sert de date de référence (30 derniers jours) et de battement de cœur : rafraîchie au moins chaque semaine


def doit_ecrire(texte, aujourdhui=None):
    """Audit des robots du 10/10/2026 : on ne réécrit le fichier (donc pas de commit ni de publication) que si son contenu
    change AUTREMENT que par la date « maj », ou si cette date a plus de JOURS_RAFRAICHIR jours."""
    try:
        ancien = SORTIE.read_text(encoding="utf-8")
    except FileNotFoundError:
        return True
    motif = re.compile(r'"maj":"([^"]*)"')
    if motif.sub('"maj":""', ancien, count=1) != motif.sub('"maj":""', texte, count=1):
        return True
    m = motif.search(ancien)
    try:
        vieux = date.fromisoformat(m.group(1)[:10])
    except (AttributeError, ValueError):
        return True
    return ((aujourdhui or date.today()) - vieux).days >= JOURS_RAFRAICHIR


def ecrire(reponses, maintenant=None):
    base = connus()
    points, votes, retires, rejets = calculer(reponses, base)
    infos, rejets_i = calculer_infos(reponses, {c["id"] for c in base} | {p["id"] for p in points}, sources())
    infos = {k: v for k, v in infos.items() if k not in retires}
    texte = ("// GÉNÉRÉ par tools/lieux_priere.py (via signalements_lieux.py, toutes les 2 h) — lieux signalés par les visiteurs\n"
                      "window.MOSQUEES_SIGNALES = " + json.dumps({"maj": maintenant or datetime.now().isoformat(timespec="minutes"),
                                                                  "points": points, "votes": votes, "retires": retires, "infos": infos},
                                                                 ensure_ascii=False, separators=(",", ":")) + ";\n")
    if doit_ecrire(texte):
        SORTIE.write_text(texte, encoding="utf-8", newline="\n")
    else:
        print("Aucun changement : fichier non réécrit (pas de commit).")
    print(f"Lieux de prière signalés : {len(points)} publiés, {len(votes)} lieux connus avec des votes, {len(retires)} retirés, {len(rejets)} rejet(s)")
    print(f"Prière du vendredi / Coran : {sum(len(v) for v in infos.values())} information(s) sur {len(infos)} lieu(x), {len(rejets_i)} rejet(s)")
    return points, votes, retires
