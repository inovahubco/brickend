/**
 * Main Generator Class for Brickend Templates
 * Orchestrates template rendering and file generation
 */

import * as fs from 'fs-extra';
import * as path from 'path';
import { TemplateEngine } from './engine/template-engine.js';
import { TemplateRegistry } from './engine/template-registry.js';
import { ContextBuilder } from './utils/context-builder.js';
import type {
    GeneratorOptions,
    GenerationResult,
    ProjectGenerationOptions,
    ResourceGenerationOptions,
    ConfigGenerationOptions,
    TemplateContext,
    TemplateDefinition,
    GenerationError,
    RenderOptions,
    ITemplateEngine,
    ITemplateRegistry,
} from './types/index.js';

/**
 * Main Generator class that orchestrates template processing and file generation
 */
export class Generator {
    private engine: ITemplateEngine;
    private registry: ITemplateRegistry;
    private verbose: boolean;
    private defaultRenderOptions: Partial<RenderOptions>;

    constructor(options: GeneratorOptions = {}) {
        this.engine = options.engine || new TemplateEngine();
        this.registry = options.registry || new TemplateRegistry();
        this.verbose = options.verbose || false;
        this.defaultRenderOptions = options.defaultRenderOptions || {};
    }

    /**
     * Generate a complete project from template
     */
    async generateProject(
        name: string,
        templateId: string,
        options: Partial<ProjectGenerationOptions> = {}
    ): Promise<GenerationResult> {
        const startTime = Date.now();
        const errors: GenerationError[] = [];
        const warnings: string[] = [];
        const generatedFiles: string[] = [];

        try {
            // Validate inputs
            this.validateProjectInputs(name, templateId);

            // Get template definition
            const template = this.registry.get(templateId);
            if (!template) {
                throw new Error(`Project template '${templateId}' not found`);
            }

            if (template.category !== 'project') {
                throw new Error(`Template '${templateId}' is not a project template`);
            }

            this.log(`Starting project generation: ${name} using template ${templateId}`);

            // Build generation options
            const generationOptions: ProjectGenerationOptions = {
                templateId,
                name,
                outputDir: options.outputDir || `./${name}`,
                overwrite: options.overwrite || false,
                createDirs: options.createDirs !== false,
                encoding: options.encoding || 'utf8',
                variables: options.variables || {},
                context: options.context || {}
            };

            // Build template context
            const context = ContextBuilder.buildProjectContext(generationOptions);
            const enhancedContext = ContextBuilder.enhanceContext(context, generationOptions.context);

            // Validate context
            const contextErrors = ContextBuilder.validateContext(enhancedContext);
            if (contextErrors.length > 0) {
                contextErrors.forEach(error => {
                    errors.push({
                        type: 'validation',
                        message: error,
                        file: undefined,
                        originalError: undefined
                    });
                });
            }

            // Generate files
            const fileResults = await this.generateTemplateFiles(
                template,
                enhancedContext,
                generationOptions
            );

            generatedFiles.push(...fileResults.files);
            errors.push(...fileResults.errors);
            warnings.push(...fileResults.warnings);

            this.log(`Project generation completed. Generated ${generatedFiles.length} files.`);

            return {
                success: errors.length === 0,
                files: generatedFiles,
                errors,
                warnings,
                metadata: {
                    templateId,
                    context: enhancedContext,
                    duration: Date.now() - startTime,
                    timestamp: new Date()
                }
            };

        } catch (error) {
            errors.push({
                type: 'system',
                message: error instanceof Error ? error.message : 'Unknown error',
                originalError: error instanceof Error ? error : undefined
            });

            return {
                success: false,
                files: generatedFiles,
                errors,
                warnings,
                metadata: {
                    templateId,
                    context: {} as TemplateContext,
                    duration: Date.now() - startTime,
                    timestamp: new Date()
                }
            };
        }
    }

