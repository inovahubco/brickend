This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/create-next-app).

## Project Overview

This is a full-stack web application built with:
- **Frontend**: Next.js 15 with App Router
- **Backend**: Supabase (Database, Authentication, Real-time subscriptions)
- **Package Manager**: Bun
- **Styling**: Tailwind CSS
- **UI Components**: Custom component library

## Getting Started

### Prerequisites

- [Bun](https://bun.sh/) package manager
- [Node.js](https://nodejs.org/) 18 or later
- [Docker](https://www.docker.com/) (required for Supabase local development)
- [Supabase CLI](https://supabase.com/docs/guides/cli/getting-started)

### Installation Steps

#### 1. Install Supabase CLI

```bash
# On macOS
brew install supabase/tap/supabase

# On Windows (with Scoop)
scoop bucket add supabase https://github.com/supabase/scoop-bucket.git
scoop install supabase

# Or with npm
npm install -g supabase
```

#### 2. Install Project Dependencies

```bash
bun install
```

#### 3. Start Supabase Local Development

Navigate to the project root and start Supabase:

```bash
# From the demo directory
cd ../..  # Go to project root if you're in demo/apps/web
supabase start
```

This will:
- Start a local PostgreSQL database
- Start the Supabase Studio (database management UI)
- Start the Auth server for user authentication
- Start the API server
- Start the Storage server for file uploads

**Important**: The first time you run this, it will download Docker images which may take a few minutes.

After starting, you'll see output like:
```
Started supabase local development setup.

         API URL: http://localhost:54321
     GraphQL URL: http://localhost:54321/graphql/v1
          DB URL: postgresql://postgres:postgres@localhost:54322/postgres
      Studio URL: http://localhost:54323
    Inbucket URL: http://localhost:54324
      JWT secret: your-jwt-secret
       anon key: your-anon-key
service_role key: your-service-role-key
```

#### 4. Create Environment File

Create a `.env.local` file in the `demo/apps/web` directory:

```bash
# Navigate back to the web app directory
cd demo/apps/web
touch .env.local
```

Add the following environment variables to `.env.local` (use the values from the Supabase start output):

```env
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=http://localhost:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-from-supabase-start-output

# Optional: Add these if your app uses them
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-from-output
SUPABASE_JWT_SECRET=your-jwt-secret-from-output
```

#### 5. Run the Development Server

```bash
bun dev
```

### Accessing the Application

- **Web App**: [http://localhost:3000](http://localhost:3000)
- **Supabase Studio** (Database UI): [http://localhost:54323](http://localhost:54323)
- **Supabase API**: [http://localhost:54321](http://localhost:54321)

### Understanding the Project Structure

- **Authentication**: User login/signup functionality powered by Supabase Auth
- **Database**: PostgreSQL database managed through Supabase with real-time capabilities
- **API Routes**: Next.js API routes for server-side logic
- **UI Components**: Reusable components built with Tailwind CSS

## Demo Workspace Structure

This project is part of a Turborepo monorepo. Here's how the `demo/` workspace is organized:

```
demo/
├── apps/                          # Applications
│   ├── docs/                     # Documentation site (Next.js)
│   │   ├── app/                  # Next.js App Router pages
│   │   ├── public/               # Static assets
│   │   └── package.json          # Dependencies for docs app
│   │
│   └── web/                      # Main web application (THIS APP)
│       ├── app/                  # Next.js App Router
│       │   ├── (auth)/          # Auth pages (login, signup)
│       │   ├── dashboard/       # Protected dashboard pages
│       │   ├── error/           # Error pages
│       │   └── layout.tsx       # Root layout
│       ├── components/          # App-specific components
│       ├── lib/                 # App-specific utilities
│       ├── middleware.ts        # Next.js middleware for auth
│       └── package.json         # Web app dependencies
│
├── packages/                      # Shared packages
│   ├── eslint-config/            # Shared ESLint configurations
│   │   ├── base.js              # Base ESLint rules
│   │   ├── next.js              # Next.js specific rules
│   │   └── react-internal.js    # React internal rules
│   │
│   ├── typescript-config/        # Shared TypeScript configurations
│   │   ├── base.json            # Base TS config
│   │   ├── nextjs.json          # Next.js TS config
│   │   └── react-library.json   # React library TS config
│   │
│   ├── ui/                       # Shared UI component library
│   │   ├── src/components/ui/   # Reusable UI components
│   │   │   ├── auth/            # Authentication forms
│   │   │   ├── button.tsx       # Button component
│   │   │   ├── card.tsx         # Card component
│   │   │   ├── form.tsx         # Form components
│   │   │   ├── input.tsx        # Input component
│   │   │   └── loading-button.tsx # Loading button component
│   │   └── src/lib/utils.ts     # UI utility functions
│   │
│   └── utils/                    # Shared utility functions
│       └── src/auth/            # Authentication utilities
│           ├── actions.ts       # Server actions for auth
│           ├── client.ts        # Client-side Supabase client
│           ├── server.ts        # Server-side Supabase client
│           ├── middleware.ts    # Auth middleware helpers
│           └── types.ts         # Auth TypeScript types
│
├── supabase/                     # Supabase configuration
│   ├── config.toml              # Supabase project config
│   ├── functions/               # Edge functions
│   └── README.md                # Supabase setup instructions
│
├── package.json                  # Root package.json for workspace
├── turbo.json                   # Turborepo configuration
└── bun.lock                     # Lockfile for dependencies
```

### Key Features by Directory:

**`apps/web/`** (This application):
- **Authentication Flow**: Complete login/signup with Supabase
- **Protected Routes**: Dashboard and profile pages
- **Middleware**: Route protection and session management
- **Modern UI**: Tailwind CSS with custom component library

**`packages/ui/`** (Shared Components):
- **Auth Forms**: Reusable login/signup components
- **Base Components**: Buttons, cards, inputs, forms
- **Consistent Styling**: Shared design system
- **TypeScript**: Full type safety

**`packages/utils/`** (Shared Logic):
- **Auth Actions**: Server-side authentication logic
- **Supabase Clients**: Configured for client/server environments
- **Type Definitions**: Shared TypeScript interfaces

**`supabase/`** (Backend Configuration):
- **Database Schema**: PostgreSQL tables and relationships
- **Authentication**: User management and sessions
- **Edge Functions**: Serverless functions for custom logic

### Stopping the Development Environment

To stop all services:

```bash
# Stop the Next.js dev server
# Press Ctrl+C in the terminal running `bun dev`

# Stop Supabase
supabase stop
```

### Useful Development Commands

```bash
# View Supabase status
supabase status

# Reset the local database (⚠️ This will delete all data)
supabase db reset

# View database migrations
supabase db diff

# Generate TypeScript types from your database schema
supabase gen types typescript --local > types/supabase.ts
```

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load Inter, a custom Google Font.

## Learn More

To learn more about the technologies used:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.
- [Supabase Documentation](https://supabase.com/docs) - learn about Supabase features and API.
- [Supabase Local Development](https://supabase.com/docs/guides/cli/local-development) - detailed local development guide.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!


