/* Accueil léger (19/11/2026, Ahmed, CV.3c) : les données de la carte (donnees/lieux.js : 2 255 lieux de prière, signales.js,
   monde_carte.js) et le script de la carte (assets/mosquees.js) ne sont plus chargés avec la page (prête en 8 à 14 s sur un
   téléphone moyen) mais au 1er geste (défiler, toucher, touche du clavier) ou quand la carte approche de l'écran ; tout de suite
   si l'adresse vise un lieu (?lieu=, ?ll=, #ancre). Les fichiers (attribut data-scripts, chemins relatifs à CE fichier) sont
   ajoutés dans l'ordre (async = false) avec le même ?v= que ce fichier. Aucun script en ligne (CSP). */
(function () {
  "use strict";
  var moi = document.currentScript;
  if (!moi) return;
  var base = moi.src, v = base.split("?")[1] || "";
  var fichiers = (moi.getAttribute("data-scripts") || "").split("|").filter(Boolean);
  var gestes = ["scroll", "pointerdown", "keydown", "touchstart"], fait = false;
  function charger() {
    if (fait) return;
    fait = true;
    gestes.forEach(function (e) { window.removeEventListener(e, charger, true); });
    fichiers.forEach(function (f) {
      var s = document.createElement("script");
      s.src = new URL(f, base).href.split("?")[0] + (v ? "?" + v : "");
      s.async = false;
      document.body.appendChild(s);
    });
  }
  window.chargerCarte = charger;
  var q = new URLSearchParams(location.search);
  if (q.get("lieu") || q.get("ll") || location.hash) { charger(); return; }
  gestes.forEach(function (e) { window.addEventListener(e, charger, { capture: true, passive: true }); });
  var c = document.getElementById("carte");
  if (c && "IntersectionObserver" in window) {
    var o = new IntersectionObserver(function (es) {
      if (es.some(function (x) { return x.isIntersecting; })) { o.disconnect(); charger(); }
    }, { rootMargin: "200px" });
    o.observe(c);
  }
})();
