# Users Edge Function

Edge Function de Supabase para el manejo completo de perfiles de usuarios con CRUD, autenticación JWT, paginación, filtros y soft delete.

## 🚀 Características

- **CRUD completo** para perfiles de usuarios
- **Autenticación JWT** simple para pruebas
- **Row Level Security (RLS)** aplicado correctamente
- **Cliente Supabase optimizado** - una sola inicialización por request
- **Paginación** y filtros avanzados
- **Soft delete** con posibilidad de restauración
- **Validación robusta** con Zod schemas
- **Arquitectura modular** con handlers separados
- **Manejo de errores** estandarizado
- **CORS** habilitado
- **TypeScript** con tipos seguros

## 📋 Requisitos

- Supabase CLI instalado
- Deno 2.x
- Variables de entorno configuradas:
  - `SUPABASE_URL`
  - `SUPABASE_ANON_KEY`
  - `SUPABASE_SERVICE_ROLE_KEY` (para operaciones administrativas)

## 🗃️ Estructura de archivos

```
users/
├── index.ts           # Punto de entrada y router principal
├── auth.ts            # Middleware de autenticación
├── schemas.ts         # Esquemas Zod y tipos TypeScript
├── handlers/
│   ├── get.ts         # Handlers para requests GET
│   ├── post.ts        # Handlers para requests POST
│   ├── put.ts         # Handlers para requests PUT
│   └── delete.ts      # Handlers para requests DELETE
├── deno.json          # Configuración de Deno
└── README.md          # Este archivo
```

## 🔗 Endpoints disponibles

### GET Requests

| Endpoint | Descripción | Parámetros de consulta |
|----------|-------------|------------------------|
| `GET /users` | Listar perfiles con paginación | page, limit, search, gender, country, is_profile_public, sort_by, sort_order |
| `GET /users/me` | Obtener mi perfil | - |
| `GET /users/{id}` | Obtener perfil por ID | - |

### POST Requests

| Endpoint | Descripción | Body |
|----------|-------------|------|
| `POST /users` | Crear nuevo perfil | UserProfile JSON |
| `POST /users/{id}/restore` | Restaurar perfil eliminado | - |

### PUT Requests

| Endpoint | Descripción | Body |
|----------|-------------|------|
| `PUT /users/me` | Actualizar mi perfil | Partial UserProfile JSON |
| `PUT /users/{id}` | Actualizar perfil por ID | Partial UserProfile JSON |

### DELETE Requests

| Endpoint | Descripción | Body |
|----------|-------------|------|
| `DELETE /users/me` | Eliminar mi perfil (soft delete) | - |
| `DELETE /users/{id}` | Eliminar perfil por ID (soft delete) | - |

## 🔐 Autenticación

La función utiliza autenticación JWT simple. Incluye el token en el header `Authorization`:

```bash
Authorization: Bearer <your-jwt-token>
```

### Tokens de prueba

Para desarrollo, puedes usar el token hardcodeado:
```bash
Authorization: Bearer test-token-2024
```

### Generar JWT personalizado

Usa la función `generateTestJWT` en el archivo `auth.ts`:

```javascript
const token = generateTestJWT("user-uuid-here", "user@example.com");
```

## 📊 Estructura de datos

### UserProfile Schema

```typescript
{
  username: string,              // Requerido, único
  first_name?: string,
  last_name?: string,
  date_of_birth?: string,        // Formato ISO date
  gender?: "male" | "female" | "other" | "prefer_not_to_say",
  phone?: string,
  address_line1?: string,
  address_line2?: string,
  city?: string,
  state?: string,
  postal_code?: string,
  country?: string,              // Default: "Colombia"
  preferences?: Record<string, any>,
  bio?: string,
  avatar_url?: string,           // URL válida
  website?: string,              // URL válida
  occupation?: string,
  is_profile_public?: boolean    // Default: false
}
```

