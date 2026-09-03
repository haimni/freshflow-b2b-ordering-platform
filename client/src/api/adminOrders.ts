import { readAccessToken } from './auth'
import { ApiError, apiRequest } from './http'
import type {
  AdminOrder,
  AdminOrderStatusUpdate,
} from '../types/adminOrder'
import type { OrderStatus } from '../types/order'

interface GetAdminOrdersOptions {
  customerId?: number
  status?: OrderStatus
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

export function getAdminOrders(
  options: GetAdminOrdersOptions = {},
): Promise<AdminOrder[]> {
  const parameters = new URLSearchParams({
    offset: String(options.offset ?? 0),
    limit: String(options.limit ?? 100),
  })

  if (options.customerId !== undefined) {
    parameters.set(
      'customer_id',
      String(options.customerId),
    )
  }

  if (options.status !== undefined) {
    parameters.set('status', options.status)
  }

  return apiRequest<AdminOrder[]>(
    `/admin/orders?${parameters.toString()}`,
    {
      headers: authorizationHeaders(),
    },
  )
}

export function getAdminOrder(
  orderId: number,
): Promise<AdminOrder> {
  return apiRequest<AdminOrder>(
    `/admin/orders/${orderId}`,
    {
      headers: authorizationHeaders(),
    },
  )
}

export function updateAdminOrderStatus(
  orderId: number,
  update: AdminOrderStatusUpdate,
): Promise<AdminOrder> {
  return apiRequest<AdminOrder>(
    `/admin/orders/${orderId}/status`,
    {
      method: 'PATCH',
      headers: {
        ...authorizationHeaders(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(update),
    },
  )
}