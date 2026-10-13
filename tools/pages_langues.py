# -*- coding: utf-8 -*-
"""Une VRAIE page par langue, avec sa propre adresse (visibilité Google, 12/10/2026).

Avant : une seule adresse par page, écrite en français ; les 7 autres langues n'apparaissaient qu'après coup, dans le
navigateur (bouton de langue, « ?lang=ar »). Google ne voyait donc que le français.
Maintenant : tools/construire.py fabrique la page française (adresse d'origine, inchangée), puis ce module en tire
  ar/<page>, en/<page>, tr/<page>, id/<page>, ur/<page>, de/<page>, es/<page>, it/, pt/, nl/, zh/, ja/, ko/, hi/, ru/, vi/, th/, tl/, sv/, ro/ (20 dossiers)
où tout est DÉJÀ dans la langue : <html lang>, sens d'écriture, titre, description, texte de la page (les éléments
data-l des autres langues sont retirés ; pour tr, id, ur, de, es la traduction — assets/langues.js et assets/trad/*.js,
clé = texte français — est écrite dans la page), adresse officielle (canonical) et liens hreflang entre les 8 versions.
Les liens vers les autres pages restent dans le dossier de la langue ; les fichiers communs (assets/, donnees/…)
sont pris à la racine du site. Aucune dépendance : seulement la bibliothèque standard de Python."""
import html, json, os, posixpath, re
from html.parser import HTMLParser

LANGUES = ["fr", "ar", "en", "tr", "id", "ur", "de", "es", "it", "pt", "nl", "zh", "ja", "ko", "hi", "ru", "vi", "th", "tl", "sv", "ro"]
NOUVELLES = ["tr", "id", "ur", "de", "es", "it", "pt", "nl", "zh", "ja", "ko", "hi", "ru", "vi", "th", "tl", "sv", "ro"]
DROITE = ("ar", "ur")
COMMUNS = ("assets/", "donnees/", "manifest.webmanifest", "sw.js", "favicon.ico")      # fichiers pris à la racine du site
SITE = {"fr": "Mosquées en Tunisie", "ar": "مساجد تونس", "en": "Mosques in Tunisia", "tr": "Tunus Camileri", "id": "Masjid di Tunisia",
        "ur": "تیونس کی مساجد", "de": "Moscheen in Tunesien", "es": "Mezquitas de Túnez",
        "it": "Moschee in Tunisia", "pt": "Mesquitas na Tunísia", "nl": "Moskeeën in Tunesië", "zh": "突尼斯的清真寺", "ja": "チュニジアのモスク",
        "ko": "튀니지의 모스크", "hi": "ट्यूनीशिया की मस्जिदें",
        "ru": "Мечети Туниса", "vi": "Thánh đường ở Tunisia", "th": "มัสยิดในตูนิเซีย", "tl": "Mga moske sa Tunisia",
        "sv": "Moskéer i Tunisien", "ro": "Moschei în Tunisia"}
