# Mobile Authentication

Deep-link OAuth callback plumbing, hosted callback HTML, Apple Sign-In, and the full React AuthContext with deep-link listener cleanup. The OAuth/PKCE security architecture lives in `authentication.md` -- this file is the mobile-specific wiring.

## When to use

Wiring OAuth sign-in for an Android/iOS Tauri 2 app: deep-link config, hosted callback page, Apple Sign-In flow, AuthContext shape. For desktop/general OAuth security patterns, see `authentication.md`.

## Deep-link config (the parts that matter)

```json
// tauri.conf.json
"plugins": {
  "deep-link": {
    "mobile": [{ "scheme": ["myapp"], "appLink": false }]
  }
}
```

```json
// capabilities/default.json
"permissions": ["deep-link:default", "opener:default", "store:default"]
```

## Gotchas

- **`shell:open` does NOT work for URLs on Android.** It throws `Scoped shell IO error: No such file or directory (os error 2)`. **Use the `opener` plugin** (v2.3.0+) -- it opens Chrome Custom Tabs on Android and Safari on iOS.
- **The system browser cannot directly redirect to `myapp://...`** in the OAuth flow. You need a hosted callback page (Firebase Hosting or similar) that receives the OAuth fragment, parses tokens, and bounces via `window.location.href = "myapp://..."`. Pattern below.
- **Apple Sign-In returns user info ONLY on first sign-in.** The `user` parameter (containing name + email) is NOT returned on subsequent sign-ins. Persist it on first auth -- you cannot fetch it later.
- **Apple `nonce` MUST be passed as `rawNonce` to Firebase**, not the SHA-256-hashed version. Firebase's `OAuthProvider('apple.com').credential({ idToken, rawNonce: nonce })` expects the original random nonce. Hashing breaks signature verification.
- **Deep-link listener cleanup is async.** `onOpenUrl()` returns `Promise<UnlistenFn>` -- store the returned unlisten in state and call it on unmount/unload, otherwise you leak a listener every re-render.
- **`response_type=token id_token` is implicit flow.** For production prefer PKCE (`response_type=code`) -- see `authentication.md`. The hosted callback page has different behavior for each.
- **Callback page CORS**: must be served from the same domain as the OAuth `redirect_uri`. Mismatched origin = silent failure.
- **Cache-Control: no-store on the callback page.** Otherwise mobile browsers may serve a stale page that bounces to a stale state.

## Hosted callback page (the bridge between OAuth and deep link)

