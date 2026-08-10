# Case: synthetic-connection-pool-leak (resource-lifecycle)

Synthetic. Materialize into a scratch repo (`worker/exporter.ts`), commit, review the diff that added the exporter.

## Buggy code

```typescript
// worker/exporter.ts
const pool = new Pool({ max: 10 })

export async function exportRows(query: string, res: Response) {
  const client = await pool.connect()
  const stream = client.query(new QueryStream(query))
  stream.pipe(res)
  stream.on("end", () => client.release())
}

export function watchExports(emitter: EventEmitter) {
  setInterval(async () => {
    const client = await pool.connect()
    const pending = await client.query("SELECT count(*) FROM exports WHERE state = 'pending'")
    emitter.emit("pending", pending.rows[0].count)
    client.release()
  }, 5_000)
}
```

## Ground truth (4 bugs)

| # | Known bug | Expected dimension |
|---|-----------|--------------------|
| 1 | `exportRows` releases the client only on `end`: a stream `error`, or the response closing early (client disconnect / cancellation), never releases; with `max: 10`, ten abandoned downloads exhaust the pool for the whole process | resource-lifecycle |
| 2 | The interval body can throw between `connect()` and `release()` (query failure): the client leaks once per failing tick, forever, at 12 leaks/minute | resource-lifecycle / temporal-resilience |
| 3 | `watchExports` returns nothing and never clears the interval: callers cannot stop it, and calling it twice doubles the polling forever | resource-lifecycle |
| 4 | No error handler on the stream at all: a query error after headers are sent kills the response with no signal | temporal-resilience / architecture |

## Scoring notes

- Bug 1 is the three-exits archetype (success released, error and cancellation not). Full credit requires naming the cancellation path (response close), not just the error path.
