export interface AdminCategory {
  id: number
  name: string
  description: string | null
  active: boolean
}

export interface AdminCategoryCreate {
  name: string
  description: string | null
  active: boolean
}

export interface AdminCategoryUpdate {
  name?: string
  description?: string | null
  active?: boolean
}

export interface AdminProduct {
  id: number
  category_id: number
  name: string
  description: string | null
  default_price: string
  stock: string
  image_url: string | null
  active: boolean
}

export interface AdminProductCreate {
  category_id: number
  name: string
  description: string | null
  default_price: string
  stock: string
  image_url: string | null
  active: boolean
}

export interface AdminProductUpdate {
  category_id?: number
  name?: string
  description?: string | null
  default_price?: string
  image_url?: string | null
  active?: boolean
}