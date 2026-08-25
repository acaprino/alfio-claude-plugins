<!--
Outline inspired by dchuk/claude-code-tauri-skills (tauri-ios-distribution),
which has no license. No upstream text reused. Content written fresh against
Tauri v2 documentation, Apple Developer / App Store Connect docs.
-->

# iOS Distribution (App Store + TestFlight)

End-to-end workflow for shipping a Tauri 2 iOS build to the App Store: certificate and provisioning setup, Xcode signing, `Info.plist` usage descriptions, App Store Connect API key, upload methods, TestFlight, and the rejection patterns reviewers actually flag.

## When to use

You have a working `cargo tauri ios build` and need to move it to TestFlight or the public App Store. For build commands and the mobile build-time gotchas, see `build-deploy-mobile.md`. For CI signing patterns, see `ci-cd-mobile.md`. For Sign in with Apple and deep-link OAuth, see `authentication-mobile.md`.

## Prerequisites

| Item | Where |
|---|---|
| macOS host with Xcode (full IDE, not just Command Line Tools) | App Store |
| Apple Developer Program enrolment ($99/year) | https://developer.apple.com/programs |
| Tauri iOS initialised | `cargo tauri ios init` |
| App Store Connect record for the app | https://appstoreconnect.apple.com |
| Privacy policy URL | required for any listing |
| App Privacy answers ready (data collected, purposes, linkage to identity) | required before submission |

## Bundle identifier and version configuration

```json
{
  "identifier": "com.yourcompany.yourapp",
  "version": "1.0.0",
  "bundle": {
    "iOS": {
      "bundleVersion": "1"
    }
  }
}
```

| Field | Maps to | Rules |
|---|---|---|
| `identifier` | `CFBundleIdentifier` | Reverse-domain. Must match the App ID registered in App Store Connect. Cannot be changed after first release. |
| `version` | `CFBundleShortVersionString` | User-visible semver. App Store displays this. Must be greater than the previously approved version when you release. |
| `bundleVersion` | `CFBundleVersion` | Build number. Must strictly increase on every TestFlight or App Store upload, even within the same `version`. |

A common CI pattern keeps `version` aligned with semver and uses an integer build counter for `bundleVersion`.

## Register the App ID

1. Apple Developer -> Certificates, Identifiers & Profiles -> Identifiers -> Add.
2. App IDs -> App.
3. Bundle ID: Explicit, matching `identifier` byte-for-byte.
4. Enable only the capabilities you will actually request (Push Notifications, Associated Domains, Sign in with Apple, etc.). Unused capabilities in the App ID generate provisioning churn later.

Once registered, also create the listing in App Store Connect (My Apps -> + -> New App). Bundle ID, primary language, SKU (any unique string), and user access level are required at create time.

## Code signing setup

Two artefacts are required: a Distribution certificate (private key on the build machine) and a Distribution provisioning profile (binds the cert to the App ID).

### Distribution certificate

1. Keychain Access -> Certificate Assistant -> Request a Certificate From a Certificate Authority. Email and name. Save to disk; do not upload to the CA from Keychain (that path is for Apple Mail).
2. Apple Developer -> Certificates -> Add -> Apple Distribution.
3. Upload the `.certSigningRequest` from step 1.
4. Download the resulting `.cer` and double-click. The private key in Keychain Access pairs with it automatically.
5. Export the matched cert+key as a `.p12` for backup (right-click in Keychain -> Export -> set a password). Store the `.p12` and password securely; this is what you need to reproduce signing on a new machine or in CI.

### Distribution provisioning profile

1. Apple Developer -> Profiles -> Add -> App Store.
2. Pick the App ID.
3. Pick the Distribution certificate.
4. Name it (e.g. `MyApp_AppStore`) and download the `.mobileprovision`.
5. Install by double-click (Xcode imports it) or copy into `~/Library/MobileDevice/Provisioning Profiles/`.

