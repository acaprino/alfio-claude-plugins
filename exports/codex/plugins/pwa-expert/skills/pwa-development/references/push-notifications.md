# Push Notifications

Web Push is the only browser-standard mechanism for delivering server-initiated messages to a user agent regardless of whether the originating site or PWA is currently open. The pipeline involves three actors: the application server (your backend), the push service (Mozilla autopush for Firefox, Google FCM for Chrome, Apple Push Notification service for Safari), and the user agent (the browser or installed PWA). End-to-end encryption guarantees that the push service can route messages without reading their content.

## Standards stack

The Web Push protocol is defined by four interlocking specifications.

- **RFC 8030** is *Generic Event Delivery Using HTTP Push*, jointly authored by Mozilla and Microsoft. It defines how a push service, an application server, and a user agent communicate over HTTP/2.
- **RFC 8291** is *Message Encryption for Web Push*. It defines payload encryption (ECDH on P-256, HKDF, AES-128-GCM) so the push service cannot read message content.
- **RFC 8292** is *Voluntary Application Server Identification (VAPID) for Web Push*. It defines the `vapid` authentication scheme (a JWT signed with ES256 carrying `aud`, `exp` capped at 24 hours, and `sub` as either a `mailto:` or `https:` URI).
- **W3C Push API** defines the browser-side surface: `PushManager`, `PushSubscription`, and the `PushEvent` delivered to a service worker.

## VAPID key generation

VAPID identifies your application server to the push service. You generate the keypair once and store both halves in secrets management.

```bash
npx web-push generate-vapid-keys
```

The command returns an EC P-256 keypair. Both values are base64url-encoded strings. The public key is embedded in the client subscription call; the private key signs the JWT that authenticates each `sendNotification` request from your backend.

Sample output:

```
=======================================
Public Key:
BNs...91-character base64url public key...XYZ

Private Key:
aB...43-character base64url private key...9c
=======================================
```

The public key is 65 bytes uncompressed (1 prefix byte + 32 X + 32 Y), encoded as 87 base64url characters. The private key is 32 bytes, encoded as 43 base64url characters.

Operational guidelines for VAPID key management:

- Generate one keypair per environment (development, staging, production). Never share keys across environments. A leaked development key has limited blast radius if production uses a different one.
- Store the private key in a secrets manager (AWS Secrets Manager, HashiCorp Vault, GCP Secret Manager, or your platform-provided equivalent). Never commit the private key to source control.
- The public key is not secret; ship it to the client as plaintext (in a JSON config file, in an HTML meta tag, or as part of your auth response payload). It is safe to put in client-side JavaScript.
- Rotating VAPID keys invalidates every existing subscription. Plan a re-subscription flow if you ever need to rotate (compromise, employee turnover, key-aging policy). Send the new public key, force the client to re-subscribe, and persist the new endpoint alongside the old one until the user reopens the app.
- The `sub` claim in the JWT can be a `mailto:` URI such as `mailto:dev@acme.com` or an `https:` URI such as `https://acme.com`. Some push services use this contact for abuse reports. Use a monitored inbox.

The JWT that VAPID generates (handled internally by the `web-push` library) carries three claims:

```json
{
  "aud": "https://fcm.googleapis.com",
  "exp": 1748145600,
  "sub": "mailto:dev@acme.com"
}
```

- `aud` is the origin of the push service derived from the subscription endpoint. The JWT is bound to that audience and cannot be replayed against another push service.
- `exp` is the JWT expiration timestamp. RFC 8292 caps it at 24 hours from issuance; most libraries default to 12 hours.
- `sub` is the contact URI described above.

The JWT is signed with ES256 (ECDSA on P-256 with SHA-256) using the private VAPID key. The push service verifies the signature against the public key embedded in the `Crypto-Key` (or, on newer push services, `Authorization`) HTTP header.

## Client subscription

The client subscribes through a registered service worker. The `applicationServerKey` must be passed as a `Uint8Array`, so a small base64url-to-bytes helper is required.

