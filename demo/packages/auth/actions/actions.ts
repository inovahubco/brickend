'use server'

import { revalidatePath } from 'next/cache'
import { redirect } from 'next/navigation'
import { createClient } from '../lib/server'

/**
 * Authenticates a user with email and password
 * Used with form actions for login forms
 * 
 * @param formData - FormData containing 'email' and 'password' fields
 * @throws {redirect} Redirects to '/error' on authentication failure
 * @throws {redirect} Redirects to '/dashboard' on successful login
 * 
 * @example
 * ```tsx
 * <form action={login}>
 *   <input name="email" type="email" required />
 *   <input name="password" type="password" required />
 *   <button type="submit">Sign In</button>
 * </form>
 * ```
 */
export async function login(formData: FormData) {
  const supabase = await createClient()

  // Type-casting to ensure we have the correct data
  const data = {
    email: formData.get('email') as string,
    password: formData.get('password') as string,
  }

  const { error } = await supabase.auth.signInWithPassword(data)

  if (error) {
    redirect('/error')
  }

  // Revalidate the layout to refresh auth state
  revalidatePath('/', 'layout')
  redirect('/dashboard')
}

/**
 * Creates a new user account with email and password
 * Used with form actions for signup forms
 * 
 * @param formData - FormData containing 'email' and 'password' fields
 * @throws {redirect} Redirects to '/error' on signup failure
 * @throws {redirect} Redirects to '/dashboard' on successful signup
 * 
 * @example
 * ```tsx
 * <form action={signup}>
 *   <input name="email" type="email" required />
 *   <input name="password" type="password" required />
 *   <button type="submit">Sign Up</button>
 * </form>
 * ```
 */
export async function signup(formData: FormData) {
  const supabase = await createClient()

  // Type-casting to ensure we have the correct data
  const data = {
    email: formData.get('email') as string,
    password: formData.get('password') as string,
  }

  const { error } = await supabase.auth.signUp(data)

  if (error) {
    redirect('/error')
  }

  // Revalidate the layout to refresh auth state
  revalidatePath('/', 'layout')
  redirect('/dashboard')
}

/**
 * Signs out the current user
 * Used with form actions for logout buttons
 * 
 * @throws {redirect} Redirects to '/error' on logout failure
 * @throws {redirect} Redirects to '/' on successful logout
 * 
 * @example
 * ```tsx
 * <form action={logout}>
 *   <button type="submit">Sign Out</button>
 * </form>
 * ```
 */
export async function logout() {
  const supabase = await createClient()

  const { error } = await supabase.auth.signOut()

  if (error) {
    redirect('/error')
  }

  // Revalidate the layout to refresh auth state
  revalidatePath('/', 'layout')
  redirect('/')
}

/**
 * Gets the current authenticated user without redirecting
 * Useful for optional authentication checks
 * 
 * @returns {Promise<User | null>} The user object if authenticated, null otherwise
 * 
 * @example
 * ```tsx
 * const user = await getUser()
 * if (user) {
 *   // User is authenticated
 *   return <div>Welcome, {user.email}!</div>
 * } else {
 *   // User is not authenticated
 *   return <div>Please log in</div>
 * }
 * ```
 */
export async function getUser() {
  const supabase = await createClient()
  const { data: { user }, error } = await supabase.auth.getUser()
  
  if (error) {
    return null
  }
  
  return user
}

/**
 * Ensures the user is authenticated, redirects to login if not
 * This is the primary function for protecting server components
 * 
 * @param redirectTo - The path to redirect to if not authenticated (default: '/login')
 * @returns {Promise<User>} The authenticated user object
 * @throws {redirect} Redirects to the specified login page if not authenticated
 * 
 * @example
 * ```tsx
 * // Basic usage - redirects to /login if not authenticated
 * const user = await requireAuth()
 * 
 * // Custom redirect path
 * const user = await requireAuth('/custom-login')
 * 
 * // Use in server component
 * export default async function ProtectedPage() {
 *   const user = await requireAuth()
 *   return <div>Welcome, {user.email}!</div>
 * }
 * ```
 */
export async function requireAuth(redirectTo: string = '/login') {
  const supabase = await createClient()
  const { data: { user }, error } = await supabase.auth.getUser()
  
  // Redirect to login if not authenticated
  if (error || !user) {
    redirect(redirectTo)
  }
  
  return user
} 