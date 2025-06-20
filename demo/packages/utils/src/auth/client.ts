import { createBrowserClient } from '@supabase/ssr'

/**
 * Creates a Supabase client for use in browser/client-side components
 * This client is configured to work with Next.js SSR and handles cookies automatically
 * 
 * @returns {SupabaseClient} A Supabase client instance for browser use
 * 
 * @example
 * ```tsx
 * 'use client'
 * import { createClient } from '@repo/utils/auth/client'
 * 
 * export function ClientComponent() {
 *   const supabase = createClient()
 *   
 *   const handleLogin = async () => {
 *     const { data, error } = await supabase.auth.signInWithPassword({
 *       email: 'user@example.com',
 *       password: 'password'
 *     })
 *   }
 *   
 *   return <button onClick={handleLogin}>Login</button>
 * }
 * ```
 * 
 * @note This function should only be used in client components ('use client')
 * @note For server components, use the createClient function from './server'
 */
export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  )
} 