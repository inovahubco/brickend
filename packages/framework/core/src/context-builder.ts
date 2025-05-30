import { templateHelpers } from './helpers/index.js';
import type {
    ProjectConfig,
    ProjectContext,
    ContextBuildOptions,
    Entity,
    TemplateConfig,
    TemplateVariable
} from './types/index.js';

/**
 * Simple logger interface for context builder
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
 * Context Builder - Creates rich context for template rendering
 */
export class ContextBuilder {
    private readonly logger: Logger;

    constructor(options: { logger?: Logger } = {}) {
        this.logger = options.logger || createDefaultLogger();
    }

    /**
     * Build context from project configuration
     * @param options - Context build options
     * @returns Rich project context for template rendering
     */
    async buildContext(options: ContextBuildOptions): Promise<ProjectContext> {
        const { config, template, overrides = {}, validateEntities = true, validateVariables = true } = options;

        this.logger.debug('Building context', {
            templateName: template.name,
            projectName: config?.name || 'unknown'
        });

        // Start with base context
        const context: ProjectContext = {
            project: this.buildProjectInfo(config, template),
            template: this.buildTemplateInfo(template),
            entities: [],
            features: {},
            env: {},
            variables: {},
            utils: templateHelpers,
            timestamps: this.buildTimestamps(),
        };

        // Add entities if provided
        if (config?.entities && config.entities.length > 0) {
            context.entities = validateEntities
                ? await this.validateAndProcessEntities(config.entities)
                : config.entities;
        }

        // Build features map
        context.features = this.buildFeaturesMap(config?.features || [], template.features || []);

        // Add environment variables
        context.env = this.buildEnvironmentVariables(config?.environment || {});

        // Process template variables
        context.variables = await this.buildTemplateVariables(
            template.variables,
            config?.variables || {},
            validateVariables
        );

        // Apply overrides
        if (Object.keys(overrides).length > 0) {
            this.applyOverrides(context, overrides);
        }

        this.logger.debug('Context built successfully', {
            entitiesCount: context.entities.length,
            featuresCount: Object.keys(context.features).length,
            variablesCount: Object.keys(context.variables).length
        });

        return context;
    }

    /**
     * Build context from CLI prompts (interactive mode)
     * @param template - Template configuration
     * @param answers - Answers from CLI prompts
     * @returns Project context
     */
    async buildContextFromPrompts(
        template: TemplateConfig,
        answers: Record<string, any>
    ): Promise<ProjectContext> {
        this.logger.debug('Building context from prompts', { templateName: template.name });

        // Convert prompt answers to project config format
        const config: ProjectConfig = {
            name: answers.projectName || 'my-project',
            description: answers.description || '',
            version: answers.version || '1.0.0',
            template: template.name,
            provider: template.provider,
            entities: answers.entities || [],
            features: answers.features || [],
            variables: answers.variables || {},
            environment: answers.environment || {},
        };

        return this.buildContext({
            config,
            template,
            validateEntities: true,
            validateVariables: true,
        });
    }

    /**
     * Build project information section
     * @param config - Project configuration
     * @param template - Template configuration
     * @returns Project info object
     */
    private buildProjectInfo(config: ProjectConfig | undefined, template: TemplateConfig) {
        return {
            name: config?.name || 'my-project',
            description: config?.description || `Project generated with ${template.name} template`,
            version: config?.version || '1.0.0',
            author: config?.variables?.author as string || process.env.USER || process.env.USERNAME || 'Developer',
        };
    }

    /**
     * Build template information section
     * @param template - Template configuration
     * @returns Template info object
     */
    private buildTemplateInfo(template: TemplateConfig) {
        return {
            name: template.name,
            version: template.version,
            provider: template.provider,
        };
    }

    /**
     * Build timestamps section
     * @returns Timestamps object
     */
    private buildTimestamps() {
        const now = new Date();
        return {
            generated: now,
            generatedISO: now.toISOString(),
            year: now.getFullYear(),
        };
    }

    /**
     * Build features map from project and template features
     * @param projectFeatures - Features requested in project config
     * @param templateFeatures - Features supported by template
     * @returns Features map
     */
    private buildFeaturesMap(projectFeatures: string[], templateFeatures: string[]): Record<string, boolean> {
        const features: Record<string, boolean> = {};

        // Start with all template features as false
        for (const feature of templateFeatures) {
            features[feature] = false;
        }

        // Enable requested project features
        for (const feature of projectFeatures) {
            if (templateFeatures.includes(feature)) {
                features[feature] = true;
            } else {
                this.logger.warn('Feature not supported by template', {
                    feature,
                    supportedFeatures: templateFeatures
                });
            }
        }

        return features;
    }