## 🔍 Parámetros de consulta (GET /users)

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `page` | number | 1 | Número de página |
| `limit` | number | 10 | Elementos por página (max 100) |
| `search` | string | - | Buscar en username, first_name, last_name |
| `gender` | enum | - | Filtrar por género |
| `country` | string | - | Filtrar por país |
| `is_profile_public` | boolean | - | Filtrar por visibilidad |
| `sort_by` | enum | created_at | Campo para ordenar |
| `sort_order` | enum | desc | asc o desc |

## 📝 Ejemplos de uso

### 1. Crear un perfil

```bash
curl -X POST 'http://127.0.0.1:54321/functions/v1/users' \
  --header 'Authorization: Bearer test-token-2024' \
  --header 'Content-Type: application/json' \
  --data '{
    "username": "johndoe",
    "first_name": "John",
    "last_name": "Doe",
    "date_of_birth": "1990-01-15",
    "gender": "male",
    "country": "Colombia",
    "bio": "Software developer",
    "is_profile_public": true
  }'
```

### 2. Obtener mi perfil

```bash
curl -X GET 'http://127.0.0.1:54321/functions/v1/users/me' \
  --header 'Authorization: Bearer test-token-2024'
```

### 3. Listar perfiles con filtros

```bash
curl -X GET 'http://127.0.0.1:54321/functions/v1/users?page=1&limit=5&search=john&gender=male&sort_by=username&sort_order=asc' \
  --header 'Authorization: Bearer test-token-2024'
```

### 4. Actualizar mi perfil

```bash
curl -X PUT 'http://127.0.0.1:54321/functions/v1/users/me' \
  --header 'Authorization: Bearer test-token-2024' \
  --header 'Content-Type: application/json' \
  --data '{
    "bio": "Senior Software Developer",
    "website": "https://johndoe.dev"
  }'
```

### 5. Eliminar mi perfil (soft delete)

```bash
curl -X DELETE 'http://127.0.0.1:54321/functions/v1/users/me' \
  --header 'Authorization: Bearer test-token-2024'
```

## 🚨 Respuestas de error

La función devuelve errores en formato estandarizado:

```json
{
  "error": {
    "message": "Error description",
    "status": 400,
    "details": {},
    "timestamp": "2024-01-01T12:00:00.000Z"
  }
}
```

### Códigos de error comunes

- `400` - Bad Request (datos inválidos)
- `401` - Unauthorized (autenticación fallida)
- `404` - Not Found (recurso no encontrado)
- `405` - Method Not Allowed
- `409` - Conflict (username duplicado)
- `500` - Internal Server Error

## 🧪 Testing

### Ejecutar localmente

1. Iniciar Supabase local:
```bash
supabase start
```

2. Desplegar la función:
```bash
supabase functions deploy users
```

3. Hacer requests de prueba usando los ejemplos anteriores.

### Variables de entorno necesarias

Asegúrate de que estén configuradas:
```bash
export SUPABASE_URL="http://127.0.0.1:54321"
export SUPABASE_ANON_KEY="your-anon-key"
export SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
```

## 🔧 Configuración de la base de datos

La función requiere que ejecutes la migración incluida para crear la tabla `user_profiles`:

```bash
supabase db push
```

La migración incluye:
- Tabla `user_profiles` con todos los campos necesarios
- Índices para optimizar rendimiento
- Triggers para `updated_at` y soft delete
- Row Level Security (RLS) policies
- Funciones SQL auxiliares

## 🛡️ Seguridad

- **RLS habilitado**: Los usuarios solo pueden acceder a sus propios perfiles
- **Cliente con JWT del usuario**: Se usa el token del usuario para aplicar RLS correctamente
- **Una sola inicialización**: El cliente se crea una vez por request para optimizar rendimiento
- **Validación de entrada**: Todos los datos se validan con Zod
- **Autenticación requerida**: Todas las requests requieren token válido
- **Soft delete**: Los datos no se eliminan físicamente
- **Sanitización**: Prevención de SQL injection con Supabase client

## 🔄 Versionado

Esta es la versión 1.0.0 de la función users. Para cambios futuros, considera:
- Mantener compatibilidad hacia atrás
- Documentar breaking changes
- Usar versionado semántico 