# Project Fugu Capabilities

Project Fugu is the cross-vendor effort, led by Google with participation
from Microsoft and Intel, to bring native-grade capabilities to the web
platform. As of early 2026, Thomas Steiner's Chrome for Developers post
"Is Project Fugu done?" states the canonical count: "Here are the 55
shipped APIs, in order of least to most recently shipped". Most of the
headline capabilities ship in Chromium first, with Firefox and Safari
trailing or declining on hardware-access surfaces. The matrix below
captures the production reality for the 14 APIs that matter most when
scoping a PWA in 2026.

## API matrix

| API | Chrome/Edge | Firefox | Safari |
|---|---|---|---|
| File System Access | Yes (desktop) | No | No |
| Web Share | Yes | Partial | Yes |
| Web Share Target | Yes (Android, desktop) | No | No |
| Contact Picker | Yes (Android) | No | No |
| Web Bluetooth | Yes (desktop, Android) | No | No |
| Web USB / Serial / HID | Yes (desktop) | No | No |
| WebNFC | Yes (Android) | No | No |
| WebRTC | Yes | Yes | Yes |
| Payment Request | Yes | Partial | Yes |
| WebAuthn / Passkeys | Yes | Yes | Yes |
| Geolocation | Yes | Yes | Yes |
| Screen Capture | Yes | Yes | Yes (limited on iOS) |
| Web Speech (recognition) | Yes (Chrome) | Behind a pref | Partial |
| File Handlers (manifest) | Yes (desktop) | No | No |

Notes on the matrix:

- "Yes (desktop)" means the API is available on Chromium desktop builds
  (Chrome, Edge) but not on Chrome for Android or any mobile browser
  engine.
- "Yes (Android)" means the API ships on Android Chrome but not on
  Chromium desktop. WebNFC and Contact Picker fall in this category
  because they rely on Android hardware integrations.
- "Partial" for Firefox Web Share means the call surface exists but file
  payloads and some metadata fields are restricted compared to Chromium.
- "Partial" for Safari Web Speech means SpeechSynthesis works broadly,
  while SpeechRecognition is limited and gated.
- "Limited on iOS" for Screen Capture reflects that iOS Safari supports
  `getDisplayMedia` in a constrained form, with no support for surface
  selection and stricter user gestures.
- WebRTC, WebAuthn / Passkeys, Geolocation, and Screen Capture are the
  four rows where all three browser families ship a usable implementation.
  Treat anything outside this group as Chromium-first and plan a degraded
  path for WebKit and Gecko.

The interoperability gap is not random. Hardware-access APIs (Bluetooth,
USB, Serial, HID, NFC) and filesystem-access APIs (File System Access,
File Handlers) are concentrated on Chromium. Apple and Mozilla have
raised privacy and fingerprinting objections to these surfaces and have
publicly declined to implement most of them. Plan accordingly: feature
detect at runtime and either degrade gracefully or surface a non-blocking
notice when the user is on a non-Chromium engine.

### Per-API quick notes

A short orientation for each row of the matrix, focused on what a PWA
team needs to decide before adopting the API.

- File System Access. Lets a Chromium desktop user pick a file or
  directory and grants the site a handle that persists across sessions
  (with IndexedDB-backed handle storage). Use it for editors,
  IDE-style tools, and any flow that benefits from saving back to the
  user's chosen location instead of forcing a download. Mobile users
  and Safari users will need a fallback that uses an `<input type="file">`
  picker and a download for write-back.
- Web Share. Covered in detail below. The one universally adoptable
  Fugu API on the chart.
- Web Share Target. The receiving end of the share contract. Declared
  in the manifest with a `share_target` member. Lets a PWA appear in
  the system share sheet on Android and on Chromium desktop. There is
  no Safari implementation, so iOS PWAs cannot be a share target.
- Contact Picker. Returns selected contacts to the page via
  `navigator.contacts.select`. Android Chrome only. Useful for invite
  flows. Fall back to a manual entry form on every other platform.
