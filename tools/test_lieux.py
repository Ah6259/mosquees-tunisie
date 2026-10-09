# -*- coding: utf-8 -*-
"""Tests du robot des lieux de prière signalés (tools/lieux_priere.py, signalements_lieux.py) et du robot des données
(tools/mosquees_donnees.py : pannes) — sans réseau, données factices.   python tools/test_lieux.py"""
import json, os, sys, tempfile
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lieux_priere as P  # noqa: E402
import signalements_lieux as S  # noqa: E402
import mosquees_donnees as M  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
erreurs = total = 0


def check(desc, ok):
    global erreurs, total
    total += 1
    print(("OK   " if ok else "FAIL ") + desc)
    if not ok:
        erreurs += 1


def lieu(t, nom, lat, lon, j, d="2026-10-09"):
    return {"format": "LIEU-PRIERE", "marque": f"{t}|{nom}", "lieu": f"{lat},{lon}|{j}", "date": d}


def voix(f, pid, j):
    return {"format": f, "marque": pid, "lieu": f"|{j}", "date": "2026-10-09"}


OSM = [{"id": "osm-n1", "lat": 36.7972, "lon": 10.1711}]          # la Zitouna (factice)
J = ["lp:aaaaaa1", "lp:bbbbbb2", "lp:cccccc3", "lp:dddddd4"]

# 1. une salle de prière signalée à Sfax → publiée « signalé », nom nettoyé
pts, votes, ret, rej = P.calculer([lieu("salle", "Salle de prière gare, appelez 98 765 432 www.pub.tn", 34.7406, 10.7603, J[0])], OSM)
check("salle de prière signalée à Sfax : publiée, type « salle », statut « signalé »", len(pts) == 1 and pts[0]["type"] == "salle" and pts[0]["statut"] == "signale")
check("nom nettoyé : sans numéro de téléphone ni lien", pts and "98" not in pts[0]["nom"] and "www" not in pts[0]["nom"] and pts[0]["nom"].startswith("Salle de prière gare"))
check("le lieu OpenStreetMap n'est ni retiré ni compté comme voté", not ret and not votes)

# 2. rejets : hors de Tunisie, type inconnu, sans jeton, position illisible, jeton au mauvais format (celui des points d'eau)
pts, votes, ret, rej = P.calculer([lieu("mosquee", "x", 48.85, 2.35, J[0]), lieu("eglise", "x", 36.8, 10.1, J[0]),
                                   lieu("mosquee", "x", 36.8, 10.1, "sans-jeton"), {"format": "LIEU-PRIERE", "marque": "mosquee|x", "lieu": "abc|" + J[0]},
                                   lieu("mosquee", "x", 36.8, 10.1, "pt:abcdef1")], [])
check(f"rejetés : Paris (hors Tunisie), type inconnu, sans jeton, position illisible, jeton « pt: » ({len(rej)} rejets)", len(pts) == 0 and len(rej) == 5)

# 3. formats des autres sites ignorés (POINT des points d'eau, lignes de prix sans format)
pts, votes, ret, rej = P.calculer([{"format": "POINT", "marque": "source|Ain", "lieu": "36.8,10.1|pt:abcdef1"},
                                   {"format": "Pack 6 x 1,5 L", "marque": "Safia", "lieu": "Tunis", "date": "2026-10-09"}], OSM)
check("lignes POINT (points d'eau) et lignes de prix ignorées", not pts and not rej and not votes)

# 4. doublon à moins de 40 m = confirmation ; 2 personnes → « confirmé »
pid = P.lire_lieu(lieu("mosquee", "Jamaa", 35.5, 11.0, J[0]))[0]["id"]
pts, *_ = P.calculer([lieu("mosquee", "Jamaa", 35.5, 11.0, J[0]), lieu("mosquee", "", 35.50015, 11.00015, J[1])], [])
check("même mosquée signalée à ~20 m par un 2e visiteur : un seul lieu, « confirmé »", len(pts) == 1 and pts[0]["id"] == pid and pts[0]["statut"] == "confirme" and pts[0]["ok"] == 2)
pts, *_ = P.calculer([lieu("mosquee", "A", 35.5, 11.0, J[0]), lieu("mosquee", "B", 35.501, 11.0, J[1])], [])
check("une autre mosquée à ~110 m : deux lieux distincts", len(pts) == 2)
pts, votes, *_ = P.calculer([lieu("mosquee", "Zitouna", 36.79725, 10.17112, J[0])], OSM)
check("signaler un lieu déjà sur la carte (à ~6 m) = une confirmation de celui-ci, pas de doublon", not pts and votes.get("osm-n1") == [1, 0])

# 5. « n'existe plus »
pts, *_ = P.calculer([lieu("mosquee", "A", 35.5, 11.0, J[0]), voix("LIEU-PRIERE-KO", pid, J[1]), voix("LIEU-PRIERE-KO", pid, J[2])], [])
check("lieu signalé puis 2 « n'existe plus » (plus que les confirmations) : retiré", not pts)
pts, votes, ret, _ = P.calculer([voix("LIEU-PRIERE-KO", "osm-n1", J[0]), voix("LIEU-PRIERE-KO", "osm-n1", J[1])], OSM)
check("lieu OpenStreetMap : 2 « n'existe plus » ne suffisent pas (il en faut 3)", not ret and votes.get("osm-n1") == [0, 2])
pts, votes, ret, _ = P.calculer([voix("LIEU-PRIERE-KO", "osm-n1", J[0]), voix("LIEU-PRIERE-KO", "osm-n1", J[1]), voix("LIEU-PRIERE-KO", "osm-n1", J[2])], OSM)
check("lieu OpenStreetMap : 3 « n'existe plus » → retiré de la carte", ret == ["osm-n1"])
pts, votes, ret, _ = P.calculer([voix("LIEU-PRIERE-KO", "osm-n1", J[0]), voix("LIEU-PRIERE-OK", "osm-n1", J[0])], OSM)
check("la dernière voix d'un navigateur compte (KO puis OK = 1 confirmation)", votes.get("osm-n1") == [1, 0])

