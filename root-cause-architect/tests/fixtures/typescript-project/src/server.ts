import { handleOrder } from "./routes/orders";

const app: any = {};
app.post("/orders", handleOrder);
app.listen(3000);
