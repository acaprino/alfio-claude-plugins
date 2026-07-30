# Firefox WebExtension Best Practices, Pitfalls, and Anti-Patterns

Comprehensive guide covering JavaScript patterns, security, performance, cross-browser compatibility, and common mistakes when developing Firefox WebExtensions.

---

## 1. JavaScript Patterns

### 1.1 Async/Await in Message Listeners

**Mistake**: Using `async` directly as `runtime.onMessage` listener without handling all branches.

**Why**: If an `async` listener returns `undefined` implicitly (missing return in a branch), the response port closes prematurely. Only the first listener returning a non-`undefined` value sends the response.

```javascript
// BAD - missing return in one branch
browser.runtime.onMessage.addListener(async (message, sender) => {
  if (message.type === "getData") {
    const data = await fetchData();
    return data;
  }
  // implicit return undefined - closes response port
});

// GOOD - explicit handling of all branches
browser.runtime.onMessage.addListener((message, sender) => {
  if (message.type === "getData") {
    return fetchData().then(data => ({ success: true, data }));
  }
  return false; // let other listeners handle it
});
```

### 1.2 Unhandled Promise Rejections

**Mistake**: Not catching errors in async extension API calls.

**Why**: In MV3 event pages, unhandled rejections can cause the page to unload mid-operation with no recovery.

```javascript
// BAD
browser.tabs.sendMessage(tabId, { action: "highlight" });

// GOOD
try {
  await browser.tabs.sendMessage(tabId, { action: "highlight" });
} catch (err) {
  if (err.message.includes("Could not establish connection")) {
    console.warn(`Content script not ready in tab ${tabId}`);
  } else {
    throw err;
  }
}
```

### 1.3 Memory Leaks from Event Listeners

**Mistake**: Storing full tab objects in closures without cleanup.

**Why**: Extensions tracking many tabs can consume hundreds of MB. See Bugzilla 1652925, 1669626.

```javascript
// BAD - holds reference to entire tab object
const trackedTabs = new Map();
browser.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  trackedTabs.set(tabId, tab);
});

// GOOD - store only IDs, clean up on removal
const trackedTabIds = new Set();
browser.tabs.onUpdated.addListener((tabId) => {
  trackedTabIds.add(tabId);
});
browser.tabs.onRemoved.addListener((tabId) => {
  trackedTabIds.delete(tabId);
});
```

### 1.4 Closures Capturing Large Scopes

**Mistake**: Awaiting promises while holding references to large data structures.

```javascript
// BAD - largeData retained during entire await
async function processPage(tabId) {
  const largeData = await browser.tabs.captureVisibleTab();
  await expensiveNetworkCall(); // largeData held in memory
  return summarize(largeData);
}

// GOOD - release references when no longer needed
async function processPage(tabId) {
  let summary;
  {
    const largeData = await browser.tabs.captureVisibleTab();
    summary = summarize(largeData);
  }
  await expensiveNetworkCall();
  return summary;
}
```

### 1.5 Port Disconnection Without Cleanup

**Mistake**: Opening long-lived ports without handling disconnection.

**Why**: In MV3, the event page can unload while ports are open. Ports cannot prevent shutdown. Subsequent `postMessage` calls throw errors.

```javascript
// BAD
const port = browser.runtime.connect({ name: "data-stream" });
port.postMessage({ subscribe: true });

// GOOD
let port;
function connectPort() {
  port = browser.runtime.connect({ name: "data-stream" });
  port.onDisconnect.addListener(() => {
    console.warn("Port disconnected, reconnecting...");
    setTimeout(connectPort, 1000);
  });
  port.postMessage({ subscribe: true });
}
connectPort();
```

---

## 2. Multithreading / Web Workers

### 2.1 Web Workers in Extension Contexts

Workers behave differently per context:
- **Background (event pages)**: Workers terminated when event page unloads
- **Content scripts**: Worker URL must be `moz-extension://` URL or blob URL, not relative path
- **Extension pages** (popup, sidebar, options): Workers function normally, tied to page lifecycle