```ts
function urlBase64ToUint8Array(base64: string) {
  const padding = '='.repeat((4 - base64.length % 4) % 4);
  const raw = atob((base64 + padding).replace(/-/g, '+').replace(/_/g, '/'));
  return Uint8Array.from([...raw].map(c => c.charCodeAt(0)));
}

async function subscribe(vapidPublicKey: string) {
  const reg = await navigator.serviceWorker.ready;
  const sub = await reg.pushManager.subscribe({
    userVisibleOnly: true,                                  // mandatory in Chromium
    applicationServerKey: urlBase64ToUint8Array(vapidPublicKey)
  });
  await fetch('/api/subscriptions', { method: 'POST', body: JSON.stringify(sub) });
}
```

The `userVisibleOnly: true` flag is non-negotiable on Chromium. It is a binding commitment that every received push will trigger a user-visible notification. Silent pushes are not supported on the open web; the browser will reject any attempt to subscribe without this flag set to `true`. Firefox enforces the same constraint in practice. Safari follows the same model: every push must be shown to the user, otherwise the subscription can be revoked.

The serialized `PushSubscription` posted to your backend looks roughly like this:

```json
{
  "endpoint": "https://fcm.googleapis.com/fcm/send/abcdef...",
  "expirationTime": null,
  "keys": {
    "p256dh": "BG...base64url...",
    "auth": "k0...base64url..."
  }
}
```

The `endpoint` is the push service URL for that subscription. The `p256dh` key is the user agent's ECDH public key used to encrypt the payload. The `auth` secret is mixed into the HKDF derivation. Store the whole object verbatim; the server library needs every field.

The endpoint origin identifies which push service is in play. A few common patterns to recognize when looking at your stored subscriptions:

- `https://fcm.googleapis.com/fcm/send/...` is Chrome and other Chromium browsers (Firebase Cloud Messaging Web Push).
- `https://updates.push.services.mozilla.com/wpush/v2/...` is Firefox (Mozilla autopush).
- `https://web.push.apple.com/...` is Safari on macOS and iOS (Apple Push Notification service).
- `https://wns2-...notify.windows.com/...` is Edge on Windows when configured to use the native WNS bridge (less common; Edge defaults to FCM via Chromium).

Recommended subscriptions table schema:

```sql
CREATE TABLE push_subscriptions (
  id          BIGSERIAL PRIMARY KEY,
  user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  endpoint    TEXT NOT NULL UNIQUE,
  p256dh      TEXT NOT NULL,
  auth        TEXT NOT NULL,
  ua          TEXT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_used   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ON push_subscriptions(user_id);
```

The `UNIQUE` constraint on `endpoint` avoids duplicate rows when a client re-subscribes with the same key. The `ua` column (user-agent string captured at subscription time) is useful for diagnosing platform-specific delivery problems later.

A common subtle bug: if you persist the `PushSubscription` via `JSON.stringify(subscription)` in the browser and then `JSON.parse(req.body)` on the server, the result is the same shape, but the `keys.p256dh` and `keys.auth` values are stored as base64url strings, not as binary buffers. The `web-push` library accepts both forms; pass the object as is.

## Server (Node + web-push)

The canonical Node implementation uses the `web-push` package, which encapsulates JWT signing, payload encryption, and HTTP/2 delivery.

```ts
import webpush from 'web-push';
webpush.setVapidDetails('mailto:dev@acme.com', VAPID_PUBLIC, VAPID_PRIVATE);

await webpush.sendNotification(subscription, JSON.stringify({
  title: 'New message',
  body: 'Mario: hi!',
  url: '/inbox/42'
}), { TTL: 60, urgency: 'high' });
```

The `TTL` option is the number of seconds the push service may hold the message if the user agent is offline. A short TTL (60 seconds for chat, for example) lets stale events expire. A longer TTL (24 hours or 7 days) is appropriate for non-urgent transactional notifications. If TTL is zero the push service drops the message immediately if the user agent is not currently connected.

The `urgency` option is one of `very-low`, `low`, `normal`, or `high`. The push service uses this hint together with the user agent's battery and connectivity state to decide whether to wake the device. Use `high` for time-sensitive events such as incoming calls or messages, `normal` for most product notifications, and `low` for background updates that can wait.

Production servers must also handle three failure modes returned by `sendNotification`:

- HTTP 410 (Gone): the subscription is dead. Delete the row from your database and stop sending to that endpoint.
- HTTP 404 (Not Found): same treatment as 410.
- HTTP 429 (Too Many Requests): respect the `Retry-After` header.

