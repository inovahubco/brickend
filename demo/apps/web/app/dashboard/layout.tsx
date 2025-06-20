import { logout, requireAuth } from '@repo/auth'
import { Button } from '@repo/ui/button'
import Link from 'next/link'

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const user = await requireAuth()

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="container mx-auto flex h-16 items-center justify-between px-4">
          <div className="flex items-center space-x-4">
            <h1 className="text-xl font-semibold">Dashboard</h1>
            <nav className="flex items-center space-x-4">
              <Link href="/dashboard" className="text-sm text-muted-foreground hover:text-foreground">
                Overview
              </Link>
              <Link href="/dashboard/profile" className="text-sm text-muted-foreground hover:text-foreground">
                Profile
              </Link>
            </nav>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-muted-foreground">
              Welcome, {user.email}
            </span>
            <form action={logout}>
              <Button variant="outline" size="sm">
                Sign Out
              </Button>
            </form>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {children}
      </main>
    </div>
  )
} 