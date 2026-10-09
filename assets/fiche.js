/* Pages des mosquées (mosquee/…/) et liste (grandes-mosquees/) :
   - nom dans la langue choisie s'il existe (Wikidata), sinon arabe + français (demande d'Ahmed) ;
   - résumé Wikipédia dans la langue choisie s'il existe, sinon anglais puis français, en le disant ;
   - petite carte (Leaflet + fond OpenStreetMap) avec le repère de la mosquée, chargée seulement quand on la voit. */
(function () {
  const L2 = (fr, ar, en) => (window.T ? window.T(fr, ar, en) : fr);
  const NOMS_LANGUES = { fr: ["français", "الفرنسية", "French"], en: ["anglais", "الإنجليزية", "English"], ar: ["arabe", "العربية", "Arabic"] };

  // noms : un seul visible (celui de la langue, sinon arabe/français) ; le nom arabe en second quand la page n'est pas en arabe
  function noms() {
    const lg = document.documentElement.lang;
    document.querySelectorAll(".mq-noms, .mq-sous-titre, .mq-groupe h3, .mq-liens li a").forEach(bloc => {
      const n = [...bloc.querySelectorAll(":scope > .nl")];
      if (!n.length) return;
      const par = l => n.find(x => x.dataset.nl === l);
      const choisi = par(lg) || (["ar", "ur"].includes(lg) ? (par("ar") || par("fr") || par("en")) : (par("fr") || par("en") || par("ar"))) || n[0];
      const second = bloc.tagName === "H1" && lg !== "ar" && par("ar") && par("ar") !== choisi ? par("ar") : null;
      n.forEach(x => { x.hidden = x !== choisi && x !== second; x.classList.toggle("nl-second", x === second); });
    });
  }

  // résumé Wikipédia : langue choisie, sinon anglais, sinon français (sinon le premier disponible), avec une phrase qui le dit
  function resumes() {
    const r = [...document.querySelectorAll(".mq-resume")];
    if (!r.length) return;
    const lg = document.documentElement.lang, par = l => r.find(x => x.dataset.rl === l);
    const choisi = par(lg) || par("en") || par("fr") || par("ar") || r[0];
    r.forEach(x => x.classList.toggle("choisi", x === choisi));
    const note = document.getElementById("mq-resume-note");
    if (note) {
      const autre = choisi.dataset.rl !== lg;
      note.hidden = !autre;
      if (autre) {
        const nl = NOMS_LANGUES[choisi.dataset.rl];
        note.textContent = L2("Pas de résumé Wikipédia dans votre langue : le voici en {l}.", "لا يوجد ملخّص من ويكيبيديا بلغتك: ها هو بـ{l}.", "No Wikipedia summary in your language: here it is in {l}.")
          .replace("{l}", nl ? L2(...nl) : choisi.dataset.rl);
      }
    }
  }

  // petite carte de la mosquée
  function carte() {
    const div = document.getElementById("mq-mini");
    if (!div || div.dataset.pret) return;
    const go = () => {
      if (div.dataset.pret || !window.L) return;
      div.dataset.pret = "1";
      const lat = +div.dataset.lat, lon = +div.dataset.lon;
      const m = L.map(div, { scrollWheelZoom: false }).setView([lat, lon], 16);
      L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">contributeurs OpenStreetMap</a>' }).addTo(m);
      L.circleMarker([lat, lon], { radius: 10, color: "#F2B33D", weight: 3, fillColor: "#0E6B4C", fillOpacity: .95 }).addTo(m);
    };
    const charger = () => {
      if (window.L) return go();
      if (document.getElementById("leaflet-js")) return;
      const css = document.createElement("link"); css.rel = "stylesheet"; css.href = "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css";
      document.head.appendChild(css);
      const js = document.createElement("script"); js.id = "leaflet-js"; js.src = "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js";
      js.onload = go; document.head.appendChild(js);
    };
    if ("IntersectionObserver" in window) {
      const o = new IntersectionObserver(es => { if (es.some(x => x.isIntersecting)) { o.disconnect(); charger(); } }, { rootMargin: "200px" });
      o.observe(div);
    } else charger();
  }

  function tout() { noms(); resumes(); }
  window.FICHE = { noms, resumes };
  document.addEventListener("langue", tout);
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", () => { tout(); carte(); });
  else { tout(); carte(); }
})();
