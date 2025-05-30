import type { Entity } from './entity.js';
import type { TemplateConfig } from './template.js';

/**
 * Project configuration from brickend.config.ts
 */
export interface ProjectConfig {
    name: string;
    description?: string;
    version?: string;

    // Template and provider
    template?: string; // Template name to use
    provider?: string; // Provider name (e.g., 'supabase')

    // Entities and schema
    entities?: Entity[];

    // Features to enable
    features?: string[];

    // Environment configuration
    environment?: Record<string, string>;

    // Deployment configuration
    deployment?: {
        target?: string; // e.g., 'vercel', 'netlify'
        regions?: string[];
        environment?: Record<string, string>;
    };

    // Custom variables for template
    variables?: Record<string, unknown>;
}

/**
 * Context passed to template engine for rendering
 */
export interface ProjectContext {
    // Project metadata
    project: {
        name: string;
        description: string;
        version: string;
        author?: string;
    };

    // Template information
    template: {
        name: string;
        version: string;
        provider?: string;
    };

    // Entities and schema
    entities: Entity[];

    // Feature flags
    features: Record<string, boolean>;

    // Environment variables
    env: Record<string, string>;

    // Custom variables
    variables: Record<string, unknown>;

    // Utility functions available in templates
    utils: {
        camelCase: (str: string) => string;
        pascalCase: (str: string) => string;
        kebabCase: (str: string) => string;
        snakeCase: (str: string) => string;
        pluralize: (str: string) => string;
        singularize: (str: string) => string;
        capitalize: (str: string) => string;
        lowercase: (str: string) => string;
        uppercase: (str: string) => string;
    };

    // Timestamps
    timestamps: {
        generated: Date;
        generatedISO: string;
        year: number;
    };
}

/**
 * Generated file information
 */
export interface GeneratedFile {
    path: string; // Relative path from project root
    content: string; // File content
    encoding?: 'utf8' | 'binary';
    executable?: boolean;
}

/**
 * Project generation result
 */
export interface GeneratedProject {
    // Project metadata
    name: string;
    path: string; // Absolute path to generated project
    template: string;

    // Generated files
    files: GeneratedFile[];

    // Generation metadata
    generatedAt: Date;
    brickendVersion: string;
    templateVersion: string;

    // Post-generation instructions
    instructions?: {
        install?: string[]; // Commands to install dependencies
        setup?: string[]; // Commands to setup project
        dev?: string[]; // Commands to start development
        deploy?: string[]; // Commands to deploy
    };

    // Validation results
    validation: {
        success: boolean;
        errors?: string[];
        warnings?: string[];
    };
}

/**
 * Template generation options
 */
export interface GenerationOptions {
    // Output configuration
    outputPath: string;
    overwrite?: boolean;
    dryRun?: boolean;

    // Processing options
    skipPostProcessors?: boolean;
    skipHooks?: boolean;
    skipInstall?: boolean;

    // Validation options
    validateOnly?: boolean;
    skipValidation?: boolean;

    // Logging
    verbose?: boolean;
    silent?: boolean;
}

/**
 * Context building options
 */
export interface ContextBuildOptions {
    // Source of context data
    config?: ProjectConfig;
    interactive?: boolean; // Build context from CLI prompts

    // Template information
    template: TemplateConfig;

    // Override options
    overrides?: Record<string, unknown>;

    // Validation
    validateEntities?: boolean;
    validateVariables?: boolean;
}