    /**
     * Build environment variables map
     * @param envConfig - Environment configuration
     * @returns Environment variables map
     */
    private buildEnvironmentVariables(envConfig: Record<string, string>): Record<string, string> {
        const env: Record<string, string> = {};

        // Add configuration environment variables
        Object.assign(env, envConfig);

        // Add some default environment variables
        env.NODE_ENV = env.NODE_ENV || 'development';
        env.PORT = env.PORT || '3000';

        return env;
    }

    /**
     * Process and validate template variables
     * @param templateVariables - Variables defined in template
     * @param providedVariables - Variables provided in config
     * @param validate - Whether to validate variables
     * @returns Processed variables map
     */
    private async buildTemplateVariables(
        templateVariables: TemplateVariable[],
        providedVariables: Record<string, any>,
        validate: boolean
    ): Promise<Record<string, any>> {
        const variables: Record<string, any> = {};

        for (const templateVar of templateVariables) {
            const { name, type, required, defaultValue, validation } = templateVar;

            let value = providedVariables[name];

            // Use default value if not provided
            if (value === undefined && defaultValue !== undefined) {
                value = defaultValue;
            }

            // Check required variables
            if (required && value === undefined) {
                throw new Error(`Required template variable '${name}' is not provided`);
            }

            // Skip validation if not required
            if (!validate) {
                variables[name] = value;
                continue;
            }

            // Validate variable if provided
            if (value !== undefined) {
                try {
                    variables[name] = await this.validateTemplateVariable(templateVar, value);
                } catch (error) {
                    throw new Error(`Validation failed for variable '${name}': ${error instanceof Error ? error.message : 'Unknown error'}`);
                }
            }
        }

        return variables;
    }

    /**
     * Validate and process entities
     * @param entities - Raw entities from config
     * @returns Validated and processed entities
     */
    private async validateAndProcessEntities(entities: Entity[]): Promise<Entity[]> {
        const processedEntities: Entity[] = [];

        for (const entity of entities) {
            try {
                const processedEntity = await this.validateAndProcessEntity(entity);
                processedEntities.push(processedEntity);
            } catch (error) {
                throw new Error(`Validation failed for entity '${entity.name}': ${error instanceof Error ? error.message : 'Unknown error'}`);
            }
        }

        // Validate entity relationships
        this.validateEntityRelationships(processedEntities);

        return processedEntities;
    }

    /**
     * Validate and process a single entity
     * @param entity - Entity to validate
     * @returns Processed entity
     */
    private async validateAndProcessEntity(entity: Entity): Promise<Entity> {
        // Validate entity name
        if (!/^[A-Z][a-zA-Z0-9]*$/.test(entity.name)) {
            throw new Error(`Entity name '${entity.name}' must be PascalCase and start with uppercase letter`);
        }

        // Validate fields
        for (const field of entity.fields) {
            if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(field.name)) {
                throw new Error(`Field name '${field.name}' must be a valid identifier`);
            }

            // Validate field type
            const validTypes = ['string', 'number', 'boolean', 'date', 'datetime', 'email', 'url', 'uuid', 'json', 'text', 'integer', 'float', 'decimal'];
            if (!validTypes.includes(field.type)) {
                throw new Error(`Invalid field type '${field.type}' for field '${field.name}'`);
            }
        }

        // Ensure entity has at least one field
        if (entity.fields.length === 0) {
            throw new Error('Entity must have at least one field');
        }

        // Add default options if not provided
        const processedEntity: Entity = {
            ...entity,
            options: {
                timestamps: true,
                softDelete: false,
                auditLog: false,
                rowLevelSecurity: false,
                ...entity.options,
            },
        };

