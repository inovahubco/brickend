/**
 * Supabase Edge Functions Utilities
 * 
 * CRUD generation and function utilities
 */

import { CRUDGenerator } from './crud-generator.js';

export { CRUDGenerator } from './crud-generator.js';

// Convenience functions
export async function generateCRUDFunction(
    config: import('../types/index.js').SupabaseConfig,
    schema: import('../types/index.js').DatabaseSchema,
    entity: import('@brickend/core').Entity,
    options: {
        includeAuth?: boolean;
        includeValidation?: boolean;
        includeErrorHandling?: boolean;
        includeCors?: boolean;
        includeLogging?: boolean;
        includePagination?: boolean;
        includeFiltering?: boolean;
        includeSorting?: boolean;
        typescript?: boolean;
    } = {}
): Promise<Array<{
    filename: string;
    content: string;
    method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
    endpoint: string;
    description: string;
}>> {
    const generator = new CRUDGenerator(config, schema);
    return generator.generateCRUDFunction(entity, options);
}

export async function generateValidationSchemas(
    entity: import('@brickend/core').Entity
): Promise<string> {
    const generator = new CRUDGenerator({} as any, { entities: [] } as any);
    return generator.generateValidationSchemas(entity);
}

export async function generateErrorHandlers(): Promise<string> {
    const generator = new CRUDGenerator({} as any, { entities: [] } as any);
    return generator.generateErrorHandlers();
}

export async function generateMiddleware(): Promise<string> {
    const generator = new CRUDGenerator({} as any, { entities: [] } as any);
    return generator.generateMiddleware();
}
