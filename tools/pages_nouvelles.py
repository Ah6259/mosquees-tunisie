# -*- coding: utf-8 -*-
"""Plan des pages ajoutées le 23/10/2026 (demande d'Ahmed) — les TEXTES sont dans tools/textes/ (21 langues), ici seulement
l'ordre des parties, les photos (fichiers de Wikimedia Commons, crédits lus par tools/photos_pages.py) et les vidéos YouTube
(identifiants vérifiés intégrables le 23/10/2026)."""

# Le rôle de la mosquée (role-de-la-mosquee/) : une partie par époque ; « liste:a,b » = liste à puces de ces clés ;
# photos = [(fichier Commons, clé de la légende dans tools/textes/base/role.json)]
ROLE_ETAPES = [
    {"cle": "e1", "contenu": ["e1_p1", "e1_p2", "liste:e1_l1,e1_l2,e1_l3,e1_l4,e1_l5,e1_l6"],
     "photos": [("Khalili Collection Hajj and Arts of Pilgrimage Arc.pp-0254.11.jpg", "ph_e1_a"), ("Quba Mosque Full Picture (2024).jpg", "ph_e1_b")]},
    {"cle": "e2", "contenu": ["e2_p1", "e2_p2"],
     "photos": [("The Umayyad Mosque, Courtyard, Damascus, Syria.jpg", "ph_e2_a"), ("Courtyard and minaret of the Great Mosque of Kairouan, Tunisia.jpg", "ph_e2_b")]},
    {"cle": "e3", "contenu": ["e3_p1", "e3_p2"],
     "photos": [("A Library in Golden Islamic Age.jpg", "ph_e3_a"), ("Qadi Abbasid - Maqamat Harir 1237.jpg", "ph_e3_b"),
                ("Qarawiyyin courtyard and pavilion.jpg", "ph_e3_c"), ("La salle de prière de la grande Mosquée ez Zitouna (Medina de Tunis) (49802391061).jpg", "ph_e3_d")]},
    {"cle": "e4", "contenu": ["e4_p1", "e4_p2"],
     "photos": [("Süleymaniye Camii - İstanbul Üniversitesi - Aerial view.jpg", "ph_e4_a"), ("Istanbul Süleymaniye complex Imaret in 2009 7050.jpg", "ph_e4_b")]},
    {"cle": "e5", "contenu": ["e5_p1"],
     "photos": [("Tunisia - Pre-School in the early 1900s.jpg", "ph_e5_a"),
                ("Binnenplaats van de Al-Azhar-moskee te Caïro met studenten Le Caire. Mosquée el-Azhar, les etudiants. (titel op object), RP-F-00-4163.jpg", "ph_e5_b")]},
    {"cle": "e6", "contenu": ["e6_p1", "liste:e6_l1,e6_l2,e6_l3,e6_l4"],
     "photos": [("Kocatepe Mosque friday prayers DSCF8876.jpg", "ph_e6_a"), ("Hidangan Buka Puasa di Masjid Nabawi.jpg", "ph_e6_b")]},
]
# vidéos : {"id": identifiant YouTube, "cle": clé du titre dans role.json, "chaine": nom de la chaîne, "langue": langue parlée}
# (vérifiées intégrables par oEmbed le 23/10/2026 ; les reportages de la série UNESCO/NHK ont une musique de fond : écartés)
ROLE_VIDEOS = [
    {"id": "fsbBC1dgUbo", "cle": "v_qarawiyyin", "chaine": "Al Jazeera English", "langue": "English", "duree": "2:26"},
    {"id": "Q48ddBmCjQA", "cle": "v_suleymaniye", "chaine": "Smarthistory", "langue": "English", "duree": "6:37"},
]


def fichiers_photos():
    """Tous les fichiers de Wikimedia Commons utilisés par ces pages (pour tools/photos_pages.py)."""
    return sorted({f for e in ROLE_ETAPES for f, _ in e.get("photos", [])})


