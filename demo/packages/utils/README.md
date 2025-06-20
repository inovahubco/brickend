# @repo/utils

Shared utilities package for the monorepo, starting with Supabase authentication utilities.

## Installation

```bash
bun add @repo/utils
```

## Auth Module

The auth module provides utilities for integrating Supabase authentication with Next.js applications, following the [official Supabase documentation](https://supabase.com/docs/guides/auth/server-side/nextjs).

### Setup

1. Add environment variables to your `.env.local`:

```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

2. Set up middleware in your `middleware.ts`:

```typescript
import { type NextRequest } from 'next/server'
import { updateSession } from '@repo/utils/auth/middleware'

export async function middleware(request: NextRequest) {
  return await updateSession(request, {
    redirectTo: '/login',
    allowUnauthenticated: ['/login', '/signup', '/confirm', '/public']
  })
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}
```

### Usage

#### Client Components

```typescript
import { createClient } from '@repo/utils/auth/client'

export function ClientComponent() {
  const supabase = createClient()
  
  // Use supabase client for client-side operations
  const handleSignOut = async () => {
    await supabase.auth.signOut()
  }

  return <button onClick={handleSignOut}>Sign Out</button>
}
```

#### Server Components

```typescript
import { createClient } from '@repo/utils/auth/server'
import { redirect } from 'next/navigation'

export default async function ProtectedPage() {
  const supabase = await createClient()
  const { data: { user }, error } = await supabase.auth.getUser()

  if (error || !user) {
    redirect('/login')
  }

  return <div>Hello {user.email}</div>
}
```

#### Server Actions

```typescript
import { login, signup, logout } from '@repo/utils/auth/actions'

export default function LoginPage() {
  return (
    <form>
      <input name="email" type="email" required />
      <input name="password" type="password" required />
      <button formAction={login}>Log in</button>
      <button formAction={signup}>Sign up</button>
    </form>
  )
}
```

#### Route Handlers

```typescript
import { createClient } from '@repo/utils/auth/server'
import { NextResponse } from 'next/server'

export async function GET() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  return NextResponse.json({ user })
}
```

### Types

```typescript
import type { 
  AuthState, 
  LoginCredentials, 
  SignUpCredentials,
  ProtectedRouteConfig 
} from '@repo/utils/auth/types'
```

### Auth Confirmation Route

Create `app/(auth)/confirm/route.ts`:

```typescript
import { type EmailOtpType } from '@supabase/supabase-js'
import { type NextRequest } from 'next/server'
import { createClient } from '@repo/utils/auth/server'
import { redirect } from 'next/navigation'

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const token_hash = searchParams.get('token_hash')
  const type = searchParams.get('type') as EmailOtpType | null
  const next = searchParams.get('next') ?? '/'

  if (token_hash && type) {
    const supabase = await createClient()
    const { error } = await supabase.auth.verifyOtp({
      type,
      token_hash,
    })

    if (!error) {
      redirect(next)
    }
  }

  redirect('/error')
}
```

### Email Template Configuration

Update your Supabase email templates:

1. Go to Auth > Email Templates in your Supabase dashboard
2. In the "Confirm signup" template, change:
   ```
   {{ .ConfirmationURL }}
   ```
   to:
   ```
   {{ .SiteURL }}/confirm?token_hash={{ .TokenHash }}&type=email
   ```

## Features

- ✅ Client-side auth utilities
- ✅ Server-side auth utilities  
- ✅ Middleware for session management
- ✅ Server actions for auth operations
- ✅ TypeScript types and interfaces
- ✅ Configurable protected routes
- ✅ Email confirmation flow

## Security Notes

- Always use `supabase.auth.getUser()` in server code to validate sessions
- Never trust `supabase.auth.getSession()` on the server side
- The middleware automatically refreshes expired tokens
- Server components can't write cookies, so middleware handles token refresh 