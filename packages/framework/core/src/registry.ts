/**
 * Simple logger interface for template registry
 */
interface Logger {
    debug(message: string, data?: any): void;
    info(message: string, data?: any): void;
    warn(message: string, data?: any): void;
    error(message: string, data?: any): void;
}

/**
 * Default console-based logger implementation
 */
const createDefaultLogger = (): Logger => ({
    debug: (message: string, data?: any) => {
        if (process.env.DEBUG || process.env.NODE_ENV === 'development') {
            console.debug('🔍', message, data ? JSON.stringify(data, null, 2) : '');
        }
    },
    info: (message: string, data?: any) => {
        console.log('ℹ️ ', message, data ? JSON.stringify(data, null, 2) : '');
    },
    warn: (message: string, data?: any) => {
        console.warn('⚠️ ', message, data ? JSON.stringify(data, null, 2) : '');
    },
    error: (message: string, data?: any) => {
        console.error('❌', message, data ? JSON.stringify(data, null, 2) : '');
    },
});
import { z } from 'zod';
import { fileUtils, pathUtils } from './helpers/index.js';
import type {
    TemplateConfig,
    TemplateMetadata,
    DiscoveredTemplate,
    TemplateCategory,
    TemplateVariableType
} from './types/index.js';

/**
 * Zod schema for template configuration validation
 */
const TemplateVariableSchema = z.object({
    name: z.string().min(1),
    type: z.enum(['string', 'number', 'boolean', 'array', 'object'] as const),
    required: z.boolean(),
    description: z.string(),
    defaultValue: z.any().optional(),
    validation: z.object({
        pattern: z.string().optional(),
        minLength: z.number().optional(),
        maxLength: z.number().optional(),
        min: z.number().optional(),
        max: z.number().optional(),
        enum: z.array(z.string()).optional(),
    }).optional(),
});

const TemplateDependencySchema = z.object({
    name: z.string().min(1),
    version: z.string().optional(),
    dev: z.boolean().optional(),
    optional: z.boolean().optional(),
});

const PostProcessorSchema = z.object({
    name: z.string().min(1),
    config: z.record(z.any()).optional(),
    filePatterns: z.array(z.string()).optional(),
});

const TemplateHooksSchema = z.object({
    beforeGenerate: z.array(z.string()).optional(),
    afterGenerate: z.array(z.string()).optional(),
    beforeInstall: z.array(z.string()).optional(),
    afterInstall: z.array(z.string()).optional(),
});

const FileInstructionSchema = z.object({
    source: z.string().min(1),
    destination: z.string().min(1),
    condition: z.string().optional(),
});

const TemplateConfigSchema = z.object({
    // Basic metadata
    name: z.string().min(1),
    version: z.string().min(1),
    description: z.string(),
    author: z.string().optional(),
    license: z.string().optional(),

    // Template categorization
    category: z.enum(['service', 'frontend', 'infra', 'fullstack'] as const),
    provider: z.string().optional(),
    tags: z.array(z.string()).optional(),

    // Template requirements
    brickendVersion: z.string().optional(),
    nodeVersion: z.string().optional(),

    // Configuration
    variables: z.array(TemplateVariableSchema),
    dependencies: z.array(TemplateDependencySchema).optional(),
    devDependencies: z.array(TemplateDependencySchema).optional(),

    // Generation behavior
    files: z.array(FileInstructionSchema).optional(),
    postProcessors: z.array(PostProcessorSchema).optional(),
    hooks: TemplateHooksSchema.optional(),

    // Features and capabilities
    features: z.array(z.string()).optional(),
    supports: z.object({
        entities: z.boolean().optional(),
        auth: z.boolean().optional(),
        deployment: z.boolean().optional(),
    }).optional(),
});

/**
 * Template Registry - Manages discovery, loading, and validation of templates
 */
export class TemplateRegistry {
    private readonly logger: Logger;
    private readonly templatePaths: string[] = [];
    private readonly loadedTemplates: Map<string, TemplateMetadata> = new Map();
    private lastScanTime: Date | null = null;

    constructor(options: { templatePaths?: string[]; logger?: Logger } = {}) {
        this.logger = options.logger || createDefaultLogger();
        this.templatePaths = options.templatePaths || [];
    }

    /**
     * Add a template search path
     * @param templatePath - Absolute path to templates directory
     */
    addTemplatePath(templatePath: string): void {
        const resolvedPath = pathUtils.resolvePath(templatePath);

        if (!this.templatePaths.includes(resolvedPath)) {
            this.templatePaths.push(resolvedPath);
            this.logger.debug('Added template path', { templatePath: resolvedPath });
        }
    }

