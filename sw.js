const CACHE_NAME = "vamus-audit-v3"; // Mudamos para v3 para forçar a limpeza
const ASSETS = [
  "./",
  "./index.html",
  "./baseDadosHorarios.json",
  "./manifest.json",
  
  // Adicione aqui os nomes exatos do seu ficheiro CSS e JS se os tiver separado, por exemplo:
  // "./style.css",
  // "./script.js",
  // Se usa ExcelJS por CDN, ele também pode ser guardado em cache:
  "https://cdn.jsdelivr.net/npm/exceljs/dist/exceljs.min.js" 
];

// Instalação do Service Worker e Caching dos ficheiros
self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS);
    })
  );
});

// Ativação e limpeza de caches antigas
self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    })
  );
});

// Responder offline com os ficheiros guardados em cache
self.addEventListener("fetch", (e) => {
  e.respondWith(
    caches.match(e.request).then((cachedResponse) => {
      return cachedResponse || fetch(e.request);
    })
  );
});