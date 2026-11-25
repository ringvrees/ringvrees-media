#!/usr/bin/env python3
"""Bouwt ringvrees.nl uit _bron/artikelen/*.json.

Gebruik (vanuit de root van de gh-pages-branch):  python3 _bron/bouw.py

Elk artikel is één JSON-bestand in _bron/artikelen/ met deze velden:
  slug        url-deel, kleine letters en streepjes (bv. "2026-11-22-poppers-wallen")
  datum       "YYYY-MM-DD"
  tijd        optioneel "HH:MM" (volgorde op dezelfde dag; standaard 17:00)
  type        "nieuws" of "tijdloos"
  rubriek     kort label, bv. "Wallen", "Verkeer", "Cultuur"
  titel       de kop (satirisch, met Amsterdam/onderwerp erin)
  lede        1 à 2 zinnen intro
  beeld       pad naar header-afbeelding 1600x900 (bv. "/img/artikelen/<slug>.jpg"), zonder slide-info
  beeld_alt   korte feitelijke omschrijving van het beeld
  beeld_bron  bij een foto verplicht en beginnend met "Foto:" (dan toont de site hem in kaartjes als zwevende afdruk);
              bij een getekende graphic weglaten. Noem de fotograaf en licentie (bv. "Foto: Naam via Unsplash")
  blokken     lijst van blokken, elk één van:
                {"p": "alinea"}                     (mag <b>, <i>, <a> bevatten)
                {"tussenkop": "tekst"}
                {"citaat": "tekst", "door": "L.B. (34), Lauriergracht"}
                {"getal": "388", "tekst": "uur zaten ..."}
                {"lijst": ["item", ...], "vinkjes": true/false}
                {"tabel": {"kop": ["", "GTA VI", "Amsterdam"], "rijen": [["Bouwtijd","8 jaar","15 jaar"], ...]}}
                {"beeld": "/img/artikelen/x.jpg", "alt": "..."}
  doorstuur   de doorstuur-regel uit de caption (bv. "Stuur door naar ...")
  seo_titel   optioneel, eigen <title> voor Google (max ~60 tekens); anders "<titel> | Ringvrees"
  seo_beschrijving optioneel, eigen meta description (max ~155 tekens); anders de lede
  Interview (fictief, anoniem, als lopende tekst):
              {"interview": {"wie": "L.B. (34)", "waar": "Lauriergracht"}} als kopje,
              daarna gewone p- en tussenkop-blokken met de quotes erdoorheen geweven
  bron        alleen bij eigen onderzoek of exclusief nieuws van één medium (zoals "Via @..." in de caption):
              naam van het medium, bv. "AT5". Toont onderaan "Bron: AT5". Bij algemeen nieuws weglaten.
  bron_url    optioneel, link naar het bronartikel
  bijgewerkt  optioneel "YYYY-MM-DD": bij tijdloze artikelen de datum van de laatste inhoudelijke update
              (de site toont dan "Bijgewerkt op ..."; zonder dit veld geldt de datum)
  instagram   optioneel, url van de Instagram-post
"""
import json, html, pathlib, datetime, re, unicodedata, hashlib
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://ringvrees.nl"
MAANDEN = ["januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus",
           "september", "oktober", "november", "december"]
DAGEN = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"]
IG = "https://www.instagram.com/ringvrees/"
FB = "https://www.facebook.com/Ringvrees"
ORG = {"@type": "NewsMediaOrganization", "name": "Ringvrees", "alternateName": ["@ringvrees", "Ringvrees.nl"],
       "url": "https://ringvrees.nl/", "logo": {"@type": "ImageObject", "url": "https://ringvrees.nl/icon-512.png", "width": 512, "height": 512},
       "description": "Satirisch nieuwsplatform uit Amsterdam. Dagelijks echt Amsterdams nieuws, maar dan zoals het écht voelt binnen de ring A10.",
       "email": "hallo@ringvrees.nl", "areaServed": "Amsterdam", "sameAs": [IG, FB]}


def nl_datum(d, dag=False):
    s = f"{d.day} {MAANDEN[d.month - 1]}"
    return (DAGEN[d.weekday()].capitalize() + " " + s) if dag else s


def rslug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def rubriek_url(r):
    return f"/rubriek/{rslug(r)}/"


def esc(s):
    return html.escape(s, quote=True)


def kop(titel, beschrijving, url, beeld=None, extra=""):
    img = f'\n<meta property="og:image" content="{SITE}{beeld}">\n<meta property="og:image:width" content="1600">\n<meta property="og:image:height" content="900">\n<meta property="og:image:type" content="image/jpeg">' if beeld else f'\n<meta property="og:image" content="{SITE}/icon-512.png">'
    return f"""<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(titel)}</title>
<meta name="description" content="{esc(beschrijving)}">
<link rel="canonical" href="{SITE}{url}">
<meta property="og:title" content="{esc(titel)}">
<meta property="og:description" content="{esc(beschrijving)}">
<meta property="og:site_name" content="Ringvrees">
<meta property="og:type" content="{'article' if url.startswith('/nieuws/') else 'website'}">
<meta property="og:locale" content="nl_NL">
<meta name="twitter:card" content="summary_large_image">
<meta property="og:url" content="{SITE}{url}">{img}
<meta name="theme-color" content="#E1251B">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta name="robots" content="max-image-preview:large">
<link rel="preload" href="/fonts/inter-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/dm-serif-display-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/style.css?v={CSS_V}">
<link rel="alternate" type="application/rss+xml" title="Ringvrees" href="/feed.xml">{extra}
</head>
<body>"""


