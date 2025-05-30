/**
 * Template categories for organization
 */
export type TemplateCategory = 'service' | 'frontend' | 'infra' | 'fullstack';

/**
 * Supported template variable types
 */
export type TemplateVariableType = 'string' | 'number' | 'boolean' | 'array' | 'object';

/**
 * Definition of a configurable variable in a template
 */
export interface TemplateVariable {
    name: string;
    type: TemplateVariableType;
    required: boolean;
    description: string;
    defaultValue?: unknown;
    validation?: {
        pattern?: string;
        minLength?: number;
        maxLength?: number;
        min?: number;
        max?: number;
        enum?: string[];
    };
}

/**
 * Hook configuration for template lifecycle events
 */
export interface TemplateHooks {
    beforeGenerate?: string[]; // Commands to run before generation
    afterGenerate?: string[]; // Commands to run after generation
    beforeInstall?: string[]; // Commands to run before installing dependencies
    afterInstall?: string[]; // Commands to run after installing dependencies
}

/**
 * Post-processor configuration for generated files
 */
export interface PostProcessor {
    name: string; // e.g., 'prettier', 'eslint'
    config?: Record<string, unknown>;
    filePatterns?: string[]; // Glob patterns for files to process
}

/**
 * Template dependency specification
 */
export interface TemplateDependency {
    name: string;
    version?: string;
    dev?: boolean;
    optional?: boolean;
}

/**
 * File generation instruction
 */
export interface FileInstruction {
    source: string; // Source template file path (relative to template)
    destination: string; // Destination path (supports EJS variables)
    condition?: string; // EJS condition to determine if file should be generated
}

/**
 * Complete template configuration
 */
export interface TemplateConfig {
    // Basic metadata
    name: string;
    version: string;
    description: string;
    author?: string;
    license?: string;

    // Template categorization
    category: TemplateCategory;
    provider?: string; // e.g., 'supabase', 'firebase', 'prisma'
    tags?: string[];

    // Template requirements
    brickendVersion?: string; // Minimum Brickend version required
    nodeVersion?: string; // Node.js version requirement

    // Configuration
    variables: TemplateVariable[];
    dependencies?: TemplateDependency[];
    devDependencies?: TemplateDependency[];

    // Generation behavior
    files?: FileInstruction[]; // Optional: explicit file mapping
    postProcessors?: PostProcessor[];
    hooks?: TemplateHooks;

    // Features and capabilities
    features?: string[]; // e.g., ['auth', 'crud', 'realtime', 'storage']
    supports?: {
        entities?: boolean; // Does this template support entity generation?
        auth?: boolean; // Does this template include authentication?
        deployment?: boolean; // Does this template include deployment config?
    };
}

/**
 * Template metadata for registry
 */
export interface TemplateMetadata {
    path: string; // Absolute path to template directory
    config: TemplateConfig;
    isValid: boolean;
    validationErrors?: string[];
    lastModified?: Date;
}

/**
 * Template discovery result
 */
export interface DiscoveredTemplate {
    name: string;
    path: string;
    configPath: string;
    isValid: boolean;
    error?: string;
}