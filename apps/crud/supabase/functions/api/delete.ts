import { corsHeaders } from "../shared/cors.ts";
import { IdParamSchema } from "../shared/interfaces/schemas.ts";
import { DatabaseService } from "../shared/database.ts";
import type { ApiResponse } from "../shared/interfaces/types.ts";

export async function deleteHandler(request: Request, url: URL, user: any): Promise<Response> {
  try {
    // Extract ID from URL path
    const pathSegments = url.pathname.split('/').filter(Boolean);
    const lastSegment = pathSegments[pathSegments.length - 1];
    
    // Validate ID format
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

    const db = new DatabaseService();
    const userId = user.id;

    // Check if item exists first
    const existingItem = await db.findById(lastSegment, userId);
    if (!existingItem) {
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

    // Delete the item
    await db.delete(lastSegment, userId);

    const response: ApiResponse = {
      success: true,
      data: { id: lastSegment },
      message: "Item deleted successfully",
    };

    return new Response(JSON.stringify(response), {
      status: 200,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });

  } catch (error) {
    console.error("Delete handler error:", error);
    
    const response: ApiResponse = {
      success: false,
      error: error instanceof Error ? error.message : "Failed to delete item",
    };

    return new Response(JSON.stringify(response), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
} 