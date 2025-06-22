import { createCorsResponse, createErrorResponse } from "../auth.ts";
import type { SupabaseClient } from "https://esm.sh/@supabase/supabase-js@2";

export async function handleDelete(request: Request, user_id: string, profile_id: string | undefined, supabase: SupabaseClient): Promise<Response> {
  try {

    // Determinar qué perfil eliminar
    let query = supabase
      .from("user_profiles")
      .update({ 
        is_deleted: true,
        deleted_at: new Date().toISOString()
      })
      .eq("is_deleted", false);

    if (profile_id) {
      // Eliminar perfil específico (verificar que sea del usuario autenticado)
      query = query.eq("id", profile_id).eq("user_id", user_id);
    } else {
      // Eliminar mi perfil
      query = query.eq("user_id", user_id);
    }

    // Ejecutar soft delete
    const { data, error } = await query.select().single();

    if (error) {
      if (error.code === "PGRST116") {
        return createErrorResponse("User profile not found", 404);
      }
      console.error("Error deleting profile:", error);
      return createErrorResponse("Error deleting user profile", 500, error);
    }

    return createCorsResponse({
      message: "User profile deleted successfully",
      data
    });

  } catch (error) {
    console.error("Unexpected error in handleDelete:", error);
    return createErrorResponse("Internal server error", 500);
  }
}

export async function handleDeleteMyProfile(request: Request, user_id: string, supabase: SupabaseClient): Promise<Response> {
  return handleDelete(request, user_id, undefined, supabase);
}

/**
 * Función auxiliar para restaurar un perfil eliminado (soft delete reverso)
 */
export async function handleRestore(request: Request, user_id: string, profile_id: string | undefined, supabase: SupabaseClient): Promise<Response> {
  try {

    // Determinar qué perfil restaurar
    let query = supabase
      .from("user_profiles")
      .update({ 
        is_deleted: false,
        deleted_at: null
      })
      .eq("is_deleted", true);

    if (profile_id) {
      // Restaurar perfil específico (verificar que sea del usuario autenticado)
      query = query.eq("id", profile_id).eq("user_id", user_id);
    } else {
      // Restaurar mi perfil
      query = query.eq("user_id", user_id);
    }

    // Ejecutar restauración
    const { data, error } = await query.select().single();

    if (error) {
      if (error.code === "PGRST116") {
        return createErrorResponse("Deleted user profile not found", 404);
      }
      console.error("Error restoring profile:", error);
      return createErrorResponse("Error restoring user profile", 500, error);
    }

    return createCorsResponse({
      message: "User profile restored successfully",
      data
    });

  } catch (error) {
    console.error("Unexpected error in handleRestore:", error);
    return createErrorResponse("Internal server error", 500);
  }
} 