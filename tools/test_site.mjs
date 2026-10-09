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
const BASE = "https://ah6259.github.io/mosquees-tunisie/";
const GRANDES = ["zitouna", "kairouan", "sousse", "mahdia", "sfax", "trois-portes", "youssef-dey", "hammouda-pacha", "sidi-mahrez", "sidi-sahbi", "testour", "malik-ibn-anas", "fadhloun", "kasbah", "monastir"];

const PAGES = [];
(function parcourir(d) {
  for (const n of readdirSync(join(root, d))) {
    const p = d ? d + "/" + n : n;
    if (["node_modules", ".git", "tools"].includes(n)) continue;
    if (statSync(join(root, p)).isDirectory()) parcourir(p); else if (n === "index.html") PAGES.push(p);
  }
})("");

async function page(chemin = "index.html", { stockage = { langue: "fr", "recitation-mosquees": "non" }, lang, recherche = "" } = {}) {
  const dossier = dirname(chemin);
  const html = lire(chemin).replace(/<script[^>]*gc\.zgo\.at[^>]*><\/script>/, "")
    .replace(/<script( defer)? src="((?:\.\.\/)*(?:assets|donnees)\/[^"?]+)(\?[^"]*)?"><\/script>/g, (_, d, f) => `<script>${lire(join(dossier, f).replace(/\\/g, "/"))}</script>`);
  const vc = new VirtualConsole(), js = [];
  vc.on("jsdomError", e => { if (!/Not implemented/.test(e.message)) js.push(e.message); });
  const q = [lang ? "lang=" + lang : "", recherche].filter(Boolean).join("&");
  const url = BASE + (chemin === "index.html" ? "" : chemin.replace(/index\.html$/, "")) + (q ? "?" + q : "");
  const dom = new JSDOM(html, { url, runScripts: "dangerously", pretendToBeVisual: true, virtualConsole: vc,
    beforeParse(w) { for (const [k, v] of Object.entries(stockage)) w.localStorage.setItem(k, v);
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
check("CSP : carte (cdnjs, tuiles OpenStreetMap), photos Wikimedia, lecteur youtube-nocookie, envoi au formulaire Google", (() => { const h = lire("index.html");
  return /script-src[^;]*cdnjs\.cloudflare\.com/.test(h) && /img-src[^;]*tile\.openstreetmap\.org/.test(h) && /img-src[^;]*upload\.wikimedia\.org/.test(h)
    && /frame-src https:\/\/www\.youtube-nocookie\.com/.test(h) && /connect-src[^;]*docs\.google\.com/.test(h) && !/frame-src[^;]*\*/.test(h); })());
check("installation : manifeste (id unique), icônes, service worker, aperçu < 250 Ko", (() => { const m = JSON.parse(lire("manifest.webmanifest"));
  return m.id === "/mosquees-tunisie/" && ["assets/icons/icon-192.png", "assets/icons/icon-512.png", "assets/icons/icon-maskable-512.png", "assets/apple-touch-icon.png", "sw.js", "favicon.ico", "assets/og-image-v1.jpg"]
    .every(f => existsSync(join(root, f))) && statSync(join(root, "assets/og-image-v1.jpg")).size < 250 * 1024; })());
{
  const sm = lire("sitemap.xml"), manque = PAGES.filter(p => !p.startsWith("video/") && !sm.includes(`<loc>${BASE}${p.replace(/index\.html$/, "")}</loc>`));
  check(`robots.txt (IA refusées, Google accepté, sitemap) ; sitemap avec TOUTES les pages ${manque.slice(0, 3).join(" ")} ; LICENSE`, /GPTBot/.test(lire("robots.txt")) && /ClaudeBot/.test(lire("robots.txt"))
    && /User-agent: Googlebot[\s\S]*?Allow: \//.test(lire("robots.txt")) && /mosquees-tunisie\/sitemap\.xml/.test(lire("robots.txt")) && !manque.length && /Tous droits réservés/.test(lire("LICENSE")));
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
  check("lien vers Points d'eau Tunisie (Le Coran et l'eau) : carte de l'accueil + pied de page", !!d.querySelector('main a[href="https://ah6259.github.io/points-eau-tunisie/coran-et-eau/"]')
    && !!d.querySelector('footer a[href="https://ah6259.github.io/points-eau-tunisie/"]'));
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
    && /Confirmer cette position/.test(d.getElementById("mq-pos-ok").textContent) && /soyez le premier/.test(d.getElementById("mq-derniers").textContent));
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
    if (!d.querySelector('a[href="https://www.google.com/maps/dir/?api=1&destination=' + m.dataset.lat + "," + m.dataset.lon + '"]')) manque.push(s + " itinéraire");
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
  for (const p of PAGES.filter(x => !x.startsWith("video/"))) {
    const { d } = await page(p);
    if (d.querySelectorAll("header .partager").length !== 1) manque.push(p + " partager");
    if (!d.querySelector('footer a[href$="#avis"]')) manque.push(p + " avis");
    if (d.querySelectorAll(".menu a").length !== 4) manque.push(p + " menu");
    if (d.querySelectorAll("header .rec-bouton").length !== 1) manque.push(p + " récitation");
  }
  check(`toutes les pages : Partager et bouton de récitation dans l'en-tête, « Votre avis », menu ${manque.slice(0, 5).join(" | ")}`, !manque.length);
}
// ---- 8. huit langues
{
  const manque = [];
  for (const p of PAGES) {
    const h = lire(p), n = l => (h.match(new RegExp(`data-l="${l}"`, "g")) || []).length;
    if (n("fr") !== n("ar") || n("fr") !== n("en")) manque.push(`${p} (fr ${n("fr")}, ar ${n("ar")}, en ${n("en")})`);
  }
  for (const [a, b] of [["data-fr=", "data-en="], ["data-ph-fr=", "data-ph-en="], ["data-alt-ar=", "data-alt-en="]])
    for (const p of PAGES) { const h = lire(p); if (h.split(a).length !== h.split(b).length) manque.push(p + " " + b); }
  check(`chaque texte français a sa traduction arabe ET anglaise, sur toutes les pages ${manque.slice(0, 4).join(" | ")}`, !manque.length);
  const NOUVELLES = ["tr", "id", "ur", "de", "es"];
  const TR = (() => { const w = {}; new Function("window", lire("assets/langues.js"))(w);
    for (const f of readdirSync(join(root, "assets/trad"))) new Function("window", lire("assets/trad/" + f))(w); return w.TRADUCTIONS || {}; })();
  const cle = s => String(s).replace(/\s+/g, " ").trim();
  const textes = new Map(), structure = [];
  const ajouter = (fr, ou) => { fr = cle(fr || ""); if (fr && !textes.has(fr)) textes.set(fr, ou); };
  for (const p of PAGES) {
    const d = new JSDOM(lire(p)).window.document;
    d.querySelectorAll('[data-l="fr"]').forEach(f => f.tagName === "UL" ? [...f.children].forEach(li => ajouter(li.innerHTML, p)) : ajouter(f.innerHTML, p));
    d.querySelectorAll('[data-l="en"]').forEach(e => { const f = e.previousElementSibling && e.previousElementSibling.previousElementSibling;
      if (!f || f.dataset.l !== "fr" || e.previousElementSibling.dataset.l !== "ar") structure.push(p + " : " + cle(e.textContent).slice(0, 30)); });
    d.querySelectorAll("[data-fr]").forEach(o => ajouter(o.dataset.fr, p));
    d.querySelectorAll("[data-ph-fr]").forEach(o => ajouter(o.dataset.phFr, p));
    d.querySelectorAll("img[data-alt-ar]").forEach(o => ajouter(o.dataset.altFr || o.alt, p));
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
  check("CSS : les éléments « en » sont montrés pour tr, id, ur, de, es", NOUVELLES.every(l => lire("assets/style.css").includes(`html[lang="${l}"] [data-l="en"]`)));
  check("hreflang des 8 langues sur toutes les pages (sauf video/)", PAGES.filter(p => !p.startsWith("video/")).every(p => ["fr", "ar", "en", ...NOUVELLES, "x-default"].every(l => lire(p).includes(`hreflang="${l}"`))));
}
{
  const { w, d, js } = await page("index.html", { lang: "tr", stockage: { "recitation-mosquees": "non" } });
  check("?lang=tr : turc, de gauche à droite, titre traduit, menu et filtres en turc, mémoire partagée « langue » non touchée",
    d.documentElement.lang === "tr" && d.documentElement.dir === "ltr" && d.querySelector('h1 [data-l="en"]').textContent === "Tunus camileri: harita ve tarih"
    && [...d.querySelectorAll(".menu a")].some(a => a.textContent === "Harita") && /Cami/.test(d.getElementById("mq-filtres").textContent)
    && w.localStorage.getItem("langue") === null && w.localStorage.getItem("langue-mosquees") === "tr" && js.length === 0);
  const { d: u } = await page("mosquee/kairouan/index.html", { lang: "ur" });
  check("page Kairouan en ourdou : de droite à gauche, histoire traduite (trad/g-kairouan.js)", u.documentElement.dir === "rtl" && /عقبہ بن نافع/.test(u.querySelector('#histoire p [data-l="en"]').textContent));
  const { d: a } = await page("mosquee/sousse/index.html", { lang: "ar" });
  check("page Sousse en arabe : nombres isolés (U+2066) et texte arabe", a.documentElement.dir === "rtl" && /⁦850-851⁩/.test(a.querySelector('#histoire p [data-l="ar"]').textContent));
}
{
  const { w, d, js } = await page("index.html");
  const bouton = () => d.querySelector(".langues-bouton"), liste = () => d.getElementById("langues-liste");
  check("sélecteur compact « FR ▾ » : liste des 8 langues écrites dans leur langue",
    /FR/.test(bouton().textContent) && liste().hidden && [...liste().querySelectorAll("[data-lang]")].map(b => b.textContent).join("|") === "Français|العربية|English|Türkçe|Bahasa Indonesia|اردو|Deutsch|Español");
  bouton().click(); [...liste().querySelectorAll("[data-lang]")].find(b => b.textContent === "Deutsch").click();
  check("choisir Deutsch : page en allemand, « langue-mosquees » = de, « langue » partagée inchangée (fr)", d.documentElement.lang === "de"
    && w.localStorage.getItem("langue-mosquees") === "de" && w.localStorage.getItem("langue") === "fr" && d.querySelector('h1 [data-l="en"]').textContent === "Die Moscheen Tunesiens: Karte und Geschichte" && js.length === 0);
  bouton().click(); liste().querySelector('[data-lang="fr"]').click();
  const restes = [...d.querySelectorAll('[data-l="en"]')].filter(e => e.dataset.enOrigine !== undefined && e.innerHTML !== e.dataset.enOrigine).length;
  check("retour en français : plus aucun texte allemand", d.documentElement.lang === "fr" && restes === 0 && !/Karte|Moschee/.test(d.querySelector(".menu").textContent));
  const { d: s } = await page("index.html", { stockage: { "recitation-mosquees": "non" } });
  check("sans choix enregistré, téléphone en anglais → anglais", s.documentElement.lang === "en");
  const { d: s2 } = await page("index.html", { lang: "xx", stockage: { langue: "ar", "recitation-mosquees": "non" } });
  check("?lang=xx inconnu ignoré ; choix « arabe » fait sur un autre de nos sites → arabe", s2.documentElement.lang === "ar" && s2.documentElement.dir === "rtl");
}
console.log(`\n${erreurs ? erreurs + " PROBLÈME(S)" : "TOUT PASSE"} (${total} vérifications)`);
process.exit(erreurs ? 1 : 0);
