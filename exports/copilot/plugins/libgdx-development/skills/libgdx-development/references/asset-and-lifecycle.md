# Assets and Lifecycle

AssetManager async loading, disposal discipline, Screen lifecycle, input processor management.

## AssetManager

`AssetManager` is libGDX's central asset loader. It handles async loading on a worker thread, dependency resolution (a Skin depending on a TextureAtlas), reference counting, and unloading.

### Basic Workflow
```java
AssetManager assets = new AssetManager();

// Queue loads (returns immediately)
assets.load("atlas/game.atlas", TextureAtlas.class);
assets.load("ui/skin.json", Skin.class);
assets.load("audio/music.ogg", Music.class);
assets.load("audio/jump.wav", Sound.class);

// In your render loop, pump:
if (assets.update()) {
    // All queued loads complete
    TextureAtlas atlas = assets.get("atlas/game.atlas", TextureAtlas.class);
    Skin skin = assets.get("ui/skin.json", Skin.class);
}
```

### update() return value
`update()` returns true when ALL queued assets are loaded. Returns false otherwise. Use `getProgress()` (0..1) for progress bars.

### Pumping in a Loading Screen
The default `update()` once per frame is too slow for snappy loading; the AssetManager async worker is rate-limited by the call frequency. On a dedicated loading screen, pump multiple times per frame:
```java
@Override
public void render(float delta) {
    ScreenUtils.clear(0, 0, 0, 1);
    for (int i = 0; i < 4 && !assets.update(); i++) {
        // Pump up to 4 times per frame
    }
    progressBar.setValue(assets.getProgress());
    if (assets.isFinished()) game.setScreen(new GameplayScreen(game));
}
```

### Custom Loaders
For custom asset types (e.g. binary level files), implement `AsynchronousAssetLoader<MyType, MyParameter>`. Register with `assets.setLoader(MyType.class, new MyLoader(...))`.

### Reference Counting
Each `load()` increments a refcount. `unload()` decrements. When refcount hits zero, the asset is disposed. This lets multiple screens share assets cleanly:
```java
// MainMenu calls
assets.load("atlas/ui.atlas", TextureAtlas.class);

// Gameplay also loads
assets.load("atlas/ui.atlas", TextureAtlas.class);  // refcount = 2

// MainMenu hide()
assets.unload("atlas/ui.atlas");  // refcount = 1, NOT disposed

// Gameplay dispose()
assets.unload("atlas/ui.atlas");  // refcount = 0, disposed
```

