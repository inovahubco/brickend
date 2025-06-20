import { AuthForm } from '@repo/ui/auth-form'

export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <AuthForm mode="login" />
    </div>
  )
} 