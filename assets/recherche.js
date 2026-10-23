/* Page « Grandes mosquées » : recherche (demande d'Ahmed du 23/10/2026 : « toujours pouvoir chercher les grandes mosquées
   d'autres pays »).
   - En Tunisie : la liste de la page est filtrée à chaque lettre (noms dans toutes les langues, sans accents).
   - Dans le monde : Wikidata (query.wikidata.org, sans clé), mosquées dont le nom ou la description contient le mot (nom,
     ville ou pays, dans n'importe quelle langue), classées de la plus connue à la moins connue (nombre d'articles Wikipédia).
     Chaque résultat : photo (Wikimedia Commons), nom et description dans la langue de la page, « Voir sur la carte »
     (accueil ?ll=lat,lon), Wikipédia dans la langue de la page, et « Notre page » si la mosquée a une page sur ce site.
   Textes : éléments cachés [data-txt] de la page (déjà traduits dans les 21 langues par tools/construire.py). */
(function () {
  const zone = document.getElementById("mq-cherche");
  if (!zone) return;
  const html = document.documentElement;
  const rp = html.dataset.racinePages !== undefined ? html.dataset.racinePages : (html.dataset.racine || "");
  const pages = JSON.parse(zone.dataset.pages || "{}");          // QID Wikidata -> page de ce site
  const champ = document.getElementById("mq-cherche-q");
  const sortie = document.getElementById("mq-cherche-res");
  const lg = () => html.lang || "fr";
  const txt = cle => {
    const b = document.querySelector(`[data-txt="${cle}"]`);
    if (!b) return cle;
    const e = b.querySelector(`[data-l="${lg()}"]`) || b.querySelector('[data-l="en"]') || b;
    return e.textContent.trim();
  };
  const sans = s => (s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[ً-ْـ]/g, "").toLowerCase();
  const esc = s => String(s || "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  champ.placeholder = txt("ph");

  // ---- en Tunisie : filtre de la liste de la page ----
  function filtrer(q) {
    const m = sans(q).trim();
    let n = 0;
    document.querySelectorAll(".mq-grande").forEach(a => { const ok = !m || sans(a.textContent).includes(m); a.hidden = !ok; if (ok) n++; });
    document.querySelectorAll(".mq-groupe").forEach(g => {
      let vus = 0;
      g.querySelectorAll("li").forEach(li => { const ok = !m || sans(g.querySelector("h3").textContent + " " + li.textContent).includes(m); li.hidden = !ok; if (ok) vus++; });
      g.hidden = !vus; n += vus;
    });
    return n;
  }

  // ---- dans le monde : Wikidata ----
  let compteur = 0, attente = null;
  function requete(mot, l) {
    const langues = [...new Set([l, "en", "fr", "ar"])].join(",");
    return `SELECT ?item ?label ?desc ?img ?coord ?liens ?art ?date WHERE {
 SERVICE wikibase:mwapi { bd:serviceParam wikibase:endpoint "www.wikidata.org"; wikibase:api "Search";
   mwapi:srsearch "${mot} haswbstatement:P31=Q32815|P31=Q1454820"; mwapi:srlimit "300". ?item wikibase:apiOutputItem mwapi:title. }
 FILTER(EXISTS {?item wdt:P31 wd:Q32815} || EXISTS {?item wdt:P140 wd:Q432})
 ?item wikibase:sitelinks ?liens. OPTIONAL {?item wdt:P18 ?img} OPTIONAL {?item wdt:P625 ?coord} OPTIONAL {?item wdt:P571 ?date}
 OPTIONAL {?art schema:about ?item; schema:isPartOf <https://${l}.wikipedia.org/>}
 SERVICE wikibase:label { bd:serviceParam wikibase:language "${langues}". ?item rdfs:label ?label. ?item schema:description ?desc }
} ORDER BY DESC(?liens) LIMIT 60`;
  }
  // mot nettoyé : lettres, chiffres, espaces, apostrophe et tiret seulement (rien qui puisse casser la requête)
  const nettoyer = q => q.replace(/[^\p{L}\p{N}\s'’-]/gu, " ").replace(/\s+/g, " ").trim().slice(0, 50);

  const annee = d => { const m = /^(-?)(\d+)-/.exec(d || ""); return m ? (m[1] ? -1 : 1) * +m[2] : null; };
  function carteRes(r, i) {
    const qid = r.item.split("/").pop();
    const img = r.local || (r.img ? r.img.replace(/^http:/, "https:") + "?width=330" : "");
    const pt = /Point\(([-\d.]+) ([-\d.]+)\)/.exec(r.coord || "");
    const liens = [];
    const notre = pages[qid] || r.page || ((window.MOSQUEES_MONDE_GRANDES || []).find(g => g.i === "wd-" + qid) || {}).p;
    if (notre) liens.push(`<a class="btn-principal" href="${rp}${notre}">${esc(txt("notre_page"))}</a>`);
    if (pt) liens.push(`<a class="chipbtn" href="${rp}?ll=${(+pt[2]).toFixed(5)},${(+pt[1]).toFixed(5)}#carte">${esc(txt("voir_carte"))}</a>`);
    if (r.art) liens.push(`<a class="chipbtn" href="${esc(r.art)}" target="_blank" rel="noopener">${esc(txt("wikipedia"))}</a>`);
    const an = annee(r.date);
    return `<article class="mq-monde-res" data-i="${i}" data-an="${an === null ? "" : an}">${img ? `<span class="mq-monde-img"><img src="${esc(img)}" alt="" loading="lazy" referrerpolicy="no-referrer"></span>` : `<span class="mq-monde-img vide" aria-hidden="true"></span>`}`
      + `<div>${an !== null ? `<b class="mo-an">${an < 0 ? -an + " " + esc(txt("av_jc")) : an}</b>` : ""}<b class="mo-nom">${esc(r.label)}</b>${r.desc ? `<small>${esc(r.desc)}</small>` : ""}<p class="mq-monde-liens">${liens.join(" ")}</p></div></article>`;
  }

  // grandes mosquées du monde de notre site (donnees/monde_carte.js) : nom ou PAYS dans n'importe quelle langue, sans attendre
  // Wikidata (23/10/2026 : « Palestine » doit trouver al-Aqsa, même quand Wikidata est saturé)
  function locales(q) {
    const m = sans(q).trim();
    if (m.length < 3) return [];
    return (window.MOSQUEES_MONDE_GRANDES || []).filter(g => sans(Object.values(g.n || {}).concat(Object.values(g.pn || {}), Object.values(g.d || {})).join(" | ")).includes(m))
      .sort((a, b) => (b.k || 0) - (a.k || 0))
      .map(g => ({ item: "http://www.wikidata.org/entity/" + g.i.slice(3), label: (g.n || {})[lg()] || (g.n || {}).en || (g.n || {}).fr,
        desc: (g.pn || {})[lg()] || (g.pn || {}).en || "", date: g.an === null || g.an === undefined ? "" : (g.an < 0 ? "-" : "") + String(Math.abs(g.an)).padStart(4, "0") + "-01-01",
        coord: `Point(${g.o} ${g.a})`, local: g.f ? rp + g.f : "", page: g.p }));
  }
  function afficher(bloc, res, enCours) {
    const options = ["connue", "ancien", "recent", "az"].map(o => `<option value="${o}">${esc(txt("t_" + o))}</option>`).join("");
    bloc.innerHTML = res.length ? `<p class="tri"><label>${esc(txt("trier"))} <select data-tri="mq-monde-liste-res">${options}</select></label></p>`
      + `<div class="mq-monde-grille" id="mq-monde-liste-res">${res.map(carteRes).join("")}</div>`
      + (enCours ? `<p class="aide mq-attente">${esc(txt("attente"))}</p>` : "") + `<p class="aide">${esc(txt("source"))}</p>`
      : `<p class="aide">${esc(txt("aucune"))}</p>`;
    const sel = bloc.querySelector("select[data-tri]");
    if (sel && window.MOSQUEES_TRI) sel.addEventListener("change", () => window.MOSQUEES_TRI.trier(sel));
  }
  async function monde(q) {
    const mot = nettoyer(q), n = ++compteur, bloc = document.getElementById("mq-monde-res");
    if (mot.length < 3) { bloc.innerHTML = `<p class="aide">${esc(txt("court"))}</p>`; return; }
    const loc = locales(q);
    if (loc.length) afficher(bloc, loc, true);
    else bloc.innerHTML = `<p class="aide mq-attente">${esc(txt("attente"))}</p>`;
    try {
      const url = "https://query.wikidata.org/sparql?format=json&query=" + encodeURIComponent(requete(mot, lg()));
      const rep = window.__wikidata ? await window.__wikidata(url) : await (await fetch(url, { headers: { Accept: "application/sparql-results+json" } })).json();
      if (n !== compteur) return;                                    // une recherche plus récente a été lancée
      const vus = new Set(loc.map(r => r.item)), res = loc.slice();
      for (const b of rep.results.bindings) {
        const r = Object.fromEntries(Object.entries(b).map(([k, v]) => [k, v.value]));
        if (vus.has(r.item) || /^Q\d+$/.test(r.label || "")) { const v = res.find(x => x.item === r.item); if (v && r.date && (!v.date || r.date < v.date)) v.date = r.date; continue; }   // une seule fois chaque mosquée (la plus ancienne date) ; pas de fiche sans nom
        vus.add(r.item); res.push(r);
        if (res.length >= Math.max(12, loc.length + 6)) break;
      }
      afficher(bloc, res, false);
    } catch (e) {
      if (n === compteur && !loc.length) bloc.innerHTML = `<p class="aide mq-erreur">${esc(txt("erreur"))}</p>`;
      else if (n === compteur) bloc.querySelector(".mq-attente") && bloc.querySelector(".mq-attente").remove();
    }
  }

  function chercher(q, tout) {
    q = (q || "").trim();
    if (!q) { filtrer(""); sortie.hidden = true; return; }
    const n = filtrer(q);
    sortie.hidden = false;
    document.getElementById("mq-tunisie-res").innerHTML = n
      ? `<p class="aide"><b>${n}</b> · <a href="#mq-liste">${esc(txt("tunisie_titre"))} ↓</a></p>`
      : `<p class="aide">${esc(txt("tunisie_aucune"))}</p>`;
    clearTimeout(attente);
    if (tout) monde(q); else attente = setTimeout(() => monde(q), 900);
  }

  champ.addEventListener("input", () => chercher(champ.value, false));
  zone.addEventListener("submit", e => { e.preventDefault(); chercher(champ.value, true); });
  zone.addEventListener("click", e => {
    const b = e.target.closest("[data-ex]");
    if (!b) return;
    champ.value = b.textContent.trim();
    chercher(b.dataset.ex, true);
  });
  const q0 = new URLSearchParams(location.search).get("q");
  if (q0) { champ.value = q0; chercher(q0, true); }
  window.MOSQUEES_RECHERCHE = { filtrer, requete, nettoyer, chercher, locales };   // pour les tests
})();
