# Architecture Patterns

Game-level structure, Screen management, Scene2D for UI, Ashley ECS for entities, Box2D physics, and 3D basics.

## ApplicationListener and Game

The entry point implements `ApplicationListener` (6 callbacks: create, resize, render, pause, resume, dispose). For most projects, extend `Game` instead of implementing ApplicationListener directly. `Game` adds a Screen abstraction and delegates lifecycle callbacks to the current Screen.

```java
public class MyGame extends Game {
    public SpriteBatch batch;
    public AssetManager assets;
    public Skin skin;

    @Override
    public void create() {
        batch = new SpriteBatch();
        assets = new AssetManager();
        setScreen(new LoadingScreen(this));
    }

    @Override
    public void dispose() {
        if (getScreen() != null) getScreen().dispose();
        batch.dispose();
        assets.dispose();
        if (skin != null) skin.dispose();
    }
}
```

## Screen Pattern

Each major game state is a `Screen`: MainMenuScreen, GameplayScreen, PauseScreen, GameOverScreen, OptionsScreen. The `Screen` interface has show, render, resize, pause, resume, hide, dispose.

### Switching Screens
`Game.setScreen(newScreen)` calls the new screen's `show()` and the previous screen's `hide()`. It does NOT dispose the previous screen automatically.

Two strategies:

**A. Keep all screens alive, switch with no disposal**
```java
public class MyGame extends Game {
    public MainMenuScreen menu;
    public GameplayScreen gameplay;

    @Override
    public void create() {
        menu = new MainMenuScreen(this);
        gameplay = new GameplayScreen(this);
        setScreen(menu);
    }

    @Override
    public void dispose() {
        menu.dispose();
        gameplay.dispose();
    }
}
```
Best for screens with heavy assets you want to keep loaded.

**B. Dispose old screen when switching permanently**
```java
public void switchTo(Screen newScreen) {
    Screen old = getScreen();
    setScreen(newScreen);
    if (old != null) old.dispose();
}
```
Best for one-way transitions (menu -> game -> game over -> back to menu).

### Screen Lifecycle Rules
1. Construct screens lazily if they hold heavy assets
2. Reuse screen instances rather than constructing new ones on every transition (construction reallocates GPU resources)
3. Set `Gdx.input.setInputProcessor(...)` in `show()`, NOT in the constructor; constructor runs before the screen is visible
4. Null the input processor in `hide()` to avoid stale handlers
5. Call `viewport.update(width, height, true)` in `resize()`
6. Dispose all owned resources in `dispose()`

### Transition Library
For animated screen transitions, the canonical community library is `crykn/libgdx-screenmanager`. It handles input processor switching, transition effects (fade, slide, blinds), and resource lifecycle.

## Scene2D

UI framework: a scene graph of `Actor`s rooted at a `Stage`. The Stage owns a `Viewport`, a `Batch`, and handles input routing.

### Core Hierarchy
```
Stage
  Group (e.g. root Table)
    Table
      Label
      TextButton
      Image
      ScrollPane
        Table (inner)
          ...
```

### Tables for Layout
`Table` is the most common layout container. Cells with row()-based positioning:
```java
Table table = new Table();
table.setFillParent(true);
stage.addActor(table);

table.add(new Label("Score:", skin)).left().pad(10);
table.add(new Label("0", skin)).expandX().right().pad(10);
table.row();
table.add(playButton).colspan(2).fillX().pad(20);
```