- Web Bluetooth. GATT-only on Chromium. Requires a user gesture, a
  filter on services or names, and HTTPS. Apple and Mozilla have
  declined to implement.
- Web USB, Web Serial, Web HID. Three sibling APIs for low-level device
  IO on Chromium. Each has its own permission grant. The new
  `forget()` methods (see the 2025-2026 trends section) let a site
  release a previously granted device.
- WebNFC. Read-only and write-only NDEF records on Android Chrome.
  Niche but the only way to interact with passive NFC tags from a web
  page.
- WebRTC. Interoperable across all three engine families. Mainly
  relevant to PWAs that include video calling, screen sharing, or
  peer-to-peer data channels.
- Payment Request. Standard payment-sheet surface. Apple Pay and Google
  Pay both ride on this API on their respective platforms. Use it
  instead of bespoke checkout flows when a tokenized network payment is
  the goal.
- WebAuthn / Passkeys. Covered in detail below. The default
  authentication choice for a modern PWA in 2026.
- Geolocation. Universal. Requires a user-gesture-triggered permission
  prompt on iOS.
- Screen Capture. `navigator.mediaDevices.getDisplayMedia`. Works
  across engines but with platform-specific constraints around surface
  selection.
- Web Speech (recognition). `SpeechRecognition` (`webkitSpeechRecognition`
  on Safari). Chrome routes to a Google service; Firefox and Safari
  use platform speech. Synthesis is universal; recognition is not.
- File Handlers. Manifest declaration that lets a PWA register as a
  default opener for one or more MIME types. Chromium desktop only.
  Files arrive at the launched window via `window.launchQueue` (see
  `manifest.md` for the launch handler details).

## Web Share

The Web Share API hands a payload (text, URL, files) to the operating
system share sheet. It is the highest-yield Fugu API to adopt in 2026
because it works on all three engine families, requires a user gesture,
and avoids any custom UI work for the share target picker.

```ts
await navigator.share({
  title: 'Acme', text: 'Look at this',
  url: 'https://acme.com/x',
  files: [new File([blob], 'image.png', { type: 'image/png' })]
});
```

Use `navigator.canShare(data)` for feature detection. The check is
important when the payload includes files, because Firefox in particular
accepts a share call but rejects file payloads. The pattern:

```ts
const data = {
  title: 'Acme',
  text: 'Look at this',
  url: 'https://acme.com/x',
  files: [imageFile]
};

if (navigator.canShare && navigator.canShare(data)) {
  await navigator.share(data);
} else if (navigator.share) {
  await navigator.share({ title: data.title, text: data.text, url: data.url });
} else {
  showFallbackShareUi(data);
}
```

Three pitfalls worth flagging:

1. The call must be inside the same task that received the user gesture.
   Awaiting other promises before `navigator.share` can break the gesture
   chain on Safari. If a file needs to be generated before sharing,
   generate it first inside the click handler, then await `navigator.share`
   without any intervening I/O.
2. The `url` field is validated against the document origin on some
   engines. Pass an absolute URL on the same origin as the page or expect
   a `TypeError` on stricter engines.
3. `navigator.share` rejects with an `AbortError` when the user dismisses
   the share sheet. Treat this as a normal outcome, not a bug. The
   recommended pattern is to swallow `AbortError` and rethrow anything else.

```ts
try {
  await navigator.share(data);
} catch (err) {
  if ((err as DOMException).name !== 'AbortError') {
    throw err;
  }
}
```

## WebAuthn / Passkeys

WebAuthn with passkeys is the second universally shipped Fugu surface
and the single best replacement for password-based login in a PWA. All
three engine families support synced passkeys via the platform
authenticator (iCloud Keychain on Apple, Google Password Manager on
Android and Chrome, Windows Hello on Edge).

