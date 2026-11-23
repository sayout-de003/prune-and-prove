from app.services.payment import PaymentService


class FastAPI:
    def post(self, path: str):
        return lambda fn: fn


app = FastAPI()
service = PaymentService()


@app.post("/api/payments")
def create_payment(amount: int, currency: str) -> dict:
    return service.process_payment(amount, currency)


def run() -> None:
    create_payment(100, "USD")


if __name__ == "__main__":
    run()
