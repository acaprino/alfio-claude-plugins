# Permissions

The Permissions API gives a unified way to query the current state of a capability (granted, prompt, or denied) and to react when that state changes. It does not grant or revoke a permission directly; it exposes the runtime state managed by the browser. Together with the `Permissions-Policy` HTTP header (which scopes which capabilities are allowed at the document and iframe boundary) it forms the two-layer permission model that every PWA must implement correctly.

This reference covers the query pattern, the canonical list of permission names, the four practical best practices for prompting users, the `Permissions-Policy` header, and the per-platform availability matrix.

## Query pattern

The Permissions API exposes a single async entry point: `navigator.permissions.query({ name })`. It returns a `PermissionStatus` object with a `state` property and a `change` event. Wrap the call in a try/catch because permission names that are unknown to the current browser throw a `TypeError` rather than returning a `denied` state.

```ts
async function ensure(name: PermissionName, onGranted: () => void) {
  try {
    const status = await navigator.permissions.query({ name });
    if (status.state === 'granted') onGranted();
    else if (status.state === 'prompt') showRationale(name, onGranted);
    status.addEventListener('change', () => { /* react */ });
  } catch { /* permission not supported */ }
}
```

The three possible values of `state` are:

- `granted`: the capability is allowed without further interaction. Proceed with the action.
- `prompt`: the user has not decided yet. The browser will display the native permission prompt the next time the capability is invoked. This is the point at which a rationale UI must be shown beforehand.
- `denied`: the user (or a policy header) has refused. Do not call the capability and do not re-trigger a prompt; the browser will silently reject subsequent attempts after the first denial.

The `change` event fires when the state transitions at runtime, for example when the user revokes a permission through the site settings panel while the page is still open. Keep a single listener per capability and update the relevant UI in place.

### Typical state transitions

The `state` value moves through a small graph of transitions. Knowing the graph helps to size the UI correctly:

- Initial load on a fresh origin: `prompt`. The browser has no record of a prior decision.
- After the user clicks "Allow" on the native prompt: `prompt` to `granted`. The `change` event fires once.
- After the user clicks "Block" on the native prompt: `prompt` to `denied`. The `change` event fires once.
- User opens site settings and revokes a previously granted permission: `granted` to either `prompt` or `denied`, depending on the browser. Chrome typically goes to `prompt`; Safari typically goes to `denied`.
- User opens site settings and re-enables a previously denied permission: `denied` to `prompt` or directly to `granted`.

Always keep the `change` listener attached for the lifetime of the page. Permissions can flip while the user is interacting with the app (for example, on macOS the system-level camera permission can be revoked from System Settings while the browser tab is open).

### A complete usage example

The pattern below combines support detection, state inspection, rationale UI, and the native invocation. It assumes a click handler bound to a visible button so that the user gesture is preserved through to the capability call.

```ts
async function requestNotificationsOnClick() {
  if (!('Notification' in window) || !('permissions' in navigator)) {
    showFallbackInbox();
    return;
  }
  const status = await navigator.permissions.query({ name: 'notifications' });
  if (status.state === 'granted') {
    subscribeToPush();
    return;
  }
  if (status.state === 'denied') {
    showSiteSettingsHint();
    return;
  }
  // state === 'prompt'
  const rationale = await showRationaleModal({
    title: 'Stay up to date',
    body: 'We will send notifications when an order ships.',
    confirmLabel: 'Enable notifications',
  });
  if (!rationale.confirmed) return;
  const result = await Notification.requestPermission();
  if (result === 'granted') subscribeToPush();
}
```

Note that `Notification.requestPermission()` is called inside the same async task as the click handler, with no intervening network round-trip, so the user gesture is still valid when the native prompt is shown.

## Permission names

MDN documents the following permission names as valid arguments to `navigator.permissions.query()` (this is the canonical list as quoted in the MDN `Permissions: query() method` reference):

- `accelerometer`
- `accessibility-events`
- `ambient-light-sensor`
- `background-sync`
- `camera`
- `clipboard-read`
- `clipboard-write`
- `geolocation`
- `gyroscope`
- `local-fonts`
- `magnetometer`
- `microphone`
- `midi`
- `notifications`
- `payment-handler`
- `persistent-storage`
- `push`
- `screen-wake-lock`
- `storage-access`
- `top-level-storage-access`
- `window-management`

Not every name is implemented in every browser. Querying an unknown name throws; this is why the helper above wraps the call in try/catch. To detect support before querying, the safest pattern is a one-shot probe at startup:

```ts
async function supports(name: PermissionName): Promise<boolean> {
  try {
    await navigator.permissions.query({ name });
    return true;
  } catch {
    return false;
  }
}
```

Cache the result. Do not probe on every action.

## Best practices

Four rules govern how a PWA should prompt for permissions. They are derived from observed user behavior across Chrome, Safari, and Firefox over the last several years, and from the way each browser hardens its permission heuristics against abuse.

