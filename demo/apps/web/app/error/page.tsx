import { Button } from '@repo/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@repo/ui/card'
import Link from 'next/link'

export default function ErrorPage() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-destructive">Authentication Error</CardTitle>
          <CardDescription>
            There was a problem with your authentication request.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            This could be due to:
          </p>
          <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
            <li>Invalid email or password</li>
            <li>Email confirmation required</li>
            <li>Account does not exist</li>
            <li>Network connectivity issues</li>
          </ul>
          <div className="flex gap-2">
            <Button asChild className="flex-1">
              <Link href="/login">
                Try Again
              </Link>
            </Button>
            <Button variant="outline" asChild className="flex-1">
              <Link href="/signup">
                Sign Up
              </Link>
            </Button>
          </div>
          <div className="text-center">
            <Button variant="ghost" size="sm" asChild>
              <Link href="/">
                Back to Home
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 