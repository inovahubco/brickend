/**
 * Context Builder for creating template contexts
 */

import type {
    TemplateContext,
    TemplateField,
    ProjectGenerationOptions,
    ResourceGenerationOptions,
    ConfigGenerationOptions
} from '../types/index.js';

/**
 * Context Builder utility class
 */
export class ContextBuilder {
    /**
     * Build context for project generation
     */
    static buildProjectContext(options: ProjectGenerationOptions): TemplateContext {
        const names = this.buildNameVariations(options.name);

        return {
            name: options.name,
            names,
            variables: options.variables || {},
            metadata: {
                name: options.templateId,
                description: `Generated project: ${options.name}`,
                version: '1.0.0'
            }
        };
    }

    /**
     * Build context for resource generation
     */
    static buildResourceContext(options: ResourceGenerationOptions): TemplateContext {
        const names = this.buildNameVariations(options.name);

        return {
            name: options.name,
            names,
            fields: options.fields,
            variables: options.variables || {},
            metadata: {
                name: options.templateId || 'resource',
                description: `Generated resource: ${options.name}`,
                version: '1.0.0'
            }
        };
    }

    /**
     * Build context for config generation
     */
    static buildConfigContext(options: ConfigGenerationOptions): TemplateContext {
        const names = this.buildNameVariations(options.type);

        return {
            name: options.type,
            names,
            variables: options.variables || {},
            metadata: {
                name: options.templateId,
                description: `Generated config: ${options.type}`,
                version: '1.0.0'
            }
        };
    }

    /**
     * Build name variations for a given name
     */
    static buildNameVariations(name: string): TemplateContext['names'] {
        return {
            camelCase: this.toCamelCase(name),
            pascalCase: this.toPascalCase(name),
            kebabCase: this.toKebabCase(name),
            snakeCase: this.toSnakeCase(name),
            plural: this.pluralize(name),
            singular: this.singularize(name)
        };
    }

    /**
     * Create enhanced context with additional helpers
     */
    static enhanceContext(baseContext: TemplateContext, additional: Record<string, any> = {}): TemplateContext {
        return {
            ...baseContext,
            variables: {
                ...baseContext.variables,
                ...additional,
                // Add common utilities
                timestamp: new Date().toISOString(),
                year: new Date().getFullYear(),
                date: new Date().toLocaleDateString(),
                // Field utilities
                ...(baseContext.fields && {
                    hasRequiredFields: baseContext.fields.some(f => f.required),
                    fieldCount: baseContext.fields.length,
                    fieldTypes: [...new Set(baseContext.fields.map(f => f.type))],
                    stringFields: baseContext.fields.filter(f => f.type === 'string'),
                    numberFields: baseContext.fields.filter(f => f.type === 'number'),
                    booleanFields: baseContext.fields.filter(f => f.type === 'boolean')
                })
            }
        };
    }

    /**
     * Validate template context
     */
    static validateContext(context: TemplateContext): string[] {
        const errors: string[] = [];

        if (!context.name || typeof context.name !== 'string') {
            errors.push('Context name is required and must be a string');
        }

        if (!context.names || typeof context.names !== 'object') {
            errors.push('Context names object is required');
        }

        if (context.fields && !Array.isArray(context.fields)) {
            errors.push('Context fields must be an array');
        }

        if (context.fields) {
            context.fields.forEach((field, index) => {
                if (!field.name || typeof field.name !== 'string') {
                    errors.push(`Field ${index}: name is required and must be a string`);
                }
                if (!field.type || typeof field.type !== 'string') {
                    errors.push(`Field ${index}: type is required and must be a string`);
                }
            });
        }

        return errors;
    }

    // String transformation utilities
    private static toCamelCase(str: string): string {
        return str.replace(/[-_\s]+(.)?/g, (_, c) => (c ? c.toUpperCase() : ''));
    }

    private static toPascalCase(str: string): string {
        const camelCased = this.toCamelCase(str);
        return camelCased.charAt(0).toUpperCase() + camelCased.slice(1);
    }

    private static toKebabCase(str: string): string {
        return str
            .replace(/([a-z])([A-Z])/g, '$1-$2')
            .replace(/[\s_]+/g, '-')
            .toLowerCase();
    }

    private static toSnakeCase(str: string): string {
        return str
            .replace(/([a-z])([A-Z])/g, '$1_$2')
            .replace(/[\s-]+/g, '_')
            .toLowerCase();
    }

    private static pluralize(str: string): string {
        if (str.endsWith('y')) {
            return str.slice(0, -1) + 'ies';
        }
        if (str.endsWith('s') || str.endsWith('sh') || str.endsWith('ch') || str.endsWith('x') || str.endsWith('z')) {
            return str + 'es';
        }
        return str + 's';
    }

    private static singularize(str: string): string {
        if (str.endsWith('ies')) {
            return str.slice(0, -3) + 'y';
        }
        if (str.endsWith('es')) {
            return str.slice(0, -2);
        }
        if (str.endsWith('s') && !str.endsWith('ss')) {
            return str.slice(0, -1);
        }
        return str;
    }
}