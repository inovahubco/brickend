import { corsHeaders } from "../shared/cors.ts";
import { QueryParamsSchema, IdParamSchema } from "../shared/interfaces/schemas.ts";
import { DatabaseService } from "../shared/database.ts";
import type { ApiResponse, PaginatedApiResponse } from "../shared/interfaces/types.ts";

export async function readHandler(request: Request, url: URL, user: any): Promise<Response> {
  try {
    const db = new DatabaseService();
    const userId = user.id;

    // Check if this is a single item request (has ID in path)
    const pathSegments = url.pathname.split('/').filter(Boolean);
    const lastSegment = pathSegments[pathSegments.length - 1];
    
    // If last segment looks like a UUID, treat as single item request
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    
    if (uuidRegex.test(lastSegment)) {
      // Single item request
      const idValidation = IdParamSchema.safeParse({ id: lastSegment });
      if (!idValidation.success) {
        return new Response(
          JSON.stringify({
            success: false,
            error: "Invalid ID format",
            details: idValidation.error.errors,
          }),
          {
            status: 400,
            headers: { ...corsHeaders, "Content-Type": "application/json" },
          }
        );
      }

      const item = await db.findById(lastSegment, userId);
      
      if (!item) {
        return new Response(
          JSON.stringify({
            success: false,
            error: "Item not found",
          }),
          {
            status: 404,
            headers: { ...corsHeaders, "Content-Type": "application/json" },
          }
        );
      }

      const response: ApiResponse = {
        success: true,
        data: item,
      };

      return new Response(JSON.stringify(response), {
        status: 200,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    // Multiple items request with query parameters
    const queryParams = Object.fromEntries(url.searchParams.entries());
    const validationResult = QueryParamsSchema.safeParse(queryParams);
    
    if (!validationResult.success) {
      return new Response(
        JSON.stringify({
          success: false,
          error: "Invalid query parameters",
          details: validationResult.error.errors,
        }),
        {
          status: 400,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    const { items, pagination } = await db.findMany(userId, validationResult.data);

    const response: PaginatedApiResponse = {
      success: true,
      data: items,
      pagination,
    };

    return new Response(JSON.stringify(response), {
      status: 200,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });

  } catch (error) {
    console.error("Read handler error:", error);
    
    const response: ApiResponse = {
      success: false,
      error: error instanceof Error ? error.message : "Failed to fetch items",
    };

    return new Response(JSON.stringify(response), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
} 