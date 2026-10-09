# -*- coding: utf-8 -*-
"""Sabotage volontaire (règle commune) : on abîme une COPIE du site de plusieurs façons ; chaque fois, le test visé doit échouer.
  python tools/test_sabotage.py      (lancé aussi par .github/workflows/tests.yml)
Ancres courtes et stables (règle du 08/10/2026) : si une ancre n'est plus trouvée, le test le dit (à adapter dans le même commit)."""
import os, shutil, subprocess, sys, tempfile

ICI = os.path.dirname(os.path.abspath(__file__)); RACINE = os.path.dirname(ICI)
SITE = ["node", "tools/test_site.mjs"]
ROBOT = [sys.executable, "tools/test_lieux.py"]
SABOTAGES = [
    ("assets/mosquees.js", "corps.append(CH.format, format);", 'corps.append(CH.format, "PRIX");', "le signalement part avec le format des prix", SITE),
    ("assets/mosquees.js", "if (!(la > 30 && la < 37.6 && lo > 7.4 && lo < 11.7))", "if (false)", "une position hors de Tunisie est envoyée", SITE),
    ("assets/recitation.js", 'const ORIGINE_YT = "https://www.youtube-nocookie.com";', 'const ORIGINE_YT = "https://www.youtube.com";', "lecteur YouTube avec cookies (pas nocookie)", SITE),
    ("assets/recitation.js", "if (c === null) ecran();", "if (false) ecran();", "plus d'écran d'entrée à la première visite", SITE),
    ("assets/page.js", '<button class="partager"', '<button class="x-partager"', "bouton Partager retiré", SITE),
    ("mosquee/zitouna/index.html", "reconstruite en 864", "reconstruite en 964", "date fausse dans la page de la Zitouna", SITE),
    ("assets/langues.js", '"Autour de moi": "Yakınımda",', "", "une traduction turque manque", SITE),
    ("tools/lieux_priere.py", "if ko >= seuil and ko > ok:", "if False:", "le robot ne retire plus un lieu « n'existe plus »", ROBOT),
    ("tools/lieux_priere.py", 'TUNISIE = (30.1, 37.6, 7.4, 11.7)', 'TUNISIE = (-90, 90, -180, 180)', "le robot accepte un lieu hors de Tunisie", ROBOT),
]
IGNORER = shutil.ignore_patterns(".git", "_icone", "__pycache__", "node_modules")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    rate = 0
    for f, avant, apres, quoi, test in SABOTAGES:
        with tempfile.TemporaryDirectory() as tmp:
            copie = os.path.join(tmp, "site")
            shutil.copytree(RACINE, copie, ignore=IGNORER)
            nm = os.path.join(RACINE, "node_modules")
            if os.path.isdir(nm):
                try: os.symlink(nm, os.path.join(copie, "node_modules"), target_is_directory=True)
                except OSError: pass
            p = os.path.join(copie, f)
            s = open(p, encoding="utf-8").read()
            if avant not in s:
                print(f"FAIL ancre introuvable dans {f} : {avant!r} (adapter ce sabotage)"); rate += 1; continue
            open(p, "w", encoding="utf-8", newline="\n").write(s.replace(avant, apres, 1))
            cmd = test + ([copie] if test is SITE else [])
            r = subprocess.run(cmd, cwd=copie if test is ROBOT else RACINE, capture_output=True, text=True, encoding="utf-8", stdin=subprocess.DEVNULL)
            if r.returncode == 0:
                print(f"FAIL sabotage NON détecté : {quoi}"); rate += 1
            else:
                print(f"OK   sabotage détecté : {quoi}")
    print("\nTOUT PASSE" if not rate else f"\n{rate} PROBLÈME(S)")
    return 1 if rate else 0


if __name__ == "__main__":
    sys.exit(main())
