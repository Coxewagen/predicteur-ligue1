// Service worker minimal : juste ce qu'il faut pour que Chrome propose
// "Ajouter à l'écran d'accueil" et que l'appli s'ouvre même en réseau faible.
// Ne met PAS en cache les données (classement/compos) : on va toujours
// chercher la dernière version sur le réseau si possible.
const CACHE = "predicteur-l1-shell-v2";
const SHELL = ["./index.html", "./manifest.webmanifest"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(SHELL))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  event.respondWith(
    // "no-store" : on ignore volontairement le cache HTTP du téléphone/
    // navigateur, pas seulement le cache du service worker. Sans ça,
    // Chrome pouvait servir une ancienne copie de index.html même quand
    // le réseau fonctionnait, sans jamais repasser par le serveur.
    fetch(event.request, { cache: "no-store" })
      .then((resp) => {
        caches.open(CACHE).then((cache) => cache.put(event.request, resp.clone()));
        return resp;
      })
      .catch(() => caches.match(event.request))
  );
});
