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
  instagram   optioneel, url van de Instagram-post
"""
import json, html, pathlib, datetime, re, unicodedata
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
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/style.css">{extra}
</head>
<body>"""


def balk(vandaag, home=False):
    logo = '<a class="logo" href="/">RINGVREES</a>'
    if home:
        logo = '<h1 style="margin:0;font-size:inherit;font-weight:inherit;line-height:inherit">' + logo + '</h1>'
    return f"""<div class="strip"><div class="wrap"><span>{nl_datum(vandaag, True)}</span><span><b>Satire</b> · Nieuws van binnen de A10</span></div></div>
<header class="top"><div class="wrap">
  {logo}
  <nav class="nav"><a class="hide" href="/#nieuws">Nieuws</a><a class="hide" href="/#tijdloos">Tijdloos</a><a class="hide" href="/rubrieken/">Rubrieken</a><a class="hide" href="/over/">Over</a><a class="ig" href="/test/">Doe de test →</a>
  <details class="menu"><summary aria-label="Menu"><span></span><span></span><span></span></summary>
   <div class="menu-paneel" onclick="this.parentNode.removeAttribute('open')"><a href="/#nieuws">Nieuws</a><a href="/#tijdloos">Tijdloos</a><a href="/rubrieken/">Rubrieken</a><a href="/over/">Over Ringvrees</a><a href="/test/">Heb jij ringvrees? De test</a><a href="/afstand/">Ring-afstandmeter</a><a href="{IG}">Instagram</a><a href="{FB}">Facebook</a></div>
  </details></nav>
</div></header>"""


VOET = """<footer><div class="wrap"><span>Ringvrees is satire. Alles is gebaseerd op echt nieuws, maar dan zoals het écht voelt binnen de A10.</span></div></footer>
</body>
</html>
"""


WEER = """<div class="weer" id="weer" hidden><div class="wrap"><span class="weer-k">Weer binnen de ring</span><span id="weerNu"></span><span class="weer-b" id="weerBuiten"></span></div></div>
<script>(function(){
var t={0:["Zonnig","Buiten de ring waarschijnlijk ook zon, maar wie gaat dat checken?"],1:["Licht bewolkt","Buiten de ring: niet relevant."],2:["Half bewolkt","Buiten de ring: niet relevant."],3:["Bewolkt","Buiten de ring is het grijzer. Zeggen ze."],45:["Mist","Buiten de ring zie je nu helemaal niks. Dus niks veranderd."],48:["Mist","Buiten de ring zie je nu helemaal niks. Dus niks veranderd."],51:["Motregen","Buiten de ring regent het harder. Wij gaan niet kijken."],61:["Regen","Buiten de ring regent het harder. Wij gaan niet kijken."],71:["Sneeuw","Buiten de ring: wegen onbegaanbaar. Ook zonder sneeuw."],80:["Buien","Blijf binnen. Binnen de ring, bedoelen we."],95:["Onweer","Blijf binnen. Binnen de ring, bedoelen we."]};
function zoek(c){var k=[95,80,71,61,51,48,45,3,2,1,0];for(var i=0;i<k.length;i++){if(c>=k[i])return t[k[i]];}return t[3];}
fetch("https://api.open-meteo.com/v1/forecast?latitude=52.37&longitude=4.89&current=temperature_2m,weather_code,wind_speed_10m&timezone=Europe%2FAmsterdam").then(function(r){return r.json()}).then(function(j){var c=j.current,w=zoek(c.weather_code),b=w[1];if(c.wind_speed_10m>38)b="Harde wind. De pont naar Noord is nu een avontuur.";
document.getElementById("weerNu").textContent=Math.round(c.temperature_2m)+"° · "+w[0];document.getElementById("weerBuiten").textContent=b;document.getElementById("weer").hidden=false;}).catch(function(){});
})();</script>"""


