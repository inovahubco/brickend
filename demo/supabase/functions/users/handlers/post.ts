import { CreateUserProfileSchema, type CreateUserProfile } from "../schemas.ts";
import { createCorsResponse, createErrorResponse } from "../auth.ts";
import type { SupabaseClient } from "https://esm.sh/@supabase/supabase-js@2";

export async function handlePost(request: Request, user_id: string, supabase: SupabaseClient): Promise<Response> {
  try {
    // Parsear el body de la request
    const body = await request.json();
    
    // Validar datos con Zod
    const validationResult = CreateUserProfileSchema.safeParse(body);
    if (!validationResult.success) {
      return createErrorResponse(
        "Invalid input data",
        400,
        validationResult.error.issues
      );
    }

    const profileData: CreateUserProfile = validationResult.data;

    // Verificar si el usuario ya tiene un perfil
    const { data: existingProfile, error: checkError } = await supabase
      .from("user_profiles")
      .select("id")
      .eq("user_id", user_id)
      .eq("is_deleted", false)
      .single();

    if (checkError && checkError.code !== "PGRST116") {
      console.error("Error checking existing profile:", checkError);
      return createErrorResponse("Error checking existing profile", 500, checkError);
    }

    if (existingProfile) {
      return createErrorResponse("User profile already exists", 409);
    }

    // Verificar si el username ya está en uso
    const { data: existingUsername, error: usernameError } = await supabase
      .from("user_profiles")
      .select("id")
      .eq("username", profileData.username)
      .eq("is_deleted", false)
      .single();

    if (usernameError && usernameError.code !== "PGRST116") {
      console.error("Error checking username:", usernameError);
      return createErrorResponse("Error checking username availability", 500, usernameError);
    }

    if (existingUsername) {
      return createErrorResponse("Username already exists", 409);
    }

    // Crear el perfil
    const { data, error } = await supabase
      .from("user_profiles")
      .insert({
        user_id,
        ...profileData,
        // Establecer valores por defecto
        preferences: profileData.preferences || {},
        is_profile_public: profileData.is_profile_public ?? false,
        country: profileData.country || 'Colombia'
      })
      .select()
      .single();

    if (error) {
      console.error("Error creating profile:", error);
      return createErrorResponse("Error creating user profile", 500, error);
    }

    return createCorsResponse({
      message: "User profile created successfully",
      data
    }, 201);

  } catch (error) {
    console.error("Unexpected error in handlePost:", error);
    return createErrorResponse("Internal server error", 500);
  }
} 