```javascript
// BAD - relative URL fails in content scripts
const worker = new Worker("worker.js");

// GOOD - use extension URL
const workerUrl = browser.runtime.getURL("worker.js");
const worker = new Worker(workerUrl);

// ALTERNATIVE - blob URL for inline worker code
const blob = new Blob([`
  self.onmessage = (e) => {
    const result = heavyComputation(e.data);
    self.postMessage(result);
  };
`], { type: "application/javascript" });
const worker = new Worker(URL.createObjectURL(blob));
```

### 2.2 Worker Lifecycle in MV3 Event Pages

**Mistake**: Starting long-running Workers from background script expecting survival across unloads.

```javascript
// BAD - worker dies when event page unloads
let worker;
browser.runtime.onMessage.addListener((msg) => {
  if (msg.type === "startProcessing") {
    worker = new Worker("processor.js");
    worker.postMessage(msg.data);
  }
});

// GOOD - short-lived workers, persist progress to storage
browser.runtime.onMessage.addListener(async (msg) => {
  if (msg.type === "startProcessing") {
    const worker = new Worker(browser.runtime.getURL("processor.js"));
    return new Promise((resolve) => {
      worker.onmessage = async (e) => {
        if (e.data.type === "progress") {
          await browser.storage.session.set({ progress: e.data.value });
        }
        if (e.data.type === "complete") {
          worker.terminate();
          resolve(e.data.result);
        }
      };
      worker.postMessage(msg.data);
    });
  }
});
```

### 2.3 Large Data Transfer Between Contexts

**Mistake**: Sending large binary data (>10MB) through `runtime.sendMessage`.

**Why**: No `Transferable` support in extension messaging. See W3C WebExtensions issue #293.

```javascript
// BAD - sending 50MB image through messaging
const imageData = await captureImage();
browser.runtime.sendMessage({ type: "upload", data: imageData });

// GOOD - use IndexedDB as shared storage, pass only a key
// Content script:
async function storeAndNotify(data) {
  const db = await openDB();
  const key = crypto.randomUUID();
  await db.put("blobs", data, key);
  browser.runtime.sendMessage({ type: "upload", key });
}

// Background script:
browser.runtime.onMessage.addListener(async (msg) => {
  if (msg.type === "upload") {
    const db = await openDB();
    const data = await db.get("blobs", msg.key);
    await uploadToServer(data);
    await db.delete("blobs", msg.key);
  }
});
```

### 2.4 OffscreenDocument (Chrome-Only)

Firefox does NOT support `chrome.offscreen.createDocument()`. Firefox event pages already have DOM access.

```javascript
// Cross-browser feature detection
if (typeof chrome !== "undefined" && chrome.offscreen) {
  // Chrome: create offscreen document
  await chrome.offscreen.createDocument({
    url: "offscreen.html",
    reasons: ["DOM_PARSER"],
    justification: "Parse HTML content",
  });
} else {
  // Firefox: parse directly in background
  const parser = new DOMParser();
  const doc = parser.parseFromString(html, "text/html");
}
```

---

## 3. Session Management

### 3.1 storage.session vs storage.local vs globals

| Storage | Persists across restart | Persists across unload | Limit | Use for |
|---------|----------------------|----------------------|-------|---------|
| Global variable | No | No | N/A | Never in MV3 |
| `storage.session` | No | Yes | 10 MB | Ephemeral runtime state |
| `storage.local` | Yes | Yes | 10 MB (unlimited with permission) | User preferences, persistent data |
| `Window.localStorage` | Unreliable | Yes | 5 MB | Never use in extensions |

```javascript
// BAD - global variable lost on event page unload
let currentMode = "default";

// BAD - ephemeral state written to disk
await browser.storage.local.set({ currentMode: "default" });

// GOOD - ephemeral state
await browser.storage.session.set({ currentMode: "default" });

// GOOD - persistent state
await browser.storage.local.set({ userPreferences: { theme: "dark" } });
```

### 3.2 storage.session Access from Content Scripts

By default, `storage.session` is only available to privileged contexts. Content scripts need explicit access level.

```javascript
// Background script, during initialization:
browser.runtime.onInstalled.addListener(async () => {
  await browser.storage.session.setAccessLevel({
    accessLevel: "TRUSTED_AND_UNTRUSTED_CONTEXTS",
  });
});

// Now content scripts can use storage.session
```

