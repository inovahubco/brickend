/**
 * Función de Supabase Edge Function para manejo de perfiles de usuarios
 * 
 * Endpoints disponibles:
 * GET /users - Listar perfiles (con paginación y filtros)
 * GET /users/me - Obtener mi perfil
 * GET /users/{id} - Obtener perfil por ID
 * POST /users - Crear nuevo perfil
 * PUT /users/me - Actualizar mi perfil
 * PUT /users/{id} - Actualizar perfil por ID
 * DELETE /users/me - Eliminar mi perfil (soft delete)
 * DELETE /users/{id} - Eliminar perfil por ID (soft delete)
 * POST /users/{id}/restore - Restaurar perfil eliminado
 * 
 * Autenticación: Bearer token en header Authorization
 */

import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { authenticateRequest, createCorsResponse, createErrorResponse, createSupabaseClientWithUserJWT } from "./auth.ts";
import { handleGet, handleGetById, handleGetMyProfile } from "./handlers/get.ts";
import { handlePost } from "./handlers/post.ts";
import { handlePut, handlePutMyProfile } from "./handlers/put.ts";
import { handleDelete, handleDeleteMyProfile, handleRestore } from "./handlers/delete.ts";
import type { SupabaseClient } from "https://esm.sh/@supabase/supabase-js@2";

// Interfaz para el contexto de la request
interface RequestContext {
  request: Request;
  method: string;
  path: string;
  pathSegments: string[];
  user_id: string;
  supabaseClient: SupabaseClient;
}

/**
 * Función principal que maneja todas las requests
 */
Deno.serve(async (req: Request): Promise<Response> => {
  try {
    // Manejar requests OPTIONS para CORS
    if (req.method === "OPTIONS") {
      return createCorsResponse({}, 204);
    }

    // Autenticar la request
    const authResult = await authenticateRequest(req);
    if (!authResult) {
      return createErrorResponse("Authentication failed", 401);
    }

    // Crear cliente de Supabase con JWT del usuario para RLS
    const supabaseClient = createSupabaseClientWithUserJWT(authResult.jwt_token);

    // Crear contexto de la request
    const url = new URL(req.url);
    const pathSegments = url.pathname.split('/').filter(segment => segment !== '');
    
    // Remover el primer segmento si es "users"
    if (pathSegments[0] === 'users') {
      pathSegments.shift();
    }

    const context: RequestContext = {
      request: req,
      method: req.method,
      path: url.pathname,
      pathSegments,
      user_id: authResult.user_id,
      supabaseClient
    };

    // Router principal
    return await routeRequest(context);

  } catch (error) {
    console.error("Unexpected error in main handler:", error);
    return createErrorResponse("Internal server error", 500);
  }
});

/**
 * Router que determina qué handler ejecutar basado en la request
 */
async function routeRequest(context: RequestContext): Promise<Response> {
  const { request, method, pathSegments, user_id, supabaseClient } = context;

  try {
    switch (method) {
      case "GET":
        return await handleGetRequests(context);
      
      case "POST":
        return await handlePostRequests(context);
      
      case "PUT":
        return await handlePutRequests(context);
      
      case "DELETE":
        return await handleDeleteRequests(context);
      
      default:
        return createErrorResponse(`Method ${method} not allowed`, 405);
    }
  } catch (error) {
    console.error(`Error in ${method} route:`, error);
    return createErrorResponse("Internal server error", 500);
  }
}

/**
 * Maneja todas las requests GET
 */
async function handleGetRequests(context: RequestContext): Promise<Response> {
  const { request, pathSegments, user_id, supabaseClient } = context;

  // GET /users - Listar perfiles con paginación y filtros
  if (pathSegments.length === 0) {
    return await handleGet(request, user_id, supabaseClient);
  }

  // GET /users/me - Obtener mi perfil
  if (pathSegments.length === 1 && pathSegments[0] === "me") {
    return await handleGetMyProfile(request, user_id, supabaseClient);
  }

  // GET /users/{id} - Obtener perfil por ID
  if (pathSegments.length === 1 && isValidUUID(pathSegments[0])) {
    return await handleGetById(request, user_id, pathSegments[0], supabaseClient);
  }

  return createErrorResponse("Invalid GET endpoint", 404);
}

/**
 * Maneja todas las requests POST
 */
async function handlePostRequests(context: RequestContext): Promise<Response> {
  const { request, pathSegments, user_id, supabaseClient } = context;

  // POST /users - Crear nuevo perfil
  if (pathSegments.length === 0) {
    return await handlePost(request, user_id, supabaseClient);
  }

  // POST /users/{id}/restore - Restaurar perfil eliminado
  if (pathSegments.length === 2 && isValidUUID(pathSegments[0]) && pathSegments[1] === "restore") {
    return await handleRestore(request, user_id, pathSegments[0], supabaseClient);
  }

  return createErrorResponse("Invalid POST endpoint", 404);
}

/**
 * Maneja todas las requests PUT
 */
async function handlePutRequests(context: RequestContext): Promise<Response> {
  const { request, pathSegments, user_id, supabaseClient } = context;

  // PUT /users/me - Actualizar mi perfil
  if (pathSegments.length === 1 && pathSegments[0] === "me") {
    return await handlePutMyProfile(request, user_id, supabaseClient);
  }

  // PUT /users/{id} - Actualizar perfil por ID
  if (pathSegments.length === 1 && isValidUUID(pathSegments[0])) {
    return await handlePut(request, user_id, pathSegments[0], supabaseClient);
  }

  return createErrorResponse("Invalid PUT endpoint", 404);
}

/**
 * Maneja todas las requests DELETE
 */
async function handleDeleteRequests(context: RequestContext): Promise<Response> {
  const { request, pathSegments, user_id, supabaseClient } = context;

  // DELETE /users/me - Eliminar mi perfil
  if (pathSegments.length === 1 && pathSegments[0] === "me") {
    return await handleDeleteMyProfile(request, user_id, supabaseClient);
  }

  // DELETE /users/{id} - Eliminar perfil por ID
  if (pathSegments.length === 1 && isValidUUID(pathSegments[0])) {
    return await handleDelete(request, user_id, pathSegments[0], supabaseClient);
  }

  return createErrorResponse("Invalid DELETE endpoint", 404);
}

/**
 * Valida si una string es un UUID válido
 */
function isValidUUID(uuid: string): boolean {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  return uuidRegex.test(uuid);
} 