# Histoires des mosquées (histoires-des-mosquees/ + partie « Histoires et récits » de chaque grande mosquée de Tunisie).
# Chaque histoire : (clé dans tools/textes/base/histoires.json — <clé>_t titre, <clé>_r récit —, nature, [(source, adresse)])
# nature : coran, sahih, faible, fait, tradition, legende, croyance (clés n_… de histoires.json)
SUNNAH = "https://sunnah.com/"
HISTOIRES_SAINTES = [
    ("g_medine", [
        ("medine_1", "faible", [("Ibn Hajar, al-Isaba (récit) ; Ibn Majah 760", "https://hadithprophet.com/hadith-42080.html")]),
        ("medine_2", "sahih", [("al-Bukhari 3584", SUNNAH + "bukhari:3584")]),
        ("medine_3", "sahih", [("al-Bukhari 6452", SUNNAH + "bukhari:6452")]),
        ("medine_4", "sahih", [("al-Bukhari 3906", SUNNAH + "bukhari:3906")]),
        ("medine_5", "sahih", [("Abu Dawud 499", SUNNAH + "abudawud:499")]),
    ]),
    ("g_quba", [("quba_1", "coran", [("Coran 9:108", "https://quran.com/9/108"), ("Ibn Majah 1412", SUNNAH + "ibnmajah:1412")])]),
    ("g_qiblatayn", [("qiblatayn_1", "sahih", [("Coran 2:144", "https://quran.com/2/144"), ("al-Bukhari 40", SUNNAH + "bukhari:40")])]),
    ("g_haram", [("haram_1", "fait", [("Ibn Hicham, Sira ; Musnad Ahmad 15504", "https://hadithprophet.com/hadith-19547.html")])]),
    ("g_aqsa", [
        ("aqsa_1", "coran", [("Coran 17:1", "https://quran.com/17/1"), ("al-Bukhari 1189", SUNNAH + "bukhari:1189")]),
        ("aqsa_2", "fait", [("Wikipedia", "https://en.wikipedia.org/wiki/Siege_of_Jerusalem_(636%E2%80%93637)")]),
    ]),
]
HISTOIRES_TUNISIE = {    # slug de la grande mosquée -> histoires
    "zitouna": [("zitouna_1", "legende", [("Wikipédia", "https://fr.wikipedia.org/wiki/Mosqu%C3%A9e_Zitouna")]),
                ("zitouna_2", "fait", [("ويكيبيديا", "https://ar.wikipedia.org/wiki/%D8%AC%D8%A7%D9%85%D8%B9_%D8%A7%D9%84%D8%B2%D9%8A%D8%AA%D9%88%D9%86%D8%A9")])],
    "kairouan": [("kairouan_1", "legende", [("Chapoutot-Remadi, Afkar/Idées (IEMed)", "https://www.iemed.org/wp-content/uploads/2009/12/3-24-26.pdf")]),
                 ("kairouan_2", "croyance", [("Chapoutot-Remadi, Afkar/Idées (IEMed)", "https://www.iemed.org/wp-content/uploads/2009/12/3-24-26.pdf")]),
                 ("kairouan_3", "legende", [("AramcoWorld 1967", "https://archive.aramcoworld.com/issue/196701/the.fourth.holy.city.htm"), ("Wikipedia", "https://en.wikipedia.org/wiki/Great_Mosque_of_Kairouan")])],
    "sousse": [("sousse_1", "fait", [("Wikipedia", "https://en.wikipedia.org/wiki/Great_Mosque_of_Sousse")])],
    "mahdia": [("mahdia_1", "fait", [("Wikipedia", "https://en.wikipedia.org/wiki/Great_Mosque_of_Mahdia")])],
    "sfax": [("sfax_1", "fait", [("Wikipedia", "https://en.wikipedia.org/wiki/Great_Mosque_of_Sfax")])],
    "trois-portes": [("trois-portes_1", "fait", [("Wikipedia", "https://en.wikipedia.org/wiki/Mosque_of_the_Three_Doors")])],
    "youssef-dey": [("youssef-dey_1", "fait", [("Wikipedia", "https://en.wikipedia.org/wiki/Youssef_Dey_Mosque")])],
    "hammouda-pacha": [("hammouda-pacha_1", "fait", [("Wikipedia", "https://en.wikipedia.org/wiki/Hammouda_Pacha_Mosque")])],
    "sidi-mahrez": [("sidi-mahrez_1", "tradition", [("Wikipédia", "https://fr.wikipedia.org/wiki/Sidi_Mahrez")]),
                    ("sidi-mahrez_2", "fait", [("Wikipédia", "https://fr.wikipedia.org/wiki/Mosqu%C3%A9e_Sidi_Mahrez")])],
    "sidi-sahbi": [("sidi-sahbi_1", "tradition", [("Tunisie Patrimoine", "https://www.tunisiepatrimoine.tn/en/monuments/the-mausoleum-of-abu-zamaa-al-balawi/overview/"), ("Wikipedia", "https://en.wikipedia.org/wiki/Zawiya_of_Sidi_Sahib")])],
    "testour": [("testour_1", "fait", [("Wikipedia", "https://en.wikipedia.org/wiki/Great_Mosque_of_Testour")]),
                ("testour_2", "fait", [("WMC, 23/04/2026", "https://www.webmanagercenter.com/2026/04/23/565244/testour-lhorloge-inversee-chef-doeuvre-andalou-unique-au-monde-au-coeur-du-mois-du-patrimoine-2026/")])],
    "malik-ibn-anas": [("malik-ibn-anas_1", "fait", [("Mosqpedia", "https://mosqpedia.org/masajid/malik-ibn-anas-mosque/")])],
    "fadhloun": [("fadhloun_1", "fait", [("Patrimoine de Tunisie", "https://www.patrimoinedetunisie.com.tn/en/monuments/the-fadhloun-mosque/")])],
    "kasbah": [("kasbah_1", "tradition", [("Wikipedia", "https://en.wikipedia.org/wiki/Kasbah_Mosque_(Tunis)"), ("Webdo", "https://www.webdo.tn/fr/?p=215986")])],
    "monastir": [("monastir_1", "fait", [("Chapoutot-Remadi, Afkar/Idées (IEMed)", "https://www.iemed.org/wp-content/uploads/2009/12/3-24-26.pdf")])],
}