### Skin
A `Skin` is a bundle of resources (textures, fonts, drawables, colors) plus a JSON style definition. Generate with Skin Composer (https://github.com/raeleus/skin-composer).

### Input Routing
`Stage` implements `InputProcessor`. Hand it to `Gdx.input` (often via an `InputMultiplexer` if you also have gameplay input):
```java
InputMultiplexer mux = new InputMultiplexer();
mux.addProcessor(stage);          // UI first
mux.addProcessor(gameInputHandler); // gameplay second
Gdx.input.setInputProcessor(mux);
```
The Stage will consume events it handles (button clicks), gameplay handler sees only events the Stage rejected.

### Actor Update vs Draw
- `Actor.act(float delta)` is called once per frame to update state, run actions, fire events
- `Actor.draw(Batch, parentAlpha)` draws to the Stage's Batch
- Stage handles both: `stage.act(delta); stage.draw();`

## Ashley ECS

Entity-Component-System framework that pairs naturally with libGDX. Game-world entities live as Ashley `Entity`s; logic lives in `EntitySystem`s.

### Core Concepts
- **Entity**: a unique ID + a bag of components
- **Component**: pure data (position, velocity, sprite, health)
- **System**: logic that operates on entities matching a Family

### Example
```java
public class Position implements Component {
    public float x, y;
}

public class Velocity implements Component {
    public float dx, dy;
}

public class MovementSystem extends IteratingSystem {
    private final ComponentMapper<Position> pm = ComponentMapper.getFor(Position.class);
    private final ComponentMapper<Velocity> vm = ComponentMapper.getFor(Velocity.class);

    public MovementSystem() {
        super(Family.all(Position.class, Velocity.class).get());
    }

    @Override
    protected void processEntity(Entity entity, float delta) {
        Position p = pm.get(entity);
        Velocity v = vm.get(entity);
        p.x += v.dx * delta;
        p.y += v.dy * delta;
    }
}
```

### Engine Setup
```java
Engine engine = new Engine();
engine.addSystem(new MovementSystem());
engine.addSystem(new RenderSystem(batch, camera));

Entity player = engine.createEntity();
player.add(new Position()).add(new Velocity());
engine.addEntity(player);

// Each frame:
engine.update(delta);
```

### Pitfalls
- **Cache ComponentMappers**: `ComponentMapper.getFor(...)` is moderately expensive. Cache as `private final` fields, never call per-frame
- **Components with collections must clear in `reset()`**: when implementing `Poolable`, clear arrays/maps in `reset()`. Otherwise pooled components retain dangling references and leak memory
- **Order systems by priority**: `engine.addSystem(system, priority)`. Lower priority runs first. Typical order: input -> physics -> movement -> collision -> rendering
- **Family changes are expensive**: adding/removing components from an entity recomputes Family membership. Avoid in hot paths

### Scene2D + Ashley Combination
Standard community pattern:
- Scene2D handles UI rendering, input routing, hit detection, layout
- Ashley handles game-world entities and logic

Do not try to use Ashley for UI (no built-in input or hit testing) and do not use Scene2D for game entities (poor scaling for hundreds of game objects). Both have legitimate roles.

## Box2D Physics

2D rigid-body physics simulation, ported from Erin Catto's C++ Box2D. Included as a libGDX extension.

### Core Concepts
- **World**: container, gravity, simulation
- **Body**: rigid body, position + velocity + mass
- **Fixture**: shape attached to body (circle, polygon, edge)
- **Joint**: constraint between bodies

### Fixed Timestep
Box2D simulation MUST run at a fixed timestep, decoupled from render rate. Variable timestep produces unstable simulation.

```java
private static final float STEP = 1f / 60f;
private float accumulator = 0f;

public void update(float delta) {
    accumulator += Math.min(delta, 0.25f);  // cap to avoid spiral of death
    while (accumulator >= STEP) {
        world.step(STEP, 6, 2);  // 6 velocity iterations, 2 position iterations
        accumulator -= STEP;
    }
}
```

### Units
- Box2D works best with units that approximate meters (0.1 to 10 range)
- libGDX uses pixels by default; convert with a scale constant
- Convention: `PPM = 100` (pixels per meter), divide pixel coords by PPM when passing to Box2D

### Performance
- Sleeping bodies: Box2D auto-sleeps inactive bodies; do not disable
- Contact listeners: implement `ContactListener` for collision callbacks; do NOT modify the world inside callbacks (queue changes)
- DebugRenderer: `Box2DDebugRenderer` overlays shapes; useful during dev, disable in production

## 3D Basics

libGDX has a 3D rendering API though less mature than 2D. Used for 3D games or 2.5D effects.

### Core Classes
- **Model**: shared mesh + materials, expensive
- **ModelInstance**: cheap reference to a Model with its own transform
- **ModelBatch**: 3D analog of SpriteBatch
- **Environment**: lighting setup
- **PerspectiveCamera**: standard 3D camera

### Minimal Setup
```java
camera = new PerspectiveCamera(67, viewport.getWorldWidth(), viewport.getWorldHeight());
camera.position.set(10, 10, 10);
camera.lookAt(0, 0, 0);
camera.near = 1f;
camera.far = 300f;

environment = new Environment();
environment.set(new ColorAttribute(ColorAttribute.AmbientLight, 0.4f, 0.4f, 0.4f, 1f));
environment.add(new DirectionalLight().set(0.8f, 0.8f, 0.8f, -1f, -0.8f, -0.2f));

modelBatch = new ModelBatch();

// per frame
modelBatch.begin(camera);
modelBatch.render(instance, environment);
modelBatch.end();
```

### Model Loading
- G3DJ format: libGDX's native JSON 3D format (fbx-conv to convert from FBX/Collada/OBJ)
- GLTF: third-party library `gdx-gltf` (https://github.com/mgsx-dev/gdx-gltf) is the modern choice
- OBJ: loadable but typically lacks animations

### 3D Physics
Bullet bindings come with libGDX (`gdx-bullet`). For most indie 3D games, Bullet via libGDX is the path of least resistance.

## Source References

- https://libgdx.com/wiki/scene2d/scene2d
- https://libgdx.com/wiki/scene2d/scene2d-ui
- https://libgdx.com/wiki/extensions/ashley
- https://libgdx.com/wiki/extensions/physics/box2d
- https://libgdx.com/wiki/graphics/3d/3d-graphics
- https://github.com/libgdx/ashley/wiki
- https://github.com/crykn/libgdx-screenmanager