### 3.3 Tab ID Instability Across Restarts

Tab IDs are reassigned on browser restart. Never persist tab IDs to storage.local.

```javascript
// BAD - tab IDs don't survive restart
await browser.storage.local.set({ activeTab: 42 });

// GOOD - use URL as stable identifier
browser.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (changeInfo.status === "complete") {
    const state = await getStateForUrl(tab.url);
    if (state) await applyState(tabId, state);
  }
});
```

### 3.4 storage.session Size Limits

`storage.session` is limited to 10 MB total. `unlimitedStorage` does NOT apply to session storage.

```javascript
// BAD - storing full page content
await browser.storage.session.set({
  [`page_${tabId}`]: document.documentElement.outerHTML,
});

// GOOD - store metadata, use IndexedDB for large data
await browser.storage.session.set({
  [`page_${tabId}`]: {
    url: document.location.href,
    title: document.title,
    extractedAt: Date.now(),
  },
});
```

---

## 4. Startup / Initialization

### 4.1 Listener Registration Timing

**Critical rule**: All event listeners MUST be registered synchronously at top level during initial script execution. Async registration breaks event page wake-up.

```javascript
// BAD - listener registered asynchronously
window.onload = () => {
  browser.bookmarks.onCreated.addListener(handleBookmark);
};

// BAD - listener registered after await
async function init() {
  const config = await browser.storage.local.get("config");
  browser.webNavigation.onCompleted.addListener(handleNav); // too late
}
init();

// GOOD - all listeners at top level
browser.bookmarks.onCreated.addListener(handleBookmark);
browser.webNavigation.onCompleted.addListener(handleNav);
browser.runtime.onInstalled.addListener(handleInstall);

// Initialization logic inside the listener
async function handleNav(details) {
  const config = await browser.storage.local.get("config");
  // use config...
}
```

### 4.2 onInstalled vs onStartup

| Event | Fires on | Use for |
|-------|----------|---------|
| `onInstalled` | First install, update, Firefox update | Context menus, first-run setup, data migration |
| `onStartup` | Every browser start (profile load) | Per-session initialization |

```javascript
// Context menus persist across restarts - create in onInstalled
browser.runtime.onInstalled.addListener(() => {
  browser.contextMenus.create({
    id: "myMenu", title: "My Action", contexts: ["selection"],
  });
});

// Per-session init
browser.runtime.onStartup.addListener(async () => {
  await browser.storage.session.set({ sessionStart: Date.now() });
});

// First-run detection
browser.runtime.onInstalled.addListener((details) => {
  if (details.reason === "install") {
    browser.tabs.create({ url: "onboarding.html" });
  } else if (details.reason === "update") {
    console.log(`Updated from ${details.previousVersion}`);
  }
});
```

### 4.3 Race Conditions on Startup

Content scripts may execute before the background event page has initialized (especially on browser restart with restored tabs).

```javascript
// Content script - retry with backoff
async function sendWithRetry(message, maxRetries = 3) {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await browser.runtime.sendMessage(message);
    } catch (err) {
      if (attempt < maxRetries - 1) {
        await new Promise((r) => setTimeout(r, 100 * (attempt + 1)));
      } else {
        throw err;
      }
    }
  }
}
```

### 4.4 Alarms vs setTimeout/setInterval

Timers are cleared when the event page unloads. Use `browser.alarms` instead.

```javascript
// BAD - timer dies with event page
setTimeout(() => checkForUpdates(), 5 * 60 * 1000);
setInterval(() => syncData(), 60 * 1000);

// GOOD - alarms survive event page unloads
browser.alarms.create("checkUpdates", { delayInMinutes: 5 });
browser.alarms.create("syncData", { periodInMinutes: 1 });

browser.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "checkUpdates") checkForUpdates();
  if (alarm.name === "syncData") syncData();
});
```

### 4.5 Lazy Initialization

**Mistake**: Heavy initialization on every event page wake-up.