    /**
     * Remove a template search path
     * @param templatePath - Template path to remove
     */
    removeTemplatePath(templatePath: string): void {
        const resolvedPath = pathUtils.resolvePath(templatePath);
        const index = this.templatePaths.indexOf(resolvedPath);

        if (index !== -1) {
            this.templatePaths.splice(index, 1);
            this.logger.debug('Removed template path', { templatePath: resolvedPath });

            // Remove templates from this path from cache
            this.clearTemplatesFromPath(resolvedPath);
        }
    }

    /**
     * Get all registered template paths
     * @returns Array of template paths
     */
    getTemplatePaths(): string[] {
        return [...this.templatePaths];
    }

    /**
     * Discover all templates in registered paths
     * @param force - Force rescan even if recently scanned
     * @returns Array of discovered templates
     */
    async discoverTemplates(force: boolean = false): Promise<DiscoveredTemplate[]> {
        // Skip scan if recently performed and not forced
        if (!force && this.lastScanTime && (Date.now() - this.lastScanTime.getTime()) < 5000) {
            this.logger.debug('Skipping template discovery - recently scanned');
            return Array.from(this.loadedTemplates.values()).map(meta => ({
                name: meta.config.name,
                path: meta.path,
                configPath: pathUtils.joinPath(meta.path, 'template.config.json'),
                isValid: meta.isValid,
                error: meta.validationErrors?.join('; '),
            }));
        }

        this.logger.info('Discovering templates...');
        const discovered: DiscoveredTemplate[] = [];

        for (const templatePath of this.templatePaths) {
            try {
                if (!(await fileUtils.exists(templatePath))) {
                    this.logger.warn('Template path does not exist', { templatePath });
                    continue;
                }

                if (!(await fileUtils.isDirectory(templatePath))) {
                    this.logger.warn('Template path is not a directory', { templatePath });
                    continue;
                }

                const pathTemplates = await this.discoverTemplatesInPath(templatePath);
                discovered.push(...pathTemplates);
            } catch (error) {
                this.logger.error('Failed to discover templates in path', {
                    templatePath,
                    error: error instanceof Error ? error.message : 'Unknown error'
                });
            }
        }

        this.lastScanTime = new Date();
        this.logger.info('Template discovery completed', { count: discovered.length });

        return discovered;
    }

    /**
     * Discover templates in a specific path
     * @param basePath - Base path to search
     * @returns Array of discovered templates in this path
     */
    private async discoverTemplatesInPath(basePath: string): Promise<DiscoveredTemplate[]> {
        const discovered: DiscoveredTemplate[] = [];

        try {
            // Look for template.config.json files
            const configFiles = await fileUtils.findFiles('**/template.config.json', {
                cwd: basePath,
                ignore: ['**/node_modules/**']
            });

            for (const configFile of configFiles) {
                const templatePath = pathUtils.getDirName(configFile);
                const templateName = pathUtils.getBaseName(templatePath);

                const discoveredTemplate: DiscoveredTemplate = {
                    name: templateName,
                    path: templatePath,
                    configPath: configFile,
                    isValid: false,
                };

                try {
                    // Try to load and validate the template
                    const metadata = await this.loadTemplateMetadata(templatePath);
                    discoveredTemplate.isValid = metadata.isValid;
                    discoveredTemplate.name = metadata.config.name; // Use name from config

                    if (!metadata.isValid) {
                        discoveredTemplate.error = metadata.validationErrors?.join('; ');
                    }

                    // Cache the loaded template
                    this.loadedTemplates.set(metadata.config.name, metadata);

                } catch (error) {
                    discoveredTemplate.error = error instanceof Error ? error.message : 'Unknown error';
                    this.logger.warn('Failed to load template', {
                        templatePath,
                        error: discoveredTemplate.error
                    });
                }

                discovered.push(discoveredTemplate);
            }
        } catch (error) {
            this.logger.error('Failed to discover templates in path', {
                basePath,
                error: error instanceof Error ? error.message : 'Unknown error'
            });
        }

        return discovered;
    }

    /**
     * Load template metadata from directory
     * @param templatePath - Path to template directory
     * @returns Template metadata
     */
    private async loadTemplateMetadata(templatePath: string): Promise<TemplateMetadata> {
        const configPath = pathUtils.joinPath(templatePath, 'template.config.json');

        if (!(await fileUtils.exists(configPath))) {
            throw new Error(`Template configuration not found: ${configPath}`);
        }

        // Read and parse config
        const configData = await fileUtils.readJsonFile(configPath);

        // Validate config
        const validation = TemplateConfigSchema.safeParse(configData);
        const validationErrors: string[] = [];
        let isValid = true;

        if (!validation.success) {
            isValid = false;
            validationErrors.push(...validation.error.errors.map(err =>
                `${err.path.join('.')}: ${err.message}`
            ));
        }

        // Additional validation
        try {
            await this.validateTemplateStructure(templatePath, validation.data || configData);
        } catch (error) {
            isValid = false;
            validationErrors.push(error instanceof Error ? error.message : 'Template structure validation failed');
        }

        const metadata: TemplateMetadata = {
            path: templatePath,
            config: validation.data || configData,
            isValid,
            validationErrors: validationErrors.length > 0 ? validationErrors : undefined,
            lastModified: new Date(),
        };

        return metadata;
    }