A naive loop without HTTP 410 cleanup will keep sending to expired endpoints forever and may trigger rate limiting from the push service.

A production-ready fan-out helper looks roughly like this:

```ts
import webpush, { WebPushError } from 'web-push';
import { pool } from './db';

webpush.setVapidDetails(
  process.env.VAPID_SUBJECT!,
  process.env.VAPID_PUBLIC!,
  process.env.VAPID_PRIVATE!
);

export async function pushToUser(userId: number, payload: object, opts = { TTL: 60, urgency: 'normal' as const }) {
  const { rows } = await pool.query(
    'SELECT id, endpoint, p256dh, auth FROM push_subscriptions WHERE user_id = $1',
    [userId]
  );
  const body = JSON.stringify(payload);

  await Promise.all(rows.map(async (row) => {
    const subscription = {
      endpoint: row.endpoint,
      keys: { p256dh: row.p256dh, auth: row.auth }
    };
    try {
      await webpush.sendNotification(subscription, body, opts);
      await pool.query('UPDATE push_subscriptions SET last_used = now() WHERE id = $1', [row.id]);
    } catch (err) {
      if (err instanceof WebPushError && (err.statusCode === 404 || err.statusCode === 410)) {
        // Subscription is gone; remove it
        await pool.query('DELETE FROM push_subscriptions WHERE id = $1', [row.id]);
      } else {
        // Log and continue; do not fail the whole fan-out
        console.error('push send failed', { userId, endpoint: row.endpoint, err });
      }
    }
  }));
}
```

`Promise.all` parallelizes the fan-out, which matters when a single user has 3 to 10 subscriptions across devices. Wrap each `sendNotification` call in its own try/catch so one bad endpoint cannot abort delivery to the others.

The maximum payload size is 4 KB after encryption. The encryption overhead is roughly 100 bytes, so plan for a 3.8 KB ceiling for the JSON body. Larger payloads must be split or replaced with a notification-id pattern: the push delivers a tiny `{ "id": "msg_42" }` payload, and the service worker fetches the full content from your API before calling `showNotification`.

## Service worker handlers

Two events drive the end-user experience: `push` (a notification arrived) and `notificationclick` (the user tapped or activated it).

```ts
self.addEventListener('push', (event) => {
  const data = event.data?.json() ?? {};
  event.waitUntil(self.registration.showNotification(data.title, {
    body: data.body,
    icon: '/icons/icon-192.png',
    badge: '/icons/badge-72.png',           // monochrome on Android
    image: data.image,
    tag: data.tag,
    renotify: true,
    requireInteraction: false,
    silent: false,
    vibrate: [200, 100, 200],
    actions: [
      { action: 'reply', title: 'Reply' },
      { action: 'dismiss', title: 'Dismiss' }
    ],
    data: { url: data.url }
  }));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil((async () => {
    const all = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    const target = event.notification.data?.url ?? '/';
    const existing = all.find(c => new URL(c.url).pathname.startsWith('/'));
    if (existing) { await existing.focus(); existing.navigate(target); }
    else await self.clients.openWindow(target);
  })());
});
```

A few notes on the option set passed to `showNotification`:

- `icon` is the main visual asset. 192×192 PNG works on every platform.
- `badge` is the small monochrome glyph shown in the status bar on Android. It must be a 72×72 PNG with transparency; only the alpha channel is used. Color information is discarded.
- `image` is a large hero image rendered below the title and body on Android.
- `tag` groups notifications. A new notification with the same tag replaces an earlier one in the tray rather than stacking. Useful for incremental progress updates.
- `renotify: true` forces a vibration or sound when a tag-replaced notification arrives. Without it, the replacement is silent.
- `requireInteraction: true` keeps the notification visible until the user dismisses it. Use sparingly; aggressive use causes user revocation.
- `actions` defines extra buttons (reply, mute, archive). Each is identified by an `action` string that surfaces in the `notificationclick` event's `event.action` field. Android shows actions inline; iOS displays them in the long-press menu.
- `data` is an arbitrary object preserved on `event.notification.data` when the user clicks the notification. The example above stashes the deep-link URL there.

The `notificationclick` handler must always call `event.notification.close()` first so the system removes the notification from the tray. The focus-existing pattern via `matchAll` is the recommended UX: if a window of the PWA is already open, focus it and navigate it to the target URL; otherwise open a new window. This avoids the common bug of spawning a fresh tab on every notification tap.

