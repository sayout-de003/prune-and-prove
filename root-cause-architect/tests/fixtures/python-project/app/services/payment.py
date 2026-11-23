from app.repositories.payment_repo import save_payment


def register(fn):
    return fn


class BaseService:
    pass


class PaymentService(BaseService):
    def validate_amount(self, amount: int) -> bool:
        return amount > 0

    def process_payment(self, amount: int, currency: str) -> dict:
        if not self.validate_amount(amount):
            raise ValueError("Invalid amount")
        return save_payment(amount, currency)


@register
def on_payment_webhook(payload: dict) -> dict:
    handler = getattr(PaymentService, "process_payment")
    return handler(PaymentService(), payload["amount"], payload["currency"])
