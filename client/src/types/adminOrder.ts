import type {
  CustomerOrder,
  OrderStatus,
} from './order'

export interface AdminOrderCustomer {
  id: number
  company_name: string
}

export interface AdminOrder extends CustomerOrder {
  customer: AdminOrderCustomer
}

export interface AdminOrderStatusUpdate {
  status: OrderStatus
}