Regenerate the profile after any capability change on the App ID; an outdated profile produces "entitlements do not match" at archive time.

## Xcode signing configuration

```bash
cargo tauri ios build --open
```

Then in Xcode:

1. Select the project, then the app target.
2. Signing & Capabilities tab.
3. For **manual signing** (recommended for CI parity): uncheck "Automatically manage signing", pick the Team, pick the Distribution provisioning profile.
4. For **local-only convenience**: leave automatic signing on. Xcode handles cert and profile rotation for that machine but the same project will not build cleanly in CI without manual overrides.

Add capabilities here only when you have already enabled them on the App ID. Mismatch is the most frequent cause of "Provisioning profile doesn't include capability" build errors.

## `Info.plist` essentials

Tauri generates `src-tauri/gen/apple/<AppName>_iOS/Info.plist`. Keep it under version control even though it lives inside `gen/`; the file frequently needs hand-edits Tauri does not yet round-trip. Required keys for any App Store build:

```xml
<key>CFBundleDisplayName</key>            <string>My App</string>
<key>CFBundleIdentifier</key>             <string>$(PRODUCT_BUNDLE_IDENTIFIER)</string>
<key>CFBundleShortVersionString</key>     <string>$(MARKETING_VERSION)</string>
<key>CFBundleVersion</key>                <string>$(CURRENT_PROJECT_VERSION)</string>
<key>LSRequiresIPhoneOS</key>             <true/>
<key>UILaunchStoryboardName</key>         <string>LaunchScreen</string>
<key>UISupportedInterfaceOrientations</key>
<array>
  <string>UIInterfaceOrientationPortrait</string>
</array>
```

### Usage descriptions

Any time the OS prompts the user for a sensitive resource, the binary must ship a non-empty purpose string. Reviewers grep these. Add only the keys for resources you actually request.

| Key | Triggered by |
|---|---|
| `NSCameraUsageDescription` | AVCaptureDevice / camera plugin |
| `NSPhotoLibraryUsageDescription` | Photo picker / Photos framework read |
| `NSPhotoLibraryAddUsageDescription` | Saving to Photos |
| `NSMicrophoneUsageDescription` | Audio capture |
| `NSLocationWhenInUseUsageDescription` | CLLocationManager foreground |
| `NSLocationAlwaysAndWhenInUseUsageDescription` | Background location |
| `NSContactsUsageDescription` | Contacts framework |
| `NSFaceIDUsageDescription` | Local Authentication / biometric plugin in Face ID mode |
| `NSBluetoothAlwaysUsageDescription` | Core Bluetooth |
| `NSUserTrackingUsageDescription` | App Tracking Transparency prompt (iOS 14.5+) |

Each string must be specific and human-readable. "Required for app functionality" is the canonical rejection bait; "Used to read product barcodes during checkout" passes.

### Encryption export compliance

If your app does not use non-exempt encryption beyond standard HTTPS, declare it to skip the per-build re-prompt:

```xml
<key>ITSAppUsesNonExemptEncryption</key>
<false/>
```

If you do use custom crypto, leave the key absent and answer the prompt in App Store Connect on every upload, or set the key to `true` and provide the export-compliance documentation.

## App icons

Source: 1024x1024 PNG, no transparency.

```bash
cargo tauri icon /absolute/path/app-icon.png
```

This populates `src-tauri/gen/apple/Assets.xcassets/AppIcon.appiconset/` with every size Apple expects. Validate the icon set by opening the asset catalogue in Xcode: any missing slot is shown as a dashed border.

## App Store Connect API key

API key (`.p8`) authenticates uploads from `xcrun altool`, Transporter, fastlane, and most CI integrations. Beats Apple ID + app-specific password by a wide margin: no MFA prompts, key-level revocation, less brittle.

