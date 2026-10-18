#!/usr/bin/env python3
"""Génère les icônes Android (ballon de foot) dans ./android-icons/ — à relancer
seulement si on veut changer le dessin ; le CI se contente de copier le résultat."""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

GREEN = (20, 128, 60)        # pelouse
GREEN_DARK = (13, 92, 42)
INK = (24, 24, 28)

def pent(cx, cy, r, rot_deg):
    return [(cx + r*math.cos(math.radians(rot_deg + 72*i)),
             cy + r*math.sin(math.radians(rot_deg + 72*i))) for i in range(5)]

def ball(S):
    """Dessine un ballon centré dans un carré S×S (fond transparent), rayon S/2."""
    SS = 4                      # sur-échantillonnage
    N = S*SS
    R = N/2
    c = N/2
    # --- fond blanc avec léger dégradé sphérique
    yy, xx = np.mgrid[0:N, 0:N]
    dx = (xx - (c - 0.18*R))/R
    dy = (yy - (c - 0.22*R))/R
    d = np.clip(np.sqrt(dx*dx + dy*dy)/1.35, 0, 1)
    shade = 255 - (d**2.2)*70
    rgb = np.stack([shade, shade, shade+2], axis=-1).clip(0, 255).astype(np.uint8)
    art = Image.fromarray(rgb, 'RGB')
    dr = ImageDraw.Draw(art)

    lw = max(2, int(0.045*R))
    a = 0.34*R                  # rayon du pentagone central
    b = 0.62*R                  # fin des coutures partant du centre
    dd = 0.34*R                 # rayon des pentagones du bord
    # pentagone central
    center = pent(c, c, a, -90)
    # coutures + pentagones du bord
    rim = []
    for k in range(5):
        ang = math.radians(-90 + 72*k)
        vx, vy = c + a*math.cos(ang), c + a*math.sin(ang)
        ex, ey = c + b*math.cos(ang), c + b*math.sin(ang)
        dr.line([(vx, vy), (ex, ey)], fill=INK, width=lw)
        pc = (c + (b+dd)*math.cos(ang), c + (b+dd)*math.sin(ang))
        poly = pent(pc[0], pc[1], dd, -90 + 72*k + 180)   # sommet vers le centre
        rim.append(poly)
    for poly in rim:
        dr.polygon(poly, fill=INK)
    dr.polygon(center, fill=INK)
    # --- masque circulaire + contour
    mask = Image.new('L', (N, N), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, N-1, N-1], fill=255)
    out = Image.new('RGBA', (N, N), (0, 0, 0, 0))
    out.paste(art, (0, 0), mask)
    ring = Image.new('RGBA', (N, N), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    rw = max(2, int(0.05*R))
    rd.ellipse([rw/2, rw/2, N-1-rw/2, N-1-rw/2], outline=INK + (255,), width=rw)
    out = Image.alpha_composite(out, ring)
    return out.resize((S, S), Image.LANCZOS)

def compose(size, ball_frac, shape):
    """Icône complète (fond + ballon). shape: 'none' (foreground transparent),
    'square' (coins arrondis), 'round', 'full' (fond plein, sans masque)."""
    SS = 4
    N = size*SS
    img = Image.new('RGBA', (N, N), (0, 0, 0, 0))
    if shape != 'none':
        bg = Image.new('RGBA', (N, N), GREEN + (255,))
        # bandes de tonte
        bd = ImageDraw.Draw(bg)
        stripes = 6
        for i in range(0, stripes, 2):
            bd.rectangle([i*N/stripes, 0, (i+1)*N/stripes, N], fill=GREEN_DARK + (255,))
        m = Image.new('L', (N, N), 0)
        md = ImageDraw.Draw(m)
        if shape == 'round':
            md.ellipse([0, 0, N-1, N-1], fill=255)
        elif shape == 'square':
            md.rounded_rectangle([0, 0, N-1, N-1], radius=int(N*0.22), fill=255)
        else:
            md.rectangle([0, 0, N, N], fill=255)
        img.paste(bg, (0, 0), m)
    bs = int(N*ball_frac)
    # ombre douce sous le ballon
    sh = Image.new('RGBA', (N, N), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([(N-bs)/2 + bs*0.04, (N-bs)/2 + bs*0.10, (N+bs)/2 + bs*0.04, (N+bs)/2 + bs*0.10], fill=(0, 0, 0, 90))
    sh = sh.filter(ImageFilter.GaussianBlur(N*0.012))
    img = Image.alpha_composite(img, sh)
    bl = ball(bs//SS*SS)  # multiple de SS
    img.alpha_composite(bl, ((N - bl.width)//2, (N - bl.height)//2))
    return img.resize((size, size), Image.LANCZOS)

SPLASH_BG = (10, 32, 19)   # #0A2013, même vert foncé que la page de l'appli

def splash(w, h):
    """Écran de démarrage : fond vert foncé uni + ballon centré."""
    img = Image.new('RGBA', (w, h), SPLASH_BG + (255,))
    d = int(min(w, h)*0.30)
    b = compose(d, 1.0, 'none')
    img.alpha_composite(b, ((w - d)//2, (h - d)//2))
    return img.convert('RGB')

SPLASH_SIZES = {
    'drawable': (480, 320),
    'drawable-land-mdpi': (480, 320), 'drawable-land-hdpi': (800, 480), 'drawable-land-xhdpi': (1280, 720),
    'drawable-land-xxhdpi': (1600, 960), 'drawable-land-xxxhdpi': (1920, 1280),
    'drawable-port-mdpi': (320, 480), 'drawable-port-hdpi': (480, 800), 'drawable-port-xhdpi': (720, 1280),
    'drawable-port-xxhdpi': (960, 1600), 'drawable-port-xxxhdpi': (1280, 1920),
}

DENS = {'mdpi': 1, 'hdpi': 1.5, 'xhdpi': 2, 'xxhdpi': 3, 'xxxhdpi': 4}

def main(outdir):
    for d, f in DENS.items():
        folder = os.path.join(outdir, f'mipmap-{d}')
        os.makedirs(folder, exist_ok=True)
        legacy = int(48*f)
        fg = int(108*f)
        compose(legacy, 0.74, 'square').save(os.path.join(folder, 'ic_launcher.png'))
        compose(legacy, 0.74, 'round').save(os.path.join(folder, 'ic_launcher_round.png'))
        # zone de sécurité adaptative = disque de 66 % ; le ballon en occupe 58 %
        compose(fg, 0.58, 'none').save(os.path.join(folder, 'ic_launcher_foreground.png'))
    vdir = os.path.join(outdir, 'values')
    os.makedirs(vdir, exist_ok=True)
    open(os.path.join(vdir, 'ic_launcher_background.xml'), 'w').write(
        '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
        '    <color name="ic_launcher_background">#14803C</color>\n</resources>\n')
    open(os.path.join(vdir, 'splash_background.xml'), 'w').write(
        '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
        '    <color name="splash_background">#0A2013</color>\n</resources>\n')
    for folder, (w, h) in SPLASH_SIZES.items():
        os.makedirs(os.path.join(outdir, folder), exist_ok=True)
        splash(w, h).save(os.path.join(outdir, folder, 'splash.png'), optimize=True)
    # icônes de la version web (PWA) : mêmes visuels
    pwa = os.environ.get('PWA_ICONS_DIR')
    if pwa:
        os.makedirs(pwa, exist_ok=True)
        compose(192, 0.74, 'square').save(os.path.join(pwa, 'icon-192.png'), optimize=True)
        compose(512, 0.74, 'square').save(os.path.join(pwa, 'icon-512.png'), optimize=True)
        compose(512, 0.56, 'full').save(os.path.join(pwa, 'icon-maskable-512.png'), optimize=True)
    # aperçus
    compose(512, 0.74, 'square').save(os.path.join(outdir, 'preview-512.png'))

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'android-icons')
