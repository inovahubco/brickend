/**
 * Field data types supported by Brickend
 */
export type FieldType =
    | 'string'
    | 'number'
    | 'boolean'
    | 'date'
    | 'datetime'
    | 'email'
    | 'url'
    | 'uuid'
    | 'json'
    | 'text'
    | 'integer'
    | 'float'
    | 'decimal';

/**
 * Validation rules for entity fields
 */
export interface FieldValidation {
    required?: boolean;
    minLength?: number;
    maxLength?: number;
    min?: number;
    max?: number;
    pattern?: string;
    enum?: string[];
    unique?: boolean;
}

/**
 * Database-specific field options
 */
export interface FieldOptions {
    primaryKey?: boolean;
    autoIncrement?: boolean;
    defaultValue?: string | number | boolean | null;
    nullable?: boolean;
    index?: boolean;
    foreignKey?: {
        table: string;
        column: string;
        onDelete?: 'CASCADE' | 'SET NULL' | 'RESTRICT';
        onUpdate?: 'CASCADE' | 'SET NULL' | 'RESTRICT';
    };
}

/**
 * Definition of a field in an entity
 */
export interface Field {
    name: string;
    type: FieldType;
    validation?: FieldValidation;
    options?: FieldOptions;
    description?: string;
}

/**
 * Relationship types between entities
 */
export type RelationshipType = 'oneToOne' | 'oneToMany' | 'manyToOne' | 'manyToMany';

/**
 * Definition of a relationship between entities
 */
export interface Relationship {
    type: RelationshipType;
    target: string; // Target entity name
    foreignKey?: string;
    joinTable?: string; // For many-to-many relationships
    onDelete?: 'CASCADE' | 'SET NULL' | 'RESTRICT';
    onUpdate?: 'CASCADE' | 'SET NULL' | 'RESTRICT';
}

/**
 * Entity configuration for database table generation
 */
export interface EntityOptions {
    tableName?: string; // Custom table name (defaults to pluralized entity name)
    timestamps?: boolean; // Add created_at, updated_at fields
    softDelete?: boolean; // Add deleted_at field for soft deletion
    auditLog?: boolean; // Enable audit logging
    rowLevelSecurity?: boolean; // Enable RLS (for Supabase)
}

/**
 * Complete definition of an entity (database table)
 */
export interface Entity {
    name: string; // Entity name in PascalCase (e.g., "User", "BlogPost")
    fields: Field[];
    relationships?: Record<string, Relationship>;
    options?: EntityOptions;
    description?: string;
}

/**
 * Schema definition containing multiple entities
 */
export interface Schema {
    entities: Entity[];
    version?: string;
    description?: string;
}