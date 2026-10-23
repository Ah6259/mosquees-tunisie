# -*- coding: utf-8 -*-
"""Fabrique les pages du site « Mosquées en Tunisie » (pages statiques, bonnes pour Google) :
  - donnees/lieux.js            : tous les lieux de prière pour la carte (depuis donnees/mosquees.json, robot mosquees_donnees.py)
  - mosquee/<page>/index.html   : une page par GRANDE mosquée (textes : tools/contenu_grandes_*.py + tools/langues_plus/, 21 langues)
                                  + une page par autre mosquée ayant une fiche Wikidata (photo, noms, année, résumé Wikipédia, carte, liens)
  - grandes-mosquees/index.html : la liste de toutes ces pages
  - <gabarit>/index.html        : pages écrites à la main dans tools/gabarits/<page>.html (À propos…)
  - assets/trad/<page>.js       : traductions turc, indonésien, ourdou, allemand, espagnol des textes de chaque grande page
                                  (même méthode que assets/langues.js : clé = texte français exact)
  - sitemap.xml ; la version ?v= de l'accueil (écrit à la main) et la grille des grandes mosquées de l'accueil.
Même en-tête technique partout (CSP, iPhone, aperçu de partage, polices, une seule version ?v=).
  python tools/construire.py"""
import html, json, os, re, sys, unicodedata

ICI = os.path.dirname(os.path.abspath(__file__)); RACINE = os.path.dirname(ICI)
sys.path.insert(0, ICI)
from contenu_grandes_1 import GRANDES as G1, L  # noqa: E402
from contenu_grandes_2 import GRANDES as G2  # noqa: E402
from contenu_grandes_3 import GRANDES as G3  # noqa: E402
import pages_langues as PL  # noqa: E402
import langues_plus  # noqa: E402
from mosquees_donnees import vignette  # noqa: E402  (photo de 960 px, VS.7 du 18/10/2026)
import textes  # noqa: E402  (textes ajoutés le 23/10/2026, 21 langues : tools/textes/)

VERSION = "20261023b"          # à changer à chaque modification des fichiers assets/ (le test vérifie une seule version)
BASE = "https://mosquees.clicvia.com/"
LANGUES = ["fr", "ar", "en", "tr", "id", "ur", "de", "es", "it", "pt", "nl", "zh", "ja", "ko", "hi", "ru", "vi", "th", "tl", "sv", "ro"]
NOUVELLES = ["tr", "id", "ur", "de", "es", "it", "pt", "nl", "zh", "ja", "ko", "hi", "ru", "vi", "th", "tl", "sv", "ro"]      # toutes sauf fr, ar, en (écrits dans les pages)
ANCIENNES = ["tr", "id", "ur", "de", "es"]   # celles de assets/langues.js et assets/trad/*.js (affichage sur place de la page française)
NOM_LANGUE = {"fr": "Français", "ar": "العربية", "en": "English", "tr": "Türkçe", "id": "Bahasa Indonesia", "ur": "اردو", "de": "Deutsch", "es": "Español",
              "it": "Italiano", "pt": "Português", "nl": "Nederlands", "zh": "中文", "ja": "日本語", "ko": "한국어", "hi": "हिन्दी",
              "ru": "Русский", "vi": "Tiếng Việt", "th": "ไทย", "tl": "Filipino", "sv": "Svenska", "ro": "Română"}
CSP = ("default-src 'self'; script-src 'self' https://gc.zgo.at https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
       "font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https://upload.wikimedia.org https://thumb.wikimedia.org https://commons.wikimedia.org https://tile.openstreetmap.org https://*.tile.openstreetmap.org https://cdnjs.cloudflare.com https://prix-eaux-tunisie.goatcounter.com; "
       "frame-src https://www.youtube-nocookie.com; connect-src 'self' https://prix-eaux-tunisie.goatcounter.com https://formspree.io https://docs.google.com https://query.wikidata.org "
       "https://maps.mail.ru https://overpass-api.de https://overpass.kumi.systems https://overpass.private.coffee https://overpass.openstreetmap.fr https://nominatim.openstreetmap.org; object-src 'none'; base-uri 'self'; "
       "form-action 'self' https://formspree.io https://docs.google.com")
GRANDES = G1 + G2 + G3
VILLES = {
    "tunis": L("Tunis", "تونس", "Tunis", "Tunus", "Tunis", "تونس", "Tunis", "Túnez"),
    "kairouan": L("Kairouan", "القيروان", "Kairouan", "Kayrevan", "Kairouan", "قیروان", "Kairouan", "Cairuán"),
    "sousse": L("Sousse", "سوسة", "Sousse", "Susa", "Sousse", "سوسہ", "Sousse", "Susa"),
    "mahdia": L("Mahdia", "المهدية", "Mahdia", "Mehdiye", "Mahdia", "مہدیہ", "Mahdia", "Mahdía"),
    "sfax": L("Sfax", "صفاقس", "Sfax", "Sefâkus", "Sfax", "صفاقس", "Sfax", "Sfax"),
    "testour": L("Testour", "تستور", "Testour", "Testur", "Testour", "تستور", "Testour", "Testour"),
    "carthage": L("Carthage", "قرطاج", "Carthage", "Kartaca", "Kartago", "قرطاجنہ", "Karthago", "Cartago"),
    "djerba": L("Djerba (Midoun)", "جربة (ميدون)", "Djerba (Midoun)", "Cerbe (Midun)", "Djerba (Midoun)", "جربہ (میدون)", "Djerba (Midoun)", "Yerba (Midoun)"),
    "monastir": L("Monastir", "المنستير", "Monastir", "Münestir", "Monastir", "منستیر", "Monastir", "Monastir"),
}
TRAD = {}          # page -> langue -> {français: traduction}
# Les 7 langues ajoutées le 13/10/2026 : chaque texte (fr, ar, en, tr, id, ur, de, es) des grandes mosquées et des villes reçoit
# aussi it, pt, nl, zh, ja, ko, hi, pris dans tools/langues_plus/ (clé = texte français).
PLUS, UI_PLUS = langues_plus.charger()


def completer(x):
    if isinstance(x, dict):
        if isinstance(x.get("fr"), str) and "ar" in x:
            for l in langues_plus.PLUS:
                if x["fr"] not in PLUS[l]:
                    raise SystemExit(f"tools/langues_plus/{l}.txt : pas de traduction pour « {x['fr'][:60]} »")
                x[l] = PLUS[l][x["fr"]]
        else:
            for v in x.values():
                completer(v)
    elif isinstance(x, (list, tuple)):
        for v in x:
            completer(v)


completer(GRANDES); completer(VILLES)
# Une vraie page par langue (tools/pages_langues.py) : pour chaque page (dossier depuis la racine, « » = accueil)
META = {}          # -> langue -> (titre, description[, titre de partage]) ; absent : tiré du <h1> et de l'introduction de la page
INDEX = {}         # -> langues où la page a un contenu propre (les autres existent pour le visiteur mais ne sont pas proposées à Google)
CLE_TRAD = {}      # -> nom du fichier assets/trad/<nom>.js de la page


# ---------- petits outils ----------
def esc(s):
    return html.escape(str(s or ""), quote=False)


def att(s):
    return html.escape(str(s or ""), quote=True)


def iso(s, l):
    """Nombres isolés dans un texte arabe ou ourdou (U+2066…U+2069), règle commune."""
    if l not in ("ar", "ur"):
        return s
    return re.sub(r"(\d[\d\s.,×–-]*\d|\d)", lambda m: "⁦" + m.group(1) + "⁩", s)


def S(d, page=None, tag="span", attrs=""):
    """Trois éléments data-l (fr, ar, en) ; les 5 autres langues vont dans TRAD[page] (clé = texte français)."""
    fr = esc(d["fr"])
    if page:
        for l in NOUVELLES:
            if d.get(l):
                TRAD.setdefault(page, {}).setdefault(l, {})[re.sub(r"\s+", " ", fr).strip()] = esc(iso(d[l], l))
    a = (" " + attrs) if attrs else ""
    return "".join(f'<{tag} data-l="{l}"{a}>{esc(iso(d[l], l))}</{tag}>' for l in ("fr", "ar", "en"))


def X(nom, cle, page, tag="span", attrs=""):
    """Texte de tools/textes/ (21 langues, 23/10/2026) : comme S()."""
    return S(textes.D(nom, cle), page, tag, attrs)


def TXT(nom, cles, page):
    """Textes lus par un script (assets/recherche.js…) : éléments cachés [data-txt], traduits comme le reste de la page."""
    return "".join(f'<span hidden data-txt="{c}">{X(nom, c, page)}</span>' for c in cles)


def U(fr, ar, en, tag="span"):
    """Texte d'interface (traduit dans assets/langues.js pour les 5 autres langues)."""
    return "".join(f'<{tag} data-l="{l}">{t}</{tag}>' for l, t in (("fr", fr), ("ar", iso(ar, "ar")), ("en", en)))


def ascii_slug(s):
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:50] or "mosquee"


def est_arabe(s):
    return bool(re.search(r"[؀-ۿ]", s or ""))