# Construire une mosquée : textes arabes d'origine (versets : édition uthmanie, api.alquran.cloud, 23/10/2026) (jamais traduits par nous : le sens est dans construire.json)
CORAN = [
    ("9:18", "إِنَّمَا يَعْمُرُ مَسَٰجِدَ ٱللَّهِ مَنْ ءَامَنَ بِٱللَّهِ وَٱلْيَوْمِ ٱلْءَاخِرِ وَأَقَامَ ٱلصَّلَوٰةَ وَءَاتَى ٱلزَّكَوٰةَ وَلَمْ يَخْشَ إِلَّا ٱللَّهَ ۖ فَعَسَىٰٓ أُو۟لَٰٓئِكَ أَن يَكُونُوا۟ مِنَ ٱلْمُهْتَدِينَ", "coran_9_18"),
    ("24:36", "فِى بُيُوتٍ أَذِنَ ٱللَّهُ أَن تُرْفَعَ وَيُذْكَرَ فِيهَا ٱسْمُهُۥ يُسَبِّحُ لَهُۥ فِيهَا بِٱلْغُدُوِّ وَٱلْءَاصَالِ", "coran_24_36"),
]
HADITHS = [
    ("h1", "مَنْ بَنَى مَسْجِدًا يَبْتَغِي بِهِ وَجْهَ اللَّهِ، بَنَى اللَّهُ لَهُ مِثْلَهُ فِي الْجَنَّةِ", SUNNAH + "bukhari:450"),
    ("h2", "مَنْ بَنَى مَسْجِدًا لِلَّهِ كَمَفْحَصِ قَطَاةٍ أَوْ أَصْغَرَ بَنَى اللَّهُ لَهُ بَيْتًا فِي الْجَنَّةِ", SUNNAH + "ibnmajah:738"),
    ("h3", "إِذَا مَاتَ الإِنْسَانُ انْقَطَعَ عَنْهُ عَمَلُهُ إِلاَّ مِنْ ثَلاَثَةٍ: إِلاَّ مِنْ صَدَقَةٍ جَارِيَةٍ، أَوْ عِلْمٍ يُنْتَفَعُ بِهِ، أَوْ وَلَدٍ صَالِحٍ يَدْعُو لَهُ", SUNNAH + "muslim:1631"),
    ("h4", "إِنَّ مِمَّا يَلْحَقُ الْمُؤْمِنَ مِنْ عَمَلِهِ وَحَسَنَاتِهِ بَعْدَ مَوْتِهِ … أَوْ مَسْجِدًا بَنَاهُ …", SUNNAH + "ibnmajah:242"),
]
# organismes : (nom, clé du pays, clé de la description, page officielle, [(magasin, adresse de l'application)]) — vus répondre le 23/10/2026
ORGANISMES = [
    ("Muslim Hands", "p_uk", "o_muslimhands", "https://muslimhands.org.uk/donate/major-giving-mosques", []),
    ("Ummah Welfare Trust", "p_uk", "o_uwt", "https://uwt.org/projects/masjid-construction/", []),
    ("Penny Appeal", "p_uk", "o_penny", "https://pennyappeal.org/appeal/the-mosque-project", []),
    ("Human Appeal", "p_uk", "o_humanappeal", "https://humanappealusa.org/appeals/mosques", []),
    ("Qatar Charity — قطر الخيرية", "p_qatar", "o_qatar", "https://www.qcharity.org/en/qa/donation/projecttype/2",
     [("App Store", "https://apps.apple.com/us/app/qtr-alkhyryt/id998227578"), ("Google Play", "https://play.google.com/store/apps/details?id=com.qcandroidfull")]),
    ("Direct Aid — العون المباشر", "p_koweit", "o_directaid", "https://direct-aid.org/donate/en/sharing/msajid/?sl=en", []),
    ("Türkiye Diyanet Vakfı (TDV)", "p_turquie", "o_tdv", "https://bagis.tdv.org/cami-mescit/camilere-yardim-7",
     [("App Store", "https://apps.apple.com/tr/app/tdv-ba%C4%9F%C4%B1%C5%9F/id1462745077"), ("Google Play", "https://play.google.com/store/apps/details?id=com.tdvmobilapp")]),
    ("Ehsan — إحسان", "p_arabie", "o_ehsan", "https://ehsan.sa/mosques",
     [("App Store", "https://apps.apple.com/us/app/ehsan-%D8%A5%D8%AD%D8%B3%D8%A7%D9%86/id1602515092"), ("Google Play", "https://play.google.com/store/apps/details?id=sa.gov.sdaia.ehsan")]),
]
SICAD = "http://www.sicad.gov.tn/Fr/Prestations_57_3_D1389"


