const CACHE_NAME = 'relay-portal-v1';
const STATIC_ASSETS = [
  '/',
  '/offline',
];

// Install - cache shell
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

// Activate - clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Fetch - network first, fallback to cache
self.addEventListener('fetch', (event) => {
  const { request } = event;

  // Skip non-GET, chrome-extension, and API/SSE requests
  if (
    request.method !== 'GET' ||
    request.url.includes('/api/') ||
    request.url.includes('chrome-extension') ||
    request.url.includes('extension')
  ) {
    return;
  }

  event.respondWith(
    fetch(request)
      .then((response) => {
        // Cache successful responses for static assets
        if (response.ok && (request.url.includes('/_next/static/') || request.url.includes('/icons/'))) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
        }
        return response;
      })
      .catch(() => {
        // Fallback to cache
        return caches.match(request).then((cached) => {
          if (cached) return cached;
          // For navigation requests, show offline page
          if (request.mode === 'navigate') {
            return caches.match('/offline');
          }
          return new Response('', { status: 408 });
        });
      })
  );
});
