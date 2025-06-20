# Auth Package Documentation

This package provides authentication utilities for Next.js applications using Supabase Auth with Server-Side Rendering (SSR) support.

## Overview

The auth package consists of several modules that work together to provide a complete authentication solution:

- **Client**: Browser-side Supabase client
- **Server**: Server-side Supabase client
- **Actions**: Server actions for authentication operations
- **Middleware**: Request middleware for protecting routes
- **Types**: TypeScript type definitions

## Files Structure

```
src/auth/
├── actions.ts      # Server actions for auth operations
├── client.ts       # Browser-side Supabase client
├── server.ts       # Server-side Supabase client
├── middleware.ts   # Route protection middleware
├── types.ts        # TypeScript type definitions
└── README.md       # This documentation
```

## Quick Start

### 1. Environment Variables

Ensure these environment variables are set:

```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### 2. Basic Usage

```typescript
import { requireAuth, login, logout } from '@repo/utils/auth/actions'

// Protect a server component
export default async function ProtectedPage() {
  const user = await requireAuth() // Redirects to /login if not authenticated
  return <div>Welcome, {user.email}!</div>
}
```

## API Reference

### Server Actions (`actions.ts`)

#### `requireAuth(redirectTo?: string)`
**Purpose**: Ensures user is authenticated, redirects if not.
**Usage**: Server components that require authentication
**Returns**: User object if authenticated
**Throws**: Redirects to login page if not authenticated

```typescript
// Basic usage
const user = await requireAuth()

// Custom redirect
const user = await requireAuth('/custom-login')
```

#### `getUser()`
**Purpose**: Gets current user without redirecting
**Usage**: When you need to check auth status without forcing redirect
**Returns**: User object or null

```typescript
const user = await getUser()
if (user) {
  // User is authenticated
} else {
  // User is not authenticated
}
```

#### `login(formData: FormData)`
**Purpose**: Authenticates user with email/password
**Usage**: Login forms
**Form fields**: `email`, `password`

```typescript
<form action={login}>
  <input name="email" type="email" required />
  <input name="password" type="password" required />
  <button type="submit">Sign In</button>
</form>
```

#### `signup(formData: FormData)`
**Purpose**: Creates new user account
**Usage**: Registration forms
**Form fields**: `email`, `password`

```typescript
<form action={signup}>
  <input name="email" type="email" required />
  <input name="password" type="password" required />
  <button type="submit">Sign Up</button>
</form>
```

#### `logout()`
**Purpose**: Signs out current user
**Usage**: Logout buttons

```typescript
<form action={logout}>
  <button type="submit">Sign Out</button>
</form>
```

### Client Functions

#### `createClient()` (from `client.ts`)
**Purpose**: Creates browser-side Supabase client
**Usage**: Client components that need Supabase access

```typescript
import { createClient } from '@repo/utils/auth/client'

const supabase = createClient()
const { data: { user } } = await supabase.auth.getUser()
```

#### `createClient()` (from `server.ts`)
**Purpose**: Creates server-side Supabase client
**Usage**: Server components and API routes

```typescript
import { createClient } from '@repo/utils/auth/server'

const supabase = await createClient()
const { data: { user } } = await supabase.auth.getUser()
```

### Middleware

#### `updateSession(request, config?)`
**Purpose**: Protects routes and manages session cookies
**Usage**: Next.js middleware

```typescript
// middleware.ts
import { updateSession } from '@repo/utils/auth/middleware'

export async function middleware(request: NextRequest) {
  return await updateSession(request, {
    redirectTo: '/login',
    allowUnauthenticated: ['/login', '/signup', '/']
  })
}
```

**Configuration Options:**
- `redirectTo`: Where to redirect unauthenticated users (default: `/login`)
- `allowUnauthenticated`: Array of paths that don't require auth
- `requireAuth`: Array of paths that explicitly require auth

## Common Patterns

### Protected Server Component

```typescript
import { requireAuth } from '@repo/utils/auth/actions'

export default async function Dashboard() {
  const user = await requireAuth()
  
  return (
    <div>
      <h1>Dashboard</h1>
      <p>Welcome, {user.email}!</p>
    </div>
  )
}
```

### Optional Authentication

```typescript
import { getUser } from '@repo/utils/auth/actions'

export default async function HomePage() {
  const user = await getUser()
  
  return (
    <div>
      <h1>Home</h1>
      {user ? (
        <p>Welcome back, {user.email}!</p>
      ) : (
        <p>Please log in to continue</p>
      )}
    </div>
  )
}
```

### Client-Side Auth Check

```typescript
'use client'
import { createClient } from '@repo/utils/auth/client'
import { useEffect, useState } from 'react'

export function ClientComponent() {
  const [user, setUser] = useState(null)
  const supabase = createClient()
  
  useEffect(() => {
    supabase.auth.getUser().then(({ data: { user } }) => {
      setUser(user)
    })
  }, [])
  
  return <div>{user ? `Hello ${user.email}` : 'Not logged in'}</div>
}
```

## TypeScript Types

The package exports several TypeScript interfaces for type safety:

- `AuthState`: Authentication state object
- `LoginCredentials`: Login form data
- `SignUpCredentials`: Signup form data
- `AuthError`: Authentication error object
- `ProtectedRouteConfig`: Middleware configuration
- `AuthCookieConfig`: Cookie configuration

## Error Handling

Authentication errors are handled automatically:
- Failed login/signup redirects to `/error`
- Unauthenticated access redirects to login page
- Server errors are caught and handled gracefully

## Security Notes

1. Always use `requireAuth()` for protected server components
2. The middleware automatically manages session cookies
3. Don't expose sensitive auth logic to client-side code
4. Use server actions for all authentication operations

## Migration Guide

If migrating from manual auth checks:

**Before:**
```typescript
const supabase = await createClient()
const { data: { user }, error } = await supabase.auth.getUser()
if (error || !user) {
  redirect('/login')
}
```

**After:**
```typescript
const user = await requireAuth()
``` 