# IPC Streaming and High-Frequency Data

This reference covers Tauri v2 IPC patterns optimized for high-frequency/streaming data (trading, real-time dashboards, telemetry). Extracted from the `tauri-desktop` agent to keep the agent body focused; use these patterns when sustained throughput above ~100 msg/sec is required.

## Channel API vs emit/listen

The `emit`/`listen` pair has per-event overhead (~0.5-2ms). For high-frequency updates, use `Channel` -- a typed, one-shot pipe that bypasses the event bus.

**Anti-pattern (events for streaming):**
```rust
// BAD: emit/listen has overhead for high-frequency updates
app.emit("price-update", &price)?;
```

**Correct (Channel API):**
```rust
use tauri::ipc::Channel;

#[tauri::command]
async fn subscribe_prices(channel: Channel<PriceUpdate>) -> Result<(), String> {
    let mut rx = PRICE_STREAM.subscribe();
    tokio::spawn(async move {
        while let Ok(price) = rx.recv().await {
            if channel.send(price).is_err() {
                break; // Frontend disconnected
            }
        }
    });
    Ok(())
}
```

**Frontend consumption:**
```typescript
import { Channel } from '@tauri-apps/api/core';

const channel = new Channel<PriceUpdate>();
channel.onmessage = (price) => {
  updatePriceAtom(price); // Target: < 1ms handling time
};
await invoke('subscribe_prices', { channel });
```

## Batching to reduce IPC count

Instead of N round-trips for N items, issue one command returning the batch:

```rust
#[tauri::command]
async fn get_orderbook_batch(symbols: Vec<String>) -> Result<Vec<OrderBook>, Error> {
    let books = fetch_all_orderbooks(&symbols).await?;
    Ok(books)
}
```

## Binary payloads (bypass JSON)

Use `tauri::ipc::Response::new(bytes)` to return raw `ArrayBuffer` to the frontend. Eliminates the JSON serialize/parse round-trip.

```rust
use tauri::ipc::Response;

#[tauri::command]
fn get_chart_data() -> Response {
    let data: Vec<u8> = generate_binary_chart_data();
    Response::new(data)
}
```

## Zero-copy serialization with rkyv

For complex structured payloads, rkyv lets the frontend read the archive in-place without parsing.

```rust
use rkyv::{Archive, Deserialize, Serialize};
use tauri::ipc::Response;

#[derive(Archive, Deserialize, Serialize)]
struct OrderBookSnapshot {
    bids: Vec<(f64, f64)>,
    asks: Vec<(f64, f64)>,
    timestamp: u64,
}

#[tauri::command]
async fn get_orderbook_binary() -> Response {
    let snapshot = generate_orderbook_snapshot();
    let bytes = rkyv::to_bytes::<_, 4096>(&snapshot)
        .expect("serialization failed");
    Response::new(bytes.to_vec())
}
```

**Frontend TypedArray consumption:**
```typescript
const buffer = await invoke<ArrayBuffer>('get_orderbook_binary');
const view = new Float64Array(buffer);
// Direct memory access -- zero parsing overhead
// Layout: [bid_price, bid_qty, ..., ask_price, ask_qty, ..., timestamp]
```

## Backpressure and memory protection

If the Rust backend produces data faster than the frontend consumes, the queue grows unbounded and causes OOM.

**Rust-side throttling (preferred -- drop stale data):**
```rust
use tokio::time::{interval, Duration};

async fn throttled_stream(channel: Channel<Vec<u8>>) {
    let mut tick = interval(Duration::from_millis(16)); // ~60 FPS cap
    let mut latest: Option<Vec<u8>> = None;

    loop {
        tokio::select! {
            data = data_rx.recv() => {
                latest = Some(data?); // Always keep only the latest frame
            }
            _ = tick.tick() => {
                if let Some(frame) = latest.take() {
                    let _ = channel.send(frame);
                }
            }
        }
    }
}
```

**Frontend worker queue limit:**
```typescript
let pendingFrames = 0;
const MAX_PENDING = 3;

channel.onmessage = (data) => {
  if (pendingFrames < MAX_PENDING) {
    pendingFrames++;
    worker.postMessage({ type: 'data', buffer: data }, [data]);
  }
  // else: drop frame silently
};

worker.onmessage = () => { pendingFrames--; };
```

**Memory monitoring (dev-only):**
```typescript
if (import.meta.env.DEV) {
  setInterval(() => {
    const mem = (performance as any).memory;
    if (mem && mem.usedJSHeapSize > 500 * 1024 * 1024) {
      console.warn('Heap exceeding 500MB -- check for leaks');
    }
  }, 5000);
}
```

## Rust concurrency patterns

### Tokio channel selection

| Channel | Use case | Example |
|---------|----------|---------|
| `mpsc` | Many producers, single consumer | Order submissions |
| `broadcast` | One producer, many consumers | Price distribution |
| `watch` | Single latest value | Connection status |
| `oneshot` | Single response | Request/response |

### Broadcast for price distribution

```rust
use tokio::sync::broadcast;

lazy_static! {
    static ref PRICE_TX: broadcast::Sender<PriceUpdate> = {
        let (tx, _) = broadcast::channel(1024);
        tx
    };
}

// Publisher (single source)
PRICE_TX.send(price_update)?;

// Subscribers (multiple consumers)
let mut rx = PRICE_TX.subscribe();
while let Ok(update) = rx.recv().await {
    process_price(update);
}
```

### I/O-bound vs CPU-bound separation

```rust
// I/O-bound: use tokio (async runtime)
async fn fetch_market_data() -> Result<Data> {
    let response = reqwest::get(url).await?;
    Ok(response.json().await?)
}

// CPU-bound: use rayon (thread pool)
fn calculate_indicators(data: &[Candle]) -> Vec<Indicator> {
    use rayon::prelude::*;
    data.par_iter()
        .map(|candle| compute_indicator(candle))
        .collect()
}

// CRITICAL RULE: Async code must not block > 10-100us without .await.
// Use spawn_blocking for CPU work in async context:
let result = tokio::task::spawn_blocking(|| {
    calculate_heavy_indicators(&data)
}).await?;
```

## Memory management

### React cleanup patterns

```typescript
useEffect(() => {
  const controller = new AbortController();
  const channel = new Channel<PriceUpdate>();

  channel.onmessage = (price) => updatePrice(price);
  invoke('subscribe_prices', { channel });

  return () => {
    controller.abort();
    channel.onmessage = null; // Clear reference
    invoke('unsubscribe_prices'); // Notify Rust to cleanup
  };
}, []);
```

### Rust Drop + Weak refs

```rust
impl Drop for PriceSubscriber {
    fn drop(&mut self) {
        self.channels.clear();
        self.buffer.shrink_to_fit();
    }
}

// Weak references for long-lived subscribers
use std::sync::Weak;

struct SubscriptionManager {
    subscribers: Vec<Weak<Subscriber>>,
}

impl SubscriptionManager {
    fn cleanup_dead(&mut self) {
        self.subscribers.retain(|s| s.strong_count() > 0);
    }
}
```