```javascript
// BAD - heavy init on every wake
const db = await initializeDatabase();
const cache = await buildCache();

// GOOD - lazy initialization
let _db = null;
async function getDb() {
  if (!_db) _db = await initializeDatabase();
  return _db;
}

browser.runtime.onMessage.addListener(async (msg) => {
  if (msg.type === "query") {
    const db = await getDb(); // initializes on first use only
    return db.query(msg.params);
  }
});
```

Note: `_db` resets to `null` after event page unload. If initialization is expensive, cache results in `storage.session`.

---

## 5. Security

### 5.1 innerHTML and Unsafe DOM APIs

**Never** use `innerHTML`, `outerHTML`, `document.write()`, or `insertAdjacentHTML()` with untrusted data in extension pages.

```javascript
// BAD - XSS if result.title contains HTML
document.getElementById("output").innerHTML = result.title;

// GOOD - safe DOM methods
const div = document.createElement("div");
div.textContent = result.title;
document.getElementById("output").appendChild(div);

// GOOD - when you must render HTML, use DOMPurify 2.0.7+
import DOMPurify from "dompurify";
element.innerHTML = DOMPurify.sanitize(untrustedHtml);
```

### 5.2 eval() and Dynamic Code Execution

Blocked by default CSP. AMO rejects extensions using `eval()`. In content scripts, `window.eval()` runs in the PAGE context -- malicious pages can intercept it.

```javascript
// BAD - blocked by CSP, rejected by AMO
eval("processData()");
setTimeout("doWork()", 1000);
const fn = new Function("return x + y");

// GOOD - direct function calls
processData();
setTimeout(() => doWork(), 1000);

// For dynamic dispatch, use a map
const handlers = { processData, doWork };
handlers[actionName]?.();
```

### 5.3 Content Script to Page Script Boundary

**Mistake**: Trusting data from `wrappedJSObject` or `window.postMessage` without validation.

**Why**: `wrappedJSObject` bypasses Firefox's Xray vision protection. Malicious pages can modify object prototypes.

```javascript
// BAD - no origin validation
window.addEventListener("message", (event) => {
  browser.runtime.sendMessage(event.data);
});

// GOOD - validate origin, source, and structure
window.addEventListener("message", (event) => {
  if (event.origin !== "https://trusted-site.example.com") return;
  if (event.source !== window) return;
  if (typeof event.data !== "object" || event.data.type !== "MY_EXT_MSG") return;

  const sanitized = {
    type: String(event.data.type),
    value: String(event.data.value).slice(0, 1000),
  };
  browser.runtime.sendMessage(sanitized);
});

// Safe data transfer from content to page
const safeData = cloneInto({ result: "ok" }, window.wrappedJSObject);
window.wrappedJSObject.extensionResult = safeData;
```

### 5.4 Extension Page Fingerprinting

**Mistake**: Injecting `moz-extension://` URLs into web pages, exposing per-instance UUID.

```javascript
// BAD - exposes extension URL
const img = document.createElement("img");
img.src = browser.runtime.getURL("icons/status.png");
document.body.appendChild(img);

// GOOD - use web_accessible_resources with match patterns
// Or embed via srcdoc iframe
const iframe = document.createElement("iframe");
iframe.srcdoc = `<img src="${browser.runtime.getURL("icons/status.png")}">`;
document.body.appendChild(iframe);
```

### 5.5 Content Security Policy

**MV3 restrictions**: Only `'self'` and `'wasm-unsafe-eval'` allowed in `script-src`. No remote scripts, no inline scripts, no event handlers.

```json
{
  "content_security_policy": {
    "extension_pages": "script-src 'self' 'wasm-unsafe-eval'"
  }
}
```

Always bundle third-party libraries locally. Remote script loading causes AMO rejection.

### 5.6 ESLint Security Auditing

```bash
npm install --save-dev eslint-plugin-no-unsanitized
```

```json
{
  "plugins": ["no-unsanitized"],
  "rules": {
    "no-unsanitized/method": "error",
    "no-unsanitized/property": "error"
  }
}
```

---

## 6. Performance

### 6.1 Content Script Impact on Page Load

**Mistake**: Large monolithic content scripts at `document_start` on every page.

