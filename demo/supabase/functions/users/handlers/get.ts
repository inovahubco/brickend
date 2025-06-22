import { QueryParamsSchema, type QueryParams, type PaginatedResponse } from "../schemas.ts";
import { createCorsResponse, createErrorResponse } from "../auth.ts";
import type { SupabaseClient } from "https://esm.sh/@supabase/supabase-js@2";

export async function handleGet(request: Request, user_id: string, supabase: SupabaseClient): Promise<Response> {
  try {
    const url = new URL(request.url);
    const searchParams = Object.fromEntries(url.searchParams.entries());
    
    // Validar parámetros de consulta
    const queryResult = QueryParamsSchema.safeParse(searchParams);
    if (!queryResult.success) {
      return createErrorResponse(
        "Invalid query parameters",
        400,
        queryResult.error.issues
      );
    }

    const params: QueryParams = queryResult.data;

    // Construir query base
    let query = supabase
      .from("user_profiles")
      .select("*", { count: "exact" })
      .eq("is_deleted", false);

    // Aplicar filtros
    if (params.search) {
      query = query.or(`username.ilike.%${params.search}%,first_name.ilike.%${params.search}%,last_name.ilike.%${params.search}%`);
    }

    if (params.gender) {
      query = query.eq("gender", params.gender);
    }

    if (params.country) {
      query = query.eq("country", params.country);
    }

    if (params.is_profile_public !== undefined) {
      query = query.eq("is_profile_public", params.is_profile_public);
    }

    // Aplicar ordenamiento
    query = query.order(params.sort_by, { ascending: params.sort_order === "asc" });

    // Aplicar paginación
    const offset = (params.page - 1) * params.limit;
    query = query.range(offset, offset + params.limit - 1);

    // Ejecutar query
    const { data, error, count } = await query;

    if (error) {
      console.error("Database error:", error);
      return createErrorResponse("Error fetching user profiles", 500, error);
    }

    // Calcular metadata de paginación
    const total = count || 0;
    const total_pages = Math.ceil(total / params.limit);
    const has_next = params.page < total_pages;
    const has_prev = params.page > 1;

    const response: PaginatedResponse = {
      data: data || [],
      pagination: {
        page: params.page,
        limit: params.limit,
        total,
        total_pages,
        has_next,
        has_prev,
      },
    };

    return createCorsResponse(response);

  } catch (error) {
    console.error("Unexpected error in handleGet:", error);
    return createErrorResponse("Internal server error", 500);
  }
}

export async function handleGetById(request: Request, user_id: string, profile_id: string, supabase: SupabaseClient): Promise<Response> {
  try {

    const { data, error } = await supabase
      .from("user_profiles")
      .select("*")
      .eq("id", profile_id)
      .eq("is_deleted", false)
      .single();

    if (error) {
      if (error.code === "PGRST116") {
        return createErrorResponse("User profile not found", 404);
      }
      console.error("Database error:", error);
      return createErrorResponse("Error fetching user profile", 500, error);
    }

    return createCorsResponse({ data });

  } catch (error) {
    console.error("Unexpected error in handleGetById:", error);
    return createErrorResponse("Internal server error", 500);
  }
}

export async function handleGetMyProfile(request: Request, user_id: string, supabase: SupabaseClient): Promise<Response> {
  try {

    const { data, error } = await supabase
      .from("user_profiles")
      .select("*")
      .eq("user_id", user_id)
      .eq("is_deleted", false)
      .single();

    if (error) {
      if (error.code === "PGRST116") {
        return createErrorResponse("User profile not found", 404);
      }
      console.error("Database error:", error);
      return createErrorResponse("Error fetching user profile", 500, error);
    }

    return createCorsResponse({ data });

  } catch (error) {
    console.error("Unexpected error in handleGetMyProfile:", error);
    return createErrorResponse("Internal server error", 500);
  }
} 