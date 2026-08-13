# Gateway Verification

Provisioning a disposable paper Gateway and using it to answer questions instead of guessing.

Two scripts ship with this skill:

- **`${CLAUDE_PLUGIN_ROOT}/skills/ibkr-trading/scripts/ibkr_gateway.py`** downloads, installs,
  configures, starts and stops an IB Gateway pinned to paper trading. Standard library only, so it runs
  before anything else is installed.
- **`${CLAUDE_PLUGIN_ROOT}/skills/ibkr-trading/scripts/ibkr_probe.py`** connects to it and measures
  venue behaviour: capability dumps, order-shape verdicts, compatibility matrices, bracket lifecycle
  transcripts, and message-code lookups. Requires `ib_async`.

## Safety model

Live money is one configuration mistake away from any tool that speaks this protocol, so the guards are
in code rather than in prose.

1. **Live ports are refused before connecting.** `4001` and `7496` abort both scripts. Paper defaults
   are `4002` (Gateway) and `7497` (TWS).
2. **The account is re-checked after connecting.** Every managed account must begin with `D` (IBKR
   paper account ids look like `DU…` / `DF…`). Anything else disconnects and aborts. Port and account
   are two independent checks on purpose: a paper port can be pointed at a live gateway.
3. **`TradingMode=paper` is pinned** in the generated IBC configuration.
4. **Order-placing probes use prices far from the market** and cancel everything on the way out.
5. **The what-if budget is enforced**, not just documented: probes are spaced to at most one per minute,
   per IBKR's published guidance.

There is deliberately **no live provisioning path**. Provisioning a production Gateway belongs to your
deployment tooling, where it can be reviewed.

## Provisioning

```bash
S=${CLAUDE_PLUGIN_ROOT}/skills/ibkr-trading/scripts

python $S/ibkr_gateway.py doctor                       # what is present, which ports are open
python $S/ibkr_gateway.py install --channel stable     # download + unattended install of Gateway and IBC
python $S/ibkr_gateway.py configure --user <paper-user>  # writes config.ini, TradingMode=paper
export IB_PASSWORD='…'                                 # never written to the repository
python $S/ibkr_gateway.py start --timeout 900          # launches headless, then probes the port
python $S/ibkr_gateway.py stop
```

On PowerShell, set the password with `$env:IB_PASSWORD = '...'`; the script invocations are identical.

Notes that come from how these installers actually behave:

- **Everything lands outside the repository**, in a per-user state directory (`IBKR_VERIFY_HOME`
  overrides it). Credentials never enter the working tree.
- **Windows and Linux install unattended.** macOS ships a `.dmg` that needs mounting, so the script
  stops and tells you the two commands rather than pretending.
- **`start` goes through IBC's service entry points** (`scripts/ibcstart.sh` / `scripts\StartIBC.bat`)
  with everything passed as explicit arguments. The top-level `gatewaystart.sh` / `StartGateway.bat`
  are user-editable config files that hard-assign their own paths, config file and trading mode, so
  environment variables never survive them.
- **`start` verifies by probing the API port, never by the launcher's exit code.** Launchers background
  the JVM and return success within a second or two; treating that return as "it started" produces
  restart loops.
- **On Linux a display is required** (the Gateway is a Java GUI app): run under `xvfb-run -a`, which
  `doctor` checks for.
- **A cold first login can take 10 to 15 minutes** (updates, 2FA on IBKR Mobile, warm-up). The default
  timeout is 900 s for that reason. A 90-second timeout guarantees a crash loop.
- **The Gateway is detached from its spawner**, so stopping the script does not kill the Gateway.

The Docker route is a legitimate alternative to all of the above:
`gnzsnz/ib-gateway-docker` packages IB Gateway plus IBC and supports live and paper simultaneously. The
same rules apply: one starter, port-probe verification, a generous cold-start timeout.

## Answering a question with the prober

### What does this contract actually permit?

```bash
python $S/ibkr_probe.py capabilities --stock AAPL
python $S/ibkr_probe.py capabilities --forex EURUSD
python $S/ibkr_probe.py capabilities --cfd EUR.USD
python $S/ibkr_probe.py capabilities --option 'AAPL,20261218,200,C'
```

Emits JSON: `orderTypes` (the venue's own capability token list), `validExchanges`, `minSize`,
`sizeIncrement`, trading hours, and **the resolved market rules per exchange**, meaning the actual
price bands and increments rather than the `minTick` floor. It then calls out on stderr whether tokens
like `AON`, `GTC`, `IOC` and `POSTONLY` are present for that contract.

**This is the first thing to run for any "does IBKR support X" question.** If an order-type token is
absent, the answer is no for that contract and no probe is needed. TIF tokens under-report (EUR.USD
CFD declares no `IOC` yet accepts it at what-if), so an absent TIF still goes to `shape`. Reading
beats probing whenever reading suffices.

### Will this exact order shape be accepted?

```bash
python $S/ibkr_probe.py shape --stock AAPL --type STP --tif GTC --attr allOrNone
python $S/ibkr_probe.py shape --forex EURUSD --type LMT --tif IOC --attr minQty=1000
```

One what-if submission via `ib.whatIfOrderAsync` (the API that actually returns the venue's
`OrderState`; on the plain `placeOrder` path ib_async discards it). Returns `ACCEPTED`, `REFUSED` or
`UNDECIDED`, every non-informational error code, and the margin impact. Each code is then explained
from the shipped table, including the grade `ib_async` gives it.

A `REFUSED` verdict is trustworthy for that shape. An `ACCEPTED` verdict is a credit check passing, not
a promise: terminal presets and book state can still refuse the real order.

**What paper can and cannot prove is itself documented.** IBKR's paper-account guide states the
simulator's limits: fills "are simulated from the top of the book" with no deep book; "stops and other
complex order types are always simulated in paper trading", which "may result in slightly different
behavior from a production account"; some order types are unsupported outright (VWAP, Auction, RFQ,
Pegged to Market); combo and EFP trading is limited; US options never receive penny fills; and an
exchange-directed market order that partially executes has its remainder rejected by the simulator.
Validation verdicts transfer to live; fill behaviour, partials and timing do not.