```javascript
// BAD - monolithic, runs on every page at document_start
import { heavyLibrary } from "./heavy-lib.js";
heavyLibrary.init(); // blocks page load

// GOOD - minimal bootstrap, lazy loading, deferred
// manifest.json: "run_at": "document_idle"
if (shouldActivateOnThisPage()) {
  requestIdleCallback(async () => {
    const { heavyLibrary } = await import(
      browser.runtime.getURL("heavy-lib.js")
    );
    heavyLibrary.init();
  });
}
```

### 6.2 MutationObserver Overhead

**Mistake**: Observing entire DOM tree, processing every mutation individually.

**Why**: SPAs generate thousands of mutations/sec. See mozilla/contain-facebook issue #884.

```javascript
// BAD - processes every mutation, causes infinite loops
const observer = new MutationObserver((mutations) => {
  mutations.forEach((mutation) => {
    mutation.addedNodes.forEach((node) => {
      node.classList.add("processed"); // triggers another mutation
    });
  });
});
observer.observe(document.body, { subtree: true, childList: true });

// GOOD - debounce, observe selectively, disconnect during processing
let pendingMutations = [];
let debounceTimer = null;

const observer = new MutationObserver((mutations) => {
  pendingMutations.push(...mutations);
  if (!debounceTimer) {
    debounceTimer = setTimeout(() => {
      observer.disconnect();
      processBatch(pendingMutations);
      pendingMutations = [];
      debounceTimer = null;
      observer.observe(targetElement, { childList: true });
    }, 200);
  }
});

// Observe only specific container, not entire document
const targetElement = document.querySelector("#content-feed");
if (targetElement) {
  observer.observe(targetElement, { childList: true });
}
```

### 6.3 Storage API - Batch Operations

Each storage call involves IPC overhead. Always batch.

```javascript
// BAD - N individual reads
const name = (await browser.storage.local.get("name")).name;
const email = (await browser.storage.local.get("email")).email;

// GOOD - single batch
const { name, email, prefs } = await browser.storage.local.get([
  "name", "email", "prefs",
]);

// BAD - N individual writes
await browser.storage.local.set({ name: "Alice" });
await browser.storage.local.set({ email: "alice@example.com" });

// GOOD - single batch
await browser.storage.local.set({
  name: "Alice",
  email: "alice@example.com",
  lastLogin: Date.now(),
});
```

### 6.4 declarativeNetRequest vs webRequest

`declarativeNetRequest` evaluates rules in the browser engine without waking the extension. `webRequest` requires active background script for every request.

Firefox uniquely supports BOTH APIs including blocking `webRequest` in MV3.

```javascript
// Prefer declarativeNetRequest for simple rules (rules.json):
[{
  "id": 1, "priority": 1,
  "action": { "type": "block" },
  "condition": {
    "urlFilter": "tracker.example.com",
    "resourceTypes": ["script", "image"]
  }
}]

// Reserve webRequest for dynamic evaluation only:
browser.webRequest.onBeforeRequest.addListener(
  (details) => {
    if (complexDynamicCondition(details)) return { cancel: true };
  },
  { urls: ["<all_urls>"] },
  ["blocking"]
);
```

### 6.5 Background Script - Dynamic Imports

**Mistake**: Importing large libraries at top level (re-executed on every event page wake).

```javascript
// BAD - 500KB+ parsed on every wake
import { PDFDocument } from "pdf-lib";

// GOOD - dynamic import only when needed
browser.runtime.onMessage.addListener(async (msg) => {
  if (msg.type === "processPDF") {
    const { PDFDocument } = await import("./lib/pdf-lib.js");
    return processPDF(PDFDocument, msg.data);
  }
});
```

---

## 7. Cross-Browser Pitfalls

### 7.1 Background Script Model

| Aspect | Firefox | Chrome |
|--------|---------|--------|
| Context | Event page (has DOM) | Service worker (no DOM) |
| Manifest | `"background": { "scripts": [...] }` | `"background": { "service_worker": "bg.js" }` |
| DOM APIs | Available directly | Requires OffscreenDocument |

Cross-browser manifest (Firefox ignores `service_worker`, Chrome ignores `scripts`):
```json
{
  "background": {
    "scripts": ["background.js"],
    "service_worker": "background.js",
    "type": "module"
  }
}
```

