from app.services.payment import PaymentService


def test_process_payment():
    svc = PaymentService()
    res = svc.process_payment(50, "USD")
    assert res["status"] == "completed"
