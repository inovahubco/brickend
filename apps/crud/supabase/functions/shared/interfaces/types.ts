import { z } from "zod";
import {
  BaseEntitySchema,
  ItemSchema,
  CreateItemSchema,
  UpdateItemSchema,
  QueryParamsSchema,
  IdParamSchema,
  SuccessResponseSchema,
  ErrorResponseSchema,
  PaginatedResponseSchema,
} from "./schemas.ts";

// Infer types from schemas
export type BaseEntity = z.infer<typeof BaseEntitySchema>;
export type Item = z.infer<typeof ItemSchema>;
export type CreateItem = z.infer<typeof CreateItemSchema>;
export type UpdateItem = z.infer<typeof UpdateItemSchema>;
export type QueryParams = z.infer<typeof QueryParamsSchema>;
export type IdParam = z.infer<typeof IdParamSchema>;
export type SuccessResponse<T = any> = z.infer<typeof SuccessResponseSchema> & { data: T };
export type ErrorResponse = z.infer<typeof ErrorResponseSchema>;
export type PaginatedResponse<T = any> = z.infer<typeof PaginatedResponseSchema> & { data: T[] };

// Database table interface
export interface DatabaseItem extends BaseEntity {
  title: string;
  description?: string;
  status: "active" | "inactive" | "pending";
  priority: number;
  tags?: string[];
  metadata?: Record<string, any>;
}

// API Response types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
}

export interface PaginatedApiResponse<T = any> extends ApiResponse<T[]> {
  pagination: PaginationMeta;
}

// Request context
export interface RequestContext {
  user: {
    id: string;
    email?: string;
    [key: string]: any;
  };
  params: Record<string, string>;
  query: QueryParams;
} 