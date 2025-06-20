import { AuthForm } from '@repo/auth'
import { Suspense } from 'react'

export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <Suspense fallback={<div>Loading...</div>}>
        <AuthForm mode="login" />
      </Suspense>
    </div>
  )
} 