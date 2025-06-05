/**
 * Supabase Database Utilities
 * 
 * Schema generation, migrations, and database utilities
 */

import { SchemaGenerator } from './schema-generator.js';

export { SchemaGenerator };

// Convenience functions
export async function generateMigration(
    schema: import('../types/index.js').DatabaseSchema
): Promise<import('../types/index.js').GeneratedMigration> {
    const generator = new SchemaGenerator(schema);
    return generator.generateMigration();
}

export async function generateTypes(
    schema: import('../types/index.js').DatabaseSchema
): Promise<string> {
    const generator = new SchemaGenerator(schema);
    return generator.generateTypes();
}

export async function generateRLS(
    schema: import('../types/index.js').DatabaseSchema
): Promise<string> {
    const generator = new SchemaGenerator(schema);
    return generator.generateRLS();
}

export async function generateIndexes(
    schema: import('../types/index.js').DatabaseSchema
): Promise<string> {
    const generator = new SchemaGenerator(schema);
    return generator.generateIndexes();
}