def balk(vandaag, home=False):
    logo = '<a class="logo" href="/">RINGVREES</a>'
    if home:
        logo = '<h1 style="margin:0;font-size:inherit;font-weight:inherit;line-height:inherit">' + logo + '</h1>'
    return f"""<div class="strip"><div class="wrap"><span>{nl_datum(vandaag, True)}</span><span><button class="sat-knop" type="button" onclick="document.getElementById('verklaring').showModal()"><b>Satire</b></button> · Nieuws van binnen de A10</span></div></div>
<dialog id="verklaring" class="verklaring" onclick="if(event.target===this)this.close()"><div class="vk-in">
  <div class="vk-stempel">Officiële verklaring</div>
  <p class="vk-kop">Alles op Ringvrees is satire.*</p>
  <p class="vk-ster">* Behalve voor wie buiten de A10 woont. Voor hen is dit gewoon hoe het is.</p>
  <p class="vk-uit">Of het voor jou satire is, hangt dus af van je postcode.</p>
  <div class="vk-knoppen"><button type="button" class="vk-ok" onclick="this.closest('.vk-in').classList.add('stap2')">Begrepen</button><a class="vk-check" href="/afstand/">Ik woon buiten de ring →</a></div>
  <div class="vk-voet">Ringvrees · Afdeling Juridische Zaken Binnen de Ring</div>
  <div class="vk-twee">
    <p class="vk-kop">Bedankt voor uw begrip.</p>
    <p class="vk-ster">U ontvangt binnen 6 tot 8 weken een schriftelijke bevestiging. Per bakfiets.</p>
    <p class="vk-uit">Woont u buiten de ring? Dan kan het iets langer duren.</p>
    <div class="vk-afgehandeld">Afgehandeld</div>
    <button type="button" class="vk-ok" onclick="if(location.pathname==='/'){{var d=this.closest('dialog');d.close();d.querySelector('.vk-in').classList.remove('stap2')}}else{{location.href='/'}}">Terug naar het nieuws</button>
  </div>
</div></dialog>
<header class="top"><div class="wrap">
  {logo}
  <nav class="nav"><a class="hide" href="/#nieuws">Nieuws</a><a class="hide" href="/#handboek">Handboek</a><a class="hide" href="/rubrieken/">Rubrieken</a><a class="hide" href="/over/">Over</a><a class="ig" href="/test/">Doe de test →</a>
  <details class="menu"><summary aria-label="Menu"><span></span><span></span><span></span></summary>
   <div class="menu-paneel" onclick="this.parentNode.removeAttribute('open')"><a href="/#nieuws">Nieuws</a><a href="/#handboek">Handboek</a><a href="/rubrieken/">Rubrieken</a><a href="/over/">Over Ringvrees</a><a href="/test/">Heb jij ringvrees? De test</a><a href="/afstand/">Ring-afstandmeter</a><a href="{IG}">Instagram</a><a href="{FB}">Facebook</a></div>
  </details></nav>
</div></header>"""


VOET = """<footer><div class="wrap"><span>Ringvrees is satire. Alles is gebaseerd op echt nieuws, maar dan zoals het écht voelt binnen de A10.</span></div></footer>
<script>(function(){
/* Paaseitje: typ ergens op de site "A10" en de pagina rijdt een rondje over de ring. */
var b="";
document.addEventListener("keydown",function(e){
 var t=e.target;
 if(e.metaKey||e.ctrlKey||e.altKey||(t&&(t.isContentEditable||/^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName))))return;
 b=(b+(e.key&&e.key.length===1?e.key:"")).toLowerCase().slice(-3);
 if(b==="a10"){b="";rond();}
});
function rond(){
 var h=document.documentElement;
 if(h.classList.contains("rond")||document.querySelector(".ring-melding"))return;
 var stil=window.matchMedia&&matchMedia("(prefers-reduced-motion: reduce)").matches;
 if(!stil){document.body.style.transformOrigin="50% "+(window.scrollY+window.innerHeight/2)+"px";h.classList.add("rond");setTimeout(function(){h.classList.remove("rond");document.body.style.transformOrigin="";},1600);}
 setTimeout(melding,stil?0:1500);
}
function melding(){
 var d=document.createElement("div");d.className="ring-melding";d.setAttribute("role","status");
 d.innerHTML='<span class="ring-stempel">Rondje A10</span><b>U heeft de hele ring rondgereden.</b><span>32 kilometer, nul keer de afslag gemist. Gefeliciteerd: u bent nu officieel Amsterdammer.</span>';
 d.onclick=function(){d.remove()};
 document.body.appendChild(d);
 setTimeout(function(){d.classList.add("weg")},5200);setTimeout(function(){d.remove()},5800);
}
})();</script>
</body>
</html>
"""


