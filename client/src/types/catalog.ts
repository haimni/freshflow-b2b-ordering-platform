export type PriceSource = 'contract' | 'default'

export interface CustomerProduct {
  id: number
  category_id: number
  name: string
  description: string | null
  stock: string
  image_url: string | null
  effective_price: string
  price_source: PriceSource
  contract_id: number | null
}