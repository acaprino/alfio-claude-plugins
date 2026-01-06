# In-App Purchases & Subscriptions

## Plugin Installation

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

## Architecture

```
App (Tauri) → Backend Server → Store API (Play/Apple)
     │              │                    │
     │ 1. Purchase  │                    │
     │ 2. Token ───▶│ 3. Verify ────────▶│
     │              │◀──── 4. Status ────│
     │◀── 5. Grant──│                    │
```

**Backend required** for security. Client-side validation can be bypassed.

## Store Setup

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

## Frontend Implementation

```typescript
import {
  initialize,
  getProducts,
  purchase,
  restorePurchases,
  acknowledgePurchase,
  getProductStatus,
  onPurchaseUpdated,
  PurchaseState,
} from '@choochmeque/tauri-plugin-iap-api';

// Initialize (required on Android)
await initialize();

// Get products
const products = await getProducts(
  ['premium_monthly', 'premium_yearly'],
  'subs'  // 'subs' or 'inapp'
);

// Check subscription status
const status = await getProductStatus('premium_monthly', 'subs');
if (status.isOwned && status.purchaseState === PurchaseState.PURCHASED) {
  console.log('Active subscription');
  console.log('Auto-renewing:', status.isAutoRenewing);
  console.log('Expires:', new Date(status.expirationTime));
}

// Purchase with options
const result = await purchase('premium_monthly', 'subs', {
  // Android: specific offer token
  offerToken: product.subscriptionOfferDetails[0].offerToken,
  // Android: fraud prevention
  obfuscatedAccountId: hashedUserId,
  obfuscatedProfileId: hashedProfileId,
  // iOS: account tracking (must be valid UUID)
  appAccountToken: '550e8400-e29b-41d4-a716-446655440000',
});

// Acknowledge (required on Android within 3 days)
if (result.purchaseToken && !result.isAcknowledged) {
  await acknowledgePurchase(result.purchaseToken);
}

// Restore purchases
const restored = await restorePurchases('subs');

// Listen for updates
await onPurchaseUpdated((purchase) => {
  switch (purchase.purchaseState) {
    case PurchaseState.PURCHASED:
      // Verify on server, grant access
      break;
    case PurchaseState.PENDING:
      // Show "payment pending" UI
      break;
    case PurchaseState.CANCELED:
      // Update UI
      break;
  }
});
```

## Server-Side Verification

### Google Play (Node.js)
```typescript
import { google } from 'googleapis';

async function verifyGoogleSubscription(
  packageName: string,
  purchaseToken: string
) {
  const auth = new google.auth.GoogleAuth({
    keyFile: process.env.GOOGLE_APPLICATION_CREDENTIALS,
    scopes: ['https://www.googleapis.com/auth/androidpublisher'],
  });

  const androidPublisher = google.androidpublisher('v3');
  google.options({ auth: await auth.getClient() });

  const response = await androidPublisher.purchases.subscriptionsv2.get({
    packageName,
    token: purchaseToken,
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

### App Store (Node.js)
```typescript
import { SignedDataVerifier } from '@apple/app-store-server-library';

async function verifyAppleTransaction(signedTransaction: string) {
  const verifier = new SignedDataVerifier(
    rootCertificates,
    true,
    environment,  // 'Production' or 'Sandbox'
    bundleId,
    appAppleId
  );

  const transaction = await verifier.verifyAndDecodeTransaction(
    signedTransaction
  );

  return {
    valid: true,
    productId: transaction.productId,
    expiresAt: transaction.expiresDate 
      ? new Date(transaction.expiresDate) 
      : undefined,
    autoRenewing: transaction.autoRenewStatus === 1,
  };
}
```

## Real-Time Notifications (RTDN)

### Google Play (Cloud Pub/Sub)
```typescript
const NOTIFICATION_TYPES = {
  SUBSCRIPTION_RECOVERED: 1,
  SUBSCRIPTION_RENEWED: 2,
  SUBSCRIPTION_CANCELED: 3,
  SUBSCRIPTION_PURCHASED: 4,
  SUBSCRIPTION_ON_HOLD: 5,
  SUBSCRIPTION_IN_GRACE_PERIOD: 6,
  SUBSCRIPTION_RESTARTED: 7,
  SUBSCRIPTION_REVOKED: 12,
  SUBSCRIPTION_EXPIRED: 13,
};

function handleGoogleRTDN(notification) {
  const { notificationType, purchaseToken } = notification.subscriptionNotification;
  
  switch (notificationType) {
    case 1: // RECOVERED
    case 2: // RENEWED
    case 4: // PURCHASED
      activateSubscription(purchaseToken);
      break;
    case 3: // CANCELED
      markWillNotRenew(purchaseToken);
      break;
    case 5: // ON_HOLD
      suspendAccess(purchaseToken);
      notifyUser('Payment issue');
      break;
    case 6: // GRACE_PERIOD
      notifyUser('Payment issue - access continues');
      break;
    case 12: // REVOKED
    case 13: // EXPIRED
      revokeAccess(purchaseToken);
      break;
  }
}
```

### App Store Server Notifications V2
```typescript
async function handleAppleNotification(signedPayload: string) {
  const notification = await verifier.verifyAndDecodeNotification(signedPayload);
  const { notificationType, subtype, data } = notification;

  switch (notificationType) {
    case 'SUBSCRIBED':
      handleNewSubscription(data.signedTransactionInfo);
      break;
    case 'DID_RENEW':
      handleRenewal(data.signedTransactionInfo);
      break;
    case 'DID_CHANGE_RENEWAL_STATUS':
      if (subtype === 'AUTO_RENEW_DISABLED') {
        markWillNotRenew(data.signedTransactionInfo);
      }
      break;
    case 'DID_FAIL_TO_RENEW':
      if (subtype === 'GRACE_PERIOD') {
        notifyUserPaymentIssue();
      }
      break;
    case 'EXPIRED':
    case 'REFUND':
    case 'REVOKE':
      revokeAccess(data.signedTransactionInfo);
      break;
  }
}
```

## Testing

### Google Play
- Add license testers in Play Console
- Subscription renewals every 5 minutes in test mode
- Use test card numbers

### App Store
- Create Sandbox testers in App Store Connect
- StoreKit Configuration files for local testing
- Renewals accelerated in sandbox

## Manage Subscription Links

```typescript
function openSubscriptionManagement() {
  if (platform === 'android') {
    window.open('https://play.google.com/store/account/subscriptions');
  } else if (platform === 'ios') {
    window.open('itms-apps://apps.apple.com/account/subscriptions');
  }
}
```

## Checklist

- [ ] Products created in Play Console / App Store Connect
- [ ] Backend verification implemented
- [ ] RTDN / Server Notifications configured
- [ ] Grace period enabled
- [ ] Restore purchases implemented
- [ ] Subscription management link
- [ ] Error handling for payment issues
- [ ] Testing with sandbox accounts
- [ ] Privacy policy updated