WEER = """<div class="weer" id="weer" hidden><a class="wrap weer-in" href="/weer/">
  <span class="weer-ic" id="weerIc"></span>
  <div class="weer-kol"><span class="weer-k">Binnen de ring</span><span class="weer-t" id="weerT"></span><span class="weer-c" id="weerC"></span></div>
  <div class="weer-kol weer-uit"><span class="weer-k">Buiten de ring</span><span class="weer-t">—</span><span class="weer-c" id="weerU"></span></div>
  <span class="weer-meer">Komende dagen →</span>
</a></div>
<script>(function(){
var I={zon:'<circle cx="16" cy="16" r="6"/><path d="M16 3v4M16 25v4M3 16h4M25 16h4M6.8 6.8l2.8 2.8M22.4 22.4l2.8 2.8M6.8 25.2l2.8-2.8M22.4 9.6l2.8-2.8"/>',maan:'<path d="M22 20.5A9 9 0 0 1 11.5 8a9.5 9.5 0 1 0 10.5 12.5z"/>',zonwolk:'<circle cx="12" cy="11" r="4.5"/><path d="M12 2.5v2.2M3 11h2.2M5.6 4.6l1.6 1.6M18.4 4.6l-1.6 1.6M5.6 17.4l1.6-1.6"/><path fill="#F3EDE3" d="M12 27h11a4.6 4.6 0 0 0 0-9.2 6.4 6.4 0 0 0-12.3 1.5A3.9 3.9 0 0 0 12 27z"/>',maanwolk:'<path d="M16.5 13A6.5 6.5 0 0 1 8.8 4.2a7 7 0 1 0 7.7 8.8z"/><path fill="#F3EDE3" d="M12 27h11a4.6 4.6 0 0 0 0-9.2 6.4 6.4 0 0 0-12.3 1.5A3.9 3.9 0 0 0 12 27z"/>',wolk:'<path d="M9 24h14a5 5 0 0 0 0-10 7 7 0 0 0-13.5 1.5A4.3 4.3 0 0 0 9 24z"/>',motregen:'<path d="M9 19h14a5 5 0 0 0 0-10 7 7 0 0 0-13.5 1.5A4.3 4.3 0 0 0 9 19z"/><path d="M11.5 23.5l-.6 1.6M16.5 23.5l-.6 1.6M21.5 23.5l-.6 1.6M14 27.5l-.5 1.2M19 27.5l-.5 1.2"/>',regen:'<path d="M9 19h14a5 5 0 0 0 0-10 7 7 0 0 0-13.5 1.5A4.3 4.3 0 0 0 9 19z"/><path d="M11 23l-1.5 4M16 23l-1.5 4M21 23l-1.5 4"/>',bui:'<circle cx="11" cy="9.5" r="4"/><path d="M11 2v2M3.5 9.5h2M5.7 4.2l1.4 1.4M16.3 4.2l-1.4 1.4"/><path fill="#F3EDE3" d="M11 22h12a4.6 4.6 0 0 0 0-9.2 6.4 6.4 0 0 0-12.3 1.5A3.9 3.9 0 0 0 11 22z"/><path d="M13 25l-1.2 3M18 25l-1.2 3M23 25l-1.2 3"/>',mist:'<path d="M5 12h22M8 17h19M5 22h22M9 27h15"/>',sneeuw:'<path d="M9 19h14a5 5 0 0 0 0-10 7 7 0 0 0-13.5 1.5A4.3 4.3 0 0 0 9 19z"/><path d="M11 24v.1M16 26v.1M21 24v.1M13.5 28.5v.1M18.5 28.5v.1"/>',onweer:'<path d="M9 18h14a5 5 0 0 0 0-10 7 7 0 0 0-13.5 1.5A4.3 4.3 0 0 0 9 18z"/><path d="M17 20l-3 5h4l-3 5"/>',wind:'<path d="M4 12h14a3.5 3.5 0 1 0-3.5-3.5M4 17h20a3.5 3.5 0 1 1-3.5 3.5M4 22h9"/>'};
function kies(c,dag,wind){if(wind>=50)return"wind";if(c>=95)return"onweer";if(c>=85)return"sneeuw";if(c>=80)return dag?"bui":"regen";if(c>=71)return"sneeuw";if(c>=61)return"regen";if(c>=51)return"motregen";if(c>=45)return"mist";if(c>=3)return"wolk";if(c>=1)return dag?"zonwolk":"maanwolk";return dag?"zon":"maan";}
var t={0:["Zonnig","zon","Waarschijnlijk ook zon, maar wie gaat dat checken?","Niet gecontroleerd"],1:["Licht bewolkt","wolk","Buiten de ring hebben ze vast ook iets van weer.","Niet relevant"],2:["Half bewolkt","wolk","Buiten de ring hebben ze vast ook iets van weer.","Niet relevant"],3:["Bewolkt","wolk","Buiten de ring schijnt het grijzer te zijn. Zeggen ze.","Niet relevant"],45:["Mist","mist","Buiten de ring zie je nu helemaal niks. Dus niks veranderd.","Niet zichtbaar"],48:["Mist","mist","Buiten de ring zie je nu helemaal niks. Dus niks veranderd.","Niet zichtbaar"],51:["Motregen","regen","Buiten de ring regent het harder. Wij gaan niet kijken.","Niet gemeten"],61:["Regen","regen","Buiten de ring regent het harder. Wij gaan niet kijken.","Niet gemeten"],71:["Sneeuw","sneeuw","Buiten de ring zijn de wegen onbegaanbaar. Ook zonder sneeuw.","Onbegaanbaar"],80:["Buien","regen","Blijf binnen. Binnen de ring, bedoelen we.","Niet gemeten"],95:["Onweer","onweer","Blijf binnen. Binnen de ring, bedoelen we.","Afgeraden"]};
function zoek(c){var k=[95,80,71,61,51,48,45,3,2,1,0];for(var i=0;i<k.length;i++){if(c>=k[i])return t[k[i]];}return t[3];}
fetch("https://api.open-meteo.com/v1/forecast?latitude=52.37&longitude=4.89&current=temperature_2m,weather_code,wind_speed_10m,is_day&timezone=Europe%2FAmsterdam").then(function(r){return r.json()}).then(function(j){var c=j.current,w=zoek(c.weather_code).slice(),zin=w[2];w[1]=kies(c.weather_code,c.is_day,c.wind_speed_10m);if(!c.is_day&&c.weather_code===0)w[0]="Heldere nacht";if(c.wind_speed_10m>=50)w[0]="Harde wind";if(c.wind_speed_10m>38)zin="Harde wind. De pont naar Noord is nu een avontuur.";
document.getElementById("weerIc").innerHTML='<svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'+I[w[1]]+'</svg>';
document.getElementById("weerT").textContent=Math.round(c.temperature_2m)+"°";document.getElementById("weerC").textContent=w[0];document.getElementById("weerU").textContent=w[3];document.getElementById("weer").hidden=false;}).catch(function(){});
})();</script>"""


def band(tekst):
    return f"""<section class="band"><div class="wrap">
  <div class="h">{tekst}</div>
  <a href="{IG}">Volg @ringvrees →</a>
</div></section>"""


def url_van(a):
    return f"/nieuws/{a['slug']}/"


