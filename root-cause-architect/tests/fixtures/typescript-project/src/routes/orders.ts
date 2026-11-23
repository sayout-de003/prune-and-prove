export interface OrderPayload {
  id: string;
  total: number;
}

export function handleOrder(payload: OrderPayload): boolean {
  return payload.total > 0;
}
