# Rendering and Performance

The libGDX rendering pipeline, batching, viewports, frame-budget profiling, and the most common performance pitfalls.

## The Render Loop

`ApplicationListener.render()` is called once per frame on the render thread. `Gdx.graphics.getDeltaTime()` gives elapsed seconds since the last frame.

Frame-time budgets:
- 60 fps: 16.6 ms per frame
- 120 fps: 8.3 ms per frame
- VR / mobile high-refresh: 8.3-11 ms

Anything that exceeds this budget drops the frame rate. On Android, blocking the render thread for too long triggers an ANR (Application Not Responding) dialog.

## Core Rule: Never Block the GL Thread

The render thread is the ONLY thread allowed to call `Gdx.gl.*` or touch OpenGL-backed resources (Texture, Mesh, ShaderProgram, FrameBuffer).

Forbidden on the render thread:
- File IO that isn't going through `AssetManager` async loading
- Network requests
- Heavy CPU work (pathfinding over large grids, decompression, JSON parsing of large blobs)
- Thread.sleep, blocking semaphore acquisitions

Correct pattern: run heavy work on a worker thread and push results back:
```java
new Thread(() -> {
    String json = httpClient.get("https://api.example.com/leaderboard").body();
    Gdx.app.postRunnable(() -> {
        leaderboard.update(parseJson(json));
    });
}).start();
```
`Gdx.app.postRunnable` queues a Runnable to execute on the next render frame.

## SpriteBatch

`SpriteBatch` is the workhorse for 2D rendering. It batches draw calls that share the same Texture, flushing to the GPU when:
- `end()` is called
- A different Texture is bound
- The internal vertex buffer fills (default 1000 sprites per batch)
- A different blend mode is set
- A different shader is set

Cost of a flush: one OpenGL draw call. The dominant performance variable for 2D libGDX games is the number of flushes per frame.

### Reducing flushes
1. Pack sprites into one (or few) atlases so most sprites share a texture
2. Order draw calls by texture, not by entity:
   - All backgrounds (texture A) first
   - All enemies (texture B) next
   - All UI (texture C) last
3. Use `TextureRegion` from a single `TextureAtlas` to draw multiple sprites without binding
4. Pre-multiplied alpha or premultiplied PNGs can avoid some blend-mode changes

### SpriteBatch boilerplate
```java
batch.begin();
batch.draw(region, x, y, width, height);
batch.end();
```
Always pair `begin()`/`end()`. Inside the begin/end pair, do NOT call other rendering operations (no ShapeRenderer, no Stage.draw on a different batch).

## TextureAtlas and TexturePacker

A `TextureAtlas` is a single large texture (typically 2048x2048, power-of-two) containing many smaller sprite regions, plus a `.atlas` file describing UV coordinates.

### Why POT and 2048
- Older Android GPUs require POT textures
- 2048x2048 fits within virtually every device's maxTextureSize
- Larger atlases save flushes; smaller atlases waste VRAM

### Packing workflow
1. Drop loose PNGs into a folder (e.g. `assets-raw/`)
2. Run TexturePacker:
   ```bash
   java -cp gdx.jar:gdx-tools.jar com.badlogic.gdx.tools.texturepacker.TexturePacker \
     assets-raw/ android/assets/atlas/ game
   ```
   Produces `android/assets/atlas/game.atlas` plus `game.png` (or `game1.png`, `game2.png` if it splits)
3. In code:
   ```java
   TextureAtlas atlas = assets.get("atlas/game.atlas", TextureAtlas.class);
   TextureRegion player = atlas.findRegion("player");
   ```

### TexturePacker settings (`pack.json` next to source folder)
- `pot: true` (force power-of-two)
- `maxWidth: 2048, maxHeight: 2048`
- `paddingX: 2, paddingY: 2` (prevents bleed between regions)
- `duplicatePadding: true` (clamps edge pixels)
- `filterMin: Linear, filterMag: Linear` (smooth scaling)
- `useIndexes: false` for static sprites; `true` for animations

## Cameras and Viewports

A `Camera` defines the view frustum; a `Viewport` adapts the camera to screen size.

| Viewport | Behavior |
|----------|----------|
| `FitViewport` | Keeps aspect ratio, black bars on mismatched screens |
| `FillViewport` | Keeps aspect ratio, crops overflow |
| `StretchViewport` | Stretches to screen, distorts aspect |
| `ScreenViewport` | 1 unit = 1 pixel, no aspect handling |
| `ExtendViewport` | Keeps aspect ratio, extends in one dimension |

Standard pattern for 2D games:
```java
camera = new OrthographicCamera();
viewport = new FitViewport(1280, 720, camera);

@Override
public void resize(int width, int height) {
    viewport.update(width, height, true);  // true centers the camera
}
```

Always call `viewport.apply()` and `camera.update()` before rendering, and apply `batch.setProjectionMatrix(camera.combined)` once per begin/end pair.

## Profiling