def blok(b):
    if "p" in b:
        return f"<p>{b['p']}</p>"
    if "tussenkop" in b:
        return f"<h2 class='h'>{esc(b['tussenkop'])}</h2>"
    if "citaat" in b:
        door = f"<span class='meta'>{esc(b['door'])}</span>" if b.get("door") else ""
        return f"<blockquote>“{esc(b['citaat'])}”{'<br>' + door if door else ''}</blockquote>"
    if "getal" in b:
        return f"<div class='getal'><span class='h'>{esc(b['getal'])}</span><p>{b['tekst']}</p></div>"
    if "lijst" in b:
        cls = "lijst vink" if b.get("vinkjes") else "lijst"
        return f"<ul class='{cls}'>" + "".join(f"<li>{x}</li>" for x in b["lijst"]) + "</ul>"
    if "tabel" in b:
        t = b["tabel"]
        k = "".join(f"<th>{esc(x)}</th>" for x in t["kop"])
        r = "".join("<tr>" + "".join(f"<td>{esc(x)}</td>" for x in rij) + "</tr>" for rij in t["rijen"])
        return f"<div class='tabelwrap'><table><thead><tr>{k}</tr></thead><tbody>{r}</tbody></table></div>"
    if "interview" in b:
        iv = b["interview"]
        return (f"<div class='iv-kop'><span class='kick'>Interview</span><h2 class='h'>{esc(iv['wie'])}</h2>"
                f"<p class='meta'>{esc(iv.get('waar', ''))}</p>" + (f"<p>{iv['intro']}</p>" if iv.get('intro') else "") + "</div>")
    if "vraag" in b:
        return f"<p class='iv-v'>{esc(b['vraag'])}</p>"
    if "antwoord" in b:
        wie = f"<b>{esc(b['wie'])}:</b> " if b.get("wie") else ""
        return f"<p class='iv-a'>{wie}{b['antwoord']}</p>"
    if "beeld" in b:
        return f"<figure><img src='{b['beeld']}' alt='{esc(b.get('alt', ''))}' loading='lazy'></figure>"
    raise ValueError(f"onbekend blok: {b}")


def kaart(a, groot=False, kort=False):
    d = datetime.date.fromisoformat(a["datum"])
    meta = ("Bijgewerkt " + nl_datum(datetime.date.fromisoformat(a.get("bijgewerkt") or a["datum"])) + " " + (a.get("bijgewerkt") or a["datum"])[:4]) if a["type"] == "tijdloos" else nl_datum(d)
    if groot:
        return f"""<div class="hero">
    <a class="heroimg" href="{url_van(a)}"><img src="{a['beeld']}" alt="{esc(a['beeld_alt'])}" width="1600" height="900" fetchpriority="high"></a>
    <div>
      <a class="kick" href="{rubriek_url(a['rubriek'])}">{esc(a['rubriek'])}</a>
      <a href="{url_van(a)}"><h2 class="h">{esc(a['titel'])}</h2>
      <p>{esc(a['lede'])}</p></a>
      <div class="meta">{meta}</div>
    </div>
  </div>"""
    return f"""<div class="card">
      <a class="beeld{' foto' if a.get('beeld_bron', '').startswith('Foto') else ''}" href="{url_van(a)}"><img src="{a['beeld']}" alt="{esc(a['beeld_alt'])}" width="1600" height="900" loading="lazy" decoding="async"></a>
      <a class="kick" href="{rubriek_url(a['rubriek'])}">{esc(a['rubriek'])}</a>
      <a href="{url_van(a)}"><h3 class="h">{esc(a['titel'])}</h3>
      {'' if kort else '<p>' + esc(a['lede']) + '</p>'}</a>
      <div class="meta">{meta}</div>
    </div>"""


DEF = ('<aside class="def"><b>ringvrees</b> <i>(de; v.)</i> de aanhoudende angst om de Amsterdamse ring A10 te verlaten. '
       'Komt vooral voor bij mensen die alles wat ze nodig hebben op fietsafstand hebben. '
       '<a href="/nieuws/symptomen-van-ringvrees/">Wat is ringvrees? Herken de symptomen →</a></aside>')


def google_titel(titel):
    """Google toont ongeveer 60 tekens. Is de kop te lang, neem dan het deel vóór de dubbele punt of komma."""
    t = f"{titel} | Ringvrees"
    if len(t) <= 62:
        return t
    for teken in (":", ",", " – "):
        deel = titel.split(teken)[0].strip()
        if 20 <= len(deel) and len(deel) + 12 <= 62:
            return f"{deel} | Ringvrees"
    woorden, uit = titel.split(), ""
    for w in woorden:
        if len(uit) + len(w) + 13 > 62:
            break
        uit = (uit + " " + w).strip()
    return f"{uit} | Ringvrees"


def seo_met_merk(t):
    """Eigen seo_titel krijgt ook de merknaam, zoals Google aanraadt (als het binnen ~62 tekens past)."""
    t = t.strip()
    if t.endswith("| Ringvrees") or len(t) + 12 > 62:
        return t
    return f"{t} | Ringvrees"