# accueil : titre, description, titre de partage (le français reste celui de index.html, écrit à la main)
ACCUEIL = {
    "ar": ("مساجد تونس: خريطة كل المساجد، صور وتاريخ (مجاني)",
           "خريطة مجانية لكل المساجد والمصلّيات في تونس: ابحث بالاسم أو بالمدينة واعثر على الأقرب إليك. تاريخ وصور ووثائق الجوامع الكبرى: الزيتونة، القيروان، سوسة، المهدية، صفاقس، تستور. وأيضًا مساجد العالم كله: ابحث عن مدينة.",
           "مساجد تونس والعالم: الخريطة والصور والتاريخ"),
    "en": ("Mosques in Tunisia: map of every mosque, photos and history (free)",
           "Free map of every mosque and prayer room in Tunisia: search by name or town, find the nearest one. History, photos and documents of the great mosques: Zitouna, Kairouan, Sousse, Mahdia, Sfax, Testour. Also mosques all over the world: search for a city.",
           "Mosques of Tunisia and the world: map, photos and history"),
    "tr": ("Tunus Camileri: tüm camilerin haritası, fotoğraflar ve tarih (ücretsiz)",
           "Tunus'taki tüm camilerin ve mescitlerin ücretsiz haritası: ada veya şehre göre arayın, en yakın camiyi bulun. Büyük camilerin tarihi, fotoğrafları ve belgeleri: Zeytune, Kayrevan, Susa, Mehdiye, Sefâkus, Testur. Ayrıca tüm dünyadaki camiler: bir şehir arayın.",
           "Tunus ve dünya camileri: harita, fotoğraflar ve tarih"),
    "id": ("Masjid di Tunisia: peta semua masjid, foto, dan sejarah (gratis)",
           "Peta gratis semua masjid dan musala di Tunisia: cari berdasarkan nama atau kota, temukan yang terdekat. Sejarah, foto, dan dokumen masjid-masjid besar: Zaitunah, Kairouan, Sousse, Mahdia, Sfax, Testour. Juga masjid di seluruh dunia: cari sebuah kota.",
           "Masjid Tunisia dan dunia: peta, foto, dan sejarah"),
    "ur": ("تیونس کی مساجد: تمام مساجد کا نقشہ، تصاویر اور تاریخ (مفت)",
           "تیونس کی تمام مساجد اور نماز گاہوں کا مفت نقشہ: نام یا شہر سے تلاش کریں اور قریب ترین مسجد معلوم کریں۔ بڑی مساجد کی تاریخ، تصاویر اور دستاویزات: زیتونہ، قیروان، سوسہ، مہدیہ، صفاقس، تستور۔ دنیا بھر کی مساجد بھی: کوئی شہر تلاش کریں۔",
           "تیونس اور دنیا کی مساجد: نقشہ، تصاویر اور تاریخ"),
    "de": ("Moscheen in Tunesien: Karte aller Moscheen, Fotos und Geschichte (kostenlos)",
           "Kostenlose Karte aller Moscheen und Gebetsräume in Tunesien: nach Name oder Stadt suchen, die nächste Moschee finden. Geschichte, Fotos und Dokumente der großen Moscheen: Zitouna, Kairouan, Sousse, Mahdia, Sfax, Testour. Auch Moscheen in aller Welt: einfach eine Stadt suchen.",
           "Moscheen in Tunesien und weltweit: Karte, Fotos und Geschichte"),
    "es": ("Mezquitas de Túnez: mapa de todas las mezquitas, fotos e historia (gratis)",
           "Mapa gratuito de todas las mezquitas y salas de oración de Túnez: busque por nombre o ciudad y encuentre la más cercana. Historia, fotos y documentos de las grandes mezquitas: Zitouna, Cairuán, Susa, Mahdía, Sfax, Testour. También las mezquitas de todo el mundo: busque una ciudad.",
           "Mezquitas de Túnez y del mundo: mapa, fotos e historia"),
}
SUITE_GRANDE = {"fr": " : histoire, architecture, photos", "ar": ": التاريخ والعمارة والصور", "en": ": history, architecture, photos",
                "tr": ": tarih, mimari, fotoğraflar", "id": ": sejarah, arsitektur, foto", "ur": ": تاریخ، فنِ تعمیر، تصاویر",
                "de": ": Geschichte, Architektur, Fotos", "es": ": historia, arquitectura, fotos",
                "it": ": storia, architettura, foto", "pt": ": história, arquitetura, fotos", "nl": ": geschiedenis, architectuur, foto's",
                "zh": "：历史、建筑、照片", "ja": "：歴史・建築・写真", "ko": ": 역사, 건축, 사진", "hi": ": इतिहास, वास्तुकला, तस्वीरें",
                "ru": ": история, архитектура, фотографии", "vi": ": lịch sử, kiến trúc, hình ảnh", "th": ": ประวัติ สถาปัตยกรรม ภาพถ่าย",
                "tl": ": kasaysayan, arkitektura, mga larawan", "sv": ": historia, arkitektur, foton", "ro": ": istorie, arhitectură, fotografii"}
