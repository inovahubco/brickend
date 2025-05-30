import ejs from 'ejs';
import prettier from 'prettier';
import { fileUtils, pathUtils } from './helpers/index.js';
import { TemplateRegistry } from './registry.js';
import { ContextBuilder } from './context-builder.js';
import type {
    ProjectConfig,
    ProjectContext,
    GeneratedProject,
    GeneratedFile,
    GenerationOptions,
    TemplateConfig,
    PostProcessor
} from './types/index.js';

/**
 * Simple logger interface for template engine
 */
interface Logger {
    debug(message: string, data?: any): void;
    info(message: string, data?: any): void;
    warn(message: string, data?: any): void;
    error(message: string, data?: any): void;
}

/**
 * Default console-based logger
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

/**
 * Template Engine - Orchestrates the entire code generation process
 */
export class TemplateEngine {
    private readonly registry: TemplateRegistry;
    private readonly contextBuilder: ContextBuilder;
    private readonly logger: Logger;

    constructor(options: {
        registry?: TemplateRegistry;
        contextBuilder?: ContextBuilder;
        logger?: Logger;
    } = {}) {
        this.registry = options.registry || new TemplateRegistry();
        this.contextBuilder = options.contextBuilder || new ContextBuilder();
        this.logger = options.logger || createDefaultLogger();
    }

    /**
     * Generate project from template
     * @param templateName - Name of template to use
     * @param config - Project configuration
     * @param options - Generation options
     * @returns Generated project
     */
    async generateProject(
        templateName: string,
        config: ProjectConfig,
        options: GenerationOptions
    ): Promise<GeneratedProject> {
        const startTime = Date.now();

        this.logger.info('Starting project generation', {
            templateName,
            projectName: config.name,
            outputPath: options.outputPath
        });

        try {
            // Validate options
            this.validateGenerationOptions(options);

            // Load template
            const template = await this.loadTemplate(templateName);

            // Build context
            const context = await this.buildContext(config, template, options);

            // Validate context
            this.validateContext(context, template);

            // Generate files
            const generatedFiles = options.dryRun
                ? await this.generateFilesDryRun(template, context, options)
                : await this.generateFiles(template, context, options);

            // Create result
            const result: GeneratedProject = {
                name: config.name,
                path: options.outputPath,
                template: templateName,
                files: generatedFiles,
                generatedAt: new Date(),
                brickendVersion: this.getBrickendVersion(),
                templateVersion: template.version,
                instructions: this.buildInstructions(template, context),
                validation: { success: true }
            };

            const endTime = Date.now();
            this.logger.info('Project generation completed', {
                projectName: config.name,
                filesGenerated: generatedFiles.length,
                duration: `${endTime - startTime}ms`,
                dryRun: options.dryRun
            });

            return result;

        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            this.logger.error('Project generation failed', {
                templateName,
                projectName: config.name,
                error: errorMessage
            });

            return {
                name: config.name,
                path: options.outputPath,
                template: templateName,
                files: [],
                generatedAt: new Date(),
                brickendVersion: this.getBrickendVersion(),
                templateVersion: '0.0.0',
                validation: {
                    success: false,
                    errors: [errorMessage]
                }
            };
        }
    }

    /**
     * Generate project from CLI prompts
     * @param templateName - Template name
     * @param answers - CLI prompt answers
     * @param options - Generation options
     * @returns Generated project
     */
    async generateFromPrompts(
        templateName: string,
        answers: Record<string, any>,
        options: GenerationOptions
    ): Promise<GeneratedProject> {
        // Load template first
        const template = await this.loadTemplate(templateName);

        // Build context from prompts
        const context = await this.contextBuilder.buildContextFromPrompts(template, answers);

        // Convert context back to config format for generateProject
        const config: ProjectConfig = {
            name: context.project.name,
            description: context.project.description,
            version: context.project.version,
            template: templateName,
            provider: template.provider,
            entities: context.entities,
            features: Object.entries(context.features)
                .filter(([, enabled]) => enabled)
                .map(([name]) => name),
            variables: context.variables,
            environment: context.env,
        };

        return this.generateProject(templateName, config, options);
    }

    /**
     * Load template from registry
     * @param templateName - Template name
     * @returns Template configuration
     */
    private async loadTemplate(templateName: string): Promise<TemplateConfig> {
        const template = await this.registry.getTemplate(templateName);

        if (!template) {
            throw new Error(`Template '${templateName}' not found`);
        }

        if (!template.isValid) {
            throw new Error(`Template '${templateName}' is invalid: ${template.validationErrors?.join(', ')}`);
        }

        this.logger.debug('Template loaded', {
            templateName: template.config.name,
            version: template.config.version,
            category: template.config.category
        });

        return template.config;
    }

