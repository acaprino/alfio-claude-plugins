# Authentication in Tauri Apps

OAuth + system browser + deep-link return is the only Tauri-friendly path -- Google explicitly blocks OAuth from WebViews. The composite local pattern is: PKCE flow, store-backed CSRF state, Firebase `signInWithCredential` bridge.

## When to use

Designing OAuth (Google, generic OIDC) for a Tauri 2 app. For Apple Sign-In and the mobile-side wiring (deep-link plugin config, hosted callback HTML, AuthContext cleanup), see `authentication-mobile.md`.

## When NOT to use

In-app auth via Firebase `signInWithPopup()` or `signInWithRedirect()` -- both fail in Tauri's WebView. Use system browser + deep link.

## Why this is hard (the WebView problem)

Google explicitly blocks OAuth sign-in from WebViews / embedded browsers for security reasons. This means:
- `signInWithPopup()` does not work in Tauri's WebView (desktop OR mobile)
- `signInWithRedirect()` also fails
- Applies to Firebase Auth and direct Google OAuth

The fix is to launch the system browser via the `opener` plugin and bring the user back via a deep-link scheme.

## Required plugins

```bash
npm run tauri add opener
npm run tauri add deep-link
```

On desktop you can use `opener` or `shell:open`. On mobile **use `opener`** -- the `shell` plugin does not work for URLs on Android.

## Flow architecture

```
App -> openUrl() -> System Browser (Google OAuth)
                             |
                       User signs in
                             |
                Callback page (parses tokens, redirects)
                             |
                  myapp://auth/callback (deep link)
                             |
                       App (validates state, signs in via Firebase)
```

## Gotchas

- **Implicit flow exposes tokens in URLs** -- they may be logged in browser history, server access logs, or referrer headers. **Use Authorization Code + PKCE for production.** Implicit is acceptable only for prototypes.
- **State parameter MUST be validated on every callback.** Otherwise CSRF: an attacker can send a victim a crafted `myapp://auth/callback?state=...&id_token=...` URL and force-sign-in as the attacker. The state-store is one-time-use.
- **Use the same `nonce` for both `state` and the OpenID `nonce` parameter.** This way you can validate the ID token nonce matches the value you saved before the redirect.
- **OAuth state must expire.** A stale state from yesterday should not be honored. 10-minute TTL is the default; check `Date.now() - state.timestamp` on retrieval.
- **`tauri-plugin-store` requires `await store.save()`** after `set()` to flush to disk -- without it the state is lost on app exit, breaking the callback.
- **Firebase `signInWithCredential`** is the bridge between OAuth tokens (from system browser) and the Firebase user session. After successful credential sign-in, `onAuthStateChanged` fires and your AuthContext updates.
- **Don't store the access token in `localStorage`** -- it persists across logouts and is XSS-exfiltrable. Keep it in JS memory; Firebase handles refresh internally via `onIdTokenChanged`.
- **Deep-link listener must be cleaned up** in `onunload` (app) or component unmount (React) -- see `authentication-mobile.md` for the full AuthContext shape.

## TypeScript shape (the types worth keeping)

```typescript
export interface OAuthState {
  continueUri: string;     // myapp://auth/callback
  nonce: string;           // crypto.randomUUID()
  timestamp: number;       // Date.now() for TTL
}

export interface OAuthCallbackParams {
  access_token?: string;
  id_token?: string;
  state?: string;
  error?: string;
  error_description?: string;
}

export class OAuthError extends Error {
  constructor(message: string, public code?: string) {
    super(message);
    this.name = 'OAuthError';
  }
}
```

## State store (one-time use, store-backed)

```typescript
import { Store } from '@tauri-apps/plugin-store';
const STATE_KEY = 'pending_oauth_state';
const STATE_TTL_MS = 10 * 60 * 1000;

let store: Store | null = null;
async function getStore() { return store ??= new Store('auth.json'); }

export async function saveOAuthState(state: OAuthState) {
  const s = await getStore();
  await s.set(STATE_KEY, state);
  await s.save();           // <-- without this, lost on exit
}

export async function consumeOAuthState(): Promise<OAuthState | null> {
  const s = await getStore();
  const state = await s.get<OAuthState>(STATE_KEY);
  await s.delete(STATE_KEY);                                     // one-time use
  await s.save();
  if (!state || Date.now() - state.timestamp > STATE_TTL_MS) return null;
  return state;
}
```

## Initiate flow (with CSRF protection)