# Descriptions écrites par nous (demande d'Ahmed du 23/10/2026 : « les mosquées de Djerba n'ont pas de description ») :
# QID Wikidata -> sources ; texte dans tools/textes/base/descriptions.json (clé = QID), montré en haut de la page de la mosquée.
UNESCO_DJERBA = ("UNESCO, dossier « Djerba » (2023)", "https://whc.unesco.org/document/192677")
INP_2022 = ("Arrêté de classement du 15/03/2022 (INP)", "https://www.inp2020.tn/documents/Arrete2022_1283Fr.pdf")
WFR = lambda t: ("Wikipédia", "https://fr.wikipedia.org/wiki/" + t)
DESCRIPTIONS = {
    "Q140590839": [WFR("Grande_mosqu%C3%A9e_des_Ban%C5%AB_Yahr%C4%81san"), UNESCO_DJERBA],
    "Q125407791": [WFR("Mosqu%C3%A9e_Tajdit"), UNESCO_DJERBA],
    "Q12204317": [WFR("Mosqu%C3%A9e_Tlakin"), UNESCO_DJERBA],
    "Q129439244": [UNESCO_DJERBA, INP_2022],
    "Q130241326": [WFR("Mosqu%C3%A9e_El_Bassi"), UNESCO_DJERBA],
    "Q140590538": [WFR("Mosqu%C3%A9e_Sidi_Yati"), UNESCO_DJERBA],
    "Q130241278": [WFR("Mosqu%C3%A9e_Ouelhi"), UNESCO_DJERBA],
    "Q140590768": [WFR("Mosqu%C3%A9e_El_Ghar"), UNESCO_DJERBA],
    "Q130241279": [UNESCO_DJERBA, INP_2022],
    "Q2497772": [UNESCO_DJERBA, ("Webdo, H. Bourial (2023)", "https://www.webdo.tn/fr/?p=203375")],
    "Q130241277": [WFR("Mosqu%C3%A9e_Bouliman"), INP_2022],
    "Q107714141": [WFR("Mosqu%C3%A9e_El_Cheikh"), ("ويكيبيديا", "https://ar.wikipedia.org/wiki/%D8%AC%D8%A7%D9%85%D8%B9_%D8%A7%D9%84%D8%B4%D9%8A%D8%AE_(%D8%AC%D8%B1%D8%A8%D8%A9)")],
    "Q550314": [WFR("Mosqu%C3%A9e_des_Turcs"), UNESCO_DJERBA],
    "Q3324933": [WFR("Mosqu%C3%A9e_des_%C3%89trangers")],
    "Q42765071": [WFR("Liste_des_monuments_class%C3%A9s_du_gouvernorat_de_M%C3%A9denine"), ("AramcoWorld 1994", "https://archive.aramcoworld.com/issue/199404/the.white.mosques.of.jerba.htm")],
    "Q130241283": [INP_2022], "Q126692587": [INP_2022], "Q126726598": [INP_2022], "Q130241282": [INP_2022],
}
DJERBA_SOURCES = [("UNESCO", "https://whc.unesco.org/fr/list/1640/"), WFR("Mosqu%C3%A9es_de_Djerba")]