1. **Never ask at page load. Ask at the moment of the action requiring it.** A prompt that appears immediately after navigation has no context, surprises the user, and gets denied at a high rate. Worse, an early denial is sticky: most browsers will not surface the native prompt again for the same origin for a long cool-off period (or ever, depending on the capability). Bind the request to an explicit user action such as a click on "Use my location" or "Enable notifications".

2. **Always show a rationale UI before the native prompt.** A short in-page explanation (one sentence and a button) that says why the capability is needed and what it will do gives the user enough information to choose. The native browser prompt is intentionally generic and cannot convey product-specific reasoning. The rationale UI is also the right place to handle the `prompt` state returned by the Permissions API: defer the actual call to the capability until the user clicks "Allow" inside your rationale UI.

3. **For `push` and `notifications` the prompt must be preceded by a user gesture. On iOS this is binding.** Chromium, Firefox, and Safari all require a transient user activation before `Notification.requestPermission()` or `pushManager.subscribe()` can show the native prompt. On iOS Safari (16.4+) the requirement is enforced strictly and the prompt is silently suppressed if the call is not directly inside a tap handler. Async work between the tap and the call (a network round-trip, a `setTimeout`, a `Promise` chain that yields too long) can also consume the gesture and break the prompt. Keep the call synchronous to the gesture, or wrap it carefully.

4. **Handle `denied` with an alternative UI. Do not re-prompt.** Once a capability is denied, the browser will not surface a new native prompt no matter how many times you call the API. Detect the `denied` state and show a non-modal explanation pointing to the site settings page (and a screenshot, on iOS, since the path is non-obvious). Examples: for `geolocation`, fall back to a manual address input; for `notifications`, fall back to in-app inbox polling; for `camera`, fall back to file upload. The product must continue to function without the capability.

### Rationale UI checklist

A rationale UI that earns the grant is short, specific, and timed. Use this checklist when designing one:

- One-sentence headline that names the capability in plain language ("Use your camera to scan the QR code").
- One short paragraph (no more than 25 words) explaining the immediate user benefit.
- A primary button labeled with a verb that matches the capability ("Scan", "Locate me", "Enable notifications"). Avoid "Allow" or "OK" because the next surface the user sees is the native browser prompt with those same words.
- A secondary button labeled "Not now" that closes the rationale without ever calling the API. This preserves the `prompt` state for a future attempt.
- Do not include "Block" or "Never" as visible options. The browser will accept the user's refusal via the native prompt; an in-page "Never" button burns the opportunity.
- Do not stack multiple rationales in a single session. Sequence them across distinct user actions.

## Permissions-Policy header

The `Permissions-Policy` HTTP response header controls which capabilities the document (and any iframes it embeds) is allowed to use. It is a defense-in-depth measure that complements the runtime prompt: even if a malicious third-party script tries to access `camera`, the browser will reject the call when the header does not allow that origin.

Example header value disabling third-party iframe access:

```http
Permissions-Policy: camera=(self), microphone=(self), geolocation=(self "https://maps.acme.com"), interest-cohort=()
```

Read it left to right:

- `camera=(self)` allows the camera only for documents on the same origin as the response. Cross-origin iframes embedded by the page cannot use the camera.
- `microphone=(self)` applies the same rule to the microphone.
- `geolocation=(self "https://maps.acme.com")` allows geolocation on the document's own origin plus the explicitly listed `https://maps.acme.com` origin (useful when embedding a trusted map widget that needs the user's location).
- `interest-cohort=()` disables the FLoC / Topics API entirely (the empty allowlist means no origin can use the feature).

The empty allowlist `()` is the canonical way to disable a feature outright; `*` is the canonical way to enable it for all origins. Always prefer `self` over `*` for sensitive capabilities. The header must be set on the top-level document response; setting it inside an iframe response only restricts the iframe further (it cannot relax restrictions inherited from the parent).

Per-iframe overrides use the `allow` attribute on the iframe element:

```html
<iframe src="https://maps.acme.com/embed" allow="geolocation"></iframe>
```

The combination of `Permissions-Policy` on the parent document and `allow` on the iframe is the correct way to grant a capability to a specific embedded origin without weakening the policy for the rest of the page.

### Common directive recipes

Three recipes cover most production sites:

```http
Permissions-Policy: camera=(), microphone=(), geolocation=(), interest-cohort=()
```

Deny everything for the page and all iframes. Suitable for static marketing pages that never need a capability.

```http
Permissions-Policy: camera=(self), microphone=(self), geolocation=(self), payment=(self), publickey-credentials-get=(self), publickey-credentials-create=(self), interest-cohort=()
```

Allow common PWA capabilities only on the same origin. Suitable for a self-contained PWA that does not embed third-party widgets.

```http
Permissions-Policy: camera=(self "https://video.acme.com"), microphone=(self "https://video.acme.com"), geolocation=(self), interest-cohort=()
```

Allow camera and microphone on the same origin plus an explicitly listed embed origin (for example, a video call widget). Geolocation is restricted to the same origin only.

