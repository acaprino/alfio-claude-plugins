# High-Frequency UI Rendering in Tauri

This reference covers frontend rendering strategies for high-update-rate UIs (trading dashboards, orderbooks, heatmaps, real-time charts). Extracted from the `tauri-desktop` agent to keep the agent body focused.

## State management for trading workloads

### Zustand with atomic selectors

```typescript
// BAD: Destructuring entire store causes re-renders on ANY change
const { price, volume, trades } = useStore();

// GOOD: Atomic selectors -- component re-renders only when its value changes
const price = useStore((state) => state.price);
const volume = useStore((state) => state.volume);
```

### Jotai for granular data (orderbook, price levels)

```typescript
// Each price level is its own atom -- surgical updates
const priceLevelAtom = atomFamily((price: number) =>
  atom({ price, quantity: 0, orders: 0 })
);

// Only components watching a specific price level re-render
const PriceLevel = ({ price }: { price: number }) => {
  const [level] = useAtom(priceLevelAtom(price));
  return <Row data={level} />;
};
```

### Computed values with createSelector

```typescript
import { createSelector } from 'reselect';

const selectSpread = createSelector(
  [(state) => state.bestBid, (state) => state.bestAsk],
  (bid, ask) => ask - bid // Recalculates only when inputs change
);
```

### Critical vs deferrable updates

```typescript
// Critical: price must be immediate
const price = useStore((s) => s.price);

// Deferrable: chart can lag during heavy updates
const chartData = useDeferredValue(useStore((s) => s.chartData));
```

### React Compiler considerations

- The Compiler handles ~30-40% of memoization automatically.
- Manual optimization still needed for:
  - External library callbacks (WebSocket, IndexedDB)
  - Complex derived state
  - High-frequency update handlers
  - WebSocket message processors

## Virtualization for large datasets

TanStack Virtual can handle 1M+ rows with careful key selection.

```typescript
const virtualizer = useVirtualizer({
  count: orderbook.length, // Can handle 1M+ items
  getScrollElement: () => parentRef.current,
  estimateSize: () => 24,  // Row height in pixels
  overscan: 10,            // Extra rows for smooth scrolling
  getItemKey: (index) => orderbook[index].price, // Stable keys, NOT index
});

return (
  <div ref={parentRef} style={{ height: '400px', overflow: 'auto' }}>
    <div style={{ height: virtualizer.getTotalSize() }}>
      {virtualizer.getVirtualItems().map((row) => (
        <OrderBookRow key={row.key} index={row.index} />
      ))}
    </div>
  </div>
);
```

### Key strategy

```typescript
// BAD: Index as key -- causes re-renders when data shifts
getItemKey: (index) => index

// GOOD: Stable identifier -- maintains component identity
getItemKey: (index) => items[index].id
getItemKey: (index) => items[index].price  // For orderbook
```

## Extreme high-frequency rendering (> 60 FPS)

Virtual DOM diffing cannot sustain sub-16ms ticks for thousands of rows. Delegate data-dense rendering to Canvas driven from a Web Worker.

**React shell + OffscreenCanvas in Worker:**
```typescript
const canvasRef = useRef<HTMLCanvasElement>(null);

useEffect(() => {
  const canvas = canvasRef.current!;
  const offscreen = canvas.transferControlToOffscreen();
  const worker = new Worker(new URL('./renderWorker.ts', import.meta.url));

  // Transfer canvas ownership to worker -- React no longer touches these pixels
  worker.postMessage({ type: 'init', canvas: offscreen }, [offscreen]);

  // Connect Tauri IPC binary channel directly to worker
  const channel = new Channel<ArrayBuffer>();
  channel.onmessage = (data) => {
    worker.postMessage({ type: 'data', buffer: data }, [data]);
  };
  invoke('subscribe_orderbook_binary', { channel });

  return () => worker.terminate();
}, []);
```

**renderWorker.ts (off main thread):**
```typescript
let ctx: OffscreenCanvasRenderingContext2D;

self.onmessage = (e) => {
  if (e.data.type === 'init') {
    ctx = e.data.canvas.getContext('2d')!;
  } else if (e.data.type === 'data') {
    const view = new Float64Array(e.data.buffer);
    renderOrderbook(ctx, view); // Pure canvas drawing, no DOM
  }
};
```

### When to use Canvas vs DOM

| Scenario | Approach |
|----------|----------|
| < 100 rows, < 10 updates/sec | React + virtualization |
| 100-1000 rows, 10-60 updates/sec | React + Jotai atomic + virtualization |
| > 1000 rows or > 60 updates/sec | Canvas + Web Worker |
| Charts with streaming data | Canvas (lightweight-charts or custom) |

## Build optimization for trading apps

### Cargo.toml release profile

```toml
[profile.release]
codegen-units = 1      # Better optimization, slower compile
lto = true             # Link-time optimization
opt-level = 3          # Maximum optimization
strip = true           # Remove symbols
panic = "abort"        # Smaller binary

[profile.release.package."*"]
opt-level = 3
```

### Windows linker (rust-lld)

Problem: MSVC default linker (`link.exe`) stalls 30-60s on final link. Rust's bundled LLD is 3-12x faster.

```bash
rustup component add llvm-tools
```

`.cargo/config.toml`:
```toml
[target.x86_64-pc-windows-msvc]
linker = "rust-lld.exe"
```

Caveats: large projects may hit the COFF 65k symbol limit; avoid combining with `-Ctarget-cpu=native`.

### Vite chunk splitting

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    target: 'esnext',
    minify: 'terser',
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react':  ['react', 'react-dom'],
          'vendor-charts': ['lightweight-charts'],
          'vendor-state':  ['zustand', 'jotai'],
        },
      },
    },
  },
});
```

### Lazy-load non-critical routes

```typescript
const Settings = lazy(() => import('./pages/Settings'));
const History  = lazy(() => import('./pages/History'));
// Trading dashboard loads immediately, others on demand
```

## Performance targets (trading UI)

| Metric | Target | Critical threshold |
|--------|--------|--------------------|
| Startup time | < 1s | < 2s |
| Memory baseline | < 100MB | < 150MB |
| Memory growth | < 5MB/hour | < 10MB/hour |
| Frontend bundle | < 3MB | < 5MB |
| Frame rate | 60 FPS stable | > 30 FPS minimum |
| IPC latency | < 0.5ms | < 1ms |
| Price update -> render | < 5ms | < 16ms |
