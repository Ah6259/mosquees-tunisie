# -*- coding: utf-8 -*-
"""Les 13 langues ajoutées le 13/10/2026 : italien, portugais, néerlandais, chinois, japonais, coréen, hindi, puis russe,
vietnamien, thaï, filipino, suédois, roumain (mêmes langues que nos sites The Message et Points d'eau). Une seule méthode pour tout (interface ET textes des grandes mosquées) :
  tools/langues_plus/_francais.json : la liste des textes français (« ui » = clés de assets/langues.js ; « contenu » = textes
                                      de tools/contenu_grandes_*.py et noms des villes), dans l'ordre ;
  tools/langues_plus/<langue>.txt   : une ligne « numéro<TAB>traduction » par texte, même ordre.
Le verset 9:18 (ligne 51) n'est PAS traduit par nous : c'est la traduction officielle de QuranEnc.com dans chaque langue
(italian_rwwad, portuguese_nasr, dutch_center, chinese_makin, japanese_saeedsato, korean_hamid, hindi_omari, russian_rwwad, vietnamese_rwwad, thai_rwwad, tagalog_rwwad, swedish_rwwad, romanian_project), nom à la ligne 52.
Ajouter un texte français : l'ajouter à la fin de la bonne liste de _francais.json et une ligne dans CHAQUE <langue>.txt
(tools/construire.py s'arrête si une traduction manque). Traductions écrites par Claude : à faire relire par quelqu'un dont
c'est la langue."""
import json, os

ICI = os.path.dirname(os.path.abspath(__file__))
PLUS = ["it", "pt", "nl", "zh", "ja", "ko", "hi", "ru", "vi", "th", "tl", "sv", "ro"]


def charger():
    """({langue: {français: traduction}}, textes d'interface). Arrêt si un fichier est incomplet."""
    d = json.load(open(os.path.join(ICI, "langues_plus", "_francais.json"), encoding="utf-8"))
    fr = d["ui"] + d["contenu"]
    out = {}
    for l in PLUS:
        lignes = [x for x in open(os.path.join(ICI, "langues_plus", l + ".txt"), encoding="utf-8").read().split("\n") if x.strip()]
        if len(lignes) != len(fr):
            raise SystemExit(f"langues_plus/{l}.txt : {len(lignes)} lignes pour {len(fr)} textes français")
        out[l] = {}
        for i, x in enumerate(lignes):
            n, _, tr = x.partition("\t")
            if n != str(i) or not tr.strip():
                raise SystemExit(f"langues_plus/{l}.txt : ligne {i} absente ou vide")
            out[l][fr[i]] = tr
    return out, d["ui"]
