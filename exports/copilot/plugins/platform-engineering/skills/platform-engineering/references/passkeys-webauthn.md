# Passkeys and WebAuthn

Passkeys (WebAuthn-based credentials) are the default recommendation for new authentication flows in 2025-2026. They replace passwords + TOTP entirely for supported users and mitigate credential phishing at the protocol level.

## MUST

- **Use passkeys as the primary auth factor for new consumer apps.** Apple, Google, and Microsoft all support passkey sync via their respective platform credential managers. Consumer apps that require only a password + TOTP in 2026 should treat that as technical debt.
- **Verify `userVerification: 'required'`** on both registration and authentication for high-value operations (payments, admin actions). `'preferred'` is acceptable for low-risk sign-in.
- **Store credential metadata server-side, not secrets.** The server stores: `credentialId`, `publicKey`, `signCount`, `transports`, `userHandle` (opaque user identifier). Never the private key -- that lives in the authenticator.
- **Validate the `clientDataJSON.origin` matches your RP ID.** Prevents relay attacks. The `rpId` should be the registrable domain (`example.com`, not `www.example.com`) to allow passkey sharing across subdomains.
- **Use `attestation: 'none'` for consumer apps.** Only enterprise or regulated contexts need `'direct'` or `'enterprise'` attestation (and they add significant complexity for marginal value).
- **Rotate `signCount`** server-side -- if a new assertion has a `signCount` lower than what you have stored, treat it as a cloned authenticator and revoke the credential.

## DO

- Use `@simplewebauthn/server` (Node) or `py_webauthn` (Python) or `webauthn4j` (Java). Do NOT hand-roll WebAuthn parsing -- CBOR decoding and attestation verification are historically error-prone.
- Support multiple passkeys per user (one per device is common). Show the user a list with `friendlyName`, last-used timestamp, and let them revoke.
- Offer passkey enrollment as an upgrade path from password + TOTP. Don't force migration; users add passkeys voluntarily and you retire passwords once adoption is sufficient.
- Allow cross-device authentication via QR code (hybrid transport) for users whose primary device doesn't have the credential.
- Instrument passkey success vs fallback rates; if fallback (password) rate is high, your UX is broken.

## DON'T

- Treat `userVerification: 'discouraged'` as acceptable -- it bypasses biometric / PIN verification and defeats the point of passkeys.
- Accept a passkey registration without calling `verifyRegistrationResponse` (or equivalent) on the server. The client-returned `PublicKeyCredential` is attacker-controllable in a compromised browser.
- Use passwordless SMS or email magic links as "passkeys". Those are still phishable; real passkeys are public-key credentials tied to a specific origin.
- Block browsers that don't support WebAuthn (very few remain in 2026). Fall back to a second-best option, don't reject the user.
- Use the same `userHandle` value as the user's email or username. `userHandle` should be an opaque random identifier so that leaking a credential doesn't leak PII.

## Sample server-side verification (Node)

```typescript
import {
  verifyRegistrationResponse,
  verifyAuthenticationResponse,
} from '@simplewebauthn/server';

// Registration
const verification = await verifyRegistrationResponse({
  response: body,
  expectedChallenge: session.challenge,
  expectedOrigin: 'https://example.com',
  expectedRPID: 'example.com',
  requireUserVerification: true,
});

if (!verification.verified) throw new Error('Registration failed');

await db.credentials.insert({
  userId: session.userId,
  credentialId: verification.registrationInfo!.credentialID,
  publicKey: verification.registrationInfo!.credentialPublicKey,
  signCount: verification.registrationInfo!.counter,
  transports: body.response.transports ?? [],
  createdAt: new Date(),
});

// Authentication
const stored = await db.credentials.findByCredentialId(body.id);
if (!stored) throw new Error('Unknown credential');

const auth = await verifyAuthenticationResponse({
  response: body,
  expectedChallenge: session.challenge,
  expectedOrigin: 'https://example.com',
  expectedRPID: 'example.com',
  authenticator: {
    credentialID: stored.credentialId,
    credentialPublicKey: stored.publicKey,
    counter: stored.signCount,
    transports: stored.transports,
  },
  requireUserVerification: true,
});

if (!auth.verified) throw new Error('Authentication failed');

// Detect cloned authenticator
if (auth.authenticationInfo.newCounter <= stored.signCount && stored.signCount !== 0) {
  await db.credentials.revoke(stored.credentialId);
  throw new Error('Cloned authenticator detected');
}

await db.credentials.updateSignCount(stored.credentialId, auth.authenticationInfo.newCounter);
```

## Platform notes

| Platform | Passkey support | Notes |
|----------|-----------------|-------|
| iOS 16+ | Native (iCloud Keychain) | Syncs across Apple devices with same Apple ID |
| Android 9+ | Native (Google Password Manager, Chrome) | Android 14+ adds improved Credential Manager API |
| macOS 13+ | Native (iCloud Keychain) | Can authenticate Android/Windows sites via QR |
| Windows 10/11 | Native (Windows Hello) | Enterprise: Azure AD passkey policies |
| Chrome | All platforms | Credential Manager API |
| Safari | iOS / macOS only | Keychain-backed |
| Firefox | All platforms | Uses OS credential store |
| Edge | Windows / macOS / mobile | Inherits Chrome behavior |

## References
- [WebAuthn Level 3 (2024)](https://www.w3.org/TR/webauthn-3/)
- [FIDO Alliance Passkey Dev Resources](https://fidoalliance.org/passkeys/)
- [SimpleWebAuthn (Node)](https://simplewebauthn.dev/)
- [py_webauthn (Python)](https://github.com/duo-labs/py_webauthn)
- [webauthn4j (Java)](https://github.com/webauthn4j/webauthn4j)
- [passkeys.dev](https://passkeys.dev/)
