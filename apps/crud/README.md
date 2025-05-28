# Supabase Edge Functions CRUD API

A complete CRUD API built with Supabase Edge Functions and Deno 2, featuring authentication, validation, and database operations.

## Features

- ✅ **Deno 2** runtime with modern TypeScript support
- ✅ **Supabase Edge Functions** for serverless deployment
- ✅ **JWT Authentication** with Supabase Auth
- ✅ **Zod Validation** for request/response schemas
- ✅ **Row Level Security (RLS)** for data protection
- ✅ **CORS Support** for web applications
- ✅ **Pagination** and filtering for list endpoints
- ✅ **Full-text search** capabilities
- ✅ **Database migrations** with proper indexing

## Project Structure

```
apps/crud/
├── supabase/
│   ├── functions/
│   │   ├── api/
│   │   │   ├── index.ts          # Main entry point and router
│   │   │   ├── create.ts         # POST endpoint handler
│   │   │   ├── read.ts           # GET endpoint handler
│   │   │   ├── update.ts         # PUT/PATCH endpoint handler
│   │   │   └── delete.ts         # DELETE endpoint handler
│   │   └── shared/
│   │       ├── auth.ts           # Authentication utilities
│   │       ├── cors.ts           # CORS configuration
│   │       ├── database.ts       # Database service layer
│   │       └── interfaces/
│   │           ├── schemas.ts    # Zod validation schemas
│   │           └── types.ts      # TypeScript interfaces
│   ├── migrations/
│   │   └── 20240101000000_create_items_table.sql
│   └── config.toml               # Supabase configuration
├── deno.json                     # Deno 2 configuration
└── README.md                     # This file
```

## API Endpoints

### Base URL
```
https://your-project.supabase.co/functions/v1/api
```

### Authentication
All endpoints require a valid JWT token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

### Endpoints

#### Create Item
```http
POST /api
Content-Type: application/json

{
  "title": "My Item",
  "description": "Item description",
  "status": "active",
  "priority": 1,
  "tags": ["tag1", "tag2"],
  "metadata": {"key": "value"}
}
```

#### Get Items (List with pagination)
```http
GET /api?page=1&limit=10&sort=created_at&order=desc&search=query&status=active
```

#### Get Single Item
```http
GET /api/{item-id}
```

#### Update Item
```http
PUT /api/{item-id}
Content-Type: application/json

{
  "title": "Updated Title",
  "status": "inactive"
}
```

#### Delete Item
```http
DELETE /api/{item-id}
```

## Data Schema

### Item Object
```typescript
interface Item {
  id: string;                    // UUID
  created_at: string;           // ISO datetime
  updated_at: string;           // ISO datetime
  user_id: string;              // UUID (automatically set)
  title: string;                // Required, max 255 chars
  description?: string;         // Optional
  status: "active" | "inactive" | "pending"; // Default: "active"
  priority: number;             // 1-5, default: 1
  tags?: string[];              // Optional array
  metadata?: Record<string, any>; // Optional JSON object
}
```

### Response Format
```typescript
// Success Response
{
  "success": true,
  "data": Item | Item[],
  "message"?: string,
  "pagination"?: {
    "page": number,
    "limit": number,
    "total": number,
    "totalPages": number
  }
}

// Error Response
{
  "success": false,
  "error": string,
  "details"?: any
}
```

## Setup Instructions

### Prerequisites
- [Deno 2](https://deno.land/) installed
- [Supabase CLI](https://supabase.com/docs/guides/cli) installed
- Supabase project created

### Local Development

1. **Initialize Supabase project:**
   ```bash
   cd apps/crud
   supabase init
   ```

2. **Start local Supabase:**
   ```bash
   supabase start
   ```

3. **Run database migrations:**
   ```bash
   supabase db reset
   ```

4. **Deploy Edge Function locally:**
   ```bash
   supabase functions serve api --no-verify-jwt
   ```

5. **Test the API:**
   ```bash
   curl -X GET http://localhost:54321/functions/v1/api \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
   ```

### Production Deployment

1. **Link to your Supabase project:**
   ```bash
   supabase link --project-ref YOUR_PROJECT_REF
   ```

2. **Deploy the Edge Function:**
   ```bash
   supabase functions deploy api
   ```

3. **Run migrations on production:**
   ```bash
   supabase db push
   ```

## Environment Variables

Set these in your Supabase project settings:

- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_ANON_KEY`: Your Supabase anon key
- `SUPABASE_SERVICE_ROLE_KEY`: Your Supabase service role key

## Security Features

### Row Level Security (RLS)
- Users can only access their own items
- Automatic user_id assignment on creation
- Secure by default with Supabase Auth

### Input Validation
- Zod schemas for all inputs
- Type-safe request/response handling
- Comprehensive error messages

### Authentication
- JWT token validation
- Supabase Auth integration
- Automatic user context extraction

## Query Parameters

### List Endpoint (`GET /api`)
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 10, max: 100)
- `sort`: Sort field (default: "created_at")
- `order`: Sort order "asc" | "desc" (default: "desc")
- `search`: Full-text search in title and description
- `status`: Filter by status ("active" | "inactive" | "pending")

## Error Handling

The API returns appropriate HTTP status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request (validation errors)
- `401`: Unauthorized
- `404`: Not Found
- `405`: Method Not Allowed
- `500`: Internal Server Error

## Development Commands

```bash
# Format code
deno task fmt

# Lint code
deno task lint

# Run locally
deno task dev

# Run tests
deno task test
```

## Database Schema

The `items` table includes:
- Proper indexing for performance
- Full-text search capabilities
- Automatic timestamp updates
- JSON support for metadata
- Array support for tags
- Row Level Security policies

## Contributing

1. Follow the existing code structure
2. Add proper TypeScript types
3. Include Zod validation for new fields
4. Update migrations for schema changes
5. Test all endpoints thoroughly

## License

This project is part of the Brickend monorepo.