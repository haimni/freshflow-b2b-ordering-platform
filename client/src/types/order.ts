export type OrderStatus =
  | 'pending'
  | 'confirmed'
  | 'processing'
  | 'completed'
  | 'cancelled'

export interface OrderItemCreate {
  product_id: number
  quantity: string
}

export interface OrderCreate {
  items: OrderItemCreate[]
}

export interface OrderItem {
  id: number
  product_id: number
  product_name: string
  quantity: string
  unit_price: string
  line_total: string
}

export interface CustomerOrder {
  id: number
  customer_id: number
  contract_id: number
  created_by_user_id: number
  total: string
  status: OrderStatus
  created_at: string
  updated_at: string
  items: OrderItem[]
}