def artikel_pagina(a, alle, vandaag):
    d = datetime.date.fromisoformat(a["datum"])
    url = url_van(a)
    tijd = a.get("tijd") or "12:00"
    pub = datetime.datetime.fromisoformat(f"{a['datum']}T{tijd}").replace(tzinfo=ZoneInfo("Europe/Amsterdam")).isoformat()
    ld = {"@context": "https://schema.org", "@type": "NewsArticle", "headline": a["titel"][:110],
          "description": a["lede"], "image": [SITE + a["beeld"]], "datePublished": pub, "dateModified": (a.get("bijgewerkt") + "T12:00:00+01:00") if a.get("bijgewerkt") else pub,
          "inLanguage": "nl-NL", "genre": "satire", "articleSection": a["rubriek"], "url": SITE + url,
          "mainEntityOfPage": SITE + url, "isAccessibleForFree": True,
          "contentLocation": {"@type": "Place", "name": "Amsterdam"},
          "author": {"@type": "Organization", "name": "Redactie Ringvrees", "url": SITE + "/over/#redactie"},
          "publisher": ORG}
    kruimel = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Ringvrees", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": a["rubriek"], "item": SITE + rubriek_url(a["rubriek"])},
        {"@type": "ListItem", "position": 3, "name": a["titel"]}]}
    extra = f'\n<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>\n<script type="application/ld+json">{json.dumps(kruimel, ensure_ascii=False)}</script>'
    bron = ""
    if a.get("bron"):
        b = f"<a href='{a['bron_url']}'>{esc(a['bron'])}</a>" if a.get("bron_url") else esc(a["bron"])
        bron = f"<p class='src'>Bron: {b}</p>"
    ig = ""
    meer = [x for x in alle if x["slug"] != a["slug"]][:3]
    meer_html = ""
    if meer:
        meer_html = "<div class='wrap'><div class='sec'><h2 class='h'>Meer van binnen de ring</h2></div><div class='grid'>" + "".join(kaart(x) for x in meer) + "</div></div>"
    beeldbron = f"<figcaption>{esc(a['beeld_bron'])}</figcaption>" if a.get("beeld_bron") else ""
    meta = ("Bijgewerkt op " + nl_datum(datetime.date.fromisoformat(a.get("bijgewerkt") or a["datum"])) + " " + (a.get("bijgewerkt") or a["datum"])[:4]) if a["type"] == "tijdloos" else nl_datum(d, True)
    return (kop(seo_met_merk(a["seo_titel"]) if a.get("seo_titel") else google_titel(a["titel"]), a.get("seo_beschrijving") or a["lede"], url, a["beeld"], extra) + balk(vandaag) + f"""
<article class="art">
  <a class="kick" href="{rubriek_url(a['rubriek'])}">{esc(a['rubriek'])}</a>
  <h1 class="h">{esc(a['titel'])}</h1>
  <p class="lede">{esc(a['lede'])}</p>
  <div class="meta">{meta} · Redactie Ringvrees</div>
</article>
<figure class="kopbeeld"><img src="{a['beeld']}" alt="{esc(a['beeld_alt'])}" width="1600" height="900" fetchpriority="high">{beeldbron}</figure>
<article class="art body">
  {''.join(blok(b) for b in a['blokken'])}
  <div class="share"><b>{esc(a.get('doorstuur', 'Stuur door naar je huisgenoot'))}</b><a href="https://wa.me/?text={esc(a['titel'] + ' ' + SITE + url)}">WhatsApp</a>{ig}</div>
  {bron}
  {DEF if a['slug'] != 'symptomen-van-ringvrees' else ''}
</article>
""" + meer_html + band("Morgen weer vers nieuws van binnen de ring.") + VOET)


def home(alle, vandaag):
    nieuws = [a for a in alle if a["type"] == "nieuws"]
    tijdloos = [a for a in alle if a["type"] == "tijdloos"]
    ld = {"@context": "https://schema.org", "@graph": [dict(ORG, **{"@id": SITE + "/#org"}),
          {"@type": "WebSite", "@id": SITE + "/#site", "name": "Ringvrees", "alternateName": "Ringvrees.nl", "url": SITE + "/",
           "inLanguage": "nl-NL", "publisher": {"@id": SITE + "/#org"},
           "description": "Satirisch nieuws uit Amsterdam, zoals het écht voelt binnen de A10."}]}
    extra = f'\n<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
    delen = [kop("Ringvrees – Satirisch nieuws uit Amsterdam, binnen de A10",
                 "Ringvrees brengt dagelijks satirisch nieuws uit Amsterdam: gebaseerd op echt nieuws, maar dan zoals het écht voelt binnen de ring A10.",
                 "/", None, extra), balk(vandaag, home=True), WEER, "<main class='wrap'>"]
    if nieuws:
        delen.append(kaart(nieuws[0], groot=True))
    if nieuws[1:]:
        delen.append("<div class='alleen-breed'><div class='sec' id='nieuws'><h2 class='h'>Meer nieuws</h2><span class='meta'>Elke dag vers</span></div><div class='grid'>"
                     + "".join(kaart(a, kort=True) for a in nieuws[1:4]) + "</div></div>")
        # mobiel: alles na het hoofdartikel in de lijst; op desktop staan de eerste drie al als kaart
        delen.append(eerder(nieuws[1:], dubbel=3))
    if tijdloos:
        delen.append("<div class='sec' id='handboek'><h2 class='h'>Handboek</h2><span class='meta'>Alles wat je moet weten binnen de A10</span></div><div class='grid'>"
                     + "".join(kaart(a) for a in tijdloos) + "</div>")
    delen.append("</main>")
    delen.append(band("Liever ook nooit de ring uit?<br>Volg het nieuws waar je het al leest."))
    delen.append(VOET)
    return "\n".join(delen)


def eerder(items, dubbel=0):
    """Nieuwsberichten als compacte lijst, per dag een kopje (zoals een nieuwsoverzicht).
    De eerste `dubbel` berichten staan op desktop al als kaart: die regels (en een dagkopje
    met alleen zulke regels) zijn alleen op mobiel zichtbaar."""
    dagen = {}
    for i, a in enumerate(items):
        dagen.setdefault(a["datum"], []).append(i)
    uit, dag = ["<div class='eerder'>"], None
    for i, a in enumerate(items):
        if a["datum"] != dag:
            if dag: uit.append("</ul>")
            dag = a["datum"]
            mob = " alleen-mobiel" if all(j < dubbel for j in dagen[dag]) else ""
            uit.append(f"<h3 class='e-dag{mob}'>{nl_datum(datetime.date.fromisoformat(dag), True)}</h3><ul class='e-lijst{mob}'>")
        mob = " class='alleen-mobiel'" if i < dubbel else ""
        uit.append(f"""<li{mob}><a class="e-img" href="{url_van(a)}"><img src="{a['beeld']}" alt="{esc(a['beeld_alt'])}" width="1600" height="900" loading="lazy" decoding="async"></a>
  <div><a class="kick" href="{rubriek_url(a['rubriek'])}">{esc(a['rubriek'])}</a>
  <a class="e-t" href="{url_van(a)}">{esc(a['titel'])}</a>
  <div class="meta">{a.get('tijd', '')}</div></div></li>""")
    uit.append("</ul></div>")
    return "\n".join(uit)