def a_djerba(lat, lon):
    return 33.6 < lat < 33.95 and 10.7 < lon < 11.1


# Année de construction des 15 grandes mosquées de Tunisie (tri « la plus ancienne / la plus récente », 23/10/2026) : la date de
# fondation donnée sur leur page (siècle seul : milieu du siècle).
ANNEES_GRANDES = {"zitouna": 698, "kairouan": 670, "sousse": 851, "mahdia": 916, "sfax": 849, "trois-portes": 866, "youssef-dey": 1612,
                  "hammouda-pacha": 1655, "sidi-mahrez": 1692, "sidi-sahbi": 1629, "testour": 1630, "malik-ibn-anas": 2003,
                  "fadhloun": 1350, "kasbah": 1231, "monastir": 850}
# Grandes mosquées du monde : seulement les vraies mosquées (P31 mosquée) + ces trois lieux saints qui n'ont pas ce P31
LIEUX_SAINTS = {"Q428858", "Q486080", "Q12192963"}

# Les 15 autres pages de mosquées de Tunisie sans texte (recherche du 23/10/2026)
DESCRIPTIONS.update({
    'Q42595875': [('Wikidata Q42595875', 'https://www.wikidata.org/wiki/Q42595875'), ('Wikipédia FR, liste des monuments classés (Tunis)', 'https://fr.wikipedia.org/wiki/Liste_des_monuments_class%C3%A9s_du_gouvernorat_de_Tunis'), ('Wikimedia Commons (catégorie)', 'https://commons.wikimedia.org/wiki/Category:Ben_Moussa_Mosque')],
    'Q138799338': [('Wikidata Q138799338', 'https://www.wikidata.org/wiki/Q138799338'), ('Wikimedia Commons (catégorie)', 'https://commons.wikimedia.org/wiki/Category:Great_Mosque_of_Gabès')],
    'Q97324532': [('Wikidata Q97324532', 'https://www.wikidata.org/wiki/Q97324532'), ('Wikimedia Commons (catégorie)', 'https://commons.wikimedia.org/wiki/Category:Ferkous_Mosque')],
    'Q42762178': [('Wikidata Q42762178', 'https://www.wikidata.org/wiki/Q42762178'), ('Wikipédia FR, liste des monuments classés (Sousse)', 'https://fr.wikipedia.org/wiki/Liste_des_monuments_class%C3%A9s_du_gouvernorat_de_Sousse'), ('Areq (copie de Wikipédia AR), liste des monuments classés de Sousse', 'https://areq.net/m/قائمة_المعالم_الأثرية_المصنفة_في_ولاية_سوسة.html'), ('Wikimedia Commons (catégorie)', 'https://commons.wikimedia.org/wiki/Category:El_Rabba_Mosque')],
    'Q42605621': [('Wikidata Q42605621', 'https://www.wikidata.org/wiki/Q42605621'), ('Wikipédia FR, liste des monuments classés (Béja)', 'https://fr.wikipedia.org/wiki/Liste_des_monuments_class%C3%A9s_du_gouvernorat_de_Béja'), ('Blog « Morisques de Tunisie » : urbanisme et architecture des Morisques', 'https://moriscostunez.blogspot.com/2009/12/urbanisme-et-architecture-des-morisques.html'), ('Wikimedia Commons (catégorie)', 'https://commons.wikimedia.org/wiki/Category:Great_Mosque_of_Medjez_El_Bab')],
    'Q42601658': [('Wikidata Q42601658', 'https://www.wikidata.org/wiki/Q42601658'), ('Wikipédia FR, liste des monuments classés (Nabeul)', 'https://fr.wikipedia.org/wiki/Liste_des_monuments_class%C3%A9s_du_gouvernorat_de_Nabeul'), ('Mosaïque FM (25/05/2021)', 'https://www.mosaiquefm.net/mobile/ar/أخبار-تونس-جهات/901832/نابل-بناء-مدرسة-قرآنية-فوق-معلم-تاريخي-والبلدية-تتدخ-ل'), ('Routard, Mosquée de Nabeul', 'https://www.routard.com/fr/guide/afrique/tunisie/cap-bon/nabeul/mosquee-de-nabeul'), ('Wikimedia Commons (catégorie)', 'https://commons.wikimedia.org/wiki/Category:Great_Mosque_of_Nabeul')],
    'Q59364230': [('Wikidata Q59364230', 'https://www.wikidata.org/wiki/Q59364230'), ('Wikipédia FR, Ribat de Lamta', 'https://fr.wikipedia.org/wiki/Ribat_de_Lamta'), ('Wikipédia FR, liste des monuments classés (Monastir)', 'https://fr.wikipedia.org/wiki/Liste_des_monuments_class%C3%A9s_du_gouvernorat_de_Monastir')],
    'Q107700732': [('Wikidata Q107700732', 'https://www.wikidata.org/wiki/Q107700732'), ('Wikimedia Commons (catégorie)', 'https://commons.wikimedia.org/wiki/Category:Sidi_Mahrez_Mosque_(Djerba)')],
    'Q130241274': [('Wikidata Q130241274', 'https://www.wikidata.org/wiki/Q130241274'), ('Wikipédia FR, liste des monuments classés (Médenine)', 'https://fr.wikipedia.org/wiki/Liste_des_monuments_class%C3%A9s_du_gouvernorat_de_Médenine'), ('Wikimedia Commons (catégorie)', 'https://commons.wikimedia.org/wiki/Category:Alloula_Mosque')],
    'Q133801823': [('Wikidata Q133801823', 'https://www.wikidata.org/wiki/Q133801823'), ('Wikimedia Commons (catégorie)', 'https://commons.wikimedia.org/wiki/Category:Ouled_Saied_Mosque')],
    'Q133819470': [('Wikidata Q133819470', 'https://www.wikidata.org/wiki/Q133819470'), ('Wikimedia Commons (catégorie)', 'https://commons.wikimedia.org/wiki/Category:Sidi_Siyid_Mosque_(Tozeur)')],
    'Q134537716': [('Wikidata Q134537716', 'https://www.wikidata.org/wiki/Q134537716'), ('Wikimedia Commons (catégorie)', 'https://commons.wikimedia.org/wiki/Category:Naoura_Mosque')],
    'Q135193509': [('Wikidata Q135193509', 'https://www.wikidata.org/wiki/Q135193509'), ('Wikimedia Commons (catégorie)', 'https://commons.wikimedia.org/wiki/Category:Chorfa_Mosque')],
    'Q135485009': [('Wikidata Q135485009', 'https://www.wikidata.org/wiki/Q135485009'), ('Wikimedia Commons (catégorie)', 'https://commons.wikimedia.org/wiki/Category:Sidi_Touati_Mosque')],
    'Q42597862': [('Wikidata Q42597862', 'https://www.wikidata.org/wiki/Q42597862'), ('Wikipédia FR, liste des monuments classés (Tunis)', 'https://fr.wikipedia.org/wiki/Liste_des_monuments_class%C3%A9s_du_gouvernorat_de_Tunis'), ("Webdo (H. Bourial), l'oratoire de Lamine Bey à Carthage", 'https://www.webdo.tn/fr/actualite/chroniques/mosquees-de-tunisie-a-carthage-loratoire-meconnu-de-lamine-bey/387298/'), ('Wikimedia Commons (catégorie)', 'https://commons.wikimedia.org/wiki/Category:Douar_El_Chott_Mosque')],
})
# … et jamais ces lieux, classés « mosquée » dans Wikidata mais qui n'en sont pas aujourd'hui (vérifié le 23/10/2026) :
# mont du Temple (esplanade), dôme du Rocher (sanctuaire, pas une mosquée), cathédrale d'Ohrid (église aujourd'hui),
# Beit Al Qur'an (bibliothèque), chapelle de l'Ascension (sanctuaire)
PAS_MOSQUEES = {"Q193163", "Q172077", "Q164743", "Q630922", "Q773726"}


