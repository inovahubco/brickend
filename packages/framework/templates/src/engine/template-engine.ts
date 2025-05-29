/**
 * Template Engine implementation using EJS
 */

import * as ejs from 'ejs';
import * as fs from 'fs-extra';
import type { ITemplateEngine, TemplateContext, TemplateHelper } from '../types/index.js';

/**
 * Template Engine implementation using EJS
 */
export class TemplateEngine implements ITemplateEngine {
    private helpers: Record<string, TemplateHelper> = {};

    constructor() {
        this.registerDefaultHelpers();
    }

    /**
     * Register default helper functions
     */
    private registerDefaultHelpers(): void {
        //
        // String transformation helpers
        //

        // 1) camelCase helper extracted to a local constant
        const camelCaseHelper: TemplateHelper = (str: string) =>
            str.replace(/[-_\s]+(.)?/g, (_, c) => (c ? c.toUpperCase() : ''));
        this.registerHelper('camelCase', camelCaseHelper);

        // 2) pascalCase uses the local camelCaseHelper
        const pascalCaseHelper: TemplateHelper = (str: string) => {
            const camelCased = camelCaseHelper(str);
            return camelCased.charAt(0).toUpperCase() + camelCased.slice(1);
        };
        this.registerHelper('pascalCase', pascalCaseHelper);

        // Other case transformations
        this.registerHelper('kebabCase', (str: string) =>
            str
                .replace(/([a-z])([A-Z])/g, '$1-$2')
                .replace(/[\s_]+/g, '-')
                .toLowerCase()
        );

        this.registerHelper('snakeCase', (str: string) =>
            str
                .replace(/([a-z])([A-Z])/g, '$1_$2')
                .replace(/[\s-]+/g, '_')
                .toLowerCase()
        );

        //
        // Pluralization / Singularization
        //
        this.registerHelper('pluralize', (str: string) => {
            if (str.endsWith('y')) {
                return str.slice(0, -1) + 'ies';
            }
            if (/(s|sh|ch|x|z)$/.test(str)) {
                return str + 'es';
            }
            return str + 's';
        });

        this.registerHelper('singularize', (str: string) => {
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
        });

        //
        // Utility helpers
        //
        this.registerHelper('upper', (str: string) => str.toUpperCase());
        this.registerHelper('lower', (str: string) => str.toLowerCase());
        this.registerHelper('capitalize', (str: string) =>
            str.charAt(0).toUpperCase() + str.slice(1).toLowerCase()
        );

        //
        // Date helpers
        //
        this.registerHelper('now', () => new Date().toISOString());
        this.registerHelper('year', () => new Date().getFullYear());
        this.registerHelper('date', (format?: string) => {
            const now = new Date();
            if (format === 'iso') return now.toISOString();
            if (format === 'short') return now.toLocaleDateString();
            return now.toString();
        });

        //
        // JSON helpers
        //
        this.registerHelper('json', (obj: any, space?: number) =>
            JSON.stringify(obj, null, space ?? 2)
        );

        //
        // Conditional helpers
        //
        this.registerHelper('if', (condition: any, truthyValue: any, falsyValue: any = '') =>
            condition ? truthyValue : falsyValue
        );
        this.registerHelper('unless', (condition: any, truthyValue: any, falsyValue: any = '') =>
            !condition ? truthyValue : falsyValue
        );
    }

    /**
     * Render a template string with context
     */
    async renderString(template: string, context: TemplateContext): Promise<string> {
        try {
            // Prepare EJS context with helpers
            const ejsContext = {
                ...context,
                ...this.helpers
            };

            // Render template with EJS
            const result = await ejs.render(template, ejsContext, {
                async: true,
                rmWhitespace: false
            });

            return result;
        } catch (error) {
            throw new Error(
                `Template rendering failed: ${error instanceof Error ? error.message : 'Unknown error'}`
            );
        }
    }

    /**
     * Render a template file with context
     */
    async renderFile(templatePath: string, context: TemplateContext): Promise<string> {
        try {
            // Check if template file exists
            if (!(await fs.pathExists(templatePath))) {
                throw new Error(`Template file not found: ${templatePath}`);
            }

            // Read template file
            const templateContent = await fs.readFile(templatePath, 'utf-8');

            // Render template
            return this.renderString(templateContent, context);
        } catch (error) {
            throw new Error(
                `Template file rendering failed: ${error instanceof Error ? error.message : 'Unknown error'}`
            );
        }
    }

    /**
     * Register a helper function
     */
    registerHelper(name: string, helper: TemplateHelper): void {
        this.helpers[name] = helper;
    }

    /**
     * Get all registered helpers
     */
    getHelpers(): Record<string, TemplateHelper> {
        return { ...this.helpers };
    }

    /**
     * Remove a helper function
     */
    unregisterHelper(name: string): void {
        delete this.helpers[name];
    }

    /**
     * Check if a helper is registered
     */
    hasHelper(name: string): boolean {
        return name in this.helpers;
    }

    /**
     * Clear all custom helpers (keeps default helpers)
     */
    clearCustomHelpers(): void {
        this.helpers = {};
        this.registerDefaultHelpers();
    }
}
