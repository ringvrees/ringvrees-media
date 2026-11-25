"""Deelbeeld per artikel (1200x630) in Ringvrees-stijl A: papier met kop links, foto rechts.
Wordt bij het bouwen gemaakt als het nog niet bestaat of als het artikel is gewijzigd. Gebruikt Playwright met Chrome."""
import html, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
UIT = ROOT / "img" / "deel"
F = ROOT / "fonts"

def _html(a):
    v = ROOT / "img" / "artikelen" / "v" / f"{a['slug']}-1600.webp"
    foto = v if v.exists() else ROOT / a["beeld"].lstrip("/")
    e = html.escape
    import re
    zinnen = [z.strip() for z in re.split(r"(?<=[.!?])\s+", a.get("lede", "").strip()) if z.strip()]
    zin = a.get("deelzin") or (zinnen[-1] if zinnen else a["titel"])
    if len(zin) > 170 or len(zin) < 25:
        zin = a["titel"]
    passend = "" if a.get("beeld_bron", "").startswith("Foto") else ";object-fit:contain;transform:scale(1.3);transform-origin:60% 50%;background:#F2ECE1"
    return f"""<html><head><meta charset=utf-8><style>
@font-face{{font-family:DMS;src:url({(F/'dm-serif-display-latin-400-normal.woff2').as_uri()})}}
@font-face{{font-family:Int;font-weight:900;src:url({(F/'inter-latin-900-normal.woff2').as_uri()})}}
@font-face{{font-family:Int;font-weight:600;src:url({(F/'inter-latin-600-normal.woff2').as_uri()})}}
*{{margin:0;padding:0;box-sizing:border-box}}body{{width:1200px;height:630px;overflow:hidden;background:#F2ECE1}}
.foto{{position:absolute;right:0;top:0;width:560px;height:630px;object-fit:cover;object-position:45% 50%}}
.paneel{{position:absolute;left:0;top:0;width:680px;height:630px;background:#F2ECE1;padding:48px 56px;display:flex;flex-direction:column;justify-content:space-between;color:#111012}}
.paneel::after{{content:"";position:absolute;right:-1px;top:0;bottom:0;width:6px;background:#111012}}
.logo{{font:900 22px Int;letter-spacing:.22em}}
.kick{{display:inline-block;background:#E1251B;color:#fff;font:900 18px Int;letter-spacing:.16em;padding:7px 12px;text-transform:uppercase}}
h1{{font:400 50px/1.08 DMS;text-wrap:balance;margin-top:24px}}.voet{{font:600 17px Int;color:#6d665c;letter-spacing:.04em}}
</style></head><body><img class=foto style="{passend}" src="{foto.as_uri()}"><div class=paneel><div class=logo>RINGVREES</div>
<div id=midden><span class=kick>{e(a['rubriek'])}</span><h1 id=kop>{e(zin)}</h1></div>
<div class=voet>ringvrees.nl · Nieuws van binnen de A10</div></div>
<script>var k=document.getElementById('kop'),s=50;document.fonts.ready.then(function(){{while(k.offsetHeight>340&&s>32){{s-=2;k.style.fontSize=s+'px'}}document.body.dataset.klaar=1}});</script></body></html>"""

def maak_alle(alle):
    UIT.mkdir(parents=True, exist_ok=True)
    nodig = []
    for a in alle:
        doel = UIT / f"{a['slug']}.jpg"
        bron = ROOT / "_bron" / "artikelen" / f"{a['slug']}.json"
        if not doel.exists() or (bron.exists() and bron.stat().st_mtime > doel.stat().st_mtime):
            nodig.append(a)
    if not nodig:
        return
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("deelbeeld: playwright ontbreekt, overgeslagen"); return
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--allow-file-access-from-files"])
        pg = b.new_page(viewport={"width": 1200, "height": 630})
        for a in nodig:
            t = UIT / f"_{a['slug']}.html"
            t.write_text(_html(a), encoding="utf-8")
            pg.goto(t.as_uri()); pg.wait_for_selector("body[data-klaar]", timeout=10000)
            pg.screenshot(path=str(UIT / f"{a['slug']}.jpg"), type="jpeg", quality=86)
            t.unlink()
        b.close()

def pad(a):
    return f"/img/deel/{a['slug']}.jpg" if (UIT / f"{a['slug']}.jpg").exists() else None