# Histoires des grandes mosquées du monde (pages mosquee-monde/…) : groupe de HISTOIRES_SAINTES / HISTOIRES_MONDE -> QID Wikidata
QID_GROUPES = {"g_medine": "Q486080", "g_haram": "Q428858", "g_aqsa": "Q12192963"}
HISTOIRES_MONDE = {}      # QID -> [(clé, nature, sources)] (ajoutées après les recherches du 23/10/2026)


def histoires_de(qid):
    hs = []
    for g, liste in HISTOIRES_SAINTES:
        if QID_GROUPES.get(g) == qid:
            hs += liste
    return hs + HISTOIRES_MONDE.get(qid, [])
QID_GROUPES.update({"g_quba": "Q276569", "g_qiblatayn": "Q2334553"})


# Histoires ajoutées par les recherches du 23/10/2026 (demande d'Ahmed : « le plus possible d'histoires pour chaque mosquée ») :
# tools/textes/histoires_sources.json = { clé: {groupe, qid, nature, sources} } ; textes dans tools/textes/base/histoires.json
def _charger_histoires():
    import json as _j, os as _o
    p = _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "textes", "histoires_sources.json")
    if not _o.path.exists(p):
        return
    for cle, x in _j.load(open(p, encoding="utf-8")).items():
        h = (cle, x["nature"], [tuple(s) for s in x["sources"]])
        if x["groupe"] in HISTOIRES_TUNISIE or (not x.get("qid") and x["groupe"] in ANNEES_GRANDES):
            HISTOIRES_TUNISIE.setdefault(x["groupe"], []).append(h)
        elif x.get("qid"):
            HISTOIRES_MONDE.setdefault(x["qid"], []).append(h)


_charger_histoires()