### 7.2 API Namespace

```javascript
// Cross-browser without polyfill
const api = typeof browser !== "undefined" ? browser : chrome;
```

### 7.3 Message Serialization

| | Firefox | Chrome |
|---|---------|--------|
| Algorithm | Structured Clone | JSON serialization |
| Supports Map/Set/Date/RegExp/ArrayBuffer | Yes | No |

```javascript
// BAD - works in Firefox, breaks in Chrome
browser.runtime.sendMessage({ data: new Map([["key", "value"]]) });

// GOOD - cross-browser safe
browser.runtime.sendMessage({
  data: Object.fromEntries(new Map([["key", "value"]])),
});
```

### 7.4 Content Script Differences

| Behavior | Firefox | Chrome |
|----------|---------|--------|
| `globalThis === window` | false | true |
| `window.eval()` context | PAGE world | Content script world |
| Persistence on navigation | Persists (window props lost) | Destroyed, re-injected |
| Relative fetch URLs | Fails (must use absolute) | Resolves to page origin |

### 7.5 webextension-polyfill Limitations

The polyfill only wraps Chrome callbacks with Promises. It does NOT:
- Add Firefox-only APIs to Chrome (sidebarAction, proxy.onRequest)
- Fix behavioral differences (tabs.remove timing, windows.onFocusChanged multi-fire)
- Handle manifest key differences

For MV3, the polyfill is less necessary since Chrome MV3 natively supports Promises.

### 7.6 web_accessible_resources UUID

