/**
 * Brickend Supabase Module
 * 
 * Utilities and generators for Supabase integration
 */

// Type definitions
export type * from './types/index.js';

// Database utilities
export * from './database/index.js';

// Client utilities  
export * from './client/index.js';

// Edge Functions utilities
export * from './functions/index.js';

// Main Supabase utilities
import { createSupabaseClient } from './client/index.js';
import { generateMigration } from './database/index.js';
import type { SupabaseConfig } from './types/index.js';

/**
 * Main Supabase utility class
 */
export class SupabaseModule {
    private config: SupabaseConfig;

    constructor(config: SupabaseConfig) {
        this.config = config;
    }

    /**
     * Get Supabase configuration
     */
    getConfig(): SupabaseConfig {
        return { ...this.config };
    }

    /**
     * Update Supabase configuration
     */
    updateConfig(updates: Partial<SupabaseConfig>): void {
        this.config = { ...this.config, ...updates };
    }

    /**
     * Validate Supabase configuration
     */
    validateConfig(): { valid: boolean; errors: string[] } {
        const errors: string[] = [];

        // Basic validation
        if (!this.config.url && !this.config.projectId) {
            errors.push('Either url or projectId is required');
        }

        if (!this.config.anonKey) {
            errors.push('anonKey is required');
        }

        // URL format validation
        if (this.config.url && !this.isValidUrl(this.config.url)) {
            errors.push('Invalid Supabase URL format');
        }

        // Project ID validation  
        if (this.config.projectId && !this.isValidProjectId(this.config.projectId)) {
            errors.push('Invalid project ID format');
        }

        return {
            valid: errors.length === 0,
            errors
        };
    }

    /**
     * Create Supabase client with current config
     */
    createClient(type: 'server' | 'browser' = 'server') {
        const validation = this.validateConfig();
        if (!validation.valid) {
            throw new Error(`Invalid Supabase config: ${validation.errors.join(', ')}`);
        }

        return createSupabaseClient(this.config, type);
    }

    /**
     * Get connection status
     */
    async getStatus() {
        // Implementation would check Supabase project status
        // This is a placeholder for the actual implementation
        return {
            connected: false,
            message: 'Status check not implemented yet'
        };
    }

    private isValidUrl(url: string): boolean {
        try {
            const parsed = new URL(url);
            return parsed.hostname.includes('supabase.co') ||
                parsed.hostname.includes('localhost') ||
                parsed.hostname.includes('127.0.0.1');
        } catch {
            return false;
        }
    }

    private isValidProjectId(projectId: string): boolean {
        // Supabase project IDs are typically lowercase alphanumeric with hyphens
        return /^[a-z0-9][a-z0-9-]{0,61}[a-z0-9]$/.test(projectId);
    }
}

/**
 * Create a new Supabase module instance
 */
export function createSupabaseModule(config: SupabaseConfig): SupabaseModule {
    return new SupabaseModule(config);
}

/**
 * Validate Supabase project configuration
 */
export function validateSupabaseConfig(config: SupabaseConfig): { valid: boolean; errors: string[] } {
    const module = new SupabaseModule(config);
    return module.validateConfig();
}

/**
 * Helper to get default Supabase configuration
 */
export function getDefaultSupabaseConfig(projectId?: string): SupabaseConfig {
    return {
        projectId,
        url: projectId ? `https://${projectId}.supabase.co` : undefined,
        environment: 'development',
        database: {
            schema: 'public'
        },
        auth: {
            providers: {
                email: true
            },
            email: {
                confirmSignup: true,
                enableSignups: true
            },
            password: {
                minLength: 8
            },
            session: {
                timeoutHours: 24,
                refreshTokenRotation: true
            }
        },
        functions: {
            region: 'us-east-1',
            timeout: 30,
            memory: 512
        }
    };
}