import { serve } from "@std/http";
import { corsHeaders } from "../shared/cors.ts";
import { validateAuth } from "../shared/auth.ts";
import { createHandler } from "./create.ts";
import { readHandler } from "./read.ts";
import { updateHandler } from "./update.ts";
import { deleteHandler } from "./delete.ts";

interface RouteHandler {
  (request: Request, url: URL, user: any): Promise<Response>;
}

const routes: Record<string, RouteHandler> = {
  POST: createHandler,
  GET: readHandler,
  PUT: updateHandler,
  PATCH: updateHandler,
  DELETE: deleteHandler,
};

serve(async (request: Request) => {
  // Handle CORS preflight requests
  if (request.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const url = new URL(request.url);
    
    // Validate authorization
    const authResult = await validateAuth(request);
    if (!authResult.success) {
      return new Response(
        JSON.stringify({ error: authResult.error }),
        {
          status: 401,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    // Route to appropriate handler
    const handler = routes[request.method];
    if (!handler) {
      return new Response(
        JSON.stringify({ error: "Method not allowed" }),
        {
          status: 405,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    // Execute handler with user context
    const response = await handler(request, url, authResult.user);
    
    // Ensure CORS headers are included
    const headers = new Headers(response.headers);
    Object.entries(corsHeaders).forEach(([key, value]) => {
      headers.set(key, value);
    });

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers,
    });

  } catch (error) {
    console.error("Unhandled error:", error);
    return new Response(
      JSON.stringify({ error: "Internal server error" }),
      {
        status: 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      }
    );
  }
}); 