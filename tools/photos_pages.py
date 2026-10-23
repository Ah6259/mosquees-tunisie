# -*- coding: utf-8 -*-
"""Crédits (auteur, licence) et vignettes des photos des pages ajoutées le 23/10/2026 (tools/pages_nouvelles.py), lus sur
Wikimedia Commons et gardés dans donnees/photos_pages.json : la construction (tools/construire.py) n'utilise pas le réseau.
Licence libre exigée (CC, domaine public) : une photo refusée arrête l'outil. À relancer après tout ajout de photo :
  python tools/photos_pages.py"""
import json, os, sys

ICI = os.path.dirname(os.path.abspath(__file__)); RACINE = os.path.dirname(ICI)
sys.path.insert(0, ICI)
from mosquees_donnees import credits_photos  # noqa: E402
import pages_nouvelles as PN  # noqa: E402


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    fichiers = [f.replace("_", " ") for f in PN.fichiers_photos()]
    c = credits_photos(fichiers)
    manque = [f for f in fichiers if f not in c]
    if manque:
        raise SystemExit("Photos introuvables ou licence non libre : " + " | ".join(manque))
    dest = os.path.join(RACINE, "donnees", "photos_pages.json")
    open(dest, "w", encoding="utf-8", newline="\n").write(json.dumps(c, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print(len(c), "photos ->", dest)


if __name__ == "__main__":
    main()
