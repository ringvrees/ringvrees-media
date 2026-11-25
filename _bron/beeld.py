"""Vaste Ringvrees-beeldbehandeling: rustige kleur, warme papiertoon, fijne korrel. Maakt WebP in 1600 en 800 breed."""
import json, pathlib, numpy as np
from PIL import Image, ImageEnhance
ROOT = pathlib.Path(__file__).resolve().parent.parent
UIT = ROOT / "img" / "artikelen" / "v"

def behandel(im):
    im = im.convert("RGB")
    im = ImageEnhance.Color(im).enhance(0.74)
    im = ImageEnhance.Contrast(im).enhance(1.07)
    a = np.asarray(im).astype(np.float32) / 255
    papier = np.array([242, 232, 214], np.float32) / 255
    a = a * 0.82 + (a * papier) * 0.18 + 0.03            # warme toon en iets opgetilde zwarten
    a = 18/255 + a * (1 - 26/255)
    rng = np.random.default_rng(7)
    a += rng.normal(0, 0.016, a.shape[:2])[..., None]    # monochrome korrel
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))

def maak(slug, foto=True):
    bron = ROOT / "img" / "artikelen" / f"{slug}.jpg"
    if not bron.exists(): return False
    UIT.mkdir(parents=True, exist_ok=True)
    doel = UIT / f"{slug}-1600.webp"
    if doel.exists() and doel.stat().st_mtime > bron.stat().st_mtime: return True
    im = Image.open(bron)
    im = behandel(im) if foto else im.convert("RGB")
    for w in (1600, 800):
        k = im if im.width <= w else im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        k.save(UIT / f"{slug}-{w}.webp", "WEBP", quality=78, method=6)
    return True
