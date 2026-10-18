// Tests de Mosquées en Tunisie (faux navigateur jsdom) — node tools/test_site.mjs [dossier]
// (accepte un dossier pour tester une copie sabotée ; jsdom : npm install --no-save --no-package-lock jsdom)
// Règle commune : des MINIMUMS (le robot peut ajouter des lieux), jamais des nombres exacts ; des éléments précis (id, texte exact).
import { readFileSync, existsSync, readdirSync, statSync } from "fs";
import { createRequire } from "module";
import { fileURLToPath } from "url";
import { dirname, join, resolve } from "path";

const require = createRequire(import.meta.url);
let JSDOM, VirtualConsole;
try { ({ JSDOM, VirtualConsole } = require("jsdom")); }
catch (e) { ({ JSDOM, VirtualConsole } = createRequire(resolve(dirname(fileURLToPath(import.meta.url)), "../../../documents Tunisie/site/package.json"))("jsdom")); }

const root = process.argv[2] ? resolve(process.argv[2]) : join(dirname(fileURLToPath(import.meta.url)), "..");
const lire = f => readFileSync(join(root, f), "utf8");
let erreurs = 0, total = 0;
const check = (d, ok) => { total++; if (ok) console.log("OK   " + d); else { erreurs++; console.log("FAIL " + d); } };
const BASE = "https://mosquees.clicvia.com/";
const GRANDES = ["zitouna", "kairouan", "sousse", "mahdia", "sfax", "trois-portes", "youssef-dey", "hammouda-pacha", "sidi-mahrez", "sidi-sahbi", "testour", "malik-ibn-anas", "fadhloun", "kasbah", "monastir"];

const PAGES = [];
(function parcourir(d) {
  for (const n of readdirSync(join(root, d))) {
    const p = d ? d + "/" + n : n;
    if (["node_modules", ".git", "tools"].includes(n)) continue;
    if (statSync(join(root, p)).isDirectory()) parcourir(p); else if (n === "index.html") PAGES.push(p);
  }
})("");

// Une adresse par langue (12/10/2026) : ar/…, en/…, tr/…, id/…, ur/…, de/…, es/… ; le français garde les adresses d'origine.
const AUTRES = ["ar", "en", "tr", "id", "ur", "de", "es", "it", "pt", "nl", "zh", "ja", "ko", "hi", "ru", "vi", "th", "tl", "sv", "ro"];
const langueDe = p => AUTRES.find(l => p.startsWith(l + "/")) || "fr";
const PAGES_FR = PAGES.filter(p => langueDe(p) === "fr");
const PAGES_LANGUE = PAGES.filter(p => langueDe(p) !== "fr");
const sansIndex = p => /<meta name="robots" content="noindex/.test(lire(p));

async function page(chemin = "index.html", { stockage = { langue: "fr", "recitation-mosquees": "non" }, lang, recherche = "", adresseFr = false } = {}) {
  const parAdresse = lang && AUTRES.includes(lang) && !chemin.startsWith("video/") && !adresseFr;
  if (parAdresse) { chemin = lang + "/" + chemin; lang = ""; }
  const dossier = dirname(chemin);
  const html = lire(chemin).replace(/<script[^>]*gc\.zgo\.at[^>]*><\/script>/, "")
    .replace(/<script( defer)? src="((?:\.\.\/)*(?:assets|donnees)\/[^"?]+)(\?[^"]*)?"><\/script>/g, (_, d, f) => `<script>${lire(join(dossier, f).replace(/\\/g, "/"))}</script>`);
  const vc = new VirtualConsole(), js = [];
  vc.on("jsdomError", e => { if (!/Not implemented/.test(e.message)) js.push(e.message); });
  const q = [lang ? "lang=" + lang : "", recherche].filter(Boolean).join("&");
  const url = BASE + (chemin === "index.html" ? "" : chemin.replace(/index\.html$/, "")) + (q ? "?" + q : "");
  const dom = new JSDOM(html, { url, runScripts: "dangerously", pretendToBeVisual: true, virtualConsole: vc,
    beforeParse(w) { for (const [k, v] of Object.entries(stockage)) w.localStorage.setItem(k, v);
      w.__allers = []; w.allerVers = u => w.__allers.push(u);
      w.__envois = []; w.IntersectionObserver = class { observe() {} disconnect() {} }; w.open = () => null; } });
  await new Promise(r => setTimeout(r, 80));
  return { w: dom.window, d: dom.window.document, js };
}

// ---- 1. toutes les pages : sécurité, installation, référencement
const grandesPages = GRANDES.map(s => `mosquee/${s}/index.html`);
const fiches = PAGES.filter(p => p.startsWith("mosquee/") && !grandesPages.includes(p));
check(`pages : accueil, À propos, liste, les ${GRANDES.length} grandes mosquées, au moins 80 autres pages de mosquées (${fiches.length})`,
  ["index.html", "a-propos/index.html", "grandes-mosquees/index.html", ...grandesPages].every(p => PAGES.includes(p)) && fiches.length >= 80);
