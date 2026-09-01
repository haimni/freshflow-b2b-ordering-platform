import type { CustomerProduct } from './catalog'

export interface CartItem {
  product: CustomerProduct
  quantity: string
}