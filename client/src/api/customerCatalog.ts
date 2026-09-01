import { readAccessToken } from './auth'
import { ApiError, apiRequest } from './http'
import type { CustomerProduct } from '../types/catalog'

interface CustomerCatalogQuery {
  categoryId?: number
  offset?: number
  limit?: number
}

export function getCustomerProducts(
  query: CustomerCatalogQuery = {},
): Promise<CustomerProduct[]> {
  const accessToken = readAccessToken()

  if (!accessToken) {
    throw new ApiError(401, 'Authentication required')
  }

  const parameters = new URLSearchParams()

  if (query.categoryId !== undefined) {
    parameters.set('category_id', String(query.categoryId))
  }

  parameters.set('offset', String(query.offset ?? 0))
  parameters.set('limit', String(query.limit ?? 100))

  return apiRequest<CustomerProduct[]>(
    `/customer/products?${parameters.toString()}`,
    {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    },
  )
}