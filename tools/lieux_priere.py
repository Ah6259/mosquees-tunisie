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
from datetime import datetime
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


def connus():
    if not BASE.exists():
        return []
    d = json.loads(BASE.read_text(encoding="utf-8"))
    return [{"id": l["id"], "lat": l["lat"], "lon": l["lon"]} for l in d.get("lieux", [])]


def ecrire(reponses, maintenant=None):
    points, votes, retires, rejets = calculer(reponses, connus())
    SORTIE.write_text("// GÉNÉRÉ par tools/lieux_priere.py (via signalements_lieux.py, toutes les 2 h) — lieux signalés par les visiteurs\n"
                      "window.MOSQUEES_SIGNALES = " + json.dumps({"maj": maintenant or datetime.now().isoformat(timespec="minutes"),
                                                                  "points": points, "votes": votes, "retires": retires},
                                                                 ensure_ascii=False, separators=(",", ":")) + ";\n",
                      encoding="utf-8", newline="\n")
    print(f"Lieux de prière signalés : {len(points)} publiés, {len(votes)} lieux connus avec des votes, {len(retires)} retirés, {len(rejets)} rejet(s)")
    return points, votes, retires
