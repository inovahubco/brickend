/**
 * Schema Generator for Supabase
 * 
 * Generates SQL migrations, TypeScript types, RLS policies, and indexes
 * from Brickend entity definitions
 */

import pluralize from 'pluralize';
import type {
    Entity,
    Field
} from '@brickend/core';
import type {
    DatabaseSchema,
    SQLDataType,
    FieldToSQLMapping,
    GeneratedMigration
} from '../types/index.js';

/**
 * Schema Generator - Converts Brickend entities to Supabase SQL
 */
export class SchemaGenerator {
    private readonly schema: DatabaseSchema;

    constructor(schema: DatabaseSchema) {
        this.schema = schema;
    }

    /**
     * Generate complete SQL migration from entities
     */
    async generateMigration(): Promise<GeneratedMigration> {
        const timestamp = this.generateTimestamp();
        const version = this.schema.version || timestamp;

        const sqlParts: string[] = [];

        // Add header comment
        sqlParts.push(this.generateMigrationHeader(version));

        // Add before script if provided
        if (this.schema.beforeScript) {
            sqlParts.push('-- Custom before script');
            sqlParts.push(this.schema.beforeScript);
            sqlParts.push('');
        }

        // Generate tables
        for (const entity of this.schema.entities) {
            sqlParts.push(this.generateTableSQL(entity));
            sqlParts.push('');
        }

        // Generate relationships (foreign keys)
        for (const entity of this.schema.entities) {
            const relationshipSQL = this.generateRelationshipsSQL(entity);
            if (relationshipSQL) {
                sqlParts.push(relationshipSQL);
                sqlParts.push('');
            }
        }

        // Generate indexes
        const indexesSQL = this.generateAllIndexes();
        if (indexesSQL) {
            sqlParts.push('-- Indexes');
            sqlParts.push(indexesSQL);
            sqlParts.push('');
        }

        // Generate RLS policies if enabled
        if (this.schema.settings?.enableRLS) {
            const rlsSQL = this.generateAllRLS();
            if (rlsSQL) {
                sqlParts.push('-- Row Level Security');
                sqlParts.push(rlsSQL);
                sqlParts.push('');
            }
        }

        // Generate triggers for timestamps and soft delete
        const triggersSQL = this.generateAllTriggers();
        if (triggersSQL) {
            sqlParts.push('-- Triggers');
            sqlParts.push(triggersSQL);
            sqlParts.push('');
        }

        // Add after script if provided
        if (this.schema.afterScript) {
            sqlParts.push('-- Custom after script');
            sqlParts.push(this.schema.afterScript);
            sqlParts.push('');
        }

        const content = sqlParts.join('\n');

        return {
            filename: `${timestamp}_initial_schema.sql`,
            content,
            version,
            description: this.schema.description || 'Initial schema migration',
            dependencies: []
        };
    }

    /**
     * Generate TypeScript types from schema
     */
    async generateTypes(): Promise<string> {
        const typeParts: string[] = [];

        // Add header
        typeParts.push('/**');
        typeParts.push(' * Generated TypeScript types for Supabase schema');
        typeParts.push(' * DO NOT EDIT - This file is auto-generated');
        typeParts.push(' */');
        typeParts.push('');

        // Generate database interface
        typeParts.push('export interface Database {');
        typeParts.push('  public: {');
        typeParts.push('    Tables: {');

        for (const entity of this.schema.entities) {
            typeParts.push(this.generateEntityTypeScript(entity));
        }

        typeParts.push('    };');
        typeParts.push('    Views: {');
        typeParts.push('      [_ in never]: never;');
        typeParts.push('    };');
        typeParts.push('    Functions: {');
        typeParts.push('      [_ in never]: never;');
        typeParts.push('    };');
        typeParts.push('    Enums: {');
        typeParts.push('      [_ in never]: never;');
        typeParts.push('    };');
        typeParts.push('  };');
        typeParts.push('}');
        typeParts.push('');

        // Generate individual entity types for convenience
        for (const entity of this.schema.entities) {
            const tableName = this.getTableName(entity);
            typeParts.push(`export type ${entity.name} = Database['public']['Tables']['${tableName}']['Row'];`);
            typeParts.push(`export type ${entity.name}Insert = Database['public']['Tables']['${tableName}']['Insert'];`);
            typeParts.push(`export type ${entity.name}Update = Database['public']['Tables']['${tableName}']['Update'];`);
            typeParts.push('');
        }

        return typeParts.join('\n');
    }

    /**
     * Generate RLS policies for all entities
     */
    async generateRLS(): Promise<string> {
        const policies: string[] = [];

        policies.push('-- Row Level Security Policies');
        policies.push('');

        for (const entity of this.schema.entities) {
            if (entity.options?.rowLevelSecurity !== false) {
                policies.push(this.generateEntityRLS(entity));
                policies.push('');
            }
        }

        return policies.join('\n');
    }

