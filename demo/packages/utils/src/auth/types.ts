import type { User } from '@supabase/supabase-js'

/**
 * Represents the current authentication state of the application
 * Useful for managing auth state in client components
 */
export interface AuthState {
  /** The current authenticated user, null if not authenticated */
  user: User | null
  /** Whether an authentication operation is in progress */
  loading: boolean
  /** Any authentication error that occurred */
  error: string | null
}

/**
 * Credentials required for user login
 * Used with login forms and authentication functions
 */
export interface LoginCredentials {
  /** User's email address */
  email: string
  /** User's password */
  password: string
}

/**
 * Credentials required for user registration
 * Used with signup forms and user creation functions
 */
export interface SignUpCredentials {
  /** User's email address */
  email: string
  /** User's chosen password */
  password: string
  /** Optional additional data to store with the user */
  options?: {
    /** Custom user metadata */
    data?: Record<string, unknown>
  }
}

/**
 * Standardized error object for authentication operations
 * Provides consistent error handling across the auth package
 */
export interface AuthError {
  /** Human-readable error message */
  message: string
  /** HTTP status code if applicable */
  status?: number
}

/**
 * Types of authentication actions that can be performed
 * Used for logging and state management
 */
export type AuthAction = 'signIn' | 'signUp' | 'signOut' | 'resetPassword'

/**
 * Configuration for setting authentication cookies
 * Used internally by the middleware and server functions
 */
export interface AuthCookieConfig {
  /** Cookie name */
  name: string
  /** Cookie value */
  value: string
  /** Optional cookie configuration */
  options?: {
    /** Domain where cookie is valid */
    domain?: string
    /** Cookie expiration date */
    expires?: Date
    /** Whether cookie is HTTP-only (not accessible via JavaScript) */
    httpOnly?: boolean
    /** Maximum age in seconds */
    maxAge?: number
    /** Path where cookie is valid */
    path?: string
    /** SameSite cookie attribute for CSRF protection */
    sameSite?: 'strict' | 'lax' | 'none'
    /** Whether cookie requires HTTPS */
    secure?: boolean
  }
}

/**
 * Configuration for route protection middleware
 * Defines which routes require authentication and where to redirect users
 */
export interface ProtectedRouteConfig {
  /** Where to redirect unauthenticated users (default: '/login') */
  redirectTo?: string
  /** Array of paths that don't require authentication (e.g., ['/login', '/signup', '/public']) */
  allowUnauthenticated?: string[]
  /** Array of paths that explicitly require authentication */
  requireAuth?: string[]
} 