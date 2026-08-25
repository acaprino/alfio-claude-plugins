# Deployment Platforms

Targeting Desktop (LWJGL3), Android, iOS (RoboVM), and HTML5 (GWT/TeaVM) from a shared libGDX codebase.

## Desktop (LWJGL3)

The Desktop backend uses LWJGL3 (Lightweight Java Game Library 3) for windowing, input, and OpenGL.

### Launcher
```java
public class Lwjgl3Launcher {
    public static void main(String[] args) {
        Lwjgl3ApplicationConfiguration config = new Lwjgl3ApplicationConfiguration();
        config.setTitle("My Game");
        config.setWindowedMode(1280, 720);
        config.setForegroundFPS(60);
        config.useVsync(true);
        config.setWindowIcon("icon128.png", "icon32.png", "icon16.png");
        new Lwjgl3Application(new MyGame(), config);
    }
}
```

### Build Outputs
- `:lwjgl3:run` -- launch in IDE
- `:lwjgl3:dist` -- builds a fat JAR with all dependencies bundled (large, ~50-100 MB for a typical game)
- `:lwjgl3:jpackage` (manual setup) -- builds platform-native installers via `jpackage`

### Packaging Options
1. **Fat JAR**: simplest distribution; requires user to have Java installed; runs with `java -jar mygame.jar`
2. **jpackage**: ships a bundled JDK runtime and creates `.exe`/`.dmg`/`.deb` installers. Recommended for end-user distribution. Requires JDK 14+ on the build machine
3. **PackR** (community): older alternative to jpackage; bundles a minimal JRE; still works but jpackage is the modern path
4. **Steam**: distribute as fat JAR or jpackage build; Steam runtime handles launching

### LWJGL3 Version
libGDX 1.14.0 ships LWJGL3 3.4.1 by default, which supports Java 25+. Earlier libGDX shipped LWJGL3 3.3.x.

### Window and Fullscreen
```java
config.setWindowedMode(1280, 720);
// or
Graphics.DisplayMode primary = Lwjgl3ApplicationConfiguration.getDisplayMode();
config.setFullscreenMode(primary);

// In-game toggle:
Gdx.graphics.setFullscreenMode(Gdx.graphics.getDisplayMode());
Gdx.graphics.setWindowedMode(1280, 720);
```

### Audio Backends
LWJGL3 uses OpenAL via `OpenALAudio`. No configuration usually needed.

## Android

The Android backend uses native libraries and runs on the GLSurfaceView thread.

### Project Layout
```
android/
  AndroidManifest.xml
  build.gradle              # Android-specific Gradle config
  src/main/java/.../android/AndroidLauncher.java
  res/                      # icons, drawables
  assets/                   # shared with the game (symlinked or referenced from core)
```

### Launcher
```java
public class AndroidLauncher extends AndroidApplication {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        AndroidApplicationConfiguration config = new AndroidApplicationConfiguration();
        config.useImmersiveMode = true;
        initialize(new MyGame(), config);
    }
}
```

### Recommended Versions (2025-2026)
- `compileSdk = 34` or 35
- `targetSdk = 34` or 35 (Play Store requires 34+ for new submissions as of August 2024)
- `minSdk = 21` (covers ~99% of active devices)
- `kotlin = "1.9+"` if using Kotlin

### Build Outputs
- `:android:installDebug` -- install debug APK to connected device
- `:android:assembleRelease` -- release APK (requires signing)
- `:android:bundleRelease` -- AAB (Android App Bundle); required for Play Store

### Signing
Add to `android/build.gradle`:
```gradle
android {
    signingConfigs {
        release {
            storeFile file(System.getenv("KEYSTORE_PATH"))
            storePassword System.getenv("KEYSTORE_PASSWORD")
            keyAlias System.getenv("KEY_ALIAS")
            keyPassword System.getenv("KEY_PASSWORD")
        }
    }
    buildTypes {
        release {
            signingConfig signingConfigs.release
            minifyEnabled false  // libGDX + Proguard requires careful rule tuning
        }
    }
}
```

### Permissions
Add to `AndroidManifest.xml` only what you need:
- `android.permission.INTERNET` for networked games
- `android.permission.VIBRATE` for `Gdx.input.vibrate(...)`
- Storage permissions are no longer needed for `Gdx.files.local(...)`

### Android-Specific Lifecycle
- `pause()` is called when the activity backgrounds
- `resume()` is called when it returns to foreground
- The OpenGL context may be destroyed; libGDX recreates Textures from cached pixmaps where possible. Custom GPU resources may need manual recreation
- AssetManager-managed assets survive pause/resume

### Immersive Mode
Hide system bars during gameplay:
```java
config.useImmersiveMode = true;
```

### Gradle Plugin Compatibility
libGDX 1.14.0 supports recent Android Gradle Plugin versions (8.x). Always match the Android Gradle Plugin to the Gradle version (8.x AGP requires Gradle 8.x+).

## iOS (RoboVM)

iOS deployment uses RoboVM, an AOT compiler that converts Java bytecode to native ARM. RoboVM is now maintained by the libGDX team after the Microsoft acquisition shutdown.

### Constraints
- **Java 8 language level cap**: RoboVM does not support Java 9+ syntax or APIs. Your core module must compile against Java 8 if it targets iOS
- **macOS-only builds**: Xcode is required; you cannot produce iOS builds from Linux or Windows
- **Apple Developer account required** for App Store distribution

