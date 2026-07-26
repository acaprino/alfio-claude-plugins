# libGDX Development Plugin

> Cross-platform game development with the libGDX Java/Kotlin framework. Covers project scaffolding via gdx-liftoff, the rendering pipeline, Scene2D + Ashley ECS architecture, Box2D physics, AssetManager lifecycle, and deployment to Desktop (LWJGL3), Android, iOS (RoboVM), and HTML5 (GWT/TeaVM).

## Agents

### `libgdx-architect`

Expert in libGDX cross-platform game development with Java and Kotlin. Designs Game/Screen architecture, configures multi-platform Gradle builds, and debugs rendering/lifecycle issues.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Scaffolding a libGDX project, choosing between gdx-liftoff and gdx-setup, designing Screen/Game/ApplicationListener structure, integrating Scene2D + Ashley + Box2D, managing OpenGL resource disposal, packing textures with TexturePacker, debugging frame-rate drops or GL thread blocking, configuring multi-platform Gradle builds, migrating to libGDX 1.14.0, deciding Kotlin vs Java for a libGDX project |

**Invocation:**
```
Use the libgdx-architect agent to [design/scaffold/optimize/migrate] [target]
```

**Expertise:**
- Project generation: gdx-liftoff (preferred), gdx-setup (legacy)
- Rendering pipeline: SpriteBatch, TextureAtlas, ShaderProgram, viewports, cameras
- Architecture: Scene2D (UI/Stage/Actor), Ashley ECS (Entity/Component/System), Game/Screen lifecycle
- Physics: Box2D world, body/fixture configuration, contact listeners
- Assets: AssetManager, TexturePacker, ParticleEffect, BitmapFont, Tiled (TMX) maps
- Multi-platform deploy: Desktop (LWJGL3), Android, iOS (RoboVM), HTML5 (GWT/TeaVM)
- libGDX 1.14.0 breaking changes: `Pools` -> `PoolManager`, `JsonValue` case sensitivity
- Kotlin compatibility: KTX libraries, coroutines on the GL thread

---

## Skills

### `libgdx-development`

Comprehensive libGDX knowledge base covering the rendering pipeline, ECS architecture, physics, asset lifecycle, screen management, and multi-platform deployment.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Building, optimizing, or debugging libGDX games; scaffolding new projects; migrating libGDX versions; choosing libGDX architecture patterns |

**Reference files:**
| File | Content |
|------|---------|
| setup-and-tooling.md | gdx-liftoff vs gdx-setup, Gradle multi-platform config, libGDX 1.14.0 migration (`Pools` -> `PoolManager`, `JsonValue` case sensitivity) |
| rendering-and-performance.md | SpriteBatch, TextureAtlas, ShaderProgram, viewports/cameras, draw-call batching, GL thread tuning, VRAM management |
| architecture-patterns.md | Game/Screen/ApplicationListener structure, Scene2D Stage/Actor, Ashley ECS Entity/Component/System, Box2D world + contact listeners |
| asset-and-lifecycle.md | AssetManager loading queue, TexturePacker, ParticleEffect, BitmapFont, Tiled (TMX) maps, OpenGL resource disposal |
| deployment-platforms.md | Desktop (LWJGL3), Android, iOS (RoboVM), HTML5 (GWT/TeaVM); Kotlin compatibility caveats |

---

## Commands

### `/libgdx-audit`

Audit an existing libGDX project for rendering pipeline correctness, asset disposal hygiene, Screen lifecycle bugs, GL thread blocking, multi-platform configuration drift, and libGDX 1.14.0 migration readiness.

| | |
|---|---|
| **Argument** | `[path-or-description]` |
| **Output** | Prioritized audit report with concrete fixes |

---

**Related:** [tauri-development](tauri-development.md) (alternative cross-platform target for desktop/mobile) | [kotlin-development](kotlin-development.md) (idiomatic Kotlin patterns when building libGDX games in Kotlin)