const pb = [], versions = new Set();
for (const p of PAGES) {
  const h = lire(p);
  if (!/http-equiv="Content-Security-Policy"/.test(h) || !/noai, noimageai/.test(h) || !/translate="no"/.test(h) || !/strict-origin-when-cross-origin/.test(h)) pb.push(p + " sécurité");
  if (/<script(?![^>]*\bsrc=)(?![^>]*application\/ld\+json)[^>]*>/.test(h) || /\son[a-z]+=/i.test(h)) pb.push(p + " script en ligne");
  if (!/apple-mobile-web-app-capable/.test(h) || !/manifest\.webmanifest/.test(h)) pb.push(p + " iPhone");
  if (!/assets\/recitation\.js/.test(h) && !p.startsWith("video/")) pb.push(p + " récitation");
  [...h.matchAll(/\?v=(\w+)/g)].forEach(m => versions.add(m[1]));
}
check(`toutes les pages : CSP, noai, pas de traduction auto, iPhone, aucun script en ligne, récitation ${pb.slice(0, 6).join(" | ")}`, !pb.length);
check(`une seule version ?v= (${[...versions].join(", ")})`, versions.size === 1);
// ---- 18/10/2026 (règle VS.9, tous les sites qui affichent des images d'autres sites) : chaque image d'un autre site est autorisée
//      par la CSP (img-src) de SA page : balises <img>/<source>, fonds de carte et images citées par les scripts chargés (données
//      comprises). Sinon l'image est cassée chez tous les visiteurs (vu sur Mosquées : 144 photos de thumb.wikimedia.org bloquées).
{
  const pagesHtml = [];
  (function parcourir(d) {
    for (const n of readdirSync(join(root, d))) {
      const p = d ? d + "/" + n : n;
      if (n.startsWith(".") || ["node_modules", "tools"].includes(n) || /preuves/i.test(n)) continue;
      if (statSync(join(root, p)).isDirectory()) parcourir(p); else if (n.endsWith(".html")) pagesHtml.push(p);
    }
  })("");
  const imgSrc = h => ((/http-equiv="Content-Security-Policy" content="[^"]*?img-src([^;"]*)/.exec(h) || [])[1] || "").trim().split(/\s+/).filter(Boolean);
  const permis = (srcs, url) => {
    let u; try { u = new URL(url.replace(/\{s\}/g, "a").replace(/\{[a-z]+\}/g, "0")); } catch (e) { return false; }
    return srcs.some(s => s === "*" || s === "https:" || s === u.origin || (s.startsWith("https://*.") && u.protocol === "https:" && u.host.endsWith(s.slice(9))));
  };
  const IMG = /https:\/\/[a-z0-9.-]+\.[a-z]{2,}\/[^\s"'`<>()\\]*?\.(?:png|jpe?g|webp|gif|svg|avif)\b/gi;
  const cache = new Map(), lireJs = f => { if (!cache.has(f)) cache.set(f, existsSync(join(root, f)) ? (lire(f).match(IMG) || []).filter(u => !/\/wiki\//.test(u)) : []); return cache.get(f); };
  const bloquees = new Set(); let vues = 0;
  for (const p of pagesHtml) {
    const h = lire(p), csp = imgSrc(h), dossier = dirname(p);
    const urls = [...h.matchAll(/<(?:img|source)\b[^>]*?\s(?:src|srcset)="([^"]+)"/g)]
      .flatMap(m => m[1].split(",").map(x => x.trim().split(/\s+/)[0])).filter(u => /^https:\/\//.test(u));
    for (const m of h.matchAll(/<script\b[^>]*\ssrc="(?!https?:|\/\/)([^"?#]+)/g))
      urls.push(...lireJs(m[1].startsWith("/") ? m[1].slice(1) : join(dossier, m[1]).replace(/\\/g, "/")));
    for (const u of urls) { vues++; if (!permis(csp, u)) bloquees.add(p + " -> " + u.slice(0, 90)); }
  }
  check(`chaque image d'un autre site (balise, carte, script, données) est autorisée par la CSP img-src de sa page (${vues} vues, ${pagesHtml.length} pages) ${[...bloquees].slice(0, 3).join(" | ")}`,
    pagesHtml.length > 0 && !bloquees.size);
}
// 18/10/2026 (VS.7) : photos Wikimedia en vignette sur thumb.wikimedia.org : 960 px, ou la plus grande taille standard qui ne
// dépasse pas l'original (les autres tailles sont refusées, les fichiers originaux limités par Wikimedia : erreur 429)
{
  const TAILLES = [20, 40, 60, 120, 250, 330, 500, 960], attendue = w => Math.max(0, ...TAILLES.filter(t => t <= Math.min(w, 960)));
  const ph = JSON.parse(lire("donnees/mosquees.json")).lieux.map(l => (l.fiche || {}).photo).filter(Boolean), mal = [];
  for (const p of ph) {
    const m = /^https:\/\/thumb\.wikimedia\.org\/wikipedia\/commons\/thumb\/[0-9a-f]\/[0-9a-f]{2}\/([^/]+)\/(\d+)px-\1$/.exec(p.url);
    if (!m || +m[2] !== attendue(p.w)) mal.push(p.url.slice(0, 90) + " (" + p.w + " px)");
  }
  const urls = new Set(ph.map(p => p.url));
  const pages = PAGES.filter(p => p.startsWith("mosquee/")).flatMap(p => [...lire(p).matchAll(/<img[^>]*\ssrc="(https:\/\/[a-z]+\.wikimedia\.org\/[^"]+)"/g)].map(m => m[1].replace(/&amp;/g, "&")));
  const autres = pages.filter(u => !urls.has(u));
  check(`photos Wikimedia : vignette de 960 px (ou plus petite si l'original est plus petit), jamais le fichier original (${ph.length} photos, ${pages.length} dans les pages) ${[...mal, ...autres].slice(0, 3).join(" | ")}`,
    ph.length >= 50 && ph.every(p => p.w > 0) && !mal.length && pages.length > 0 && !autres.length);
}
check("CSP : carte (cdnjs, tuiles OpenStreetMap), photos Wikimedia, lecteur youtube-nocookie, envoi au formulaire Google", (() => { const h = lire("index.html");
  return /script-src[^;]*cdnjs\.cloudflare\.com/.test(h) && /img-src[^;]*tile\.openstreetmap\.org/.test(h) && /img-src[^;]*upload\.wikimedia\.org/.test(h)
    && /frame-src https:\/\/www\.youtube-nocookie\.com/.test(h) && /connect-src[^;]*docs\.google\.com/.test(h) && !/frame-src[^;]*\*/.test(h); })());
check("installation : manifeste (id unique), icônes, service worker, aperçu < 250 Ko", (() => { const m = JSON.parse(lire("manifest.webmanifest"));
  return m.id === "/" && ["assets/icons/icon-192.png", "assets/icons/icon-512.png", "assets/icons/icon-maskable-512.png", "assets/apple-touch-icon.png", "sw.js", "favicon.ico", "assets/og-image-v1.jpg"]
    .every(f => existsSync(join(root, f))) && statSync(join(root, "assets/og-image-v1.jpg")).size < 250 * 1024; })());
{
  const sm = lire("sitemap.xml"), dans = p => sm.includes(`<loc>${BASE}${p.replace(/index\.html$/, "")}</loc>`),
    manque = PAGES.filter(p => !p.startsWith("video/") && dans(p) === sansIndex(p));
  check(`robots.txt (IA refusées, Google accepté, sitemap) ; sitemap avec TOUTES les pages ${manque.slice(0, 3).join(" ")} ; LICENSE`, /GPTBot/.test(lire("robots.txt")) && /ClaudeBot/.test(lire("robots.txt"))
    && /User-agent: Googlebot[\s\S]*?Allow: \//.test(lire("robots.txt")) && /mosquees\.clicvia\.com\/sitemap\.xml/.test(lire("robots.txt")) && !manque.length && /Tous droits réservés/.test(lire("LICENSE")));
}
check("aucun secret ni clé dans les fichiers publiés", !/AIza|ghp_|github_pat_|sk-[A-Za-z0-9]{20}/.test(PAGES.map(lire).join("") + readdirSync(join(root, "assets")).filter(f => f.endsWith(".js")).map(f => lire("assets/" + f)).join("")));

// ---- 2. accueil : carte, recherche, filtres, autour de moi
{
  const { w, d, js } = await page();
  const L = w.MOSQUEES_LIEUX;
  check(`données : au moins 1 500 lieux de prière (${L.length}), positions en Tunisie, au moins 100 avec une page`, L.length >= 1500
    && L.every(l => l.a > 30 && l.a < 37.6 && l.o > 7.4 && l.o < 11.7) && L.filter(l => l.p).length >= 100);
  check("accueil sans erreur JS ; compteur du bandeau = nombre de lieux ; filtres Mosquée et « Avec page d'histoire », aucun à 0",
    js.length === 0 && d.getElementById("mq-total").textContent.replace(/\D/g, "") === String(L.length)
    && !!d.querySelector('#mq-filtres [data-type="m"]') && !!d.querySelector("#mq-filtres [data-pages]") && ![...d.querySelectorAll("#mq-filtres b")].some(b => b.textContent === "0"));
  const z = w.MOSQUEES_CHERCHER("zitouna") || [];
  check(`recherche « zitouna » : trouve la mosquée Zitouna avec sa page (${z.length} résultats)`, z.some(l => l.p === "mosquee/zitouna/"));
  check("recherche en arabe, ta marbouta écrite « ه » (« الزيتونه ») : trouve la Zitouna", (w.MOSQUEES_CHERCHER("الزيتونه") || []).some(l => l.p === "mosquee/zitouna/"));
  check(`recherche par ville « Kairouan » : au moins 20 lieux (${(w.MOSQUEES_CHERCHER("Kairouan") || []).length})`, (w.MOSQUEES_CHERCHER("Kairouan") || []).length >= 20);
  d.getElementById("mq-q").value = "Testour"; w.MOSQUEES_RECHERCHER();
  check("recherche « Testour » dans la page : liste de résultats, la Grande Mosquée de Testour en premier (elle a une page)",
    /lieux trouvés/.test(d.getElementById("mq-info").textContent) && /Testour/.test((d.querySelector("#mq-resultats li") || {}).textContent || ""));
  d.getElementById("mq-q").value = "zzqqxx"; w.MOSQUEES_RECHERCHER();
  check("recherche sans résultat : message « Aucun lieu trouvé » avec l'idée de signaler", /Aucun lieu trouvé/.test(d.getElementById("mq-resultats").textContent));
  d.getElementById("mq-q").value = ""; w.MOSQUEES_RECHERCHER();
  w.MOSQUEES_ICI({ a: 36.8065, o: 10.1815 });
  check("Autour de moi (Tunis) : les 8 lieux les plus proches, avec leur distance", d.querySelectorAll("#mq-resultats li").length === 8 && /\d (m|km)/.test(d.getElementById("mq-resultats").textContent));
  const zit = L.find(l => l.p === "mosquee/zitouna/"), b = w.MOSQUEES_BULLE(zit);
  check("bulle d'une grande mosquée : nom, lien vers sa page, itinéraire Google Maps, « C'est vrai » / « N'existe plus »",
    /Zitouna|Zaytuna/.test(b) && b.includes('href="mosquee/zitouna/"') && b.includes("google.com/maps/dir/") && /data-ok=/.test(b) && /data-ko=/.test(b));
  const sansNom = L.find(l => !l.n && l.v);
  check("lieu sans nom : « Mosquée — <ville> » (jamais une bulle vide)", !!sansNom && /^Mosquée — \S/.test(w.MOSQUEES_NOM(sansNom)));
  check("bulle : le texte venu des visiteurs est échappé (pas de HTML injecté)", !/<img/.test(w.MOSQUEES_BULLE({ i: "sig-x", a: 36, o: 10, t: "m", n: { fr: '<img src=x onerror=alert(1)>' }, vis: true, statut: "signale" })));
  d.querySelector("#mq-filtres [data-pages]").click();
  check("filtre « Avec page d'histoire » : un clic l'active", d.querySelector("#mq-filtres [data-pages]").getAttribute("aria-pressed") === "true");
  const cartes = [...d.querySelectorAll(".mq-grandes a.mq-grande")];
  check(`accueil : les ${GRANDES.length} grandes mosquées en cartes avec photo (fichier présent) et lien vers leur page`, cartes.length === GRANDES.length
    && cartes.every(a => { const i = a.querySelector("img"); return i && existsSync(join(root, i.getAttribute("src"))) && existsSync(join(root, a.getAttribute("href"), "index.html")); }));
  check("accueil : verset 9:18 en arabe + traduction citée (QuranEnc) ; photo du bandeau créditée (auteur + licence)",
    /يَعۡمُرُ مَسَٰجِدَ ٱللَّهِ/.test(d.querySelector(".mq-verset-ar").textContent) && !!d.querySelector('.mq-verset-source a[href="https://quranenc.com/"]')
    && /Z thomas/.test(d.querySelector(".hero figcaption").textContent) && /CC BY-SA 4\.0/.test(d.querySelector(".hero figcaption").textContent));
  const vues = [...d.querySelectorAll(".hero [data-diapo] .diapo-vue")], leg = [...d.querySelectorAll(".hero [data-diapo] .diapo-legende")];
  check(`accueil : la photo du bandeau fait défiler les ${GRANDES.length} grandes mosquées (Kairouan d'abord, fichier présent, lien vers sa page, une légende créditée par photo, une seule visible)`,
    vues.length === GRANDES.length && leg.length === vues.length && /kairouan/.test(vues[0].getAttribute("href"))
    && vues.every(a => existsSync(join(root, a.querySelector("img").getAttribute("src"))) && existsSync(join(root, a.getAttribute("href"), "index.html")))
    && leg.every(f => /CC BY|CC0|domaine public|Public domain/i.test(f.textContent) && f.querySelector('a[href^="https://commons.wikimedia.org/"]'))
    && leg.filter(f => !f.hidden).length === 1 && vues.filter(a => a.classList.contains("actif")).length === 1);
  check("lien vers The Message (découvrir l'Islam) : carte de l'accueil + pied de page", !!d.querySelector('main a[href="https://message.clicvia.com/"]')
    && !!d.querySelector('footer a[href^="https://message.clicvia.com/"]'));
  check("lien vers Points d'eau Tunisie (Le Coran et l'eau) : carte de l'accueil + pied de page", !!d.querySelector('main a[href="https://eau.clicvia.com/coran-et-eau/"]')
    && !!d.querySelector('footer a[href="https://eau.clicvia.com/"]'));
}
// ---- 3. signaler une mosquée ou une salle de prière (même Google Forms, format LIEU-PRIERE)
{
  const { w, d } = await page();
  const pop = d.getElementById("mq-sig-pop");
  check("signaler : une barre (pas de grand formulaire dans la page), fenêtre fermée au départ, formulaire DANS la fenêtre",
    !!d.querySelector("#signaler .sig-bar#mq-sig-ouvrir") && pop.hidden && !!pop.querySelector("#mq-form") && !d.querySelector("main #mq-form"));
  d.getElementById("mq-sig-ouvrir").click();
  check("barre → fenêtre ouverte : carte pour le repère, « Me localiser (GPS) », « Confirmer cette position », derniers signalés",
    !pop.hidden && !!pop.querySelector("#mq-sig-carte") && /Me localiser/.test(d.getElementById("mq-ma-pos").textContent)
    && /Confirmer cette position/.test(d.getElementById("mq-pos-ok").textContent) && /soyez le premier|Derniers lieux signalés/.test(d.getElementById("mq-derniers").textContent));   // vide ou vrais signalements (11/10/2026 : 1er signalement réel)
  d.getElementById("mq-pos-ok").click();
  check("« Confirmer » sans repère : « Placez d'abord le repère », aucune position prise", /Placez d'abord le repère/.test(d.getElementById("mq-pos-txt").textContent) && d.getElementById("mq-pos").value === "");
  d.dispatchEvent(new w.KeyboardEvent("keydown", { key: "Escape" }));
  check("Échap ferme la fenêtre ; le lien « Signaler un lieu » du menu la rouvre", pop.hidden && (() => {
    const m = [...d.querySelectorAll(".menu a")].find(x => /#signaler$/.test(x.getAttribute("href"))); m && m.click(); return !!m && !pop.hidden; })());
  const envoyer = async () => { d.getElementById("mq-form").dispatchEvent(new w.Event("submit", { bubbles: true, cancelable: true })); await new Promise(r => setTimeout(r, 20)); };
  d.getElementById("mq-type").value = "salle"; d.getElementById("mq-pos").value = ""; await envoyer();
  check("sans position confirmée : rien n'est envoyé", w.__envois.length === 0 && /Placez le repère/.test(d.getElementById("mq-statut").textContent));
  d.getElementById("mq-pos").value = "48.85000,2.35000"; await envoyer();
  check("position hors de Tunisie (Paris) : refusée, rien n'est envoyé", w.__envois.length === 0 && /pas en Tunisie/.test(d.getElementById("mq-statut").textContent));
  d.getElementById("mq-type").value = "salle"; d.getElementById("mq-nom").value = "Salle | gare de Sousse"; d.getElementById("mq-pos").value = "35.82540,10.63690"; await envoyer();
  const e = w.__envois[0] || {};
  check("signaler : format LIEU-PRIERE (propre à ce site), « type|nom » (le « | » du nom remplacé), « position|jeton lp: », remerciement",
    e["entry.1939823394"] === "LIEU-PRIERE" && /^salle\|Salle\s+gare de Sousse$/.test(e["entry.897098257"] || "") && /^35\.82540,10\.63690\|lp:[a-z0-9]+$/.test(e["entry.506707149"] || "")
    && /Merci/.test(d.getElementById("mq-statut").textContent));
  d.getElementById("mq-type").value = ""; d.getElementById("mq-pos").value = "36.80000,10.18000"; await envoyer();
  check("sans type : rien n'est envoyé, « Choisissez : mosquée ou salle de prière »", w.__envois.length === 1 && /Choisissez/.test(d.getElementById("mq-statut").textContent));
  const box = d.createElement("div"); box.innerHTML = `<div class="mq-voix"><button type="button" data-ko="osm-n1">✗</button></div>`; d.body.appendChild(box);
  box.querySelector("button").click(); await new Promise(r => setTimeout(r, 20));
  check("« n'existe plus » : format LIEU-PRIERE-KO, id du lieu", w.__envois[1] && w.__envois[1]["entry.1939823394"] === "LIEU-PRIERE-KO" && w.__envois[1]["entry.897098257"] === "osm-n1");
}
// ---- 4. récitation de cheikh Ali El Barrak (écran d'entrée, lecteur visible, souvenir du choix)
{
  const { w, d, js } = await page("index.html", { stockage: { langue: "fr" } });
  const ent = d.getElementById("entree");
  check("1re visite : écran d'entrée avec « Entrer avec la récitation de cheikh Ali El Barrak » et « Entrer sans le son », aucune erreur",
    !!ent && /Entrer avec la récitation de cheikh Ali El Barrak/.test(d.getElementById("entree-son").textContent) && /Entrer sans le son/.test(d.getElementById("entree-silence").textContent) && js.length === 0);
  d.getElementById("entree-son").click();
  const f = d.querySelector("#recitation-lecteur iframe");
  check("« Entrer avec la récitation » : écran fermé, choix « oui » gardé (clé propre au site), lecteur youtube-nocookie VISIBLE, Juz' 'Amma, lecture auto",
    !d.getElementById("entree") && w.localStorage.getItem("recitation-mosquees") === "oui" && !!f && !d.getElementById("recitation-lecteur").hidden
    && /^https:\/\/www\.youtube-nocookie\.com\/embed\/ymODAAIfowI\?autoplay=1/.test(f.getAttribute("src")) && /autoplay/.test(f.getAttribute("allow")));
  const rb = d.querySelector("header .rec-bouton");
  check("bouton rond de l'en-tête : « Arrêter la récitation » (aria-pressed true)", !!rb && rb.getAttribute("aria-pressed") === "true" && /Arrêter la récitation/.test(rb.getAttribute("aria-label")));
  rb.click();
  check("le bouton coupe la récitation : lecteur fermé, plus d'iframe, choix « non » gardé", !d.querySelector("#recitation-lecteur iframe") && w.localStorage.getItem("recitation-mosquees") === "non");
  d.querySelector('[data-video="ygnfUhIY09w"]').click();
  check("choisir Al-Fâtiha relance la récitation avec cette vidéo (choix « oui »)", /\/embed\/ygnfUhIY09w\?/.test(d.querySelector("#recitation-lecteur iframe").getAttribute("src")) && w.localStorage.getItem("recitation-mosquees") === "oui");
  check("crédit : « Récitation : cheikh Ali El Barrak (1899-1981), chaîne officielle » + lien vers la chaîne officielle", /Récitation : cheikh Ali El Barrak \(1899-1981\), chaîne officielle/.test(d.querySelector(".mq-credit-recitation").textContent)
    && !!d.querySelector('.mq-credit-recitation a[href="https://www.youtube.com/channel/UC4DO2q7J9Y71xeIKj0XqKDQ"]'));
  const { d: d2 } = await page("index.html", { stockage: { langue: "fr", "recitation-mosquees": "non" } });
  check("choix « sans le son » gardé : pas d'écran d'entrée, pas de lecteur", !d2.getElementById("entree") && !d2.querySelector("#recitation-lecteur iframe"));
  const { d: d3 } = await page("a-propos/index.html", { stockage: { langue: "fr", "recitation-mosquees": "oui" } });
  check("choix « avec la récitation » gardé : sur une autre page, le lecteur se relance seul (sans écran)", !d3.getElementById("entree") && !!d3.querySelector("#recitation-lecteur iframe"));
  const { d: d4 } = await page("index.html", { stockage: { langue: "fr" }, recherche: "son=0" });
  check("?son=0 : pas d'écran d'entrée (captures, liens partagés)", !d4.getElementById("entree"));
  const { d: d5, w: w5 } = await page("index.html", { stockage: { langue: "fr", "recitation-mosquees": "peut-etre" } });
  check("valeur inconnue dans la mémoire : traitée comme « pas de choix » (écran d'entrée)", !!d5.getElementById("entree") && w5.localStorage.getItem("recitation-mosquees") === "peut-etre");
}
// ---- 5. pages des grandes mosquées
{
  const manque = [];
  for (const s of GRANDES) {
    const { d, js } = await page(`mosquee/${s}/index.html`);
    const imgs = [...d.querySelectorAll("figure.mq-photo img")];
    if (js.length) manque.push(s + " erreur JS");
    if (!imgs.length || !imgs.every(i => existsSync(join(root, "mosquee", s, i.getAttribute("src"))))) manque.push(s + " photo");
    if (![...d.querySelectorAll("figure.mq-photo figcaption a")].every(a => /^https:\/\/commons\.wikimedia\.org\/wiki\/File:/.test(a.href))) manque.push(s + " crédit");
    if (!d.querySelector("#histoire p") || !d.querySelector("#architecture p") || d.querySelectorAll(".mq-dates li").length < 3) manque.push(s + " textes");
    if (!d.querySelector('#sources a[href^="https://www.wikidata.org/wiki/Q"]') || d.querySelectorAll("#documents li a").length < 2) manque.push(s + " sources");
    const m = d.getElementById("mq-mini");
    if (!m || !(+m.dataset.lat > 30 && +m.dataset.lat < 37.6 && +m.dataset.lon > 7.4 && +m.dataset.lon < 11.7)) manque.push(s + " carte");
    if (!/"@type": "Mosque"/.test(lire(`mosquee/${s}/index.html`))) manque.push(s + " JSON-LD");
    if (![...d.querySelectorAll("a")].some(x => x.getAttribute("href") === "https://www.google.com/maps/dir/?api=1&destination=" + m.dataset.lat + "," + m.dataset.lon)) manque.push(s + " itinéraire");
  }
  check(`les ${GRANDES.length} grandes mosquées : photo locale créditée (Commons), histoire, architecture, ≥ 3 dates, carte en Tunisie, documents, sources Wikidata, itinéraire ${manque.join(" | ")}`, !manque.length);
  const { d } = await page("mosquee/zitouna/index.html");
  check("Zitouna : reconstruite en 864, rôle d'université (Ibn Arafa), minaret de 1894", /864/.test(d.getElementById("histoire").textContent) && /Ibn Arafa/.test(d.getElementById("role").textContent) && /1894/.test(d.getElementById("dates").textContent));
  const { d: k } = await page("mosquee/kairouan/index.html");
  check("Kairouan : fondée en 670 par Okba ibn Nafi, minbar le plus ancien, lien UNESCO 499", /670/.test(k.getElementById("histoire").textContent) && /Okba ibn Nafi/.test(k.getElementById("histoire").textContent)
    && /plus ancien minbar/.test(k.getElementById("architecture").textContent) && !!k.querySelector('#documents a[href="https://whc.unesco.org/fr/list/499"]'));
}
// ---- 6. autres pages de mosquées (fiche Wikidata) : jamais vides, résumé Wikipédia cité, langue de repli annoncée
{
  const vides = [];
  for (const p of fiches) {
    const h = lire(p);
    if (!/class="mq-photo/.test(h) && !/class="mq-resume"/.test(h) && !/Fondée en/.test(h)) vides.push(p);
    if (/class="mq-resume"/.test(h) && !/creativecommons\.org\/licenses\/by-sa\/4\.0/.test(h)) vides.push(p + " licence");
  }
  check(`autres pages (${fiches.length}) : chacune a une photo, un résumé Wikipédia ou une année ; résumé cité « CC BY-SA 4.0 » ${vides.slice(0, 4).join(" | ")}`, !vides.length);
  const cible = fiches.find(p => { const h = lire(p); return /data-rl="fr"/.test(h) && !/data-rl="tr"/.test(h) && !/data-rl="en"/.test(h); });
  const { d, js } = await page(cible, { lang: "tr" });
  const choisi = d.querySelector(".mq-resume.choisi");
  check(`page sans résumé turc (${cible}) en turc : le résumé français est montré, avec la phrase qui le dit`, js.length === 0 && !!choisi && choisi.dataset.rl === "fr"
    && /Fransızca/.test(d.getElementById("mq-resume-note").textContent) && !d.getElementById("mq-resume-note").hidden);
  const cible2 = fiches.find(p => /data-nl="ar"/.test(lire(p)) && /data-nl="fr"/.test(lire(p)));
  const { d: e } = await page(cible2, { lang: "de" });
  const vus = [...e.querySelectorAll("h1 .nl")].filter(x => !x.hidden).map(x => x.dataset.nl);
  check("nom : sans nom allemand, le nom français est montré avec le nom arabe en second", (vus.includes("de") && vus.length <= 2) || (vus[0] === "fr" || vus.includes("fr")) && vus.includes("ar"));
}
// ---- 7. toutes les pages : Partager, Votre avis, menu, bouton de récitation
{
  const manque = [];
  const echantillon = AUTRES.flatMap(l => ["index.html", "a-propos/index.html", "grandes-mosquees/index.html", "mosquee/kairouan/index.html", fiches[0]].map(p => l + "/" + p));
  for (const p of [...PAGES_FR.filter(x => !x.startsWith("video/")), ...echantillon]) {
    const { d } = await page(p);
    if (d.querySelectorAll("header .partager").length !== 1) manque.push(p + " partager");
    if (!d.querySelector('footer a[href$="#avis"]')) manque.push(p + " avis");
    if (d.querySelectorAll(".menu a").length !== 6 || d.querySelectorAll('.menu a.menu-annuaire[target="_blank"][rel="noopener"] img').length !== 2) manque.push(p + " menu");
    if (d.querySelectorAll("header .rec-bouton").length !== 1) manque.push(p + " récitation");
  }
  check(`toutes les pages : Partager et bouton de récitation dans l'en-tête, « Votre avis », menu ${manque.slice(0, 5).join(" | ")}`, !manque.length);
}
// ---- 8. huit langues
{
  const manque = [];
  for (const p of PAGES_FR) {
    const h = lire(p), n = l => (h.match(new RegExp(`data-l="${l}"`, "g")) || []).length;
    if (n("fr") !== n("ar") || n("fr") !== n("en")) manque.push(`${p} (fr ${n("fr")}, ar ${n("ar")}, en ${n("en")})`);
  }
  for (const [a, b] of [["data-fr=", "data-en="], ["data-ph-fr=", "data-ph-en="], ["data-alt-ar=", "data-alt-en="]])
    for (const p of PAGES_FR) { const h = lire(p); if (h.split(a).length !== h.split(b).length) manque.push(p + " " + b); }
  check(`chaque texte français a sa traduction arabe ET anglaise, sur toutes les pages ${manque.slice(0, 4).join(" | ")}`, !manque.length);
  const NOUVELLES = ["tr", "id", "ur", "de", "es", "it", "pt", "nl", "zh", "ja", "ko", "hi", "ru", "vi", "th", "tl", "sv", "ro"];
  const TR = (() => { const w = {}; new Function("window", lire("assets/langues.js"))(w);
    // on lit les SOURCES des traductions (assets/langues.js, assets/trad/, tools/langues_plus/), pas les fichiers fabriqués
    // assets/l/<langue>.js : sinon une traduction retirée d'une source ne serait pas vue (sabotage « traduction turque manque »)
    // textes des grandes mosquées dans les 7 langues ajoutées le 13/10/2026 : tools/langues_plus/ (écrits dans les pages de langue)
    const P = JSON.parse(lire("tools/langues_plus/_francais.json")), frP = [...P.ui, ...P.contenu];
    for (const l of ["it", "pt", "nl", "zh", "ja", "ko", "hi", "ru", "vi", "th", "tl", "sv", "ro"]) (w.TRADUCTIONS[l] = w.TRADUCTIONS[l] || {}, lire(`tools/langues_plus/${l}.txt`)).split(String.fromCharCode(10)).filter(x => x.trim()).forEach(x => {
      const i = x.indexOf(String.fromCharCode(9)); w.TRADUCTIONS[l][frP[+x.slice(0, i)].replace(/\s+/g, " ").trim()] = x.slice(i + 1); });
    for (const f of readdirSync(join(root, "assets/trad"))) new Function("window", lire("assets/trad/" + f))(w); return w.TRADUCTIONS || {}; })();
  const cle = s => String(s).replace(/\s+/g, " ").trim();
  const textes = new Map(), structure = [];
  const ajouter = (fr, ou) => { fr = cle(fr || ""); if (fr && !textes.has(fr)) textes.set(fr, ou); };
  for (const p of PAGES_FR) {
    const d = new JSDOM(lire(p)).window.document;
    d.querySelectorAll('[data-l="fr"]').forEach(f => f.tagName === "UL" ? [...f.children].forEach(li => ajouter(li.innerHTML, p)) : ajouter(f.innerHTML, p));
    d.querySelectorAll('[data-l="en"]').forEach(e => { const f = e.previousElementSibling && e.previousElementSibling.previousElementSibling;
      if (!f || f.dataset.l !== "fr" || e.previousElementSibling.dataset.l !== "ar") structure.push(p + " : " + cle(e.textContent).slice(0, 30)); });
    d.querySelectorAll("[data-fr]").forEach(o => ajouter(o.dataset.fr, p));
    d.querySelectorAll("[data-ph-fr]").forEach(o => ajouter(o.dataset.phFr, p));
    d.querySelectorAll("img[data-alt-ar]").forEach(o => ajouter(o.dataset.altFr || o.alt, p));
    d.querySelectorAll("[data-vfr]").forEach(o => ajouter(o.dataset.vfr, p));
  }
  const lit = s => JSON.parse('"' + s + '"');
  for (const f of readdirSync(join(root, "assets")).filter(f => f.endsWith(".js") && f !== "langues.js")) {
    const js = lire("assets/" + f);
    for (const m of js.matchAll(/"((?:[^"\\]|\\.)*)"\s*,\s*"(?:[^"\\]|\\.)*[؀-ۿ](?:[^"\\]|\\.)*"/g)) {
      const fr = lit(m[1]); if (fr.length > 2 && /[A-Za-zÀ-ÿ]/.test(fr) && !/[؀-ۿ]/.test(fr)) ajouter(fr, f);
    }
    for (const m of js.matchAll(/\bfr:\s*"((?:[^"\\]|\\.)*)"[^}]*?\ben:\s*"/g)) ajouter(lit(m[1]), f);
  }
  const absents = [];
  for (const [fr, ou] of textes) for (const l of NOUVELLES) if (!String((TR[l] || {})[fr] || "").trim()) absents.push(`${l} « ${fr.slice(0, 50)} » (${ou})`);
  check(`(a) 8 langues : les ${textes.size} textes français (pages + scripts) ont une traduction en ${NOUVELLES.join(", ")}`
    + (absents.length ? ` — MANQUE ${absents.length} : ${absents.slice(0, 6).join(" | ")}` : ""), textes.size >= 250 && !absents.length);
  check("(a) chaque texte « en » suit ses textes « fr » et « ar » " + structure.slice(0, 3).join(" | "), !structure.length);
  const balises = []; for (const l of NOUVELLES) for (const [fr, t] of Object.entries(TR[l] || {})) if ((fr.match(/</g) || []).length !== (t.match(/</g) || []).length || (/\{n\}/.test(fr) && !/\{n\}/.test(t)) || (/\{l\}/.test(fr) && !/\{l\}/.test(t))) balises.push(l + " « " + fr.slice(0, 30) + " »");
  check("(a) traductions : mêmes balises HTML et mêmes « {n} » / « {l} » que le français " + balises.slice(0, 4).join(" | "), !balises.length);
  check("un dictionnaire d'interface par langue (assets/l/<langue>.js), chargé par les pages de cette langue seulement ; aucun pour l'arabe et l'anglais",
    NOUVELLES.every(l => existsSync(join(root, `assets/l/${l}.js`)) && lire(`${l}/index.html`).includes(`assets/l/${l}.js`) && !lire(`${l}/index.html`).includes("assets/langues.js"))
    && !/assets\/(l\/|langues\.js)/.test(lire("ar/index.html")) && !/assets\/trad\//.test(lire("tr/mosquee/kairouan/index.html")));
  {   // boutons The Message et Points d'eau dans le menu, après « Signaler un lieu », dans la langue du visiteur (13/10/2026)
    const liens = async (p, o) => [...(await page(p, o)).d.querySelectorAll(".menu a")].map(a => a.getAttribute("href"));
    const fr = await liens("index.html"), es = await liens("index.html", { lang: "es" }), tr = await liens("mosquee/kairouan/index.html", { lang: "tr" });
    check("menu : The Message et Points d'eau juste après « Signaler un lieu », avant « À propos » ; ouverts dans la langue du visiteur (anglais si le site ne l'a pas)",
      /#signaler$/.test(fr[2]) && fr[3] === "https://message.clicvia.com/?lang=fr" && fr[4] === "https://eau.clicvia.com/" && /a-propos\/$/.test(fr[5])
      && es[3] === "https://message.clicvia.com/?lang=es" && es[4] === "https://eau.clicvia.com/es/" && /^https:\/\/message\.clicvia\.com\/\?lang=/.test(tr[3]) && /^https:\/\/eau\.clicvia\.com\/tr\/$/.test(tr[4]));
  }
  check("CSS : les éléments « en » sont montrés pour tr, id, ur, de, es", NOUVELLES.every(l => lire("assets/style.css").includes(`html[lang="${l}"] [data-l="en"]`)));
  // ---- une adresse par langue : chaque page de langue est écrite dans sa langue, avec sa propre adresse officielle
  const pbL = [], droite = ["ar", "ur"];
  for (const p of PAGES_LANGUE) {
    const h = lire(p), l = langueDe(p), fr = p.slice(l.length + 1), url = BASE + p.replace(/index\.html$/, "");
    if (!PAGES_FR.includes(fr)) { pbL.push(p + " sans page française"); continue; }
    if (!new RegExp(`<html lang="${l}" dir="${droite.includes(l) ? "rtl" : "ltr"}"`).test(h)) pbL.push(p + " lang/dir");
    if (!h.includes(`<link rel="canonical" href="${url}">`) || !h.includes(`<meta property="og:url" content="${url}">`)) pbL.push(p + " adresse officielle");
    const garde = ["ar", "en"].includes(l) ? l : "en";
    if (["fr", "ar", "en"].some(x => x !== garde && h.includes(`data-l="${x}"`))) pbL.push(p + " reste d'une autre langue");
    if ([...h.matchAll(/(?:src|href)="((?:\.\.\/)*)(?:assets|donnees)\//g)].some(m => m[1] !== "../".repeat(p.split("/").length - 1))) pbL.push(p + " chemin des fichiers communs");
    if (!sansIndex(p) && !h.includes(`hreflang="${l}" href="${url}"`)) pbL.push(p + " hreflang vers elle-même");
    if (sansIndex(p) && /hreflang=/.test(h)) pbL.push(p + " noindex avec hreflang");
    if (h.match(/<title>([^<]*)<\/title>/)[1] === lire(fr).match(/<title>([^<]*)<\/title>/)[1] && l !== "en") pbL.push(p + " titre resté en français");
  }
  check(`une adresse par langue : ${PAGES_LANGUE.length} pages (${AUTRES.length} langues × ${PAGES_FR.filter(p => !p.startsWith("video/")).length}), chacune dans sa langue (lang, sens, titre, adresse officielle, fichiers communs) ${pbL.slice(0, 4).join(" | ")}`,
    PAGES_LANGUE.length === AUTRES.length * PAGES_FR.filter(p => !p.startsWith("video/")).length && !pbL.length);
  const pbH = [];
  for (const p of PAGES_FR.filter(x => !x.startsWith("video/"))) {
    const h = lire(p), dossier = p.replace(/index\.html$/, "");
    const liens = Object.fromEntries([...h.matchAll(/<link rel="alternate" hreflang="([^"]+)" href="([^"]+)">/g)].map(m => [m[1], m[2]]));
    const attendues = ["fr", ...AUTRES.filter(l => !sansIndex(l + "/" + p))];
    if (liens.fr !== BASE + dossier || !liens["x-default"] || /[?]lang=/.test(Object.values(liens).join(" "))) pbH.push(p + " français / x-default");
    if (attendues.some(l => l !== "fr" && liens[l] !== BASE + l + "/" + dossier) || Object.keys(liens).length !== attendues.length + 1) pbH.push(p + " langues");
    for (const l of attendues.slice(1)) if ([...lire(l + "/" + p).matchAll(/<link rel="alternate"[^>]*>/g)].join("") !== [...h.matchAll(/<link rel="alternate"[^>]*>/g)].join("")) pbH.push(l + "/" + p + " liens différents de la page française");
  }
  check(`hreflang : chaque page française et ses versions de langue portent les MÊMES liens (ar/, en/, tr/…), plus aucun « ?lang= » ${pbH.slice(0, 4).join(" | ")}`, !pbH.length);
  check("accueil, À propos, liste et grandes mosquées : proposés à Google dans les 8 langues ; x-default = anglais",
    ["index.html", "a-propos/index.html", "grandes-mosquees/index.html", ...grandesPages].every(p => AUTRES.every(l => !sansIndex(l + "/" + p)) && lire(p).includes(`hreflang="x-default" href="${BASE}en/${p.replace(/index\.html$/, "")}"`)));
  {
    const sans = PAGES_LANGUE.filter(sansIndex), fr0 = fiches.find(p => sansIndex("de/" + p));
    check(`autres mosquées : une version sans nom ni résumé dans la langue n'est pas proposée à Google (${sans.length} versions « noindex », hors plan du site)`,
      sans.length > 100 && sans.every(p => fiches.includes(p.slice(p.indexOf("/") + 1))) && !!fr0 && !lire(fr0).includes('hreflang="de"'));
  }
}
{
  const { w, d, js } = await page("index.html", { lang: "tr", stockage: { "recitation-mosquees": "non" } });
  check("adresse tr/ : turc, de gauche à droite, titre traduit, menu et filtres en turc ; une simple visite n'enregistre aucun choix de langue",
    d.documentElement.lang === "tr" && d.documentElement.dir === "ltr" && d.querySelector('h1 [data-l="en"]').textContent === "Tunus camileri: harita ve tarih"
    && [...d.querySelectorAll(".menu a")].some(a => a.textContent === "Harita") && /Cami/.test(d.getElementById("mq-filtres").textContent)
    && w.localStorage.getItem("langue") === null && w.localStorage.getItem("langue-mosquees") === null && w.__allers.length === 0 && js.length === 0
    && /^Tunus Camileri/.test(d.title) && d.querySelector(".menu a").getAttribute("href") === "./" && d.querySelector(".logo-mark").getAttribute("src") === "../assets/logo.svg");
  const { d: u } = await page("mosquee/kairouan/index.html", { lang: "ur" });
  check("page Kairouan en ourdou : de droite à gauche, histoire traduite (trad/g-kairouan.js)", u.documentElement.dir === "rtl" && /عقبہ بن نافع/.test(u.querySelector('#histoire p [data-l="en"]').textContent));
  const { d: a } = await page("mosquee/sousse/index.html", { lang: "ar" });
  check("page Sousse en arabe : nombres isolés (U+2066) et texte arabe", a.documentElement.dir === "rtl" && /⁦850-851⁩/.test(a.querySelector('#histoire p [data-l="ar"]').textContent));
}
{
  const { w, d, js } = await page("index.html");
  const bouton = () => d.querySelector(".langues-bouton"), liste = () => d.getElementById("langues-liste");
  check("sélecteur compact « FR ▾ » : liste des 15 langues écrites dans leur langue",
    /FR/.test(bouton().textContent) && liste().hidden && [...liste().querySelectorAll("[data-lang]")].map(b => b.textContent).join("|") === "Français|العربية|English|Türkçe|Bahasa Indonesia|اردو|Deutsch|Español|Italiano|Português|Nederlands|中文|日本語|한국어|हिन्दी|Русский|Tiếng Việt|ไทย|Filipino|Svenska|Română");
  bouton().click(); [...liste().querySelectorAll("[data-lang]")].find(b => b.textContent === "Deutsch").click();
  check("choisir Deutsch : ouvre l'adresse de/, « langue-mosquees » = de, « langue » partagée inchangée (fr) ; la page française ne change pas sur place",
    w.__allers.join() === "/de/" && d.documentElement.lang === "fr" && w.localStorage.getItem("langue-mosquees") === "de" && w.localStorage.getItem("langue") === "fr" && js.length === 0);
  const { w: wd, d: dd } = await page("index.html", { lang: "de", stockage: { "langue-mosquees": "de", "recitation-mosquees": "non" } });
  dd.querySelector(".langues-bouton").click(); dd.querySelector('#langues-liste [data-lang="fr"]').click();
  check("page allemande (de/) : texte allemand écrit dans la page, bouton « DE » ; revenir au français ouvre l'adresse française",
    dd.documentElement.lang === "de" && dd.querySelector('h1 [data-l="en"]').textContent === "Die Moscheen Tunesiens: Karte und Geschichte" && /DE/.test(dd.querySelector(".langues-bouton").textContent)
    && /Die Moscheen Tunesiens: Karte und Geschichte/.test(lire("de/index.html")) && wd.__allers.join() === "/" && wd.localStorage.getItem("langue-mosquees") === "fr");
  const { w: ws, d: s } = await page("index.html", { stockage: { "recitation-mosquees": "non" } });
  const prop = s.querySelector(".autre-langue a");
  check("sans choix enregistré, téléphone en anglais : la page reste en français (Google lit la bonne langue) et PROPOSE « English → » (adresse en/)",
    s.documentElement.lang === "fr" && ws.__allers.length === 0 && !!prop && prop.getAttribute("href") === "/en/" && /English/.test(prop.textContent));
  prop.click();
  check("toucher « English → » : choix gardé, adresse en/ ouverte", ws.__allers.join() === "/en/" && ws.localStorage.getItem("langue-mosquees") === "en");
  const { w: w2, d: s2 } = await page("index.html", { lang: "xx", stockage: { langue: "ar", "recitation-mosquees": "non" } });
  check("?lang=xx inconnu ignoré : la page française reste française", s2.documentElement.lang === "fr" && w2.__allers.length === 0);
  const { w: w3 } = await page("mosquee/kairouan/index.html", { lang: "ar", adresseFr: true, recherche: "lieu=x" });
  const { w: w4 } = await page("grandes-mosquees/index.html", { stockage: { "langue-mosquees": "tr", "recitation-mosquees": "non" } });
  const { w: w5, d: d5 } = await page("index.html", { lang: "ur", stockage: { "langue-mosquees": "ur", "recitation-mosquees": "non" } });
  check("ancien lien « ?lang=ar » → adresse ar/ de la même page (le reste de l'adresse est gardé) ; choix déjà fait (turc) → adresse tr/ ; bonne adresse : rien ne bouge, pas de proposition",
    w3.__allers.join() === "/ar/mosquee/kairouan/?lieu=x" && w4.__allers.join() === "/tr/grandes-mosquees/" && w5.__allers.length === 0 && !d5.querySelector(".autre-langue"));
  {
    const { d: c } = await page("index.html", { lang: "es" });
    const lv = c.getElementById("lien-video");
    check("adresse es/ : liens du menu et du pied dans la langue, lien vers la vidéo (?lang=es), liens des grandes mosquées dans es/",
      c.querySelector('.menu a[href="grandes-mosquees/"]') && c.querySelector('footer a[href="a-propos/"]') && !!lv && lv.querySelector("a").getAttribute("href") === "/video/?lang=es"
      && /href="mosquee\/kairouan\/"/.test(lire("es/index.html")) && /src="\.\.\/donnees\/lieux\.js/.test(lire("es/index.html")));
  }
}
// ---- page vidéo : sans son ; Al-Fâtiha (chaîne officielle) démarre et s'arrête avec la vidéo, sans écran d'entrée (09/10/2026)
{
  const { w, d } = await page("video/index.html", { stockage: { langue: "fr" } });
  const v = d.querySelector("video.video-lecteur");
  const avant = !d.getElementById("entree") && /voix de cheikh Ali El Barrak/.test((d.querySelector(".video-recitation") || {}).textContent || "");
  v.dispatchEvent(new w.Event("play"));
  const f = d.querySelector("#recitation-lecteur iframe");
  const joue = !!f && /youtube-nocookie\.com\/embed\/ygnfUhIY09w\?/.test(f.src);
  v.dispatchEvent(new w.Event("pause"));
  check("page vidéo : pas d'écran d'entrée, ligne « voix de cheikh Ali El Barrak », lecture → Al-Fâtiha officielle, pause → arrêt",
    avant && joue && !d.querySelector("#recitation-lecteur iframe"));
}
// ---- 9. mosquées du monde entier (demande d'Ahmed du 09/10/2026) : OpenStreetMap lu en direct hors de Tunisie, une couleur par pays,
//         « Chercher une ville du monde » (Nominatim). Faux serveurs : le 1er répond « vide + erreur cachée ».
{
  const { w, d, js } = await page();
  const M = w.MOSQUEES_MONDE, L = w.MOSQUEES_LIEUX, MO = w.MOSQUEES_MONDE_LIEUX;
  const total0 = d.getElementById("mq-total").textContent, filtres0 = d.getElementById("mq-filtres").textContent;
  const tunisien = L.find(l => /^osm-n\d+$/.test(l.i));
  const ZONE = [
    { type: "area", id: 3600192756, tags: { admin_level: "2", "ISO3166-1": "DZ", name: "الجزائر", "name:fr": "Algérie", "name:en": "Algeria" } },
    { type: "node", id: 101, lat: 36.7853, lon: 3.0606, tags: { amenity: "place_of_worship", religion: "muslim", name: "جامع كتشاوة", "name:fr": "Mosquée Ketchaoua" } },
    { type: "way", id: 202, center: { lat: 36.73, lon: 3.13 }, tags: { amenity: "place_of_worship", religion: "muslim", place_of_worship: "musalla" } },
    { type: "node", id: 303, lat: 36.70, lon: 3.10, tags: { amenity: "place_of_worship", religion: "christian", name: "Église" } },
    { type: "node", id: 404, lat: 36.71, lon: 3.20, tags: { amenity: "place_of_worship", religion: "muslim", name: "Mosquée près de la frontière", "addr:country": "MA" } },
    { type: "node", id: +tunisien.i.slice(5), lat: tunisien.a, lon: tunisien.o, tags: { amenity: "place_of_worship", religion: "muslim", name: "déjà connue" } }];
  const appels = [], corps = [];
  w.fetch = async (url, o) => { appels.push(String(url)); corps.push(o && o.body ? String(o.body.get("data")) : "");
    return appels.length === 1 ? { ok: true, json: async () => ({ elements: [], remark: "runtime error: Query timed out in \"query\"" }) }
      : { ok: true, json: async () => ({ elements: ZONE }) }; };
  const els = await M.lireZone(36.6, 2.9, 36.9, 3.3);
  check("monde : 1er serveur (mail.ru) « vide + erreur cachée » → réponse du 2e (overpass-api.de) ; requête = lieux de prière musulmans de la zone",
    /maps\.mail\.ru/.test(appels[0]) && /overpass-api\.de/.test(appels[1]) && els.length === ZONE.length
    && /nwr\["amenity"="place_of_worship"\]\["religion"="muslim"\]\(36\.6000,2\.9000,36\.9000,3\.3000\)/.test(corps[0]) && /out center tags 2000/.test(corps[0]));
  // pays du centre : demande séparée (is_in) ; serveur sans « zones » (erreur cachée) → serveur suivant ; tout Overpass en panne → Nominatim
  const ap = [];
  w.fetch = async (url, o) => { ap.push(String(url) + " " + (o && o.body ? String(o.body.get("data")) : ""));
    return /mail\.ru/.test(url) ? { ok: true, json: async () => ({ elements: [], remark: "runtime error: open64: 2 No such file or directory area_blocks.bin" }) }
      : { ok: true, json: async () => ({ elements: [ZONE[0]] }) }; };
  const pDZ = await w.MOSQUEES_MONDE.lirePays(36.75, 3.1), nAp = ap.length, pDZ2 = await w.MOSQUEES_MONDE.lirePays(36.76, 3.11);
  const ap2 = [];
  w.fetch = async (url) => { ap2.push(String(url)); if (!/nominatim/.test(url)) throw new Error("panne");
    return { ok: true, json: async () => ({ address: { country_code: "tr" } }) }; };
  const pTR = await w.MOSQUEES_MONDE.lirePays(41.01, 28.98);
  check(`monde : pays du centre par is_in (${pDZ}), gardé en mémoire (pas de 2e demande : ${nAp} → ${ap.length}) ; Overpass en panne → Nominatim reverse (${pTR})`,
    pDZ === "DZ" && pDZ2 === "DZ" && ap.length === nAp && /is_in\(36\.7500,3\.1000\)/.test(ap[0]) && pTR === "TR"
    && ap2.filter(u => /nominatim\.openstreetmap\.org\/reverse\?format=json&lat=41\.0100&lon=28\.9800&zoom=3/.test(u)).length === 1 && ap2.length === 6);
  const n1 = M.ajouterZone(els, ""), n2 = M.ajouterZone(els, "DZ");
  const k = MO.find(l => l.i === "osm-n101"), s = MO.find(l => l.i === "osm-w202"), f = MO.find(l => l.i === "osm-n404");
  check(`monde : 3 lieux ajoutés (${n1}), puis 0 (pas de doublon : ${n2}) ; église écartée ; mosquée tunisienne déjà connue jamais ajoutée en double`,
    n1 === 3 && n2 === 0 && !MO.some(l => l.i === "osm-n303") && !MO.some(l => l.i === tunisien.i) && L.filter(l => l.i === tunisien.i).length === 1);
  check("monde : nom dans la langue de la page (name:fr), salle de prière (musalla), pays du centre (DZ), addr:country respecté (MA)",
    !!k && w.MOSQUEES_NOM(k) === "Mosquée Ketchaoua" && k.t === "m" && k.pays === "DZ" && !!s && s.t === "s" && s.pays === "DZ" && !!f && f.pays === "MA");
  const teinte = c => +((/^hsl\((\d+)/.exec(c) || [])[1]);
  const interdite = h => (h >= 140 && h <= 225) || (h >= 18 && h <= 50);                 // vert / bleu / orange / or de la Tunisie
  const codes = ["DZ", "TR", "MA", "LY", "EG", "FR", "DE", "ID", "PK", "SA", "GB", "US", "NG", "SN", "BD", "MY", "IR", "IQ", "SY", "ES"];
  check(`monde : couleur du pays stable (${k && k.c}), Algérie ≠ Turquie (${M.couleurPays("TR")}) ≠ Maroc, jamais les couleurs de la Tunisie`,
    !!k && k.c === M.couleurPays("DZ") && k.c === M.couleurPays("DZ") && s.c === k.c && f.c === M.couleurPays("MA")
    && new Set([M.couleurPays("DZ"), M.couleurPays("TR"), M.couleurPays("MA"), M.couleurPays("LY")]).size === 4
    && codes.every(c => !interdite(teinte(M.couleurPays(c)))));
  check("monde : le compteur du haut et les filtres restent ceux de la Tunisie", d.getElementById("mq-total").textContent === total0 && d.getElementById("mq-filtres").textContent === filtres0);
  M.legende();
  const leg = d.getElementById("mq-pays");
  check("monde : légende « Couleur = pays » sous la carte : Tunisie, Algérie (2), Maroc (nom traduit), avec leurs couleurs",
    !leg.hidden && /Couleur = pays/.test(leg.textContent) && /Tunisie/.test(leg.querySelector('[data-pays="TN"]').textContent)
    && /Algérie\s*2/.test(leg.querySelector('[data-pays="DZ"]').textContent) && /Maroc/.test(leg.querySelector('[data-pays="MA"]').textContent)
    && leg.querySelector('[data-pays="DZ"] i').style.background !== leg.querySelector('[data-pays="MA"] i').style.background);
  const b = w.MOSQUEES_BULLE(k);
  check("monde : bulle simple (nom, type, pays, itinéraire, OpenStreetMap), sans page ni vote", /Mosquée Ketchaoua/.test(b) && /Algérie/.test(b)
    && b.includes("google.com/maps/dir/?api=1&destination=36.7853,3.0606") && b.includes("openstreetmap.org/node/101") && /lu en direct/.test(b) && !/data-ok=|mq-bulle-page/.test(b));
  check("monde : la recherche par nom trouve aussi les mosquées étrangères déjà chargées (« ketchaoua »)", (w.MOSQUEES_CHERCHER("ketchaoua") || []).some(l => l.i === "osm-n101"));
  check("monde : sans nom → « Salle de prière — Algérie »", w.MOSQUEES_NOM(s) === "Salle de prière — Algérie");
  // tous les serveurs : les 2 premiers en panne → le 3e
  const appels2 = [];
  w.fetch = async (url) => { appels2.push(String(url)); if (appels2.length <= 2) throw new Error("panne"); return { ok: true, json: async () => ({ elements: [ZONE[1]] }) }; };
  const els2 = await M.lireZone(41, 28.9, 41.1, 29.1);
  check("monde : les 2 premiers serveurs en panne → le 3e (kumi.systems) répond", els2.length === 1 && /overpass\.kumi\.systems/.test(appels2[2]));
  // « Chercher une ville du monde » : Nominatim seulement à la validation (Entrée ou bouton), jamais à chaque frappe
  const nomi = [];
  w.fetch = async (url) => { nomi.push(String(url)); return { ok: true, json: async () => [{ lat: "39.92", lon: "32.85", display_name: "Ankara, Türkiye" }] }; };
  const q = d.getElementById("mq-q");
  q.value = "Ankara"; q.dispatchEvent(new w.Event("input", { bubbles: true }));
  await new Promise(r => setTimeout(r, 350));
  const avant = nomi.length, bouton = d.querySelector("#mq-resultats [data-ville-monde]");
  q.dispatchEvent(new w.KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
  await new Promise(r => setTimeout(r, 30));
  check("ville du monde : rien envoyé pendant la frappe ; bouton « Chercher une ville du monde » ; Entrée → 1 requête Nominatim (format json, limit 1) ; carte centrée annoncée",
    avant === 0 && !!bouton && /Chercher une ville du monde/.test(bouton.textContent) && nomi.length === 1
    && /^https:\/\/nominatim\.openstreetmap\.org\/search\?format=json&q=Ankara&limit=1/.test(nomi[0]) && /Carte centrée sur : Ankara, Türkiye \(recherche Nominatim/.test(d.getElementById("mq-info").textContent));
  q.value = "Ankara"; q.dispatchEvent(new w.KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
  await new Promise(r => setTimeout(r, 30));
  check("ville du monde : la même ville n'est pas redemandée à Nominatim (mémoire)", nomi.length === 1);
  M.zoneTxt("Ailleurs dans le monde : zoomez sur une région, ou cherchez une ville, pour voir ses mosquées.");
  check("monde : message de zone sous la carte (#mq-zone) ; aucune erreur JS", /zoomez sur une région/.test(d.getElementById("mq-zone").textContent) && js.length === 0);
  const csp = p => (/connect-src([^;]*)/.exec(lire(p)) || [])[1] || "";
  check("CSP (accueil, À propos, une page de mosquée) : connect-src autorise les 5 serveurs OpenStreetMap et Nominatim",
    ["index.html", "a-propos/index.html", "mosquee/zitouna/index.html"].every(p => M.OVERPASS.every(u => csp(p).includes(new URL(u).origin)) && csp(p).includes("https://nominatim.openstreetmap.org")));
  const { d: apr } = await page("a-propos/index.html");
  check("À propos : « Ailleurs dans le monde » (OpenStreetMap en direct) et Nominatim dans les sources", /Ailleurs dans le monde/.test(apr.querySelector('.sources[data-l="fr"]').textContent) && /Nominatim/.test(apr.querySelector('.sources[data-l="fr"]').textContent));
}
console.log(`\n${erreurs ? erreurs + " PROBLÈME(S)" : "TOUT PASSE"} (${total} vérifications)`);
process.exit(erreurs ? 1 : 0);