# 6. 10 lieux au plus par navigateur
pts, _, _, rej = P.calculer([lieu("mosquee", f"M{i}", 35.0 + i * 0.01, 10.0, J[0]) for i in range(12)], [])
check("11e et 12e lieux du même navigateur refusés", len(pts) == 10 and rej.count("trop de lieux pour ce navigateur") == 2)

# 7. lecture du tableau : CSV publié (colonnes avec accents), panne = rien modifié
csv_txt = "Horodateur,Marque,Format,Lieu,Date\n09/10/2026 10:00:00,salle|Gare,LIEU-PRIERE,\"36.80000,10.18000|lp:zzzzzz9\",2026-10-09\n"
with tempfile.TemporaryDirectory() as tmp:
    vieux = P.SORTIE
    P.SORTIE = Path(tmp) / "signales.js"
    P.SORTIE.write_text("ANCIEN", encoding="utf-8")
    S.main(lecteur=lambda: (_ for _ in ()).throw(OSError("réseau coupé")))
    check("panne de lecture du tableau : le fichier publié n'est pas touché", P.SORTIE.read_text(encoding="utf-8") == "ANCIEN")
    S.main(lecteur=lambda: csv_txt.encode("utf-8"))
    t = P.SORTIE.read_text(encoding="utf-8")
    check("tableau lu : signales.js écrit (window.MOSQUEES_SIGNALES) avec la salle de la gare", t.startswith("// GÉNÉRÉ") and "window.MOSQUEES_SIGNALES" in t and '"nom":"Gare"' in t)
    P.SORTIE = vieux

# 8. robot des données (tools/mosquees_donnees.py) : pannes → ancien fichier gardé, code 1
with tempfile.TemporaryDirectory() as tmp:
    vieux_sortie, vieux_osm, vieux_villes, vieux_wd = M.SORTIE, M.lire_osm, M.lire_villes, M.lire_wikidata
    M.SORTIE = Path(tmp) / "mosquees.json"
    M.SORTIE.write_text('{"ancien": true}', encoding="utf-8")
    M.lire_osm = lambda: (_ for _ in ()).throw(RuntimeError("Overpass indisponible"))
    code = M.main()
    check("robot des données : OpenStreetMap en panne → code 1, ancien fichier gardé", code == 1 and json.loads(M.SORTIE.read_text(encoding="utf-8")) == {"ancien": True})
    M.lire_osm = lambda: [{"id": "osm-n1", "lat": 36.8, "lon": 10.1, "type": "mosquee", "noms": {}, "ville": {}, "wikidata": "", "rite": ""}] * 20
    M.lire_villes = lambda: [{"lat": 36.8, "lon": 10.1, "rang": 3, "fr": "Tunis", "ar": "تونس"}] * 600
    M.lire_wikidata = lambda: {}
    code = M.main()
    check("robot des données : réponse suspecte (20 lieux, 0 fiche) → code 1, ancien fichier gardé", code == 1 and json.loads(M.SORTIE.read_text(encoding="utf-8")) == {"ancien": True})
    M.SORTIE, M.lire_osm, M.lire_villes, M.lire_wikidata = vieux_sortie, vieux_osm, vieux_villes, vieux_wd
check("robot des données : 5 serveurs OpenStreetMap, erreurs cachées lues (remark), minimums", len(M.SERVEURS) == 5 and M.MIN_OSM >= 1000 and M.MIN_WD >= 50)
check("robot des données : noms génériques écartés (« Mosque », « مسجد »), vrais noms gardés", M.generique("Mosque") and M.generique("مسجد") and not M.generique("Mosquée Zitouna"))

# 9. les données publiées : minimums (jamais des nombres exacts : le robot peut en ajouter)
d = json.loads((P.ROOT / "donnees" / "mosquees.json").read_text(encoding="utf-8"))
L = d["lieux"]
check(f"données : au moins 1 500 lieux ({len(L)}), positions en Tunisie, au moins 80 fiches Wikidata", len(L) >= 1500
      and all(30 < x["lat"] < 37.6 and 7.4 < x["lon"] < 11.7 for x in L) and sum(1 for x in L if x.get("fiche")) >= 80)
check("données : chaque photo a une licence libre et un auteur", all(re_ok for re_ok in (
    bool(x["fiche"]["photo"]["licence"]) and bool(x["fiche"]["photo"]["auteur"]) and "NC" not in x["fiche"]["photo"]["licence"]
    for x in L if x.get("fiche") and x["fiche"].get("photo"))))

print(f"\n{'TOUT PASSE' if not erreurs else str(erreurs) + ' PROBLÈME(S)'} ({total} vérifications)")
sys.exit(1 if erreurs else 0)