Data on paper follows the live account: subscriptions are shared by opt-in (Account Settings, Paper
Trading Account), the two logins cannot consume the shared data simultaneously, and an unshared paper
account gets documented delayed defaults (US stocks and options 15 minutes, US futures 10; metals,
Forex and US bonds undelayed).

### Which combinations work?

```bash
python $S/ibkr_probe.py matrix --stock AAPL --types LMT,STP,STPLMT --tifs DAY,GTC,IOC
```

Prints a compatibility table. Shapes whose **order type** is absent from `ContractDetails.orderTypes`
are marked `NOT-DECLARED` and skipped rather than probed; every TIF is measured by what-if, because
the declaration under-reports TIFs (EUR.USD CFD declares no `IOC` and accepts it). At one probe per
minute, a full 3×3 grid takes about eight minutes; that is the cost of an answer that is true for
your account.

### What does a bracket actually do here?

```bash
python $S/ibkr_probe.py bracket --stock AAPL --qty 1 --parent-tif DAY --child-tif GTC
```

Places a genuinely staged three-leg bracket with prices far from the market (snapped to the market
rule band so the probe itself cannot die on error 110), waits, and prints per leg: the TIF sent versus
the TIF read back, status, `filled`, `remaining`, and the full trade log. Then cancels exactly the
orders it placed. If no live quote arrives (fresh paper accounts often lack market-data subscriptions),
it refuses to place rather than guessing a reference; pass `--price` with a level you have confirmed.

**A TIF read back different from the one sent is a terminal preset rewriting your order** (the error
`10349` mechanism), which is otherwise invisible. This probe is the cheapest way to detect that a
terminal is editing your orders.

Two shapes in the cleanup transcript are expected, not errors: each leg answers `202` (cancelled),
and a child the OCA relationship already cancelled in cascade answers `10148` ("cannot be cancelled,
state: Cancelled") to its own explicit cancel -- a live demonstration that 10148 judges the *cancel
request*, which is exactly why it never belongs in a rejection set. Outside regular trading hours the
parent also logs a warning-grade `399` ("will not be placed until <open>") and stays alive,
`ValidationError` pseudo-status notwithstanding.

### What is this code I have never seen?

```bash
python $S/ibkr_probe.py codes 10256 10257 10349 110 201
```

No gateway needed. Looks the code up in `assets/tws-message-codes.tsv` (all 458 published codes) and
reports the grade `ib_async` applies -- by ib_async's rule, not by table membership, so an unlisted
code in `[2100, 2200)` or in `warningCodes` is correctly reported as a warning. A genuinely
undocumented fatal code is reported with the warning that `ib_async` will cancel your local record of
a live order.

## The workflow this supports

For any question about venue behaviour, in order:

1. **Read the capability list** for the contract. Many questions end here.
2. **Read the documentation**, and quote the sentence. If you cannot locate it as a sentence, you do
   not have an answer. Silence is a result worth recording.
3. **Probe the shape** with what-if, respecting the budget.
4. **Probe the lifecycle** with a real staged order on paper when the question is about states,
   timing or attachment rather than acceptance.
5. **Record the answer with its provenance and the shapes it covers**, and delete the open question.

Steps 1 and 2 are free and answer most questions. Step 3 costs a minute. Step 4 costs a few minutes and
a paper order. None of that is expensive compared to shipping a decision built on an assumption.

## What this cannot tell you

Honest limits, so the transcripts are not over-read:

- **Paper is not production.** Fill behaviour, partial fills, queue position and slippage differ.
  Acceptance and refusal transfer well; execution quality does not.
- **A paper account can have different permissions** from your live account. Entity-dependent routing
  rules in particular may not reproduce.
- **A result is scoped to the shapes probed.** Measured on `STP` says nothing about `LMT`.
- **Terminal configuration is per machine.** A verdict measured against this disposable Gateway may
  differ from the one your production terminal produces, which is exactly why comparing the two is
  informative.

## Related

- `venue-questions-and-probes.md` - the doctrine: what counts as an answer, and the open-question register
- `error-codes-and-verdicts.md` - reading the codes the probes return
- `order-types-and-attributes.md` - the capability vocabulary the prober dumps
- `bracket-orders.md` - what the bracket probe is testing for
- `gateway-automation.md` - running a Gateway in production, as opposed to provisioning one for tests