### GLProfiler
Built-in OpenGL call profiler:
```java
GLProfiler profiler = new GLProfiler(Gdx.graphics);
profiler.enable();
// ... render frame ...
Gdx.app.log("GL", "calls=" + profiler.getCalls()
                + " drawCalls=" + profiler.getDrawCalls()
                + " textureBindings=" + profiler.getTextureBindings()
                + " shaderSwitches=" + profiler.getShaderSwitches());
profiler.reset();
```
Watch for drawCalls and textureBindings. Per frame, target:
- < 50 draw calls for mobile
- < 200 for desktop
- Texture bindings should be at most a handful per frame

### Frame-time logging
```java
@Override
public void render() {
    long start = System.nanoTime();
    // ... render ...
    long elapsedMs = (System.nanoTime() - start) / 1_000_000;
    if (elapsedMs > 16) Gdx.app.log("frame", "slow: " + elapsedMs + "ms");
}
```

### Profiler stop signal
When `glClear` dominates the profiler output (Android Studio Profiler, JProfiler, JVisualVM, or Renderdoc), you have hit the vsync ceiling. The GPU is idling between frames waiting for the next vblank. Code-level optimization beyond this point will NOT increase frame rate. To squeeze more, you would need to disable vsync or target a higher refresh rate.

## Memory Management

OpenGL resources do NOT participate in the JVM garbage collector. Every Texture, Sound, Music, ShaderProgram, Stage, Skin, BitmapFont, ParticleEffect, FrameBuffer, ModelInstance you create allocates GPU/native memory that the JVM cannot reclaim.

### Disposal checklist
| Resource | Disposed by |
|----------|-------------|
| Texture | Texture.dispose() |
| TextureAtlas | Atlas.dispose() (disposes contained Textures) |
| Pixmap | Pixmap.dispose() |
| BitmapFont | Font.dispose() (if you generated it; do NOT dispose if it came from Skin) |
| Sound | Sound.dispose() |
| Music | Music.dispose() |
| ShaderProgram | Program.dispose() |
| Stage | Stage.dispose() (disposes its Skin if owned, but be careful with shared Skin) |
| Skin | Skin.dispose() once at end of life |
| FrameBuffer | FrameBuffer.dispose() |
| ParticleEffect | Effect.dispose() |
| SpriteBatch / ShapeRenderer / ModelBatch | Batch.dispose() |

### Disposal anti-pattern: AssetManager + dispose()
If you got the resource via `assets.get(...)`, do NOT call `dispose()` on it yourself. AssetManager owns the resource. Call `assets.unload(path)` or `assets.dispose()` instead. Double-dispose corrupts AssetManager's internal state.

### Diagnosing VRAM leaks
- Android Studio Profiler -> Memory -> watch graphics memory line
- Steadily increasing graphics memory across screen transitions = leaked Texture or FrameBuffer
- Look for new Texture(...), new FrameBuffer(...), new Skin(...) outside of AssetManager that lack a corresponding dispose

## Scene2D Performance

Scene2D is the standard UI framework: `Stage`, `Group`, `Actor`, `Table`, `Cell`.

### Group.isTransform
Every `Group` defaults `isTransform = true`, which pushes/pops a transformation matrix on every draw call. Costs measurable CPU on UI trees with many Groups.
```java
group.setTransform(false);  // No rotation/scaling support, faster
```
Set false on any Group that does not need rotation or scale.

### Avoid Actor.act / draw overhead on static UI
Actors with no animation or hit-testing waste CPU each frame. Community pattern: subclass to no-op:
```java
public class ActionlessGroup extends Group {
    @Override public void act(float delta) { }
    @Override public Actor hit(float x, float y, boolean touchable) { return null; }
}
```

### Stage debug rendering
`stage.setDebugAll(true)` overlays bounding boxes; useful for layout debugging, costs frame time. Disable in production.

## ShapeRenderer

Primitive line/rect/circle drawing. Each `begin()` defines a mode (Line, Filled, Point) and ends with `end()`. Like SpriteBatch, batches draws between begin/end. Do NOT use mid-SpriteBatch.

## ModelBatch (3D)

3D analog of SpriteBatch:
```java
modelBatch.begin(camera);
modelBatch.render(instance, environment);
modelBatch.end();
```
3D rendering also requires:
- `Environment` for lighting (`ColorAttribute.AmbientLight`, `DirectionalLight`)
- `ModelInstance` (cheap, references shared `Model`)
- `PerspectiveCamera` with appropriate near/far

## Frame-Pacing Common Pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| Stutter every few seconds | Major GC | Pool Vector2/Color/Component objects; avoid per-frame allocation |
| Smooth desktop, choppy Android | Texture bindings, draw calls | Pack atlases; reduce flushes |
| First-frame freeze | Synchronous asset load | Move to AssetManager; show loading screen |
| Slow loading screen | Single update() per frame | Call assets.update() multiple times per frame |
| Frame drops on resize | Recreating textures/framebuffers | Cache and resize only if dimensions changed |

## Source References

- https://libgdx.com/wiki/graphics/2d/spritebatch-textureregions-and-sprites
- https://libgdx.com/wiki/graphics/2d/2d-graphics
- https://libgdx.com/wiki/graphics/profiling
- https://yairm210.medium.com/the-libgdx-performance-guide-1d068a84e181 (community canonical reference, 8+ years of Unciv experience)