Firefox `moz-extension://` URLs use a random UUID per browser instance (unlike Chrome's stable extension ID). Cannot hardcode extension URLs in web pages.

### 7.7 Native Messaging Differences

```json
// Firefox
{ "allowed_extensions": ["extension-id@example.com"] }

// Chrome
{ "allowed_origins": ["chrome-extension://abcdefghijklmnop/"] }
```

Firefox kills native app subprocesses when connection closes (via Job objects on Windows).

---

## 8. Common Anti-Patterns

### 8.1 Polling Instead of Events

```javascript
// BAD - polling every second
setInterval(async () => {
  const tabs = await browser.tabs.query({ active: true, currentWindow: true });
  if (tabs[0]?.url !== lastUrl) handleUrlChange(tabs[0].url);
}, 1000);

// GOOD - use event API
browser.tabs.onUpdated.addListener((tabId, changeInfo) => {
  if (changeInfo.url) handleUrlChange(changeInfo.url);
});
```

### 8.2 Global State in MV3

```javascript
// BAD - resets to 0 on every wake
let requestCount = 0;
browser.webRequest.onCompleted.addListener(() => {
  requestCount++;
  updateBadge(requestCount);
});

// GOOD - persist to storage.session
browser.webRequest.onCompleted.addListener(async () => {
  const { requestCount = 0 } = await browser.storage.session.get("requestCount");
  await browser.storage.session.set({ requestCount: requestCount + 1 });
  updateBadge(requestCount + 1);
});
```

### 8.3 Over-Broad Permissions

```json
// BAD
{ "permissions": ["tabs", "webRequest", "webRequestBlocking", "<all_urls>",
                   "storage", "cookies", "history", "bookmarks"] }

// GOOD - minimal + optional
{
  "permissions": ["storage"],
  "optional_permissions": ["tabs", "bookmarks"],
  "host_permissions": ["*://specific-site.example.com/*"]
}
```

Request optional permissions at runtime from user action handlers:
```javascript
document.getElementById("enableBookmarks").addEventListener("click", async () => {
  const granted = await browser.permissions.request({ permissions: ["bookmarks"] });
  if (granted) enableBookmarkFeature();
});
```

### 8.4 Monolithic Content Scripts

```json
// BAD - one 200KB script on all pages
{ "content_scripts": [{ "matches": ["<all_urls>"], "js": ["everything.js"] }] }

// GOOD - minimal bootstrap + programmatic injection
{ "content_scripts": [{
  "matches": ["*://specific-site.com/*"],
  "js": ["lightweight-bootstrap.js"],
  "run_at": "document_idle"
}] }
```

```javascript
// lightweight-bootstrap.js (< 1KB)
if (document.querySelector(".target-element")) {
  browser.runtime.sendMessage({ type: "injectFullScript" });
}

// background.js
browser.runtime.onMessage.addListener(async (msg, sender) => {
  if (msg.type === "injectFullScript") {
    await browser.scripting.executeScript({
      target: { tabId: sender.tab.id },
      files: ["full-feature.js"],
    });
  }
});
```

### 8.5 Missing Error Boundaries

```javascript
// BAD - unhandled error crashes listener
browser.runtime.onMessage.addListener(async (msg) => {
  const data = await riskyOperation(msg);
  return data;
});

// GOOD - error boundary with structured responses
browser.runtime.onMessage.addListener(async (msg) => {
  try {
    const data = await riskyOperation(msg);
    return { success: true, data };
  } catch (err) {
    console.error("Message handler error:", err);
    return { success: false, error: err.message };
  }
});
```

### 8.6 Tab Lifecycle Assumptions

```javascript
// BAD - tab may have closed during await
browser.tabs.onUpdated.addListener(async (tabId, changeInfo) => {
  if (changeInfo.status === "complete") {
    const data = await slowNetworkCall();
    await browser.tabs.sendMessage(tabId, data); // tab may be closed
  }
});

// GOOD - verify tab still exists
browser.tabs.onUpdated.addListener(async (tabId, changeInfo) => {
  if (changeInfo.status === "complete") {
    const data = await slowNetworkCall();
    try {
      await browser.tabs.sendMessage(tabId, data);
    } catch (err) {
      console.debug(`Tab ${tabId} no longer available`);
    }
  }
});
```

### 8.7 Relying on onSuspend for Data Persistence

`onSuspend` does NOT fire if the extension crashes. Provides limited time for cleanup.

```javascript
// BAD - data lost if extension crashes
let importantState = {};
browser.runtime.onSuspend.addListener(() => {
  browser.storage.session.set({ state: importantState });
});

// GOOD - persist incrementally as state changes
async function updateState(key, value) {
  importantState[key] = value;
  await browser.storage.session.set({ state: importantState });
}
```

---

## Quick Reference: Critical Rules

| Rule | Rationale |
|------|-----------|
| Register all listeners synchronously at top level | Required for event page wake-up |
| Never use `eval()`, `new Function()`, `setTimeout(string)` | CSP blocks it; AMO rejects it |
| Use `storage.session` for ephemeral state, `storage.local` for persistent | Globals die with event page |
| Batch storage reads/writes | Each call has IPC overhead |
| Use Alarms API, not `setTimeout`/`setInterval` | Timers die with event page |
| Use `textContent` not `innerHTML` for untrusted data | Prevents XSS in privileged context |
| Validate `postMessage` origin and structure | Any page can send messages |
| Use absolute URLs in content script `fetch()` | Relative URLs fail in Firefox |
| Handle port disconnection | Ports can't keep event pages alive |
| Never trust `wrappedJSObject` data | Pages can modify prototypes |
| Minimal permissions, use `optional_permissions` | Reduces attack surface and user friction |

---

## Sources

- [Build a secure extension - Extension Workshop](https://extensionworkshop.com/documentation/develop/build-a-secure-extension/)
- [Content Security Policy - MDN WebExtensions](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Content_Security_Policy)
- [Chrome incompatibilities - MDN](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Chrome_incompatibilities)
- [Background scripts - MDN](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Background_scripts)
- [MV3 migration guide - Extension Workshop](https://extensionworkshop.com/documentation/develop/manifest-v3-migration-guide/)
- [storage.session - MDN](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/storage/session)
- [Content scripts - MDN](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Content_scripts)
- [webextension-polyfill - GitHub](https://github.com/mozilla/webextension-polyfill)
- [Large binary transfer - W3C WebExtensions #293](https://github.com/w3c/webextensions/issues/293)
- [MutationObserver issues - contain-facebook #884](https://github.com/mozilla/contain-facebook/issues/884)
- [Extension memory usage - Bugzilla 1652925](https://bugzilla.mozilla.org/show_bug.cgi?id=1652925)