# ---------- en-tête commun ----------
def document(chemin, titre, description, corps, tete=(), bas=(), image=None, jsonld=None, index=True, og_titre=None):
    profondeur = chemin.count("/")
    r = "../" * profondeur
    dossier = chemin.rsplit("index.html", 1)[0]
    url = BASE + dossier
    scripts_tete = ["langues.js"] + list(tete) + ["page.js", "recitation.js"]
    robots = "noai, noimageai" if index else "noindex, noai, noimageai"
    ld = "".join('<script type="application/ld+json">\n' + json.dumps(j, ensure_ascii=False) + "\n</script>\n" for j in (jsonld or []))
    alt = PL.liens_hreflang(BASE, dossier, INDEX.get(dossier, LANGUES))     # une adresse par langue : ar/…, en/…, tr/… (12/10/2026)
    return f"""<!doctype html>
<html lang="fr" dir="ltr" translate="no" data-racine="{r}" data-chemin="{dossier}" data-fixe>
<head>
<meta charset="utf-8">
<meta name="google" content="notranslate">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{CSP}">
<meta name="referrer" content="strict-origin-when-cross-origin">
<meta name="robots" content="{robots}">
<title>{att(titre)}</title>
<meta name="description" content="{att(description)}">
<link rel="canonical" href="{url}">
{alt}<link rel="icon" href="{r}assets/logo.svg" type="image/svg+xml">
<link rel="manifest" href="{r}manifest.webmanifest">
<link rel="apple-touch-icon" href="{r}assets/apple-touch-icon.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Mosquées">
<meta name="theme-color" content="#0E6B4C">
<meta property="og:title" content="{att(og_titre or titre)}">
<meta property="og:description" content="{att(description)}">
<meta property="og:image" content="{image or BASE + 'assets/og-image-v1.jpg'}">
<meta property="og:image:type" content="image/jpeg">
{'<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">' + chr(10) if not image else ''}<meta name="twitter:card" content="summary_large_image">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Figtree:wght@400;600;700;800&family=Noto+Kufi+Arabic:wght@400;600;700;800&family=Amiri:wght@400;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{r}assets/style.css?v={VERSION}">
{ld}{chr(10).join(f'<script src="{r}assets/{s}?v={VERSION}"></script>' for s in scripts_tete)}
</head>
<body>
<header class="entete" id="entete"></header>
{corps.strip()}
<footer id="pied"></footer>
{"".join(f'<script src="{r}{s}?v={VERSION}"></script>' + chr(10) for s in bas)}<script data-goatcounter="https://prix-eaux-tunisie.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>
</body>
</html>
"""


def ecrire(chemin, texte):
    dest = os.path.join(RACINE, chemin)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, "w", encoding="utf-8", newline="\n").write(texte)


# ---------- gabarits écrits à la main ----------
def lire_gabarit(chemin):
    texte = open(chemin, encoding="utf-8").read()
    tete, corps = texte.split("\n---\n", 1)
    meta = {}
    for ligne in tete.splitlines():
        if ":" in ligne and not ligne.startswith("#"):
            k, v = ligne.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, corps


# ---------- données ----------
def charger():
    d = json.load(open(os.path.join(RACINE, "donnees", "mosquees.json"), encoding="utf-8"))
    photos = json.load(open(os.path.join(RACINE, "donnees", "photos_grandes.json"), encoding="utf-8"))
    for l in d["lieux"]:          # « mosquée des Étrangers » (étiquette Wikidata en minuscule) → « Mosquée des Étrangers »
        l["noms"] = {k: (v[0].upper() + v[1:] if v and v[0].islower() else v) for k, v in l["noms"].items()}
    return d, photos


def nom_principal(noms):
    return noms.get("fr") or noms.get("en") or noms.get("ar") or ""


def pages_fiches(lieux):
    """Pages des grandes mosquées (par QID) puis des autres fiches Wikidata ; chemin stable."""
    grandes_qid = {g["qid"]: g for g in GRANDES}
    pages, vus = {}, set()
    for l in sorted(lieux, key=lambda x: x["id"]):
        f = l.get("fiche")
        if not f:
            continue
        if f["qid"] in grandes_qid:
            pages[l["id"]] = "mosquee/" + grandes_qid[f["qid"]]["slug"] + "/"
            continue
        nom = nom_principal(l["noms"]) or "mosquee"
        if not (f.get("resume") or f.get("photo") or f.get("annee")):
            continue                                   # aucune fiche vide : il faut au moins un résumé, une photo ou une année
        base = ascii_slug(nom if not est_arabe(nom) else (l["noms"].get("en") or "mosquee"))
        slug = f"{base}-{f['qid'].lower()}"
        if slug in vus:
            continue
        vus.add(slug)
        pages[l["id"]] = "mosquee/" + slug + "/"
    return pages


def donnees_carte(d, pages):
    sortie = []
    for l in d["lieux"]:
        v = l.get("ville") or {}
        e = {"i": l["id"], "a": l["lat"], "o": l["lon"], "t": "s" if l["type"] == "salle" else "m"}
        if l["noms"]:
            fr = l["noms"].get("fr") or l["noms"].get("en")
            e["n"] = {k: v for k, v in l["noms"].items() if k in ("fr", "ar") or v != fr}     # pas de nom répété (fichier plus léger)
        vv = [v.get("fr", ""), v.get("ar", ""), v.get("region_fr", ""), v.get("region_ar", "")]
        if any(vv):
            e["v"] = vv
        if l["id"] in pages:
            e["p"] = pages[l["id"]]
        if l.get("rite") == "ibadite":
            e["r"] = "i"
        sortie.append(e)
    # les grandes mosquées sans lieu OpenStreetMap rattaché (ex. zaouïa Sidi Sahbi) sont ajoutées avec leurs coordonnées
    deja = set(pages.values())
    for g in GRANDES:
        p = "mosquee/" + g["slug"] + "/"
        if p not in deja:
            sortie.append({"i": "grande-" + g["slug"], "a": g["lat"], "o": g["lon"], "t": "m", "n": {k: g["nom"][k] for k in LANGUES}, "p": p,
                           "v": [VILLES[g["ville"]]["fr"], VILLES[g["ville"]]["ar"], "", ""]})
    texte = ("// GÉNÉRÉ par tools/construire.py depuis donnees/mosquees.json (robot tools/mosquees_donnees.py, tous les 3 mois) — ne pas modifier à la main\n"
             "window.MOSQUEES = " + json.dumps({"maj": d["maj"], "lieux": sortie}, ensure_ascii=False, separators=(",", ":")) + ";\n")
    ecrire("donnees/lieux.js", texte)
    return sortie


# ---------- pages des grandes mosquées ----------
TITRES = {
    "intro": ("Présentation", "تقديم", "Overview"),
    "histoire": ("Histoire", "التاريخ", "History"),
    "architecture": ("Architecture", "العمارة", "Architecture"),
    "role": ("Rôle et rayonnement", "الدور والإشعاع", "Role and influence"),
}


def figure_photo(p, r, nom_fr, classe="", principale=False):
    return (f'<figure class="mq-photo {classe}" data-source="{att(p["source"])}"><span class="cadre-photo"><img src="{r}{p["fichier"]}" alt="{att(nom_fr)}" '
            f'width="{p["w"]}" height="{p["h"]}"{"" if principale else " loading=" + chr(34) + "lazy" + chr(34)}></span>'
            f'<figcaption>{U("Photo", "صورة", "Photo")} : <a href="{att(p["source"])}" target="_blank" rel="noopener">{esc(p["auteur"])}</a>, '
            f'{esc(p["licence"])} — Wikimedia Commons</figcaption></figure>')


def liens_wiki(wiki):
    out = []
    for l in LANGUES:
        if l in wiki:
            out.append(f'<li><a href="https://{l}.wikipedia.org/wiki/{att(wiki[l].replace(" ", "_"))}" target="_blank" rel="noopener" lang="{l}">Wikipédia — {NOM_LANGUE[l]}</a></li>')
    return "".join(out)


