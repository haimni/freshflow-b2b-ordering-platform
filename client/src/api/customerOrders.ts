import { readAccessToken } from './auth'
import { ApiError, apiRequest } from './http'
import type {
  CustomerOrder,
  OrderCreate,
} from '../types/order'

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

export function createCustomerOrder(
  order: OrderCreate,
): Promise<CustomerOrder> {
  return apiRequest<CustomerOrder>('/customer/orders', {
    method: 'POST',
    headers: {
      ...authorizationHeaders(),
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(order),
  })
}

export function getCustomerOrders(
  offset = 0,
  limit = 20,
): Promise<CustomerOrder[]> {
  const parameters = new URLSearchParams({
    offset: String(offset),
    limit: String(limit),
  })

  return apiRequest<CustomerOrder[]>(
    `/customer/orders?${parameters.toString()}`,
    {
      headers: authorizationHeaders(),
    },
  )
}

export function getCustomerOrder(
  orderId: number,
): Promise<CustomerOrder> {
  return apiRequest<CustomerOrder>(
    `/customer/orders/${orderId}`,
    {
      headers: authorizationHeaders(),
    },
  )
}

export function cancelCustomerOrder(
  orderId: number,
): Promise<CustomerOrder> {
  return apiRequest<CustomerOrder>(
    `/customer/orders/${orderId}/cancel`,
    {
      method: 'POST',
      headers: authorizationHeaders(),
    },
  )
}