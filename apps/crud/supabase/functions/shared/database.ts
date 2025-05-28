import { createClient } from "@supabase/supabase-js";
import type { DatabaseItem, QueryParams, PaginationMeta } from "./interfaces/types.ts";

export function createSupabaseClient() {
  const supabaseUrl = Deno.env.get("SUPABASE_URL");
  const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");

  if (!supabaseUrl || !supabaseServiceKey) {
    throw new Error("Missing Supabase configuration");
  }

  return createClient(supabaseUrl, supabaseServiceKey);
}

export class DatabaseService {
  private supabase;
  private tableName = "items";

  constructor() {
    this.supabase = createSupabaseClient();
  }

  async create(data: Omit<DatabaseItem, "id" | "created_at" | "updated_at">, userId: string): Promise<DatabaseItem> {
    const { data: result, error } = await this.supabase
      .from(this.tableName)
      .insert({ ...data, user_id: userId })
      .select()
      .single();

    if (error) {
      throw new Error(`Failed to create item: ${error.message}`);
    }

    return result;
  }

  async findById(id: string, userId: string): Promise<DatabaseItem | null> {
    const { data, error } = await this.supabase
      .from(this.tableName)
      .select("*")
      .eq("id", id)
      .eq("user_id", userId)
      .single();

    if (error) {
      if (error.code === "PGRST116") {
        return null; // Not found
      }
      throw new Error(`Failed to find item: ${error.message}`);
    }

    return data;
  }

  async findMany(
    userId: string,
    params: QueryParams = {}
  ): Promise<{ items: DatabaseItem[]; pagination: PaginationMeta }> {
    const {
      page = 1,
      limit = 10,
      sort = "created_at",
      order = "desc",
      search,
      status,
    } = params;

    let query = this.supabase
      .from(this.tableName)
      .select("*", { count: "exact" })
      .eq("user_id", userId);

    // Apply filters
    if (status) {
      query = query.eq("status", status);
    }

    if (search) {
      query = query.or(`title.ilike.%${search}%,description.ilike.%${search}%`);
    }

    // Apply sorting
    query = query.order(sort, { ascending: order === "asc" });

    // Apply pagination
    const from = (page - 1) * limit;
    const to = from + limit - 1;
    query = query.range(from, to);

    const { data, error, count } = await query;

    if (error) {
      throw new Error(`Failed to fetch items: ${error.message}`);
    }

    const total = count || 0;
    const totalPages = Math.ceil(total / limit);

    return {
      items: data || [],
      pagination: {
        page,
        limit,
        total,
        totalPages,
      },
    };
  }

  async update(id: string, data: Partial<DatabaseItem>, userId: string): Promise<DatabaseItem> {
    const { data: result, error } = await this.supabase
      .from(this.tableName)
      .update({ ...data, updated_at: new Date().toISOString() })
      .eq("id", id)
      .eq("user_id", userId)
      .select()
      .single();

    if (error) {
      throw new Error(`Failed to update item: ${error.message}`);
    }

    return result;
  }

  async delete(id: string, userId: string): Promise<boolean> {
    const { error } = await this.supabase
      .from(this.tableName)
      .delete()
      .eq("id", id)
      .eq("user_id", userId);

    if (error) {
      throw new Error(`Failed to delete item: ${error.message}`);
    }

    return true;
  }
} 