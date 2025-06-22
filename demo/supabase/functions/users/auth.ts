import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

// Configuración JWT simple para pruebas
const TEST_JWT_SECRET = "your-test-jwt-secret-key-2024";

interface AuthenticatedUser {
  user_id: string;
  email?: string;
  jwt_token: string;
}

/**
 * Middleware de autenticación JWT simple
 * Para pruebas, usa un token hardcodeado o JWT simple
 */
export async function authenticateRequest(request: Request): Promise<AuthenticatedUser | null> {
  try {
    const authHeader = request.headers.get("Authorization");
    
    if (!authHeader) {
      throw new Error("Authorization header missing");
    }

    // Extraer token del header "Bearer <token>"
    const token = authHeader.replace("Bearer ", "");
    
    if (!token) {
      throw new Error("Token missing");
    }

    // Para pruebas: usar token hardcodeado
    if (token === "test-token-2024") {
      return {
        user_id: "test-user-uuid-2024",
        email: "test@example.com",
        jwt_token: token
      };
    }

    // Intentar decodificar JWT simple (sin verificación para pruebas)
    try {
      const payload = parseJWT(token);
      
      if (!payload.user_id) {
        throw new Error("Invalid token payload");
      }

      return {
        user_id: payload.user_id,
        email: payload.email,
        jwt_token: token
      };
    } catch (error) {
      throw new Error("Invalid JWT token");
    }

  } catch (error) {
    console.error("Authentication error:", error);
    return null;
  }
}

/**
 * Parser JWT simple para pruebas (NO usar en producción)
 */
function parseJWT(token: string): any {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) {
      throw new Error("Invalid JWT format");
    }
    
    const payload = parts[1];
    const decoded = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
    return JSON.parse(decoded);
  } catch (error) {
    throw new Error("Failed to parse JWT");
  }
}

/**
 * Generar JWT simple para pruebas
 */
export function generateTestJWT(user_id: string, email?: string): string {
  const header = {
    alg: "HS256",
    typ: "JWT"
  };

  const payload = {
    user_id,
    email,
    iat: Math.floor(Date.now() / 1000),
    exp: Math.floor(Date.now() / 1000) + (60 * 60 * 24) // 24 horas
  };

  const encodedHeader = btoa(JSON.stringify(header)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
  const encodedPayload = btoa(JSON.stringify(payload)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
  
  // Para pruebas, no verificamos la firma
  const signature = "test-signature";
  
  return `${encodedHeader}.${encodedPayload}.${signature}`;
}

/**
 * Crear cliente de Supabase con JWT del usuario para RLS
 */
export function createSupabaseClientWithUserJWT(userJWT: string) {
  const supabaseUrl = Deno.env.get("SUPABASE_URL");
  const supabaseAnonKey = Deno.env.get("SUPABASE_ANON_KEY");

  if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error("Missing Supabase environment variables");
  }

  const supabase = createClient(supabaseUrl, supabaseAnonKey, {
    global: {
      headers: {
        Authorization: `Bearer ${userJWT}`,
      },
    },
  });

  return supabase;
}

/**
 * Crear cliente de Supabase con service role (para operaciones administrativas)
 */
export function createSupabaseServiceClient() {
  const supabaseUrl = Deno.env.get("SUPABASE_URL");
  const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");

  if (!supabaseUrl || !supabaseServiceKey) {
    throw new Error("Missing Supabase environment variables");
  }

  return createClient(supabaseUrl, supabaseServiceKey);
}

/**
 * Middleware para responses con CORS
 */
export function createCorsResponse(data: any, status = 200) {
  return new Response(
    JSON.stringify(data),
    {
      status,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
      },
    }
  );
}

/**
 * Manejo de errores estandarizado
 */
export function createErrorResponse(message: string, status = 400, details?: any) {
  return createCorsResponse({
    error: {
      message,
      status,
      details,
      timestamp: new Date().toISOString()
    }
  }, status);
} 