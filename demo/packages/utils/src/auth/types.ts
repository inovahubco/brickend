import type { User } from '@supabase/supabase-js'

export interface AuthState {
  user: User | null
  loading: boolean
  error: string | null
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface SignUpCredentials {
  email: string
  password: string
  options?: {
    data?: Record<string, unknown>
  }
}

export interface AuthError {
  message: string
  status?: number
}

export type AuthAction = 'signIn' | 'signUp' | 'signOut' | 'resetPassword'

// Cookie configuration for auth middleware
export interface AuthCookieConfig {
  name: string
  value: string
  options?: {
    domain?: string
    expires?: Date
    httpOnly?: boolean
    maxAge?: number
    path?: string
    sameSite?: 'strict' | 'lax' | 'none'
    secure?: boolean
  }
}

// Protected route configuration
export interface ProtectedRouteConfig {
  redirectTo?: string
  allowUnauthenticated?: string[]
  requireAuth?: string[]
} 