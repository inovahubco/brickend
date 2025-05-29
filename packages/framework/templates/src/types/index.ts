/**
 * Types and interfaces for Brickend Templates system
 */

/**
 * Context data passed to templates during rendering
 */
export interface TemplateContext {
    /** Project/resource name */
    name: string;
    /** Formatted variations of the name */
    names: {
        camelCase: string;      // userName
        pascalCase: string;     // UserName
        kebabCase: string;      // user-name
        snakeCase: string;      // user_name
        plural: string;         // users
        singular: string;       // user
    };
    /** Fields for resource generation */
    fields?: TemplateField[];
    /** Custom variables */
    variables?: Record<string, any>;
    /** Template metadata */
    metadata?: TemplateMetadata;
}

/**
 * Field definition for resource generation
 */
export interface TemplateField {
    /** Field name */
    name: string;
    /** Field type */
    type: TemplateFieldType;
    /** Whether field is required */
    required?: boolean;
    /** Default value */
    defaultValue?: any;
    /** Field description */
    description?: string;
    /** Validation rules */
    validation?: FieldValidation;
    /** Field metadata */
    metadata?: Record<string, any>;
}

/**
 * Supported field types
 */
export type TemplateFieldType =
    | 'string'
    | 'number'
    | 'boolean'
    | 'date'
    | 'email'
    | 'url'
    | 'text'
    | 'json'
    | 'uuid'
    | 'array'
    | 'object';

/**
 * Field validation rules
 */
export interface FieldValidation {
    /** Minimum length/value */
    min?: number;
    /** Maximum length/value */
    max?: number;
    /** Regular expression pattern */
    pattern?: string;
    /** Custom validation function */
    custom?: string;
}

/**
 * Template metadata
 */
export interface TemplateMetadata {
    /** Template name */
    name: string;
    /** Template description */
    description?: string;
    /** Template version */
    version?: string;
    /** Template author */
    author?: string;
    /** Template tags */
    tags?: string[];
    /** Required variables */
    requiredVariables?: string[];
    /** Template dependencies */
    dependencies?: string[];
}

/**
 * Template definition
 */
export interface TemplateDefinition {
    /** Template identifier */
    id: string;
    /** Template name */
    name: string;
    /** Template description */
    description?: string;
    /** Template category */
    category: TemplateCategory;
    /** Path to template files */
    path: string;
    /** Template files */
    files: TemplateFile[];
    /** Template metadata */
    metadata?: TemplateMetadata;
}

/**
 * Template categories
 */
export type TemplateCategory = 'project' | 'resource' | 'config' | 'component';

/**
 * Template file definition
 */
export interface TemplateFile {
    /** Source template path (relative to template) */
    source: string;
    /** Target output path (can include variables) */
    target: string;
    /** Whether file should be executable */
    executable?: boolean;
    /** Conditions for including this file */
    condition?: string;
}

/**
 * Template rendering options
 */
export interface RenderOptions {
    /** Output directory */
    outputDir: string;
    /** Whether to overwrite existing files */
    overwrite?: boolean;
    /** Whether to create directories if they don't exist */
    createDirs?: boolean;
    /** File encoding */
    encoding?: BufferEncoding;
    /** Custom context variables */
    context?: Record<string, any>;
}

/**
 * Template engine interface - Updated to match TemplateEngine implementation
 */
export interface ITemplateEngine {
    /** Render a template string with context */
    renderString(template: string, context: TemplateContext): Promise<string>;

    /** Render a template file with context */
    renderFile(templatePath: string, context: TemplateContext): Promise<string>;

    /** Register a helper function */
    registerHelper(name: string, helper: TemplateHelper): void;

    /** Get all registered helpers */
    getHelpers(): Record<string, TemplateHelper>;

    /** Remove a helper function */
    unregisterHelper(name: string): void;

    /** Check if a helper is registered */
    hasHelper(name: string): boolean;

    /** Clear all custom helpers (keeps default helpers) */
    clearCustomHelpers(): void;
}

/**
 * Template helper function
 */
export type TemplateHelper = (...args: any[]) => any;

/**
 * Template registry interface - Updated to match TemplateRegistry implementation
 */
export interface ITemplateRegistry {
    /** Register a template */
    register(template: TemplateDefinition): void;

    /** Get a template by id */
    get(id: string): TemplateDefinition | undefined;

    /** List all templates */
    list(): TemplateDefinition[];

    /** List templates by category */
    listByCategory(category: TemplateCategory): TemplateDefinition[];

    /** Check if template exists */
    exists(id: string): boolean;

    /** Remove a template */
    unregister(id: string): boolean;

    /** Clear all templates */
    clear(): void;

    /** Get template count */
    count(): number;

    /** Load templates from a directory */
    loadFromDirectory(directoryPath: string): Promise<void>;

    /** Search templates by term */
    search(term: string): TemplateDefinition[];

    /** Validate a template definition */
    validate(template: TemplateDefinition): string[];
}

/**
 * Generator options
 */
export interface GeneratorOptions {
    /** Template registry to use */
    registry?: ITemplateRegistry;

    /** Template engine to use */
    engine?: ITemplateEngine;

    /** Default rendering options */
    defaultRenderOptions?: Partial<RenderOptions>;

    /** Whether to log generation progress */
    verbose?: boolean;
}

/**
 * Generation result
 */
export interface GenerationResult {
    /** Whether generation was successful */
    success: boolean;

    /** Generated files */
    files: string[];

    /** Generation errors */
    errors: GenerationError[];

    /** Generation warnings */
    warnings: string[];

    /** Generation metadata */
    metadata: {
        templateId: string;
        context: TemplateContext;
        duration: number;
        timestamp: Date;
    };
}

/**
 * Generation error
 */
export interface GenerationError {
    /** Error type */
    type: 'template' | 'file' | 'validation' | 'system';

    /** Error message */
    message: string;

    /** File path where error occurred */
    file?: string;

    /** Original error */
    originalError?: Error;
}

/**
 * Project generation options
 */
export interface ProjectGenerationOptions extends RenderOptions {
    /** Project template id */
    templateId: string;

    /** Project name */
    name: string;

    /** Additional context variables */
    variables?: Record<string, any>;
}

/**
 * Resource generation options
 */
export interface ResourceGenerationOptions extends RenderOptions {
    /** Resource template id */
    templateId?: string;

    /** Resource name */
    name: string;

    /** Resource fields */
    fields: TemplateField[];

    /** Additional context variables */
    variables?: Record<string, any>;
}

/**
 * Config generation options
 */
export interface ConfigGenerationOptions extends RenderOptions {
    /** Config template id */
    templateId: string;

    /** Config type */
    type: string;

    /** Additional context variables */
    variables?: Record<string, any>;
}