def page_grande(g, photos, wiki_par_qid, r="../../"):
    slug, page = g["slug"], "g-" + g["slug"]
    nom = g["nom"]
    ville = VILLES[g["ville"]]
    ph = photos.get(slug, [])
    blocs = []
    for cle in ("intro", "histoire", "architecture", "role"):
        if g.get(cle):
            t = TITRES[cle]
            blocs.append(f'<section class="carte mq-texte" id="{cle}"><h2>{U(*t)}</h2><p>{S(g[cle], page)}</p></section>')
            if cle == "intro" and len(ph) > 1:
                blocs.append('<section class="carte mq-galerie" id="photos"><h2>' + U("Photos", "صور", "Photos") + '</h2><div class="mq-galerie-grille">'
                             + "".join(figure_photo(p, r, nom["fr"]) for p in ph[1:]) + "</div></section>")
    dates = "".join(
        f'<li><b>{S(d[0], page) if isinstance(d[0], dict) else esc(d[0])}</b><span>{S(d[1], page)}</span></li>' for d in g["dates"])
    wiki = wiki_par_qid.get(g["qid"], {})
    liens = liens_wiki(wiki) + "".join(f'<li><a href="{att(u)}" target="_blank" rel="noopener" lang="fr">{esc(t)}</a></li>' for t, u in g["liens"])
    sources = (f'<li>{U("Textes rédigés par Mosquées en Tunisie à partir des documents ci-dessus (Wikipédia, Qantara, Discover Islamic Art, UNESCO), vérifiés le 09/10/2026.", "نصوص كتبها موقع مساجد تونس اعتمادًا على الوثائق أعلاه (ويكيبيديا، قنطرة، اكتشف الفن الإسلامي، اليونسكو)، رُوجعت في 09/10/2026.", "Texts written by Mosques in Tunisia from the documents above (Wikipedia, Qantara, Discover Islamic Art, UNESCO), checked on 09/10/2026.")}</li>'
               f'<li>Wikidata : <a href="https://www.wikidata.org/wiki/{g["qid"]}" target="_blank" rel="noopener">{g["qid"]}</a> (CC0)</li>'
               f'<li>{U("Photos : Wikimedia Commons, auteur et licence sous chaque photo.", "الصور: ويكيميديا كومنز، المؤلف والرخصة تحت كل صورة.", "Photos: Wikimedia Commons, author and licence under each photo.")}</li>'
               f'<li>{U("Position : OpenStreetMap (ODbL) et Wikidata.", "الموقع: OpenStreetMap ‏(ODbL) وويكي بيانات.", "Location: OpenStreetMap (ODbL) and Wikidata.")}</li>')
    autres = [x for x in GRANDES if x["slug"] != slug and x["ville"] == g["ville"]][:4] or [x for x in GRANDES if x["slug"] != slug][:3]
    voisins = "".join(f'<li><a href="../{x["slug"]}/">{S(x["nom"], page)}</a></li>' for x in autres)
    corps = f"""
<section class="hero mq-hero-page">
  <div class="wrap">
    <p class="fil"><a href="{r}">{U("Accueil", "الرئيسية", "Home")}</a> › <a href="{r}grandes-mosquees/">{U("Grandes mosquées", "الجوامع الكبرى", "Great mosques")}</a></p>
    <h1>{S(nom, page)}</h1>
    <p class="intro mq-sous-titre">{S(ville, page)} · {S(g["epoque"], page)}</p>
  </div>
</section>
<main class="wrap chevauche">
  <section class="carte mq-une">{figure_photo(ph[0], r, nom["fr"], "mq-photo-une", True) if ph else ""}
    <div class="mq-actions">
      <a class="btn-principal" href="https://www.google.com/maps/dir/?api=1&amp;destination={g["lat"]},{g["lon"]}" target="_blank" rel="noopener"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s-6.5-6.2-6.5-11.2a6.5 6.5 0 0 1 13 0C18.5 14.8 12 21 12 21z"/><circle cx="12" cy="9.8" r="2.4"/></svg>{U("Itinéraire", "الطريق", "Directions")}</a>
      <a class="chipbtn" href="{r}?lieu={att(g["slug"])}">{U("Voir sur la carte", "اعرض على الخريطة", "See on the map")}</a>
    </div>
  </section>
  {"".join(blocs)}
  <section class="carte" id="dates"><h2>{U("Dates clés", "تواريخ مهمّة", "Key dates")}</h2><ol class="mq-dates">{dates}</ol></section>
  {section_histoires(slug, page)}
  <section class="carte" id="visiter"><h2>{U("Visiter", "الزيارة", "Visiting")}</h2>
    <p>{U("C'est d'abord un lieu de prière : venez en tenue correcte, retirez vos chaussures pour entrer dans la salle de prière et évitez les heures de prière. Dans plusieurs grandes mosquées, les visiteurs non musulmans peuvent entrer dans la cour, pas dans la salle de prière. Les horaires changent : renseignez-vous sur place.", "هو أولًا مكان للصلاة: البس لباسًا محتشمًا، واخلع حذاءك لدخول بيت الصلاة، وتجنّب أوقات الصلاة. وفي عدد من الجوامع الكبرى يمكن للزوار غير المسلمين دخول الصحن دون بيت الصلاة. تتغيّر المواعيد: استعلم في عين المكان.", "It is first of all a place of prayer: dress modestly, take off your shoes to enter the prayer hall and avoid prayer times. In several great mosques, non-Muslim visitors may enter the courtyard but not the prayer hall. Opening times change: ask on site.")}</p>
  </section>
  <section class="carte" id="carte-lieu"><h2>{U("Sur la carte", "على الخريطة", "On the map")}</h2>
    <div class="mq-mini" id="mq-mini" data-lat="{g["lat"]}" data-lon="{g["lon"]}" role="region" aria-label="{att(nom["fr"])}"></div>
  </section>
  <section class="carte" id="documents"><h2>{U("Documents et liens", "وثائق وروابط", "Documents and links")}</h2><ul class="mq-liens">{liens}</ul></section>
  <section class="carte" id="sources"><h2>{U("Sources", "المصادر", "Sources")}</h2><ul class="sources">{sources}</ul></section>
  <section class="carte"><h2>{U("Autres grandes mosquées", "جوامع كبرى أخرى", "Other great mosques")}</h2><ul class="mq-liens">{voisins}</ul>
    <p><a href="{r}grandes-mosquees/">{U("Toutes les grandes mosquées et mosquées historiques", "كل الجوامع الكبرى والمساجد التاريخية", "All great and historic mosques")} →</a></p></section>
</main>"""
    titre = f"{nom['fr']} ({ville['fr']}) : histoire, architecture, photos | Mosquées en Tunisie"
    desc = re.sub(r"\s+", " ", g["intro"]["fr"])[:200]
    jsonld = [{"@context": "https://schema.org", "@type": "Mosque", "name": nom["fr"], "alternateName": [nom["ar"], nom["en"]],
               "description": g["intro"]["en"], "url": BASE + "mosquee/" + slug + "/",
               "geo": {"@type": "GeoCoordinates", "latitude": g["lat"], "longitude": g["lon"]},
               "address": {"@type": "PostalAddress", "addressLocality": ville["fr"], "addressCountry": "TN"},
               **({"image": BASE + ph[0]["fichier"]} if ph else {}), "sameAs": [f"https://www.wikidata.org/wiki/{g['qid']}"]}]
    image = BASE + ph[0]["fichier"] if ph else None
    CLE_TRAD[f"mosquee/{slug}/"] = page
    META[f"mosquee/{slug}/"] = {x: (f"{nom[x]} ({ville[x]}){PL.SUITE_GRANDE[x]} | {PL.SITE[x]}", re.sub(r"\s+", " ", g["intro"][x])[:200]) for x in LANGUES}
    ecrire(f"mosquee/{slug}/index.html", document(f"mosquee/{slug}/index.html", titre, desc, corps, tete=[f"trad/{page}.js"],
                                                   bas=["assets/fiche.js"], image=image, jsonld=jsonld))


# ---------- pages des autres mosquées (fiche Wikidata) ----------
def noms_spans(noms):
    """Le nom dans chaque langue disponible ; assets/fiche.js montre celui de la langue choisie (sinon arabe + français)."""
    return "".join(f'<span class="nl" data-nl="{l}" lang="{l}">{esc(noms[l])}</span>' for l in LANGUES if noms.get(l))