    /**
     * Generate indexes for all entities
     */
    async generateIndexes(): Promise<string> {
        const indexes: string[] = [];

        indexes.push('-- Database Indexes');
        indexes.push('');

        for (const entity of this.schema.entities) {
            indexes.push(this.generateEntityIndexes(entity));
            indexes.push('');
        }

        return indexes.join('\n');
    }

    /**
     * Generate SQL for a single table
     */
    private generateTableSQL(entity: Entity): string {
        const tableName = this.getTableName(entity);
        const sql: string[] = [];

        sql.push(`-- Table: ${tableName}`);
        sql.push(`CREATE TABLE ${tableName} (`);

        const columns: string[] = [];

        // Add ID column if not explicitly defined
        const hasIdField = entity.fields.some(f => f.name === 'id' || f.options?.primaryKey);
        if (!hasIdField) {
            columns.push('  id UUID DEFAULT gen_random_uuid() PRIMARY KEY');
        }

        // Add entity fields
        for (const field of entity.fields) {
            columns.push(this.generateColumnSQL(field));
        }

        // Add timestamp columns if enabled
        if (entity.options?.timestamps !== false && this.schema.settings?.timestampsEnabled !== false) {
            columns.push('  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL');
            columns.push('  updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL');
        }

        // Add soft delete column if enabled
        if (entity.options?.softDelete && this.schema.settings?.softDeleteEnabled !== false) {
            columns.push('  deleted_at TIMESTAMPTZ DEFAULT NULL');
        }

        sql.push(columns.join(',\n'));
        sql.push(');');

        // Enable RLS if configured
        if (entity.options?.rowLevelSecurity !== false && this.schema.settings?.enableRLS) {
            sql.push('');
            sql.push(`ALTER TABLE ${tableName} ENABLE ROW LEVEL SECURITY;`);
        }

        // Enable realtime if configured
        if (this.schema.settings?.enableRealtimeByDefault) {
            sql.push('');
            sql.push(`ALTER PUBLICATION supabase_realtime ADD TABLE ${tableName};`);
        }

        return sql.join('\n');
    }

    /**
     * Generate SQL for a single column
     */
    private generateColumnSQL(field: Field): string {
        const mapping = this.mapFieldToSQL(field);
        const parts: string[] = [];

        parts.push(`  ${field.name}`);
        parts.push(mapping.sqlType.toUpperCase());

        // Add constraints
        for (const constraint of mapping.constraints) {
            parts.push(constraint);
        }

        // Add default value
        if (mapping.defaultValue) {
            parts.push(`DEFAULT ${mapping.defaultValue}`);
        }

        // Add NOT NULL if required
        if (field.validation?.required && !field.options?.nullable) {
            parts.push('NOT NULL');
        }

        return parts.join(' ');
    }

    /**
     * Map Brickend field to SQL type and constraints
     */
    private mapFieldToSQL(field: Field): FieldToSQLMapping {
        const constraints: string[] = [];
        let sqlType: SQLDataType;
        let defaultValue: string | undefined;

        // Map field type to SQL type
        switch (field.type) {
            case 'string':
                if (field.validation?.maxLength && field.validation.maxLength <= 255) {
                    sqlType = 'varchar';
                    constraints.push(`(${field.validation.maxLength})`);
                } else {
                    sqlType = 'text';
                }
                break;

            case 'text':
                sqlType = 'text';
                break;

            case 'number':
            case 'integer':
                sqlType = 'integer';
                break;

            case 'float':
                sqlType = 'real';
                break;

            case 'decimal':
                sqlType = 'decimal';
                break;

            case 'boolean':
                sqlType = 'boolean';
                break;

            case 'date':
                sqlType = 'date';
                break;

            case 'datetime':
                sqlType = 'timestamptz';
                break;

            case 'email':
                sqlType = 'varchar';
                constraints.push('(320)'); // RFC 5321 email length limit
                break;

            case 'url':
                sqlType = 'text';
                break;

            case 'uuid':
                sqlType = 'uuid';
                if (field.options?.primaryKey) {
                    defaultValue = 'gen_random_uuid()';
                }
                break;

            case 'json':
                sqlType = 'jsonb';
                break;

            default:
                sqlType = 'text';
        }

        // Add primary key constraint
        if (field.options?.primaryKey) {
            constraints.push('PRIMARY KEY');
        }

        // Add unique constraint
        if (field.validation?.unique) {
            constraints.push('UNIQUE');
        }

        // Handle default values
        if (field.options?.defaultValue !== undefined) {
            if (typeof field.options.defaultValue === 'string') {
                defaultValue = `'${field.options.defaultValue}'`;
            } else {
                defaultValue = String(field.options.defaultValue);
            }
        }

        return {
            field,
            sqlType,
            constraints,
            defaultValue
        };
    }