def lijst_pagina(titel, intro, url, items, vandaag, seo_titel=None, seo_beschrijving=None):
    return (kop(seo_titel or f"{titel} | Ringvrees", seo_beschrijving or intro, url) + balk(vandaag) + f"""
<main class="wrap"><div class="sec" style="margin-top:44px"><h1 class="h" style="font-size:44px">{esc(titel)}</h1></div>
<p class="intro">{esc(intro)}</p>
{items}
</main>""" + band("Liever ook nooit de ring uit?<br>Volg het nieuws waar je het al leest.") + VOET)


def over(vandaag):
    ld = {"@context": "https://schema.org", "@type": "AboutPage", "url": SITE + "/over/", "name": "Over Ringvrees",
          "inLanguage": "nl-NL", "about": ORG, "mainEntity": {"@type": "DefinedTerm", "name": "ringvrees",
          "description": "De aanhoudende angst om de Amsterdamse ring A10 te verlaten. Ook: de naam van een satirisch nieuwsplatform uit Amsterdam.",
          "inDefinedTermSet": "Amsterdams"}}
    extra = f'\n<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
    d = ROOT / "over"; d.mkdir(exist_ok=True)
    (d / "index.html").write_text(kop("Wat is Ringvrees? Satirisch nieuws uit Amsterdam | Ringvrees",
        "Ringvrees is een satirisch nieuwsplatform uit Amsterdam. En ringvrees (de; v.) is de angst om de ring A10 te verlaten.",
        "/over/", None, extra) + balk(vandaag) + f"""
<article class="art">
  <span class="kick">Over ons</span>
  <h1 class="h">Wat is Ringvrees?</h1>
  <p class="lede">Ringvrees is satirisch nieuws uit Amsterdam. Elke dag echt Amsterdams nieuws, maar dan zoals het écht voelt binnen de ring A10.</p>
</article>
<article class="art body">
  <h2 class="h">Het woord</h2>
  <p><b>ringvrees</b> (de; v.) is de aanhoudende angst om de Amsterdamse ring A10 te verlaten. Het treft vooral mensen die binnen de ring wonen en alles wat ze nodig hebben op fietsafstand hebben. Amstelveen voelt als buitenland, Almere als een expeditie. Er bestaat geen zalfje voor en de meeste patiënten willen er ook niet van af.</p>
  <p>Herkent u zichzelf? Lees dan <a href="/nieuws/symptomen-van-ringvrees/">de bijsluiter met alle symptomen</a>.</p>
  <h2 class="h">Het platform</h2>
  <p>Ringvrees neemt elke dag het grootste Amsterdamse nieuws en vertelt het zoals het binnen de A10 voelt. De feiten kloppen: elk nieuwsstuk begint bij echt Amsterdams nieuws. We schrijven alles in eigen woorden, nemen geen teksten over en gebruiken alleen rechtenvrije foto’s. De rest is satire. Verzonnen bronnen zijn altijd anoniem en echte mensen leggen we nooit woorden in de mond.</p>
  <p>Je vindt Ringvrees op <a href="{IG}">Instagram (@ringvrees)</a>, op <a href="{FB}">Facebook</a> en hier op ringvrees.nl, met elke dag nieuwe verhalen.</p>
  <h2 class="h" id="redactie">De redactie</h2>
  <p>Ringvrees wordt gemaakt door een kleine redactie die vergadert in een bakfiets ergens aan de gracht, veilig binnen de ring. In de bak passen precies drie redacteuren, dus groter dan dit worden we nooit. Elke ochtend begint met koffie van het tentje op de hoek en de vraag of iemand vandaag écht naar Noord moet. Het antwoord is altijd nee, maar voor de zekerheid volgen we de dienstregeling van de pont alsof het beurskoersen zijn. Onze verslaggevers komen nooit verder dan de A10 en een trip naar Sloterdijk geldt als dienstreis met gevarentoeslag. Alles wat we schrijven gaat langs een eindredacteur die Amstelveen nog steeds een verzonnen plaats noemt. Wel zo netjes: bij nieuws van één medium zetten we de bron eronder.</p>
  <h2 class="h">Contact</h2>
  <p>Tip, klacht of een buurman die nooit de ring uit gaat? Mail naar <a id="m2" href="#">hallo [at] ringvrees [punt] nl</a>. Zit er een fout in de feiten waar een stuk mee begint? Dan zetten we het recht, sneller dan de gemeente een brug repareert.</p>
</article>
<script>(function(){{var a=document.getElementById("m2"),e="hallo"+"@"+["ringvrees","nl"].join(".");a.textContent=e;a.href="mai"+"lto:"+e;}})();</script>
""" + band("Liever ook nooit de ring uit?<br>Volg het nieuws waar je het al leest.") + VOET, encoding="utf-8")
    return ["/over/"]


def test_pagina(vandaag):
    d = ROOT / "test"; d.mkdir(exist_ok=True)
    inhoud = (ROOT / "_bron" / "test.html").read_text(encoding="utf-8")
    (d / "index.html").write_text(kop("Heb jij ringvrees? Doe de test | Ringvrees",
        "Tien vragen, één minuut: hoe erg is jouw angst om de Amsterdamse ring A10 te verlaten? Doe de ringvrees-test en deel je uitslag.",
        "/test/") + balk(vandaag) + inhoud + band("Liever ook nooit de ring uit?<br>Volg het nieuws waar je het al leest.") + VOET, encoding="utf-8")
    return ["/test/"]


