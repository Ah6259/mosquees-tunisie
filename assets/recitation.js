/* Récitation du Coran par cheikh Ali El Barrak (demande d'Ahmed, 09/10/2026), « comme le site Le message » :
   - à la PREMIÈRE visite, un écran d'entrée propose « Entrer avec la récitation » ou « Entrer sans le son »
     (les navigateurs interdisent le son automatique sans un geste du visiteur) ;
   - le choix est gardé (clé propre au site « recitation-mosquees » : « oui » / « non ») ; avec « oui », chaque page relance la
     récitation là où elle s'était arrêtée (position gardée pour la visite, clé « recitation-mosquees-position ») ;
   - lecteur YouTube intégré PETIT et VISIBLE en bas de l'écran (règle de YouTube), domaine youtube-nocookie.com (pas de cookie
     avant la lecture), bouton rond dans l'en-tête pour couper / relancer, × pour fermer ;
   - source : chaîne YouTube OFFICIELLE « الشيخ علي البراق / Cheikh Ali Al-Barrak » ; le site marche sans la vidéo (bloquée, hors ligne).
   Aucun script YouTube n'est chargé : commandes « pause / lecture » par postMessage (enablejsapi=1). */
(function () {
  const CLE = "recitation-mosquees", CLE_POS = "recitation-mosquees-position";
  const CHAINE = "https://www.youtube.com/channel/UC4DO2q7J9Y71xeIKj0XqKDQ";
  const VIDEOS = {
    ymODAAIfowI: ["Juz' 'Amma (complet)", "جزء عمّ كاملًا", "Juz' 'Amma (complete)"],
    ygnfUhIY09w: ["Al-Fâtiha", "سورة الفاتحة", "Al-Fatiha"],
    "4HEAN0AlIKc": ["Yâ-Sîn", "سورة يس", "Ya-Sin"]
  };
  const DEFAUT = "ymODAAIfowI";
  const ORIGINE_YT = "https://www.youtube-nocookie.com";
  const L2 = (fr, ar, en) => (window.T ? window.T(fr, ar, en) : fr);
  const lire = (k, s) => { try { return (s || localStorage).getItem(k); } catch (e) { return null; } };
  const ecrire = (k, v, s) => { try { (s || localStorage).setItem(k, v); } catch (e) {} };
  const choix = () => { const c = lire(CLE); return c === "oui" || c === "non" ? c : null; };
  let boite = null, iframe = null, enCours = false;

  function position() {
    try { const p = JSON.parse(lire(CLE_POS, sessionStorage) || "{}"); return VIDEOS[p.v] ? p : { v: DEFAUT, t: 0 }; } catch (e) { return { v: DEFAUT, t: 0 }; }
  }
  function garderPosition(v, t) { ecrire(CLE_POS, JSON.stringify({ v, t: Math.max(0, Math.floor(t || 0)) }), sessionStorage); }

  function adresse(v, t) {
    const o = location.protocol === "https:" ? "&origin=" + encodeURIComponent(location.origin) : "";
    return `${ORIGINE_YT}/embed/${v}?autoplay=1&playsinline=1&rel=0&modestbranding=1&enablejsapi=1${t > 5 ? "&start=" + Math.floor(t) : ""}${o}`;
  }
  window.RECITATION_ADRESSE = adresse;      // pour les tests

  function textesBoite() {
    if (!boite) return;
    const p = position();
    boite.querySelector(".rec-titre").textContent = L2("Récitation : cheikh Ali El Barrak", "تلاوة الشيخ علي البراق", "Recitation: Sheikh Ali El Barrak") + " — " + L2(...VIDEOS[p.v]);
    boite.querySelector(".rec-fermer").setAttribute("aria-label", L2("Arrêter la récitation", "أوقف التلاوة", "Stop the recitation"));
    const a = boite.querySelector(".rec-chaine"); a.textContent = L2("Chaîne officielle", "القناة الرسمية", "Official channel");
  }

  function lancer(v, depuis) {
    const p = position();
    v = VIDEOS[v] ? v : p.v;
    const t = depuis !== undefined ? depuis : (v === p.v ? p.t : 0);
    garderPosition(v, t);
    if (!boite) {
      boite = document.createElement("div");
      boite.id = "recitation-lecteur"; boite.className = "rec-boite";
      boite.innerHTML = `<div class="rec-barre"><span class="rec-titre"></span><a class="rec-chaine" href="${CHAINE}" target="_blank" rel="noopener"></a>
        <button type="button" class="rec-fermer">×</button></div><div class="rec-video"></div>`;
      document.body.appendChild(boite);
      boite.querySelector(".rec-fermer").addEventListener("click", () => arreter(true));
    }
    const zone = boite.querySelector(".rec-video");
    zone.innerHTML = "";
    iframe = document.createElement("iframe");
    iframe.src = adresse(v, t);
    iframe.title = L2("Récitation du Coran par cheikh Ali El Barrak", "تلاوة القرآن الكريم بصوت الشيخ علي البراق", "Quran recitation by Sheikh Ali El Barrak");
    iframe.setAttribute("allow", "autoplay; encrypted-media; picture-in-picture");
    iframe.setAttribute("allowfullscreen", "");
    iframe.setAttribute("referrerpolicy", "strict-origin-when-cross-origin");
    iframe.addEventListener("load", () => { try { iframe.contentWindow.postMessage(JSON.stringify({ event: "listening", id: "recitation", channel: "widget" }), ORIGINE_YT); } catch (e) {} });
    zone.appendChild(iframe);
    boite.hidden = false;
    enCours = true;
    textesBoite(); bouton();
    document.dispatchEvent(new Event("recitation"));
  }

  function arreter(retenir) {
    if (iframe) { try { iframe.contentWindow.postMessage(JSON.stringify({ event: "command", func: "pauseVideo", args: [] }), ORIGINE_YT); } catch (e) {} }
    if (boite) { boite.querySelector(".rec-video").innerHTML = ""; boite.hidden = true; }
    iframe = null; enCours = false;
    if (retenir) ecrire(CLE, "non");
    bouton();
    document.dispatchEvent(new Event("recitation"));
  }

  // position de lecture envoyée par le lecteur YouTube (messages « infoDelivery ») : reprise sur la page suivante
  window.addEventListener("message", e => {
    if (e.origin !== ORIGINE_YT || typeof e.data !== "string") return;
    try {
      const d = JSON.parse(e.data), info = d && d.info;
      if (info && typeof info.currentTime === "number") garderPosition(position().v, info.currentTime);
    } catch (x) {}
  });

  // bouton rond de l'en-tête (ajouté à chaque dessin de l'en-tête par page.js)
  function bouton() {
    const zone = document.querySelector(".entete-boutons");
    if (!zone) return;
    let b = zone.querySelector(".rec-bouton");
    if (!b) {
      b = document.createElement("button");
      b.type = "button"; b.className = "rec-bouton";
      b.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 18V6l10-2v12"/><circle cx="6.5" cy="18" r="2.5"/><circle cx="16.5" cy="16" r="2.5"/></svg>';
      b.addEventListener("click", () => { if (enCours) arreter(true); else { ecrire(CLE, "oui"); lancer(); } });
      zone.insertBefore(b, zone.firstChild);
    }
    b.setAttribute("aria-pressed", String(enCours));
    const t = enCours ? L2("Arrêter la récitation", "أوقف التلاوة", "Stop the recitation") : L2("Écouter la récitation de cheikh Ali El Barrak", "استمع إلى تلاوة الشيخ علي البراق", "Listen to Sheikh Ali El Barrak's recitation");
    b.setAttribute("aria-label", t); b.title = t;
  }

  // écran d'entrée (première visite seulement)
  function ecran() {
    const e = document.createElement("div");
    e.id = "entree"; e.className = "entree"; e.setAttribute("role", "dialog"); e.setAttribute("aria-modal", "true"); e.setAttribute("aria-labelledby", "entree-titre");
    const racine = document.documentElement.dataset.racine || "";
    e.innerHTML = `<div class="entree-boite">
      <img class="entree-logo" src="${racine}assets/logo.svg" alt="" width="72" height="72">
      <p class="entree-ar" lang="ar" dir="rtl">مساجد تونس</p>
      <h2 id="entree-titre">${L2("Mosquées en Tunisie", "مساجد تونس", "Mosques in Tunisia")}</h2>
      <p class="entree-sous">${L2("La carte de toutes les mosquées du pays et l'histoire de ses grandes mosquées.", "خريطة كل مساجد البلاد وتاريخ جوامعها الكبرى.", "The map of every mosque in the country and the history of its great mosques.")}</p>
      <button type="button" class="entree-son" id="entree-son"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>${L2("Entrer avec la récitation de cheikh Ali El Barrak", "الدخول مع تلاوة الشيخ علي البراق", "Enter with the recitation of Sheikh Ali El Barrak")}</button>
      <button type="button" class="entree-silence" id="entree-silence">${L2("Entrer sans le son", "الدخول دون صوت", "Enter without sound")}</button>
      <p class="entree-credit">${L2("Récitation : cheikh Ali El Barrak (1899-1981), chaîne officielle", "التلاوة: الشيخ علي البراق (1899-1981)، القناة الرسمية", "Recitation: Sheikh Ali El Barrak (1899-1981), official channel")}</p>
    </div>`;
    document.body.appendChild(e);
    document.documentElement.classList.add("entree-ouverte");
    const fermer = son => {
      ecrire(CLE, son ? "oui" : "non");
      e.remove(); document.documentElement.classList.remove("entree-ouverte");
      if (son) lancer();
      try { if (window.goatcounter && window.goatcounter.count) window.goatcounter.count({ path: son ? "entree-avec-recitation" : "entree-sans-son", title: "Écran d'entrée", event: true }); } catch (x) {}
    };
    e.querySelector("#entree-son").addEventListener("click", () => fermer(true));
    e.querySelector("#entree-silence").addEventListener("click", () => fermer(false));
    e.addEventListener("keydown", k => { if (k.key === "Escape") fermer(false); });
    setTimeout(() => { const b = e.querySelector("#entree-son"); if (b) b.focus(); }, 30);
  }
  window.RECITATION = { lancer, arreter, ecran, enCours: () => enCours };

  // boutons « choisir une récitation » de l'accueil
  document.addEventListener("click", e => {
    const b = e.target.closest && e.target.closest("[data-video]");
    if (!b) return;
    ecrire(CLE, "oui"); lancer(b.dataset.video, 0);
  });
  document.addEventListener("recitation", () => {
    const p = position();
    document.querySelectorAll("[data-video]").forEach(b => b.setAttribute("aria-pressed", String(enCours && b.dataset.video === p.v)));
  });

  // page video/ (décision d'Ahmed, 09/10/2026) : la vidéo de présentation n'a PAS de son ; la récitation (Al-Fâtiha, chaîne
  // officielle) démarre avec la vidéo et s'arrête avec elle. Pas d'écran d'entrée sur cette page (le bouton « lecture » suffit).
  const FATIHA = "ygnfUhIY09w";
  function brancherVideo(v) {
    const ligne = document.createElement("p");
    ligne.className = "video-recitation";
    const ecrireLigne = () => { ligne.textContent = L2("Avec la voix de cheikh Ali El Barrak (sourate Al-Fâtiha), depuis sa chaîne officielle.", "بصوت الشيخ علي البراق (سورة الفاتحة)، من قناته الرسمية.", "With the voice of Sheikh Ali El Barrak (Surah Al-Fatiha), from his official channel."); };
    ecrireLigne(); document.addEventListener("langue", ecrireLigne);
    v.insertAdjacentElement("afterend", ligne);
    v.addEventListener("play", () => lancer(FATIHA, v.currentTime < 1 ? 0 : v.currentTime));
    v.addEventListener("pause", () => { if (enCours) arreter(false); });
  }
  window.RECITATION.brancherVideo = brancherVideo;

  document.addEventListener("langue", () => { bouton(); textesBoite(); });
  document.addEventListener("DOMContentLoaded", () => {
    setTimeout(() => {
      bouton();
      const v = document.querySelector("video.video-lecteur");
      if (v) { brancherVideo(v); return; }                                      // page vidéo : récitation jouée avec la vidéo
      if (new URLSearchParams(location.search).get("son") === "0") return;     // lien sans écran d'entrée (captures, partage)
      const c = choix();
      if (c === null) ecran();
      else if (c === "oui") lancer();
    }, 0);
  });
})();