def page_fiche(l, chemin, r="../../"):
    f, noms = l["fiche"], l["noms"]
    page = "f-" + f["qid"]
    notre = f["qid"] in PN.DESCRIPTIONS                 # description écrite par nous (23/10/2026), 21 langues
    djerba = PN.a_djerba(l["lat"], l["lon"])
    nom = nom_principal(noms)
    v = l.get("ville") or {}
    ville_fr, ville_ar = v.get("fr", ""), v.get("ar", "")
    region = v.get("region_fr", "")
    ph = f.get("photo")
    if ph:
        ph = {**ph, "url": vignette(ph["url"], ph.get("w", 0))}   # vignette de 960 px, ou l'original s'il est plus petit
    an = f.get("annee")
    badges = []
    if an:
        badges.append(f'<span class="mq-badge">{U("Fondée en", "تأسّس سنة", "Founded in")} {an}</span>')
    if f.get("patrimoine"):
        badges.append(f'<span class="mq-badge mq-badge-or">{U("Monument protégé", "معلم محميّ", "Protected monument")}</span>')
    if l.get("rite") == "ibadite":
        badges.append(f'<span class="mq-badge">{U("Mosquée ibadite", "مسجد إباضي", "Ibadi mosque")}</span>')
    resumes = "".join(
        f'<blockquote class="mq-resume" data-rl="{lg}" lang="{lg}" dir="{"rtl" if lg in ("ar", "ur") else "ltr"}"><p>{esc(t)}</p>'
        f'<footer>{U("Extrait de Wikipédia", "مقتطف من ويكيبيديا", "Extract from Wikipedia")} (<a href="https://creativecommons.org/licenses/by-sa/4.0/deed.fr" target="_blank" rel="license noopener">CC BY-SA 4.0</a>) — '
        f'<a href="https://{lg}.wikipedia.org/wiki/{att(f["wiki"][lg].replace(" ", "_"))}" target="_blank" rel="noopener">{esc(f["wiki"][lg].replace("_", " "))}</a></footer></blockquote>'
        for lg, t in ((x, f["resume"][x]) for x in LANGUES if x in f.get("resume", {})))
    liste_noms = "".join(f'<li><span class="mq-lg">{NOM_LANGUE[x]}</span> <span lang="{x}">{esc(noms[x])}</span></li>' for x in LANGUES if noms.get(x))
    photo = ""
    if ph:
        photo = (f'<figure class="mq-photo mq-photo-une" data-source="{att(ph["page"])}"><span class="cadre-photo"><img src="{att(ph["url"])}" alt="{att(nom)}" loading="eager"></span>'
                 f'<figcaption>{U("Photo", "صورة", "Photo")} : <a href="{att(ph["page"])}" target="_blank" rel="noopener">{esc(ph["auteur"])}</a>, {esc(ph["licence"])} — Wikimedia Commons</figcaption></figure>')
    lieu_txt = ""
    if ville_fr or ville_ar:
        lieu_txt = f'<span class="nl" data-nl="fr">{esc(ville_fr or ville_ar)}</span><span class="nl" data-nl="ar" lang="ar">{esc(ville_ar or ville_fr)}</span>'
    corps = f"""
<section class="hero mq-hero-page">
  <div class="wrap">
    <p class="fil"><a href="{r}">{U("Accueil", "الرئيسية", "Home")}</a> › <a href="{r}grandes-mosquees/">{U("Mosquées historiques", "المساجد التاريخية", "Historic mosques")}</a></p>
    <h1 class="mq-noms">{noms_spans(noms) or esc(nom)}</h1>
    <p class="intro mq-sous-titre">{U("Mosquée", "مسجد", "Mosque")}{(" · " + lieu_txt) if lieu_txt else ""}</p>
  </div>
</section>
<main class="wrap chevauche">
  <section class="carte mq-une">{photo}
    <p class="mq-badges">{"".join(badges)}</p>
    <div class="mq-actions">
      <a class="btn-principal" href="https://www.google.com/maps/dir/?api=1&amp;destination={l["lat"]},{l["lon"]}" target="_blank" rel="noopener"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s-6.5-6.2-6.5-11.2a6.5 6.5 0 0 1 13 0C18.5 14.8 12 21 12 21z"/><circle cx="12" cy="9.8" r="2.4"/></svg>{U("Itinéraire", "الطريق", "Directions")}</a>
      <a class="chipbtn" href="{r}?lieu={att(l["id"])}">{U("Voir sur la carte", "اعرض على الخريطة", "See on the map")}</a>
    </div>
  </section>
  {(f'<section class="carte" id="notre-presentation"><h2>{X("descriptions", "titre", page)}</h2><p>{X("descriptions", f["qid"], page)}</p>'
     f'<p class="hi-source">{X("histoires", "source", page)} ' + " · ".join(f'<a href="{att(u)}" target="_blank" rel="noopener">{esc(n)}</a>' for n, u in PN.DESCRIPTIONS[f["qid"]]) + '</p></section>') if notre else ""}
  {f'<section class="carte" id="presentation"><h2>{U("Présentation", "تقديم", "Overview")}</h2><p class="mq-resume-note" id="mq-resume-note"></p>{resumes}</section>' if resumes else ""}
  {(f'<section class="carte" id="djerba"><h2>{X("descriptions", "djerba_titre", page)}</h2><p>{X("descriptions", "djerba_intro", page)}</p>'
     f'<p class="hi-source">{X("histoires", "source", page)} ' + " · ".join(f'<a href="{att(u)}" target="_blank" rel="noopener">{esc(n)}</a>' for n, u in PN.DJERBA_SOURCES) + '</p></section>') if djerba else ""}
  <section class="carte" id="noms"><h2>{U("Son nom dans les langues", "اسمه في اللغات", "Its name in other languages")}</h2><ul class="mq-noms-liste">{liste_noms}</ul></section>
  <section class="carte" id="carte-lieu"><h2>{U("Sur la carte", "على الخريطة", "On the map")}</h2>
    <div class="mq-mini" id="mq-mini" data-lat="{l["lat"]}" data-lon="{l["lon"]}" role="region" aria-label="{att(nom)}"></div>
    {f'<p class="aide">{esc(ville_fr)}{(" — " + esc(region)) if region and region != ville_fr else ""}</p>' if ville_fr else ""}
  </section>
  <section class="carte" id="documents"><h2>{U("Documents et liens", "وثائق وروابط", "Documents and links")}</h2><ul class="mq-liens">{liens_wiki(f.get("wiki", {}))}
    <li><a href="https://www.wikidata.org/wiki/{f["qid"]}" target="_blank" rel="noopener">Wikidata — {f["qid"]}</a></li>
    {f'<li><a href="https://www.openstreetmap.org/{ {"n": "node", "w": "way", "r": "relation"}[l["id"][4]]}/{l["id"][5:]}" target="_blank" rel="noopener">OpenStreetMap</a></li>' if l["id"].startswith("osm-") else ""}</ul></section>
  <section class="carte" id="sources"><h2>{U("Sources", "المصادر", "Sources")}</h2><ul class="sources">
    <li>{U("Fiche fabriquée automatiquement à partir de Wikidata (CC0), Wikipédia (CC BY-SA 4.0), Wikimedia Commons et OpenStreetMap (ODbL).", "بطاقة مصنوعة آليًا من ويكي بيانات (CC0) وويكيبيديا (CC BY-SA 4.0) وويكيميديا كومنز وOpenStreetMap ‏(ODbL).", "Page built automatically from Wikidata (CC0), Wikipedia (CC BY-SA 4.0), Wikimedia Commons and OpenStreetMap (ODbL).")}</li>
    <li>{U("Une erreur ? Corrigez-la sur Wikidata ou OpenStreetMap, ou écrivez-nous (Votre avis) : la page est refaite tous les 3 mois.", "خطأ؟ صحّحه في ويكي بيانات أو OpenStreetMap، أو اكتب لنا (رأيك): تُحدَّث الصفحة كل 3 أشهر.", "A mistake? Correct it on Wikidata or OpenStreetMap, or write to us (Your feedback): the page is rebuilt every 3 months.")}</li></ul></section>
</main>"""
    titre = f"{nom}{(' — ' + ville_fr) if ville_fr else ''} | Mosquées en Tunisie"
    desc = (f.get("resume", {}).get("fr") or f.get("resume", {}).get("en") or f"{nom} : mosquée de Tunisie ({ville_fr}). Photo, histoire, carte et liens.")[:200]
    # autres langues : proposées à Google seulement si Wikidata / Wikipédia donnent un nom ou un résumé dans cette langue
    INDEX[chemin] = LANGUES if notre else ["fr"] + [x for x in LANGUES[1:] if noms.get(x) or f.get("resume", {}).get(x)]
    META[chemin] = {}
    for x in LANGUES[1:]:
        vx = (ville_ar or ville_fr) if x in ("ar", "ur") else ville_fr
        nx = noms.get(x) or (noms.get("ar") if x == "ur" else None) or nom
        META[chemin][x] = (f"{nx}{(' — ' + vx) if vx else ''} | {PL.SITE[x]}",
                           ((textes.D("descriptions", f["qid"])[x] if notre else None) or f.get("resume", {}).get(x) or PL.FICHE_DESC[x].format(nom=nx, ville=f" ({vx})" if vx else ""))[:200])
    jsonld = [{"@context": "https://schema.org", "@type": "Mosque", "name": nom, "url": BASE + chemin,
               "alternateName": [x for x in (noms.get("ar"), noms.get("en")) if x and x != nom],
               "geo": {"@type": "GeoCoordinates", "latitude": l["lat"], "longitude": l["lon"]},
               "address": {"@type": "PostalAddress", **({"addressLocality": ville_fr} if ville_fr else {}), "addressCountry": "TN"},
               **({"image": ph["url"]} if ph else {}), "sameAs": [f"https://www.wikidata.org/wiki/{f['qid']}"]}]
    if notre:
        desc = textes.D("descriptions", f["qid"])["fr"][:200]
    if notre or djerba:
        CLE_TRAD[chemin] = page
    ecrire(chemin + "index.html", document(chemin + "index.html", titre, desc, corps, tete=[f"trad/{page}.js"] if (notre or djerba) else (),
                                           bas=["assets/fiche.js"], jsonld=jsonld))


# ---------- liste de toutes les pages ----------
def tri_html(page, cible, options=("t_page", "t_ancien", "t_recent", "t_az")):
    """Liste « Trier » (demande d'Ahmed du 23/10/2026) : assets/pages.js range les éléments [data-i] de la cible."""
    return (f'<p class="tri"><label><span class="tri-t">{X("tri", "trier", page)}</span> <select data-tri="{cible}">'
            + "".join(f'<option value="{o[2:]}">{textes.D("tri", o)["fr"]}</option>' for o in options) + "</select></label>"
            + "".join(f'<span hidden data-txt="{o}">{X("tri", o, page)}</span>' for o in options) + "</p>")


def carte_grande(g, photos, r, page, i=0):
    ph = (photos.get(g["slug"]) or [None])[0]
    img = f'<img src="{r}{ph["fichier"]}" alt="" loading="lazy" width="{ph["w"]}" height="{ph["h"]}">' if ph else ""
    return (f'<a class="mq-grande" href="{r}mosquee/{g["slug"]}/" data-i="{i}" data-an="{PN.ANNEES_GRANDES[g["slug"]]}"><span class="mq-grande-img">{img}</span>'
            f'<span class="mq-grande-txt"><b>{S(g["nom"], page)}</b><small>{S(VILLES[g["ville"]], page)} · {S(g["epoque"], page)}</small></span></a>')


