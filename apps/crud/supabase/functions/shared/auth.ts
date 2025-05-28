import { createClient } from "@supabase/supabase-js";

interface AuthResult {
  success: boolean;
  error?: string;
  user?: any;
}

export async function validateAuth(request: Request): Promise<AuthResult> {
  try {
    const authHeader = request.headers.get("Authorization");
    
    if (!authHeader) {
      return { success: false, error: "Missing authorization header" };
    }

    const token = authHeader.replace("Bearer ", "");
    
    if (!token) {
      return { success: false, error: "Invalid authorization format" };
    }

    // Get Supabase URL and anon key from environment
    const supabaseUrl = Deno.env.get("SUPABASE_URL");
    const supabaseAnonKey = Deno.env.get("SUPABASE_ANON_KEY");

    if (!supabaseUrl || !supabaseAnonKey) {
      return { success: false, error: "Missing Supabase configuration" };
    }

    // Create Supabase client
    const supabase = createClient(supabaseUrl, supabaseAnonKey, {
      global: {
        headers: { Authorization: authHeader },
      },
    });

    // Verify the token and get user
    const { data: { user }, error } = await supabase.auth.getUser(token);

    if (error || !user) {
      return { success: false, error: "Invalid or expired token" };
    }

    return { success: true, user };
  } catch (error) {
    console.error("Auth validation error:", error);
    return { success: false, error: "Authentication failed" };
  }
} 