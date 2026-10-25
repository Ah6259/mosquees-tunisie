# Mosquées de Tunisie et du monde (مساجد تونس والعالم)

Nom affiché sur le site depuis le 09/10/2026 (avant : « Mosquées en Tunisie ») ; l'adresse ne change pas.

Site gratuit : https://mosquees.clicvia.com/

Page « Comment fonctionne le site ? » : https://mosquees.clicvia.com/a-propos/ (chaque fonction en une ligne ; tenue à jour à chaque modification visible, test `FONCTIONS` de `tools/test_site.mjs`, règle commune § 44).
- carte de toutes les mosquées et salles de prière de Tunisie (OpenStreetMap + Wikidata + signalements des visiteurs),
  recherche par nom ou par ville, « Autour de moi » ; et les mosquées du monde entier (bandeau « Le monde entier est sur la carte »,
  villes d'exemple, « Voir le monde ») ;
- une page complète par grande mosquée (Zitouna, Kairouan, Sousse, Mahdia, Sfax, Trois Portes, Youssef Dey, Hammouda Pacha,
  Sidi Mahrez, Sidi Sahbi, Testour, Mâlik ibn Anas, Fadhloun/Djerba, Kasbah, Monastir) et une page pour chaque autre mosquée
  ayant une fiche Wikidata ;
- récitation du Coran par cheikh Ali El Barrak (vidéos intégrées de sa chaîne YouTube officielle) ;
- 8 langues : français, arabe, anglais, turc, indonésien, ourdou, allemand, espagnol.

## Fonctionnement automatique (aucun besoin du PC d'Ahmed)
| Robot (`.github/workflows/`) | Quand | Rôle |
|---|---|---|
| `tests.yml` | à chaque envoi | tous les tests + sabotage volontaire + pages à jour |
| `donnees.yml` | 1er jan/avr/juil/oct | relit OpenStreetMap + Wikidata (`tools/mosquees_donnees.py`), refait les pages ; panne → ancien fichier gardé + issue `alerte-robot` ; commit vide = battement de cœur |
| `signalements.yml` | toutes les 2 h (8h-22h) | publie les lieux signalés (`tools/signalements_lieux.py` → `donnees/signales.js`) |
| `gendarme-tests.yml`, `relance-pages.yml` | kit commun | réparations de tests contrôlées ; relance de GitHub Pages |

## Plan de continuité
Tout est sur GitHub (dépôt public Ah6259/mosquees-tunisie, GitHub Pages). Si un robot tombe en panne, l'issue `alerte-robot`
envoie un e-mail ; le site garde ses anciennes données. Aucun secret n'est utilisé. Pour reprendre le travail : lire `CLAUDE.md`.

## Sources et licences
OpenStreetMap (ODbL), Wikidata (CC0), Wikipédia (CC BY-SA 4.0, résumés cités avec lien), Wikimedia Commons (photos, auteur et
licence affichés), QuranEnc (traductions du sens du verset 9:18), chaîne YouTube officielle de cheikh Ali El Barrak (intégration).
Code et textes du site : © 2026, tous droits réservés (voir LICENSE).