### Reporting violations

The `Permissions-Policy` header pairs with the `Reporting-Endpoints` header and `Report-To` directive to send violation reports to a collector:

```http
Reporting-Endpoints: pp-endpoint="https://acme.com/csp-reports"
Permissions-Policy-Report-Only: camera=(self), report-to=pp-endpoint
```

Use the `-Report-Only` variant to roll out a tighter policy without breaking the site, monitor the reports for one to two weeks, then enforce.

## Platform differences in availability

PWAs run on three asymmetric platform families. The permission surface, the availability of capabilities behind those permissions, and the prompting heuristics are not the same across the three. Plan for the most restrictive target (iOS) first and progressively enhance for the others.

### iOS Safari

- No `background-sync`. The capability does not exist on WebKit.
- No `periodic-background-sync`. Same as above.
- No Web Bluetooth, USB, HID, Serial, or NFC. Apple does not implement these capabilities; querying for them returns "unsupported" and using the corresponding JavaScript APIs throws or returns `undefined`.
- `clipboard-read` requires a user gesture every time, not just at first use. There is no persistent "always allow" grant for clipboard reads on iOS.
- `notifications` are available only on installed PWAs (a site that was added to the Home Screen and opens in `display: standalone`). A site running inside the regular Safari tab cannot subscribe to Web Push. This is a stricter requirement than the desktop and Android cases.
- The user gesture requirement for the `notifications` prompt is strictly enforced. Defer the call until the user taps a visible "Enable notifications" button.

### Android Chrome

All permission names listed above are available with the standard browser prompt heuristics. Background Sync, Periodic Background Sync (engagement-gated), and Background Fetch all work. Web Bluetooth, USB, HID, Serial, and NFC are available behind the secure-context requirement. The system manages permissions for an installed WebAPK through the Android Settings app, the same surface used by native apps; users expect to find revocation controls there.

### Desktop (Chrome, Edge)

A superset of the Android capability set. In addition to everything available on Android, Web Serial, Web USB, Web HID, and Web Bluetooth are also exposed on Windows, macOS, and Linux desktops where the underlying OS supports them. `window-management` is a desktop-specific capability for multi-monitor layout control. `local-fonts` is also desktop-only in practice. The `notifications` capability uses the OS-native notification center (toasts on Windows, Notification Center on macOS) rather than an in-browser surface.

### Compatibility summary

| Capability | iOS Safari | Android Chrome | Desktop Chrome / Edge |
|---|---|---|---|
| `geolocation` | yes | yes | yes |
| `camera`, `microphone` | yes | yes | yes |
| `notifications` | installed PWA only, user gesture required | yes | yes |
| `push` | iOS 16.4+, installed PWA, user gesture | yes | yes |
| `background-sync` | no | yes | yes |
| `periodic-background-sync` | no | yes (engagement-gated) | yes (engagement-gated) |
| `clipboard-read` | gesture every call | gesture on first call | gesture on first call |
| `clipboard-write` | yes | yes | yes |
| `persistent-storage` | gated on notification permission | yes | yes |
| `screen-wake-lock` | iOS 18.4+ for Home Screen PWAs | yes | yes |
| `window-management` | no | no | yes |
| `local-fonts` | no | partial | yes |
| Web Bluetooth | no | yes | yes |
| Web USB / HID / Serial | no | partial (USB yes, HID partial, Serial no) | yes |
| WebNFC | no | yes (Android only) | no |

When the answer is "no" for a target platform, the application must still function. Design the degraded path before you design the enhanced path.

### Testing the permission surface

Manual verification across the three platform families:

- Chromium DevTools: Application panel, "Permissions" section under the origin. The dropdown next to each permission name lets you simulate `granted`, `denied`, and `prompt` states without leaving the browser. The change is reflected through `navigator.permissions.query()` and fires the `change` event, so reactive UI can be exercised end-to-end.
- Safari (macOS): the Develop menu, "Permissions" submenu, exposes a similar override surface for the current page. On iOS, use the Settings app under "Safari" then "Advanced" then "Website Data" for the manual revocation path.
- Firefox: about:preferences#privacy then "Permissions" exposes per-site settings. The runtime `change` event is fired when a permission is altered there.

For automated testing, Playwright and Puppeteer both expose context-level `grantPermissions` and `clearPermissions` helpers that map onto the Permissions API. Use them to write end-to-end tests that exercise the three states without manual interaction.

### Cross-references

- `references/push-notifications.md` covers the Web Push subscription flow that consumes the `push` and `notifications` permissions, plus the iOS 16.4+ requirements for installed PWAs.
- `references/background-execution.md` covers the `background-sync` and `periodic-background-sync` permissions and the engagement-score gate that Chromium applies to the periodic variant.
- `references/storage-persistence.md` covers `persistent-storage` and the Safari-specific dependency on a granted notification permission.
- `references/security.md` covers how `Permissions-Policy` interacts with CSP, COOP, and COEP at the HTTP-header level.

