export type UserRole =
  | 'admin'
  | 'customer_manager'
  | 'customer_user'

export interface AccessToken {
  access_token: string
  token_type: string
}

export interface AuthenticatedUser {
  id: number
  customer_id: number | null
  name: string
  email: string
  role: UserRole
  active: boolean
}