```typescript
import { openUrl } from '@tauri-apps/plugin-opener';

export async function initiateGoogleSignIn(): Promise<void> {
  const config = getAuthConfig();
  const nonce = crypto.randomUUID();
  const oauthState: OAuthState = {
    continueUri: `${config.appScheme}://auth/callback`,
    nonce,
    timestamp: Date.now(),
  };
  await saveOAuthState(oauthState);

  const authUrl = new URL('https://accounts.google.com/o/oauth2/v2/auth');
  authUrl.searchParams.set('client_id', config.googleClientId);
  authUrl.searchParams.set('redirect_uri', config.callbackUrl);
  authUrl.searchParams.set('response_type', 'token id_token');         // implicit; use 'code' for PKCE
  authUrl.searchParams.set('scope', 'openid email profile');
  authUrl.searchParams.set('state', encodeURIComponent(JSON.stringify(oauthState)));
  authUrl.searchParams.set('nonce', nonce);                            // same nonce as in state
  authUrl.searchParams.set('prompt', 'select_account');

  try {
    await openUrl(authUrl.toString());
  } catch {
    await clearOAuthState();
    throw new OAuthError('Failed to open sign-in page.', 'OPEN_URL_FAILED');
  }
}
```

## Callback handler (validates state + nonce, signs in to Firebase)

```typescript
import { getAuth, GoogleAuthProvider, signInWithCredential } from 'firebase/auth';

export async function handleOAuthCallback(url: string): Promise<void> {
  const params = parseCallbackUrl(url);
  if (params.error) throw new OAuthError(params.error_description || params.error, params.error);

  const stored = await consumeOAuthState();
  if (!stored) throw new OAuthError('No pending authentication.', 'NO_PENDING_STATE');

  // CRITICAL: validate state nonce -- prevents CSRF
  const returned = JSON.parse(decodeURIComponent(params.state || '')) as OAuthState;
  if (returned.nonce !== stored.nonce) {
    throw new OAuthError('Invalid authentication response.', 'STATE_MISMATCH');
  }

  if (!params.id_token) throw new OAuthError('No ID token.', 'MISSING_ID_TOKEN');

  const credential = GoogleAuthProvider.credential(params.id_token, params.access_token || null);
  await signInWithCredential(getAuth(), credential);
  // onAuthStateChanged fires now; AuthContext picks it up
}
```

## PKCE flow (recommended for production)

PKCE keeps tokens out of URLs entirely. Use `response_type=code` instead of `token id_token`, exchange the code via Google's token endpoint with the verifier:

- Generate `codeVerifier` (32 random bytes, base64url) and `codeChallenge` (SHA-256 of verifier, base64url).
- Store the verifier alongside the state.
- Add `code_challenge` and `code_challenge_method=S256` to the auth URL.
- On callback, POST to `https://oauth2.googleapis.com/token` with `code`, `code_verifier`, `client_id`, `redirect_uri`, `grant_type=authorization_code`.
- Use the returned `id_token` with `GoogleAuthProvider.credential()` exactly as above.

The PKCE callback page (hosted) captures the `code` param and bounces it via deep link instead of the tokens.

## Token refresh (Firebase handles this)

```typescript
import { onIdTokenChanged, getIdToken } from 'firebase/auth';

export function setupTokenRefreshListener(onTokenRefresh: (token: string) => void) {
  return onIdTokenChanged(getAuth(), async (user) => {
    if (user) onTokenRefresh(await getIdToken(user));
  });
}

// Force refresh before a critical API call:
await getIdToken(user, /* forceRefresh */ true);
```

## Google Cloud Console setup

1. https://console.cloud.google.com/apis/credentials → Create OAuth 2.0 Client ID (Web application).
2. Authorized JavaScript origins: `https://your-app.web.app`.
3. Authorized redirect URIs: `https://your-app.web.app/auth/callback`.

## Security checklist

- [ ] HTTPS for all callback URLs
- [ ] State parameter validated on every callback
- [ ] Same nonce used for state + ID token (validated on Firebase side too)
- [ ] OAuth state expires (10-minute default)
- [ ] State cleared after use (one-time)
- [ ] Tokens in JS memory, not `localStorage`
- [ ] Error messages don't leak sensitive info
- [ ] PKCE used for production (not implicit flow)
- [ ] Token refresh listener configured
- [ ] Deep-link listener properly cleaned up (see `authentication-mobile.md`)

## Official docs

- Google OAuth 2.0 reference: https://developers.google.com/identity/protocols/oauth2
- PKCE (RFC 7636): https://www.rfc-editor.org/rfc/rfc7636
- OAuth 2.0 for Native Apps (RFC 8252) -- system browser + PKCE: https://www.rfc-editor.org/rfc/rfc8252
- Firebase Auth `signInWithCredential`: https://firebase.google.com/docs/reference/js/auth.md#signinwithcredential
- Firebase ID token + refresh: https://firebase.google.com/docs/auth/admin/verify-id-tokens
- Tauri `opener` plugin: https://v2.tauri.app/plugin/opener/
- Tauri `deep-link` plugin: https://v2.tauri.app/plugin/deep-link/
- Tauri `store` plugin: https://v2.tauri.app/plugin/store/
- OWASP OAuth security cheat sheet: https://cheatsheetseries.owasp.org/cheatsheets/OAuth2_Cheat_Sheet.html

## Related

- `authentication-mobile.md` -- mobile-side: deep-link config, hosted callback HTML, Apple Sign-In, AuthContext + cleanup
- `plugins-core.md` -- `opener` vs `shell` (and why opener wins for OAuth)
- `frontend-patterns.md` -- the React lifecycle hook patterns the AuthContext uses
