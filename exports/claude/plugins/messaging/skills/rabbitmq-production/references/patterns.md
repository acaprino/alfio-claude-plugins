# Delivery Patterns

Client-neutral pseudocode for the ten delivery patterns referenced from `SKILL.md` and the `rabbitmq-expert` agent: publisher confirms, consumer acknowledgment, retry with backoff, idempotent consumption, transactional outbox, claim check, RPC, connection management, streams, and topic routing.

## Publisher Confirms

When to use: any publish whose loss must be detected; confirm delivery to the broker before treating the publish as done.

```
# synchronous: simple, slower. Await each publish (or a batch) before continuing.
confirm_select()
publish(exchange="orders", routing_key="order.created", body, properties={delivery_mode: 2, mandatory: true})
wait_for_confirms()

# asynchronous: faster, more complex. A confirm callback tracks outstanding publish ids.
confirm_select()
on_confirm(handler)   # handler removes acked/nacked ids from the outstanding set
outstanding[id] = publish(exchange="orders", routing_key="order.created", body, properties={delivery_mode: 2, mandatory: true})
```

- After a connection or channel failure, retransmit everything still unconfirmed. Accept that this produces duplicates; the downstream consumer must be idempotent (see Idempotent Consumer below).
- Use the `mandatory` flag or an alternate exchange to catch unroutable messages, and alert on the unroutable-dropped counter.
- Source: https://www.rabbitmq.com/docs/reliability

## Consumer Acknowledgment

When to use: any consumer handling messages that must survive a crash mid-processing.

```
consume("work", prefetch=30, on_message=handler)
# handler: process(msg); ack(msg) on success
# on failure: nack(msg, requeue=false) -> routes to the queue's configured DLX
```

- On quorum queues, the default `delivery-limit` of 20 combined with a DLX gives poison-message quarantine for free. Alert on DLX queue depth instead of building custom quarantine logic.
- In 4.3, client-initiated requeues no longer consume the delivery limit (the acquired-count split from delivery-count).
- Source: https://www.rabbitmq.com/docs/quorum-queues

## Retry With Exponential Backoff (TTL Tier Queues)

When to use: retrying a failed message with increasing delay between attempts.

```
queue.declare("work", durable=true, args={"x-dead-letter-exchange": "retry.5s"})
queue.declare("retry.5s", durable=true, args={"x-message-ttl": 5000, "x-dead-letter-exchange": "work"})
queue.declare("retry.30s", durable=true, args={"x-message-ttl": 30000, "x-dead-letter-exchange": "work"})
queue.declare("retry.5m", durable=true, args={"x-message-ttl": 300000, "x-dead-letter-exchange": "work"})
# handler on failure: nack(msg, requeue=false) dead-letters into the current tier
# read the attempt count from the x-death header to choose the next tier, or route to a parking queue after max attempts
```

- Per-message TTL (`expiration`) cannot implement this backoff. Expired messages are only discarded when they reach the queue head, so a long-TTL message blocks shorter-TTL messages queued behind it. Source: https://www.rabbitmq.com/docs/ttl
- RabbitMQ 4.3 quorum queues have native delayed retries (increasing or linear backoff on requeue) that replace many hand-built tier setups.
- Never use the delayed-message-exchange plugin: archived April 2026, single-node Mnesia storage, dead on 4.3.

## Idempotent Consumer

When to use: every consumer handler, since at-least-once delivery means any message can arrive more than once.

```
consume("work", prefetch=30, on_message=handler)
# handler:
#   if not msg.redelivered: process(msg)
#   else: dedup_key = msg.business_id or msg.message_id
#         if not seen(dedup_key): process(msg)
#         persist dedup_key together with the side effect
#   ack(msg)
```

- Exactly-once delivery is impossible. The official guidance is idempotent processing, not explicit deduplication.
- If deduplication is expensive, only dedup messages carrying the `redelivered` flag.
- Dedup key: business id or message id, persisted together with the side effect.
- Source: https://www.rabbitmq.com/docs/reliability

## Transactional Outbox

When to use: a business change and its outgoing message must commit or fail together.

```
# in the same database transaction as the business change:
insert_outbox_row(exchange="orders", routing_key="order.created", body)

# separate relay process:
rows = read_unpublished_outbox_rows()
for row in rows:
    publish(exchange=row.exchange, routing_key=row.routing_key, row.body, properties={delivery_mode: 2})
    wait_for_confirms()
    mark_published(row)
```