BUURTKAART = '<div class="band-r"><div class="bk-kop">Buurtkaart · tik op een buurt</div><svg class="bk-svg" viewBox="40 20 930 640" role="img" aria-label="Kaart van de buurten binnen de A10"><path d="M410 52 C397 64 399 99 388 120 C377 141 360 162 345 180 C330 198 311 208 300 225 C289 242 283 259 278 281 C273 303 270 332 270 358 C270 384 273 413 278 435 C283 457 287 476 301 492 C315 508 340 521 364 531 C388 541 417 547 442 550 C467 553 490 552 513 550 C536 548 561 544 583 537 C605 530 624 520 646 505 C668 490 695 467 716 447 C737 427 755 405 771 383 C787 361 806 336 810 313 C814 290 805 263 794 242 C783 221 761 203 743 185 C725 167 708 149 685 133 C662 117 633 100 607 88 C581 76 552 69 528 63 C504 57 486 52 466 50 C446 48 423 40 410 52Z" fill="rgba(242,236,225,.08)" stroke="#F2ECE1" stroke-width="7" stroke-linejoin="round"/><g class="bk-p" data-b="centrum" tabindex="0"><circle cx="511" cy="253" r="34" fill="transparent"/><circle class="bk-dot" cx="511" cy="253" r="11"/><text x="529" y="261" style="text-anchor:start">Centrum</text></g><g class="bk-p" data-b="jordaan" tabindex="0"><circle cx="454" cy="229" r="34" fill="transparent"/><circle class="bk-dot" cx="454" cy="229" r="11"/><text x="436" y="237" style="text-anchor:end">Jordaan</text></g><g class="bk-p" data-b="pijp" tabindex="0"><circle cx="511" cy="390" r="34" fill="transparent"/><circle class="bk-dot" cx="511" cy="390" r="11"/><text x="511" y="368">De Pijp</text></g><g class="bk-p" data-b="oost" tabindex="0"><circle cx="651" cy="337" r="34" fill="transparent"/><circle class="bk-dot" cx="651" cy="337" r="11"/><text x="651" y="315">Oost</text></g><g class="bk-p" data-b="west" tabindex="0"><circle cx="408" cy="300" r="34" fill="transparent"/><circle class="bk-dot" cx="408" cy="300" r="11"/><text x="408" y="278">Oud-West</text></g><g class="bk-p" data-b="noord" tabindex="0"><circle cx="643" cy="177" r="34" fill="transparent"/><circle class="bk-dot" cx="643" cy="177" r="11"/><text x="643" y="155">Noord</text></g><g class="bk-p" data-b="zuid" tabindex="0"><circle cx="387" cy="393" r="34" fill="transparent"/><circle class="bk-dot" cx="387" cy="393" r="11"/><text x="387" y="371">Oud-Zuid</text></g><g class="bk-p bk-uit" data-b="nieuwwest" tabindex="0"><rect x="80" y="274" width="175" height="44" fill="transparent"/><text x="250" y="300" style="text-anchor:end">← Nieuw-West</text></g><g class="bk-p bk-uit" data-b="amstelveen" tabindex="0"><rect x="295" y="604" width="160" height="44" fill="transparent"/><text x="375" y="630">Amstelveen ↓</text></g></svg><div class="bk-kaart"><b id="bkNaam">Binnen de ring</b><span id="bkTekst">Tik op een buurt en lees hoe het daar écht voelt.</span></div></div>'
BUURTSCRIPT = '<script>(function(){var D={"centrum": {"naam": "Centrum", "tekst": "Bewoners: drie echte Amsterdammers en 40.000 rolkoffers. Verlaat de buurt alleen om over de buurt te klagen.", "binnen": true}, "jordaan": {"naam": "Jordaan", "tekst": "Iedereen kent elkaar, vooral de makelaar. Bruine cafés per inwoner: genoeg.", "binnen": true}, "pijp": {"naam": "De Pijp", "tekst": "4.000 inwoners, 11.000 brunchplekken. Gaat alleen de deur uit voor de Albert Cuyp.", "binnen": true}, "oost": {"naam": "Oost", "tekst": "Havermelk-hoofdstad van Nederland. Hoogste bakfietsdichtheid ter wereld, en de langste bakfietsfile.", "binnen": true}, "west": {"naam": "Oud-West", "tekst": "Woont tussen de Kinkerstraat en een stevige mening over de Kinkerstraat.", "binnen": true}, "noord": {"naam": "Noord", "tekst": "Officieel binnen de ring, emotioneel nog buitenland. Bereikbaar per pont en per wonder.", "binnen": true}, "zuid": {"naam": "Oud-Zuid", "tekst": "Vondelpark als achtertuin, de VvE als geloof. Gaat de ring alleen uit voor Schiphol en wintersport.", "binnen": true}, "nieuwwest": {"naam": "Nieuw-West", "tekst": "Ligt buiten de ring. We hebben gehoord dat het er prima is, maar dat hebben we niet gecontroleerd.", "binnen": false}, "amstelveen": {"naam": "Amstelveen", "tekst": "Buitenland met een tramlijn. Wel heel netjes, dat moet gezegd.", "binnen": false}};document.querySelectorAll(".bk-p").forEach(function(g){function kies(){document.querySelectorAll(".bk-p").forEach(function(x){x.classList.remove("aan")});g.classList.add("aan");var b=D[g.dataset.b];document.getElementById("bkNaam").textContent=b.naam+(b.binnen?"":" · buiten de ring");document.getElementById("bkTekst").textContent=b.tekst;}g.addEventListener("click",kies);g.addEventListener("keydown",function(e){if(e.key==="Enter")kies()});});})();</script>'


