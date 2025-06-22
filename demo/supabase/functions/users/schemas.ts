import { z } from "zod";

// Esquema base para user profile
export const UserProfileSchema = z.object({
  username: z.string()
    .min(3, "Username debe tener al menos 3 caracteres")
    .max(50, "Username no puede exceder 50 caracteres")
    .regex(/^[a-zA-Z0-9_-]+$/, "Username solo puede contener letras, números, guiones y underscores"),
  
  // Datos demográficos
  first_name: z.string().max(100).optional(),
  last_name: z.string().max(100).optional(),
  date_of_birth: z.string().date().optional(),
  gender: z.enum(["male", "female", "other", "prefer_not_to_say"]).optional(),
  phone: z.string().max(20).optional(),
  
  // Ubicación
  address_line1: z.string().max(255).optional(),
  address_line2: z.string().max(255).optional(),
  city: z.string().max(100).optional(),
  state: z.string().max(100).optional(),
  postal_code: z.string().max(20).optional(),
  country: z.string().max(100).optional(),
  
  // Preferencias
  preferences: z.record(z.any()).optional(),
  
  // Campos adicionales
  bio: z.string().max(500).optional(),
  avatar_url: z.string().url().max(500).optional(),
  website: z.string().url().max(500).optional(),
  occupation: z.string().max(100).optional(),
  
  // Configuración de privacidad
  is_profile_public: z.boolean().optional(),
});

// Esquema para crear usuario
export const CreateUserProfileSchema = UserProfileSchema;

// Esquema para actualizar usuario (todos los campos opcionales excepto username)
export const UpdateUserProfileSchema = UserProfileSchema.partial();

// Esquema para parámetros de consulta
export const QueryParamsSchema = z.object({
  page: z.string().transform(val => parseInt(val, 10)).pipe(z.number().min(1)).default("1"),
  limit: z.string().transform(val => parseInt(val, 10)).pipe(z.number().min(1).max(100)).default("10"),
  search: z.string().optional(),
  gender: z.enum(["male", "female", "other", "prefer_not_to_say"]).optional(),
  country: z.string().optional(),
  is_profile_public: z.string().transform(val => val === "true").optional(),
  sort_by: z.enum(["created_at", "updated_at", "username", "first_name", "last_name"]).default("created_at"),
  sort_order: z.enum(["asc", "desc"]).default("desc"),
});

// Esquema de respuesta base
export const UserProfileResponseSchema = z.object({
  id: z.string().uuid(),
  user_id: z.string().uuid(),
  username: z.string(),
  first_name: z.string().nullable(),
  last_name: z.string().nullable(),
  date_of_birth: z.string().nullable(),
  gender: z.string().nullable(),
  phone: z.string().nullable(),
  address_line1: z.string().nullable(),
  address_line2: z.string().nullable(),
  city: z.string().nullable(),
  state: z.string().nullable(),
  postal_code: z.string().nullable(),
  country: z.string().nullable(),
  preferences: z.record(z.any()),
  bio: z.string().nullable(),
  avatar_url: z.string().nullable(),
  website: z.string().nullable(),
  occupation: z.string().nullable(),
  is_profile_public: z.boolean(),
  is_deleted: z.boolean(),
  deleted_at: z.string().nullable(),
  created_at: z.string(),
  updated_at: z.string(),
});

// Esquema de respuesta paginada
export const PaginatedResponseSchema = z.object({
  data: z.array(UserProfileResponseSchema),
  pagination: z.object({
    page: z.number(),
    limit: z.number(),
    total: z.number(),
    total_pages: z.number(),
    has_next: z.boolean(),
    has_prev: z.boolean(),
  }),
});

// Tipos TypeScript derivados de los esquemas
export type UserProfile = z.infer<typeof UserProfileSchema>;
export type CreateUserProfile = z.infer<typeof CreateUserProfileSchema>;
export type UpdateUserProfile = z.infer<typeof UpdateUserProfileSchema>;
export type QueryParams = z.infer<typeof QueryParamsSchema>;
export type UserProfileResponse = z.infer<typeof UserProfileResponseSchema>;
export type PaginatedResponse = z.infer<typeof PaginatedResponseSchema>; 