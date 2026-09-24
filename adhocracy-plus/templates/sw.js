// Minimal service worker: makes the platform installable as a PWA and
// speeds up repeat visits by cache-first serving of static assets
// (CSS/JS/images/fonts). Deliberately does NOT cache or serve HTML pages
// offline -- every page here embeds a CSRF token and often
// authenticated, per-user content, and serving a stale cached page would
// risk submitting forms with an expired token or showing another user's
// state. Navigation requests always go to the network.

const CACHE_NAME = 'a4-candy-static-v1';

self.addEventListener('install', (event) => {
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => Promise.all(
            keys.filter((key) => key !== CACHE_NAME)
                .map((key) => caches.delete(key))
        ))
    );
    self.clients.claim();
});

self.addEventListener('fetch', (event) => {
    const request = event.request;

    if (request.method !== 'GET') {
        return;
    }

    const url = new URL(request.url);
    const isStaticAsset = url.origin === self.location.origin
        && url.pathname.startsWith('/static/');

    if (!isStaticAsset) {
        // Not a static asset (a page navigation, an API call, a
        // cross-origin request): always go to the network.
        return;
    }

    event.respondWith(
        caches.open(CACHE_NAME).then((cache) => cache.match(request).then(
            (cached) => cached || fetch(request).then((response) => {
                if (response.ok) {
                    cache.put(request, response.clone());
                }
                return response;
            })
        ))
    );
});

// Web Push notifications (see apps/pushnotifications). The push
// message body is the small flat JSON built by
// apps.pushnotifications.engine.build_payload -- title/body/url only,
// never content that wasn't already safe to send unencrypted-at-rest
// through the browser's push service.
self.addEventListener('push', (event) => {
    if (!event.data) {
        return;
    }
    let payload;
    try {
        payload = event.data.json();
    } catch (err) {
        return;
    }
    event.waitUntil(
        self.registration.showNotification(payload.title || 'Update', {
            body: payload.body || '',
            data: { url: payload.url || '/' },
        })
    );
});

self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    const url = event.notification.data && event.notification.data.url;
    if (url) {
        event.waitUntil(clients.openWindow(url));
    }
});
