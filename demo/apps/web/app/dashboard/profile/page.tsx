import { createClient } from '@repo/utils/auth/server'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@repo/ui/card'
import { Button } from '@repo/ui/button'
import { Input } from '@repo/ui/input'
import { Label } from '@repo/ui/label'

export default async function ProfilePage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Profile</h2>
        <p className="text-muted-foreground">
          Manage your account settings and preferences.
        </p>
      </div>

      <div className="grid gap-6 max-w-2xl">
        <Card>
          <CardHeader>
            <CardTitle>Account Information</CardTitle>
            <CardDescription>
              Your personal account details
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-2">
              <Label htmlFor="email">Email Address</Label>
              <Input 
                id="email"
                type="email"
                value={user?.email || ''}
                disabled
                className="bg-muted"
              />
              <p className="text-xs text-muted-foreground">
                Email cannot be changed. Contact support if you need to update this.
              </p>
            </div>
            
            <div className="grid gap-2">
              <Label htmlFor="userId">User ID</Label>
              <Input 
                id="userId"
                value={user?.id || ''}
                disabled
                className="bg-muted font-mono text-xs"
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="createdAt">Member Since</Label>
              <Input 
                id="createdAt"
                value={user?.created_at ? new Date(user.created_at).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric'
                }) : 'N/A'}
                disabled
                className="bg-muted"
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Session Information</CardTitle>
            <CardDescription>
              Details about your current session
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-2">
              <Label htmlFor="lastSignIn">Last Sign In</Label>
              <Input 
                id="lastSignIn"
                value={user?.last_sign_in_at ? new Date(user.last_sign_in_at).toLocaleString() : 'N/A'}
                disabled
                className="bg-muted"
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="role">Role</Label>
              <Input 
                id="role"
                value={user?.role || 'authenticated'}
                disabled
                className="bg-muted"
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Account Actions</CardTitle>
            <CardDescription>
              Manage your account settings
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2">
              <Button disabled variant="outline">
                Change Password
              </Button>
              <Button disabled variant="outline">
                Update Profile
              </Button>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              These features are not implemented in this demo.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
} 