Host at `/auth/callback/index.html` (Firebase Hosting or similar). Parses the OAuth fragment, builds the `myapp://` URL, redirects.

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Authenticating...</title>
  <style>
    body { font-family: system-ui, sans-serif; display: flex; flex-direction: column;
           justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f5f5f5; }
    .spinner { width: 40px; height: 40px; border: 3px solid #ddd;
               border-top-color: #4285f4; border-radius: 50%; animation: spin 1s linear infinite; }
    @keyframes spin { to { transform: rotate(360deg); } }
    p { color: #666; margin-top: 16px; }
    .error { color: #d32f2f; }
    .fallback a { color: #4285f4; text-decoration: none; }
  </style>
</head>
<body>
  <div class="spinner" id="spinner"></div>
  <p id="status">Redirecting to app...</p>
  <div id="fallback" style="display:none">
    <p>If the app doesn't open automatically:</p>
    <a id="manual-link" href="#">Open App Manually</a>
  </div>
  <script>
    (function() {
      const params = new URLSearchParams(window.location.hash.substring(1));
      const error = params.get('error');
      if (error) {
        document.getElementById('spinner').style.display = 'none';
        document.getElementById('status').textContent =
          params.get('error_description') || 'Authentication failed';
        document.getElementById('status').className = 'error';
        return;
      }

      // Parse continue URI from state
      let continueUri = 'myapp://auth/callback';
      const state = params.get('state');
      if (state) {
        try {
          const stateObj = JSON.parse(decodeURIComponent(state));
          continueUri = stateObj.continueUri || continueUri;
        } catch {}
      }

      const deepLinkUrl = new URL(continueUri);
      const idToken = params.get('id_token');
      const accessToken = params.get('access_token');
      if (idToken)     deepLinkUrl.searchParams.set('id_token', idToken);
      if (accessToken) deepLinkUrl.searchParams.set('access_token', accessToken);
      if (state)       deepLinkUrl.searchParams.set('state', state);

      const finalUrl = deepLinkUrl.toString();
      document.getElementById('manual-link').href = finalUrl;
      window.location.href = finalUrl;
      setTimeout(() => { document.getElementById('fallback').style.display = 'block'; }, 2000);
    })();
  </script>
</body>
</html>
```

## Firebase Hosting config (for the callback page)

```json
{
  "hosting": {
    "rewrites": [{ "source": "/auth/callback", "destination": "/auth/callback/index.html" }],
    "headers": [{
      "source": "/auth/**",
      "headers": [
        { "key": "Cache-Control", "value": "no-store" },
        { "key": "X-Content-Type-Options", "value": "nosniff" }
      ]
    }]
  }
}
```

## Apple Sign-In

Apple Developer setup: register App ID with "Sign in with Apple" capability, create a Services ID for web auth, configure domains and redirect URLs.

```typescript
import { openUrl } from '@tauri-apps/plugin-opener';

export async function initiateAppleSignIn(): Promise<void> {
  const config = getAuthConfig();
  const nonce = crypto.randomUUID();
  await saveOAuthState({
    continueUri: `${config.appScheme}://auth/callback`,
    nonce, timestamp: Date.now(), provider: 'apple',
  });

  const authUrl = new URL('https://appleid.apple.com/auth/authorize');
  authUrl.searchParams.set('client_id', config.appleClientId);   // Your Services ID
  authUrl.searchParams.set('redirect_uri', config.callbackUrl);
  authUrl.searchParams.set('response_type', 'code id_token');
  authUrl.searchParams.set('scope', 'name email');
  authUrl.searchParams.set('response_mode', 'fragment');
  authUrl.searchParams.set('state', encodeURIComponent(JSON.stringify({nonce, ...})));
  authUrl.searchParams.set('nonce', nonce);

  await openUrl(authUrl.toString());
}
```

Firebase bridge for Apple credentials -- **`rawNonce` not hashed**:

```typescript
import { OAuthProvider, signInWithCredential } from 'firebase/auth';

export async function completeAppleSignIn(idToken: string, nonce: string) {
  const credential = new OAuthProvider('apple.com').credential({
    idToken,
    rawNonce: nonce,                                              // CRITICAL: raw, not hashed
  });
  await signInWithCredential(getAuth(), credential);
}
```

Apple-specific callback (persist user info on first sign-in only):

```typescript
function handleAppleCallback(params: OAuthCallbackParams): void {
  const userParam = params.user;
  if (userParam) {
    try {
      const userInfo = JSON.parse(decodeURIComponent(userParam));
      // Persist -- won't be returned on subsequent sign-ins
      localStorage.setItem('apple_user_info', JSON.stringify(userInfo));
    } catch {}
  }
}
```

## AuthContext with deep-link listener cleanup (React)

The full pattern that handles auth state, OAuth callbacks, and listener cleanup:

```tsx
import { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';
import { onOpenUrl } from '@tauri-apps/plugin-deep-link';
import { getAuth, onAuthStateChanged, signOut as firebaseSignOut, User } from 'firebase/auth';
import { initiateGoogleSignIn } from '../utils/oauth';
import { initiateAppleSignIn } from '../utils/oauth-apple';
import { handleOAuthCallback, OAuthError } from '../utils/oauth-callback';
import { clearOAuthState } from '../utils/oauth-state';

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const auth = getAuth();
  const clearError = useCallback(() => setError(null), []);

  const processCallback = useCallback(async (url: string) => {
    if (!url.includes('auth/callback')) return;
    setLoading(true); setError(null);
    try {
      await handleOAuthCallback(url);
    } catch (err) {
      setError(err instanceof OAuthError ? err.message : 'Authentication failed.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const unsubscribeAuth = onAuthStateChanged(auth, (u) => {
      setUser(u); setLoading(false);
    });

    let unsubscribeDeepLink: (() => void) | undefined;
    onOpenUrl((urls) => urls.forEach(processCallback))
      .then((unsub) => { unsubscribeDeepLink = unsub; });

    return () => {
      unsubscribeAuth();
      unsubscribeDeepLink?.();        // CRITICAL: clean up the deep-link listener
    };
  }, [auth, processCallback]);

  const signInWithGoogle = useCallback(async () => {
    setError(null); setLoading(true);
    try { await initiateGoogleSignIn(); }
    catch (err) {
      setLoading(false);
      setError(err instanceof OAuthError ? err.message : 'Failed to start sign-in.');
    }
  }, []);

  const signOut = useCallback(async () => {
    await clearOAuthState();
    await firebaseSignOut(auth);
  }, [auth]);

  return <AuthContext.Provider value={{ user, loading, error, signInWithGoogle, signOut, clearError }}>
    {children}
  </AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
```

## Mobile troubleshooting

| Problem | Solution |
|---------|----------|
| Shell plugin URL error on Android | Use `opener` plugin instead of `shell:open` |
| Deep link not received | Scheme in `tauri.conf.json` must match the URL scheme |
| Callback page not found | Firebase Hosting path must match `redirect_uri` |
| App not opening from browser | Verify `deep-link` plugin is initialized in `lib.rs` |
| Apple Sign-In fails | Verify Services ID + domain configuration |
| Token not in callback | Check `response_type` includes `token id_token` |
| CORS errors | Callback page must be on same domain as `redirect_uri` |
| Apple "rawNonce mismatch" | Pass the original nonce, not the SHA-256 hash |

## Official docs

- Tauri `deep-link` plugin: https://v2.tauri.app/plugin/deep-link/
- Tauri `opener` plugin: https://v2.tauri.app/plugin/opener/
- Apple Sign-In Services ID setup: https://developer.apple.com/help/account/configure-app-capabilities/configure-sign-in-with-apple-for-the-web
- Apple Sign-In JS reference: https://developer.apple.com/documentation/sign_in_with_apple/sign_in_with_apple_js
- Firebase Apple OAuth integration: https://firebase.google.com/docs/auth/web/apple
- Android Custom Tabs: https://developer.chrome.com/docs/android/custom-tabs
- iOS ASWebAuthenticationSession (alternative to Custom Tabs): https://developer.apple.com/documentation/authenticationservices/aswebauthenticationsession

## Related

- `authentication.md` -- OAuth/PKCE security architecture, state validation, Firebase signInWithCredential
- `plugins-mobile.md` -- the `deep-link` plugin in the broader mobile context
- `frontend-patterns.md` -- React lifecycle hooks (the `useEffect` cleanup pattern this file uses)
