import { z } from "zod";

// Base entity schema
export const BaseEntitySchema = z.object({
  id: z.string().uuid().optional(),
  created_at: z.string().datetime().optional(),
  updated_at: z.string().datetime().optional(),
  user_id: z.string().uuid().optional(),
});

// Example entity schema - customize based on your needs
export const ItemSchema = BaseEntitySchema.extend({
  title: z.string().min(1).max(255),
  description: z.string().optional(),
  status: z.enum(["active", "inactive", "pending"]).default("active"),
  priority: z.number().int().min(1).max(5).default(1),
  tags: z.array(z.string()).optional(),
  metadata: z.record(z.any()).optional(),
});

// Create schemas (without id, timestamps)
export const CreateItemSchema = ItemSchema.omit({
  id: true,
  created_at: true,
  updated_at: true,
  user_id: true,
});

// Update schemas (partial, without timestamps)
export const UpdateItemSchema = ItemSchema.omit({
  id: true,
  created_at: true,
  updated_at: true,
  user_id: true,
}).partial();

// Query parameters schema
export const QueryParamsSchema = z.object({
  page: z.string().transform(Number).pipe(z.number().int().min(1)).optional(),
  limit: z.string().transform(Number).pipe(z.number().int().min(1).max(100)).optional(),
  sort: z.string().optional(),
  order: z.enum(["asc", "desc"]).optional(),
  search: z.string().optional(),
  status: z.enum(["active", "inactive", "pending"]).optional(),
});

// ID parameter schema
export const IdParamSchema = z.object({
  id: z.string().uuid(),
});

// Response schemas
export const SuccessResponseSchema = z.object({
  success: z.boolean(),
  data: z.any(),
  message: z.string().optional(),
});

export const ErrorResponseSchema = z.object({
  success: z.boolean().default(false),
  error: z.string(),
  details: z.any().optional(),
});

export const PaginatedResponseSchema = z.object({
  success: z.boolean(),
  data: z.array(z.any()),
  pagination: z.object({
    page: z.number(),
    limit: z.number(),
    total: z.number(),
    totalPages: z.number(),
  }),
}); 