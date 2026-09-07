import { readAccessToken } from './auth'
import { ApiError, apiRequest } from './http'
import type {
  AdminInventoryAdjustment,
  AdminInventoryAdjustmentCreate,
} from '../types/adminInventory'

interface AdminInventoryAdjustmentQuery {
  productId?: number
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

export function getAdminInventoryAdjustments(
  query: AdminInventoryAdjustmentQuery = {},
): Promise<AdminInventoryAdjustment[]> {
  const parameters = new URLSearchParams({
    offset: String(query.offset ?? 0),
    limit: String(query.limit ?? 100),
  })

  if (query.productId !== undefined) {
    parameters.set(
      'product_id',
      String(query.productId),
    )
  }

  return apiRequest<AdminInventoryAdjustment[]>(
    `/admin/inventory-adjustments?${parameters.toString()}`,
    {
      headers: authorizationHeaders(),
    },
  )
}

export function createAdminInventoryAdjustment(
  productId: number,
  adjustment: AdminInventoryAdjustmentCreate,
): Promise<AdminInventoryAdjustment> {
  return apiRequest<AdminInventoryAdjustment>(
    `/admin/products/${productId}/inventory-adjustments`,
    {
      method: 'POST',
      headers: {
        ...authorizationHeaders(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(adjustment),
    },
  )
}