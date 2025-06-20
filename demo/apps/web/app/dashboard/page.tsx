import { createServerClient } from '@repo/auth'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@repo/ui/card'

export default async function DashboardPage() {
  const supabase = await createServerClient()
  const { data: { user } } = await supabase.auth.getUser()

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-muted-foreground">
          Welcome to your protected dashboard area.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Profile Information</CardTitle>
            <CardDescription>Your account details</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div>
                <span className="text-sm font-medium">Email:</span>
                <p className="text-sm text-muted-foreground">{user?.email}</p>
              </div>
              <div>
                <span className="text-sm font-medium">User ID:</span>
                <p className="text-sm text-muted-foreground font-mono">{user?.id}</p>
              </div>
              <div>
                <span className="text-sm font-medium">Created:</span>
                <p className="text-sm text-muted-foreground">
                  {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Authentication Status</CardTitle>
            <CardDescription>Your current session</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <div className="h-2 w-2 rounded-full bg-green-500"></div>
                <span className="text-sm">Authenticated</span>
              </div>
              <div>
                <span className="text-sm font-medium">Last Sign In:</span>
                <p className="text-sm text-muted-foreground">
                  {user?.last_sign_in_at ? new Date(user.last_sign_in_at).toLocaleString() : 'N/A'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Protected Content</CardTitle>
            <CardDescription>This content is only visible to authenticated users</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              🎉 Congratulations! You have successfully accessed a protected route. 
              This page can only be viewed by authenticated users.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
} 