### finishLoadingAsset() pitfall
`finishLoadingAsset(path)` blocks until the named asset is loaded. Convenient for early-game critical assets, BUT combined with `AbsoluteFileHandleResolver` it can deadlock (see libgdx#4888). Prefer pumping `update()` in a loading screen over blocking.

## Disposal Discipline

OpenGL resources are NOT garbage-collected. Every Texture, Sound, Music, Skin, BitmapFont, ShaderProgram, FrameBuffer, Stage you create must be explicitly disposed.

### Ownership Rules
- If you `new`'d it, you dispose it
- If `AssetManager` loaded it, AssetManager owns it. Call `unload(path)` or `dispose()` on the manager, NEVER call `dispose()` on the asset directly
- If a parent owns it (e.g. `Stage` owns its `Batch` if you used the no-arg constructor), the parent disposes it
- `TextureAtlas.dispose()` disposes all contained textures
- `Skin.dispose()` disposes its TextureAtlas and BitmapFonts

### Common Leak Sources
1. Forgetting to dispose a `Skin` constructed with `new Skin(Gdx.files.internal("..."))` instead of using AssetManager
2. Creating `new Texture(...)` per frame or per entity instead of using an atlas
3. Re-creating `FrameBuffer` on resize without disposing the old one
4. Re-creating `BitmapFont` via `FreeTypeFontGenerator` without disposing the previous generation
5. Holding a static field reference (also causes Android-lifecycle bugs)

### Static Fields Are Forbidden
NEVER make AssetManager, Texture, Sound, Skin, or any OpenGL resource a `static` field:
```java
// WRONG
public class Assets {
    public static AssetManager assets = new AssetManager();  // BREAKS on Android
}
```
Why: Android may kill the rendering context (`pause`) while the JVM stays alive. The static reference persists into the next session, but the underlying GPU resource has been destroyed. Symptom: black/missing textures after resume.

Correct: hold AssetManager as an instance field of `Game`, or pass it via constructor into Screens.

### Dispose Checklist for a Screen
```java
public class GameplayScreen extends ScreenAdapter {
    private Stage stage;
    private FrameBuffer fbo;
    private ShaderProgram blurShader;
    private ParticleEffect explosion;

    @Override
    public void dispose() {
        stage.dispose();
        fbo.dispose();
        blurShader.dispose();
        explosion.dispose();
        // Do NOT dispose Skin, atlases, music here if loaded via AssetManager;
        // those are managed centrally
    }
}
```

## Screen Lifecycle

`Screen` interface methods, called by `Game`:

| Method | When |
|--------|------|
| `show()` | Screen becomes active. Set input processor, start music |
| `render(delta)` | Each frame |
| `resize(w, h)` | Window/screen resized. Update viewport |
| `pause()` | App lost focus (Android background, desktop alt-tab) |
| `resume()` | App regained focus |
| `hide()` | Screen swapped out. Null input processor, stop music |
| `dispose()` | Screen destroyed permanently. Free resources |

### Input Processor Pattern
ALWAYS set input processor in `show()` (not constructor):
```java
@Override
public void show() {
    InputMultiplexer mux = new InputMultiplexer();
    mux.addProcessor(stage);
    mux.addProcessor(gameplayInput);
    Gdx.input.setInputProcessor(mux);
}

@Override
public void hide() {
    Gdx.input.setInputProcessor(null);
}
```
Setting in constructor: input processor is set before the screen is visible, which can intercept clicks on the previous screen during transition animations.

### Resize Pattern
```java
@Override
public void resize(int width, int height) {
    viewport.update(width, height, true);  // true = center camera
    stage.getViewport().update(width, height, true);
}
```

### Pause/Resume on Android
On Android, the rendering context can be destroyed during pause and recreated on resume. libGDX handles most of this transparently if you use AssetManager, but:
- Sounds and Music may need to be restarted manually
- Custom shaders may need to be recompiled (libGDX handles this for `ShaderProgram` if you use it standard)
- Custom OpenGL state (uniform values not re-applied each frame) may need to be re-set

## Tiled Map Integration

`.tmx` files from the Tiled Map Editor (https://www.mapeditor.org/) are natively supported.

### Loading
```java
TmxMapLoader loader = new TmxMapLoader();
TiledMap map = loader.load("maps/level01.tmx");
OrthogonalTiledMapRenderer renderer = new OrthogonalTiledMapRenderer(map);

// In render:
renderer.setView(camera);
renderer.render();
```

For better packing, use `AtlasTmxMapLoader` with a pre-packed atlas:
```java
AtlasTmxMapLoader loader = new AtlasTmxMapLoader();
TiledMap map = loader.load("maps/level01.tmx", params);
```

### libGDX 1.14.0 Tiled Changes
- `TmxMapLoader` and `AtlasTmxMapLoader` share a unified base
- Class objects supported (Tiled's typed object system)
- Template objects supported

### Object Layers
Tiled object layers map to `MapObject` instances. Iterate to spawn entities:
```java
MapLayer objects = map.getLayers().get("objects");
for (MapObject obj : objects.getObjects()) {
    if (obj.getProperties().get("type", String.class).equals("spawn")) {
        float x = obj.getProperties().get("x", Float.class);
        float y = obj.getProperties().get("y", Float.class);
        spawnPlayer(x, y);
    }
}
```

## Audio Lifecycle

- **Sound**: small, fully decoded, played multiple times. Use for SFX (< 1 second)
- **Music**: streamed, played once at a time per instance. Use for background music

### Common Patterns
```java
Sound jump = assets.get("audio/jump.wav", Sound.class);
long id = jump.play(0.7f);  // volume; returns instance ID

Music bgm = assets.get("audio/level1.ogg", Music.class);
bgm.setLooping(true);
bgm.setVolume(0.5f);
bgm.play();
```

### Audio on Android
- OGG Vorbis is the safest format across all platforms
- WAV works but is large
- MP3 has licensing concerns and partial Android support
- iOS prefers M4A; libGDX can handle but watch encoding

### Stopping Audio on hide()
```java
@Override
public void hide() {
    bgm.stop();
}

@Override
public void dispose() {
    // Music is managed by AssetManager, do not dispose here
}
```

## Save/Load State

libGDX provides `Preferences` for small key-value storage (cross-platform):
```java
Preferences prefs = Gdx.app.getPreferences("MyGameSave");
prefs.putInteger("highScore", score);
prefs.flush();

int score = prefs.getInteger("highScore", 0);
```

For larger save files, use the `Json` class with serializable objects:
```java
Json json = new Json();
String save = json.toJson(saveState);
Gdx.files.local("save.json").writeString(save, false);

SaveState loaded = json.fromJson(SaveState.class, Gdx.files.local("save.json"));
```
Note: In libGDX 1.14.0, `JsonValue#get(String)` is case-sensitive. Audit any save files with mixed-case keys.

## Source References

- https://libgdx.com/wiki/managing-your-assets
- https://libgdx.com/wiki/file-handling
- https://libgdx.com/wiki/audio
- https://libgdx.com/wiki/preferences
- https://libgdx.com/wiki/graphics/2d/tile-maps
- https://github.com/libgdx/libgdx/issues/6642 (static AssetManager pitfall)
- https://github.com/libgdx/libgdx/issues/4888 (finishLoadingAsset deadlock)
