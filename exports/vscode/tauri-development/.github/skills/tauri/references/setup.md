# Environment Setup

Base prerequisites for any Tauri 2 project. Mobile setup builds on top of this in `setup-mobile.md`.

## When to use

First time setting up Tauri on a machine, or onboarding a new contributor. For mobile-specific tooling (Android Studio, Xcode, NDK), continue to `setup-mobile.md` after this.

## Gotchas

- `cargo tauri info` is your fastest sanity check after install -- it surfaces missing toolchains, SDK paths, and version drift before you waste time on a broken `dev`.
- Vite users **must** set `envPrefix: ['VITE_', 'TAURI_']` -- otherwise `TAURI_*` env vars (used by mobile dev host, debug flags) are stripped at build time.
- `clearScreen: false` in `vite.config.ts` is non-negotiable when running under `cargo tauri dev`; without it, Tauri logs (Rust panics, plugin errors) get wiped from the terminal on every HMR reload.
- Don't `npm install -g @tauri-apps/cli` -- pin it as a devDependency per project so versions don't drift across apps on the same machine.

## Official docs

- Prerequisites + per-OS install: https://v2.tauri.app/start/prerequisites/
- Create a project: https://v2.tauri.app/start/create-project/
- Rust install: https://www.rust-lang.org/tools/install
- Vite + Tauri config reference: https://v2.tauri.app/start/frontend/vite/

## Related

- `setup-mobile.md` -- Android SDK / iOS Xcode on top of these prerequisites
- `rust-patterns.md` -- backend code organization once Rust toolchain is up
