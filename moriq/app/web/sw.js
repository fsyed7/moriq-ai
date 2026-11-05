// Keeps the app shell available so it opens like an installed app. Chats and answers never pass through this cache.
const CACHE = 'moriq-shell-v2';
const SHELL = ['/', '/app.js', '/welcome.js', '/styles.css', '/welcome.css', '/manifest.webmanifest', '/icons/icon-192.png', '/icons/icon-180.png'];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE).map(key => caches.delete(key)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  if (event.request.method !== 'GET' || url.origin !== location.origin || url.pathname.startsWith('/api/')) return;
  // Network first, so updates appear straight away; the cache only covers the app being offline.
  event.respondWith(fetch(event.request).then(response => {
    if (response.ok && SHELL.includes(url.pathname)) {
      const copy = response.clone();
      caches.open(CACHE).then(cache => cache.put(event.request, copy));
    }
    return response;
  }).catch(() => caches.match(event.request).then(hit => hit || Response.error())));
});