def page_liste(lieux, pages, photos):
    page = "liste"
    CLE_TRAD["grandes-mosquees/"] = page
    grandes = "".join(carte_grande(g, photos, "../", page, i) for i, g in enumerate(GRANDES))
    grandes_chemins = {"mosquee/" + g["slug"] + "/" for g in GRANDES}
    autres = [(l, pages[l["id"]]) for l in lieux if l["id"] in pages and pages[l["id"]] not in grandes_chemins]
    par_ville = {}
    for l, p in autres:
        v = l.get("ville") or {}
        cle = v.get("region_fr") or v.get("fr") or "—"
        par_ville.setdefault(cle, []).append((l, p, v))
    groupes = []
    for cle in sorted(par_ville, key=lambda x: ascii_slug(x)):
        items = sorted(par_ville[cle], key=lambda x: ascii_slug(nom_principal(x[0]["noms"])))
        v0 = items[0][2]
        titre_ar = v0.get("region_ar") if v0.get("region_fr") else v0.get("ar")
        h = f'<span class="nl" data-nl="fr">{esc(cle)}</span><span class="nl" data-nl="ar" lang="ar">{esc(titre_ar or cle)}</span>'
        lis = "".join(
            f'<li><a href="../{p}">{noms_spans(l["noms"]) or esc(nom_principal(l["noms"]))}</a>'
            f'{" <small>" + str(l["fiche"]["annee"]) + "</small>" if l["fiche"].get("annee") else ""}'
            f'{" <i class=" + chr(34) + "mq-pastille" + chr(34) + " title=" + chr(34) + "photo" + chr(34) + "></i>" if l["fiche"].get("photo") else ""}</li>'
            for l, p, v in items)
        groupes.append(f'<section class="mq-groupe"><h3>{h}</h3><ul class="mq-liens mq-noms">{lis}</ul></section>')
    # recherche (23/10/2026) : liste tunisienne filtrée + grandes mosquées du monde (Wikidata) ; QID -> notre page
    qids = {g["qid"]: "mosquee/" + g["slug"] + "/" for g in GRANDES}
    qids.update({l["fiche"]["qid"]: p for l, p in autres})
    exemples = [("ex_mecque", "Mecca"), ("ex_medine", "Medina"), ("ex_jerusalem", "Jerusalem"), ("ex_istanbul", "Istanbul"),
                ("ex_caire", "Cairo"), ("ex_maroc", "Morocco"), ("ex_indonesie", "Indonesia")]
    recherche = (f'<form class="mq-cherche" id="mq-cherche" role="search" data-pages="{att(json.dumps(qids, separators=(",", ":")))}">'
                 f'<label for="mq-cherche-q">{X("recherche", "etiquette", page)}</label>'
                 f'<div class="mq-cherche-ligne"><input id="mq-cherche-q" type="search" autocomplete="off" maxlength="50" enterkeyhint="search">'
                 f'<button type="submit" class="btn-principal">{X("recherche", "bouton", page)}</button></div>'
                 f'<p class="mq-cherche-ex">{X("recherche", "exemples", page)} '
                 + "".join(f'<button type="button" class="chipbtn" data-ex="{q}">{X("recherche", c, page)}</button>' for c, q in exemples)
                 + "</p>" + TXT("recherche", ["ph", "attente", "aucune", "erreur", "court", "voir_carte", "notre_page", "wikipedia", "source", "tunisie_titre", "tunisie_aucune"], page)
                 + TXT("tri", ["trier", "t_connue", "t_ancien", "t_recent", "t_az", "av_jc"], page)
                 + "</form>")
    corps = f"""
<section class="hero">
  <div class="wrap">
    <p class="fil"><a href="../">{U("Accueil", "الرئيسية", "Home")}</a> › {U("Grandes mosquées", "الجوامع الكبرى", "Great mosques")}</p>
    <h1>{U("Grandes mosquées et mosquées historiques de Tunisie", "الجوامع الكبرى والمساجد التاريخية في تونس", "Great and historic mosques of Tunisia")}</h1>
    <p class="intro">{U("Les grandes mosquées racontées en détail, puis toutes les mosquées de Tunisie qui ont une fiche dans Wikidata : photo, histoire et liens.", "الجوامع الكبرى مع شرح مفصّل، ثم كل مساجد تونس التي لها بطاقة في ويكي بيانات: صورة وتاريخ وروابط.", "The great mosques described in detail, then every mosque in Tunisia that has a Wikidata record: photo, history and links.")}</p>
    <span class="maj"><b>{len(GRANDES) + len(autres)}</b>&nbsp;{U("pages de mosquées", "صفحة مساجد", "mosque pages")}</span>
    {recherche}
  </div>
</section>
<main class="wrap chevauche">
  <section class="carte mq-cherche-res" id="mq-cherche-res" hidden aria-live="polite">
    <h2>{X("recherche", "tunisie_titre", page)}</h2><div id="mq-tunisie-res"></div>
    <h2>{X("recherche", "monde_titre", page)}</h2><div id="mq-monde-res"></div>
  </section>
  <section class="carte" id="mq-liste"><h2>{U("Les grandes mosquées", "الجوامع الكبرى", "The great mosques")}</h2>{tri_html(page, "mq-grandes-liste")}<div class="mq-grandes" id="mq-grandes-liste">{grandes}</div>
    <p class="mq-voir-aussi"><a class="chipbtn" href="../grandes-mosquees-du-monde/">🌍 {X("tri", "monde_menu", page)} →</a> <a class="chipbtn" href="../histoires-des-mosquees/">{X("recherche", "lien_histoires", page)} →</a> <a class="chipbtn" href="../role-de-la-mosquee/">{X("recherche", "lien_role", page)} →</a></p></section>
  <section class="carte" id="historiques"><h2>{U("Autres mosquées historiques", "مساجد تاريخية أخرى", "Other historic mosques")} <span class="mq-compte">{len(autres)}</span></h2>
    <p class="aide">{U("Classées par ville. Le point vert signale une photo.", "مرتّبة حسب المدينة. النقطة الخضراء تعني وجود صورة.", "Sorted by town. The green dot means there is a photo.")}</p>
    {"".join(groupes)}</section>
</main>"""
    ecrire("grandes-mosquees/index.html", document("grandes-mosquees/index.html",
           "Grandes mosquées et mosquées historiques de Tunisie (photos, histoire) | Mosquées en Tunisie",
           "Zitouna, Grande Mosquée de Kairouan, Sousse, Mahdia, Sfax, Testour… et toutes les mosquées historiques de Tunisie : photos, histoire, architecture et liens. جوامع تونس الكبرى والتاريخية.",
           corps, tete=[f"trad/{page}.js"], bas=["assets/fiche.js", "assets/recherche.js", "assets/pages.js"]))
    return len(autres)


# ---------- pages ajoutées le 23/10/2026 (demande d'Ahmed) : rôle de la mosquée, construire une mosquée, histoires ----------
# Photos : liste ci-dessous (fichiers de Wikimedia Commons) ; auteur, licence et vignette lus une fois par
# `python tools/photos_pages.py` dans donnees/photos_pages.json (la construction n'utilise pas le réseau).
# Vidéos : identifiant YouTube vérifié (oEmbed : intégrable) ; lue par youtube-nocookie seulement après un appui (assets/pages.js).
import pages_nouvelles as PN  # noqa: E402