def band(tekst):
    return ('<section class="band"><div class="wrap band-grid"><div class="band-l"><div class="h">' + tekst + '</div>'
            '<a class="band-ig" href="' + IG + '">Volg @ringvrees →</a></div>' + BUURTKAART + '</div>' + BUURTSCRIPT + '</section>')


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


def kaart(a, groot=False):
    d = datetime.date.fromisoformat(a["datum"])
    meta = "Tijdloos" if a["type"] == "tijdloos" else nl_datum(d)
    if groot:
        return f"""<div class="hero">
    <a class="heroimg" href="{url_van(a)}"><img src="{a['beeld']}" alt="{esc(a['beeld_alt'])}"></a>
    <div>
      <a class="kick" href="{rubriek_url(a['rubriek'])}">{esc(a['rubriek'])}</a>
      <a href="{url_van(a)}"><h1 class="h">{esc(a['titel'])}</h1>
      <p>{esc(a['lede'])}</p></a>
      <div class="meta">{meta}</div>
    </div>
  </div>"""
    return f"""<div class="card">
      <a class="beeld{' foto' if a.get('beeld_bron', '').startswith('Foto') else ''}" href="{url_van(a)}"><img src="{a['beeld']}" alt="{esc(a['beeld_alt'])}"></a>
      <a class="kick" href="{rubriek_url(a['rubriek'])}">{esc(a['rubriek'])}</a>
      <a href="{url_van(a)}"><h3 class="h">{esc(a['titel'])}</h3>
      <p>{esc(a['lede'])}</p></a>
      <div class="meta">{meta}</div>
    </div>"""


