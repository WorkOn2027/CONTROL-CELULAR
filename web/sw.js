// Service worker mínimo: guarda la página para que la app abra rápido.
// Siempre intenta traer la versión nueva de la PC; si no responde, usa la guardada.
const CACHE = "control-v6";
const ARCHIVOS = ["/", "/plantillas.js", "/manifest.webmanifest", "/icono-192.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ARCHIVOS)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  e.respondWith(
    fetch(e.request).then((r) => {
      if (r.ok && ARCHIVOS.includes(new URL(e.request.url).pathname)) {
        const copia = r.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copia));
      }
      return r;
    }).catch(() => caches.match(e.request))
  );
});
