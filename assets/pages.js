/* Pages « Le rôle de la mosquée », « Construire une mosquée », « Histoires des mosquées » (23/10/2026) :
   vidéo YouTube chargée seulement après un appui (youtube-nocookie : pas de cookie publicitaire, rien de chargé sans le
   vouloir), dans la langue de la page quand YouTube a des sous-titres. */
(function () {
  document.addEventListener("click", e => {
    const b = e.target.closest("[data-yt]");
    if (!b || !/^[\w-]{11}$/.test(b.dataset.yt)) return;
    const f = document.createElement("iframe");
    f.src = "https://www.youtube-nocookie.com/embed/" + b.dataset.yt + "?autoplay=1&rel=0&hl=" + encodeURIComponent(document.documentElement.lang || "fr");
    f.title = b.querySelector("b") ? b.querySelector("b").textContent.trim() : "YouTube";
    f.allow = "autoplay; encrypted-media; picture-in-picture; fullscreen";
    f.setAttribute("allowfullscreen", "");
    f.loading = "lazy";
    f.className = "pg-video-cadre";
    b.replaceWith(f);
  });
})();

/* Tri des listes de grandes mosquées (demande d'Ahmed du 23/10/2026) : <select data-tri="id de la liste"> ; chaque élément de la
   liste porte data-i (ordre de la page), data-an (année de construction, vide si inconnue : toujours à la fin) et data-n (notoriété).
   Le choix est gardé pour la visite suivante (clé « tri-mosquees »). Textes des options : éléments cachés [data-txt]. */
(function () {
  const html = document.documentElement;
  const lire = k => { try { return localStorage.getItem(k) || ""; } catch (e) { return ""; } };
  const ecrire = (k, v) => { try { localStorage.setItem(k, v); } catch (e) { /* stockage refusé : sans importance */ } };
  const txt = (bloc, cle) => {
    const b = bloc.querySelector(`[data-txt="${cle}"]`);
    if (!b) return null;
    const e = b.querySelector(`[data-l="${html.lang}"]`) || b.querySelector('[data-l="en"]') || b;
    return e.textContent.trim();
  };
  const nom = el => { const n = el.querySelector(".mo-nom .nl:not([hidden]), .mq-grande-txt b [data-l]:not([hidden])") || el.querySelector(".mo-nom, .mq-grande-txt b") || el; return n.textContent.trim(); };
  function trier(sel) {
    const liste = document.getElementById(sel.dataset.tri);
    if (!liste) return;
    const els = [...liste.children].filter(x => x.dataset.i !== undefined);
    const an = x => x.dataset.an === "" || x.dataset.an === undefined ? null : +x.dataset.an;
    const parAn = sens => (a, b) => (an(a) === null) - (an(b) === null) || sens * ((an(a) || 0) - (an(b) || 0)) || (+a.dataset.i - +b.dataset.i);
    const f = { page: (a, b) => +a.dataset.i - +b.dataset.i, connue: (a, b) => +a.dataset.i - +b.dataset.i, ancien: parAn(1), recent: parAn(-1),
      az: (a, b) => nom(a).localeCompare(nom(b), html.lang, { sensitivity: "base" }) }[sel.value] || ((a, b) => +a.dataset.i - +b.dataset.i);
    els.sort(f).forEach(x => liste.appendChild(x));
  }
  function preparer() {
    document.querySelectorAll("select[data-tri]").forEach(sel => {
      const p = sel.closest(".tri");
      [...sel.options].forEach(o => { const t = txt(p, "t_" + o.value); if (t) o.textContent = t; });
      const garde = lire("tri-mosquees");
      if (garde && [...sel.options].some(o => o.value === garde)) { sel.value = garde; trier(sel); }
      sel.addEventListener("change", () => { ecrire("tri-mosquees", sel.value); trier(sel); });
    });
  }
  // description d'une grande mosquée du monde : donnees/monde/<langue>.json, chargé une fois, à la première ouverture
  let desc = null;
  document.addEventListener("toggle", async e => {
    const d = e.target;
    if (!d.matches || !d.matches("details.mo-desc") || !d.open) return;
    const boite = d.querySelector(".mo-desc-txt");
    if (boite.dataset.pret) return;
    const carte = d.closest("[data-q]"), page = d.closest("main");
    try {
      if (!desc) desc = fetch((html.dataset.racine || "") + "donnees/monde/" + html.lang + ".json").then(r => r.json());
      const x = (await desc)[carte.dataset.q];
      boite.textContent = "";
      if (x && x.r) {
        const p = document.createElement("p"); p.textContent = x.r; p.lang = x.rl; p.dir = ["ar", "ur"].includes(x.rl) ? "rtl" : "ltr";
        const s = document.createElement("small"), a = document.createElement("a");
        a.href = x.w; a.target = "_blank"; a.rel = "noopener"; a.textContent = txt(page, "wiki_extrait") || "Wikipedia (CC BY-SA 4.0)";
        s.appendChild(a); boite.append(p, s);
      } else if (x && x.d) { const p = document.createElement("p"); p.textContent = x.d; boite.appendChild(p); }
      else { const p = document.createElement("p"); p.className = "aide"; p.textContent = txt(page, "pas_de_desc") || "—"; boite.appendChild(p); }
      boite.dataset.pret = "1";
    } catch (err) { boite.textContent = "…"; }
  }, true);
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", preparer); else preparer();
  window.MOSQUEES_TRI = { trier };    // pour les tests
})();
