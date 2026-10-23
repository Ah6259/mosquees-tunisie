# -*- coding: utf-8 -*-
"""Mosquées AUTOUR de chaque grande mosquée du monde (3 km), lues une fois sur OpenStreetMap (Overpass) et gardées dans
donnees/monde/autour/<QID>.json : la carte les montre tout de suite, même quand les serveurs Overpass sont saturés
(23/10/2026 : carte vide à La Mecque, Médine et Jérusalem, erreurs 504 et 429 — remarque d'Ahmed). La carte relit ensuite
la zone en direct quand les serveurs répondent. Relancé par le robot trimestriel ; un fichier déjà là et récent n'est pas
redemandé (moins de 80 jours) ; une mosquée dont les serveurs ne répondent pas garde son ancien fichier.
  python tools/monde_autour.py"""
import json, os, sys, time, urllib.parse, urllib.request

ICI = os.path.dirname(os.path.abspath(__file__)); RACINE = os.path.dirname(ICI)
SERVEURS = ["https://overpass-api.de/api/interpreter", "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter", "https://overpass.private.coffee/api/interpreter"]
UA = {"User-Agent": "MosqueesTunisie/1.0 (https://mosquees.clicvia.com/)"}
RAYON = 3000
LANGUES = ["fr", "ar", "en", "tr", "id", "ur", "de", "es", "it", "pt", "nl", "zh", "ja", "ko", "hi", "ru", "vi", "th", "tl", "sv", "ro"]


def lire(lat, lon):
    q = f'[out:json][timeout:40];nwr["amenity"="place_of_worship"]["religion"="muslim"](around:{RAYON},{lat},{lon});out center tags 1500;'
    for essai in range(len(SERVEURS) * 2):
        url = SERVEURS[essai % len(SERVEURS)]
        try:
            req = urllib.request.Request(url, data=urllib.parse.urlencode({"data": q}).encode(), headers=UA)
            d = json.loads(urllib.request.urlopen(req, timeout=70).read())
            if "error" in str(d.get("remark", "")).lower() or "timed out" in str(d.get("remark", "")).lower():
                raise RuntimeError(d["remark"])
            return d.get("elements", [])
        except Exception:
            time.sleep(4 + 3 * essai)
    return None


def court(el):
    t = el.get("tags", {})
    lat = el.get("lat", (el.get("center") or {}).get("lat")); lon = el.get("lon", (el.get("center") or {}).get("lon"))
    if lat is None or lon is None:
        return None
    garde = {k: v[:80] for k, v in t.items() if k in ("name", "amenity", "religion", "place_of_worship", "addr:country") or (k.startswith("name:") and k[5:] in LANGUES)}
    return {"type": el["type"], "id": el["id"], "lat": round(lat, 6), "lon": round(lon, 6), "tags": garde}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ms = json.load(open(os.path.join(RACINE, "donnees", "monde_grandes.json"), encoding="utf-8"))["mosquees"]
    dossier = os.path.join(RACINE, "donnees", "monde", "autour")
    os.makedirs(dossier, exist_ok=True)
    garder, lus, rates = set(), 0, []
    for m in ms:
        if not m.get("pos"):
            continue
        f = os.path.join(dossier, m["q"] + ".json")
        garder.add(m["q"] + ".json")
        if os.path.exists(f) and time.time() - os.path.getmtime(f) < 80 * 86400:
            continue
        els = lire(*m["pos"])
        if els is None:
            rates.append(m["q"]); continue
        sortie = [x for x in (court(e) for e in els) if x]
        open(f, "w", encoding="utf-8", newline="\n").write(json.dumps({"lu": time.strftime("%Y-%m-%d"), "elements": sortie}, ensure_ascii=False, separators=(",", ":")) + "\n")
        lus += 1
        time.sleep(2)
    for n in os.listdir(dossier):
        if n not in garder:
            os.remove(os.path.join(dossier, n))
    print(f"{lus} zones lues, {len(rates)} sans réponse (ancien fichier gardé) : {' '.join(rates[:10])}")


if __name__ == "__main__":
    main()
