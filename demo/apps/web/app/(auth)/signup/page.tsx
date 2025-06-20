import { AuthForm } from '@repo/auth'
import { Suspense } from 'react'

export default function SignUpPage() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <Suspense fallback={<div>Loading...</div>}>
        <AuthForm mode="signup" />
      </Suspense>
    </div>
  )
} 