    /**
     * Generate a resource (CRUD, component, etc.) from template
     */
    async generateResource(
        name: string,
        fields: ResourceGenerationOptions['fields'],
        options: Partial<ResourceGenerationOptions> = {}
    ): Promise<GenerationResult> {
        const startTime = Date.now();
        const errors: GenerationError[] = [];
        const warnings: string[] = [];
        const generatedFiles: string[] = [];

        try {
            // Validate inputs
            this.validateResourceInputs(name, fields);

            // Get template definition
            const templateId = options.templateId || 'crud';
            const template = this.registry.get(templateId);
            if (!template) {
                throw new Error(`Resource template '${templateId}' not found`);
            }

            if (template.category !== 'resource') {
                throw new Error(`Template '${templateId}' is not a resource template`);
            }

            this.log(`Starting resource generation: ${name} using template ${templateId}`);

            // Build generation options
            const generationOptions: ResourceGenerationOptions = {
                templateId,
                name,
                fields,
                outputDir: options.outputDir || './src',
                overwrite: options.overwrite || false,
                createDirs: options.createDirs !== false,
                encoding: options.encoding || 'utf8',
                variables: options.variables || {},
                context: options.context || {}
            };

            // Build template context
            const context = ContextBuilder.buildResourceContext(generationOptions);
            const enhancedContext = ContextBuilder.enhanceContext(context, generationOptions.context);

            // Validate context
            const contextErrors = ContextBuilder.validateContext(enhancedContext);
            if (contextErrors.length > 0) {
                contextErrors.forEach(error => {
                    errors.push({
                        type: 'validation',
                        message: error,
                        file: undefined,
                        originalError: undefined
                    });
                });
            }

            // Generate files
            const fileResults = await this.generateTemplateFiles(
                template,
                enhancedContext,
                generationOptions
            );

            generatedFiles.push(...fileResults.files);
            errors.push(...fileResults.errors);
            warnings.push(...fileResults.warnings);

            this.log(`Resource generation completed. Generated ${generatedFiles.length} files.`);

            return {
                success: errors.length === 0,
                files: generatedFiles,
                errors,
                warnings,
                metadata: {
                    templateId,
                    context: enhancedContext,
                    duration: Date.now() - startTime,
                    timestamp: new Date()
                }
            };

        } catch (error) {
            errors.push({
                type: 'system',
                message: error instanceof Error ? error.message : 'Unknown error',
                originalError: error instanceof Error ? error : undefined
            });

            return {
                success: false,
                files: generatedFiles,
                errors,
                warnings,
                metadata: {
                    templateId: options.templateId || 'crud',
                    context: {} as TemplateContext,
                    duration: Date.now() - startTime,
                    timestamp: new Date()
                }
            };
        }
    }

    /**
     * Generate configuration files from template
     */
    async generateConfig(
        type: string,
        options: Partial<ConfigGenerationOptions> = {}
    ): Promise<GenerationResult> {
        const startTime = Date.now();
        const errors: GenerationError[] = [];
        const warnings: string[] = [];
        const generatedFiles: string[] = [];

        try {
            // Validate inputs
            this.validateConfigInputs(type);

            // Get template definition
            const templateId = options.templateId || type;
            const template = this.registry.get(templateId);
            if (!template) {
                throw new Error(`Config template '${templateId}' not found`);
            }

            if (template.category !== 'config') {
                throw new Error(`Template '${templateId}' is not a config template`);
            }

            this.log(`Starting config generation: ${type} using template ${templateId}`);

            // Build generation options
            const generationOptions: ConfigGenerationOptions = {
                templateId,
                type,
                outputDir: options.outputDir || '.',
                overwrite: options.overwrite || false,
                createDirs: options.createDirs !== false,
                encoding: options.encoding || 'utf8',
                variables: options.variables || {},
                context: options.context || {}
            };

            // Build template context
            const context = ContextBuilder.buildConfigContext(generationOptions);
            const enhancedContext = ContextBuilder.enhanceContext(context, generationOptions.context);

            // Generate files
            const fileResults = await this.generateTemplateFiles(
                template,
                enhancedContext,
                generationOptions
            );

            generatedFiles.push(...fileResults.files);
            errors.push(...fileResults.errors);
            warnings.push(...fileResults.warnings);

            this.log(`Config generation completed. Generated ${generatedFiles.length} files.`);

            return {
                success: errors.length === 0,
                files: generatedFiles,
                errors,
                warnings,
                metadata: {
                    templateId,
                    context: enhancedContext,
                    duration: Date.now() - startTime,
                    timestamp: new Date()
                }
            };

        } catch (error) {
            errors.push({
                type: 'system',
                message: error instanceof Error ? error.message : 'Unknown error',
                originalError: error instanceof Error ? error : undefined
            });

            return {
                success: false,
                files: generatedFiles,
                errors,
                warnings,
                metadata: {
                    templateId: options.templateId || type,
                    context: {} as TemplateContext,
                    duration: Date.now() - startTime,
                    timestamp: new Date()
                }
            };
        }
    }

    /**
     * Load templates from a directory
     */
    async loadTemplates(directoryPath: string): Promise<void> {
        try {
            await this.registry.loadFromDirectory(directoryPath);
            this.log(`Loaded templates from: ${directoryPath}`);
        } catch (error) {
            throw new Error(
                `Failed to load templates: ${error instanceof Error ? error.message : 'Unknown error'}`
            );
        }
    }

    /**
     * Get available templates
     */
    getTemplates(): TemplateDefinition[] {
        return this.registry.list();
    }

    /**
     * Get templates by category
     */
    getTemplatesByCategory(category: TemplateDefinition['category']): TemplateDefinition[] {
        return this.registry.listByCategory(category);
    }

