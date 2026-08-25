# In-App Purchases & Subscriptions

`@choochmeque/tauri-plugin-iap` for Tauri 2 mobile. Backend verification is non-negotiable; client-side validation can be bypassed. The composite local IP is: server-verification snippets, RTDN type-to-action mapping, and the Tauri-specific `obfuscatedAccountId`/`appAccountToken` nuances.

## When to use

Adding subscriptions or one-shot in-app purchases to a Tauri 2 mobile app. For the underlying Android Billing / StoreKit reference, see the official docs links.

## Architecture (memorize this)

```
App (Tauri) -> Backend Server -> Store API (Play / Apple)
     |              |                    |
     | 1. Purchase  |                    |
     | 2. Token --->| 3. Verify -------->|
     |              |<-- 4. Status ------|
     |<-- 5. Grant -|                    |
```

**Backend verification is non-negotiable.** Client-side `getProductStatus()` can be MITM'd, replayed, or spoofed. Always verify the purchase token against the store API server-side before granting access.

## Setup

```bash
npm install @choochmeque/tauri-plugin-iap-api
cargo add tauri-plugin-iap
```

```rust
// lib.rs
.plugin(tauri_plugin_iap::init())
```

```json
// capabilities/default.json
{ "permissions": ["iap:default"] }
```

## Store-side setup (one-time)

### Google Play Console
1. Create subscription product
2. Configure base plans (monthly, yearly)
3. Add offers (free trial, intro price)
4. Enable Grace Period (7-30 days)
5. Configure Account Hold (max 30 days)

### App Store Connect
1. Create subscription group
2. Add subscription products
3. Configure Introductory Offers
4. Enable Billing Grace Period (16 days)

## Gotchas

- **`initialize()` is required on Android** before any other call. Skipping it = silent failure on first purchase.
- **Android: `acknowledgePurchase` MUST run within 3 days** of a successful purchase, otherwise Google auto-refunds. Always check `result.isAcknowledged` and call `acknowledgePurchase(result.purchaseToken)` if false.
- **`obfuscatedAccountId` (Android) and `appAccountToken` (iOS)** are the Tauri-specific fraud-prevention fields. Pass a hashed user ID for Android; a **valid UUID** for iOS (StoreKit rejects non-UUID strings). Use these to detect cross-account fraud server-side.
- **`offerToken` is per-offer on Android** -- products with intro pricing or trials require selecting the right `subscriptionOfferDetails[i].offerToken`. Pass the wrong one = user gets full price instead of the intro.
- **Restore purchases must be wired** -- otherwise users who reinstall lose access. Implement and surface a "Restore Purchases" button in settings.
- **`PurchaseState.PENDING`** (Android) is real -- some users have delayed payment methods. Show "payment pending" UI; do NOT grant access until state transitions to `PURCHASED`.
- **Test mode renewals are accelerated**: Google = every 5 minutes; Apple sandbox = much faster than real time. Plan test scenarios around this.
- **Subscription management deep links** are platform-specific: `https://play.google.com/store/account/subscriptions` (Android) vs `itms-apps://apps.apple.com/account/subscriptions` (iOS).

## Frontend usage (the canonical recipe)

```typescript
import {
  initialize, getProducts, purchase, restorePurchases, acknowledgePurchase,
  getProductStatus, onPurchaseUpdated, PurchaseState,
} from '@choochmeque/tauri-plugin-iap-api';

await initialize();                                                    // Android: required

const products = await getProducts(['premium_monthly', 'premium_yearly'], 'subs');

const status = await getProductStatus('premium_monthly', 'subs');
if (status.isOwned && status.purchaseState === PurchaseState.PURCHASED) {
  // Active subscription
}

const result = await purchase('premium_monthly', 'subs', {
  offerToken: product.subscriptionOfferDetails[0].offerToken,         // Android
  obfuscatedAccountId: hashedUserId,                                  // Android fraud prevention
  obfuscatedProfileId: hashedProfileId,                               // Android fraud prevention
  appAccountToken: '550e8400-e29b-41d4-a716-446655440000',            // iOS (must be UUID)
});

if (result.purchaseToken && !result.isAcknowledged) {
  await acknowledgePurchase(result.purchaseToken);                    // <3 days on Android
}

const restored = await restorePurchases('subs');                      // wire to "Restore" button

await onPurchaseUpdated((purchase) => {
  switch (purchase.purchaseState) {
    case PurchaseState.PURCHASED: /* verify on server, grant access */ break;
    case PurchaseState.PENDING:   /* show pending UI -- don't grant yet */ break;
    case PurchaseState.CANCELED:  /* update UI */ break;
  }
});
```

## Server-side verification

### Google Play (Node)

```typescript
import { google } from 'googleapis';

async function verifyGoogleSubscription(packageName: string, purchaseToken: string) {
  const auth = new google.auth.GoogleAuth({
    keyFile: process.env.GOOGLE_APPLICATION_CREDENTIALS,
    scopes: ['https://www.googleapis.com/auth/androidpublisher'],
  });
  google.options({ auth: await auth.getClient() });

  const response = await google.androidpublisher('v3').purchases.subscriptionsv2.get({
    packageName, token: purchaseToken,
  });

  const lineItem = response.data.lineItems?.[0];
  const expiryTime = new Date(lineItem?.expiryTime || 0);
  return {
    valid: expiryTime > new Date(),
    expiresAt: expiryTime,
    autoRenewing: lineItem?.autoRenewingPlan?.autoRenewEnabled,
  };
}
```