`event.waitUntil` is mandatory in both handlers. Without it the service worker can be terminated before the asynchronous work completes, resulting in dropped notifications or failed navigations.

The `notificationclose` event is also available and fires when the user dismisses a notification without clicking it (swipe-to-dismiss on Android, the X button on desktop, swipe on iOS Notification Center). Use it for analytics or to mark the corresponding row as read:

```ts
self.addEventListener('notificationclose', (event) => {
  const data = event.notification.data ?? {};
  event.waitUntil(fetch('/api/notifications/dismissed', {
    method: 'POST',
    body: JSON.stringify({ id: data.id, at: Date.now() })
  }));
});
```

A `pushsubscriptionchange` event fires when the push service invalidates and reissues a subscription. This can happen for several reasons: a Chrome reinstall, a Firefox profile reset, an iOS PWA uninstall and reinstall, or the push service rotating its internal identifiers. The event has two interesting fields, `event.oldSubscription` and `event.newSubscription`, although both may be absent on some browsers. The defensive pattern is to re-subscribe and notify the server:

```ts
self.addEventListener('pushsubscriptionchange', (event) => {
  event.waitUntil((async () => {
    const reg = await self.registration;
    const sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: VAPID_PUBLIC_BYTES
    });
    await fetch('/api/subscriptions/refresh', {
      method: 'POST',
      body: JSON.stringify({
        old: event.oldSubscription ?? null,
        new: sub
      })
    });
  })());
});
```

The server uses the `old` field to find the existing row by endpoint and update it to the new endpoint and keys. This pattern avoids creating orphan rows that would later be cleaned up by HTTP 410 handling.

Reception flow timing matters in two situations. First, when the device is asleep and the push arrives over a push service that uses doze-friendly delivery, the latency can be several seconds. Second, when the user agent is offline, the push service buffers messages up to the TTL and delivers them on reconnection, in delivery-time order. Do not rely on push event timing for time-of-day logic; carry the canonical timestamp in the payload.

## Declarative Web Push (Safari 18.4+)

Apple shipped Declarative Web Push in Safari 18.4 for iOS and iPadOS on 31 March 2025. The WebKit team explained the motivation in their announcement:

> "Compared to the original Safari Push, which used a declarative model, requiring a Service Worker introduces added complexity for web developers. It also demands more from the system, consuming additional battery and CPU resources, and opens the door to potential misuse."

In the declarative model the application server delivers a JSON payload that conforms to the WebKit notification schema. Safari renders it directly from a system process. No service worker wakes up, no JavaScript executes on the device for the display step. The trade-off is loss of flexibility: you cannot fetch additional data, run logic, or call `clients.matchAll` from a payload that never instantiated a worker.

The payload looks roughly like this:

```json
{
  "web_push": 8030,
  "notification": {
    "title": "New message",
    "body": "Mario: hi!",
    "navigate": "https://acme.com/inbox/42",
    "app_badge": "3"
  }
}
```

Key fields:

- `web_push: 8030` is the schema version marker that tells Safari to render declaratively.
- `notification.navigate` is the URL opened when the user taps the notification. No `notificationclick` handler is needed.
- `notification.app_badge` updates the app icon badge atomically with the notification display.

The benefits are concrete. Battery and CPU draw drop because the system never spins up a JavaScript runtime for the display path. The abuse vector closes because a malicious site cannot use the push channel to run arbitrary code in the background. The declarative payload still travels over the same RFC 8030 transport and is encrypted under RFC 8291, so the server side of your stack does not need to change other than emitting the new JSON shape when targeting Safari.

A hybrid approach is also possible: emit the declarative payload as the body and keep a service worker registered to handle non-Safari push for the same subscription. Chromium and Firefox ignore the declarative schema and route the push to the `push` event in the worker as usual.

Server-side branching strategy when supporting both models:

```ts
function isAppleEndpoint(endpoint: string) {
  return endpoint.startsWith('https://web.push.apple.com/');
}

function buildPayload(notification: NotificationData, endpoint: string) {
  if (isAppleEndpoint(endpoint)) {
    // Declarative Web Push payload for Safari 18.4+
    return JSON.stringify({
      web_push: 8030,
      notification: {
        title: notification.title,
        body: notification.body,
        navigate: notification.url,
        app_badge: notification.unreadCount?.toString()
      }
    });
  }
  // Imperative payload for Chromium and Firefox; the SW push handler renders it
  return JSON.stringify({
    title: notification.title,
    body: notification.body,
    url: notification.url,
    image: notification.image
  });
}
```

