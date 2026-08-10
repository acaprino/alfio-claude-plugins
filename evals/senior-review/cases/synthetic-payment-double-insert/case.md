# Case: synthetic-payment-double-insert (data-integrity)

Synthetic. Materialize the file below into a scratch git repo (`payments/service.py`, plus an empty `payments/models.py` defining a `Payment` model with NO unique constraint), commit, then review the diff that added `record_payment`.

## Buggy code

```python
# payments/service.py
async def record_payment(session, order_id: str, amount: Decimal) -> Payment:
    existing = await session.execute(
        select(Payment).where(Payment.order_id == order_id)
    )
    if existing.scalar_one_or_none() is not None:
        raise DuplicatePaymentError(order_id)

    payment = Payment(order_id=order_id, amount=amount, status="captured")
    session.add(payment)
    await session.commit()

    await charge_gateway(order_id, amount)  # network call, can fail
    return payment
```

## Ground truth (3 bugs)

| # | Known bug | Expected dimension |
|---|-----------|--------------------|
| 1 | Check-then-insert without a UNIQUE constraint on `Payment.order_id`: two concurrent requests both pass the SELECT and both insert; uniqueness exists only in the application layer | data-integrity |
| 2 | The payment row is committed BEFORE the gateway charge: a failed `charge_gateway` leaves a `captured` row for money never taken, with no compensation or status rollback | data-integrity / logic-integrity |
| 3 | No idempotency key on the gateway call: a retry of `record_payment` after a timeout can double-charge even when the row insert is fixed | data-integrity / distributed-flow |

## Scoring notes

- Bug 1 is the reviewer-conversation archetype ("the invariant exists in the application layer but not in the database"). `partial` for flagging the race without naming the missing constraint as the fix.