    /**
     * Validate template directory structure
     * @param templatePath - Path to template directory
     * @param config - Template configuration
     */
    private async validateTemplateStructure(templatePath: string, config: any): Promise<void> {
        // Check if template has any .ejs files
        const templateFiles = await fileUtils.templateFiles.listTemplates(templatePath);

        if (templateFiles.length === 0) {
            throw new Error('Template contains no .ejs files');
        }

        // If explicit file instructions are provided, validate them
        if (config.files && Array.isArray(config.files)) {
            for (const fileInstruction of config.files) {
                const sourcePath = pathUtils.joinPath(templatePath, fileInstruction.source);

                if (!(await fileUtils.exists(sourcePath))) {
                    throw new Error(`Template file not found: ${fileInstruction.source}`);
                }
            }
        }

        // Validate variable names are valid identifiers
        if (config.variables && Array.isArray(config.variables)) {
            for (const variable of config.variables) {
                if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(variable.name)) {
                    throw new Error(`Invalid variable name: ${variable.name}`);
                }
            }
        }
    }

    /**
     * Get template by name
     * @param name - Template name
     * @returns Template metadata or undefined if not found
     */
    async getTemplate(name: string): Promise<TemplateMetadata | undefined> {
        // Try cache first
        if (this.loadedTemplates.has(name)) {
            return this.loadedTemplates.get(name);
        }

        // If not in cache, try to discover templates
        await this.discoverTemplates();

        return this.loadedTemplates.get(name);
    }

    /**
     * Get all loaded templates
     * @returns Array of all template metadata
     */
    getAllTemplates(): TemplateMetadata[] {
        return Array.from(this.loadedTemplates.values());
    }

    /**
     * Get templates by category
     * @param category - Template category
     * @returns Array of templates in category
     */
    getTemplatesByCategory(category: TemplateCategory): TemplateMetadata[] {
        return this.getAllTemplates().filter(template =>
            template.config.category === category && template.isValid
        );
    }

    /**
     * Get templates by provider
     * @param provider - Provider name
     * @returns Array of templates for provider
     */
    getTemplatesByProvider(provider: string): TemplateMetadata[] {
        return this.getAllTemplates().filter(template =>
            template.config.provider === provider && template.isValid
        );
    }

    /**
     * Check if template exists
     * @param name - Template name
     * @returns True if template exists and is valid
     */
    async hasTemplate(name: string): Promise<boolean> {
        const template = await this.getTemplate(name);
        return template?.isValid === true;
    }

    /**
     * Reload template from disk
     * @param name - Template name
     * @returns Updated template metadata
     */
    async reloadTemplate(name: string): Promise<TemplateMetadata | undefined> {
        const existing = this.loadedTemplates.get(name);
        if (!existing) {
            return undefined;
        }

        try {
            const updated = await this.loadTemplateMetadata(existing.path);
            this.loadedTemplates.set(name, updated);

            this.logger.info('Template reloaded', { templateName: name });
            return updated;
        } catch (error) {
            this.logger.error('Failed to reload template', {
                templateName: name,
                error: error instanceof Error ? error.message : 'Unknown error'
            });

            return existing;
        }
    }

    /**
     * Clear template cache
     */
    clearCache(): void {
        this.loadedTemplates.clear();
        this.lastScanTime = null;
        this.logger.debug('Template cache cleared');
    }

    /**
     * Remove templates from a specific path from cache
     * @param templatePath - Path to remove templates from
     */
    private clearTemplatesFromPath(templatePath: string): void {
        const toRemove: string[] = [];

        for (const [name, metadata] of this.loadedTemplates.entries()) {
            if (metadata.path.startsWith(templatePath)) {
                toRemove.push(name);
            }
        }

        for (const name of toRemove) {
            this.loadedTemplates.delete(name);
        }

        if (toRemove.length > 0) {
            this.logger.debug('Removed templates from cache', {
                templatePath,
                removedCount: toRemove.length
            });
        }
    }

    /**
     * Get registry statistics
     * @returns Registry stats
     */
    getStats(): {
        templatePaths: number;
        totalTemplates: number;
        validTemplates: number;
        invalidTemplates: number;
        lastScanTime: Date | null;
    } {
        const templates = this.getAllTemplates();
        const validTemplates = templates.filter(t => t.isValid);

        return {
            templatePaths: this.templatePaths.length,
            totalTemplates: templates.length,
            validTemplates: validTemplates.length,
            invalidTemplates: templates.length - validTemplates.length,
            lastScanTime: this.lastScanTime,
        };
    }
}