Note that older iOS versions (16.4 to 18.3) running a non-declarative Safari still route to the service worker's `push` handler, so keep the imperative handler registered. The hybrid branch only changes the body shape; the transport, encryption, and delivery contract are unchanged.

## iOS-specific gotchas

Web Push on iOS is functional but constrained. Four constraints regularly trip up teams shipping their first PWA.

- **Install requirement.** Push works only if the user added the PWA to the Home Screen and it opens in `display: standalone`. Pushes will not be delivered to a tab in the system Safari browser. The `Notification.requestPermission()` call returns immediately with `denied` outside of an installed standalone PWA on iOS.
- **User gesture.** The permission prompt requires a user gesture (a tap on a button). Calling `Notification.requestPermission()` from page load or from a timer is rejected silently. This is binding on iOS; the same code may technically work on Chromium with permission policy, but you must architect the iOS path around an explicit "Enable notifications" tap.
- **Silent subscription loss.** Subscriptions can disappear silently after long periods of inactivity, after iOS upgrades, or after the user clears Safari data. The defensive pattern is to call `pushManager.getSubscription()` on every app startup and re-subscribe if the result is `null`. Re-subscribing with the same VAPID public key may return a fresh endpoint; treat each call as a fresh row in your server-side subscription store and clean up the old one when the server responds 410 Gone to the prior endpoint.
- **No remote inspection.** Safari iOS is not inspectable for Home Screen Web Apps. The standard Safari Web Inspector remote-debug surface works only for tabs in the Safari browser. A standalone PWA on the Home Screen is a separate process container with no debug bridge. Workarounds: ship an in-app diagnostics panel that surfaces logs, register a service worker `message` handler that posts internal state to a connected DevTools client on Mac (only viable in development), or embed Eruda or a similar in-page console behind a hidden tap sequence.

Defensive subscription-check helper to paste at app startup:

```ts
async function ensurePushSubscription(vapidPublicKey: string) {
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
    return null; // Push not supported on this user agent
  }
  const reg = await navigator.serviceWorker.ready;
  let sub = await reg.pushManager.getSubscription();
  if (!sub) {
    // Was previously subscribed and lost the subscription; or never subscribed
    const permission = Notification.permission;
    if (permission === 'denied') return null;
    if (permission === 'default') return null; // Wait for the user-gesture path
    sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(vapidPublicKey)
    });
    await fetch('/api/subscriptions', { method: 'POST', body: JSON.stringify(sub) });
  }
  return sub;
}
```

Call `ensurePushSubscription` on every app startup. On iOS this regenerates a fresh endpoint after a silent loss; on Chromium it is a no-op when the subscription is still valid.

## Debugging Web Push end-to-end

Push failures are notoriously hard to diagnose because the pipeline crosses three independent process boundaries (your backend, the push service, the user agent). The recommended troubleshooting order is from the inside out.

**On the server.** Wrap every `sendNotification` call so the full error is logged with subscription metadata:

```ts
try {
  await webpush.sendNotification(subscription, body, opts);
} catch (err) {
  if (err instanceof WebPushError) {
    console.error('webpush error', {
      statusCode: err.statusCode,
      headers: err.headers,
      body: err.body,
      endpoint: subscription.endpoint.slice(0, 80)
    });
  }
  throw err;
}
```

Common status codes:

- 201 Created: the message was accepted by the push service.
- 400 Bad Request: malformed payload or headers. Usually a VAPID JWT issue.
- 401 Unauthorized: invalid VAPID JWT (wrong key, expired `exp`, wrong `aud` for the endpoint).
- 403 Forbidden: VAPID key not authorized for this endpoint. Often happens after key rotation without re-subscription.
- 404 Not Found / 410 Gone: subscription is dead, delete the row.
- 413 Payload Too Large: encrypted payload exceeded 4 KB.
- 429 Too Many Requests: respect `Retry-After`.

