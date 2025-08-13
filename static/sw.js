// Service Worker for KDP Cover Creator PWA
const CACHE_NAME = 'kdp-cover-creator-v1';
const urlsToCache = [
  '/',
  '/static/css/style.css',
  '/static/manifest.json',
  '/static/offline.html',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png',
  '/static/icons/icon-maskable-192x192.png',
  '/static/icons/icon-maskable-512x512.png',
  // Bootstrap and Font Awesome from CDN will be cached when accessed
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js'
];

// Install event - cache resources
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
      .catch((error) => {
        console.log('Cache addAll failed:', error);
        // Cache individual resources, ignore failures for external resources
        return Promise.all(
          urlsToCache.map(url => 
            cache.add(url).catch(err => {
              console.log('Failed to cache:', url, err);
              return null;
            })
          )
        );
      })
  );
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  // Skip cross-origin requests and non-GET requests
  if (!event.request.url.startsWith(self.location.origin) && 
      !event.request.url.startsWith('https://cdn.jsdelivr.net') &&
      !event.request.url.startsWith('https://cdnjs.cloudflare.com')) {
    return;
  }
  
  if (event.request.method !== 'GET') {
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Return cached version or fetch from network
        if (response) {
          return response;
        }

        return fetch(event.request).then((response) => {
          // Check if valid response
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }

          // Clone the response
          const responseToCache = response.clone();

          caches.open(CACHE_NAME)
            .then((cache) => {
              cache.put(event.request, responseToCache);
            });

          return response;
        }).catch(() => {
          // Network failed, try to return cached fallback for navigation requests
          if (event.request.destination === 'document') {
            return caches.match('/static/offline.html').then(response => {
              return response || caches.match('/');
            });
          }
          // For other resources, return a transparent response to avoid error messages
          if (event.request.destination === 'image') {
            // Return a 1x1 transparent pixel for images
            return new Response(new Uint8Array([137,80,78,71,13,10,26,10,0,0,0,13,73,72,68,82,0,0,0,1,0,0,0,1,8,6,0,0,0,31,21,196,137,0,0,0,13,73,68,65,84,8,215,99,248,15,0,1,1,1,0,24,221,141,176,0,0,0,0,73,69,78,68,174,66,96,130]), {
              status: 200,
              statusText: 'OK',
              headers: new Headers({
                'Content-Type': 'image/png',
                'Cache-Control': 'no-cache'
              })
            });
          }
          // Return empty response for other resources to avoid error messages
          return new Response('', {
            status: 200,
            statusText: 'OK',
            headers: new Headers({
              'Content-Type': 'text/plain',
              'Cache-Control': 'no-cache'
            })
          });
        });
      })
  );
});

// Handle background sync for form submissions when back online
self.addEventListener('sync', (event) => {
  if (event.tag === 'cover-generation') {
    event.waitUntil(
      // Process any queued cover generation requests
      processQueuedGenerations()
    );
  }
});

// Function to process queued generations (placeholder for future implementation)
function processQueuedGenerations() {
  return Promise.resolve();
}

// Listen for messages from the main thread
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});