        return processedEntity;
    }

    /**
     * Validate entity relationships
     * @param entities - All entities to validate relationships for
     */
    private validateEntityRelationships(entities: Entity[]): void {
        const entityNames = new Set(entities.map(e => e.name));

        for (const entity of entities) {
            if (!entity.relationships) continue;

            for (const [relationName, relationship] of Object.entries(entity.relationships)) {
                // Check if target entity exists
                if (!entityNames.has(relationship.target)) {
                    throw new Error(`Entity '${entity.name}' has relationship '${relationName}' targeting non-existent entity '${relationship.target}'`);
                }

                // Validate relationship type
                const validTypes = ['oneToOne', 'oneToMany', 'manyToOne', 'manyToMany'];
                if (!validTypes.includes(relationship.type)) {
                    throw new Error(`Invalid relationship type '${relationship.type}' in entity '${entity.name}'`);
                }
            }
        }
    }

    /**
     * Validate a template variable value
     * @param templateVar - Template variable definition
     * @param value - Value to validate
     * @returns Validated value
     */
    private async validateTemplateVariable(templateVar: TemplateVariable, value: any): Promise<any> {
        const { name, type, validation } = templateVar;

        // Type validation
        switch (type) {
            case 'string':
                if (typeof value !== 'string') {
                    throw new Error(`Variable '${name}' must be a string`);
                }
                break;
            case 'number':
                if (typeof value !== 'number') {
                    throw new Error(`Variable '${name}' must be a number`);
                }
                break;
            case 'boolean':
                if (typeof value !== 'boolean') {
                    throw new Error(`Variable '${name}' must be a boolean`);
                }
                break;
            case 'array':
                if (!Array.isArray(value)) {
                    throw new Error(`Variable '${name}' must be an array`);
                }
                break;
            case 'object':
                if (typeof value !== 'object' || value === null || Array.isArray(value)) {
                    throw new Error(`Variable '${name}' must be an object`);
                }
                break;
        }

        // Additional validation rules
        if (validation && type === 'string' && typeof value === 'string') {
            if (validation.minLength && value.length < validation.minLength) {
                throw new Error(`Variable '${name}' must be at least ${validation.minLength} characters long`);
            }
            if (validation.maxLength && value.length > validation.maxLength) {
                throw new Error(`Variable '${name}' must be at most ${validation.maxLength} characters long`);
            }
            if (validation.pattern && !new RegExp(validation.pattern).test(value)) {
                throw new Error(`Variable '${name}' does not match required pattern`);
            }
            if (validation.enum && !validation.enum.includes(value)) {
                throw new Error(`Variable '${name}' must be one of: ${validation.enum.join(', ')}`);
            }
        }

        if (validation && type === 'number' && typeof value === 'number') {
            if (validation.min !== undefined && value < validation.min) {
                throw new Error(`Variable '${name}' must be at least ${validation.min}`);
            }
            if (validation.max !== undefined && value > validation.max) {
                throw new Error(`Variable '${name}' must be at most ${validation.max}`);
            }
        }

        return value;
    }

    /**
     * Apply overrides to context
     * @param context - Context to modify
     * @param overrides - Override values
     */
    private applyOverrides(context: ProjectContext, overrides: Record<string, any>): void {
        for (const [key, value] of Object.entries(overrides)) {
            if (key === 'project' && typeof value === 'object') {
                Object.assign(context.project, value);
            } else if (key === 'features' && typeof value === 'object') {
                Object.assign(context.features, value);
            } else if (key === 'env' && typeof value === 'object') {
                Object.assign(context.env, value);
            } else if (key === 'variables' && typeof value === 'object') {
                Object.assign(context.variables, value);
            } else {
                // Direct override
                (context as any)[key] = value;
            }
        }

        this.logger.debug('Applied overrides to context', { overrides });
    }

    /**
     * Validate context completeness
     * @param context - Context to validate
     * @param template - Template configuration
     * @returns Validation result
     */
    validateContext(context: ProjectContext, template: TemplateConfig): { valid: boolean; errors: string[] } {
        const errors: string[] = [];

        // Check required template variables
        for (const templateVar of template.variables) {
            if (templateVar.required && context.variables[templateVar.name] === undefined) {
                errors.push(`Required variable '${templateVar.name}' is missing`);
            }
        }

        // Check if entities are required but missing
        if (template.supports?.entities && context.entities.length === 0) {
            errors.push('Template requires entities but none were provided');
        }

        // Validate project name
        if (!context.project.name || context.project.name.trim() === '') {
            errors.push('Project name is required');
        }

        return {
            valid: errors.length === 0,
            errors,
        };
    }

    /**
     * Get context summary for logging/debugging
     * @param context - Context to summarize
     * @returns Context summary
     */
    getContextSummary(context: ProjectContext): Record<string, any> {
        return {
            projectName: context.project.name,
            templateName: context.template.name,
            entitiesCount: context.entities.length,
            entityNames: context.entities.map(e => e.name),
            enabledFeatures: Object.entries(context.features)
                .filter(([, enabled]) => enabled)
                .map(([name]) => name),
            variableCount: Object.keys(context.variables).length,
            envVariableCount: Object.keys(context.env).length,
        };
    }
}