#!/usr/bin/env python3
"""Field-verify IBKR venue behaviour against a paper Gateway.

Turns a question about how the venue behaves into a measurement with a transcript, so a
design decision rests on evidence rather than on a forum post or a search summary.

Safety, enforced and not merely documented:
  * Live API ports (4001, 7496) are refused before connecting.
  * After connecting, every managed account must look like a paper account (IBKR paper
    account ids begin with D, e.g. DU/DF). Any other account aborts the run.
  * Order-placing probes use prices far from the market and cancel immediately.
  * what-if probes are spaced to respect IBKR's published budget: at most one per minute.

Requires: pip install "ib_async<3.0.0"

Subcommands:
    capabilities  Dump what a contract actually permits: orderTypes, valid exchanges,
                  increments per price band, size rules, trading hours.
    shape         what-if a single order shape (type x TIF x attributes). The verdict.
    matrix        what-if a grid of shapes and print a compatibility table.
    bracket       Place a far-from-market bracket, read every channel, report child
                  states and quantities, then cancel. Lifecycle, not just acceptance.
    codes         Look up message codes in the shipped table with their ib_async grade.

Examples:
    python ibkr_probe.py capabilities --stock AAPL
    python ibkr_probe.py capabilities --forex EURUSD --cfd EUR.USD
    python ibkr_probe.py shape --stock AAPL --type STP --tif GTC --attr allOrNone
    python ibkr_probe.py matrix --stock AAPL --types LMT,STP --tifs DAY,GTC,IOC
    python ibkr_probe.py bracket --stock AAPL --qty 1
    python ibkr_probe.py codes 10257 10349 110
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

LIVE_PORTS = {4001, 7496}
CODES_TSV = Path(__file__).resolve().parent.parent / "assets" / "tws-message-codes.tsv"
WHATIF_MIN_INTERVAL = 60.0  # IBKR: do not exceed 1 what-if per minute.

# ib_async's own grading rule (wrapper.py). The TSV mirrors IBKR's published table, so a code
# can be absent from the file and still be warning-grade by this rule; grade by rule, not table.
IB_ASYNC_WARNING_CODES = frozenset({105, 110, 165, 321, 329, 399, 404, 434, 492, 10167})

# ContractDetails.orderTypes capability tokens are unspaced; Order.orderType strings are not.
TOKEN_TO_ORDERTYPE = {"STPLMT": "STP LMT", "TRAILLMT": "TRAIL LIMIT"}

_last_whatif = 0.0
_codes_cache: "dict[int, tuple[str, str]] | None" = None


def die(msg: str, code: int = 1):
    print(f"[ibkr-probe] ERROR: {msg}", file=sys.stderr, flush=True)
    raise SystemExit(code)


def info(msg: str) -> None:
    print(f"[ibkr-probe] {msg}", flush=True)


def state_dir() -> Path:
    """Same per-user state directory as ibkr_gateway.py, for cross-process state."""
    env = os.environ.get("IBKR_VERIFY_HOME")
    if env:
        return Path(env).expanduser()
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "ibkr-verify"


def load_codes() -> dict[int, tuple[str, str]]:
    global _codes_cache
    if _codes_cache is not None:
        return _codes_cache
    out: dict[int, tuple[str, str]] = {}
    if CODES_TSV.exists():
        with open(CODES_TSV, encoding="utf-8") as fh:
            for row in csv.reader((l for l in fh if not l.startswith("#")), delimiter="\t"):
                if len(row) >= 3 and row[0].isdigit():
                    out[int(row[0])] = (row[1], row[2])
    _codes_cache = out
    return out


def ib_async_grade(code: int) -> str:
    """The grade ib_async applies, by its rule rather than by table membership."""
    return "warning" if (code in IB_ASYNC_WARNING_CODES or 2100 <= code < 2200) else "fatal"


def describe_code(code: int) -> str:
    table = load_codes()
    if code in table:
        grade, msg = table[code]
        return f"{code} [{grade}] {msg}"
    grade = ib_async_grade(code)
    if grade == "warning":
        where = ("ib_async's warningCodes set" if code in IB_ASYNC_WARNING_CODES
                 else "ib_async's blanket warning range [2100, 2200)")
        return (
            f"{code} [warning] not in IBKR's published table, but inside {where}: "
            f"ib_async records the message and leaves the order live."
        )
    return (
        f"{code} [UNDOCUMENTED, fatal to ib_async] not in IBKR's published table. ib_async grades "
        f"it fatal and will set a working order to Cancelled locally without telling the venue."
    )


def cmd_codes(args) -> None:
    for c in args.codes:
        print(describe_code(int(c)))


# --------------------------------------------------------------------------- connection


async def connect(args):
    try:
        from ib_async import IB
    except ImportError:
        die('ib_async is not installed. Run: pip install "ib_async<3.0.0"')

    if args.port in LIVE_PORTS:
        die(f"port {args.port} is a LIVE trading port. This tool is paper-only.")

    ib = IB()
    ib.client.setConnectOptions("+PACEAPI")
    try:
        await ib.connectAsync(args.host, args.port, clientId=args.client_id, timeout=20)
    except Exception as exc:  # noqa: BLE001
        die(f"could not connect to {args.host}:{args.port} clientId={args.client_id}: {exc}")

    accounts = list(ib.managedAccounts())
    if not accounts:
        ib.disconnect()
        die("connected but no managed accounts were reported; cannot verify this is paper")
    live = [a for a in accounts if not a.upper().startswith("D")]
    if live:
        ib.disconnect()
        die(
            f"account(s) {live} do not look like paper accounts (IBKR paper ids start with D, "
            f"e.g. DU/DF). Refusing to run against a live account."
        )
    info(f"connected to {args.host}:{args.port}, paper accounts {accounts}")
    return ib


def build_contract(args):
    from ib_async import CFD, Crypto, Forex, Future, Index, Option, Stock

    if args.stock:
        return Stock(args.stock, args.exchange or "SMART", args.currency or "USD")
    if args.forex:
        return Forex(args.forex)
    if args.cfd:
        if "." in args.cfd:
            base, quote = args.cfd.split(".", 1)
            return CFD(base, currency=quote)
        return CFD(args.cfd, currency=args.currency or "USD")
    if args.future:
        return Future(args.future, args.expiry or "", args.exchange or "")
    if args.option:
        try:
            sym, expiry, strike, right = args.option.split(",")
            strike_f = float(strike)
        except ValueError:
            die(f"--option must be SYMBOL,YYYYMMDD,STRIKE,C|P (got {args.option!r})")
        return Option(sym, expiry, strike_f, right, args.exchange or "SMART")
    if args.crypto:
        return Crypto(args.crypto, args.exchange or "PAXOS", args.currency or "USD")
    if args.index:
        return Index(args.index, args.exchange or "CBOE", args.currency or "USD")
    die("name a contract: --stock/--forex/--cfd/--future/--option/--crypto/--index")


# ----------------------------------------------------------------------- capabilities


async def cmd_capabilities(args) -> None:
    ib = await connect(args)
    try:
        contract = build_contract(args)
        details = await ib.reqContractDetailsAsync(contract)
        if not details:
            die(f"no contract details returned for {contract}; the contract is ambiguous or wrong")
        info(f"{len(details)} contract(s) matched; reporting the first")
        d = details[0]
        c = d.contract

        report: dict = {
            "probed_at": datetime.now(timezone.utc).isoformat(),
            "contract": {
                "conId": c.conId,
                "symbol": c.symbol,
                "secType": c.secType,
                "exchange": c.exchange,
                "primaryExchange": c.primaryExchange,
                "currency": c.currency,
                "tradingClass": c.tradingClass,
                "multiplier": c.multiplier or None,
                "localSymbol": c.localSymbol,
            },
            "minTick_floor_across_all_venues": d.minTick,
            "minSize": d.minSize,
            "sizeIncrement": d.sizeIncrement,
            "suggestedSizeIncrement": d.suggestedSizeIncrement,
            "priceMagnifier": d.priceMagnifier,
            "timeZoneId": d.timeZoneId,
            "longName": d.longName,
            "orderTypes": sorted(t for t in d.orderTypes.split(",") if t),
            "validExchanges": [e for e in d.validExchanges.split(",") if e],
            "marketRules": {},
        }

        # The increment actually in force comes from market rules, not from minTick.
        exchanges = report["validExchanges"]
        rule_ids = [r for r in d.marketRuleIds.split(",") if r]
        for exch, rule_id in zip(exchanges, rule_ids):
            try:
                # ib_async returns None on its internal 1 s timeout instead of raising.
                increments = await ib.reqMarketRuleAsync(int(rule_id))
                if increments is None:
                    report["marketRules"][exch] = {
                        "ruleId": rule_id, "error": "timeout (ib_async 1 s budget); retry"
                    }
                    continue
                report["marketRules"][exch] = {
                    "ruleId": rule_id,
                    "bands": [
                        {"lowEdge": pi.lowEdge, "increment": pi.increment} for pi in increments
                    ],
                }
            except Exception as exc:  # noqa: BLE001
                report["marketRules"][exch] = {"ruleId": rule_id, "error": str(exc)}
                continue

        report["tradingHours"] = d.tradingHours
        report["liquidHours"] = d.liquidHours

        print(json.dumps(report, indent=2, default=str))

        # The parts most often got wrong, called out explicitly.
        print("\n--- read this before designing around the numbers above ---", file=sys.stderr)
        print(
            "minTick is the smallest increment across ANY exchange and ANY price. The increment\n"
            "your order must satisfy is the marketRules band containing your price, for the\n"
            "exchange you route to. Snapping to minTick alone is how error 110 happens.",
            file=sys.stderr,
        )
        for token in ("AON", "GTC", "GTD", "IOC", "OPG", "HID", "POSTONLY", "SWEEP"):
            state = "present" if token in report["orderTypes"] else "ABSENT"
            print(f"  capability {token:9}: {state}", file=sys.stderr)
    finally:
        ib.disconnect()


# ------------------------------------------------------------------------ shape probes


def apply_attrs(order, attrs: list[str]) -> None:
    """Set Order attributes, refusing names that are not real Order fields.

    ib_async's Order is a plain dataclass without __slots__: a mistyped attribute would be
    set successfully, never serialized, and the shape would read as tested when the
    attribute was never sent. For an evidence-producing tool that is worse than a crash.
    """
    import dataclasses

    from ib_async import Order

    valid = {f.name for f in dataclasses.fields(Order)}
    for a in attrs:
        k, v = a.split("=", 1) if "=" in a else (a, None)
        if k not in valid:
            die(f"unknown Order attribute {k!r}: not a field of ib_async.Order, "
                f"so it would be silently ignored. Check the spelling (e.g. allOrNone).")
        if v is None:
            setattr(order, k, True)
        else:
            try:
                val: object = json.loads(v)
            except json.JSONDecodeError:
                val = v
            setattr(order, k, val)


def _whatif_stamp_path() -> Path:
    return state_dir() / "whatif.stamp"


def _load_whatif_stamp() -> float:
    try:
        return float(_whatif_stamp_path().read_text().strip())
    except (OSError, ValueError):
        return 0.0


def _store_whatif_stamp(ts: float) -> None:
    try:
        p = _whatif_stamp_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(str(ts))
    except OSError:
        pass  # budget spacing degrades to per-process; not worth failing a probe over


async def whatif_shape(ib, contract, order_type: str, tif: str, attrs: list[str],
                       qty: float, price: float, respect_budget: bool) -> dict:
    """Submit one shape via whatIfOrderAsync and return the venue's verdict.

    Uses ib.whatIfOrderAsync, the API built for this: it registers the response future so
    the returned OrderState actually arrives. (On the plain placeOrder path ib_async
    discards the whatIf OrderState, so a verdict read off the Trade can never see it, and
    a hand-set whatIf flag with transmit=True is one honored-flag away from a live order.)
    """
    global _last_whatif
    from ib_async import Order

    if respect_budget:
        if not _last_whatif:
            _last_whatif = _load_whatif_stamp()  # budget survives across invocations
        wait = WHATIF_MIN_INTERVAL - (time.time() - _last_whatif)
        if wait > 0 and _last_whatif:
            info(f"what-if budget: waiting {wait:.0f}s (IBKR asks for max 1 per minute)")
            await asyncio.sleep(wait)

    order = Order()
    order.action = "BUY"
    # Capability tokens are unspaced (STPLMT); Order.orderType strings are not (STP LMT).
    order.orderType = TOKEN_TO_ORDERTYPE.get(order_type, order_type)
    order.totalQuantity = qty
    order.tif = tif
    if order_type in ("LMT", "STPLMT"):
        order.lmtPrice = price
    if order_type in ("STP", "STPLMT", "TRAIL"):
        order.auxPrice = price
    apply_attrs(order, attrs)

    codes: list[int] = []
    messages: list[str] = []

    def on_error(reqId, errorCode, errorString, contract_):  # noqa: ANN001
        # Farm-status and connectivity notices ([2100,2200)) arrive on this channel at
        # connect time and on every farm blip; they are not a verdict on this shape.
        if 2100 <= errorCode < 2200:
            return
        codes.append(errorCode)
        messages.append(f"{errorCode}: {errorString}")

    ib.errorEvent += on_error
    state = None
    timed_out = False
    try:
        try:
            state = await asyncio.wait_for(ib.whatIfOrderAsync(contract, order), timeout=20)
        except asyncio.TimeoutError:
            timed_out = True
        _last_whatif = time.time()
        _store_whatif_stamp(_last_whatif)
        await asyncio.sleep(1)  # let a trailing rejection code land before judging
    finally:
        ib.errorEvent -= on_error

    def _field(name):
        val = getattr(state, name, None)
        if val in (None, ""):
            return None
        try:  # OrderState money fields are strings; UNSET_DOUBLE means "not provided"
            if float(val) >= 1.7e308:
                return None
        except (TypeError, ValueError):
            pass
        return val

    margin = _field("initMarginChange")
    accepted = state is not None and margin is not None and not codes
    if codes:
        verdict = "REFUSED"
    elif accepted:
        verdict = "ACCEPTED"
    else:
        verdict = "UNDECIDED"

    return {
        "orderType": order_type,
        "orderType_wire": order.orderType,
        "tif": tif,
        "attrs": attrs,
        "verdict": verdict,
        "timed_out": timed_out,
        "codes": codes,
        "messages": messages,
        "initMarginChange": margin,
        "maintMarginChange": _field("maintMarginChange"),
        "commission": _field("commission"),
    }


async def cmd_shape(args) -> None:
    ib = await connect(args)
    try:
        contract = build_contract(args)
        (qualified,) = await ib.qualifyContractsAsync(contract) or (None,)
        if qualified is None or qualified.conId <= 0:
            die("contract did not qualify to a real conId")
        result = await whatif_shape(
            ib, qualified, args.type, args.tif, args.attr, args.qty, args.price,
            respect_budget=not args.no_budget,
        )
        print(json.dumps(result, indent=2, default=str))
        for c in result["codes"]:
            print("  " + describe_code(c), file=sys.stderr)
    finally:
        ib.disconnect()


async def cmd_matrix(args) -> None:
    ib = await connect(args)
    try:
        contract = build_contract(args)
        (qualified,) = await ib.qualifyContractsAsync(contract) or (None,)
        if qualified is None or qualified.conId <= 0:
            die("contract did not qualify to a real conId")

        details = await ib.reqContractDetailsAsync(qualified)
        declared = set(details[0].orderTypes.split(",")) if details else set()

        types = [t.strip() for t in args.types.split(",") if t.strip()]
        tifs = [t.strip() for t in args.tifs.split(",") if t.strip()]
        if not types or not tifs:
            die("--types and --tifs must each name at least one entry")
        # Count the cells that will actually be probed before estimating the runtime:
        # NOT-DECLARED cells are skipped without a what-if, and the first probe never waits.
        # FOK never appears as a capability token (it is a TIF only), so skip its token check.
        probed = sum(1 for ot in types for tif in tifs
                     if ot in declared and (tif == "FOK" or tif in declared))
        info(f"{len(types) * len(tifs)} cells, {probed} probed; at 1 per minute this takes "
             f"about {max(0, probed - 1)} minutes")
        rows = []
        for ot in types:
            for tif in tifs:
                if ot not in declared:
                    rows.append({"orderType": ot, "tif": tif, "verdict": "NOT-DECLARED",
                                 "codes": [], "messages": ["absent from ContractDetails.orderTypes"]})
                    continue
                if tif != "FOK" and tif not in declared:
                    rows.append({"orderType": ot, "tif": tif, "verdict": "NOT-DECLARED",
                                 "codes": [], "messages": ["TIF absent from ContractDetails.orderTypes"]})
                    continue
                rows.append(await whatif_shape(
                    ib, qualified, ot, tif, args.attr, args.qty, args.price,
                    respect_budget=not args.no_budget,
                ))

        width = max(len(t) for t in types) + 2
        print("\n" + "orderType".ljust(width) + "".join(t.ljust(14) for t in tifs))
        for ot in types:
            line = ot.ljust(width)
            for tif in tifs:
                r = next(x for x in rows if x["orderType"] == ot and x["tif"] == tif)
                line += r["verdict"].ljust(14)
            print(line)
        print()
        print(json.dumps(rows, indent=2, default=str))
    finally:
        ib.disconnect()


# --------------------------------------------------------------------- bracket probe


def _snap(price: float, increment: float) -> float:
    """Snap a price to an increment via integer steps, avoiding IEEE-754 residue."""
    from decimal import ROUND_HALF_UP, Decimal

    p, t = Decimal(str(price)), Decimal(str(increment))
    return float((p / t).quantize(Decimal(1), rounding=ROUND_HALF_UP) * t)


async def _band_increment(ib, details, exchange: str, price: float) -> float:
    """The increment in force at this price on this exchange; falls back to minTick."""
    try:
        exchanges = [e for e in details.validExchanges.split(",") if e]
        rules = [r for r in details.marketRuleIds.split(",") if r]
        rule_id = int(dict(zip(exchanges, rules)).get(exchange, rules[0]))
        bands = await ib.reqMarketRuleAsync(rule_id)
        if bands:
            applicable = [b for b in bands if b.lowEdge <= price]
            if applicable:
                return max(applicable, key=lambda b: b.lowEdge).increment
    except Exception:  # noqa: BLE001
        pass
    return details.minTick or 0.01


async def cmd_bracket(args) -> None:
    from ib_async import LimitOrder, StopOrder

    ib = await connect(args)
    trades = []  # bound before any placement so the finally block can never over-reach
    try:
        contract = build_contract(args)
        (qualified,) = await ib.qualifyContractsAsync(contract) or (None,)
        if qualified is None or qualified.conId <= 0:
            die("contract did not qualify to a real conId")

        details_list = await ib.reqContractDetailsAsync(qualified)
        details = details_list[0] if details_list else None

        ticker = ib.reqMktData(qualified, "", False, False)
        for _ in range(20):
            await asyncio.sleep(0.5)
            ref = ticker.marketPrice()
            if ref == ref and ref > 0:  # not NaN, positive
                break
        else:
            ref = None
        ib.cancelMktData(qualified)

        if ref is None:
            # Never place blind: with no quote, "50% of the reference" is 50% of a guess,
            # and on any instrument trading below that guess the entry is marketable.
            if args.price is None:
                die("no live quote for this contract (a fresh paper account often has no "
                    "market-data subscription). Re-run with an explicit --price <current "
                    "reference> once you have confirmed the level yourself.")
            ref = args.price
            info(f"no live quote; using operator-supplied reference {ref}")

        # Far from the market by construction, snapped to the increment actually in force
        # so the probe does not die on error 110 before measuring anything.
        inc = await _band_increment(ib, details, qualified.exchange, ref * 0.5) if details else 0.01
        entry = _snap(ref * 0.5, inc)
        tp = _snap(ref * 0.6, inc)
        sl = _snap(ref * 0.4, inc)
        info(f"reference {ref}, entry {entry}, tp {tp}, sl {sl}, increment {inc}")

        parent = LimitOrder("BUY", args.qty, entry)
        parent.orderId = ib.client.getReqId()
        parent.tif = args.parent_tif
        parent.transmit = False

        take = LimitOrder("SELL", args.qty, tp)
        take.orderId = ib.client.getReqId()
        take.parentId = parent.orderId
        take.tif = args.child_tif
        take.transmit = False

        stop = StopOrder("SELL", args.qty, sl)
        stop.orderId = ib.client.getReqId()
        stop.parentId = parent.orderId
        stop.tif = args.child_tif
        stop.transmit = True

        seen: list[str] = []
        ib.errorEvent += lambda r, c, s, k: seen.append(f"error {c}: {s}")

        trades = [ib.placeOrder(qualified, o) for o in (parent, take, stop)]
        await asyncio.sleep(6)

        print(json.dumps({
            "probed_at": datetime.now(timezone.utc).isoformat(),
            "parent_tif": args.parent_tif,
            "child_tif": args.child_tif,
            "legs": [
                {
                    "role": role,
                    "orderId": t.order.orderId,
                    "parentId": t.order.parentId,
                    "tif_sent": tif_sent,
                    # openOrder refreshes Order.tif from the venue; a read-back differing
                    # from what was sent is a terminal preset rewriting the order (10349).
                    "tif_readback": t.order.tif,
                    "status": t.orderStatus.status,
                    "filled": t.orderStatus.filled,
                    "remaining": t.orderStatus.remaining,
                    "log": [f"{e.status}:{e.errorCode}:{e.message}" for e in t.log],
                }
                for (role, tif_sent), t in zip(
                    (("parent", args.parent_tif), ("takeProfit", args.child_tif),
                     ("stopLoss", args.child_tif)), trades)
            ],
            "events": seen,
        }, indent=2, default=str))

        open_orders = await ib.reqOpenOrdersAsync()
        print(f"\nopen orders after placement: {len(open_orders)}", file=sys.stderr)
        print("A tif_readback differing from tif_sent means a terminal preset rewrote the "
              "order (see error 10349).", file=sys.stderr)
    finally:
        # Cancel ONLY the legs this probe placed. openTrades() would also return orders
        # resting under this client id from earlier sessions, which are not ours to kill.
        live = [t for t in trades if not t.isDone()]
        if live:
            info(f"cancelling the {len(live)} order(s) placed by this probe")
            for t in live:
                try:
                    ib.cancelOrder(t.order)
                except Exception as exc:  # noqa: BLE001
                    print(f"WARNING: cancel of order {t.order.orderId} raised: {exc}",
                          file=sys.stderr)
            await asyncio.sleep(3)
            stragglers = [t.order.orderId for t in trades if not t.isDone()]
            if stragglers:
                print(f"WARNING: order(s) {stragglers} still not done after cancel; "
                      f"verify on the gateway before walking away.", file=sys.stderr)
        ib.disconnect()


# ------------------------------------------------------------------------------- main


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=4002, help="paper only; 4001/7496 are refused")
    ap.add_argument("--client-id", type=int, default=99, help="keep clear of your running clients")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add_contract_args(p):
        p.add_argument("--stock")
        p.add_argument("--forex")
        p.add_argument("--cfd", help="EUR.USD for FX CFDs, or a plain symbol")
        p.add_argument("--future")
        p.add_argument("--option", help="SYMBOL,YYYYMMDD,STRIKE,C|P")
        p.add_argument("--crypto")
        p.add_argument("--index")
        p.add_argument("--exchange")
        p.add_argument("--currency")
        p.add_argument("--expiry")

    p = sub.add_parser("capabilities")
    add_contract_args(p)
    p.set_defaults(coro=cmd_capabilities)

    p = sub.add_parser("shape")
    add_contract_args(p)
    p.add_argument("--type", default="LMT")
    p.add_argument("--tif", default="DAY")
    p.add_argument("--attr", action="append", default=[], help="allOrNone, or minQty=100")
    p.add_argument("--qty", type=float, default=1)
    p.add_argument("--price", type=float, default=1.0)
    p.add_argument("--no-budget", action="store_true", help="skip the 1-per-minute spacing")
    p.set_defaults(coro=cmd_shape)

    p = sub.add_parser("matrix")
    add_contract_args(p)
    p.add_argument("--types", default="LMT,STP,STPLMT")
    p.add_argument("--tifs", default="DAY,GTC,IOC")
    p.add_argument("--attr", action="append", default=[])
    p.add_argument("--qty", type=float, default=1)
    p.add_argument("--price", type=float, default=1.0)
    p.add_argument("--no-budget", action="store_true")
    p.set_defaults(coro=cmd_matrix)

    p = sub.add_parser("bracket")
    add_contract_args(p)
    p.add_argument("--qty", type=float, default=1)
    p.add_argument("--price", type=float, default=None,
                   help="operator-confirmed reference, used ONLY when no live quote arrives")
    p.add_argument("--parent-tif", default="DAY")
    p.add_argument("--child-tif", default="GTC")
    p.set_defaults(coro=cmd_bracket)

    p = sub.add_parser("codes")
    p.add_argument("codes", nargs="+")
    p.set_defaults(func=cmd_codes)

    args = ap.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        asyncio.run(args.coro(args))


if __name__ == "__main__":
    main()
