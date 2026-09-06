import { readAccessToken } from './auth'
import { ApiError, apiRequest } from './http'
import type {
  AdminCategory,
  AdminCategoryCreate,
  AdminCategoryUpdate,
  AdminProduct,
  AdminProductCreate,
  AdminProductUpdate,
} from '../types/adminCatalog'

interface AdminCategoryQuery {
  active?: boolean
  offset?: number
  limit?: number
}

interface AdminProductQuery {
  categoryId?: number
  active?: boolean
  offset?: number
  limit?: number
}

function requireAccessToken(): string {
  const accessToken = readAccessToken()

  if (!accessToken) {
    throw new ApiError(401, 'Authentication required')
  }

  return accessToken
}

function authorizationHeaders(): HeadersInit {
  return {
    Authorization: `Bearer ${requireAccessToken()}`,
  }
}

export function getAdminCategories(
  query: AdminCategoryQuery = {},
): Promise<AdminCategory[]> {
  const parameters = new URLSearchParams({
    offset: String(query.offset ?? 0),
    limit: String(query.limit ?? 100),
  })

  if (query.active !== undefined) {
    parameters.set('active', String(query.active))
  }

  return apiRequest<AdminCategory[]>(
    `/admin/categories?${parameters.toString()}`,
    {
      headers: authorizationHeaders(),
    },
  )
}

export function createAdminCategory(
  category: AdminCategoryCreate,
): Promise<AdminCategory> {
  return apiRequest<AdminCategory>(
    '/admin/categories',
    {
      method: 'POST',
      headers: {
        ...authorizationHeaders(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(category),
    },
  )
}

export function updateAdminCategory(
  categoryId: number,
  changes: AdminCategoryUpdate,
): Promise<AdminCategory> {
  return apiRequest<AdminCategory>(
    `/admin/categories/${categoryId}`,
    {
      method: 'PATCH',
      headers: {
        ...authorizationHeaders(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(changes),
    },
  )
}

export function getAdminProducts(
  query: AdminProductQuery = {},
): Promise<AdminProduct[]> {
  const parameters = new URLSearchParams({
    offset: String(query.offset ?? 0),
    limit: String(query.limit ?? 100),
  })

  if (query.categoryId !== undefined) {
    parameters.set(
      'category_id',
      String(query.categoryId),
    )
  }

  if (query.active !== undefined) {
    parameters.set('active', String(query.active))
  }

  return apiRequest<AdminProduct[]>(
    `/admin/products?${parameters.toString()}`,
    {
      headers: authorizationHeaders(),
    },
  )
}

export function createAdminProduct(
  product: AdminProductCreate,
): Promise<AdminProduct> {
  return apiRequest<AdminProduct>(
    '/admin/products',
    {
      method: 'POST',
      headers: {
        ...authorizationHeaders(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(product),
    },
  )
}

export function updateAdminProduct(
  productId: number,
  changes: AdminProductUpdate,
): Promise<AdminProduct> {
  return apiRequest<AdminProduct>(
    `/admin/products/${productId}`,
    {
      method: 'PATCH',
      headers: {
        ...authorizationHeaders(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(changes),
    },
  )
}