# Authentication Token Storage and OAuth Flows

Token storage is where most authentication implementations fail. The correct approach differs significantly by platform.

## MUST

- **Never store JWTs in localStorage or sessionStorage on web platforms (SPA/PWA).** Any XSS vulnerability enables `localStorage.getItem('token')` to exfiltrate every user's session. Store access tokens in JavaScript memory (variables, React context, closures) and refresh tokens in httpOnly + Secure + SameSite=Strict cookies.
  - Privasec red team: a stored XSS vulnerability on a site using localStorage JWTs allowed the attacker to steal every visiting user's token and hijack their sessions. HttpOnly cookies would have blocked JavaScript access entirely.

- **Use short-lived access tokens (5-15 minutes) with rotating refresh tokens.** Issue a new refresh token with each access-token renewal and invalidate the old one. Limits blast radius of token theft.

- **Use the correct OAuth 2.0 flow per platform:**

| Platform | OAuth Flow |
|----------|-----------|
| **SPA/PWA** | Authorization Code + PKCE (implicit flow deprecated by OAuth 2.1) |
| **Mobile** | System browser + PKCE -- never use embedded WebViews for OAuth login (credential interception risk). Use ASWebAuthenticationSession (iOS), Custom Tabs (Android) |
| **Desktop** | Standard PKCE |

- **Store tokens in platform-native secure storage on mobile and desktop:**

| Platform | Secure Storage |
|----------|---------------|
| **iOS** | Keychain with `kSecAttrAccessibleWhenUnlockedThisDeviceOnly` |
| **Android** | Keystore with EncryptedSharedPreferences |
| **macOS** | Keychain |
| **Windows** | Credential Manager |
| **Linux** | libsecret |

- Never use SharedPreferences, NSUserDefaults, or plain-text files.

## DO

- Use RS256 (asymmetric) for JWTs verified by multiple services; HS256 only when a single service both signs and verifies.
- Add MFA for sensitive operations.
- Implement token revocation and blacklisting server-side.

## DON'T

- Use the JWT `none` algorithm -- always validate the `alg` header server-side.
- Embed sensitive user data in JWT payloads (they're base64-encoded, not encrypted).
- Store credentials in Android SharedPreferences or iOS NSUserDefaults without hardware-backed encryption.
