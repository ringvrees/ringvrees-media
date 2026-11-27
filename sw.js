/* Ringvrees web-app: service worker.
   - Pagina's: eerst het netwerk (de bots zetten de hele dag nieuws online), zonder bereik de bewaarde versie.
   - Stijl, lettertypes, scripts en foto's: meteen uit de opslag, op de achtergrond ververst.
   - Andere domeinen (Metricool-teller, weer, Instagram) en /media/ (tijdelijke Instagram-slides) gaan er gewoon langs.
   Geen cookies, geen tracking: alles blijft op het toestel van de lezer.
   Pushmeldingen: OneSignal draait mee in deze service worker (alleen gebruikt in de app op een telefoon). */
try { importScripts("https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.sw.js"); } catch (fout) { /* zonder OneSignal blijft offline lezen werken */ }
const VERSIE = "rv-2";
const PAGINAS = VERSIE + "-paginas";
const STATISCH = VERSIE + "-statisch";
const BEELD = VERSIE + "-beeld";
const OFFLINE = "/offline/";
const VOORAF = [
  OFFLINE,
  "/icon-192.png",
  "/fonts/inter-latin-400-normal.woff2",
  "/fonts/inter-latin-800-normal.woff2",
  "/fonts/dm-serif-display-latin-400-normal.woff2"
];
const MAX_PAGINAS = 40;
const MAX_BEELD = 80;

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(STATISCH).then((c) => c.addAll(VOORAF)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((ks) => Promise.all(ks.filter((k) => !k.startsWith(VERSIE + "-")).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

async function snoei(naam, max) {
  const c = await caches.open(naam);
  const ks = await c.keys();
  for (let i = 0; i < ks.length - max; i++) await c.delete(ks[i]);
}

async function pagina(req) {
  const c = await caches.open(PAGINAS);
  try {
    const res = await fetch(req);
    if (res.ok) { c.put(req, res.clone()).then(() => snoei(PAGINAS, MAX_PAGINAS)); }
    return res;
  } catch (fout) {
    return (await c.match(req, { ignoreSearch: true })) || (await caches.match(OFFLINE));
  }
}

async function bewaard(req, naam, max) {
  const c = await caches.open(naam);
  const oud = await c.match(req);
  const nieuw = fetch(req).then((res) => {
    if (res.ok) { c.put(req, res.clone()).then(() => max && snoei(naam, max)); }
    return res;
  }).catch(() => oud);
  return oud || nieuw;
}

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  if (url.pathname.startsWith("/media/") || /\.(xml|txt)$/.test(url.pathname)) return;
  if (req.mode === "navigate") { e.respondWith(pagina(req)); return; }
  if (url.pathname.startsWith("/img/")) { e.respondWith(bewaard(req, BEELD, MAX_BEELD)); return; }
  if (/\.(css|js|woff2|png|ico|webmanifest)$/.test(url.pathname)) { e.respondWith(bewaard(req, STATISCH)); return; }
});
