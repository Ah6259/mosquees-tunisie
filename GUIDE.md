# Guide — Mosquées en Tunisie

1. **Ajouter une grande mosquée** : ajouter une entrée dans `tools/contenu_grandes_3.py` (8 langues, dates, liens vérifiés),
   ses photos (Wikimedia Commons, licence libre) dans `assets/photos/` + `donnees/photos_grandes.json`, la ligne de la ville
   dans `VILLES` de `tools/construire.py`, puis `python tools/construire.py` et les tests.
2. **Corriger une mosquée « ordinaire »** : la corriger sur OpenStreetMap ou Wikidata ; le robot trimestriel la reprend.
3. **Changer la vidéo de récitation** : identifiants dans `assets/recitation.js` (VIDEOS) et boutons `data-video` de l'accueil ;
   uniquement des vidéos de la chaîne officielle, intégration autorisée.
4. **Relancer un robot** : GitHub → Actions → choisir le robot → « Run workflow » (marche aussi depuis l'application du téléphone).
5. **Après toute modification** : tests (voir CLAUDE.md), commit, push ; vérifier le site sur le téléphone.
6. **Le monde entier** (09/10/2026) : au-dessus de la carte, le bandeau « 🌍 Le monde entier est sur la carte » ; changer les villes
   d'exemple : boutons `data-ville-ex` de `index.html` (le texte affiché + la ville en anglais pour la recherche).
