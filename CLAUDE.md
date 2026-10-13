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

- **Visibilité Google (12/10/2026, règle commune § 8)** : liens vers nos autres sites en `https://<site>.clicvia.com/` (jamais `ah6259.github.io`), lien « Tous nos services » → https://clicvia.com/ dans le pied de page, `robots.txt` avec ligne Sitemap, `sitemap.xml` daté, JSON-LD sur l'accueil, clé IndexNow `377f054ba9c5ed40d6796adc8d87d1e8.txt` à la racine (ne pas supprimer : robot `indexnow` du portail). Contrôle : `node "outils visibilite/controle.mjs"` (dépôt projets-ahmed). Sitemap envoyé dans Search Console par Ahmed le 12/10/2026.

- **Google + Bing (12/10/2026)** : sitemap envoyé par Ahmed dans Google Search Console et dans Bing Webmaster Tools (site clicvia.com/), indexation de l'accueil demandée. Pour un nouveau site : mêmes gestes, voir `nouveau site - procedure.md` § 4 étape 5 (dépôt projets-ahmed).

- **UNE ADRESSE PAR LANGUE (12/10/2026, visibilité Google — demande d'Ahmed)** : avant, les 8 langues n'apparaissaient que dans
  le navigateur (`?lang=ar`), Google ne voyait que le français. Maintenant chaque page existe en français à son adresse d'origine
  ET dans `ar/`, `en/`, `tr/`, `id/`, `ur/`, `de/`, `es/` (861 pages), déjà écrite dans la langue : `<html lang>`, sens, titre,
  description, texte, adresse officielle, liens hreflang (x-default = anglais). Fabrication : `tools/construire.py` écrit la page
  française puis `tools/pages_langues.py` (bibliothèque standard seulement) en tire les 7 autres — **ne jamais modifier à la main
  un fichier de `ar/ … es/`** (refaits et effacés à chaque construction). Liens entre pages : dans le dossier de la langue ;
  `assets/`, `donnees/`… : à la racine ; `video/` reste une seule page (`?lang=`).
  - Titres / descriptions : `META` de construire.py (grandes mosquées, fiches), `ACCUEIL` de pages_langues.py, sinon `<h1>` + intro.
  - Fiches des autres mosquées : une langue sans nom ni résumé Wikidata/Wikipédia existe pour le visiteur mais est `noindex`,
    hors plan du site et hors hreflang (`INDEX` de construire.py) — pas de pages vides proposées à Google (420 versions).
  - `assets/page.js` : sur ces pages (`data-fixe`), la langue est celle de l'ADRESSE ; le bouton de langue ouvre l'autre adresse
    et garde le choix (`langue-mosquees`) ; un ancien lien `?lang=ar` ou un choix déjà fait mène à la bonne adresse ; JAMAIS de
    changement d'après la langue du téléphone seule (le robot de Google lirait de l'anglais sur la page française) : on propose
    un lien « English → » sous le menu. `window.allerVers` = crochet des tests.
  - Nouveau texte français : le traduire dans `assets/langues.js` comme avant ; la construction dit « N texte(s) resté(s) en
    anglais » (doit être 0). Robot `donnees.yml` : `git add` inclut `ar en tr id ur de es`.
  - Tests : `test_site.mjs` (langue, adresse officielle, fichiers communs, hreflang identiques, noindex), 4 sabotages.

- **15 LANGUES (13/10/2026, demande d'Ahmed : « le plus possible de langues », mêmes langues que The Message)** : aux 8 d'origine
  (fr, ar, en, tr, id, ur, de, es) s'ajoutent **it, pt, nl, zh, ja, ko, hi**, puis (13/10, même jour) **ru, vi, th, tl, sv, ro**. 123 pages × 21 langues = 2 584 pages ; 813 adresses
  proposées à Google (les fiches sans nom ni résumé dans une langue restent `noindex`).
  - Textes des 7 nouvelles langues : `tools/langues_plus/<langue>.txt` (une ligne « numéro<TAB>traduction » par texte français de
    `_francais.json` : 201 textes d'interface + 145 textes des grandes mosquées et des villes) ; module `tools/langues_plus.py`.
    Les 5 langues d'avant restent dans `assets/langues.js` et `tools/contenu_grandes_*.py`.
  - **Nouveau texte français** : l'ajouter dans `assets/langues.js` (5 langues) ET à la fin de la bonne liste de `_francais.json`
    + une ligne dans chacun des 7 fichiers `.txt` ; la construction s'arrête si une traduction manque.
  - Verset 9:18 : traduction OFFICIELLE de QuranEnc.com dans chaque langue (jamais traduit par nous), nom du traducteur à côté.
  - Chaque page de langue ne charge que SON dictionnaire d'interface `assets/l/<langue>.js` (fabriqué par construire.py ; la page
    arabe et la page anglaise n'en chargent aucun) : avant, toutes les pages chargeaient les 122 Ko de `langues.js`.
    `assets/trad/*.js` ne contient que les 5 anciennes langues (il ne sert qu'à la page française).
  - Robot `mosquees_donnees.py` : demande à Wikidata les noms et articles dans les 21 langues.
  - Traductions écrites par Claude, non relues par des personnes dont c'est la langue : à faire relire quand ce sera possible.