def photos_pages():
    p = os.path.join(RACINE, "donnees", "photos_pages.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


def figure_commons(fichier, nom, cle, page, credits):
    c = credits.get(fichier.replace("_", " "))
    if not c:
        raise SystemExit(f"donnees/photos_pages.json : pas de crédit pour « {fichier} » (lancer python tools/photos_pages.py)")
    return (f'<figure class="pg-photo"><span class="cadre-photo"><img src="{att(c["url"])}" alt="" loading="lazy"></span>'
            f'<figcaption>{X(nom, cle, page)} <small>{U("Photo", "صورة", "Photo")} : <a href="{att(c["page"])}" target="_blank" rel="noopener">{esc(c["auteur"])}</a>, '
            f'{esc(c["licence"])} — Wikimedia Commons</small></figcaption></figure>')


def video_yt(v, nom, page):
    return (f'<figure class="pg-video"><button type="button" class="pg-video-lire" data-yt="{att(v["id"])}">'
            f'<span class="pg-video-ico" aria-hidden="true">▶</span><span><b>{X(nom, v["cle"], page)}</b>'
            f'<small>{esc(v["chaine"])} · {esc(v["langue"])}{(" · " + esc(v["duree"])) if v.get("duree") else ""}</small>'
            f'<span class="pg-video-txt">{X("role", "lire_video", page)}</span></span></button></figure>')


def ecrire_page_libre(chemin, nom, corps, page, bas=("assets/pages.js",), jsonld=None):
    """Page de tools/textes/ : titre et description de chaque langue tirés des clés meta_titre (sinon titre) et intro."""
    t = textes.D(nom, "meta_titre" if "meta_titre" in textes.cles(nom) else "titre")
    d = textes.D(nom, "intro")
    CLE_TRAD[chemin] = page
    META[chemin] = {x: (f"{t[x]} | {PL.SITE[x]}", re.sub(r"\s+", " ", d[x])[:200]) for x in LANGUES}
    ecrire(chemin + "index.html", document(chemin + "index.html", META[chemin]["fr"][0], META[chemin]["fr"][1], corps,
                                           bas=list(bas), jsonld=jsonld))
    return chemin


def page_role(credits):
    nom, page, r = "role", "p-role", "../"
    etapes = []
    for e in PN.ROLE_ETAPES:
        k = e["cle"]
        blocs = []
        for x in e["contenu"]:
            if x.startswith("liste:"):
                blocs.append('<ul class="pg-liste">' + "".join(f"<li>{X(nom, c, page)}</li>" for c in x[6:].split(",")) + "</ul>")
            else:
                blocs.append(f"<p>{X(nom, x, page)}</p>")
        photos = "".join(figure_commons(f, nom, c, page, credits) for f, c in e.get("photos", []))
        etapes.append(f'<section class="carte pg-etape" id="{k}"><p class="pg-date">{X(nom, k + "_date", page)}</p>'
                      f'<h2>{X(nom, k + "_titre", page)}</h2>{"".join(blocs)}'
                      + (f'<div class="pg-photos">{photos}</div>' if photos else "") + "</section>")
    sommaire = "".join(f'<li><a href="#{e["cle"]}"><b>{X(nom, e["cle"] + "_date", page)}</b> {X(nom, e["cle"] + "_titre", page)}</a></li>' for e in PN.ROLE_ETAPES)
    videos = "".join(video_yt(v, nom, page) for v in PN.ROLE_VIDEOS)
    corps = f"""
<section class="hero">
  <div class="wrap">
    <p class="fil"><a href="{r}">{U("Accueil", "الرئيسية", "Home")}</a> › {X(nom, "menu", page)}</p>
    <h1>{X(nom, "titre", page)}</h1>
    <p class="intro">{X(nom, "intro", page)}</p>
  </div>
</section>
<main class="wrap chevauche">
  <nav class="carte pg-sommaire"><h2>{X(nom, "sommaire", page)}</h2><ol>{sommaire}</ol></nav>
  {"".join(etapes)}
  {f'<section class="carte" id="videos"><h2>{X(nom, "videos_titre", page)}</h2><div class="pg-videos">{videos}</div><p class="aide">{X(nom, "videos_note", page)}</p></section>' if videos else ""}
  <section class="carte" id="plus"><h2>{X(nom, "voir_aussi", page)}</h2><ul class="mq-liens">
    <li><a href="{r}histoires-des-mosquees/">{X(nom, "lien_histoires", page)}</a></li>
    <li><a href="{r}construire-une-mosquee/">{X(nom, "lien_construire", page)}</a></li>
    <li><a href="{r}grandes-mosquees/">{X(nom, "lien_grandes", page)}</a></li></ul></section>
  <section class="carte" id="sources"><h2>{X(nom, "sources_titre", page)}</h2><p class="aide">{X(nom, "sources_txt", page)}</p></section>
</main>"""
    jsonld = [{"@context": "https://schema.org", "@type": "Article", "headline": textes.D(nom, "titre")["fr"], "inLanguage": "fr",
               "datePublished": "2026-10-23", "author": {"@type": "Organization", "name": "Mosquées de Tunisie et du monde"}}]
    return ecrire_page_libre("role-de-la-mosquee/", nom, corps, page, jsonld=jsonld)


def histoire_html(h, page, niveau="h3"):
    cle, nature, sources = h
    src = " · ".join(f'<a href="{att(u)}" target="_blank" rel="noopener">{esc(t)}</a>' for t, u in sources)
    return (f'<article class="hi-histoire"><p class="hi-nature hi-{nature}">{X("histoires", "n_" + nature, page)}</p>'
            f'<{niveau}>{X("histoires", cle + "_t", page)}</{niveau}><p>{X("histoires", cle + "_r", page)}</p>'
            f'<p class="hi-source">{X("histoires", "source", page)} {src}</p></article>')


def section_histoires(slug, page, r="../../"):
    """Partie « Histoires et récits » d'une grande mosquée (vide si aucune histoire vérifiée)."""
    hs = PN.HISTOIRES_TUNISIE.get(slug)
    if not hs:
        return ""
    return (f'<section class="carte" id="histoires"><h2>{X("histoires", "section_page", page)}</h2>'
            + "".join(histoire_html(h, page) for h in hs)
            + f'<p><a href="{r}histoires-des-mosquees/">{X("histoires", "toutes", page)} →</a></p></section>')


def page_histoires():
    nom, page, r = "histoires", "p-histoires", "../"
    saintes = "".join(f'<section class="carte hi-groupe" id="{g[2:]}"><h2>{X(nom, g, page)}</h2>'
                      + "".join(histoire_html(h, page) for h in hs) + "</section>" for g, hs in PN.HISTOIRES_SAINTES)
    tunisie = "".join(f'<section class="carte hi-groupe" id="{g["slug"]}"><h2><a href="{r}mosquee/{g["slug"]}/">{S(g["nom"], page)}</a></h2>'
                      + "".join(histoire_html(h, page) for h in PN.HISTOIRES_TUNISIE[g["slug"]]) + "</section>"
                      for g in GRANDES if g["slug"] in PN.HISTOIRES_TUNISIE)
    sommaire = ("".join(f'<li><a href="#{g[2:]}">{X(nom, g, page)}</a></li>' for g, _ in PN.HISTOIRES_SAINTES)
                + "".join(f'<li><a href="#{g["slug"]}">{S(g["nom"], page)}</a></li>' for g in GRANDES if g["slug"] in PN.HISTOIRES_TUNISIE))
    corps = f"""
<section class="hero">
  <div class="wrap">
    <p class="fil"><a href="{r}">{U("Accueil", "الرئيسية", "Home")}</a> › {X(nom, "menu", page)}</p>
    <h1>{X(nom, "titre", page)}</h1>
    <p class="intro">{X(nom, "intro", page)}</p>
  </div>
</section>
<main class="wrap chevauche">
  <nav class="carte pg-sommaire"><ol>{sommaire}</ol></nav>
  <h2 class="hi-titre">{X(nom, "titre_saintes", page)}</h2>
  {saintes}
  <h2 class="hi-titre">{X(nom, "titre_tunisie", page)}</h2>
  {tunisie}
  <section class="carte"><p class="aide">{X(nom, "note", page)}</p>
    <ul class="mq-liens"><li><a href="{r}role-de-la-mosquee/">{X("role", "titre", page)}</a></li>
    <li><a href="{r}construire-une-mosquee/">{X("role", "lien_construire", page)}</a></li></ul></section>
</main>"""
    return ecrire_page_libre("histoires-des-mosquees/", nom, corps, page)


def page_construire():
    nom, page, r = "construire", "p-construire", "../"
    coran = "".join(f'<figure class="cs-texte"><blockquote lang="ar" dir="rtl" class="cs-arabe">{esc(t)}</blockquote>'
                    f'<figcaption><p class="mq-verset-trad">{X(nom, c, page)}</p><p class="mq-verset-source">{X(nom, c + "_ref", page)} — {X(nom, "traducteur", page)}, '
                    f'<a href="https://quranenc.com/" target="_blank" rel="noopener">QuranEnc.com</a> · '
                    f'<a href="https://quran.com/{v.replace(":", "/")}" target="_blank" rel="noopener">{X(nom, "lire_verset", page)}</a></p></figcaption></figure>'
                    for v, t, c in PN.CORAN)
    hadiths = "".join(f'<figure class="cs-texte"><blockquote lang="ar" dir="rtl" class="cs-arabe">{esc(t)}</blockquote>'
                      f'<figcaption><p>{X(nom, k + "_sens", page)}</p><p class="hi-source"><a href="{att(u)}" target="_blank" rel="noopener">{X(nom, k + "_ref", page)}</a></p></figcaption></figure>'
                      for k, t, u in PN.HADITHS)
    orgs = "".join(
        f'<li class="cs-org"><b>{esc(n)}</b><small>{X(nom, "pays", page)} {X(nom, p, page)}</small><p>{X(nom, d, page)}</p>'
        f'<p class="mq-monde-liens"><a class="chipbtn" href="{att(u)}" target="_blank" rel="noopener">{X(nom, "page_dons", page)} ↗</a>'
        + "".join(f' <a class="chipbtn" href="{att(au)}" target="_blank" rel="noopener">{X(nom, "appli", page)} : {esc(m)}</a>' for m, au in apps)
        + "</p></li>" for n, p, d, u, apps in PN.ORGANISMES)
    corps = f"""
<section class="hero">
  <div class="wrap">
    <p class="fil"><a href="{r}">{U("Accueil", "الرئيسية", "Home")}</a> › {X(nom, "menu", page)}</p>
    <h1>{X(nom, "titre", page)}</h1>
    <p class="intro">{X(nom, "intro", page)}</p>
  </div>
</section>
<main class="wrap chevauche">
  <section class="carte" id="bienfaits"><h2>{X(nom, "bienfaits_titre", page)}</h2>
    <h3>{X(nom, "coran_titre", page)}</h3>{coran}<p class="aide">{X(nom, "coran_note", page)}</p>
    <h3>{X(nom, "hadiths_titre", page)}</h3>{hadiths}
    <h3>{X(nom, "social_titre", page)}</h3><p>{X(nom, "social_p", page)}</p></section>
  <section class="carte" id="organismes"><h2>{X(nom, "orgs_titre", page)}</h2><p class="cs-avert">{X(nom, "orgs_avert", page)}</p>
    <ul class="cs-orgs">{orgs}</ul></section>
  <section class="carte" id="tunisie"><h2>{X(nom, "tunisie_titre", page)}</h2><p>{X(nom, "tunisie_p1", page)}</p><p>{X(nom, "tunisie_p2", page)}</p>
    <p><a href="{PN.SICAD}" target="_blank" rel="noopener">{X(nom, "tunisie_lien", page)} ↗</a></p></section>
  <section class="carte" id="aider"><h2>{X(nom, "autres_titre", page)}</h2><p>{X(nom, "autres_p", page)}</p>
    <p><a class="chipbtn" href="{r}#signaler">{X(nom, "signaler", page)}</a></p></section>
  <section class="carte"><ul class="mq-liens"><li><a href="{r}role-de-la-mosquee/">{X("role", "titre", page)}</a></li>
    <li><a href="{r}histoires-des-mosquees/">{X("role", "lien_histoires", page)}</a></li></ul>
    <h2>{X("role", "sources_titre", page)}</h2><p class="aide">{X(nom, "sources_txt", page)}</p></section>
</main>"""
    return ecrire_page_libre("construire-une-mosquee/", nom, corps, page)


def nl_spans(d, classe):
    """Le texte dans chaque langue disponible (assets/fiche.js montre celui de la langue de la page)."""
    return f'<span class="{classe}">' + "".join(f'<span class="nl" data-nl="{l}" lang="{l}">{esc(d[l])}</span>' for l in LANGUES if d.get(l)) + "</span>"


def page_monde():
    """grandes-mosquees-du-monde/ (demande d'Ahmed du 23/10/2026) : donnees/monde_grandes.json (tools/monde_grandes.py), tri par
    date, nom ou notoriété ; description (résumé Wikipédia) chargée seulement à l'ouverture, depuis donnees/monde/<langue>.json."""
    nom, page, r = "tri", "p-monde", "../"
    src = os.path.join(RACINE, "donnees", "monde_grandes.json")
    if not os.path.exists(src):
        return []
    ms = json.load(open(src, encoding="utf-8"))["mosquees"]
    tunisie = {g["qid"]: g["slug"] for g in GRANDES}
    cartes = []
    for i, m in enumerate(ms):
        ph = m.get("photo")
        img = f'<img src="{att(ph["url"])}" alt="" loading="lazy" referrerpolicy="no-referrer">' if ph else ""
        an = m.get("an")
        an_txt = (f'{-an} {X(nom, "av_jc", page)}' if an < 0 else str(an)) if an is not None else X(nom, "date_inconnue", page)
        liens = []
        if m["q"] in tunisie:
            liens.append(f'<a class="btn-principal" href="{r}mosquee/{tunisie[m["q"]]}/">{X("recherche", "notre_page", page)}</a>')
        if m.get("pos"):
            liens.append(f'<a class="chipbtn" href="{r}?ll={m["pos"][0]},{m["pos"][1]}#carte">{X("recherche", "voir_carte", page)}</a>')
        cartes.append(
            f'<article class="mq-monde-res mo-carte" data-i="{i}" data-an="{an if an is not None else ""}" data-n="{m["n"]}" data-q="{m["q"]}">'
            f'<span class="mq-monde-img">{img}</span><div><b class="mo-an">{an_txt}</b>{nl_spans(m["noms"], "mq-noms mo-nom")}'
            f'<small>{nl_spans(m["pays"], "mq-noms") if m.get("pays") else ""} · {m["n"]} {X(nom, "articles", page)}</small>'
            f'<details class="mo-desc"><summary>{X("descriptions", "titre_monde", page)}</summary><div class="mo-desc-txt"></div></details>'
            + (f'<p class="mq-monde-liens">{" ".join(liens)}</p>' if liens else "")
            + (f'<small class="mo-credit">{U("Photo", "صورة", "Photo")} : <a href="{att(ph["page"])}" target="_blank" rel="noopener">{esc(ph["auteur"])}</a>, {esc(ph["licence"])}</small>' if ph else "")
            + "</div></article>")
    # descriptions par langue : résumé Wikipédia de la langue, sinon anglais, sinon français, sinon arabe, sinon description courte Wikidata
    for l in LANGUES:
        out = {}
        for m in ms:
            rl = next((x for x in (l, "en", "fr", "ar") if m.get("resume", {}).get(x)), None)
            dl = next((x for x in (l, "en", "fr") if m.get("desc", {}).get(x)), None)
            e = {}
            if rl:
                e = {"r": m["resume"][rl], "rl": rl, "w": f"https://{rl}.wikipedia.org/wiki/" + m["wiki"][rl].replace(" ", "_")}
            elif dl:
                e = {"d": m["desc"][dl]}
            if e:
                out[m["q"]] = e
        ecrire(f"donnees/monde/{l}.json", json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n")
    corps = f"""
<section class="hero">
  <div class="wrap">
    <p class="fil"><a href="{r}">{U("Accueil", "الرئيسية", "Home")}</a> › <a href="{r}grandes-mosquees/">{U("Grandes mosquées", "الجوامع الكبرى", "Great mosques")}</a> › {X(nom, "monde_menu", page)}</p>
    <h1>{X(nom, "monde_titre", page)}</h1>
    <p class="intro">{X(nom, "monde_intro", page)}</p>
    <span class="maj"><b>{len(ms)}</b>&nbsp;{X(nom, "monde_menu", page)}</span>
  </div>
</section>
<main class="wrap chevauche">
  <section class="carte" id="liste">{tri_html(page, "mo-liste", ("t_connue", "t_ancien", "t_recent", "t_az"))}
    <div class="mq-monde-grille" id="mo-liste">{"".join(cartes)}</div>
    {TXT("descriptions", ["wiki_extrait", "pas_de_desc"], page)}
    <p class="aide">{X(nom, "monde_note", page)}</p>
    <p class="mq-voir-aussi"><a class="chipbtn" href="{r}grandes-mosquees/">{X("recherche", "etiquette", page)} →</a></p></section>
</main>"""
    t = textes.D(nom, "monde_titre"); dd = textes.D(nom, "monde_intro")
    chemin = "grandes-mosquees-du-monde/"
    CLE_TRAD[chemin] = page
    META[chemin] = {x: (f"{t[x]} | {PL.SITE[x]}", dd[x][:200]) for x in LANGUES}
    ecrire(chemin + "index.html", document(chemin + "index.html", META[chemin]["fr"][0], META[chemin]["fr"][1], corps,
                                           bas=["assets/fiche.js", "assets/pages.js"]))
    return [chemin]


def PN_construire(credits):
    """Les nouvelles pages, dans l'ordre du plan du site."""
    return [page_role(credits), page_histoires(), page_construire()] + page_monde()


def diapo_accueil(photos):
    """Photo du bandeau de l'accueil (entre <!-- diapo:debut --> et <!-- diapo:fin -->) : les grandes mosquées défilent
    toutes les 3 secondes (demande d'Ahmed du 11/10/2026 : « ça donne une vie au site ») ; Kairouan d'abord ; chaque photo
    mène à la page de sa mosquée, son crédit (auteur + licence) s'affiche dessous. Sans JavaScript : Kairouan seule."""
    ordre = sorted(GRANDES, key=lambda g: g["slug"] != "kairouan")
    vues, legendes = [], []
    for i, g in enumerate(x for x in ordre if photos.get(x["slug"])):
        ph = photos[g["slug"]][0]
        actif = ' actif' if i == 0 else ''
        cache = '' if i == 0 else ' aria-hidden="true"'
        lent = '' if i == 0 else ' loading="lazy"'
        vues.append(f'<a class="diapo-vue{actif}" href="mosquee/{g["slug"]}/" tabindex="{0 if i == 0 else -1}"{cache}>'
                    f'<img src="{ph["fichier"]}" alt="" width="{ph["w"]}" height="{ph["h"]}"{lent}></a>')
        legendes.append(f'<figcaption class="diapo-legende{actif}"{"" if i == 0 else " hidden"}><b>{S(g["nom"], "accueil")}</b> '
                        f'{U("Photo", "صورة", "Photo")} : <a href="{att(ph["source"])}" rel="noopener" target="_blank">{esc(ph["auteur"])}</a>, '
                        f'{esc(ph["licence"])}</figcaption>')
    return ('<figure class="illus diapo" data-diapo><span class="cadre-photo">' + "".join(vues) + "</span>" + "".join(legendes) + "</figure>")


def grille_accueil(photos):
    """Grille des grandes mosquées de l'accueil (entre les repères <!-- grandes:debut --> et <!-- grandes:fin -->)."""
    return (tri_html("accueil", "mq-grandes-acc") + '<div class="mq-grandes" id="mq-grandes-acc">'
            + "".join(carte_grande(g, photos, "", "accueil", i) for i, g in enumerate(GRANDES)) + "</div>"
            + f'<p class="mq-voir-aussi"><a class="chipbtn" href="grandes-mosquees-du-monde/">🌍 {X("tri", "monde_menu", "accueil")} →</a></p>')


def ecrire_trad():
    os.makedirs(os.path.join(RACINE, "assets", "trad"), exist_ok=True)
    for page, par_l in TRAD.items():
        texte = ("/* GÉNÉRÉ par tools/construire.py (textes : tools/contenu_grandes_*.py) — traductions turc, indonésien, ourdou, allemand, espagnol\n"
                 "   de cette page, ajoutées à window.TRADUCTIONS (assets/langues.js) ; clé = texte français exact. */\n"
                 "(function (T) {\n" + "".join(
                     f"  Object.assign(T.{l} = T.{l} || {{}}, {json.dumps(par_l.get(l, {}), ensure_ascii=False, indent=0, sort_keys=True)});\n" for l in ANCIENNES)
                 + "})(window.TRADUCTIONS = window.TRADUCTIONS || {});\n")
        ecrire(f"assets/trad/{page}.js", texte)


def sitemap(chemins):
    maj = f"{VERSION[:4]}-{VERSION[4:6]}-{VERSION[6:8]}"   # date de la dernière modification (tirée de VERSION) : aide Google à repasser
    lignes = "".join(f"  <url><loc>{BASE}{c}</loc><lastmod>{maj}</lastmod></url>\n" for c in chemins)
    ecrire("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + lignes + "</urlset>\n")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    d, photos = charger()
    pages = pages_fiches(d["lieux"])
    donnees_carte(d, pages)
    wiki_par_qid = {}
    meta_wiki = os.path.join(ICI, "wiki_grandes.json")
    if os.path.exists(meta_wiki):
        wiki_par_qid = json.load(open(meta_wiki, encoding="utf-8"))
    for l in d["lieux"]:
        if l.get("fiche"):
            wiki_par_qid.setdefault(l["fiche"]["qid"], l["fiche"].get("wiki", {}))
    for g in GRANDES:
        page_grande(g, photos, wiki_par_qid)
    grandes_chemins = {"mosquee/" + g["slug"] + "/" for g in GRANDES}
    n_fiches = 0
    for l in d["lieux"]:
        p = pages.get(l["id"])
        if p and p not in grandes_chemins:
            page_fiche(l, p); n_fiches += 1
    n_autres = page_liste(d["lieux"], pages, photos)
    # gabarits écrits à la main
    dossier = os.path.join(ICI, "gabarits")
    gabarits = []
    for nom in sorted(os.listdir(dossier)):
        if nom.endswith(".html"):
            meta, corps = lire_gabarit(os.path.join(dossier, nom))
            chemin = nom[:-5].replace("__", "/") + "/index.html"
            if "{{credits_photos}}" in corps:
                noms_fr = {g["slug"]: g["nom"]["fr"] for g in GRANDES}
                corps = corps.replace("{{credits_photos}}", "".join(
                    f'<li><a href="../mosquee/{s}/">{esc(noms_fr.get(s, s))}</a> : '
                    + ", ".join(f'<a href="{att(p["source"])}" target="_blank" rel="noopener">{esc(p["auteur"])}</a> ({esc(p["licence"])})' for p in ps) + "</li>"
                    for s, ps in photos.items())
                    + f'<li>{U("Photos des autres mosquées : affichées depuis Wikimedia Commons, auteur et licence sous chaque photo.", "صور المساجد الأخرى: معروضة من ويكيميديا كومنز، المؤلف والرخصة تحت كل صورة.", "Photos of the other mosques: shown from Wikimedia Commons, author and licence under each photo.")}</li>')
            ecrire(chemin, document(chemin, meta["titre"], meta["description"], corps,
                                    bas=[s.strip() for s in meta.get("scripts", "").split(",") if s.strip()]))
            gabarits.append(chemin.rsplit("index.html", 1)[0])
    # pages ajoutées le 23/10/2026 (tools/textes/, 21 langues)
    credits = photos_pages()
    gabarits += PN_construire(credits)
    # accueil (écrit à la main) : une seule version ?v=, grille des grandes mosquées
    for g in GRANDES:
        carte_grande(g, photos, "", "accueil")
    grille_accueil(photos)
    acc = os.path.join(RACINE, "index.html")
    if os.path.exists(acc):
        t = open(acc, encoding="utf-8").read()
        t2 = re.sub(r"\?v=\d{8}[a-z]", "?v=" + VERSION, t)
        # même en-tête de langue que les autres pages (langue fixée par l'adresse, liens hreflang vers ar/, en/, tr/…)
        t2 = re.sub(r'<html lang="fr" dir="ltr" translate="no"[^>]*>', '<html lang="fr" dir="ltr" translate="no" data-racine="" data-chemin="" data-fixe>', t2, count=1)
        t2 = re.sub(r'(?:<link rel="alternate" hreflang="[^"]*" href="[^"]*">\n)+', lambda m: PL.liens_hreflang(BASE, "", LANGUES), t2, count=1)
        t2 = re.sub(r"<!-- grandes:debut -->.*?<!-- grandes:fin -->", lambda m: "<!-- grandes:debut -->" + grille_accueil(photos) + "<!-- grandes:fin -->", t2, flags=re.S)
        t2 = re.sub(r"<!-- diapo:debut -->.*?<!-- diapo:fin -->", lambda m: "<!-- diapo:debut -->" + diapo_accueil(photos) + "<!-- diapo:fin -->", t2, flags=re.S)
        if t2 != t:
            open(acc, "w", encoding="utf-8", newline="\n").write(t2)
    ecrire_trad()
    chemins = [""] + ["grandes-mosquees/"] + gabarits + sorted(grandes_chemins) + sorted(p for p in set(pages.values()) if p not in grandes_chemins)
    # pages devenues vides ou disparues (le robot trimestriel a changé les données) : supprimées, jamais de page orpheline
    import shutil
    garder = set(grandes_chemins) | set(pages.values())
    for nom in sorted(os.listdir(os.path.join(RACINE, "mosquee"))):
        if "mosquee/" + nom + "/" not in garder:
            shutil.rmtree(os.path.join(RACINE, "mosquee", nom))
            print("page retirée :", "mosquee/" + nom + "/")
    # une vraie page par langue (ar/, en/, tr/ … ro/ : 20 dossiers), tirée de chaque page française
    CLE_TRAD[""] = "accueil"; META[""] = PL.ACCUEIL
    langues_js = PL.lire_traductions(os.path.join(RACINE, "assets", "langues.js"))
    for l in langues_plus.PLUS:                                   # interface des 7 nouvelles langues : mêmes clés que langues.js
        langues_js[l] = {k: PLUS[l][k] for k in UI_PLUS}
    if set(UI_PLUS) != set(langues_js["tr"]):
        raise SystemExit("tools/langues_plus/_francais.json (« ui ») n'a pas les mêmes textes que assets/langues.js : "
                         + " | ".join(sorted(set(langues_js["tr"]) ^ set(UI_PLUS))[:5]))
    for l in NOUVELLES:
        ecrire(f"assets/l/{l}.js", "/* GÉNÉRÉ par tools/construire.py (assets/langues.js et tools/langues_plus/) — textes d'interface de cette langue,\n"
               "   chargés seulement par les pages de cette langue ; clé = texte français exact. */\n"
               f"window.TRADUCTIONS = window.TRADUCTIONS || {{}};\nwindow.TRADUCTIONS.{l} = "
               + json.dumps(langues_js[l], ensure_ascii=False, indent=0, sort_keys=True) + ";\n")
    for l in LANGUES[1:]:
        if os.path.isdir(os.path.join(RACINE, l)):
            shutil.rmtree(os.path.join(RACINE, l))
    adresses, manque = [], 0
    for c in chemins:
        fr = open(os.path.join(RACINE, c, "index.html"), encoding="utf-8").read()
        langues = INDEX.get(c, LANGUES)
        adresses.append(c)
        for l in LANGUES[1:]:
            trad = {**langues_js.get(l, {}), **TRAD.get(CLE_TRAD.get(c, ""), {}).get(l, {})}
            texte, m = PL.variante(fr, BASE, c, l, langues, trad, META.get(c, {}).get(l), indexer=l in langues)
            ecrire(f"{l}/{c}index.html", texte)
            manque += m
            if l in langues:
                adresses.append(f"{l}/{c}")
    sitemap(adresses)
    # page vidéo (video/) tirée de la page À propos (mêmes en-tête, CSP, ?v=) : outil vidéos d'Ahmed ; s'ajoute au sitemap
    if os.path.exists(os.path.join(ICI, "page_video.json")):
        from page_video import pages_video
        pages_video(RACINE)
    print(f"{len(GRANDES)} grandes mosquées, {n_fiches} autres pages de mosquées, {len(adresses)} adresses dans le sitemap "
          f"({len(chemins)} pages en {len(LANGUES)} langues, moins les versions sans contenu propre), {manque} texte(s) resté(s) en anglais, version {VERSION}")


if __name__ == "__main__":
    sys.exit(main())