- Delivery remains at-least-once, so idempotent consumer processing stays mandatory downstream.
- Costs: relay polling latency and load.

## Claim Check

When to use: a payload too large to publish directly on the queue.

```
if len(body) > threshold:
    ref = store_in_object_storage(body)
    publish(exchange="orders", routing_key="order.created", ref, properties={content_type: "application/json", delivery_mode: 2})
else:
    publish(exchange="orders", routing_key="order.created", body, properties={delivery_mode: 2})
```

- Payloads beyond the KB range go to object storage or a database; the message carries only the reference.
- Pairs with the 16 MiB default `max_message_size` (hard cap 512 MiB).
- Set `content_type` accordingly.

## RPC

When to use: request/response over AMQP using a reply queue and a correlation ID.

```
publish(exchange="", routing_key="rpc-requests", body, properties={reply_to: callback_queue, correlation_id: id})
consume(callback_queue, on_message=handler)   # handler matches the reply's correlation_id to the pending request

# server side:
consume("rpc-requests", on_message=handler)
# handler: publish(exchange="", routing_key=msg.reply_to, response, properties={correlation_id: msg.correlation_id})
```

- `reply_to` is an exclusive, auto-delete callback queue; the server echoes `correlation_id` on its reply.
- Direct Reply-To avoids the queue round-trip, and since 4.2 it also works cross-protocol for AMQP 1.0.
- The `local-random` exchange (4.0+) gives the lowest latency for RPC to node-local queues.

## Connection Management

When to use: every long-lived producer or consumer process; governs how connections, channels, and reconnection should be structured.

```
# one long-lived connection per direction, never per publish
publish_connection = connect()  # separate connection for publishing
consume_connection = connect()  # separate connection for consuming
channel = publish_connection.channel()  # one channel per thread, never shared

# reconnect loop with exponential backoff and jitter
attempt = 0
while not connected:
    try:
        connection = connect()
        connected = true
        attempt = 0   # reset on success
    except:
        delay = min(base * 2^attempt, cap) + jitter()
        sleep(delay)
        attempt += 1

# optional: pool connections for high-churn publishers instead of opening one per publish
pool = connection_pool(size=n)
conn = pool.acquire()
...
pool.release(conn)
```

- Use separate connections for publishing and consuming. A memory alarm blocks all publishing connections cluster-wide, and on a shared connection that block also stalls consumer acks and deadlocks the drain. Source: https://www.rabbitmq.com/docs/alarms
- Heartbeats: do not set below roughly 5 seconds (false positives). Without heartbeats, a dead TCP peer takes about 11 minutes to detect on default Linux. Source: https://www.rabbitmq.com/docs/reliability
- Each connection costs roughly 100 KB of broker RAM, more with TLS. Connection churn above roughly 100/s is a client bug signal. Source: https://www.rabbitmq.com/docs/connections

## Streams

When to use: a single active consumer (SAC) reading a stream, where offset tracking and takeover behavior decide correctness.

```
consume_stream("events", single_active_consumer=true, on_message=handler, on_consumer_update=resume_handler)
# resume_handler: return the last stored offset (not the stream start) when this consumer becomes active
# handler: process(msg); every few thousand messages, store_offset(msg.offset)
```

- The classic bug: the new active consumer restarts from the beginning of the stream instead of the stored offset. Resume via the consumer-update callback.
- Store offsets every few thousand messages, never per message: offset writes persist into the stream and grow disk.
- Bloom-filter stream filtering (3.13+) is probabilistic; clients must re-check filter values client-side.
- Single active consumer per partition plus super streams gives ordered processing with horizontal scale-out.
- Streams have no TTL, no priority, and no DLX; only per-consumer prefetch applies.
- Sources: https://www.rabbitmq.com/docs/streams and https://www.rabbitmq.com/blog/2021/09/13/rabbitmq-streams-offset-tracking

## Topic Routing

When to use: routing needs wildcard patterns on the routing key rather than exact equality.

```
queue.bind("error-alerts", exchange="logs", routing_key="*.error")
```

- `logs.*` matches `logs.info`, `logs.error` (one word)
- `logs.#` matches `logs.info`, `logs.error.auth` (any number of words)
- `*.error` matches `logs.error`, `app.error`
- `#` matches everything (catch-all)