def afstand_pagina(vandaag):
    d = ROOT / "afstand"; d.mkdir(exist_ok=True)
    inhoud = (ROOT / "_bron" / "afstand.html").read_text(encoding="utf-8")
    (d / "index.html").write_text(kop("Hoe ver woon jij van de ring? De Ring-afstandmeter | Ringvrees",
        "Vul je postcode in en zie hoeveel meter je binnen of buiten de Amsterdamse ring A10 woont. Plus wat dat over je zegt.",
        "/afstand/") + balk(vandaag) + inhoud + band("Liever ook nooit de ring uit?<br>Volg het nieuws waar je het al leest.") + VOET, encoding="utf-8")
    return ["/afstand/"]


def weer_pagina(vandaag):
    d = ROOT / "weer"; d.mkdir(exist_ok=True)
    inhoud = (ROOT / "_bron" / "weer.html").read_text(encoding="utf-8")
    (d / "index.html").write_text(kop("Weer in Amsterdam: de komende dagen binnen de ring | Ringvrees",
        "Het weerbericht voor Amsterdam binnen de A10, voor de komende vijf dagen. Voor het weer buiten de ring zoekt u het zelf maar uit.",
        "/weer/") + balk(vandaag) + inhoud + band("Liever ook nooit de ring uit?<br>Volg het nieuws waar je het al leest.") + VOET, encoding="utf-8")
    return ["/weer/"]


def pagina_404(vandaag):
    inhoud = """<section class="wrap" style="padding:70px 24px 80px;max-width:760px">
  <span class="kick">Fout 404</span>
  <h1 class="h" style="font-size:52px;margin:18px 0 16px">Deze pagina ligt buiten de ring</h1>
  <p style="font:500 19px/1.55 Inter;color:#2b2a2e;margin-bottom:28px">Wij gaan er ook niet heen. Misschien is de link verhuisd, misschien heeft hij nooit bestaan. Hoe dan ook: binnen de ring is genoeg te lezen.</p>
  <p style="display:flex;gap:12px;flex-wrap:wrap"><a class="kick" style="font-size:14px;padding:12px 16px" href="/">Terug naar het nieuws →</a><a class="kick" style="font-size:14px;padding:12px 16px;background:var(--ink)" href="/test/">Doe de ringvrees-test →</a></p>
</section>"""
    html = kop("Pagina niet gevonden | Ringvrees", "Deze pagina ligt buiten de ring.", "/404.html",
               extra='\n<meta name="robots" content="noindex">') + balk(vandaag) + inhoud + VOET
    (ROOT / "404.html").write_text(html, encoding="utf-8")


def feed(alle):
    from email.utils import format_datetime
    items = ""
    for a in alle[:20]:
        dt = datetime.datetime.fromisoformat(f"{a['datum']}T{a.get('tijd') or '12:00'}").replace(tzinfo=ZoneInfo("Europe/Amsterdam"))
        items += (f"<item><title>{esc(a['titel'])}</title><link>{SITE}{url_van(a)}</link><guid>{SITE}{url_van(a)}</guid>"
                  f"<pubDate>{format_datetime(dt)}</pubDate><category>{esc(a['rubriek'])}</category>"
                  f"<description>{esc(a['lede'])}</description>"
                  f"<enclosure url=\"{SITE}{a['beeld']}\" type=\"image/jpeg\" length=\"{(ROOT / a['beeld'].lstrip('/')).stat().st_size}\"/></item>\n")
    (ROOT / "feed.xml").write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>
