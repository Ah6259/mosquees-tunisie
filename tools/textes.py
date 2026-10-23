# -*- coding: utf-8 -*-
"""Textes des parties ajoutées le 23/10/2026 (demande d'Ahmed) : recherche des grandes mosquées du monde, page « Le rôle de la
mosquée », page « Construire une mosquée », histoires des mosquées. Une seule méthode, en 21 langues :
  tools/textes/base/<nom>.json : { clé: {"fr": …, "ar": …, "en": …} }   (écrit par nous ; le français est la référence)
  tools/textes/<langue>.json   : { "<nom>/<clé>": traduction }           (les 18 autres langues, une ligne par texte)
D(nom, clé) rend le texte dans les 21 langues ; la construction S'ARRÊTE si une traduction manque (jamais de page à moitié
traduite). Changer un texte français = changer aussi sa traduction dans les 18 fichiers (ou changer la clé pour s'en souvenir).
Traductions écrites par Claude : à faire relire par quelqu'un dont c'est la langue, comme le reste du site.
Les textes du Coran ne sont JAMAIS traduits par nous : on montre l'arabe et on renvoie à la traduction officielle (QuranEnc)."""
import json, os

ICI = os.path.dirname(os.path.abspath(__file__))
DOSSIER = os.path.join(ICI, "textes")
LANGUES = ["fr", "ar", "en", "tr", "id", "ur", "de", "es", "it", "pt", "nl", "zh", "ja", "ko", "hi", "ru", "vi", "th", "tl", "sv", "ro"]
AUTRES = LANGUES[3:]
_BASE, _TRAD = {}, {}


def charger():
    if _BASE:
        return
    for f in sorted(os.listdir(os.path.join(DOSSIER, "base"))):
        if f.endswith(".json"):
            _BASE[f[:-5]] = json.load(open(os.path.join(DOSSIER, "base", f), encoding="utf-8"))
    for l in AUTRES:
        p = os.path.join(DOSSIER, l + ".json")
        _TRAD[l] = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


def cles(nom):
    charger()
    return list(_BASE[nom])


def D(nom, cle):
    """Le texte « nom/clé » dans les 21 langues ({langue: texte})."""
    charger()
    b = _BASE[nom][cle]
    out = {l: b[l] for l in ("fr", "ar", "en")}
    for l in AUTRES:
        t = _TRAD[l].get(f"{nom}/{cle}")
        if (not t or not str(t).strip()) and os.environ.get("MOSQUEES_BROUILLON"):
            t = b["en"]                      # brouillon pour regarder une page avant les traductions : JAMAIS publié
        if not t or not str(t).strip():
            raise SystemExit(f"tools/textes/{l}.json : pas de traduction pour « {nom}/{cle} » ({b['fr'][:60]})")
        out[l] = t
    return out


def manquants():
    """[(langue, « nom/clé »)] : traductions absentes (pour l'outil de contrôle et les tests)."""
    charger()
    return [(l, f"{n}/{c}") for l in AUTRES for n in _BASE for c in _BASE[n] if not str(_TRAD[l].get(f"{n}/{c}", "")).strip()]


def en_trop():
    """Traductions dont la clé n'existe plus dans tools/textes/base/ (texte retiré ou renommé)."""
    charger()
    toutes = {f"{n}/{c}" for n in _BASE for c in _BASE[n]}
    return [(l, k) for l in AUTRES for k in _TRAD[l] if k not in toutes]


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    m, t = manquants(), en_trop()
    print(f"{sum(len(v) for v in (_BASE or {}).values())} textes, {len(m)} traduction(s) manquante(s), {len(t)} en trop")
    for x in (m + t)[:30]:
        print(" ", *x)
    sys.exit(1 if m or t else 0)