FICHE_DESC = {"ar": "{nom}: مسجد في تونس{ville}. صورة وتاريخ وخريطة وروابط.", "en": "{nom}: mosque in Tunisia{ville}. Photo, history, map and links.",
              "tr": "{nom}: Tunus'ta bir cami{ville}. Fotoğraf, tarih, harita ve bağlantılar.", "id": "{nom}: masjid di Tunisia{ville}. Foto, sejarah, peta, dan tautan.",
              "ur": "{nom}: تیونس کی ایک مسجد{ville}۔ تصویر، تاریخ، نقشہ اور روابط۔", "de": "{nom}: Moschee in Tunesien{ville}. Foto, Geschichte, Karte und Links.",
              "es": "{nom}: mezquita de Túnez{ville}. Foto, historia, mapa y enlaces.",
              "it": "{nom}: moschea della Tunisia{ville}. Foto, storia, mappa e link.", "pt": "{nom}: mesquita da Tunísia{ville}. Foto, história, mapa e ligações.",
              "nl": "{nom}: moskee in Tunesië{ville}. Foto, geschiedenis, kaart en links.", "zh": "{nom}：突尼斯的清真寺{ville}。照片、历史、地图和链接。",
              "ja": "{nom}：チュニジアのモスク{ville}。写真・歴史・地図・リンク。", "ko": "{nom}: 튀니지의 모스크{ville}. 사진, 역사, 지도, 링크.",
              "hi": "{nom}: ट्यूनीशिया की एक मस्जिद{ville}। तस्वीर, इतिहास, नक़्शा और लिंक।",
              "ru": "{nom}: мечеть в Тунисе{ville}. Фото, история, карта и ссылки.", "vi": "{nom}: thánh đường ở Tunisia{ville}. Ảnh, lịch sử, bản đồ và đường dẫn.",
              "th": "{nom}: มัสยิดในตูนิเซีย{ville} ภาพถ่าย ประวัติ แผนที่ และลิงก์", "tl": "{nom}: moske sa Tunisia{ville}. Larawan, kasaysayan, mapa at mga link.",
              "sv": "{nom}: moské i Tunisien{ville}. Foto, historia, karta och länkar.", "ro": "{nom}: moschee din Tunisia{ville}. Fotografie, istorie, hartă și legături."}
VIDES = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
ISOLES = re.compile("[⁦-⁩‎‏]")


def adresse(base, chemin, l):
    """Adresse d'une page (chemin = dossier depuis la racine, « » pour l'accueil) dans la langue l."""
    return base + ("" if l == "fr" else l + "/") + chemin


def liens_hreflang(base, chemin, langues):
    """Les mêmes lignes sur les 8 versions d'une page ; x-default = anglais (visiteurs d'une autre langue), sinon français."""
    defaut = "en" if "en" in langues else "fr"
    return ("".join(f'<link rel="alternate" hreflang="{l}" href="{adresse(base, chemin, l)}">\n' for l in LANGUES if l in langues)
            + f'<link rel="alternate" hreflang="x-default" href="{adresse(base, chemin, defaut)}">\n')


# ---------- petit arbre HTML (bibliothèque standard), qui réécrit la page à l'identique sauf ce qu'on change ----------
class Noeud:
    def __init__(self, balise=None, attrs=None, brut="", parent=None):
        self.balise, self.attrs, self.brut, self.parent, self.enfants, self.ferme = balise, list(attrs or []), brut, parent, [], False

    def get(self, nom):
        for k, v in self.attrs:
            if k == nom:
                return v if v is not None else ""
        return None

    def poser(self, nom, valeur):
        if self.get(nom) is None:
            self.attrs.append((nom, valeur))
        else:
            self.attrs = [(k, (valeur if k == nom else v)) for k, v in self.attrs]
        self.brut = "<" + self.balise + "".join(f" {k}" if v is None else f' {k}="{html.escape(v, quote=True)}"' for k, v in self.attrs) + ">"

    def ecrire(self):
        if self.balise is None:
            return self.brut
        return self.brut + "".join(e.ecrire() for e in self.enfants) + (f"</{self.balise}>" if self.ferme else "")

    def dedans(self):
        return "".join(e.ecrire() for e in self.enfants)

    def elements(self):
        return [e for e in self.enfants if e.balise]

    def tous(self):
        for e in self.enfants:
            if e.balise:
                yield e
                yield from e.tous()

    def texte(self):
        if self.balise is None:
            return "" if self.brut.startswith("<!") else html.unescape(self.brut)
        return "".join(e.texte() for e in self.enfants)

    def navigateur(self):
        """Contenu tel que le navigateur le rend (innerHTML) : c'est la clé des traductions de assets/langues.js."""
        out = []
        for e in self.enfants:
            if e.balise is None:
                out.append(e.brut if e.brut.startswith("<!") else html.escape(html.unescape(e.brut), quote=False).replace(" ", "&nbsp;"))
            else:
                out.append("<" + e.balise + "".join(f' {k}="{html.escape(v or "", quote=True).replace(chr(160), "&nbsp;").replace("&#x27;", chr(39))}"' for k, v in e.attrs) + ">")
                if e.balise not in VIDES:
                    out.append(e.navigateur() + f"</{e.balise}>")
        return "".join(out)


