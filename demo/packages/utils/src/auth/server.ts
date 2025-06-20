import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'

/**
 * Creates a Supabase client for use in server-side components and API routes
 * This client is configured to work with Next.js SSR and manages auth cookies properly
 * 
 * @returns {Promise<SupabaseClient>} A Supabase client instance for server use
 * 
 * @example
 * ```tsx
 * // In a server component
 * import { createClient } from '@repo/utils/auth/server'
 * 
 * export default async function ServerComponent() {
 *   const supabase = await createClient()
 *   const { data: { user } } = await supabase.auth.getUser()
 *   
 *   return <div>User: {user?.email}</div>
 * }
 * 
 * // In an API route
 * export async function GET() {
 *   const supabase = await createClient()
 *   const { data: users } = await supabase.from('users').select('*')
 *   return Response.json(users)
 * }
 * ```
 * 
 * @note This function should only be used in server components and API routes
 * @note For client components, use the createClient function from './client'
 */
export async function createClient() {
  // Get the cookie store from Next.js headers
  const cookieStore = await cookies()

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        // Get all cookies for reading auth state
        getAll() {
          return cookieStore.getAll()
        },
        // Set cookies for managing auth state
        setAll(cookiesToSet: Array<{ name: string; value: string; options?: Record<string, unknown> }>) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            )
          } catch {
            // The `setAll` method was called from a Server Component.
            // This can be ignored if you have middleware refreshing
            // user sessions.
          }
        },
      },
    }
  )
} 