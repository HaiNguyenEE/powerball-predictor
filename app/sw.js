// sw.js — service worker for offline support
// Strategy:
//   - HTML pages (index.html, /) → NETWORK-FIRST so updates show immediately,
//     fallback to cache when offline
//   - Static assets (icons, manifest, sw itself) → CACHE-FIRST for speed
//   - NY Open Data API → network-only (no cache, freshness matters)
//
// Bumping CACHE name invalidates the old cache on activation.

const CACHE = 'powerball-v3';
const SHELL = [
  './',
  './index.html',
  './manifest.json',
  './icon-192.png',
  './icon-512.png',
  './apple-touch-icon.png',
  './favicon.png',
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

function isHTML(req) {
  if (req.mode === 'navigate') return true;
  const accept = req.headers.get('accept') || '';
  if (accept.includes('text/html')) return true;
  const url = new URL(req.url);
  if (url.pathname.endsWith('/') || url.pathname.endsWith('.html')) return true;
  return false;
}

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);

  // NY Open Data refresh: network only, never cache
  if (url.host.includes('data.ny.gov')) {
    e.respondWith(fetch(e.request).catch(() => new Response('', {status: 504})));
    return;
  }

  // HTML: NETWORK-FIRST so banner updates / model snapshots show immediately
  if (isHTML(e.request)) {
    e.respondWith(
      fetch(e.request)
        .then((resp) => {
          // Cache a copy for offline fallback
          if (resp.ok && e.request.method === 'GET') {
            const copy = resp.clone();
            caches.open(CACHE).then((c) => c.put(e.request, copy));
          }
          return resp;
        })
        .catch(() => caches.match(e.request).then((cached) => cached || caches.match('./index.html')))
    );
    return;
  }

  // Static assets (icons, manifest, png): CACHE-FIRST
  e.respondWith(
    caches.match(e.request).then((cached) => cached || fetch(e.request).then((resp) => {
      if (resp.ok && e.request.method === 'GET' && url.origin === location.origin) {
        const copy = resp.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy));
      }
      return resp;
    }))
  );
});

// Listen for skipWaiting from the page (manual update button)
self.addEventListener('message', (e) => {
  if (e.data && e.data.type === 'SKIP_WAITING') self.skipWaiting();
});