    /**
     * Build context for template rendering
     * @param config - Project configuration
     * @param template - Template configuration
     * @param options - Generation options
     * @returns Project context
     */
    private async buildContext(
        config: ProjectConfig,
        template: TemplateConfig,
        options: GenerationOptions
    ): Promise<ProjectContext> {
        const context = await this.contextBuilder.buildContext({
            config,
            template,
            validateEntities: !options.skipValidation,
            validateVariables: !options.skipValidation,
        });

        this.logger.debug('Context built', this.contextBuilder.getContextSummary(context));

        return context;
    }

    /**
     * Validate context against template requirements
     * @param context - Project context
     * @param template - Template configuration
     */
    private validateContext(context: ProjectContext, template: TemplateConfig): void {
        const validation = this.contextBuilder.validateContext(context, template);

        if (!validation.valid) {
            throw new Error(`Context validation failed: ${validation.errors.join(', ')}`);
        }
    }

    /**
     * Generate all files from template
     * @param template - Template configuration
     * @param context - Project context
     * @param options - Generation options
     * @returns Array of generated files
     */
    private async generateFiles(
        template: TemplateConfig,
        context: ProjectContext,
        options: GenerationOptions
    ): Promise<GeneratedFile[]> {
        const templateMetadata = await this.registry.getTemplate(template.name);
        if (!templateMetadata) {
            throw new Error(`Template metadata not found for '${template.name}'`);
        }

        const templatePath = templateMetadata.path;
        const generatedFiles: GeneratedFile[] = [];

        // Get files to process
        const filesToProcess = template.files && template.files.length > 0
            ? await this.getExplicitFiles(templatePath, template.files, context)
            : await this.getImplicitFiles(templatePath, context);

        this.logger.info('Processing files', { count: filesToProcess.length });

        // Process each file
        for (const fileInfo of filesToProcess) {
            try {
                const generatedFile = await this.processFile(
                    templatePath,
                    fileInfo.sourcePath,
                    fileInfo.destinationPath,
                    context,
                    options
                );

                if (generatedFile) {
                    generatedFiles.push(generatedFile);
                }
            } catch (error) {
                const errorMessage = error instanceof Error ? error.message : 'Unknown error';
                this.logger.error('Failed to process file', {
                    sourcePath: fileInfo.sourcePath,
                    error: errorMessage
                });

                if (!options.skipValidation) {
                    throw error;
                }
            }
        }

        // Apply post-processors if not skipped
        if (!options.skipPostProcessors && template.postProcessors) {
            await this.applyPostProcessors(generatedFiles, template.postProcessors, options);
        }

        return generatedFiles;
    }

    /**
     * Generate files in dry-run mode (no actual file writing)
     * @param template - Template configuration
     * @param context - Project context
     * @param options - Generation options
     * @returns Array of files that would be generated
     */
    private async generateFilesDryRun(
        template: TemplateConfig,
        context: ProjectContext,
        options: GenerationOptions
    ): Promise<GeneratedFile[]> {
        this.logger.info('Running in dry-run mode - no files will be written');

        // Same logic as generateFiles but without actual file writing
        const files = await this.generateFiles(template, context, {
            ...options,
            dryRun: false // Temporarily disable to get through processing
        });

        // Log what would be generated
        for (const file of files) {
            this.logger.info('Would generate file', { path: file.path });
        }

        return files;
    }

    /**
     * Get files from explicit file instructions
     * @param templatePath - Template directory path
     * @param fileInstructions - Explicit file instructions
     * @param context - Project context
     * @returns File processing info
     */
    private async getExplicitFiles(
        templatePath: string,
        fileInstructions: any[],
        context: ProjectContext
    ): Promise<Array<{ sourcePath: string; destinationPath: string }>> {
        const files: Array<{ sourcePath: string; destinationPath: string }> = [];

        for (const instruction of fileInstructions) {
            // Check condition if specified
            if (instruction.condition) {
                try {
                    const shouldInclude = this.evaluateCondition(instruction.condition, context);
                    if (!shouldInclude) {
                        this.logger.debug('Skipping file due to condition', {
                            file: instruction.source,
                            condition: instruction.condition
                        });
                        continue;
                    }
                } catch (error) {
                    this.logger.warn('Failed to evaluate condition, including file', {
                        file: instruction.source,
                        condition: instruction.condition,
                        error: error instanceof Error ? error.message : 'Unknown error'
                    });
                }
            }

            // Process destination path template
            const destinationPath = pathUtils.parsePathTemplate(instruction.destination, context);

            files.push({
                sourcePath: pathUtils.joinPath(templatePath, instruction.source),
                destinationPath
            });
        }

        return files;
    }