    /**
     * Generate foreign key constraints for entity relationships
     */
    private generateRelationshipsSQL(entity: Entity): string | null {
        if (!entity.relationships) return null;

        const tableName = this.getTableName(entity);
        const sql: string[] = [];

        sql.push(`-- Foreign keys for ${tableName}`);

        for (const [relationName, relationship] of Object.entries(entity.relationships)) {
            const targetTable = this.getTableNameForEntity(relationship.target);
            const foreignKey = relationship.foreignKey || `${relationship.target.toLowerCase()}_id`;

            sql.push(
                `ALTER TABLE ${tableName} ADD CONSTRAINT fk_${tableName}_${relationName} ` +
                `FOREIGN KEY (${foreignKey}) REFERENCES ${targetTable}(id)` +
                `${relationship.onDelete ? ` ON DELETE ${relationship.onDelete}` : ''}` +
                `${relationship.onUpdate ? ` ON UPDATE ${relationship.onUpdate}` : ''};`
            );
        }

        return sql.length > 1 ? sql.join('\n') : null;
    }

    /**
     * Generate RLS policies for an entity
     */
    private generateEntityRLS(entity: Entity): string {
        const tableName = this.getTableName(entity);
        const sql: string[] = [];

        sql.push(`-- RLS Policies for ${tableName}`);

        // Default policies - these can be customized based on entity configuration
        const policies = [
            {
                name: `${tableName}_select_policy`,
                operation: 'SELECT',
                condition: 'true' // Allow all reads by default
            },
            {
                name: `${tableName}_insert_policy`,
                operation: 'INSERT',
                condition: 'auth.uid() IS NOT NULL' // Require authentication
            },
            {
                name: `${tableName}_update_policy`,
                operation: 'UPDATE',
                condition: 'auth.uid() IS NOT NULL' // Require authentication
            },
            {
                name: `${tableName}_delete_policy`,
                operation: 'DELETE',
                condition: 'auth.uid() IS NOT NULL' // Require authentication
            }
        ];

        for (const policy of policies) {
            sql.push(
                `CREATE POLICY ${policy.name} ON ${tableName} ` +
                `FOR ${policy.operation} USING (${policy.condition});`
            );
        }

        return sql.join('\n');
    }

    /**
     * Generate indexes for an entity
     */
    private generateEntityIndexes(entity: Entity): string {
        const tableName = this.getTableName(entity);
        const sql: string[] = [];

        sql.push(`-- Indexes for ${tableName}`);

        // Create indexes for foreign keys
        if (entity.relationships) {
            for (const [relationName, relationship] of Object.entries(entity.relationships)) {
                const foreignKey = relationship.foreignKey || `${relationship.target.toLowerCase()}_id`;
                sql.push(
                    `CREATE INDEX idx_${tableName}_${foreignKey} ON ${tableName}(${foreignKey});`
                );
            }
        }

        // Create indexes for unique fields
        for (const field of entity.fields) {
            if (field.validation?.unique && !field.options?.primaryKey) {
                sql.push(
                    `CREATE UNIQUE INDEX idx_${tableName}_${field.name}_unique ON ${tableName}(${field.name});`
                );
            }
        }

        // Create index for timestamps if enabled
        if (entity.options?.timestamps !== false) {
            sql.push(
                `CREATE INDEX idx_${tableName}_created_at ON ${tableName}(created_at);`
            );
        }

        // Create index for soft delete if enabled
        if (entity.options?.softDelete) {
            sql.push(
                `CREATE INDEX idx_${tableName}_deleted_at ON ${tableName}(deleted_at) WHERE deleted_at IS NULL;`
            );
        }

        return sql.join('\n');
    }

