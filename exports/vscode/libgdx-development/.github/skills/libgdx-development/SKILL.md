---
name: libgdx-development
description: >
  Knowledge base for shipping production games from one Java or Kotlin codebase.
  Use when building, optimizing, debugging, or scaffolding libGDX games, migrating libGDX
  versions, or choosing libGDX architecture patterns.
user-invocable: true
license: MIT
metadata:
  author: Alfio Caprino
  source: acaprino/claude-code-daodan
  upstream-plugin: libgdx-development
---

# libGDX Cross-Platform Game Development

Knowledge base for building production-grade games with libGDX, the cross-platform Java/Kotlin game framework.

## When to Use

- Scaffolding a new libGDX project with gdx-liftoff
- Designing the Game/Screen structure and Scene2D + Ashley + Box2D integration
- Managing the rendering pipeline: SpriteBatch, TextureAtlas, viewports, cameras
- Handling AssetManager lifecycle and OpenGL resource disposal
- Targeting Desktop, Android, iOS, or HTML5 from a shared codebase
- Migrating to libGDX 1.14.0 and its breaking changes (`Pools` -> `PoolManager`, `JsonValue` case sensitivity)
- Debugging frame-rate drops, VRAM leaks, or input handling bugs

## Quick Start

For 80% of new libGDX projects, follow this path:

1. **Generate**: download latest `gdx-liftoff` JAR from https://github.com/libgdx/gdx-liftoff/releases, run with JDK 17 or later (Java 21 recommended)
2. **Configure** in gdx-liftoff: pick platforms (Desktop + Android typical), pick language (Kotlin if no HTML5 target, otherwise Java), pick extensions (Ashley, Box2D, FreeType, Controllers as needed)
3. **Open** the generated project in IntelliJ IDEA or Android Studio (do NOT use Eclipse for modern libGDX)
4. **Run** `:lwjgl3:run` Gradle task to launch the desktop module
5. **Architecture**: extend `Game`, create `MainMenuScreen` + `GameplayScreen`, use Scene2D for UI and Ashley for entities
6. **Assets**: pack sprites into `TextureAtlas` (2048x2048 POT), load via `AssetManager`, never load loose Textures per sprite
7. **Disposal**: every Texture, Sound, Music, Stage, Skin, BitmapFont, ShaderProgram MUST have an explicit `.dispose()` call

Then harden incrementally:
- GL thread blocking, push IO/compute to a worker thread via `Gdx.app.postRunnable`
- Screen lifecycle, set `Gdx.input.setInputProcessor` in `show()`, never in the constructor
- Memory leaks, audit static field references to Texture/AssetManager (forbidden on Android)
- Scene2D performance, set `Group.isTransform = false` on non-rotating Groups
- Ashley correctness, components with collections must implement `Poolable` and clear in `reset()`

## Reference Materials

- `references/setup-and-tooling.md`: gdx-liftoff workflow, Gradle multi-module layout, JDK and Kotlin versions, IDE setup, libGDX 1.14.0 changelog
- `references/rendering-and-performance.md`: SpriteBatch batching, TextureAtlas packing, viewports, GL thread rules, frame-budget profiling, vsync ceiling
- `references/architecture-patterns.md`: Game + Screen pattern, Scene2D + Ashley ECS combination, Box2D fixed timestep, 3D ModelBatch basics
- `references/asset-and-lifecycle.md`: AssetManager async loading, dispose discipline, Screen lifecycle, input processor management, screen transitions
- `references/deployment-platforms.md`: Desktop LWJGL3, Android (minSdk/targetSdk), iOS RoboVM constraints, HTML5 GWT vs TeaVM, packaging and signing

## Key Decision Points

| Decision | Default | Upgrade When |
|----------|---------|-------------|
| Generator | gdx-liftoff | Always (gdx-setup is deprecated) |
| Language | Kotlin (Java if HTML5 needed) | HTML5 target requires Java |
| JDK build target | Java 21 | Java 17 minimum; iOS source level capped at 8 |
| Architecture | Game + Screen + Scene2D | Add Ashley ECS for mid-size entity counts |
| Physics | Box2D fixed timestep (60 Hz) | Bullet for 3D |
| Asset loading | AssetManager async, pump update() per frame | Multiple update() per frame on loading screen |
| Texture strategy | TextureAtlas, POT, packed via TexturePacker | Never load loose Textures per sprite |
| Screen transitions | Reuse Screen instances or libgdx-screenmanager | Constructing new screens per transition is wasteful |
| Input handling | Set processor in show(), null in hide() | InputMultiplexer for Stage + custom processors |
| HTML5 backend | GWT | TeaVM if you need Kotlin or modern JS interop (still WIP for libGDX) |

## Behavioral Rules

- Never share Texture or AssetManager via static fields (Android lifecycle breaks them)
- Never call OpenGL or `Gdx.gl.*` from a non-render thread
- Never load loose Textures per sprite, always pack atlases
- Always dispose every OpenGL-backed resource on Screen.dispose() or Game.dispose()
- Always set `Gdx.input.setInputProcessor` in Screen.show(), null it in Screen.hide()
- Always set `Group.isTransform = false` on Scene2D Groups without rotation or scaling
- Always cache `ComponentMapper.getFor(...)` references in Ashley systems
- Always use a fixed timestep for Box2D, decoupled from render rate

## Source Anchors

- libgdx.com (canonical wiki and news)
- javadoc.io/doc/com.badlogicgames.gdx/gdx/latest (canonical API)
- github.com/libgdx/libgdx (source)
- github.com/libgdx/gdx-liftoff (project generator)