    /**
     * Check if template exists
     */
    hasTemplate(templateId: string): boolean {
        return this.registry.exists(templateId);
    }

    /**
     * Register a custom helper function
     */
    registerHelper(name: string, helper: (...args: any[]) => any): void {
        this.engine.registerHelper(name, helper);
    }

    /**
     * Generate files from template definition
     */
    private async generateTemplateFiles(
        template: TemplateDefinition,
        context: TemplateContext,
        options: RenderOptions
    ): Promise<{ files: string[]; errors: GenerationError[]; warnings: string[] }> {
        const files: string[] = [];
        const errors: GenerationError[] = [];
        const warnings: string[] = [];

        // Ensure output directory exists
        if (options.createDirs) {
            await fs.ensureDir(options.outputDir);
        }

        // Process each template file
        for (const file of template.files) {
            try {
                // Skip file if condition is not met
                if (file.condition && !this.evaluateCondition(file.condition, context)) {
                    this.log(`Skipping file ${file.source} (condition not met)`);
                    continue;
                }

                // Resolve template file path
                const templateFilePath = path.join(template.path, file.source);

                // Render target path with context
                const renderedTargetPath = await this.engine.renderString(file.target, context);
                const outputFilePath = path.resolve(options.outputDir, renderedTargetPath);

                // Check if file exists and handle overwrite
                if (await fs.pathExists(outputFilePath) && !options.overwrite) {
                    warnings.push(`File already exists (skipped): ${outputFilePath}`);
                    continue;
                }

                // Ensure target directory exists
                const targetDir = path.dirname(outputFilePath);
                if (options.createDirs) {
                    await fs.ensureDir(targetDir);
                }

                // Render template content
                const renderedContent = await this.engine.renderFile(templateFilePath, context);

                // Write file
                await fs.writeFile(outputFilePath, renderedContent, {
                    encoding: options.encoding || 'utf8'
                });

                // Set executable permission if needed
                if (file.executable) {
                    await fs.chmod(outputFilePath, 0o755);
                }

                files.push(outputFilePath);
                this.log(`Generated: ${outputFilePath}`);

            } catch (error) {
                errors.push({
                    type: 'file',
                    message: `Failed to generate file ${file.source}: ${error instanceof Error ? error.message : 'Unknown error'
                        }`,
                    file: file.source,
                    originalError: error instanceof Error ? error : undefined
                });
            }
        }

        return { files, errors, warnings };
    }

    /**
     * Evaluate a condition string against context
     */
    private evaluateCondition(condition: string, context: TemplateContext): boolean {
        try {
            // Simple condition evaluation - can be enhanced
            // For now, just check if variable exists and is truthy
            const parts = condition.split('.');
            let value: any = context;

            for (const part of parts) {
                value = value?.[part];
            }

            return !!value;
        } catch {
            return false;
        }
    }

    /**
     * Validation methods
     */
    private validateProjectInputs(name: string, templateId: string): void {
        if (!name || typeof name !== 'string' || name.trim().length === 0) {
            throw new Error('Project name is required and must be a non-empty string');
        }

        if (!templateId || typeof templateId !== 'string' || templateId.trim().length === 0) {
            throw new Error('Template ID is required and must be a non-empty string');
        }

        // Validate name format
        if (!/^[a-zA-Z][a-zA-Z0-9-_]*$/.test(name)) {
            throw new Error('Project name must start with a letter and contain only letters, numbers, hyphens, and underscores');
        }
    }

    private validateResourceInputs(name: string, fields: ResourceGenerationOptions['fields']): void {
        if (!name || typeof name !== 'string' || name.trim().length === 0) {
            throw new Error('Resource name is required and must be a non-empty string');
        }

        if (!Array.isArray(fields) || fields.length === 0) {
            throw new Error('Resource fields are required and must be a non-empty array');
        }

        // Validate name format
        if (!/^[a-zA-Z][a-zA-Z0-9-_]*$/.test(name)) {
            throw new Error('Resource name must start with a letter and contain only letters, numbers, hyphens, and underscores');
        }

        // Validate each field
        fields.forEach((field, index) => {
            if (!field.name || typeof field.name !== 'string') {
                throw new Error(`Field ${index}: name is required and must be a string`);
            }
            if (!field.type || typeof field.type !== 'string') {
                throw new Error(`Field ${index}: type is required and must be a string`);
            }
        });
    }

    private validateConfigInputs(type: string): void {
        if (!type || typeof type !== 'string' || type.trim().length === 0) {
            throw new Error('Config type is required and must be a non-empty string');
        }
    }

    /**
     * Logging helper
     */
    private log(message: string): void {
        if (this.verbose) {
            console.log(`[Generator] ${message}`);
        }
    }
}
