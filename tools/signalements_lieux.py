# -*- coding: utf-8 -*-
"""Lieux de prière signalés par les visiteurs → donnees/signales.js (workflow signalements.yml, toutes les 2 h de 8h à 22h).
Les signalements arrivent dans le MÊME Google Forms que les prix du site Prix des Eaux (aucun nouveau formulaire) :
seules les lignes « format = LIEU-PRIERE / LIEU-PRIERE-OK / LIEU-PRIERE-KO » sont lues ici (les robots des sites des eaux les ignorent).
Le tableau des réponses est publié en CSV (lecture seule). Panne de lecture : on ne touche à rien (code 0, message).
Usage : python tools/signalements_lieux.py"""
import csv, io, sys, unicodedata, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lieux_priere import ecrire  # noqa: E402

CSV_URL = ("https://docs.google.com/spreadsheets/d/e/2PACX-1vRI0naKTfS10a5cUe8Fz9lVDlvKaBtz7J56Yk"
           "Bo4oD-Ev2Al78sCw8zAGe3nyjCehhMdJ6c1C-yEXsn/pub?gid=287357703&single=true&output=csv")
UA = {"User-Agent": "mosquees-tunisie/1.0 (+https://mosquees.clicvia.com/)"}


def norm(s):
    s = unicodedata.normalize("NFD", s or "")
    return "".join(c for c in s if unicodedata.category(c) != "Mn").strip().lower()


def lire_reponses(texte):
    lignes = list(csv.reader(io.StringIO(texte)))
    col = {norm(x): i for i, x in enumerate(lignes[0])}
    out = []
    for l in lignes[1:]:
        g = lambda k: l[col[k]].strip() if col.get(k) is not None and col[k] < len(l) else ""
        out.append({k: g(k) for k in ("horodateur", "marque", "format", "lieu", "date")})
    return out


def main(lecteur=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    try:
        brut = lecteur() if lecteur else urllib.request.urlopen(urllib.request.Request(CSV_URL, headers=UA), timeout=60).read()
        reponses = lire_reponses(brut.decode("utf-8"))
    except Exception as e:      # tableau dépublié, Google en panne : rien n'est modifié
        print(f"! Tableau des signalements illisible ({e}) : rien n'est modifié.")
        return 0
    ecrire(reponses)
    return 0


if __name__ == "__main__":
    sys.exit(main())
