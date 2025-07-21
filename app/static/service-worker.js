const CACHE_NAME = "ulisse-voice-cache-v1";
const urlsToCache = [
  "/dashboard/voice-creator",
  "/dashboard/static/js/bundle.js",
  "/dashboard/manifest.json",
  "/dashboard/logo192.png",
  "/dashboard/logo512.png"
];

// Installazione: caching iniziale
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(urlsToCache);
    })
  );
});

// Fetch: serve dalla cache se disponibile
self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return; // 🛑 Evita interferenze con POST, PUT, ecc.

  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request);
    })
  );
});

// Pulizia cache vecchie
self.addEventListener("activate", (event) => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then((cacheNames) =>
      Promise.all(
        cacheNames.map((name) => {
          if (!cacheWhitelist.includes(name)) {
            return caches.delete(name);
          }
        })
      )
    )
  );
});