1. App Store Connect -> Users and Access -> Integrations -> App Store Connect API.
2. Generate API Key. Pick the Access role (Developer is enough for uploads). Note the Key ID and Issuer ID.
3. Download `AuthKey_<KeyID>.p8`. One-shot download; if you lose it you must revoke and regenerate.

Conventional locations the Apple toolchain auto-discovers:

```bash
mkdir -p ~/.appstoreconnect/private_keys
mv ~/Downloads/AuthKey_<KEYID>.p8 ~/.appstoreconnect/private_keys/
```

For CI, store the `.p8` content as a secret, re-materialise into one of the discovery paths before running `altool`.

## Upload methods

| Method | Best for | Notes |
|---|---|---|
| `xcrun altool --upload-app` | Headless, CI, scriptable releases | Uses ASC API key. Requires the IPA path, `--type ios`, `--apiKey`, `--apiIssuer`. |
| Transporter app (Mac App Store) | Manual GUI uploads, signing diagnostics | Free Apple-published GUI for IPA uploads. Shows pre-upload validation errors. |
| Xcode Organizer -> Distribute App | Manual archive flow | Window -> Organizer after `Product -> Archive`. Walks through validation, signing re-check, and upload. |

CLI upload:

```bash
xcrun altool --upload-app \
  --type ios \
  --file "src-tauri/gen/apple/build/arm64/MyApp.ipa" \
  --apiKey "$APPLE_API_KEY_ID" \
  --apiIssuer "$APPLE_API_ISSUER"
```

Validate first (catches signing problems without consuming an App Store Connect upload slot):

```bash
xcrun altool --validate-app \
  --type ios --file ... --apiKey ... --apiIssuer ...
```

After upload, the build appears in App Store Connect after processing (typically 5-30 minutes; sometimes longer when Apple is busy).

## TestFlight

Apple's first-party beta channel. Two tiers:

| Tier | Audience | Review needed |
|---|---|---|
| Internal | Up to 100 testers who are App Store Connect users on your team | None. Builds become available immediately after processing. |
| External | Up to 10,000 testers via email or public link | Yes. First build per `version` triggers Beta App Review (typically faster than App Store review). |

External groups can run multiple builds per `version` after the first one is approved, as long as `bundleVersion` keeps incrementing. Beta builds expire 90 days after upload.

## App Store listing prep

Assets and metadata you cannot ship without:

| Asset | Spec |
|---|---|
| App icon | 1024x1024, PNG, no alpha |
| Screenshots | iPhone 6.7" (1290x2796) is the canonical required size; 6.5", 5.5" optional but recommended. iPad 12.9" required if you ship an iPad build. |
| Description | Up to 4000 chars |
| Promotional text | 170 chars, can change without re-review |
| Keywords | 100 chars total, comma-separated |
| Support URL | Reachable; reviewers click |
| Marketing URL | Optional but useful |
| Privacy policy URL | Required |
| Age rating | Set via the questionnaire in App Store Connect |

## App Privacy questionnaire

App Store Connect -> App Privacy. Required before submission. Answer honestly; bad-faith answers are an explicit App Review Guidelines violation (5.1). Cover:

- Data types collected (device IDs, location, usage data, contact info, ...)
- For each type: purpose (analytics, app functionality, advertising, personalisation, ...)
- For each type: linked vs not linked to identity
- For each type: used for tracking across other apps/sites (triggers the AppTrackingTransparency prompt)

The form should mirror what every network request from your app, every analytics SDK, and every backend it talks to actually does. Reviewers cross-check against headers and SDK behaviour.

## Submit for review

