# Session and Recovery

What a session is, who is allowed to hold one, how it dies without saying so, and what you must know
before you are allowed to trade again. These are the questions that decide whether an integration
survives its first unattended week, and none of them is answered by the order-placing code.

Everything here is vendor-neutral. Where an example needs a concrete shape, it names the archetype from
`access-archetypes.md`, because that is the property the behaviour actually follows.

## Session exclusivity

Establish the regime before designing anything that runs more than one process. There are three, and
they are not distinguishable from a successful first connection.

| Regime | What a second attachment does | Where it is usually found |
|---|---|---|
| **Concurrent and independent** | Nothing. Each session is its own, and they do not observe each other | `direct-api` |
| **Exclusive, last one wins** | Evicts the first holder, which is disconnected and must re-establish | credential-scoped exclusivity, common under `local-terminal` and `vendor-gateway` |
| **Multiplexed through one component** | Attaches as an additional client on a session the component owns, identified by a per-client identifier | `local-terminal`, and `bridge` by construction |

The rules that follow from each:

- **Under eviction, two processes sharing one credential steal from each other indefinitely.** The
  symptom is a reconnect loop that looks like a flaky network, on both sides at once, and the cause is
  invisible from either process. Automation gets its own credential, and that credential is never used
  interactively by a person.
- **A human can cause an eviction.** Opening a vendor's web portal or phone app on the automation's
  credential is enough under an exclusive regime. Write that down where the operator will see it, not
  only in the design document.
- **Under multiplexing, the client identifier is a resource with its own failure modes.** A collision
  refuses the connect. A half-open session can hold an identifier after the process that owned it is
  gone. Assign identifiers deterministically so a restart reclaims its own, and never assign one at
  random and hope.
- **Ask what is scoped to the client identifier rather than to the account.** Under several vendors an
  order placed by one client is invisible, or visible but unmodifiable, to another. A recovery path
  that lists an order it cannot act on has not recovered it, and that distinction is worth a probe.

## Authentication without a human

Under `direct-api` this section does not apply: a credential is presented programmatically and the
question ends. Under every other archetype it is the largest operational difference between a demo that
works and a system that runs, and it decomposes into three separate questions that are answered
separately and often have different answers.

1. **Can the component start without an interactive session?** Desktop applications frequently need a
   display, a logged-in user, or a service wrapper that supplies one. This is per operating system and
   per version, and it changes under the vendor without notice.
2. **Can the login complete without a person?** A GUI login form and a second factor confirmed on a
   phone are both designed to require one. Use the vendor's supported non-interactive path when there
   is one, whether that is an API credential type, a certificate, or a documented automation hook.
   Where there is none, the honest design treats the human step as a scheduled operational requirement
   and builds around it. Never build a scheme whose purpose is to defeat a second factor: it converts a
   vendor's control into your liability and it breaks on their next release anyway.
3. **Can it stay authenticated for as long as your run?** Forced periodic re-authentication is common,
   and it is a scheduled outage with a known clock. Put it in the calendar, size the recovery for it,
   and alert on the window rather than being surprised by it.

Two rules apply to whatever automation layer you end up with:

- **A supervision layer is itself a component that must be supervised.** The thing that restarts the
  terminal is a process that can die, and when it does the symptom is indistinguishable from a healthy
  system that happens to be idle.
- **Cold start and warm restart have different budgets.** A restart that reattaches to a live session
  is fast. A cold start that re-authenticates from nothing can take minutes, and a health check written
  for the first will page during the second, every single day.

## Reconnection and the healthy-looking dead connection

The characteristic failure of a long-running broker integration is not a crash. It is a process that
stays up, logs nothing, and has not been connected for hours.

- **A connection flag is a cached belief, not a measurement.** Client libraries set it optimistically,
  and a failed or half-open connect can leave it asserting a connection that does not exist. The
  authoritative liveness check is an active round-trip to the broker with a timeout, and nothing else
  qualifies.
- **The failure shape is a supervisor guarded on the flag.** It makes one attempt, the attempt fails,
  the flag still reads connected, so the retry guard exits and no further attempt is ever made. The
  process stays alive, produces zero log output, and looks healthy from outside for as long as you let
  it.
- **Decorrelate the recovery layers.** If the supervisor, the heartbeat and the health endpoint all
  read the same boolean, one lying flag defeats all three simultaneously. At least one layer must be an
  independent active probe.