**In Chrome / Edge DevTools.** Open the Application panel, click Service Workers, find the registered worker, and use the "Push" textarea to inject a synthetic payload as a JSON string. This bypasses the server and the push service entirely, exercising only your `push` handler. Useful for iterating on the showNotification options without round-tripping to your backend.

**On Firefox.** Open `about:debugging` then This Firefox, find the worker, and click Push to send a synthetic event. Same purpose as the Chrome flow.

**On Safari.** No equivalent injection UI exists. The closest substitute is to call `self.registration.showNotification(...)` directly from the page or worker code under a debug flag to verify the rendering pipeline. Actual end-to-end push must be tested through a real APNS round-trip; there is no offline simulator.

**Field diagnostics.** Add a `/api/push/diag` endpoint that returns the user's stored subscription endpoint (truncated), the user-agent string captured at subscription time, the last delivery attempt timestamp, and the last error code if any. Surface this in your admin UI for support tickets.

**Frequent failure modes to check first**:

- VAPID `sub` claim is wrong (must be a `mailto:` or `https:` URI).
- Public key in the client subscribe call does not match the public key in `setVapidDetails`.
- Service worker file is served with a long `Cache-Control` and an old version is still controlling the page.
- `userVisibleOnly: true` is missing from the subscribe options.
- HTTPS is not enforced; Push only works over a secure context (`localhost` excepted in development).
- On iOS, the PWA is being tested in Safari rather than as an installed Home Screen app.

## Badge API

The Badge API sets the small numeric badge on the app icon visible from the home screen, launcher, dock, or taskbar. It is independent from notification delivery and can be called from either the page or the service worker.

```ts
await navigator.setAppBadge(unreadCount); // setAppBadge / clearAppBadge
```

Pass a number to display a counter, omit the argument to display a dot, or call `clearAppBadge()` to remove it.

```ts
// Show a count
await navigator.setAppBadge(7);

// Show a flag (no number)
await navigator.setAppBadge();

// Remove the badge
await navigator.clearAppBadge();
```

Support matrix:

- iOS 16.4+ on installed Home Screen PWAs.
- Android Chrome on installed WebAPKs.
- Desktop Chrome and Edge on installed PWAs.

The badge persists across app closes and reboots. Always clear it when the user has reviewed the underlying state (opened the inbox, dismissed the alerts panel, marked notifications read) rather than relying on the next notification to overwrite it.

Combined with Declarative Web Push on Safari, the `app_badge` field in the notification payload lets the server set the badge atomically with the notification display, avoiding the round-trip a service worker would otherwise need.

Feature detection is straightforward:

```ts
if ('setAppBadge' in navigator) {
  await navigator.setAppBadge(unreadCount);
}
```

Calling `setAppBadge` on an unsupported user agent throws. Always guard with the feature-detection check. On user agents where the PWA is running as an in-browser tab (not installed), `setAppBadge` may resolve without applying any visible change; this is expected and the call is harmless.

A common architectural choice is to centralize badge updates in a single helper invoked from three places: after a successful push reception in the `push` handler, when the page mounts or refocuses (using the `visibilitychange` event), and on explicit user actions that mark items read.

```ts
async function syncBadge() {
  if (!('setAppBadge' in navigator)) return;
  const res = await fetch('/api/notifications/unread-count');
  const { count } = await res.json();
  if (count > 0) await navigator.setAppBadge(count);
  else await navigator.clearAppBadge();
}

document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible') syncBadge();
});
```

This eliminates drift between the server-side unread state and the client-displayed badge, which would otherwise accumulate over weeks of use.

## Official sources on the Web Push protocol

**IETF specifications (RFCs)**

- **RFC 8030**, *Generic Event Delivery Using HTTP Push*. The transport layer: how the push service, the application server, and the user agent communicate over HTTP/2. https://datatracker.ietf.org/doc/html/rfc8030
- **RFC 8291**, *Message Encryption for Web Push*. End-to-end payload encryption (ECDH P-256, HKDF, AES-128-GCM); the push service cannot read the payload. https://datatracker.ietf.org/doc/html/rfc8291
- **RFC 8292**, *Voluntary Application Server Identification (VAPID) for Web Push*. The JWT ES256 authentication scheme with claims `aud`, `exp` (capped at 24 hours), and `sub`. https://datatracker.ietf.org/doc/html/rfc8292
- **RFC 8188**, *Encrypted Content-Encoding for HTTP* (`aes128gcm`). The content-encoding used by RFC 8291. https://datatracker.ietf.org/doc/html/rfc8188
- **RFC 7515**, *JSON Web Signature*. https://datatracker.ietf.org/doc/html/rfc7515
- **RFC 7519**, *JSON Web Token*. The foundation for VAPID. https://datatracker.ietf.org/doc/html/rfc7519