1. App Store Connect -> Your app -> + Version (or fill in version 1.0).
2. Pick the uploaded build.
3. Fill version-level metadata (what's new, screenshots, description).
4. Answer Export Compliance prompt (skipped if `ITSAppUsesNonExemptEncryption` is set in `Info.plist`).
5. Provide test credentials in App Review Information if the app gates content behind login.
6. Submit for review.

Review SLA: typically 24-48h on subsequent versions, occasionally longer for first submissions or holiday windows.

## Common errors

| Symptom | Root cause | Fix |
|---|---|---|
| "No signing certificate" at archive | Distribution cert not in the build machine's Keychain | Re-import the `.p12`. Check with `security find-identity -v -p codesigning`. |
| "Provisioning profile doesn't match the bundle identifier" | App ID, profile, and `identifier` drift | Confirm all three match exactly. Regenerate profile if you changed App ID capabilities. |
| "Missing entitlements" | Capability enabled in Xcode without matching App ID flip | Update the App ID, regenerate profile, re-download. |
| "Invalid binary: Missing usage description" | Symbol references a sensitive resource without the matching `NS*UsageDescription` | Add the key, rebuild. Check the email Apple sends; it names the missing key. |
| Build stuck in "Processing" for hours | Validation snag (often missing icon, malformed entitlements, or transient ASC delay) | Wait 1-2h; if no progress, re-validate with `xcrun altool --validate-app` against the same IPA. |
| "Missing compliance" prompt blocking submission | No export-compliance answer | Set `ITSAppUsesNonExemptEncryption` in `Info.plist` or answer the prompt in App Store Connect. |
| TestFlight build invitations not arriving | Tester signed in to multiple Apple IDs | Have the tester open TestFlight, switch account, and re-accept the invite. |

## CI sketch (GitHub Actions)

The actual content depends on whether you push to a self-hosted Mac runner or `macos-latest`. Skeleton for `macos-latest`:

1. Restore the Distribution `.p12` from a base64 secret into a temp keychain. Unlock the keychain. Add it to the search list.
2. Restore the provisioning profile into `~/Library/MobileDevice/Provisioning Profiles/`.
3. Restore the App Store Connect `.p8` API key.
4. Install Rust with the `aarch64-apple-ios` target.
5. `npm ci`, then `cargo tauri ios build --export-method app-store-connect`.
6. `xcrun altool --upload-app` using the API key.

Secrets to provision: `APPLE_CERT_BASE64`, `APPLE_CERT_PASSWORD`, `APPLE_PROVISIONING_PROFILE_BASE64`, `APPLE_API_KEY_BASE64`, `APPLE_API_KEY_ID`, `APPLE_API_ISSUER`, `APPLE_TEAM_ID`.

## Version-increment helper

```bash
#!/usr/bin/env bash
# bump-ios-build.sh
set -euo pipefail
CFG="src-tauri/tauri.conf.json"
CURRENT=$(jq -r '.bundle.iOS.bundleVersion' "$CFG")
NEXT=$((CURRENT + 1))
tmp=$(mktemp)
jq ".bundle.iOS.bundleVersion = \"$NEXT\"" "$CFG" > "$tmp" && mv "$tmp" "$CFG"
echo "bundleVersion: $CURRENT -> $NEXT"
```

## Resources

- Tauri iOS distribution: https://v2.tauri.app/distribute/app-store/
- Apple Developer Program: https://developer.apple.com/programs/
- App Store Connect: https://appstoreconnect.apple.com
- App Review Guidelines: https://developer.apple.com/app-store/review/guidelines/
- App Store Connect API: https://developer.apple.com/documentation/appstoreconnectapi
- `xcrun altool`: https://developer.apple.com/documentation/xcode/altool
- Encryption export compliance: https://developer.apple.com/documentation/security/complying_with_encryption_export_regulations
- App Privacy details on the App Store: https://developer.apple.com/app-store/app-privacy-details/

## Related local references

- `build-deploy-mobile.md` -- build commands and the mobile build-time pitfalls
- `ci-cd-mobile.md` -- CI signing patterns
- `setup-mobile.md` -- toolchain prerequisites
- `authentication-mobile.md` -- Sign in with Apple, deep-link OAuth
- `plugins-mobile.md` -- biometric prompts and other plugins that drive `Info.plist` usage descriptions
