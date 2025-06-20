import { z } from 'zod'
import type { User } from '@supabase/supabase-js'

// =============================================================================
// ZOD SCHEMAS (Single Source of Truth)
// =============================================================================

/**
 * Schema for validating authentication state
 * Useful for managing auth state in client components
 */
export const AuthStateSchema = z.object({
  /** The current authenticated user, null if not authenticated */
  user: z.custom<User>().nullable(),
  /** Whether an authentication operation is in progress */
  loading: z.boolean(),
  /** Any authentication error that occurred */
  error: z.string().nullable(),
})

/**
 * Schema for validating login credentials
 * Used with login forms and authentication functions
 */
export const LoginCredentialsSchema = z.object({
  /** User's email address */
  email: z.string().email('Please enter a valid email address'),
  /** User's password */
  password: z.string().min(6, 'Password must be at least 6 characters'),
})

/**
 * Schema for validating signup credentials
 * Used with signup forms and user creation functions
 */
export const SignUpCredentialsSchema = z.object({
  /** User's email address */
  email: z.string().email('Please enter a valid email address'),
  /** User's chosen password */
  password: z.string().min(6, 'Password must be at least 6 characters'),
  /** Optional additional data to store with the user */
  options: z.object({
    /** Custom user metadata */
    data: z.record(z.unknown()).optional(),
  }).optional(),
})

/**
 * Schema for validating authentication errors
 * Provides consistent error handling across the auth package
 */
export const AuthErrorSchema = z.object({
  /** Human-readable error message */
  message: z.string(),
  /** HTTP status code if applicable */
  status: z.number().optional(),
})

/**
 * Schema for validating authentication actions
 * Used for logging and state management
 */
export const AuthActionSchema = z.enum(['signIn', 'signUp', 'signOut', 'resetPassword'])

/**
 * Schema for validating authentication cookie configuration
 * Used internally by the middleware and server functions
 */
export const AuthCookieConfigSchema = z.object({
  /** Cookie name */
  name: z.string(),
  /** Cookie value */
  value: z.string(),
  /** Optional cookie configuration */
  options: z.object({
    /** Domain where cookie is valid */
    domain: z.string().optional(),
    /** Cookie expiration date */
    expires: z.date().optional(),
    /** Whether cookie is HTTP-only (not accessible via JavaScript) */
    httpOnly: z.boolean().optional(),
    /** Maximum age in seconds */
    maxAge: z.number().optional(),
    /** Path where cookie is valid */
    path: z.string().optional(),
    /** SameSite cookie attribute for CSRF protection */
    sameSite: z.enum(['strict', 'lax', 'none']).optional(),
    /** Whether cookie requires HTTPS */
    secure: z.boolean().optional(),
  }).optional(),
})

/**
 * Schema for validating protected route configuration
 * Defines which routes require authentication and where to redirect users
 */
export const ProtectedRouteConfigSchema = z.object({
  /** Where to redirect unauthenticated users (default: '/login') */
  redirectTo: z.string().optional(),
  /** Array of paths that don't require authentication (e.g., ['/login', '/signup', '/public']) */
  allowUnauthenticated: z.array(z.string()).optional(),
  /** Array of paths that explicitly require authentication */
  requireAuth: z.array(z.string()).optional(),
})

// =============================================================================
// TYPESCRIPT TYPES (Inferred from Zod schemas - Single Source of Truth)
// =============================================================================

/**
 * Represents the current authentication state of the application
 * Inferred from AuthStateSchema
 */
export type AuthState = z.infer<typeof AuthStateSchema>

/**
 * Credentials required for user login
 * Inferred from LoginCredentialsSchema
 */
export type LoginCredentials = z.infer<typeof LoginCredentialsSchema>

/**
 * Credentials required for user registration
 * Inferred from SignUpCredentialsSchema
 */
export type SignUpCredentials = z.infer<typeof SignUpCredentialsSchema>

/**
 * Standardized error object for authentication operations
 * Inferred from AuthErrorSchema
 */
export type AuthError = z.infer<typeof AuthErrorSchema>

/**
 * Types of authentication actions that can be performed
 * Inferred from AuthActionSchema
 */
export type AuthAction = z.infer<typeof AuthActionSchema>

/**
 * Configuration for setting authentication cookies
 * Inferred from AuthCookieConfigSchema
 */
export type AuthCookieConfig = z.infer<typeof AuthCookieConfigSchema>

/**
 * Configuration for route protection middleware
 * Inferred from ProtectedRouteConfigSchema
 */
export type ProtectedRouteConfig = z.infer<typeof ProtectedRouteConfigSchema>

// =============================================================================
// VALIDATION HELPERS
// =============================================================================

/**
 * Validates and parses login credentials
 * @param data - Raw data to validate
 * @returns Parsed and validated login credentials
 * @throws ZodError if validation fails
 */
export const validateLoginCredentials = (data: unknown): LoginCredentials => {
  return LoginCredentialsSchema.parse(data)
}

/**
 * Validates and parses signup credentials
 * @param data - Raw data to validate
 * @returns Parsed and validated signup credentials
 * @throws ZodError if validation fails
 */
export const validateSignUpCredentials = (data: unknown): SignUpCredentials => {
  return SignUpCredentialsSchema.parse(data)
}

/**
 * Validates and parses authentication error
 * @param data - Raw data to validate
 * @returns Parsed and validated auth error
 * @throws ZodError if validation fails
 */
export const validateAuthError = (data: unknown): AuthError => {
  return AuthErrorSchema.parse(data)
}

/**
 * Validates and parses protected route configuration
 * @param data - Raw data to validate
 * @returns Parsed and validated route config
 * @throws ZodError if validation fails
 */
export const validateProtectedRouteConfig = (data: unknown): ProtectedRouteConfig => {
  return ProtectedRouteConfigSchema.parse(data)
}

/**
 * Safe validation that returns a result object instead of throwing
 * @param schema - Zod schema to use for validation
 * @param data - Data to validate
 * @returns Success object with data or error object with issues
 */
export const safeValidate = <T>(schema: z.ZodSchema<T>, data: unknown) => {
  return schema.safeParse(data)
} 