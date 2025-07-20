const CACHE_NAME = 'huematch-v1';
const STATIC_CACHE_NAME = 'huematch-static-v1';
const DYNAMIC_CACHE_NAME = 'huematch-dynamic-v1';

// Assets to cache immediately
const STATIC_ASSETS = [
  '/',
  '/manifest.json',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png',
  // Add more critical assets here
];

// Assets to cache on first access
const CACHE_PATTERNS = [
  /^https:\/\/fonts\.(googleapis|gstatic)\.com\/.*/,
  /^https:\/\/images\.pexels\.com\/.*/,
  /^https:\/\/images\.unsplash\.com\/.*/,
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('Service Worker: Installing...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE_NAME)
      .then((cache) => {
        console.log('Service Worker: Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('Service Worker: Static assets cached');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('Service Worker: Failed to cache static assets', error);
      })
  );
});

// Activate event - cleanup old caches
self.addEventListener('activate', (event) => {
  console.log('Service Worker: Activating...');
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== STATIC_CACHE_NAME && 
              cacheName !== DYNAMIC_CACHE_NAME &&
              cacheName !== CACHE_NAME) {
            console.log('Service Worker: Deleting old cache', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('Service Worker: Activated');
      return self.clients.claim();
    })
  );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip chrome-extension requests
  if (url.protocol === 'chrome-extension:') {
    return;
  }

  // Handle API requests with network-first strategy
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirst(request));
    return;
  }

  // Handle navigation requests
  if (request.mode === 'navigate') {
    event.respondWith(navigateHandler(request));
    return;
  }

  // Handle static assets with cache-first strategy
  if (isStaticAsset(request)) {
    event.respondWith(cacheFirst(request));
    return;
  }

  // Handle images with stale-while-revalidate
  if (request.destination === 'image') {
    event.respondWith(staleWhileRevalidate(request));
    return;
  }

  // Default: try cache first, then network
  event.respondWith(cacheFirst(request));
});

// Cache-first strategy
async function cacheFirst(request) {
  try {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      console.log('Service Worker: Serving from cache', request.url);
      return cachedResponse;
    }

    const networkResponse = await fetch(request);
    
    if (networkResponse.ok && shouldCache(request)) {
      const cache = await caches.open(DYNAMIC_CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    console.error('Service Worker: Cache-first failed', error);
    
    // Return offline fallback for navigation requests
    if (request.mode === 'navigate') {
      return caches.match('/offline.html') || new Response('Offline', { status: 503 });
    }
    
    throw error;
  }
}

// Network-first strategy for API calls
async function networkFirst(request) {
  try {
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      const cache = await caches.open(DYNAMIC_CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.log('Service Worker: Network failed, trying cache', request.url);
    
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Return error response for failed API calls
    return new Response(JSON.stringify({ 
      error: 'Network error', 
      offline: true 
    }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

// Stale-while-revalidate for images
async function staleWhileRevalidate(request) {
  const cachedResponse = await caches.match(request);
  
  const networkResponsePromise = fetch(request).then(async (networkResponse) => {
    if (networkResponse.ok && shouldCache(request)) {
      const cache = await caches.open(DYNAMIC_CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  }).catch(() => null);

  return cachedResponse || networkResponsePromise;
}

// Navigation handler
async function navigateHandler(request) {
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      return networkResponse;
    }
  } catch (error) {
    console.log('Service Worker: Navigation network failed');
  }

  // Try to serve from cache
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }

  // Fallback to root page
  const rootPage = await caches.match('/');
  return rootPage || new Response('Offline', { status: 503 });
}

// Helper functions
function isStaticAsset(request) {
  const url = new URL(request.url);
  return /\.(js|css|woff2|woff|ttf|otf)$/.test(url.pathname);
}

function shouldCache(request) {
  const url = new URL(request.url);
  
  // Don't cache very large files
  if (request.headers.get('content-length') > 5 * 1024 * 1024) {
    return false;
  }
  
  // Cache images from supported services
  if (CACHE_PATTERNS.some(pattern => pattern.test(request.url))) {
    return true;
  }
  
  // Cache same-origin requests
  return url.origin === self.location.origin;
}

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }
});

async function doBackgroundSync() {
  console.log('Service Worker: Background sync triggered');
  // Implement background sync logic here
  // For example, sync offline color analysis requests
}

// Push notifications
self.addEventListener('push', (event) => {
  const options = {
    body: event.data ? event.data.text() : 'New update available!',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/icon-72x72.png',
    vibrate: [200, 100, 200],
    data: {
      url: '/'
    }
  };

  event.waitUntil(
    self.registration.showNotification('HueMatch', options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  event.waitUntil(
    clients.openWindow(event.notification.data.url || '/')
  );
});