- **Reset the client state after every failed connect attempt**, so the next attempt starts clean
  instead of inheriting a half-open socket, which can also collide with itself and refuse the retry.
- **Back off with jitter.** Sibling processes sharing one component land synchronized retry waves after
  a shared drop, which is exactly when the component can least afford them.
- **Escalate on silence.** A supervisor that stops producing attempt logs is a failure mode of its own.
  Alert on the absence of attempts within N seconds of a disconnect, not only on their failure, because
  a dead supervisor never reports itself.
- **Do not resume strategy logic on connect. Resume it on reconciled.** These are different events and
  the gap between them is where a system re-enters positions it already holds.

## Reconciling ground truth after a gap

After a gap, your state is a hypothesis and the broker's is the fact. Reconcile before acting, without
exception.

**A gap is not only a disconnect.** A process restart, an unhandled exception on the event path, a
dropped or overflowed message queue, and a component restart on the vendor's schedule are all gaps, and
only the disconnect announces itself. Anything that could have caused you to miss an event is a gap,
which means the safe default is to reconcile on any resumption you did not fully observe.

The order of rebuild, because each step depends on the previous one:

1. **Open orders**, so nothing is acted on twice.
2. **Positions**, as the broker holds them, signed, never derived from your own arithmetic.
3. **Executions** since your last durable record, to close the ledger.
4. **Subscriptions and cached derived data.** Instrument identifiers, symbol metadata and any cached
   contract details are invalidated by the gap too, and a stale identifier is a wrong-instrument order.
5. **Strategy**, last, and only if the previous four agree.

Four properties of the queries themselves decide whether this works at all, and all four are questions
to answer per vendor rather than assume:

- **Scope.** Does the query return the whole account, or only what your client identity placed? The
  narrower scope is common and it hides orders you are responsible for.
- **Horizon.** Execution history is frequently limited to the current day. If your run outlives the
  horizon, the durable ledger has to be yours, and statements or reports are the audit source for
  anything older.
- **Replay versus present state.** These queries return what is true now. They do not replay what
  happened while you were gone, so an intermediate state you missed is gone permanently and any logic
  that needed to see the transition must be rewritten to work from state instead.
- **Cost.** Under some vendors, gaining control of an order has a side effect, up to and including
  re-queueing it at the venue. Read before you bind, and bind deliberately.

Two rules close the section:

- **An order sent just before a gap is `UNKNOWN`, not failed.** It stays `UNKNOWN` until it appears in
  one of those answers or in your own persisted evidence.
- **Reconciliation must be allowed to say "I cannot establish this".** That answer stops trading and
  raises an alert. A reconciler that always produces a state is a reconciler that guesses, and it will
  guess on the day it matters most.

## What must be persisted

Anything you need in order to answer "what did I do" without the broker's help, and anything the vendor
will not tell you twice.

| Persist | Why | Consequence if you do not |
|---|---|---|
| The intent-to-order map, written **before** the send | An asynchronous refusal can arrive before your post-send bookkeeping completes | The refusal arrives with nothing to attribute it to, routes to no subscriber, and dies while looking wired |
| A snapshot of the order at placement: instrument, side, quantity, price, type | Synthetic lifecycle events must carry real fields | Consumers silently drop events full of zeros |
| The broker order ID, as soon as it exists | It is the only identity that survives sessions and client identities | Reconciliation after a restart cannot match anything to anything |
| The execution ledger, append-only, keyed on execution ID | The vendor's own history has a horizon shorter than your run | Fills older than the horizon are unrecoverable, and corrections either double-count or overwrite |
| Sequence numbers, under `vendor-gateway` | The session cannot resume without them | You can only start a new session and reconcile from scratch, every time |
| The last reconciled snapshot with its timestamp | It defines the size of the next gap | Every reconciliation is a full one, and you cannot tell a five-second gap from an overnight one |
| The provenance of each vendor-behaviour assumption the recovery relies on | Recovery logic is built on claims about the venue | An assumption that silently became false takes the recovery path with it, and nobody knows which one |

What deliberately does not get persisted: connection flags, session-scoped identifiers, and anything
derived from a subscription. Restoring those from disk restores a belief rather than a fact, which is
the same defect as trusting the connection flag, moved to a slower medium.