```ts
const cred = await navigator.credentials.create({
  publicKey: {
    challenge: serverChallenge,
    rp: { id: 'acme.com', name: 'Acme' },
    user: { id: userId, name: 'mario@acme.com', displayName: 'Mario' },
    pubKeyCredParams: [{ type: 'public-key', alg: -7 }, { type: 'public-key', alg: -257 }],
    authenticatorSelection: { residentKey: 'required', userVerification: 'preferred' },
    attestation: 'none'
  }
});
```

Field-by-field rationale:

- `challenge`: server-issued, single-use, at least 16 bytes of
  cryptographic randomness. Bind it to the session and reject any
  registration whose challenge has already been consumed.
- `rp.id`: the registrable domain. Subdomains can use the apex domain to
  share credentials, but the apex must match exactly. Localhost is
  allowed as an exception during development.
- `user.id`: an opaque, persistent identifier. Never reuse an email or a
  primary-key integer here; it leaks into the authenticator UI and into
  any synced credential metadata.
- `pubKeyCredParams`: ES256 (alg `-7`) is the default for platform
  authenticators. RS256 (alg `-257`) is included for compatibility with
  older Windows Hello stacks. Listing both is the safe default.
- `authenticatorSelection.residentKey: 'required'`: requests a passkey
  (discoverable credential), which enables usernameless sign-in on
  subsequent logins.
- `authenticatorSelection.userVerification: 'preferred'`: asks for
  biometric or PIN where available, but does not fail if the device
  lacks user verification.
- `attestation: 'none'`: do not request an attestation statement unless
  the deployment specifically needs to verify the authenticator model.
  Attestation creates a privacy signal and reduces user-agent
  compatibility.

For sign-in, mirror this with `navigator.credentials.get({ publicKey: { challenge, rpId, userVerification: 'preferred' } })`
and let the platform surface the available passkeys. Conditional UI via
the `mediation: 'conditional'` flag is supported on Chromium, Safari 16+,
and Firefox 119+ and is the recommended pattern for autofill-style sign-in
inside a form.

Implementation notes worth flagging:

- The server must validate the `clientDataJSON.origin`, the
  `authenticatorData.rpIdHash`, the signature, and the counter against
  the stored counter. Drop a registration or assertion that fails any of
  these checks.
- Treat `attestation: 'none'` as truthful: the server cannot rely on the
  AAGUID or attestation statement to enforce policies about which
  authenticator was used.
- Sync conflict is a real failure mode. A passkey created on one device
  may not appear instantly on another if the user's sync provider is
  slow. Build a "use another device" recovery branch (cross-device
  WebAuthn over BLE / hybrid transport) for first-time logins.

## References to track

- Fugu API Tracker: fugu-tracker.web.app. Per-API status, shipping
  version, and links to the originating intent-to-implement threads.
  Filter by "Shipped" to see the production-ready set.
- Chrome Capabilities status: developer.chrome.com/docs/capabilities/status.
  Chrome's curated capabilities page, kept in sync with Origin Trials
  and Feature Status entries.

Both pages move. Re-check before quoting a status in a deliverable.

## 2025-2026 trends folded in

The Fugu matrix is a snapshot. The trends below explain where the matrix
is moving and which assumptions need rechecking before relying on a
capability in production.

### iOS 18.4 (March 31, 2025)

Safari 18.4 was the largest single-release expansion of PWA functionality
on iOS since the Home Screen Web Apps debut. WebKit shipped 84 new
features in this release. The PWA-relevant set:

- Declarative Web Push: the server sends a JSON payload conforming to
  the notification schema, and Safari renders the notification without
  waking a service worker. This reduces battery and CPU cost on iOS and
  closes a long-standing misuse vector. See `push-notifications.md` for
  the payload schema.
- Wake Lock fix for Home Screen Web Apps: the WebKit release notes
  explicitly call this out as "Fixed Screen Wake Lock API for Home
  Screen Web Apps. (108573133)". Before 18.4 the wake lock was silently
  ignored when the PWA ran from the Home Screen.
