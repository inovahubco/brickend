# Supabase Edge Functions with Deno v2

This directory contains the Supabase configuration and Edge Functions for the demo project.

## Configuration

- **Deno Version**: v2 (configured in `config.toml`)
- **Edge Runtime**: Enabled with `oneshot` policy for hot reload
- **Inspector Port**: 8083 for debugging
- **Modern Dependency Management**: Uses Deno 2's native dependency system (no legacy import_map)
- **JSR Support**: Leverages the Deno JSR (JavaScript Registry) for type definitions

## Getting Started

### Prerequisites

Make sure you have Docker installed and running on your machine.

### Start Local Development

```bash
# Start Supabase local development environment
bunx supabase start

# Stop Supabase local development environment
bunx supabase stop
```

### Create a New Edge Function

```bash
# Traditional approach (will be updated automatically for Deno 2)
bunx supabase functions new <function-name>

# Modern Deno 2 approach (recommended)
deno init --serve <function-name>
# Then configure in supabase/config.toml:
# [functions.<function-name>]
# entrypoint = "./functions/<function-name>/main.ts"
```

### Adding Dependencies (Deno 2 Way)

```bash
cd supabase/functions/<function-name>
deno add npm:package-name        # Add npm packages
deno add jsr:@scope/package     # Add JSR packages
deno remove package-name        # Remove packages
```

### Serve Functions Locally

```bash
# Serve all functions
bunx supabase functions serve

# Serve a specific function
bunx supabase functions serve <function-name>
```

### Deploy Functions

```bash
# Deploy all functions
bunx supabase functions deploy

# Deploy a specific function
bunx supabase functions deploy <function-name>
```

## Example Function

The `hello-world` function demonstrates a basic Edge Function that:
- Accepts a JSON payload with a `name` field
- Returns a greeting message
- Uses Deno v2 runtime

### Test the hello-world function

```bash
curl -i --location --request POST 'http://127.0.0.1:54321/functions/v1/hello-world' \
  --header 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0' \
  --header 'Content-Type: application/json' \
  --data '{"name":"Functions"}'
```

## VS Code Integration

The project includes VS Code settings for Deno integration:
- Deno LSP enabled for `supabase/functions` directory
- TypeScript formatting using Deno
- Unstable features enabled for enhanced functionality

## Local URLs

When running locally:
- **API URL**: http://127.0.0.1:54321
- **Studio URL**: http://127.0.0.1:54323
- **Database URL**: postgresql://postgres:postgres@127.0.0.1:54322/postgres 