# -*- coding: utf-8 -*-
"""Ajoute des textes d'INTERFACE (ceux des scripts : L2(), T(), et des pages écrites à la main) dans les 18 langues :
assets/langues.js (tr, id, ur, de, es) et tools/langues_plus/ (_francais.json « ui », _francais.txt et les 13 .txt, renumérotés).
Entrée : un fichier JSON { "texte français exact": { "tr": "…", "id": "…", …, "ro": "…" } } (les 18 langues obligatoires).
  python tools/ajouter_ui.py textes.json
Un texte déjà présent est remplacé (traduction corrigée)."""
import json, os, re, sys

ICI = os.path.dirname(os.path.abspath(__file__)); RACINE = os.path.dirname(ICI)
L5 = ["tr", "id", "ur", "de", "es"]
L13 = ["it", "pt", "nl", "zh", "ja", "ko", "hi", "ru", "vi", "th", "tl", "sv", "ro"]


def main(chemin):
    textes = json.load(open(chemin, encoding="utf-8"))
    for fr, d in textes.items():
        manque = [l for l in L5 + L13 if not str(d.get(l, "")).strip()]
        if manque:
            raise SystemExit(f"« {fr[:50]} » : pas de traduction en {', '.join(manque)}")
    # 1) assets/langues.js
    p = os.path.join(RACINE, "assets", "langues.js"); t = open(p, encoding="utf-8").read()
    for l in L5:
        m = re.search(r"window\.TRADUCTIONS\.%s = Object\.assign\(window\.TRADUCTIONS\.%s \|\| \{\}, \{\n(.*?)\n\}\);" % (l, l), t, re.S)
        corps = m.group(1)
        for fr, d in textes.items():
            k = json.dumps(fr, ensure_ascii=False)
            ligne = f' {k}: {json.dumps(d[l], ensure_ascii=False)}'
            if (k + ":") in corps:
                corps = re.sub(r"^ " + re.escape(k) + r":.*?(,?)$", lambda x: ligne + x.group(1), corps, count=1, flags=re.M)
            else:
                corps = corps.rstrip().rstrip(",") + ",\n" + ligne
        t = t[:m.start(1)] + corps + t[m.end(1):]
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    # 2) tools/langues_plus : à la fin de « ui » (les numéros du « contenu » se décalent)
    pj = os.path.join(ICI, "langues_plus", "_francais.json")
    d = json.load(open(pj, encoding="utf-8"))
    nouveaux = [k for k in textes if k not in d["ui"]]
    n0 = len(d["ui"])
    d["ui"] += nouveaux
    open(pj, "w", encoding="utf-8", newline="\n").write(json.dumps(d, ensure_ascii=False, indent=1) + "\n")
    fr_tous = d["ui"] + d["contenu"]

    def reecrire(fichier, valeurs, remplace=None):
        lignes = [x.partition("\t")[2] for x in open(fichier, encoding="utf-8").read().split("\n") if x.strip()]
        lignes = lignes[:n0] + valeurs + lignes[n0:]
        if remplace:
            lignes = [remplace.get(fr_tous[i], x) for i, x in enumerate(lignes)]
        open(fichier, "w", encoding="utf-8", newline="\n").write("".join(f"{i}\t{x}\n" for i, x in enumerate(lignes)))
    reecrire(os.path.join(ICI, "langues_plus", "_francais.txt"), nouveaux)
    for l in L13:
        reecrire(os.path.join(ICI, "langues_plus", l + ".txt"), [textes[k][l] for k in nouveaux], {k: v[l] for k, v in textes.items()})
    print(len(nouveaux), "texte(s) ajouté(s),", len(textes) - len(nouveaux), "remplacé(s)")


if __name__ == "__main__":
    main(sys.argv[1])
