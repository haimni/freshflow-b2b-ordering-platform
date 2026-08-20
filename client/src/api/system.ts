import { apiRequest } from './http'

export interface HealthResponse {
  status: string
  service: string
}

export function getHealth(): Promise<HealthResponse> {
  return apiRequest<HealthResponse>('/health')
}