### App Store (Node, with `@apple/app-store-server-library`)

```typescript
import { SignedDataVerifier } from '@apple/app-store-server-library';

async function verifyAppleTransaction(signedTransaction: string) {
  const verifier = new SignedDataVerifier(
    rootCertificates, true, environment,                                 // 'Production' | 'Sandbox'
    bundleId, appAppleId,
  );
  const transaction = await verifier.verifyAndDecodeTransaction(signedTransaction);
  return {
    valid: true,
    productId: transaction.productId,
    expiresAt: transaction.expiresDate ? new Date(transaction.expiresDate) : undefined,
    autoRenewing: transaction.autoRenewStatus === 1,
  };
}
```

## Real-time notifications -- type-to-action mapping (the local table)

### Google Play (Cloud Pub/Sub)

| Type | Constant | Action |
|------|----------|--------|
| 1 | `SUBSCRIPTION_RECOVERED` | Activate |
| 2 | `SUBSCRIPTION_RENEWED` | Activate |
| 3 | `SUBSCRIPTION_CANCELED` | Mark "will not renew" (still active until expiry) |
| 4 | `SUBSCRIPTION_PURCHASED` | Activate |
| 5 | `SUBSCRIPTION_ON_HOLD` | Suspend access + notify user (payment issue) |
| 6 | `SUBSCRIPTION_IN_GRACE_PERIOD` | Continue access + notify user |
| 7 | `SUBSCRIPTION_RESTARTED` | Activate |
| 12 | `SUBSCRIPTION_REVOKED` | Revoke access |
| 13 | `SUBSCRIPTION_EXPIRED` | Revoke access |

```typescript
function handleGoogleRTDN(notification) {
  const { notificationType, purchaseToken } = notification.subscriptionNotification;
  switch (notificationType) {
    case 1: case 2: case 4: case 7: activateSubscription(purchaseToken); break;
    case 3: markWillNotRenew(purchaseToken); break;
    case 5: suspendAccess(purchaseToken); notifyUser('Payment issue'); break;
    case 6: notifyUser('Payment issue - access continues'); break;
    case 12: case 13: revokeAccess(purchaseToken); break;
  }
}
```

### App Store Server Notifications V2

```typescript
async function handleAppleNotification(signedPayload: string) {
  const notification = await verifier.verifyAndDecodeNotification(signedPayload);
  const { notificationType, subtype, data } = notification;

  switch (notificationType) {
    case 'SUBSCRIBED':                 handleNewSubscription(data.signedTransactionInfo); break;
    case 'DID_RENEW':                  handleRenewal(data.signedTransactionInfo); break;
    case 'DID_CHANGE_RENEWAL_STATUS':
      if (subtype === 'AUTO_RENEW_DISABLED') markWillNotRenew(data.signedTransactionInfo);
      break;
    case 'DID_FAIL_TO_RENEW':
      if (subtype === 'GRACE_PERIOD') notifyUserPaymentIssue();
      break;
    case 'EXPIRED': case 'REFUND': case 'REVOKE':
      revokeAccess(data.signedTransactionInfo);
      break;
  }
}
```

## Subscription management deep links

```typescript
function openSubscriptionManagement() {
  if (platform === 'android') {
    window.open('https://play.google.com/store/account/subscriptions');
  } else if (platform === 'ios') {
    window.open('itms-apps://apps.apple.com/account/subscriptions');
  }
}
```

## Testing

- **Google Play**: add license testers in Play Console, subscription renewals every 5 minutes in test mode, use test card numbers.
- **App Store**: create Sandbox testers in App Store Connect, StoreKit Configuration files for local testing, accelerated renewals.

## Production checklist

- [ ] Products created in Play Console / App Store Connect
- [ ] Backend verification implemented for both platforms
- [ ] RTDN / Server Notifications endpoints configured
- [ ] Grace period enabled in both stores
- [ ] Restore purchases button surfaced and tested
- [ ] Subscription management deep link works
- [ ] Error handling for `PurchaseState.PENDING` and payment failures
- [ ] Tested with sandbox accounts on both platforms
- [ ] Privacy policy updated to disclose IAP data flows

## Official docs

- Plugin (community): https://github.com/choochmeque/tauri-plugin-iap (npm: `@choochmeque/tauri-plugin-iap-api`)
- Google Play Billing Library: https://developer.android.com/google/play/billing
- Google Play Developer API (subscriptions v2): https://developers.google.com/android-publisher/api-ref/rest/v3/purchases.subscriptionsv2
- Real-Time Developer Notifications (Android): https://developer.android.com/google/play/billing/rtdn-reference
- Apple StoreKit 2: https://developer.apple.com/documentation/storekit
- App Store Server API: https://developer.apple.com/documentation/appstoreserverapi
- App Store Server Notifications V2: https://developer.apple.com/documentation/appstoreservernotifications
- App Store Server Library (Node): https://github.com/apple/app-store-server-library-node

## Related

- `plugins-mobile.md` -- where the IAP plugin lives in the broader mobile-plugin context
- `authentication-mobile.md` -- Tauri user identity (often paired with IAP for entitlements)
- `build-deploy-mobile.md` -- store upload that ships the IAP-enabled binary
- `setup-mobile.md` -- the toolchain underneath
