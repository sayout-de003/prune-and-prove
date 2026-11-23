# Flow Map Template (Quick Reference)

Use this compact format inside `execution-flow.md` (or use `templates/flow-ledger.md` for full tabular ledgers):

```text
[Entrypoint] POST /api/payments (app/main.py::create_payment)
  -> validates: amount > 0, currency in ISO-4217
  -> calls: app/services/payment.py::PaymentService.process_payment
     -> invariant: status transitions pending -> completed only once
     -> calls: app/repositories/payment_repo.py::save_payment
        -> side effect: writes payment record
  -> returns: { amount, currency, status }
  -> provenance: static_ast (verify at runtime with tests/test_payment.py)
```
