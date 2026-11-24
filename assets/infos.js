/* Prière du vendredi et lectures du Coran (24/11/2026, demande d'Ahmed) : affichage dans la bulle de la carte et sur la fiche
   de chaque mosquée, formulaire « Indiquer ou corriger », votes « C'est vrai » / « N'est plus vrai ».
   Données : window.MOSQUEES_SIGNALES.infos (donnees/signales.js, publié toutes les 2 h par tools/lieux_priere.py) :
     { id du lieu: { clé: [valeur, statut, confirmations, lien de la source] } }
   clés : joumoua (13h00 | asr | HH:MM | non), coran-jour (fajr | dhohr | asr | maghreb | icha | non),
          coran-mois (lun … dim, avec -premier / -dernier | non),
          coran-date (AAAA-MM-JJ : khatma à une date précise, 24/11/2026 ; une date passée n'est plus affichée).
   Envoi : même Google Forms que les signalements, format LIEU-PRIERE-INFO (-OK / -KO), marque « id|clé|valeur », lieu « |jeton ».
   Valeurs choisies dans une liste : aucun texte libre, aucune donnée personnelle ; aucune heure n'est inventée. */
(function () {
  const FORM = "https://docs.google.com/forms/d/e/1FAIpQLSd7sR4KmzqrCi-Yjw0WV9SmT_3sZfKJtPmkGnDjMRHl4Q78PA/formResponse";
  const CH = { marque: "entry.897098257", format: "entry.1939823394", lieu: "entry.506707149", date: "entry.1622032670" };
  const L2 = (fr, ar, en) => (window.T ? window.T(fr, ar, en) : fr);
  const esc = s => String(s || "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const lire = k => { try { return localStorage.getItem(k); } catch (e) { return null; } };
  const ecrire = (k, v) => { try { localStorage.setItem(k, v); } catch (e) {} };
  let jeton = lire("lieu-priere-jeton");
  if (!/^lp:[a-z0-9]{6,40}$/.test(jeton || "")) { jeton = "lp:" + Math.random().toString(36).slice(2) + Date.now().toString(36); ecrire("lieu-priere-jeton", jeton); }

  // couleurs des points de la carte en mode « Vendredi » (le texte de la légende reste en couleurs du thème)
  const COULEURS = { "13h00": "#7B3FA0", asr: "#C2410C", autre: "#0F766E" };
  const JOURS = ["lun", "mar", "mer", "jeu", "ven", "sam", "dim"];
  const PRIERES = {
    fajr: () => L2("Fajr", "الفجر", "Fajr"), dhohr: () => L2("Dhohr", "الظهر", "Dhuhr"), asr: () => L2("Asr", "العصر", "Asr"),
    maghreb: () => L2("Maghreb", "المغرب", "Maghrib"), icha: () => L2("Icha", "العشاء", "Isha")
  };
  const infos = () => ((window.MOSQUEES_SIGNALES || {}).infos || {});
  // khatma à une date précise : AAAA-MM-JJ, affichée tant qu'elle n'est pas passée (jour même compris)
  const aujourdhui = () => { const d = new Date(); return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10); };
  const dansDeuxAns = () => { const d = new Date(); d.setFullYear(d.getFullYear() + 2); return d.toISOString().slice(0, 10); };
  const aVenir = v => /^\d{4}-\d{2}-\d{2}$/.test(v || "") && v >= aujourdhui();
  function dateLongue(v) {
    try { return new Date(v + "T12:00:00Z").toLocaleDateString(document.documentElement.lang || "fr", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" }); } catch (e) { return v; }
  }
  // nom du jour dans la langue de la page (Intl) : lundi 23/11/2026 = 1er jour de la liste
  function jour(k) {
    const i = JOURS.indexOf(k), lg = document.documentElement.lang || "fr";
    try { return new Date(Date.UTC(2026, 10, 23 + i)).toLocaleDateString(lg, { weekday: "long", timeZone: "UTC" }); } catch (e) { return k; }
  }
  function mois(v, j) {
    const [k, rang] = v.split("-"), n = j || jour(k);
    if (rang === "premier") return L2("le premier {j} du mois", "أول يوم {j} من الشهر", "the first {j} of the month").replace("{j}", n);
    if (rang === "dernier") return L2("le dernier {j} du mois", "آخر يوم {j} من الشهر", "the last {j} of the month").replace("{j}", n);
    return L2("un {j} par mois", "يوم {j} مرة في الشهر", "one {j} a month").replace("{j}", n);
  }
  function libelle(cle, v) {
    if (cle === "joumoua") return v === "13h00" ? "13:00" : v === "asr" ? L2("juste avant l'Asr", "قبيل صلاة العصر", "just before Asr")
      : v === "non" ? L2("pas de prière du vendredi ici", "لا تُقام صلاة الجمعة هنا", "no Friday prayer here") : v;
    if (cle === "coran-jour") return v === "non" ? L2("pas de lecture quotidienne", "لا توجد قراءة يومية", "no daily recitation")
      : L2("chaque jour, après la prière : {p}", "كل يوم بعد صلاة {p}", "every day, after the prayer: {p}").replace("{p}", PRIERES[v] ? PRIERES[v]() : v);
    if (cle === "coran-date") return L2("khatma du Coran le {d}", "ختم القرآن يوم {d}", "Quran khatma on {d}").replace("{d}", dateLongue(v));
    if (cle === "coran-mois") return v === "non" ? L2("pas de khatma mensuelle", "لا يوجد ختم شهري", "no monthly khatma")
      : L2("khatma du Coran", "ختم القرآن", "Quran khatma (complete reading)") + " : " + mois(v);
    return v;
  }
  // catégorie de l'heure du vendredi pour le filtre et la couleur : 13h00, asr, autre (une heure HH:MM), sinon null
  function vendredi(id) {
    const x = (infos()[id] || {}).joumoua;
    if (!x || x[0] === "non") return null;
    return x[0] === "13h00" || x[0] === "asr" ? x[0] : "autre";
  }
  const coran = id => ["coran-jour", "coran-mois", "coran-date"].some(k => { const v = ((infos()[id] || {})[k] || [])[0]; return v && v !== "non" && (k !== "coran-date" || aVenir(v)); });

  function statut(x) {
    if (x[1] === "confirme") return L2("Confirmé par les visiteurs", "أكّده الزوار", "Confirmed by visitors");
    if (x[1] === "source") return `<a href="${esc(x[3])}" target="_blank" rel="noopener">${L2("Source", "المصدر", "Source")}</a>`;
    return L2("Signalé par un visiteur, à confirmer", "أضافه زائر، في انتظار التأكيد", "Reported by a visitor, to be confirmed");
  }
  function ligne(id, cle, x) {
    const m = esc(id + "|" + cle + "|" + x[0]);
    return `<span class="mq-info-val"><b>${esc(libelle(cle, x[0]))}</b> <small>(${statut(x)})</small>
      <span class="mq-voix mq-voix-info"><button type="button" data-iok="${m}">✓ ${L2("C'est vrai", "صحيح", "It's true")}</button><button type="button" data-iko="${m}">✗ ${L2("N'est plus vrai", "لم يعد صحيحًا", "No longer true")}</button></span></span>`;
  }
  function html(id) {
    const d = infos()[id] || {};
    const vide = `<span class="mq-info-vide">${L2("pas encore d'information — indiquez-la", "لا توجد معلومة بعد — أضِفها", "no information yet — add it")}</span>`;
    const c = ["coran-jour", "coran-mois", "coran-date"].filter(k => d[k] && (k !== "coran-date" || aVenir(d[k][0])));
    return `<div class="mq-infos" data-infos="${esc(id)}">
      <p><b>${L2("Prière du vendredi", "صلاة الجمعة", "Friday prayer")} :</b> ${d.joumoua ? ligne(id, "joumoua", d.joumoua) : `<span class="mq-info-vide">${L2("heure inconnue — indiquez-la", "الوقت غير معروف — أضِفه", "time unknown — add it")}</span>`}</p>
      <p><b>${L2("Lecture du Coran", "قراءة القرآن", "Quran recitation")} :</b> ${c.length ? c.map(k => ligne(id, k, d[k])).join(" ") : vide}</p>
      <button type="button" class="chipbtn mq-info-ouvrir" data-info-ouvrir="${esc(id)}">${L2("Indiquer ou corriger", "أضِف أو صحّح", "Add or correct")}</button></div>`;
  }
  function formulaire(id) {
    const o = (v, t) => `<option value="${esc(v)}">${esc(t)}</option>`, rien = o("", L2("— ne rien changer —", "— بدون تغيير —", "— no change —"));
    const modele = v => mois(v, "…");
    return `<form class="mq-info-form" data-info-form="${esc(id)}">
      <label>${L2("Heure de la prière du vendredi", "وقت صلاة الجمعة", "Friday prayer time")}
        <select name="joumoua">${rien}${o("13h00", "13:00")}${o("asr", libelle("joumoua", "asr"))}${o("autre", L2("Autre heure", "وقت آخر", "Other time"))}${o("non", libelle("joumoua", "non"))}</select></label>
      <input name="heure" type="time" min="11:00" max="16:30" step="300" hidden aria-label="${esc(L2("Autre heure", "وقت آخر", "Other time"))}">
      <label>${L2("Lecture du Coran chaque jour, après la prière", "قراءة القرآن كل يوم بعد صلاة", "Daily Quran recitation, after the prayer")}
        <select name="coran-jour">${rien}${Object.keys(PRIERES).map(k => o(k, PRIERES[k]())).join("")}${o("non", libelle("coran-jour", "non"))}</select></label>
      <label>${L2("Khatma du Coran une fois par mois", "ختم القرآن مرة في الشهر", "Quran khatma once a month")}
        <select name="coran-mois">${rien}${JOURS.map(k => o(k, jour(k))).join("")}${o("non", libelle("coran-mois", "non"))}</select>
        <select name="rang">${o("", modele("x"))}${o("premier", modele("x-premier"))}${o("dernier", modele("x-dernier"))}</select></label>
      <label>${L2("Khatma du Coran à une date précise", "ختم القرآن في تاريخ محدّد", "Quran khatma on a specific date")}
        <input name="coran-date" type="date" min="${aujourdhui()}" max="${dansDeuxAns()}"></label>
      <button type="submit" class="btn-principal">${L2("Envoyer", "إرسال", "Send")}</button> <small class="mq-info-etat" role="status"></small></form>`;
  }

  function envoyer(format, marque) {
    const corps = new URLSearchParams();
    corps.append(CH.format, format); corps.append(CH.marque, marque); corps.append(CH.lieu, "|" + jeton);
    corps.append(CH.date, new Date().toISOString().slice(0, 10));
    if (window.__envois) { window.__envois.push(Object.fromEntries(corps)); return Promise.resolve(); }   // tests
    return fetch(FORM, { method: "POST", mode: "no-cors", body: corps });
  }
  const merci = () => `<small>${L2("Merci ! Pris en compte dans 2 heures environ.", "شكرًا! يُحتسب خلال ساعتين تقريبًا.", "Thank you! Counted within about 2 hours.")}</small>`;

  document.addEventListener("click", e => {
    const ouvrir = e.target.closest("[data-info-ouvrir]");
    if (ouvrir) { ouvrir.insertAdjacentHTML("afterend", formulaire(ouvrir.dataset.infoOuvrir)); ouvrir.remove(); return; }
    const v = e.target.closest("[data-iok],[data-iko]");
    if (v) {
      const ok = v.hasAttribute("data-iok");
      envoyer(ok ? "LIEU-PRIERE-INFO-OK" : "LIEU-PRIERE-INFO-KO", ok ? v.dataset.iok : v.dataset.iko).then(() => { v.parentNode.innerHTML = merci(); }, () => {});
    }
  });
  document.addEventListener("change", e => {
    const s = e.target.closest(".mq-info-form [name=joumoua]");
    if (s) s.closest("form").querySelector("[name=heure]").hidden = s.value !== "autre";
  });
  document.addEventListener("submit", e => {
    const f = e.target.closest("[data-info-form]");
    if (!f) return;
    e.preventDefault();
    const id = f.dataset.infoForm, etat = f.querySelector(".mq-info-etat"), envois = [], val = n => f.querySelector(`[name="${n}"]`).value;
    let j = val("joumoua");
    if (j === "autre") j = /^(1[1-6]):([0-5][05])$/.test(val("heure")) ? val("heure") : "";
    if (j) envois.push(["joumoua", j]);
    if (val("coran-jour")) envois.push(["coran-jour", val("coran-jour")]);
    const m = val("coran-mois");
    if (m) envois.push(["coran-mois", m === "non" || !val("rang") ? m : m + "-" + val("rang")]);
    const dt = val("coran-date");
    if (dt && aVenir(dt) && dt <= dansDeuxAns()) envois.push(["coran-date", dt]);
    if (!envois.length) { etat.textContent = L2("Choisissez au moins une information.", "اختر معلومة واحدة على الأقل.", "Choose at least one item."); return; }
    Promise.all(envois.map(([k, val]) => envoyer("LIEU-PRIERE-INFO", id + "|" + k + "|" + val))).then(() => { f.outerHTML = merci(); }, () => {});
  });

  // fiche d'une mosquée : bloc « Prière du vendredi et lecture du Coran » (données chargées seulement ici, petit fichier)
  function fiche() {
    const box = document.getElementById("mq-infos");
    if (!box || !box.dataset.lieu) return;
    const dessiner = () => { box.innerHTML = html(box.dataset.lieu); };
    if (window.MOSQUEES_SIGNALES) return dessiner();
    const moi = document.querySelector('script[src*="assets/infos.js"]'), v = moi ? (moi.src.split("?")[1] || "") : "";
    const s = document.createElement("script");
    s.src = (document.documentElement.dataset.racine || "") + "donnees/signales.js" + (v ? "?" + v : "");
    s.onload = dessiner; document.body.appendChild(s);
  }
  window.MQ_INFOS = { html, libelle, vendredi, coran, COULEURS, fiche };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", fiche); else fiche();
  document.addEventListener("langue", () => { const b = document.getElementById("mq-infos"); if (b && window.MOSQUEES_SIGNALES) b.innerHTML = html(b.dataset.lieu); });
})();