### Project Layout
```
ios/
  build.gradle
  robovm.properties      # app id, version, build type
  robovm.xml             # frameworks, resources, info.plist
  src/main/java/.../ios/IOSLauncher.java
```

### Launcher
```java
public class IOSLauncher extends IOSApplication.Delegate {
    @Override
    protected IOSApplication createApplication() {
        IOSApplicationConfiguration config = new IOSApplicationConfiguration();
        return new IOSApplication(new MyGame(), config);
    }

    public static void main(String[] argv) {
        NSAutoreleasePool pool = new NSAutoreleasePool();
        UIApplication.main(argv, null, IOSLauncher.class);
        pool.close();
    }
}
```

### Build Tasks
- `:ios:launchIPhoneSimulator` -- run in iOS Simulator
- `:ios:launchIPadSimulator` -- iPad simulator
- `:ios:createIPA` -- build a signed IPA for distribution

### Signing
Configure in `robovm.properties`:
```
app.id=com.example.mygame
app.version=1.0.0
app.build=1
app.name=MyGame
app.executable=MyGame
```

Provisioning profile and signing identity are configured per build via Xcode.

### iOS-Specific Constraints
- No reflection on classes that aren't explicitly forced-linked. Add `<forceLinkClasses>` entries in `robovm.xml` for any class loaded via reflection
- Larger app size due to AOT compilation
- Floating-point performance is good on iOS hardware

## HTML5 (GWT)

The HTML5 backend compiles Java to JavaScript via GWT (Google Web Toolkit).

### Constraints
- **Java only**: Kotlin is NOT compatible with GWT
- **No reflection**: classes must be explicitly listed in the GWT module XML
- **Limited Java API**: some `java.util` and `java.text` APIs are not implemented in GWT
- **Slow builds**: full GWT compile can take 1-5 minutes on first build
- **Larger asset sizes** are awkward over network; lazy-load if possible

### Project Layout
```
html/
  build.gradle
  src/main/java/.../html/HtmlLauncher.java
  src/main/java/.../GdxDefinition.gwt.xml
  src/main/java/.../GdxDefinitionSuperdev.gwt.xml
  webapp/index.html
```

### Launcher
```java
public class HtmlLauncher extends GwtApplication {
    @Override
    public GwtApplicationConfiguration getConfig() {
        return new GwtApplicationConfiguration(640, 480);
    }

    @Override
    public ApplicationListener createApplicationListener() {
        return new MyGame();
    }
}
```

### Build Tasks
- `:html:superDev` -- super dev mode; rebuilds on save, runs at http://localhost:8080
- `:html:dist` -- production build to `html/build/dist/`; deploy this directory to a web host

### Audio on HTML
Browsers restrict autoplay; audio must start after user interaction (first click). libGDX handles most of this transparently.

### Reflection Caveats
Add to `GdxDefinition.gwt.xml`:
```xml
<extend-configuration-property name="gdx.reflect.include" value="com.example.MyClass"/>
```
Or use `@GwtIncompatible` to mark Java-only code paths.

## HTML5 (TeaVM) Alternative

TeaVM is a modern alternative to GWT that supports Kotlin and produces smaller, faster output.

### Status (2025-2026)
libGDX TeaVM support is described as "work-in-progress". The community project `xpenatan/gdx-teavm` provides the runtime. Choose TeaVM if:
- You want Kotlin in your HTML build
- You need faster builds than GWT (TeaVM compiles in seconds)
- You can accept some libGDX features may not yet work

Stay on GWT if:
- You need maximum maturity and feature parity
- Your codebase is pure Java
- You rely on extensions known to work on GWT

## Cross-Platform Code Strategy

Keep platform-specific code in the platform module, NEVER in core:
```
core/                  # game logic, rendering, input handling
  uses only Gdx.app, Gdx.gl, Gdx.input, Gdx.files etc.

lwjgl3/                # desktop-specific (jpackage config, native file dialogs)
android/               # Android-specific (Google Play Games, AdMob, permissions)
ios/                   # iOS-specific (Game Center, StoreKit)
html/                  # HTML-specific (browser fullscreen API, web storage)
```

For platform-specific behavior in core code (e.g. "show ad banner"), use the `Gdx.app.getType()` check OR define a platform-abstraction interface in core and implement per-platform:
```java
// In core
public interface AdProvider {
    void showInterstitial();
}

// In android
public class AndroidAdProvider implements AdProvider {
    public void showInterstitial() { /* AdMob calls */ }
}

// In core MyGame constructor
public MyGame(AdProvider ads) { this.ads = ads; }

// In AndroidLauncher
new MyGame(new AndroidAdProvider(this));
```

## Build Pipeline (CI/CD)

Common setup:
- **GitHub Actions** for desktop, Android, HTML5 builds (Linux runners)
- **macOS runners** for iOS builds (separate workflow)
- Cache `~/.gradle` between runs to speed up dependency resolution
- For Android signing in CI, store keystore as base64-encoded secret and decode in pre-build step
- For iOS, store p12 and provisioning profile as base64 secrets; use `xcrun` for signing

## Source References

- https://libgdx.com/wiki/deployment/deploying-your-application
- https://libgdx.com/wiki/deployment/bundling-a-jre-jpackage
- https://libgdx.com/wiki/deployment/deploying-android
- https://libgdx.com/wiki/deployment/deploying-ios
- https://libgdx.com/wiki/deployment/deploying-html5
- https://github.com/xpenatan/gdx-teavm (TeaVM backend)
- https://github.com/MobiVM/robovm (RoboVM iOS compiler)