    /**
     * Get files by discovering all .ejs files in template
     * @param templatePath - Template directory path
     * @param context - Project context
     * @returns File processing info
     */
    private async getImplicitFiles(
        templatePath: string,
        context: ProjectContext
    ): Promise<Array<{ sourcePath: string; destinationPath: string }>> {
        const templateFiles = await fileUtils.templateFiles.listTemplates(templatePath);
        const files: Array<{ sourcePath: string; destinationPath: string }> = [];

        for (const templateFile of templateFiles) {
            const sourcePath = pathUtils.joinPath(templatePath, templateFile);

            // Process path templates (e.g., {{entity.name}}/api.ts.ejs)
            let destinationPath = pathUtils.parsePathTemplate(templateFile, context);

            // Remove .ejs extension
            destinationPath = pathUtils.getOutputFileName(destinationPath);

            files.push({ sourcePath, destinationPath });
        }

        return files;
    }

    /**
     * Process a single template file
     * @param templatePath - Base template path
     * @param sourcePath - Source file path
     * @param destinationPath - Destination file path
     * @param context - Project context
     * @param options - Generation options
     * @returns Generated file or null if skipped
     */
    private async processFile(
        templatePath: string,
        sourcePath: string,
        destinationPath: string,
        context: ProjectContext,
        options: GenerationOptions
    ): Promise<GeneratedFile | null> {
        // Check if source file exists
        if (!(await fileUtils.exists(sourcePath))) {
            throw new Error(`Template file not found: ${sourcePath}`);
        }

        // Read template content
        const templateContent = await fileUtils.readFile(sourcePath);

        // Check if file should be processed based on extension
        if (!sourcePath.endsWith('.ejs')) {
            // Static file, just copy
            this.logger.debug('Copying static file', { sourcePath, destinationPath });

            const content = await fileUtils.readFile(sourcePath);
            return {
                path: destinationPath,
                content,
                encoding: 'utf8'
            };
        }

        // Render EJS template
        let renderedContent: string;
        try {
            renderedContent = await ejs.render(templateContent, context, {
                filename: sourcePath,
                async: true,
                root: templatePath
            });
        } catch (error) {
            throw new Error(`EJS rendering failed for ${sourcePath}: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }

        // Check if output file already exists and overwrite is disabled
        const outputPath = pathUtils.joinPath(options.outputPath, destinationPath);
        if (!options.overwrite && await fileUtils.exists(outputPath)) {
            this.logger.warn('File already exists, skipping', { path: outputPath });
            return null;
        }

        this.logger.debug('Generated file', {
            sourcePath: pathUtils.getRelativePath(templatePath, sourcePath),
            destinationPath
        });

        return {
            path: destinationPath,
            content: renderedContent,
            encoding: 'utf8'
        };
    }

    /**
     * Apply post-processors to generated files
     * @param files - Generated files
     * @param postProcessors - Post-processor configurations
     * @param options - Generation options
     */
    private async applyPostProcessors(
        files: GeneratedFile[],
        postProcessors: PostProcessor[],
        options: GenerationOptions
    ): Promise<void> {
        for (const processor of postProcessors) {
            try {
                await this.applyPostProcessor(files, processor, options);
            } catch (error) {
                this.logger.warn('Post-processor failed', {
                    processor: processor.name,
                    error: error instanceof Error ? error.message : 'Unknown error'
                });
            }
        }
    }

    /**
     * Apply a single post-processor
     * @param files - Generated files
     * @param processor - Post-processor configuration
     * @param options - Generation options
     */
    private async applyPostProcessor(
        files: GeneratedFile[],
        processor: PostProcessor,
        options: GenerationOptions
    ): Promise<void> {
        this.logger.debug('Applying post-processor', { processor: processor.name });

        // Filter files by patterns if specified
        const filesToProcess = processor.filePatterns
            ? files.filter(file =>
                processor.filePatterns!.some(pattern =>
                    pathUtils.matchesPattern(file.path, pattern)
                )
            )
            : files;

        if (filesToProcess.length === 0) {
            return;
        }

        switch (processor.name) {
            case 'prettier':
                await this.applyPrettierProcessor(filesToProcess, processor.config || {});
                break;

            case 'eslint':
                // ESLint post-processing would go here
                this.logger.debug('ESLint post-processor not implemented yet');
                break;

            default:
                this.logger.warn('Unknown post-processor', { processor: processor.name });
        }
    }

    /**
     * Apply Prettier formatting to files
     * @param files - Files to format
     * @param config - Prettier configuration
     */
    private async applyPrettierProcessor(files: GeneratedFile[], config: Record<string, any>): Promise<void> {
        const prettierConfig = {
            semi: true,
            singleQuote: true,
            tabWidth: 2,
            trailingComma: 'es5' as const,
            ...config
        };

        for (const file of files) {
            try {
                // Only format certain file types
                const ext = pathUtils.getExtension(file.path);
                if (!['.ts', '.tsx', '.js', '.jsx', '.json', '.md'].includes(ext)) {
                    continue;
                }

                const formatted = await prettier.format(file.content, {
                    ...prettierConfig,
                    parser: this.getPrettierParser(ext),
                    filepath: file.path
                });

                file.content = formatted;

                this.logger.debug('Formatted file with Prettier', { path: file.path });
            } catch (error) {
                this.logger.warn('Prettier formatting failed', {
                    path: file.path,
                    error: error instanceof Error ? error.message : 'Unknown error'
                });
            }
        }
    }

    /**
     * Get Prettier parser for file extension
     * @param extension - File extension
     * @returns Prettier parser name
     */
    private getPrettierParser(extension: string): string {
        switch (extension) {
            case '.ts':
            case '.tsx':
                return 'typescript';
            case '.js':
            case '.jsx':
                return 'babel';
            case '.json':
                return 'json';
            case '.md':
                return 'markdown';
            default:
                return 'babel';
        }
    }

    /**
     * Evaluate condition expression
     * @param condition - Condition string (simple EJS expression)
     * @param context - Project context
     * @returns True if condition is met
     */
    private evaluateCondition(condition: string, context: ProjectContext): boolean {
        try {
            // Simple condition evaluation using EJS
            const result = ejs.render(`<%= ${condition} %>`, context);
            return result.trim() === 'true';
        } catch {
            return false;
        }
    }

    /**
     * Build post-generation instructions
     * @param template - Template configuration
     * @param context - Project context
     * @returns Instructions object
     */
    private buildInstructions(template: TemplateConfig, context: ProjectContext) {
        const instructions: any = {};

        // Add dependency installation instructions
        if (template.dependencies || template.devDependencies) {
            instructions.install = ['npm install'];
        }

        // Add setup instructions from template hooks
        if (template.hooks?.afterGenerate) {
            instructions.setup = template.hooks.afterGenerate;
        }

        // Add development instructions
        instructions.dev = ['npm run dev'];

        // Add deployment instructions based on features
        if (context.features.deployment) {
            instructions.deploy = ['npm run build', 'npm run deploy'];
        }

        return instructions;
    }

    /**
     * Validate generation options
     * @param options - Generation options to validate
     */
    private validateGenerationOptions(options: GenerationOptions): void {
        if (!options.outputPath) {
            throw new Error('Output path is required');
        }

        if (!pathUtils.isAbsolute(options.outputPath)) {
            throw new Error('Output path must be absolute');
        }

        // Validate output path safety
        const cwd = process.cwd();
        if (!pathUtils.isSafePath(options.outputPath, cwd)) {
            throw new Error('Output path is outside current working directory');
        }
    }

    /**
     * Get Brickend version
     * @returns Brickend version string
     */
    private getBrickendVersion(): string {
        // This would typically read from package.json
        return process.env.BRICKEND_VERSION || '0.0.1';
    }

    /**
     * Write generated files to disk
     * @param files - Generated files
     * @param outputPath - Base output path
     * @param options - Generation options
     */
    async writeFiles(files: GeneratedFile[], outputPath: string, options: GenerationOptions): Promise<void> {
        if (options.dryRun) {
            this.logger.info('Dry run mode - files not written to disk');
            return;
        }

        this.logger.info('Writing files to disk', {
            count: files.length,
            outputPath
        });

        for (const file of files) {
            const fullPath = pathUtils.joinPath(outputPath, file.path);

            try {
                await fileUtils.writeFile(fullPath, file.content, file.encoding || 'utf8');

                if (file.executable) {
                    await fileUtils.makeExecutable(fullPath);
                }

                this.logger.debug('File written', { path: file.path });
            } catch (error) {
                this.logger.error('Failed to write file', {
                    path: file.path,
                    error: error instanceof Error ? error.message : 'Unknown error'
                });
                throw error;
            }
        }

        this.logger.info('All files written successfully');
    }
}