def artikel_pagina(a, alle, vandaag):
    d = datetime.date.fromisoformat(a["datum"])
    url = url_van(a)
    tijd = a.get("tijd") or "12:00"
    pub = datetime.datetime.fromisoformat(f"{a['datum']}T{tijd}").replace(tzinfo=ZoneInfo("Europe/Amsterdam")).isoformat()
    ld = {"@context": "https://schema.org", "@type": "NewsArticle", "headline": a["titel"][:110],
          "description": a["lede"], "image": [SITE + a["beeld"]], "datePublished": pub, "dateModified": pub,
          "inLanguage": "nl-NL", "genre": "satire", "articleSection": a["rubriek"], "url": SITE + url,
          "mainEntityOfPage": SITE + url, "isAccessibleForFree": True,
          "contentLocation": {"@type": "Place", "name": "Amsterdam"},
          "author": {"@type": "Organization", "name": "Redactie Ringvrees", "url": SITE + "/over/"},
          "publisher": ORG}
    extra = f'\n<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
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
    meta = "Tijdloos" if a["type"] == "tijdloos" else nl_datum(d, True)
    return (kop(a.get("seo_titel") or f"{a['titel']} | Ringvrees", a.get("seo_beschrijving") or a["lede"], url, a["beeld"], extra) + balk(vandaag) + f"""
<article class="art">
  <a class="kick" href="{rubriek_url(a['rubriek'])}">{esc(a['rubriek'])}</a>
  <h1 class="h">{esc(a['titel'])}</h1>
  <p class="lede">{esc(a['lede'])}</p>
  <div class="meta">{meta} · Redactie Ringvrees</div>
</article>
<figure class="kopbeeld"><img src="{a['beeld']}" alt="{esc(a['beeld_alt'])}">{beeldbron}</figure>
<article class="art body">
  {''.join(blok(b) for b in a['blokken'])}
  <div class="share"><b>{esc(a.get('doorstuur', 'Stuur door naar je huisgenoot'))}</b><a href="https://wa.me/?text={esc(a['titel'] + ' ' + SITE + url)}">WhatsApp</a>{ig}</div>
  {bron}
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
        delen.append("<div class='sec' id='nieuws'><h2 class='h'>Meer nieuws</h2><span class='meta'>Elke dag vers</span></div><div class='grid'>"
                     + "".join(kaart(a) for a in nieuws[1:13]) + "</div>")
    if tijdloos:
        delen.append("<div class='sec' id='tijdloos'><h2 class='h'>Tijdloos</h2><span class='meta'>Voor altijd binnen de ring</span></div><div class='grid'>"
                     + "".join(kaart(a) for a in tijdloos) + "</div>")
    delen.append("</main>")
    delen.append(band("Liever ook nooit de ring uit?<br>Volg het nieuws waar je het al leest."))
    delen.append(VOET)
    return "\n".join(delen)


def lijst_pagina(titel, intro, url, items, vandaag):
    return (kop(f"{titel} | Ringvrees", intro, url) + balk(vandaag) + f"""
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
        "Ringvrees is een satirisch nieuwsplatform uit Amsterdam. En ringvrees (de; v.) is de angst om de ring A10 te verlaten. Niet te verwarren met ringworm.",
        "/over/", None, extra) + balk(vandaag) + f"""
<article class="art">
  <span class="kick">Over ons</span>
  <h1 class="h">Wat is Ringvrees?</h1>
  <p class="lede">Ringvrees is satirisch nieuws uit Amsterdam. Elke dag echt Amsterdams nieuws, maar dan zoals het écht voelt binnen de ring A10.</p>
</article>
<article class="art body">
  <h2 class="h">Het woord</h2>
  <p><b>ringvrees</b> (de; v.) is de aanhoudende angst om de Amsterdamse ring A10 te verlaten. Het treft vooral mensen die binnen de ring wonen en alles wat ze nodig hebben op fietsafstand hebben. Amstelveen voelt als buitenland, Almere als een expeditie. Niet te verwarren met ringworm: daar is een zalfje voor. Voor ringvrees niet.</p>
  <p>Herkent u zichzelf? Lees dan <a href="/nieuws/symptomen-van-ringvrees/">de bijsluiter met alle symptomen</a>.</p>
  <h2 class="h">Het platform</h2>
  <p>Ringvrees neemt elke dag het grootste Amsterdamse nieuws en vertelt het zoals het binnen de A10 voelt. De feiten kloppen: elk stuk begint bij echt Amsterdams nieuws. We schrijven alles in eigen woorden en nemen geen teksten of foto’s over. De rest is satire. Verzonnen bronnen zijn altijd anoniem en echte mensen leggen we nooit woorden in de mond.</p>
  <p>Je vindt Ringvrees op <a href="{IG}">Instagram (@ringvrees)</a>, op <a href="{FB}">Facebook</a> en hier op ringvrees.nl, met elke dag een nieuw verhaal.</p>
  <h2 class="h">Contact</h2>
  <p>Tip, klacht of een buurman die nooit de ring uit gaat? Mail naar <a id="m2" href="#">hallo [at] ringvrees [punt] nl</a>.</p>
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


def rubrieken(alle, vandaag):
    per = {}
    for a in alle:
        per.setdefault(a["rubriek"], []).append(a)
    for r, arts in per.items():
        d = ROOT / "rubriek" / rslug(r); d.mkdir(parents=True, exist_ok=True)
        grid = "<div class='grid'>" + "".join(kaart(a) for a in arts) + "</div>"
        (d / "index.html").write_text(lijst_pagina(r, f"Al het nieuws van binnen de ring in de rubriek {r}.", rubriek_url(r), grid, vandaag), encoding="utf-8")
    tegels = "<div class='rubrieken'>" + "".join(
        f"<a href='{rubriek_url(r)}'><span class='kick'>{esc(r)}</span><b>{len(v)} {'artikel' if len(v) == 1 else 'artikelen'}</b></a>"
        for r, v in sorted(per.items(), key=lambda x: (-len(x[1]), x[0]))) + "</div>"
    d = ROOT / "rubrieken"; d.mkdir(exist_ok=True)
    (d / "index.html").write_text(lijst_pagina("Rubrieken", "Alle onderwerpen van binnen de A10 op een rij.", "/rubrieken/", tegels, vandaag), encoding="utf-8")
    return ["/rubrieken/"] + [rubriek_url(r) for r in per]


def main():
    vandaag = datetime.date.today()
    alle = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "_bron/artikelen").glob("*.json"))]
    for a in alle:
        for veld in ("slug", "datum", "type", "rubriek", "titel", "lede", "beeld", "beeld_alt", "blokken"):
            assert veld in a, f"{a.get('slug')}: veld {veld} ontbreekt"
        assert (ROOT / a["beeld"].lstrip("/")).exists(), f"{a['slug']}: beeld {a['beeld']} bestaat niet"
    alle.sort(key=lambda a: (a["datum"], a.get("tijd", "17:00")), reverse=True)
    (ROOT / "index.html").write_text(home(alle, vandaag), encoding="utf-8")
    for a in alle:
        d = ROOT / "nieuws" / a["slug"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(artikel_pagina(a, alle, vandaag), encoding="utf-8")
    extra = rubrieken(alle, vandaag) + over(vandaag) + test_pagina(vandaag) + afstand_pagina(vandaag)
    urls = [("/", vandaag.isoformat())] + [(u, vandaag.isoformat()) for u in extra] + [(url_van(a), a["datum"]) for a in alle]
    sm = "".join(f"  <url><loc>{SITE}{u}</loc><lastmod>{m}</lastmod></url>\n" for u, m in urls)
    (ROOT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{sm}</urlset>\n', encoding="utf-8")
    print(f"gebouwd: {len(alle)} artikelen")


if __name__ == "__main__":
    main()
