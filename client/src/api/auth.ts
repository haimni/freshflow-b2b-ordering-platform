import { apiRequest } from './http'
import type {
  AccessToken,
  AuthenticatedUser,
} from '../types/auth'

const TOKEN_STORAGE_KEY = 'freshflow_access_token'

export async function login(
  email: string,
  password: string,
): Promise<AccessToken> {
  const formData = new URLSearchParams()

  formData.set('username', email.trim().toLowerCase())
  formData.set('password', password)

  return apiRequest<AccessToken>('/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData,
  })
}

export function getCurrentUser(
  accessToken: string,
): Promise<AuthenticatedUser> {
  return apiRequest<AuthenticatedUser>('/auth/me', {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  })
}

export function saveAccessToken(accessToken: string): void {
  sessionStorage.setItem(TOKEN_STORAGE_KEY, accessToken)
}

export function readAccessToken(): string | null {
  return sessionStorage.getItem(TOKEN_STORAGE_KEY)
}

export function removeAccessToken(): void {
  sessionStorage.removeItem(TOKEN_STORAGE_KEY)
}