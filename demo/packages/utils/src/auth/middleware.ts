import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'
import type { ProtectedRouteConfig } from './types'

/**
 * Middleware function to protect routes and manage user sessions
 * This function should be called from your Next.js middleware to handle authentication
 * 
 * @param request - The incoming Next.js request object
 * @param config - Optional configuration for route protection
 * @returns {Promise<NextResponse>} The middleware response with updated cookies
 * 
 * @example
 * ```tsx
 * // middleware.ts
 * import { NextRequest } from 'next/server'
 * import { updateSession } from '@repo/utils/auth/middleware'
 * 
 * export async function middleware(request: NextRequest) {
 *   return await updateSession(request, {
 *     redirectTo: '/login',
 *     allowUnauthenticated: ['/login', '/signup', '/public']
 *   })
 * }
 * 
 * export const config = {
 *   matcher: [
 *     '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
 *   ],
 * }
 * ```
 * 
 * @param config.redirectTo - Where to redirect unauthenticated users (default: '/login')
 * @param config.allowUnauthenticated - Array of paths that don't require authentication
 * @param config.requireAuth - Array of paths that explicitly require authentication
 */
export async function updateSession(
  request: NextRequest, 
  config?: ProtectedRouteConfig
) {
  // Create the response that will be returned with updated cookies
  let supabaseResponse = NextResponse.next({
    request,
  })

  // Create a Supabase client configured for middleware
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        // Read cookies from the request
        getAll() {
          return request.cookies.getAll()
        },
        // Set cookies on both request and response
        setAll(cookiesToSet: Array<{ name: string; value: string; options?: Record<string, unknown> }>) {
          // Set cookies on request for the current request
          cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value))
          
          // Create new response with updated cookies
          supabaseResponse = NextResponse.next({
            request,
          })
          
          // Set cookies on response for future requests
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options)
          )
        },
      },
    }
  )

  // IMPORTANT: Avoid writing any logic between createServerClient and
  // supabase.auth.getUser(). A simple mistake could make it very hard to debug
  // issues with users being randomly logged out.

  // Get the current user from the session
  const {
    data: { user },
  } = await supabase.auth.getUser()

  // Check if current path requires authentication
  const currentPath = request.nextUrl.pathname
  const allowUnauthenticated = config?.allowUnauthenticated || ['/login', '/auth', '/signup']
  const redirectTo = config?.redirectTo || '/login'

  // Redirect unauthenticated users from protected routes
  if (
    !user &&
    !allowUnauthenticated.some(path => currentPath.startsWith(path))
  ) {
    // no user, redirect to login page
    const url = request.nextUrl.clone()
    url.pathname = redirectTo
    return NextResponse.redirect(url)
  }

  // IMPORTANT: You *must* return the supabaseResponse object as it is. If you're
  // creating a new response object with NextResponse.next() make sure to:
  // 1. Pass the request in it, like so:
  //    const myNewResponse = NextResponse.next({ request })
  // 2. Copy over the cookies, like so:
  //    myNewResponse.cookies.setAll(supabaseResponse.cookies.getAll())
  // 3. Change the myNewResponse object to fit your needs, but avoid changing
  //    the cookies!
  // 4. Finally:
  //    return myNewResponse
  // If this is not done, you may be causing the browser and server to go out
  // of sync and terminate the user's session prematurely!

  return supabaseResponse
} 