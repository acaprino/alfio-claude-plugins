# Offline-First Design

## MUST

- **Design the data model for offline-first from the start** for PWA and mobile apps -- retrofitting is extremely difficult.
- Treat the local store as the primary source of truth and sync to the server when connectivity returns.
- **Implement a conflict resolution strategy before launch.** Without one, silent data corruption or loss will occur.
- Queue writes with unique identifiers and timestamps for reconciliation -- idempotency is non-negotiable.

## Conflict Resolution Strategies

| Strategy | Best for | Example |
|----------|---------|---------|
| **Last-Write-Wins (LWW)** | Simplest approach, infrequent conflicts | Trello -- human users are forgiving |
| **CRDTs** (Conflict-Free Replicated Data Types) | Collaborative editing, guaranteed convergence | Figma -- multiple users edit simultaneously |
| **Operational Transform (OT)** | Real-time collaborative text editing | Google Docs |
| **Field-level merge** | Mixed scenarios | Auto-resolve different field changes, prompt user for same-field conflicts |

## DO

- Use **optimistic UI updates** -- apply changes locally immediately, sync in background, reconcile later.
- For PWAs: combine service workers + Cache API + IndexedDB + Background Sync API (Workbox simplifies this).
- For mobile: use the Repository pattern with offline-first reads and write queues.

## DON'T

- Assume "eventually consistent" means "always correct" -- CRDTs solve merge conflicts, not authorization or validation.
- Skip testing offline scenarios.
- Store unbounded offline data without compaction/garbage collection.
