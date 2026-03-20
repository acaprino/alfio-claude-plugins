---
title: Detect Stale Closure Bugs in Effects
impact: CRITICAL
impactDescription: silent stale data reads
tags: advanced, hooks, refs, closures, stale-data, useEffect, bug-detection
---

## Detect Stale Closure Bugs in Effects

Closures inside `useEffect(..., [])` capture variables at mount time. If those variables derive from state or props, the captured value never updates -- the handler silently reads stale data with no crash or warning. This is a TOCTOU-class bug (CWE-367 analog).

**Incorrect (stale closure -- handler reads initial count forever):**

```tsx
function Counter({ onCountChange }) {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const handler = () => {
      // count is always 0 here -- captured at mount, never refreshed
      onCountChange(count);
    };
    window.addEventListener('focus', handler);
    return () => window.removeEventListener('focus', handler);
  }, []); // empty deps = mount-only, count is stale
}
```

**Correct (ref indirection -- always reads latest value):**

```tsx
function Counter({ onCountChange }) {
  const [count, setCount] = useState(0);
  const countRef = useRef(count);
  countRef.current = count;

  const onCountChangeRef = useRef(onCountChange);
  onCountChangeRef.current = onCountChange;

  useEffect(() => {
    const handler = () => {
      onCountChangeRef.current(countRef.current);
    };
    window.addEventListener('focus', handler);
    return () => window.removeEventListener('focus', handler);
  }, []); // safe -- refs always read latest
}
```

**Alternative: `useEffectEvent` (React 19):**

```tsx
function Counter({ onCountChange }) {
  const [count, setCount] = useState(0);

  const onFocus = useEffectEvent(() => {
    onCountChange(count); // always reads latest count
  });

  useEffect(() => {
    window.addEventListener('focus', onFocus);
    return () => window.removeEventListener('focus', onFocus);
  }, []);
}
```

### Detection Heuristic

Look for variables that:
1. Derive from state (`useState`) or props
2. Are read inside a callback defined within `useEffect(..., [])` or `useEffect(..., [unrelatedDep])`
3. Are NOT accessed via `.current` on a ref

Common hiding spots:
- `addEventListener` callbacks inside mount effects
- `setInterval` / `setTimeout` callbacks reading component state
- WebSocket `onmessage` handlers capturing local variables
- Tauri `listen()` / `Channel.onmessage` callbacks in mount effects
- Any closure passed to a subscription API inside a deps-less effect
