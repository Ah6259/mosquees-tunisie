/* Accueil de « Mosquées en Tunisie » : carte de tous les lieux de prière (Leaflet + fond OpenStreetMap, rendu « canvas » pour
   2 000 points et plus), recherche par nom ou par ville, filtres, « Autour de moi », et signalement d'un lieu manquant.
   Données : donnees/lieux.js (window.MOSQUEES, fabriqué par tools/construire.py depuis OpenStreetMap + Wikidata, tous les 3 mois)
   et donnees/signales.js (window.MOSQUEES_SIGNALES, lieux signalés par les visiteurs, publiés toutes les 2 h par tools/lieux_priere.py).
   Signaler / « c'est vrai » / « n'existe plus » : même Google Forms que les prix du site Prix des Eaux, format propre
   LIEU-PRIERE / LIEU-PRIERE-OK / LIEU-PRIERE-KO, avec un jeton anonyme du navigateur (le robot des prix ignore ces lignes).
   Hors de Tunisie (09/10/2026) : mosquées du monde lues en direct dans OpenStreetMap (Overpass), une couleur par pays ;
   « Chercher une ville du monde » par Nominatim. Les pages d'histoire restent pour la Tunisie. */
(function () {
  const FORM = "https://docs.google.com/forms/d/e/1FAIpQLSd7sR4KmzqrCi-Yjw0WV9SmT_3sZfKJtPmkGnDjMRHl4Q78PA/formResponse";
  const CH = { marque: "entry.897098257", format: "entry.1939823394", lieu: "entry.506707149", date: "entry.1622032670" };
  const TYPES = {
    m: { fr: "Mosquée", ar: "مسجد", en: "Mosque", c: "#0E6B4C" },
    s: { fr: "Salle de prière", ar: "مصلّى", en: "Prayer room", c: "#2F6FB3" }
  };
  const L2 = (fr, ar, en) => (window.T ? window.T(fr, ar, en) : fr);
  const $ = id => document.getElementById(id);
  const lire = k => { try { return localStorage.getItem(k); } catch (e) { return null; } };
  const ecrire = (k, v) => { try { localStorage.setItem(k, v); } catch (e) {} };
  const esc = s => String(s || "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  let jeton = lire("lieu-priere-jeton");
  if (!/^lp:[a-z0-9]{6,40}$/.test(jeton || "")) { jeton = "lp:" + Math.random().toString(36).slice(2) + Date.now().toString(36); ecrire("lieu-priere-jeton", jeton); }

  // ---- données : lieux OpenStreetMap / Wikidata + lieux signalés par les visiteurs (votes, retraits)
  const D = window.MOSQUEES || { lieux: [] };
  const SIG = window.MOSQUEES_SIGNALES || { points: [], votes: {}, retires: [] };
  const retires = new Set(SIG.retires || []);
  const LIEUX = D.lieux.filter(l => !retires.has(l.i)).map(l => ({ ...l, ok: ((SIG.votes || {})[l.i] || [0])[0] }));
  (SIG.points || []).forEach(p => {
    if (!/^-?\d/.test(String(p.lat)) || !TYPES[p.type === "salle" ? "s" : "m"]) return;
    LIEUX.push({ i: p.id, a: p.lat, o: p.lon, t: p.type === "salle" ? "s" : "m", n: p.nom ? { [/[؀-ۿ]/.test(p.nom) ? "ar" : "fr"]: p.nom } : null,
      vis: true, statut: p.statut, ok: p.ok || 0, date: p.date });
  });
  window.MOSQUEES_LIEUX = LIEUX;            // pour les tests
  const MONDE = [], PAYS = {};              // mosquées hors de Tunisie lues en direct ; étiquettes des pays (OpenStreetMap)
  window.MOSQUEES_MONDE_LIEUX = MONDE;

  // ---- nom affiché : le nom dans la langue choisie s'il existe, sinon arabe + français (demande d'Ahmed)
  function noms(l) {
    const lg = document.documentElement.lang, n = l.n || {};
    if (l.monde) return { p: n[lg] || l.nom || "", s: "" };        // ailleurs dans le monde : name:<langue>, sinon name
    let p = n[lg];
    if (!p) p = lg === "ar" || lg === "ur" ? (n.ar || n.fr || n.en) : (n.fr || n.en || n.ar);
    const second = p && n.ar && p !== n.ar && lg !== "ar" ? n.ar : (p && lg === "ar" && n.fr && p !== n.fr ? n.fr : "");
    return { p: p || "", s: second || "" };
  }
  const nomT = t => L2(TYPES[t].fr, TYPES[t].ar, TYPES[t].en);
  function ville(l) {
    if (!l.v) return "";
    const ar = ["ar", "ur"].includes(document.documentElement.lang);
    const v = ar ? (l.v[1] || l.v[0]) : (l.v[0] || l.v[1]), r = ar ? (l.v[3] || l.v[2]) : (l.v[2] || l.v[3]);
    return v + (r && r !== v ? " (" + r + ")" : "");
  }
  function titre(l) {
    const n = noms(l);
    if (!n.p && l.monde) return nomT(l.t) + " — " + nomPays(l.pays);
    return n.p || (nomT(l.t) + (ville(l) ? " — " + ville(l) : ""));
  }
  window.MOSQUEES_NOM = titre;

  // ---- recherche : sans accents, sans voyelles arabes, alif / ya / ta marbouta unifiés
  function normaliser(s) {
    return String(s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase()
      .replace(/[ً-ْٰـ]/g, "").replace(/[إأآٱ]/g, "ا").replace(/ى/g, "ي").replace(/ة/g, "ه").replace(/ؤ/g, "و").replace(/ئ/g, "ي")
      .replace(/[-'’.,()]/g, " ").replace(/\s+/g, " ").trim();
  }
  LIEUX.forEach(l => { l._q = normaliser(Object.values(l.n || {}).join(" ") + " " + (l.v || []).join(" ")); });
  function chercher(q) {
    const mots = normaliser(q).split(" ").filter(Boolean);
    if (!mots.length) return null;
    return LIEUX.concat(MONDE).filter(l => mots.every(m => l._q.includes(m)));     // Tunisie + mosquées du monde déjà chargées
  }
  window.MOSQUEES_CHERCHER = chercher;

  function distance(a, b) {
    const R = 6371, r = x => x * Math.PI / 180, dLa = r(b.a - a.a), dLo = r(b.o - a.o);
    const h = Math.sin(dLa / 2) ** 2 + Math.cos(r(a.a)) * Math.cos(r(b.a)) * Math.sin(dLo / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(h));
  }
  const km = d => d < 1 ? Math.round(d * 1000) + " m" : d.toFixed(d < 10 ? 1 : 0).replace(".", ",") + " km";
  const itineraire = l => `https://www.google.com/maps/dir/?api=1&destination=${l.a},${l.o}`;

  // ---- filtres (jamais un filtre à 0, règle commune)
  const actifs = new Set(["m", "s"]);
  let seulementPages = false, requete = "", ici = null, carte = null, calque = null;
  const marqueurs = {};
  function visibles() {
    const trouves = requete ? chercher(requete) || [] : LIEUX.concat(MONDE);
    return trouves.filter(l => actifs.has(l.t) && (!seulementPages || l.p));
  }
  function filtres() {
    const n = t => LIEUX.filter(l => l.t === t).length, np = LIEUX.filter(l => l.p).length;
    $("mq-filtres").innerHTML = Object.entries(TYPES).filter(([k]) => n(k) > 0).map(([k, t]) =>
      `<button type="button" class="chipbtn" data-type="${k}" aria-pressed="${actifs.has(k)}"><i style="background:${t.c}"></i>${nomT(k)} <b>${n(k)}</b></button>`).join("")
      + (np ? `<button type="button" class="chipbtn" data-pages aria-pressed="${seulementPages}"><i class="or"></i>${L2("Avec page d'histoire", "لها صفحة تاريخ", "With a history page")} <b>${np}</b></button>` : "");
    const n0 = LIEUX.length.toLocaleString("fr-FR").replace(/ | /g, " ");
    $("mq-total").textContent = typeof iso === "function" ? iso(n0) : n0;      // nombre isolé dans un texte arabe
  }

  const STATUT = { confirme: ["Confirmé par les visiteurs", "أكّده الزوار", "Confirmed by visitors"], signale: ["Signalé par un visiteur, à confirmer", "أضافه زائر، في انتظار التأكيد", "Reported by a visitor, to be confirmed"] };
  function bulle(l) {
    const n = noms(l), racine = document.documentElement.dataset.racine || "";
    const osm = /^osm-[nwr]\d+$/.test(l.i) ? `https://www.openstreetmap.org/${{ n: "node", w: "way", r: "relation" }[l.i[4]]}/${l.i.slice(5)}` : "";
    if (l.monde) return `<div class="mq-bulle"><b>${esc(titre(l))}</b><br><span>${nomT(l.t)} · ${esc(nomPays(l.pays))}</span>
      <br><a href="${itineraire(l)}" target="_blank" rel="noopener">${L2("Itinéraire (Google Maps)", "الطريق (خرائط Google)", "Directions (Google Maps)")}</a>${osm ? ` · <a href="${osm}" target="_blank" rel="noopener">OpenStreetMap</a>` : ""}
      <br><small>${L2("Source : OpenStreetMap, lu en direct", "المصدر: OpenStreetMap، مقروء مباشرة", "Source: OpenStreetMap, read live")}</small></div>`;
    return `<div class="mq-bulle"><b>${esc(titre(l))}</b>${n.s ? `<br><span lang="ar">${esc(n.s)}</span>` : ""}<br>
      <span>${nomT(l.t)}${ville(l) && n.p ? " · " + esc(ville(l)) : ""}${l.r === "i" ? " · " + L2("ibadite", "إباضي", "Ibadi") : ""}</span>
      ${l.vis ? `<br><small>${L2(...(STATUT[l.statut] || STATUT.signale))}</small>` : ""}
      ${l.p ? `<br><a class="mq-bulle-page" href="${racine}${esc(l.p)}">${L2("Histoire, photos et documents", "التاريخ والصور والوثائق", "History, photos and documents")} →</a>` : ""}
      <br><a href="${itineraire(l)}" target="_blank" rel="noopener">${L2("Itinéraire (Google Maps)", "الطريق (خرائط Google)", "Directions (Google Maps)")}</a>${osm ? ` · <a href="${osm}" target="_blank" rel="noopener">OpenStreetMap</a>` : ""}
      <div class="mq-voix"><button type="button" data-ok="${esc(l.i)}">✓ ${L2("C'est vrai", "صحيح", "It's true")}</button><button type="button" data-ko="${esc(l.i)}">✗ ${L2("N'existe plus", "لم يعد موجودًا", "No longer exists")}</button></div></div>`;
  }
  window.MOSQUEES_BULLE = bulle;

  function dessiner(ajuster) {
    if (!carte) return;
    calque.clearLayers();
    const v = visibles();
    v.forEach(l => {
      if (l.monde) {                        // ailleurs dans le monde : la couleur du pays
        marqueurs[l.i] = L.circleMarker([l.a, l.o], { radius: l.t === "s" ? 4 : 5, color: "#fff", weight: 1.2, fillColor: l.c, fillOpacity: .92 })
          .bindPopup(() => bulle(l)).addTo(calque);
        return;
      }
      marqueurs[l.i] = L.circleMarker([l.a, l.o], { radius: l.p ? 7 : (l.vis ? 6 : 5), color: l.p ? "#F2B33D" : "#fff", weight: l.p ? 3 : 1.5,
        fillColor: l.vis ? "#D9822B" : TYPES[l.t].c, fillOpacity: l.statut === "signale" ? .6 : .92 }).bindPopup(() => bulle(l)).addTo(calque);
    });
    if (ajuster && v.length && v.length < LIEUX.length) {
      const b = L.latLngBounds(v.map(l => [l.a, l.o]));
      carte.fitBounds(b.pad(0.15), { maxZoom: 15 });
    }
  }

  function liste(titreListe, l, avecDistance) {
    const box = $("mq-resultats");
    if (!l) { box.innerHTML = ""; return; }
    if (!l.length) { box.innerHTML = `<p class="mq-vide">${L2("Aucun lieu trouvé. Essayez un autre nom ou une ville proche, ou signalez le lieu s'il manque.", "لم يُعثر على أي مكان. جرّب اسمًا آخر أو مدينة قريبة، أو أضف المكان إن كان غير موجود.", "No place found. Try another name or a nearby town, or report the place if it is missing.")}</p>`; return; }
    box.innerHTML = `<h3>${titreListe}</h3><ol>` + l.slice(0, 20).map(x => {
      const n = noms(x);
      return `<li>${avecDistance && ici ? `<b>${km(distance(ici, x))}</b> · ` : ""}<button type="button" class="mq-lien" data-voir="${esc(x.i)}">${esc(titre(x))}</button>`
        + `${n.s ? ` <span lang="ar" class="mq-ar">${esc(n.s)}</span>` : ""}${ville(x) && n.p ? ` <small>${esc(ville(x))}</small>` : ""}`
        + `${x.p ? ` <i class="mq-pastille-or" title="page"></i>` : ""}</li>`;
    }).join("") + "</ol>";
  }

  // valide = recherche validée (touche Entrée) : si rien n'est trouvé, la ville est cherchée dans le monde (Nominatim, 1 requête)
  function rechercher(valide) {
    requete = $("mq-q").value.trim();
    const v = visibles();
    if (!requete) { $("mq-info").textContent = ""; liste("", null); dessiner(); return; }
    const tri = v.slice().sort((a, b) => (b.p ? 1 : 0) - (a.p ? 1 : 0) || (ici ? distance(ici, a) - distance(ici, b) : titre(a).localeCompare(titre(b))));
    $("mq-info").textContent = L2("{n} lieux trouvés", "{n} مكانًا", "{n} places found").replace("{n}", v.length);
    liste(L2("Résultats", "النتائج", "Results"), tri, !!ici);
    $("mq-resultats").insertAdjacentHTML("beforeend", `<p class="mq-monde-q"><button type="button" class="chipbtn" data-ville-monde>${L2("Chercher une ville du monde", "ابحث عن مدينة في العالم", "Search for a town anywhere in the world")} : « ${esc(requete)} »</button></p>`);
    chargerLeaflet(() => dessiner(true));
    if (valide === true && !v.length) chercherVille(requete);
  }
  window.MOSQUEES_RECHERCHER = rechercher;

  function proches() {
    if (!ici) return;
    const l = visibles().map(x => ({ x, d: distance(ici, x) })).sort((a, b) => a.d - b.d).slice(0, 8).map(y => y.x);
    liste(L2("Les plus proches de vous", "الأقرب إليك", "Nearest to you"), l, true);
  }

  function demarrerCarte() {
    if (carte || !window.L) return;
    carte = L.map("mq-carte", { scrollWheelZoom: false, preferCanvas: true }).setView([34.1, 9.6], 6);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">contributeurs OpenStreetMap</a>' }).addTo(carte);
    calque = L.layerGroup().addTo(carte);
    const message = L.control({ position: "topright" });     // le message de zone, posé aussi SUR la carte (comme Points d'eau)
    message.onAdd = () => { bulleZone = L.DomUtil.create("div", "mq-zone-carte"); bulleZone.hidden = true; L.DomEvent.disableClickPropagation(bulleZone); return bulleZone; };
    message.addTo(carte);
    let attenteMonde = null;
    carte.on("moveend", () => { clearTimeout(attenteMonde); attenteMonde = setTimeout(chargerMonde, 600); });
    dessiner(!!requete);
    voirDemande();
  }

  // ---- Le monde entier (demande d'Ahmed du 09/10/2026 : « si le visiteur cherche une mosquée dans un autre pays, il doit la trouver »).
  // Méthode de Points d'eau : la Tunisie est déjà chargée (robot trimestriel + visiteurs) ; ailleurs, les lieux de prière musulmans
  // d'OpenStreetMap de la zone affichée sont lus EN DIRECT (zoom ≥ 9) auprès des 5 copies d'OpenStreetMap (règle commune) :
  // les 2 premières en même temps (la plus rapide gagne), puis les autres une par une ; 25 s au plus chacune.
  // Couleur par pays : la même requête demande le pays du centre de la zone (is_in) ; un lieu qui porte addr:country garde son pays.
  const OVERPASS = ["https://maps.mail.ru/osm/tools/overpass/api/interpreter", "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter", "https://overpass.private.coffee/api/interpreter",
    "https://overpass.openstreetmap.fr/api/interpreter"];
  const NOMINATIM = "https://nominatim.openstreetmap.org/search";
  const TUNISIE = { s: 30.1, n: 37.6, o: 7.4, e: 11.7 };
  const ZOOM_MONDE = 9, zonesLues = [];
  const codePays = t => { const c = String((t || {})["ISO3166-1"] || (t || {})["ISO3166-1:alpha2"] || "").toUpperCase(); return /^[A-Z]{2}$/.test(c) ? c : ""; };
  // couleur stable calculée depuis le code ISO ; jamais les teintes de la Tunisie (vert, bleu, orange, or)
  // voisins de la Tunisie et pays proches : teintes choisies pour que deux pays voisins ne se ressemblent pas ; les autres : hachage
  const VOISINS = { DZ: [0, 45], LY: [86, 33], MA: [280, 45], EG: [330, 45], ML: [300, 38], NE: [128, 30], TR: [300, 40], SY: [58, 35],
    IQ: [260, 50], IR: [12, 45], SA: [100, 33], JO: [344, 45], FR: [246, 55], ES: [344, 45], IT: [100, 33], DE: [58, 35], BE: [0, 45], PT: [86, 33] };
  const TEINTES = [0, 12, 58, 72, 86, 100, 114, 128, 246, 260, 274, 288, 302, 316, 330, 344];
  function couleurPays(c) {
    if (!c) return "hsl(0, 0%, 45%)";
    if (VOISINS[c]) return `hsl(${VOISINS[c][0]}, 68%, ${VOISINS[c][1]}%)`;
    let h = 7; for (const ch of c) h = (h * 31 + ch.charCodeAt(0)) % 10007;
    return `hsl(${TEINTES[h % TEINTES.length]}, 68%, ${[40, 52][Math.floor(h / TEINTES.length) % 2]}%)`;
  }
  function nomPays(c) {
    if (!c) return L2("Pays non précisé", "بلد غير محدّد", "Country not specified");
    const lg = document.documentElement.lang, t = PAYS[c] || {};
    let intl = "";
    try { intl = new Intl.DisplayNames([lg], { type: "region" }).of(c); } catch (x) { /* navigateur ancien */ }
    return t["name:" + lg] || (intl && intl !== c ? intl : "") || t["name:en"] || t.name || c;
  }
  function versLieu(el, centre) {
    const tags = el.tags || {};
    const lat = el.lat !== undefined ? el.lat : (el.center || {}).lat, lon = el.lon !== undefined ? el.lon : (el.center || {}).lon;
    if (lat === undefined || lon === undefined || tags.amenity !== "place_of_worship" || tags.religion !== "muslim") return null;
    const pays = /^[A-Z]{2}$/.test(String(tags["addr:country"] || "").toUpperCase()) ? tags["addr:country"].toUpperCase() : centre;
    if (pays === "TN") return null;                      // la Tunisie vient de nos données (lieux retirés compris)
    const n = {};
    ["fr", "ar", "en", "tr", "id", "ur", "de", "es"].forEach(l => { if (tags["name:" + l]) n[l] = String(tags["name:" + l]).slice(0, 80); });
    const l = { i: "osm-" + el.type[0] + el.id, a: +(+lat).toFixed(6), o: +(+lon).toFixed(6),
      t: ["musalla", "prayer_room", "prayer_hall"].includes(tags.place_of_worship) ? "s" : "m",
      n, nom: String(tags.name || "").slice(0, 80), pays, c: couleurPays(pays), monde: true };
    l._q = normaliser(Object.values(n).join(" ") + " " + l.nom);
    return l;
  }
  function ajouterZone(elements) {
    let centre = "";
    elements.filter(e => e.type === "area").forEach(a => { const c = codePays(a.tags); if (c) { PAYS[c] = a.tags; centre = centre || c; } });
    const connus = new Set(LIEUX.map(l => l.i).concat(MONDE.map(l => l.i)));
    let n = 0;
    elements.forEach(el => { if (el.type === "area") return; const l = versLieu(el, centre); if (l && !connus.has(l.i)) { MONDE.push(l); connus.add(l.i); n++; } });
    return n;
  }
  async function essai(url, q) {
    const arret = window.AbortController ? new AbortController() : null, minuterie = arret && setTimeout(() => arret.abort(), 25000);
    try {
      const r = await fetch(url, { method: "POST", body: new URLSearchParams({ data: q }), signal: arret && arret.signal });
      if (!r.ok) throw new Error("HTTP " + r.status);
      const d = await r.json();
      if (/error|timed out/i.test(String(d.remark || ""))) throw new Error(d.remark);   // erreur cachée : serveur suivant
      return d.elements || [];
    } finally { clearTimeout(minuterie); }
  }
  async function lireZone(s, o, n, e) {
    const bb = [s, o, n, e].map(x => x.toFixed(4)).join(",");
    const q = `[out:json][timeout:25];is_in(${((s + n) / 2).toFixed(4)},${((o + e) / 2).toFixed(4)})->.p;area.p["admin_level"="2"];out tags;`
      + `nwr["amenity"="place_of_worship"]["religion"="muslim"](${bb});out center tags 2000;`;
    try { return await Promise.any(OVERPASS.slice(0, 2).map(u => essai(u, q))); } catch (x) { /* les deux ont échoué */ }
    for (const url of OVERPASS.slice(2)) { try { return await essai(url, q); } catch (x) { /* serveur suivant */ } }
    throw new Error("OpenStreetMap injoignable");
  }
  const isoN = x => (typeof iso === "function" ? iso(x) : String(x));     // nombre isolé dans un texte arabe
  let bulleZone = null;
  const zoneTxt = (t, err) => {
    const z = $("mq-zone"); if (z) { z.textContent = t; z.className = "aide mq-zone" + (err ? " err" : ""); }
    if (bulleZone) { bulleZone.textContent = t; bulleZone.hidden = !t; bulleZone.classList.toggle("err", !!err); }
  };
  // légende « couleur = pays » : la Tunisie puis les pays déjà chargés
  function legende() {
    const box = $("mq-pays");
    if (!box) return;
    if (!MONDE.length) { box.innerHTML = ""; box.hidden = true; return; }
    const compte = {};
    MONDE.forEach(l => { compte[l.pays] = (compte[l.pays] || 0) + 1; });
    box.hidden = false;
    box.innerHTML = `<span class="mq-pays-titre">${L2("Couleur = pays :", "اللون = البلد:", "Colour = country:")}</span> `
      + `<span class="mq-pays-chip" data-pays="TN"><i style="background:${TYPES.m.c}"></i>${esc(nomPays("TN"))}</span>`
      + Object.keys(compte).sort((a, b) => compte[b] - compte[a]).map(c =>
        `<span class="mq-pays-chip" data-pays="${esc(c)}"><i style="background:${couleurPays(c)}"></i>${esc(nomPays(c))} <b>${isoN(compte[c])}</b></span>`).join("");
  }
  async function chargerMonde() {
    if (!carte) return;
    const b = carte.getBounds();
    const dedans = b.getSouth() >= TUNISIE.s && b.getNorth() <= TUNISIE.n && b.getWest() >= TUNISIE.o && b.getEast() <= TUNISIE.e
      && LIEUX.some(l => b.contains([l.a, l.o]));                    // Tunisie : déjà chargée
    if (dedans) { zoneTxt(""); return; }
    if (carte.getZoom() < ZOOM_MONDE) { zoneTxt(L2("Ailleurs dans le monde : zoomez sur une région, ou cherchez une ville, pour voir ses mosquées.", "في باقي العالم: قرّب الخريطة على منطقة، أو ابحث عن مدينة، لرؤية مساجدها.", "Elsewhere in the world: zoom in on a region, or search for a town, to see its mosques.")); return; }
    if (zonesLues.some(z => z.contains(b))) return;
    const zone = b.pad(0.25);
    zoneTxt(L2("Recherche des mosquées de cette zone…", "جارٍ البحث عن مساجد هذه المنطقة…", "Looking for the mosques in this area…"));
    try {
      const n = ajouterZone(await lireZone(zone.getSouth(), zone.getWest(), zone.getNorth(), zone.getEast()));
      zonesLues.push(zone); dessiner(); legende(); if (ici && !requete) proches();
      const total = LIEUX.concat(MONDE).filter(l => zone.contains([l.a, l.o])).length;
      zoneTxt(total ? L2("{n} lieux de prière dans cette zone.", "{n} مكان صلاة في هذه المنطقة.", "{n} places of prayer in this area.").replace("{n}", isoN(total))
        : L2("Aucun lieu de prière connu ici dans OpenStreetMap.", "لا يوجد مكان صلاة معروف هنا في OpenStreetMap.", "No known place of prayer here in OpenStreetMap."));
      return n;
    } catch (x) {
      zoneTxt(L2("OpenStreetMap ne répond pas pour le moment : réessayez dans un instant.", "OpenStreetMap لا يستجيب الآن: أعد المحاولة بعد قليل.", "OpenStreetMap is not responding right now: try again in a moment."), true);
    }
  }
  // « Chercher une ville du monde » : Nominatim (OpenStreetMap), UNE requête par recherche validée, jamais à chaque frappe
  const villesVues = {};
  let villeEnCours = false;
  async function chercherVille(q) {
    q = String(q || "").trim().slice(0, 60);
    if (!q || villeEnCours) return;
    const info = $("mq-info");
    villeEnCours = true;
    info.textContent = L2("Recherche de la ville dans le monde…", "جارٍ البحث عن المدينة في العالم…", "Looking for the town in the world…");
    try {
      let r = villesVues[q.toLowerCase()];
      if (!r) {
        const rep = await fetch(NOMINATIM + "?" + new URLSearchParams({ format: "json", q, limit: "1", "accept-language": document.documentElement.lang }), { headers: { Accept: "application/json" } });
        if (!rep.ok) throw new Error("HTTP " + rep.status);
        r = villesVues[q.toLowerCase()] = ((await rep.json()) || [])[0] || { vide: true };
      }
      if (r.vide || !isFinite(+r.lat) || !isFinite(+r.lon)) { info.textContent = L2("Aucune ville trouvée dans le monde pour ce nom.", "لم يُعثر على مدينة بهذا الاسم في العالم.", "No town with this name was found in the world."); return; }
      requete = ""; $("mq-q").value = ""; liste("", null);
      info.textContent = L2("Carte centrée sur : {l} (recherche Nominatim, © contributeurs OpenStreetMap).", "الخريطة متمركزة على: {l} (بحث Nominatim، © مساهمو OpenStreetMap).", "Map centred on: {l} (Nominatim search, © OpenStreetMap contributors).")
        .replace("{l}", String(r.display_name || q).slice(0, 120));
      chargerLeaflet(() => { dessiner(); carte.setView([+r.lat, +r.lon], 12); $("mq-carte").scrollIntoView && $("mq-carte").scrollIntoView({ behavior: "smooth", block: "center" }); });
    } catch (x) {
      info.textContent = L2("La recherche de ville ne répond pas pour le moment : réessayez dans un instant.", "البحث عن المدن لا يستجيب الآن: أعد المحاولة بعد قليل.", "The town search is not responding right now: try again in a moment.");
    } finally { villeEnCours = false; }
  }
  window.MOSQUEES_MONDE = { versLieu, ajouterZone, lireZone, chargerMonde, couleurPays, nomPays, legende, chercherVille, zoneTxt, OVERPASS };   // pour les tests
  const apresLeaflet = [];
  function chargerLeaflet(fin) {
    if (fin) apresLeaflet.push(fin);
    const suite = () => { demarrerCarte(); apresLeaflet.splice(0).forEach(f => f()); };
    if (window.L) return suite();
    if (document.getElementById("leaflet-js")) return;
    const css = document.createElement("link"); css.rel = "stylesheet"; css.href = "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css";
    document.head.appendChild(css);
    const js = document.createElement("script"); js.id = "leaflet-js"; js.src = "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js";
    js.onload = suite; document.head.appendChild(js);
  }
  function voirSurCarte(id) {
    const l = LIEUX.concat(MONDE).find(x => x.i === id || x.p === "mosquee/" + id + "/");
    if (!l) return false;
    if (!actifs.has(l.t)) actifs.add(l.t);
    seulementPages = false; filtres();
    $("mq-carte").scrollIntoView({ behavior: "smooth", block: "center" });
    chargerLeaflet(() => { if (!marqueurs[l.i] || !calque.hasLayer(marqueurs[l.i])) { requete = ""; $("mq-q").value = ""; dessiner(); } carte.setView([l.a, l.o], 17); marqueurs[l.i].openPopup(); });
    return true;
  }
  window.MOSQUEES_VOIR = voirSurCarte;
  function voirDemande() {
    const id = new URLSearchParams(location.search).get("lieu");
    if (id) { const l = LIEUX.find(x => x.i === id || x.p === "mosquee/" + id + "/"); if (l && carte) { carte.setView([l.a, l.o], 17); setTimeout(() => marqueurs[l.i] && marqueurs[l.i].openPopup(), 50); } }
  }

  function envoyer(format, marque, lieu) {
    const corps = new URLSearchParams();
    corps.append(CH.format, format); corps.append(CH.marque, marque); corps.append(CH.lieu, lieu);
    corps.append(CH.date, new Date().toISOString().slice(0, 10));
    if (window.__envois) { window.__envois.push(Object.fromEntries(corps)); return Promise.resolve(); }   // tests
    return fetch(FORM, { method: "POST", mode: "no-cors", body: corps });
  }
  function maPosition(fin) {
    if (!navigator.geolocation) { fin && fin(null); return; }
    navigator.geolocation.getCurrentPosition(g => fin({ a: g.coords.latitude, o: g.coords.longitude }), () => fin(null), { enableHighAccuracy: true, timeout: 15000 });
  }

  document.addEventListener("click", e => {
    const f = e.target.closest("#mq-filtres [data-type]");
    if (f) { const t = f.dataset.type; if (actifs.has(t) && actifs.size === 1) return; actifs.has(t) ? actifs.delete(t) : actifs.add(t); filtres(); dessiner(); if (requete) rechercher(); else proches(); return; }
    if (e.target.closest("#mq-filtres [data-pages]")) { seulementPages = !seulementPages; filtres(); dessiner(); if (requete) rechercher(); else proches(); return; }
    const v = e.target.closest("[data-ok],[data-ko]");
    if (v) {
      const ok = v.hasAttribute("data-ok"), id = ok ? v.dataset.ok : v.dataset.ko;
      envoyer(ok ? "LIEU-PRIERE-OK" : "LIEU-PRIERE-KO", id, "|" + jeton).then(() => { v.parentNode.innerHTML = `<small>${L2("Merci ! Pris en compte dans 2 heures environ.", "شكرًا! يُحتسب خلال ساعتين تقريبًا.", "Thank you! Counted within about 2 hours.")}</small>`; }, () => {});
      return;
    }
    if (e.target.closest("[data-ville-monde]")) { chercherVille($("mq-q").value); return; }
    const voir = e.target.closest("[data-voir]");
    if (voir) { fermerSig(); voirSurCarte(voir.dataset.voir); return; }
    const lien = e.target.closest('a[href$="#signaler"]');
    if (lien && lien.pathname === location.pathname) { e.preventDefault(); ouvrirSig(); }
  });
  let attente = null;
  $("mq-q").addEventListener("input", () => { clearTimeout(attente); attente = setTimeout(rechercher, 250); });
  $("mq-q").addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); clearTimeout(attente); rechercher(true); } });
  $("mq-autour").addEventListener("click", () => {
    $("mq-autour-txt").textContent = L2("Recherche de votre position…", "جارٍ تحديد موقعك…", "Finding your position…");
    maPosition(p => {
      if (!p) { $("mq-autour-txt").textContent = L2("Position indisponible : autorisez la localisation, ou cherchez une ville.", "الموقع غير متاح: اسمح بتحديد الموقع، أو ابحث عن مدينة.", "Position unavailable: allow location access, or search for a town."); return; }
      ici = p; $("mq-autour-txt").textContent = "";
      chargerLeaflet(() => carte.setView([p.a, p.o], 14));
      requete = ""; $("mq-q").value = ""; $("mq-info").textContent = "";
      proches();
    });
  });
  window.MOSQUEES_ICI = p => { ici = p; proches(); };     // pour les tests

  // ---- « Signaler une mosquée ou une salle de prière » : fenêtre, carte avec repère déplaçable, « Me localiser », « Confirmer »
  const pop = $("mq-sig-pop");
  let mini = null, repere = null;
  const etat = (txt, err) => { const t = $("mq-pos-txt"); t.textContent = txt; t.className = "geo-status" + (err ? " err" : ""); };
  function nonConfirme() {
    $("mq-pos").value = ""; $("mq-pos-ok").classList.remove("fait");
    etat(L2("Repère placé : vérifiez-le, puis « Confirmer cette position ».", "تم وضع العلامة: تحقّق منها ثم « أكّد هذا الموقع ».", "Marker placed: check it, then “Confirm this position”."));
  }
  function placerRepere(lat, lon, zoom) {
    if (!mini) return;
    if (repere) repere.setLatLng([lat, lon]);
    else { repere = L.marker([lat, lon], { draggable: true, autoPan: true }).addTo(mini); repere.on("dragend", nonConfirme); }
    if (zoom) mini.setView([lat, lon], zoom);
    nonConfirme();
  }
  function demarrerMini() {
    if (mini || !window.L) return;
    const c = carte ? carte.getCenter() : { lat: 34.1, lng: 9.6 };
    mini = L.map("mq-sig-carte", { scrollWheelZoom: false }).setView([c.lat, c.lng], carte ? Math.max(carte.getZoom(), 6) : 6);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' }).addTo(mini);
    mini.on("click", e => placerRepere(e.latlng.lat, e.latlng.lng));
  }
  function ouvrirSig() {
    pop.hidden = false;
    $("mq-statut").textContent = ""; $("mq-statut").className = "";
    derniers();
    chargerLeaflet(() => { demarrerMini(); setTimeout(() => mini && mini.invalidateSize(), 60); });
  }
  function fermerSig() {
    if (pop.hidden) return;
    pop.hidden = true;
    if (location.hash === "#signaler") history.replaceState(null, "", location.pathname + location.search);
  }
  window.MOSQUEES_SIGNALER = ouvrirSig;

  function derniers() {
    const box = $("mq-derniers");
    const ref = new Date(String(SIG.maj || "").slice(0, 10) + "T12:00:00");
    const l = LIEUX.filter(p => p.vis && /^\d{4}-\d\d-\d\d$/.test(p.date || "") && (isNaN(ref) || (ref - new Date(p.date + "T12:00:00")) / 864e5 <= 30))
      .sort((x, y) => y.date.localeCompare(x.date)).slice(0, 10);
    if (!l.length) {
      box.innerHTML = `<p class="sig-vide">${L2("Aucun lieu signalé ces 30 derniers jours : soyez le premier !", "لم يُضف أي مكان خلال الثلاثين يومًا الأخيرة: كن الأول!", "No place reported in the last 30 days: be the first!")}</p>`;
      return;
    }
    const lg = document.documentElement.lang;
    box.innerHTML = `<p class="sig-titre">${L2("Derniers lieux signalés par les visiteurs", "آخر الأماكن التي أضافها الزوار", "Latest places reported by visitors")}</p><ul>` + l.map(p => {
      const vu = new Date(p.date + "T12:00:00").toLocaleDateString({ ar: "ar-TN", en: "en-GB", tr: "tr-TR", id: "id-ID", ur: "ur-PK", de: "de-DE", es: "es-ES" }[lg] || "fr-FR", { day: "numeric", month: "short" });
      const st = p.statut === "confirme" ? L2("confirmé par {n} visiteurs", "أكّده {n} زوار", "confirmed by {n} visitors").replace("{n}", p.ok) : L2("à confirmer", "في انتظار التأكيد", "to be confirmed");
      return `<li><b>${esc(titre(p))}</b> · ${nomT(p.t)} <small>· ${L2("signalé le", "أُضيف في", "reported on")} ${vu} · ${st}</small>
        <button type="button" data-voir="${esc(p.i)}">${L2("voir sur la carte", "اعرض على الخريطة", "see on the map")}</button></li>`;
    }).join("") + `</ul>`;
  }

  $("mq-sig-ouvrir").addEventListener("click", ouvrirSig);
  $("mq-sig-fermer").addEventListener("click", fermerSig);
  pop.addEventListener("click", e => { if (e.target === pop) fermerSig(); });
  document.addEventListener("keydown", e => { if (e.key === "Escape" && !pop.hidden) fermerSig(); });
  if (location.hash === "#signaler") ouvrirSig();

  $("mq-ma-pos").addEventListener("click", () => {
    etat(L2("Recherche de votre position…", "جارٍ تحديد موقعك…", "Finding your position…"));
    maPosition(p => {
      if (!p) { etat(L2("Position indisponible : touchez plutôt l'endroit sur la carte.", "الموقع غير متاح: المس المكان على الخريطة.", "Position unavailable: tap the spot on the map instead."), true); return; }
      chargerLeaflet(() => { demarrerMini(); placerRepere(p.a, p.o, 17); });
    });
  });
  $("mq-pos-ok").addEventListener("click", () => {
    if (!repere) { etat(L2("Placez d'abord le repère : « Me localiser (GPS) » ou touchez la carte.", "ضع العلامة أولًا: « حدّد موقعي » أو المس الخريطة.", "Place the marker first: “Locate me (GPS)” or tap the map."), true); return; }
    const g = repere.getLatLng();
    $("mq-pos").value = g.lat.toFixed(5) + "," + g.lng.toFixed(5);
    $("mq-pos-ok").classList.add("fait");
    etat(L2("✔ Position confirmée", "✔ تم تأكيد الموقع", "✔ Position confirmed") + " : " + g.lat.toFixed(5) + ", " + g.lng.toFixed(5));
  });
  $("mq-form").addEventListener("submit", e => {
    e.preventDefault();
    const st = $("mq-statut"), type = $("mq-type").value, pos = $("mq-pos").value, nom = $("mq-nom").value.replace(/\|/g, " ").trim().slice(0, 60);
    const dire = (txt, cls) => { st.textContent = txt; st.className = cls || ""; };
    if (!["mosquee", "salle"].includes(type)) { dire(L2("Choisissez : mosquée ou salle de prière.", "اختر: مسجد أو مصلّى.", "Choose: mosque or prayer room."), "err"); return; }
    if (!/^-?\d+\.\d+,-?\d+\.\d+$/.test(pos)) { dire(L2("Placez le repère sur la carte, puis « Confirmer cette position ».", "ضع العلامة على الخريطة، ثم « أكّد هذا الموقع ».", "Place the marker on the map, then “Confirm this position”."), "err"); return; }
    const [la, lo] = pos.split(",").map(Number);
    if (!(la > 30 && la < 37.6 && lo > 7.4 && lo < 11.7)) { dire(L2("Cette position n'est pas en Tunisie.", "هذا الموقع ليس في تونس.", "This position is not in Tunisia."), "err"); return; }
    if ($("mq-form").querySelector("[name=_gotcha]").value) return;
    const btn = $("mq-envoyer"); btn.disabled = true; dire(L2("Envoi…", "جارٍ الإرسال…", "Sending…"));
    envoyer("LIEU-PRIERE", type + "|" + nom, pos + "|" + jeton).then(() => {
      dire(L2("Merci ! Le lieu apparaîtra sur la carte dans 2 heures environ (« à confirmer » jusqu'à ce qu'un autre visiteur le confirme).", "شكرًا! سيظهر المكان على الخريطة خلال ساعتين تقريبًا (« في انتظار التأكيد » حتى يؤكّده زائر آخر).", "Thank you! The place will appear on the map in about 2 hours (“to be confirmed” until another visitor confirms it)."), "ok");
      $("mq-form").reset(); $("mq-pos").value = ""; $("mq-pos-ok").classList.remove("fait"); etat("");
      if (repere && mini) { mini.removeLayer(repere); repere = null; }
      setTimeout(fermerSig, 3500);
    }, () => dire(L2("Échec de l'envoi — vérifiez votre connexion et réessayez.", "تعذّر الإرسال — تحقّق من الاتصال وأعد المحاولة.", "Sending failed — check your connection and try again."), "err"))
      .then(() => { btn.disabled = false; });
  });

  filtres();
  document.addEventListener("langue", () => { filtres(); legende(); if (requete) rechercher(); else proches(); if (carte) dessiner(); if (!pop.hidden) derniers(); });
  if (new URLSearchParams(location.search).get("lieu")) chargerLeaflet();
  else if ("IntersectionObserver" in window) {
    const o = new IntersectionObserver(es => { if (es.some(x => x.isIntersecting)) { o.disconnect(); chargerLeaflet(); } });
    o.observe($("mq-carte"));
  } else chargerLeaflet();
})();