<title>Ringvrees</title><link>{SITE}/</link><language>nl-nl</language>
<description>Satirisch Amsterdams nieuws zoals het écht voelt binnen de A10.</description>
<atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml"/>
{items}</channel></rss>
""", encoding="utf-8")


def eerlijke_datum(urls, vandaag):
    """Lastmod verandert alleen als de inhoud echt veranderde (de datum in de balk telt niet mee)."""
    import hashlib, re as _re
    f = ROOT / "_bron" / "lastmod.json"
    oud = json.loads(f.read_text()) if f.exists() else {}
    nieuw = {}
    for u in urls:
        p = ROOT / u.lstrip("/") / "index.html"
        if not p.exists():
            continue
        t = _re.sub(r'<div class="strip">.*?</div></div>', "", p.read_text(encoding="utf-8"), flags=_re.S)
        h = hashlib.sha1(t.encode()).hexdigest()[:12]
        nieuw[u] = oud[u] if u in oud and oud[u][0] == h else [h, vandaag.isoformat()]
    f.write_text(json.dumps(nieuw, indent=1, ensure_ascii=False))
    return {u: v[1] for u, v in nieuw.items()}


# Uitleg per rubriek (intro op de pagina en omschrijving voor Google). Nieuwe rubriek? Voeg hem toe in _bron/rubrieken.json.
# versie van style.css, zodat browsers na een wijziging meteen de nieuwe opmaak laden
CSS_V = hashlib.sha1((ROOT / 'style.css').read_bytes()).hexdigest()[:8]
_rf = ROOT / "_bron" / "rubrieken.json"
RUBRIEKEN = json.loads(_rf.read_text(encoding="utf-8")) if _rf.exists() else {}


def rubrieken(alle, vandaag):
    per = {}
    for a in alle:
        per.setdefault(a["rubriek"], []).append(a)
    for r, arts in per.items():
        d = ROOT / "rubriek" / rslug(r); d.mkdir(parents=True, exist_ok=True)
        grid = "<div class='grid'>" + "".join(kaart(a) for a in arts) + "</div>"
        info = RUBRIEKEN.get(r, {})
        intro = info.get("intro") or f"Alle artikelen van Ringvrees in de rubriek {r}: echt Amsterdams nieuws, maar dan zoals het voelt binnen de ring A10."
        (d / "index.html").write_text(lijst_pagina(r, intro, rubriek_url(r), grid, vandaag,
            seo_titel=f"{r}: satirisch nieuws uit Amsterdam | Ringvrees",
            seo_beschrijving=info.get("omschrijving") or f"Alle artikelen van Ringvrees in de rubriek {r}: echt Amsterdams nieuws, maar dan zoals het voelt binnen de ring A10. Droog, flauw en elke dag nieuw."), encoding="utf-8")
    tegels = "<div class='rubrieken'>" + "".join(
        f"<a href='{rubriek_url(r)}'><span class='kick'>{esc(r)}</span><b>{len(v)} {'artikel' if len(v) == 1 else 'artikelen'}</b></a>"
        for r, v in sorted(per.items(), key=lambda x: (-len(x[1]), x[0]))) + "</div>"
    d = ROOT / "rubrieken"; d.mkdir(exist_ok=True)
    namen = sorted(per)
    opsomming = ", ".join(namen[:-1]) + " en " + namen[-1] if len(namen) > 1 else namen[0]
    (d / "index.html").write_text(lijst_pagina("Rubrieken", "Alle onderwerpen van binnen de A10 op een rij.", "/rubrieken/", tegels, vandaag,
        seo_titel="Alle rubrieken: satirisch nieuws uit Amsterdam | Ringvrees",
        seo_beschrijving=f"Alle rubrieken van Ringvrees op een rij: {opsomming}. Satirisch nieuws uit Amsterdam, gezien van binnen de ring A10."[:158]), encoding="utf-8")
    return ["/rubrieken/"] + [rubriek_url(r) for r in per]


KOMMA_EN = re.compile(r"[,;]\s+en\b|\ben\s*,", re.I)


def komma_check(alle):
    """Huisregel: nooit een komma voor of na 'en'. Meldt overtredingen, maar bouwt gewoon door."""
    fouten = []
    def tekst(x):
        if isinstance(x, str): yield x
        elif isinstance(x, dict):
            for v in x.values(): yield from tekst(v)
        elif isinstance(x, list):
            for v in x: yield from tekst(v)
    for a in alle:
        for veld in ("titel", "lede", "seo_titel", "seo_beschrijving", "beeld_alt", "doorstuur", "blokken"):
            for t in tekst(a.get(veld, "")):
                schoon = re.sub(r"<[^>]+>", "", t)
                for m in KOMMA_EN.finditer(schoon):
                    fouten.append(f"{a['slug']}: ...{schoon[max(0, m.start()-40):m.end()+25]}...")
    if fouten:
        print("LET OP: komma voor of na 'en' gevonden. Herschrijf deze zinnen in het artikel:")
        for f in fouten: print("  -", f)


def nieuws_sitemap(alle):
    """Google News-sitemap: alleen nieuwsartikelen van de laatste 2 dagen (max 1000)."""
    nu = datetime.datetime.now(ZoneInfo("Europe/Amsterdam"))
    regels = []
    for a in alle:
        if a.get("type") == "tijdloos":
            continue
        pub = datetime.datetime.fromisoformat(f"{a['datum']}T{a.get('tijd') or '12:00'}").replace(tzinfo=ZoneInfo("Europe/Amsterdam"))
        if pub > nu or nu - pub > datetime.timedelta(days=2):
            continue
        regels.append(f"  <url><loc>{SITE}{url_van(a)}</loc><news:news><news:publication><news:name>Ringvrees</news:name>"
                      f"<news:language>nl</news:language></news:publication><news:publication_date>{pub.isoformat()}</news:publication_date>"
                      f"<news:title>{esc(a['titel'])}</news:title></news:news></url>\n")
    (ROOT / "news-sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">\n' + "".join(regels[:1000]) + "</urlset>\n", encoding="utf-8")


def main():
    vandaag = datetime.date.today()
    alle = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "_bron/artikelen").glob("*.json"))]
    for a in alle:
        for veld in ("slug", "datum", "type", "rubriek", "titel", "lede", "beeld", "beeld_alt", "blokken"):
            assert veld in a, f"{a.get('slug')}: veld {veld} ontbreekt"
        assert (ROOT / a["beeld"].lstrip("/")).exists(), f"{a['slug']}: beeld {a['beeld']} bestaat niet"
    komma_check(alle)
    alle.sort(key=lambda a: (a["datum"], a.get("tijd", "17:00")), reverse=True)
    (ROOT / "index.html").write_text(home(alle, vandaag), encoding="utf-8")
    for a in alle:
        d = ROOT / "nieuws" / a["slug"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(artikel_pagina(a, alle, vandaag), encoding="utf-8")
    extra = rubrieken(alle, vandaag) + over(vandaag) + test_pagina(vandaag) + afstand_pagina(vandaag) + weer_pagina(vandaag)
    beelden = {url_van(a): [a["beeld"]] for a in alle}
    beelden["/"] = [a["beeld"] for a in alle[:10]]
    pagina_404(vandaag)
    feed(alle)
    datums = eerlijke_datum(["/"] + extra, vandaag)
    urls = [(u, datums.get(u, vandaag.isoformat())) for u in ["/"] + extra] + [(url_van(a), a["datum"]) for a in alle]
    img = lambda u: "".join(f"<image:image><image:loc>{SITE}{b}</image:loc></image:image>" for b in beelden.get(u, []))
    sm = "".join(f"  <url><loc>{SITE}{u}</loc><lastmod>{m}</lastmod>{img(u)}</url>\n" for u, m in urls)
    (ROOT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n{sm}</urlset>\n', encoding="utf-8")
    nieuws_sitemap(alle)
    print(f"gebouwd: {len(alle)} artikelen")


if __name__ == "__main__":
    main()