**W3C / WHATWG specifications**

- **W3C Push API** (Working Draft). The browser-side interface: `PushManager`, `PushSubscription`, `PushEvent`. https://www.w3.org/TR/push-api/
- **WHATWG Notifications API** (Living Standard). `Notification`, `showNotification()`, `notificationclick`. https://notifications.spec.whatwg.org/
- **W3C Service Workers**. The execution context for the push handler. https://www.w3.org/TR/service-workers/

**Reference documentation**

- MDN, Push API: https://developer.mozilla.org/en-US/docs/Web/API/Push_API
- MDN, Notifications API: https://developer.mozilla.org/en-US/docs/Web/API/Notifications_API
- web.dev, Notifications overview: https://web.dev/explore/notifications
- Chrome for Developers, Web Push: https://developer.chrome.com/docs/capabilities/web-push

**Push service implementers**

- **Mozilla autopush** (Firefox push service, the open-source reference implementation): https://mozilla-services.github.io/autopush-rs/ and https://github.com/mozilla-services/autopush-rs
- **Chrome FCM Web Push** (also accepts standard VAPID subscriptions, not only proprietary ones): https://firebase.google.com/docs/cloud-messaging/js/client
- **Apple, Sending Web Push notifications in web apps and browsers** (iOS 16.4+): https://developer.apple.com/documentation/usernotifications/sending_web_push_notifications_in_web_apps_and_browsers

**WebKit implementation and Declarative Web Push**

- Web Push for Web Apps on iOS and iPadOS (16.4): https://webkit.org/blog/13878/web-push-for-web-apps-on-ios-and-ipados/
- Meet Web Push (WWDC22): https://developer.apple.com/videos/play/wwdc2022/10098/
- Meet Declarative Web Push (Safari 18.4): https://webkit.org/blog/16535/meet-declarative-web-push/

**Reference server libraries** (useful for reading the protocol in action)

- `web-push` (Node.js): https://github.com/web-push-libs/web-push
- `pywebpush` (Python): https://github.com/web-push-libs/pywebpush
- `webpush-go` (Go): https://github.com/SherClockHolmes/webpush-go
- `webpush-java` (Java): https://github.com/web-push-libs/webpush-java

**Recommended reading order**

1. RFC 8030 (transport).
2. W3C Push API and MDN (browser side).
3. RFC 8292 (VAPID, server authentication).
4. RFC 8291 and RFC 8188 (payload encryption).
5. Source of the `web-push` Node library or `pywebpush` to see how the pieces fit together in practice.

After completing the reading list above, build a minimal end-to-end harness: a static page that subscribes against a local Express server, a `web-push` Node script that fires a test notification, and a service worker that renders it. This three-file harness is the fastest way to internalize the protocol behavior. Once it works on Chromium, port the static page to a deployable HTTPS origin (Cloudflare Pages, Vercel, Netlify) and re-test on Firefox, Safari macOS, Android Chrome, and an installed iOS PWA. Each platform surface will reveal a different quirk; document the deltas as you go.

The single most common production incident with Web Push is silent subscription loss combined with no monitoring on the server-side delivery success rate. Emit a `push_send_total` counter labelled by status code and a `push_subscription_active` gauge labelled by platform. Page on a 24-hour drop of more than 10 percent in either metric.

A complementary signal is the ratio of `notificationclick` events received back at your analytics endpoint divided by `sendNotification` accepted responses. A healthy chat or messaging product typically lands in the 25 to 60 percent range; transactional alerts hover around 5 to 15 percent. Sustained values below 1 percent indicate that notifications are reaching the device but are visually buried or filtered by the operating system.

The most common causes for collapsed click-through rates are an over-permissive notification cadence (users have started ignoring you) or a missing icon and badge asset (notifications render as bare text and look like spam). Audit the asset paths in your `showNotification` call and confirm both `icon` and `badge` resolve with a 200 on the production origin.
