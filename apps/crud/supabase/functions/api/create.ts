import { corsHeaders } from "../shared/cors.ts";
import { CreateItemSchema } from "../shared/interfaces/schemas.ts";
import { DatabaseService } from "../shared/database.ts";
import type { ApiResponse, CreateItem } from "../shared/interfaces/types.ts";

export async function createHandler(request: Request, url: URL, user: any): Promise<Response> {
  try {
    // Parse request body
    const body = await request.json();
    
    // Validate input data
    const validationResult = CreateItemSchema.safeParse(body);
    if (!validationResult.success) {
      return new Response(
        JSON.stringify({
          success: false,
          error: "Validation failed",
          details: validationResult.error.errors,
        }),
        {
          status: 400,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    const db = new DatabaseService();
    const userId = user.id;
    
    const createdItem = await db.create(validationResult.data, userId);

    const response: ApiResponse = {
      success: true,
      data: createdItem,
      message: "Item created successfully",
    };

    return new Response(JSON.stringify(response), {
      status: 201,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });

  } catch (error) {
    console.error("Create handler error:", error);
    
    const response: ApiResponse = {
      success: false,
      error: error instanceof Error ? error.message : "Failed to create item",
    };

    return new Response(JSON.stringify(response), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
} 