- `webkitdirectory`: directory upload via
  `<input type="file" webkitdirectory>` now works on iOS, useful for any
  PWA that needs bulk file ingestion.
- Image Capture API: the basic capture surface lands on WebKit, enabling
  photo capture flows that previously required Cordova or Capacitor.

The cumulative effect: a PWA installed to the iOS Home Screen in 2026
has materially more capabilities than one installed in 2024. Re-test any
feature that was previously gated behind a "no iOS" branch.

### iOS 26

In iOS 26, every site added to the Home Screen opens as a web app by
default. This is an implicit opt-in to standalone mode. The user no
longer has to confirm a separate web-app experience; the system treats
the Home Screen icon as a PWA launcher unconditionally.

The practical consequences:

- A site with no manifest still benefits from the standalone launch but
  inherits Safari defaults for theme color and status bar. A complete
  manifest is now essentially required to control the launch experience.
- Cold-launch performance becomes more visible because users will see
  the PWA launch path more often than the Safari tab path.
- Sites that previously coexisted with Safari (no install ceremony)
  should validate their offline behavior, because the user is more
  likely to be on a Home Screen launch when the network is poor.

### DMA EU

Apple kept PWAs in the EU after the March 2024 reversal. The brief
timeline: in early 2024, Apple announced that Home Screen Web Apps
would be removed in the EU as part of the iOS 17.4 DMA response. After
pressure from the European Commission and from Open Web Advocacy, Apple
reversed the decision and PWAs remained available in the EU.

In iOS 18.2 Apple shipped BrowserEngineKit, the API that in theory
allows third-party browsers in the EU to use a non-WebKit engine. As of
early 2026 no browser vendor has shipped a non-WebKit iOS browser
through this API. The practical reality on iOS in the EU is unchanged:
every browser still rides on WebKit, and Web Push still requires
installation to the Home Screen.

### Project Fugu progress

The headline numbers from Steiner's "Is Project Fugu done?" post:
exactly 55 APIs shipped, with the post listing them "in order of least
to most recently shipped". Two themes inside that count:

- `navigator.storage.getDirectory()` (the entry point to the Origin
  Private File System) is the fastest-growing surface, with use cases
  expanding into SQLite-on-OPFS, large media editing, and offline-first
  databases. See `storage-persistence.md` for the OPFS deep-dive.
- New `forget()` and permission-revoke methods are arriving for HID,
  USB, and Serial. These let a site programmatically release a device
  grant the user previously made, which is essential for "log out"
  flows in apps that interact with hardware. Expect Chromium-only
  support throughout 2026.

The `forget()` shape is consistent across the three device APIs:

```ts
const devices = await navigator.hid.getDevices();
for (const device of devices) {
  await device.forget();
}
```

Calling `forget()` revokes the grant and removes the device from the
list returned by the next `getDevices()` call. The user will see the
permission prompt again on the next access attempt.

### Baseline web feature

The web.dev/baseline initiative continues to expand its coverage.
Baseline assigns an interoperability badge to APIs that are "widely
available" across all major browsers. Two practical uses inside a PWA
codebase:

- Production gating: only ship a feature path that uses an API in
  Baseline "widely available" without a fallback. Anything below that
  bar needs a feature-detection branch.
- Documentation: link the Baseline badge in user-facing changelogs and
  developer docs to reduce the back-and-forth on "does this work in
  Safari?".

### INP 200ms threshold

The INP threshold of 200ms is confirmed as a ranking signal. INP
replaced FID as the responsiveness Core Web Vital on March 12, 2024,
and Google Search has confirmed that the 200ms threshold (75th
percentile in CrUX) factors into ranking. PWAs are particularly exposed
to INP regressions because they often run heavy client-side logic and
because installed PWAs accumulate long-running tabs where main-thread
debt builds up. See `performance.md` for the techniques: `scheduler.yield()`,
task chunking, and `content-visibility`.