    /**
     * Generate TypeScript interface for an entity
     */
    private generateEntityTypeScript(entity: Entity): string {
        const tableName = this.getTableName(entity);
        const sql: string[] = [];

        sql.push(`      ${tableName}: {`);
        sql.push('        Row: {');

        // Add ID field if not explicitly defined
        const hasIdField = entity.fields.some(f => f.name === 'id');
        if (!hasIdField) {
            sql.push('          id: string;');
        }

        // Add entity fields
        for (const field of entity.fields) {
            const tsType = this.mapFieldToTypeScript(field);
            const optional = !field.validation?.required || field.options?.nullable ? '?' : '';
            sql.push(`          ${field.name}${optional}: ${tsType};`);
        }

        // Add timestamp fields
        if (entity.options?.timestamps !== false) {
            sql.push('          created_at: string;');
            sql.push('          updated_at: string;');
        }

        // Add soft delete field
        if (entity.options?.softDelete) {
            sql.push('          deleted_at?: string | null;');
        }

        sql.push('        };');
        sql.push('        Insert: {');

        // Insert type (most fields optional except required ones)
        if (!hasIdField) {
            sql.push('          id?: string;');
        }

        for (const field of entity.fields) {
            const tsType = this.mapFieldToTypeScript(field);
            const optional = !field.validation?.required || field.options?.defaultValue !== undefined ? '?' : '';
            sql.push(`          ${field.name}${optional}: ${tsType};`);
        }

        if (entity.options?.timestamps !== false) {
            sql.push('          created_at?: string;');
            sql.push('          updated_at?: string;');
        }

        if (entity.options?.softDelete) {
            sql.push('          deleted_at?: string | null;');
        }

        sql.push('        };');
        sql.push('        Update: {');

        // Update type (all fields optional)
        if (!hasIdField) {
            sql.push('          id?: string;');
        }

        for (const field of entity.fields) {
            const tsType = this.mapFieldToTypeScript(field);
            sql.push(`          ${field.name}?: ${tsType};`);
        }

        if (entity.options?.timestamps !== false) {
            sql.push('          created_at?: string;');
            sql.push('          updated_at?: string;');
        }

        if (entity.options?.softDelete) {
            sql.push('          deleted_at?: string | null;');
        }

        sql.push('        };');
        sql.push('      };');

        return sql.join('\n');
    }

    /**
     * Map Brickend field type to TypeScript type
     */
    private mapFieldToTypeScript(field: Field): string {
        switch (field.type) {
            case 'string':
            case 'text':
            case 'email':
            case 'url':
            case 'uuid':
                return 'string';

            case 'number':
            case 'integer':
            case 'float':
            case 'decimal':
                return 'number';

            case 'boolean':
                return 'boolean';

            case 'date':
            case 'datetime':
                return 'string'; // ISO date string

            case 'json':
                return 'any'; // Could be more specific based on schema

            default:
                return 'string';
        }
    }

    /**
     * Get table name for entity (pluralized by default)
     */
    private getTableName(entity: Entity): string {
        return entity.options?.tableName || pluralize(entity.name.toLowerCase());
    }

    /**
     * Get table name for entity by name
     */
    private getTableNameForEntity(entityName: string): string {
        const entity = this.schema.entities.find(e => e.name === entityName);
        if (!entity) {
            throw new Error(`Entity '${entityName}' not found in schema`);
        }
        return this.getTableName(entity);
    }

    /**
     * Generate all RLS policies
     */
    private generateAllRLS(): string | null {
        const policies: string[] = [];

        for (const entity of this.schema.entities) {
            if (entity.options?.rowLevelSecurity !== false) {
                policies.push(this.generateEntityRLS(entity));
            }
        }

        return policies.length > 0 ? policies.join('\n\n') : null;
    }

    /**
     * Generate all indexes
     */
    private generateAllIndexes(): string | null {
        const indexes: string[] = [];

        for (const entity of this.schema.entities) {
            indexes.push(this.generateEntityIndexes(entity));
        }

        return indexes.length > 0 ? indexes.join('\n\n') : null;
    }

    /**
     * Generate all triggers
     */
    private generateAllTriggers(): string | null {
        const triggers: string[] = [];

        triggers.push('-- Update timestamp trigger function');
        triggers.push(`
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';`);

        for (const entity of this.schema.entities) {
            if (entity.options?.timestamps !== false) {
                const tableName = this.getTableName(entity);
                triggers.push('');
                triggers.push(`-- Trigger for ${tableName}`);
                triggers.push(
                    `CREATE TRIGGER update_${tableName}_updated_at BEFORE UPDATE ON ${tableName} ` +
                    `FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();`
                );
            }
        }

        return triggers.length > 1 ? triggers.join('\n') : null;
    }

    /**
     * Generate migration header comment
     */
    private generateMigrationHeader(version: string): string {
        const now = new Date().toISOString();
        return `-- Migration: ${version}
-- Description: ${this.schema.description || 'Initial schema migration'}
-- Created: ${now}
-- Generated by Brickend Supabase Module
`;
    }

    /**
     * Generate timestamp for migration filename
     */
    private generateTimestamp(): string {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const hour = String(now.getHours()).padStart(2, '0');
        const minute = String(now.getMinutes()).padStart(2, '0');
        const second = String(now.getSeconds()).padStart(2, '0');

        return `${year}${month}${day}${hour}${minute}${second}`;
    }
}