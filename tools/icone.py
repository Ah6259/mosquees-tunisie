"""Icône du site « Mosquées en Tunisie » — même famille que les autres sites d'Ahmed : un symbole fort en aplats
2-3 tons + accent doré #F2B33D, sans texte ni brillance. Une mosquée tunisienne : coupole + minaret CARRÉ (style de
Kairouan et de la Zitouna), croissant doré sur la coupole, sol doré.
  python tools/icone.py   → assets/logo.svg, assets/icons/*.png, assets/apple-touch-icon.png, favicon.ico
Rendu avec Chrome sans écran (comme « icones des sites - generateur.py »)."""
import os, subprocess
from PIL import Image

ICI = os.path.dirname(os.path.abspath(__file__)); RACINE = os.path.dirname(ICI)
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
GOLD, GOLD_D = "#F2B33D", "#D9952A"
FOND = ("#16855F", "#08402E")

GLYPHE = f"""
<!-- minaret carré (à droite), avec son lanternon -->
<rect x="318" y="128" width="72" height="292" fill="#FFFFFF"/>
<rect x="354" y="128" width="36" height="292" fill="#D5ECE2"/>
<rect x="330" y="96" width="48" height="40" fill="#FFFFFF"/>
<rect x="354" y="96" width="24" height="40" fill="#D5ECE2"/>
<path d="M330 96 L354 70 L378 96Z" fill="{GOLD}"/>
<path d="M354 70 L378 96 L354 96Z" fill="{GOLD_D}"/>
<rect x="340" y="176" width="28" height="40" rx="14" fill="#0E6B4C"/>
<rect x="340" y="250" width="28" height="40" rx="14" fill="#0E6B4C"/>
<!-- salle de prière et coupole -->
<path d="M150 252a90 90 0 0 1 180 0Z" fill="#FFFFFF"/>
<path d="M240 162a90 90 0 0 1 90 90H240Z" fill="#D5ECE2"/>
<rect x="104" y="252" width="226" height="168" fill="#FFFFFF"/>
<rect x="240" y="252" width="90" height="168" fill="#D5ECE2"/>
<path d="M150 420v-82a24 24 0 0 1 48 0v82Z" fill="#0E6B4C"/>
<path d="M216 420v-96a24 24 0 0 1 48 0v96Z" fill="#0E6B4C"/>
<path d="M282 420v-82a24 24 0 0 1 48 0v82Z" fill="#0E6B4C" transform="translate(-6 0)"/>
<!-- croissant doré sur la coupole -->
<rect x="236" y="136" width="8" height="28" fill="{GOLD}"/>
<path d="M240 104a20 20 0 1 0 14 34a16 16 0 1 1 0-28a20 20 0 0 0-14-6Z" fill="{GOLD}"/>
<!-- sol doré -->
<rect x="84" y="420" width="324" height="20" rx="10" fill="{GOLD}"/>
<rect x="246" y="420" width="162" height="20" rx="10" fill="{GOLD_D}"/>"""


def svg(mode):
    defs = f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{FOND[0]}"/><stop offset="1" stop-color="{FOND[1]}"/></linearGradient>'
    if mode == "rounded":
        corps = f'<rect width="512" height="512" rx="112" fill="url(#bg)"/><g transform="translate(6 -8)">{GLYPHE}</g>'
    else:  # carré plein, symbole réduit dans la zone sûre des icônes adaptatives (Android)
        corps = f'<rect width="512" height="512" fill="url(#bg)"/><g transform="translate(262 252) scale(.74) translate(-256 -256)">{GLYPHE}</g>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><defs>{defs}</defs>{corps}</svg>'


def rendre(texte, png, taille=1024):
    html = os.path.splitext(png)[0] + "_r.html"
    open(html, "w", encoding="utf-8").write('<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;background:transparent;overflow:hidden}svg{width:%dpx;height:%dpx;display:block}</style></head><body>%s</body></html>' % (taille, taille, texte))
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--default-background-color=00000000",
                    f"--window-size={taille},{taille}", f"--screenshot={png}", "file:///" + html.replace("\\", "/")],
                   check=True, capture_output=True, timeout=90)
    os.remove(html)
    Image.open(png).convert("RGBA").crop((0, 0, taille, taille)).save(png)


if __name__ == "__main__":
    a = os.path.join(RACINE, "assets"); ic = os.path.join(a, "icons"); os.makedirs(ic, exist_ok=True)
    open(os.path.join(a, "logo.svg"), "w", encoding="utf-8", newline="\n").write(svg("rounded"))
    tmp = os.path.join(ICI, "_icone")
    os.makedirs(tmp, exist_ok=True)
    r, p = os.path.join(tmp, "r.png"), os.path.join(tmp, "p.png")
    rendre(svg("rounded"), r); rendre(svg("full"), p)
    R, P = Image.open(r), Image.open(p)
    R.resize((192, 192), Image.LANCZOS).save(os.path.join(ic, "icon-192.png"), optimize=True)
    R.resize((512, 512), Image.LANCZOS).save(os.path.join(ic, "icon-512.png"), optimize=True)
    P.resize((512, 512), Image.LANCZOS).save(os.path.join(ic, "icon-maskable-512.png"), optimize=True)
    P.convert("RGB").resize((180, 180), Image.LANCZOS).save(os.path.join(a, "apple-touch-icon.png"), optimize=True)
    R.resize((64, 64), Image.LANCZOS).save(os.path.join(RACINE, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    R.resize((240, 240), Image.LANCZOS).save(os.path.join(tmp, "apercu.png"))
    print("ok", tmp)
