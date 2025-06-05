/**
 * Supabase module type definitions
 */

import type { Entity, Field } from '@brickend/core';

/**
 * Supabase project configuration
 */
export interface SupabaseConfig {
    projectId?: string;
    anonKey?: string;
    serviceRoleKey?: string;
    url?: string;

    // Database configuration
    database?: {
        host?: string;
        port?: number;
        name?: string;
        schema?: string;
    };

    // Edge Functions configuration
    functions?: {
        region?: string;
        timeout?: number;
        memory?: number;
    };

    // Storage configuration
    storage?: {
        buckets?: StorageBucketConfig[];
    };

    // Auth configuration
    auth?: AuthConfig;

    // Environment-specific settings
    environment?: 'development' | 'staging' | 'production';
}

/**
 * Database schema configuration
 */
export interface DatabaseSchema {
    entities: Entity[];
    version: string;
    description?: string;

    // Global settings
    settings?: {
        enableRLS?: boolean;
        enableRealtimeByDefault?: boolean;
        timestampsEnabled?: boolean;
        softDeleteEnabled?: boolean;
    };

    // Custom SQL to run before/after schema creation
    beforeScript?: string;
    afterScript?: string;
}

/**
 * Migration configuration
 */
export interface MigrationConfig {
    name: string;
    version: string;
    description?: string;

    // Migration type
    type: 'schema' | 'data' | 'function' | 'trigger';

    // SQL operations
    up: string;
    down?: string;

    // Dependencies
    dependsOn?: string[];

    // Metadata
    createdAt: Date;
    appliedAt?: Date;
}

/**
 * Authentication configuration
 */
export interface AuthConfig {
    // Providers
    providers?: {
        email?: boolean;
        google?: boolean;
        github?: boolean;
        discord?: boolean;
        apple?: boolean;
        facebook?: boolean;
        twitter?: boolean;
    };

    // Email settings
    email?: {
        confirmSignup?: boolean;
        inviteUsers?: boolean;
        enableSignups?: boolean;
    };

    // Password settings
    password?: {
        minLength?: number;
        requireUppercase?: boolean;
        requireLowercase?: boolean;
        requireNumbers?: boolean;
        requireSymbols?: boolean;
    };

    // Session settings
    session?: {
        timeoutHours?: number;
        inactivityTimeoutMinutes?: number;
        refreshTokenRotation?: boolean;
    };

    // Custom claims
    customClaims?: Record<string, any>;

    // Hooks
    hooks?: {
        beforeSignUp?: string; // SQL function name
        afterSignUp?: string;
        beforeSignIn?: string;
        afterSignIn?: string;
    };
}

/**
 * Storage bucket configuration
 */
export interface StorageBucketConfig {
    name: string;
    public?: boolean;
    allowedMimeTypes?: string[];
    fileSizeLimit?: number; // in bytes

    // Access policies
    policies?: {
        insert?: string; // RLS policy
        select?: string;
        update?: string;
        delete?: string;
    };
}

/**
 * Row Level Security policy configuration
 */
export interface RLSPolicy {
    name: string;
    table: string;
    operation: 'SELECT' | 'INSERT' | 'UPDATE' | 'DELETE' | 'ALL';
    role?: string;
    condition: string; // SQL condition
    check?: string; // SQL check condition for INSERT/UPDATE
}

/**
 * Database index configuration
 */
export interface DatabaseIndex {
    name: string;
    table: string;
    columns: string[];
    unique?: boolean;
    type?: 'btree' | 'hash' | 'gin' | 'gist';
    where?: string; // Partial index condition
    concurrent?: boolean;
}

/**
 * Database trigger configuration
 */
export interface DatabaseTrigger {
    name: string;
    table: string;
    timing: 'BEFORE' | 'AFTER' | 'INSTEAD OF';
    events: ('INSERT' | 'UPDATE' | 'DELETE')[];
    function: string; // Function name
    condition?: string; // WHEN condition
}

/**
 * Supabase Edge Function configuration
 */
export interface EdgeFunctionConfig {
    name: string;
    description?: string;

    // Runtime configuration
    runtime?: 'deno' | 'node';
    memory?: number; // MB
    timeout?: number; // seconds

    // Environment variables
    env?: Record<string, string>;

    // CORS configuration
    cors?: {
        allowOrigin?: string | string[];
        allowMethods?: string[];
        allowHeaders?: string[];
        exposeHeaders?: string[];
        maxAge?: number;
        credentials?: boolean;
    };

    // Rate limiting
    rateLimit?: {
        requests?: number;
        window?: string; // e.g., "1m", "1h"
    };
}

/**
 * Generated client configuration
 */
export interface ClientConfig {
    // Client type
    type: 'server' | 'browser' | 'typed';

    // Generated client options
    options?: {
        includeTypes?: boolean;
        includeAuth?: boolean;
        includeStorage?: boolean;
        includeRealtime?: boolean;
        includeFunctions?: boolean;
    };

    // Custom client methods
    customMethods?: {
        name: string;
        entity: string;
        operation: 'create' | 'read' | 'update' | 'delete' | 'custom';
        implementation?: string;
    }[];
}

/**
 * SQL data types mapping
 */
export type SQLDataType =
    | 'text'
    | 'varchar'
    | 'char'
    | 'integer'
    | 'bigint'
    | 'smallint'
    | 'decimal'
    | 'numeric'
    | 'real'
    | 'double precision'
    | 'boolean'
    | 'date'
    | 'timestamp'
    | 'timestamptz'
    | 'time'
    | 'timetz'
    | 'interval'
    | 'uuid'
    | 'json'
    | 'jsonb'
    | 'bytea'
    | 'inet'
    | 'cidr'
    | 'macaddr'
    | 'point'
    | 'line'
    | 'lseg'
    | 'box'
    | 'path'
    | 'polygon'
    | 'circle';

/**
 * Field to SQL type mapping
 */
export interface FieldToSQLMapping {
    field: Field;
    sqlType: SQLDataType;
    constraints: string[];
    defaultValue?: string;
}

/**
 * Generated migration result
 */
export interface GeneratedMigration {
    filename: string;
    content: string;
    version: string;
    description: string;
    dependencies: string[];
}

/**
 * Generated client result
 */
export interface GeneratedClient {
    filename: string;
    content: string;
    type: 'server' | 'browser' | 'types' | 'typed';
    exports: string[];
}

/**
 * Validation error for Supabase configurations
 */
export interface SupabaseValidationError {
    field: string;
    message: string;
    code: string;
    severity: 'error' | 'warning';
}

/**
 * Supabase project status
 */
export interface ProjectStatus {
    connected: boolean;
    version?: string;
    region?: string;
    plan?: string;
    lastMigration?: string;
    pendingMigrations?: string[];
    health?: {
        database: 'healthy' | 'degraded' | 'down';
        api: 'healthy' | 'degraded' | 'down';
        auth: 'healthy' | 'degraded' | 'down';
        storage: 'healthy' | 'degraded' | 'down';
        functions: 'healthy' | 'degraded' | 'down';
    };
}