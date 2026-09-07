export interface InventoryProductSummary {
  id: number
  name: string
}

export interface InventoryUserSummary {
  id: number
  name: string
}

export interface AdminInventoryAdjustment {
  id: number
  product_id: number
  performed_by_user_id: number
  quantity_change: string
  stock_before: string
  stock_after: string
  reason: string
  created_at: string
  product: InventoryProductSummary
  performed_by_user: InventoryUserSummary
}

export interface AdminInventoryAdjustmentCreate {
  quantity_change: string
  reason: string
}