# Notes pour Claude — site « Mosquées en Tunisie » (dépôt public : rien de personnel ici)

- Répondre en français, simplement. `git pull` avant de modifier, commit + push après.
- Pages GÉNÉRÉES : ne pas modifier `mosquee/`, `grandes-mosquees/`, `a-propos/`, `donnees/lieux.js`, `assets/trad/`, `sitemap.xml`
  à la main → modifier `tools/construire.py`, `tools/gabarits/*.html` ou `tools/contenu_grandes_*.py` (textes des grandes mosquées,
  8 langues), puis `python tools/construire.py`. L'accueil `index.html` est écrit à la main (la grille des grandes mosquées
  entre `<!-- grandes:debut -->` et `<!-- grandes:fin -->` est refaite par construire.py).
- Une seule version `?v=` : `VERSION` dans `tools/construire.py`, à changer à chaque modification de `assets/`.
- Langues : spans `data-l="fr|ar|en"` + `assets/langues.js` (tr, id, ur, de, es ; clé = texte français exact) ; mémoire
  `langue-mosquees` (8 langues), la clé partagée `langue` ne reçoit que fr/ar. Tout texte français ajouté doit être traduit
  (le test le vérifie).
- Récitation : `assets/recitation.js` (clé `recitation-mosquees` = oui/non, lecteur youtube-nocookie visible, `?son=0` sans écran).
- Signalements : même Google Forms que Prix des Eaux, format `LIEU-PRIERE`, `LIEU-PRIERE-OK`, `LIEU-PRIERE-KO` (jeton `lp:`) ;
  les robots de Prix des Eaux et de Points d'eau ignorent ce format.
- Tests AVANT tout envoi : `python tools/construire.py`, `node tools/test_site.mjs`, `node tools/test_sw.mjs`,
  `node tools/test_avis.mjs`, `node tools/test_video.mjs`, `python tools/test_lieux.py`, `python tools/test_sabotage.py`
  (adapter l'ancre du sabotage dans le même commit si un texte visé change).
- Robot des données lent (~5 min, réseau) : ne le relancer que si nécessaire.
- **« Tunisie et monde » (09/10/2026, demande d'Ahmed : que les visiteurs sachent que la carte couvre le monde)** : nom affiché
  (en-tête, pied de page, manifeste) « Mosquées de Tunisie et du monde / مساجد تونس والعالم » (adresse du site inchangée)
  + bandeau `.monde-bande` juste au-dessus de la carte : « 🌍 Le monde entier est sur la carte », villes d'exemple (`data-ville-ex`,
  La Mecque, Istanbul, Paris, Le Caire → recherche Nominatim, une requête par appui) et « Voir le monde » (`data-monde-vue`).
  Nom SANS tiret (demande d'Ahmed du 09/10) ; sur téléphone il passe sur 2-3 lignes (`.logo-nom`, media 560 px) pour n'être jamais caché
  sous les boutons ; titre de partage (og:title) « Mosquées de Tunisie et du monde : … ».

- **10/10/2026 (audit des robots)** : `signalements.yml` (toutes les 2 h) ne commite plus que si un lieu signalé change (ou une fois par semaine : `doit_ecrire` de `tools/lieux_priere.py`) ; `tests.yml` ignore les envois qui ne changent que des `.md`.

- **Adresse depuis le 11/10/2026 : https://mosquees.clicvia.com/** (domaine clicvia.com d'Ahmed, ligne DNS `CNAME mosquees → ah6259.github.io` nuage gris, fichier `CNAME`). L'ancienne adresse ah6259.github.io/mosquees-tunisie/ redirige seule. Site à la racine « / » : `BASE_SITE` de assets/page.js (sw.js, vidéo) ; GoatCounter garde le préfixe `/mosquees-tunisie`. Si l'outil vidéo réécrit le bloc VIDEO_SITE, remettre `"base": BASE_SITE` et l'ORIGINE mosquees.clicvia.com.

- **11/10/2026 — photo du bandeau qui défile (demande d'Ahmed : « ça donne une vie au site »)** : sur l'accueil, la photo en haut à droite
  fait défiler les 15 grandes mosquées (fondu, une toutes les 3 s, Kairouan d'abord, clic = page de la mosquée, crédit auteur + licence
  sous chaque photo). Fabriquée par `diapo_accueil()` de tools/construire.py entre `<!-- diapo:debut -->` et `<!-- diapo:fin -->` ;
  mouvement dans assets/page.js (`[data-diapo]`, pause au toucher / onglet caché / « moins d'animations ») ; testé par test_site.mjs.
  Même jour : paragraphe d'accueil raccourci (5 lignes → 3 sur téléphone, demande d'Ahmed), 8 langues (index.html + assets/langues.js).
- **11/10/2026 — aperçu WhatsApp** : `og:url` (adresse canonique) ajouté sur chaque page (sans lui, WhatsApp peut montrer une petite vignette ; règle commune § 14).
