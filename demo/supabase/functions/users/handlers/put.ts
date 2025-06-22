import { UpdateUserProfileSchema, type UpdateUserProfile } from "../schemas.ts";
import { createCorsResponse, createErrorResponse } from "../auth.ts";
import type { SupabaseClient } from "https://esm.sh/@supabase/supabase-js@2";

export async function handlePut(request: Request, user_id: string, profile_id: string | undefined, supabase: SupabaseClient): Promise<Response> {
  try {
    // Parsear el body de la request
    const body = await request.json();
    
    // Validar datos con Zod
    const validationResult = UpdateUserProfileSchema.safeParse(body);
    if (!validationResult.success) {
      return createErrorResponse(
        "Invalid input data",
        400,
        validationResult.error.issues
      );
    }

    const updateData: UpdateUserProfile = validationResult.data;

    // Determinar qué perfil actualizar
    let query = supabase
      .from("user_profiles")
      .update(updateData)
      .eq("is_deleted", false);

    if (profile_id) {
      // Actualizar perfil específico (verificar que sea del usuario autenticado)
      query = query.eq("id", profile_id).eq("user_id", user_id);
    } else {
      // Actualizar mi perfil
      query = query.eq("user_id", user_id);
    }

    // Si se está actualizando el username, verificar que no esté en uso
    if (updateData.username) {
      const { data: existingUsername, error: usernameError } = await supabase
        .from("user_profiles")
        .select("id, user_id")
        .eq("username", updateData.username)
        .eq("is_deleted", false)
        .single();

      if (usernameError && usernameError.code !== "PGRST116") {
        console.error("Error checking username:", usernameError);
        return createErrorResponse("Error checking username availability", 500, usernameError);
      }

      if (existingUsername && existingUsername.user_id !== user_id) {
        return createErrorResponse("Username already exists", 409);
      }
    }

    // Ejecutar la actualización
    const { data, error } = await query.select().single();

    if (error) {
      if (error.code === "PGRST116") {
        return createErrorResponse("User profile not found", 404);
      }
      console.error("Error updating profile:", error);
      return createErrorResponse("Error updating user profile", 500, error);
    }

    return createCorsResponse({
      message: "User profile updated successfully",
      data
    });

  } catch (error) {
    console.error("Unexpected error in handlePut:", error);
    return createErrorResponse("Internal server error", 500);
  }
}

export async function handlePutMyProfile(request: Request, user_id: string, supabase: SupabaseClient): Promise<Response> {
  return handlePut(request, user_id, undefined, supabase);
} 