class Lecteur(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.racine = Noeud("#racine"); self.ici = self.racine

    def _feuille(self, brut):
        self.ici.enfants.append(Noeud(None, brut=brut, parent=self.ici))

    def handle_starttag(self, tag, attrs):
        n = Noeud(tag, attrs, self.get_starttag_text(), self.ici)
        self.ici.enfants.append(n)
        if tag not in VIDES:
            self.ici = n

    def handle_startendtag(self, tag, attrs):
        self.ici.enfants.append(Noeud(tag, attrs, self.get_starttag_text(), self.ici))

    def handle_endtag(self, tag):
        n = self.ici
        while n is not self.racine and n.balise != tag:
            n = n.parent
        if n is self.racine:
            return                                   # balise fermante sans ouvrante : ignorée
        n.ferme = True
        self.ici = n.parent

    def handle_data(self, data): self._feuille(data)
    def handle_entityref(self, name): self._feuille(f"&{name};")
    def handle_charref(self, name): self._feuille(f"&#{name};")
    def handle_comment(self, data): self._feuille(f"<!--{data}-->")
    def handle_decl(self, decl): self._feuille(f"<!{decl}>")


def lire_arbre(texte):
    p = Lecteur(); p.feed(texte); p.close()
    racine = p.racine; racine.brut = ""; racine.balise = "#racine"
    return racine


def cle(s):
    return re.sub(r"\s+", " ", s).strip()


def lire_traductions(chemin_js):
    """assets/langues.js : { langue: { texte français: traduction } } (une ligne « "clé": "valeur", » par texte)."""
    d, l = {}, None
    ligne = re.compile(r'^\s*("(?:[^"\\]|\\.)*")\s*:\s*("(?:[^"\\]|\\.)*")\s*,?\s*$')
    for t in open(chemin_js, encoding="utf-8").read().splitlines():
        m = re.match(r"\s*window\.TRADUCTIONS\.(\w+)\s*=", t)
        if m:
            l = m.group(1); d.setdefault(l, {}); continue
        m = ligne.match(t)
        if m and l:
            d[l][json.loads(m.group(1))] = json.loads(m.group(2))
    return d


def filtrer_langue(racine, l, trad):
    """Ne garde que les éléments data-l de la langue (pour tr, id, ur, de, es : l'élément « en », rempli avec la traduction du
    texte français voisin — même règle que traduirePage() de assets/page.js). Renvoie le nombre de textes restés en anglais."""
    garde = l if l in ("fr", "ar", "en") else "en"
    manque = 0
    for parent in [racine] + list(racine.tous()):
        if not any(e.balise and e.get("data-l") is not None for e in parent.enfants):
            continue
        els = parent.elements()
        if l in NOUVELLES:
            for i, en in enumerate(els):
                if en.get("data-l") != "en":
                    continue
                fr = els[i - 2] if i >= 2 else None
                if fr is None or fr.get("data-l") != "fr":
                    continue
                if en.balise == "ul":
                    for li_fr, li_en in zip(fr.elements(), en.elements()):
                        t = trad.get(cle(li_fr.navigateur()))
                        if t:
                            li_en.enfants = [Noeud(None, brut=t, parent=li_en)]
                        else:
                            manque += 1
                else:
                    t = trad.get(cle(fr.navigateur()))
                    if t:
                        en.enfants = [Noeud(None, brut=t, parent=en)]
                    else:
                        manque += 1
        parent.enfants = [e for e in parent.enfants if not (e.balise and e.get("data-l") is not None and e.get("data-l") != garde)]
    return manque


def premier(racine, test):
    for e in racine.tous():
        if test(e):
            return e
    return None


def texte_propre(n, maxi=None):
    t = cle(ISOLES.sub("", n.texte())) if n is not None else ""
    return t[:maxi] if maxi else t


def variante(page_fr, base, chemin, l, langues, trad, meta=None, indexer=True):
    """Page « chemin » (dossier depuis la racine) dans la langue l, tirée de la page française. Renvoie (html, textes sans traduction)."""
    prof = chemin.count("/")                       # « mosquee/kairouan/ » → 2 ; la version de langue est un dossier plus bas
    racine = lire_arbre(page_fr)
    manque = filtrer_langue(racine, l, trad)
    h = premier(racine, lambda e: e.balise == "html")
    h.poser("lang", l); h.poser("dir", "rtl" if l in DROITE else "ltr")
    h.poser("data-racine", "../" * (prof + 1)); h.poser("data-racine-pages", "../" * prof)
    # liens : les fichiers communs à la racine du site, la page vidéo (une seule, avec ?lang=) ; le reste reste dans la langue
    for e in racine.tous():
        for nom in ("href", "src", "poster"):
            u = e.get(nom)
            if not u or re.match(r"^([a-zA-Z][a-zA-Z0-9+.-]*:|//|#|\?)", u) or (e.balise == "link" and e.get("rel") in ("canonical", "alternate")):
                continue
            m = re.match(r"^([^?#]*)(.*)$", u)
            cible = posixpath.normpath(posixpath.join(chemin, m.group(1))) + ("/" if m.group(1).endswith("/") else "")
            cible = "" if cible in (".", "./") else cible
            if cible.startswith(COMMUNS):
                e.poser(nom, "../" * (prof + 1) + cible + m.group(2))
            elif cible.startswith("video/"):
                e.poser(nom, "../" * (prof + 1) + cible + "?lang=" + l + re.sub(r"^\?[^#]*", "", m.group(2)))
    # dictionnaires : une page de langue ne charge que le sien (assets/l/<langue>.js) ; l'arabe et l'anglais sont écrits dans la
    # page (aucun dictionnaire) ; les traductions de la page elle-même (assets/trad/…) sont déjà écrites dans le texte.
    for parent in [racine] + list(racine.tous()):
        garder = []
        for i, e in enumerate(parent.enfants):
            src = (e.get("src") or "") if e.balise == "script" else ""
            if "assets/trad/" in src or ("assets/langues.js" in src and l not in NOUVELLES):
                if garder and garder[-1].balise is None and not garder[-1].brut.strip():
                    garder.pop()                    # le saut de ligne qui précédait la balise retirée
                continue
            if "assets/langues.js" in src:
                e.poser("src", src.replace("assets/langues.js", f"assets/l/{l}.js"))
            garder.append(e)
        parent.enfants = garder
    # titre, description, aperçu de partage
    tete = premier(racine, lambda e: e.balise == "head")
    h1 = premier(racine, lambda e: e.balise == "h1")
    intro = premier(racine, lambda e: e.balise == "p" and "intro" in (e.get("class") or "").split())
    titre, desc, og = (tuple(meta or ()) + (None, None, None))[:3]
    titre = titre or (texte_propre(h1) + " | " + SITE[l])
    desc = cle(desc or texte_propre(intro) or titre)[:200]
    og = og or titre
    for e in tete.tous():
        if e.balise == "title":
            e.enfants = [Noeud(None, brut=html.escape(titre, quote=False), parent=e)]
        elif e.balise == "meta" and e.get("name") == "description":
            e.poser("content", desc)
        elif e.balise == "meta" and e.get("property") == "og:title":
            e.poser("content", og)
        elif e.balise == "meta" and e.get("property") == "og:description":
            e.poser("content", desc)
        elif e.balise == "meta" and e.get("property") == "og:url":
            e.poser("content", adresse(base, chemin, l))
        elif e.balise == "link" and e.get("rel") == "canonical":
            e.poser("href", adresse(base, chemin, l))
        elif e.balise == "meta" and e.get("name") == "robots" and not indexer:
            e.poser("content", "noindex, " + (e.get("content") or "").replace("noindex, ", ""))
    sortie = racine.ecrire()
    # mêmes liens hreflang que la page française (déjà au bon format) : rien à changer ; version sans contenu propre : pas de lien
    if not indexer:
        sortie = re.sub(r'<link rel="alternate" hreflang="[^"]*" href="[^"]*">\n', "", sortie)
    return sortie, manque
