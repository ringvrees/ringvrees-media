"""IndexNow: meldt nieuwe en gewijzigde pagina's bij Bing, Copilot, DuckDuckGo, Yandex, Seznam en Naver.
Draai NA een geslaagde push naar gh-pages:  python3 _bron/indexnow.py
Vergelijkt _bron/lastmod.json met de vorige commit (of met --sinds <commit>) en stuurt alleen de URL's
waarvan de inhoud veranderde. Wacht eerst tot GitHub Pages de nieuwe pagina's serveert (max ~4 min).
Google doet niet mee; daarvoor blijft de news-sitemap."""
import json, subprocess, sys, time, urllib.request
SITE = "https://ringvrees.nl"
KEY = "418ee61c20bd673916635d581bd230e0"

def oud_lastmod(ref):
    try:
        return json.loads(subprocess.run(["git", "show", f"{ref}:_bron/lastmod.json"], capture_output=True, text=True, check=True).stdout)
    except Exception:
        return {}

def main():
    ref = sys.argv[sys.argv.index("--sinds") + 1] if "--sinds" in sys.argv else "HEAD~1"
    nu = json.load(open("_bron/lastmod.json"))
    oud = oud_lastmod(ref)
    urls = [SITE + u for u, (h, _) in nu.items() if oud.get(u, [None])[0] != h]
    if not urls:
        print("indexnow: niets nieuws"); return
    # wacht tot de eerste artikelpagina (of anders de eerste url) live is
    test = next((u for u in urls if "/nieuws/" in u), urls[0])
    for _ in range(24):
        try:
            if urllib.request.urlopen(test, timeout=10).status == 200: break
        except Exception:
            pass
        time.sleep(10)
    body = json.dumps({"host": "ringvrees.nl", "key": KEY, "keyLocation": f"{SITE}/{KEY}.txt", "urlList": urls[:10000]}).encode()
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body, headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        r = urllib.request.urlopen(req, timeout=20); print(f"indexnow: {r.status}, {len(urls)} url's gemeld")
    except urllib.error.HTTPError as e:
        print(f"indexnow: fout {e.code} {e.read()[:200]!r}")

if __name__ == "__main__":
    main()
