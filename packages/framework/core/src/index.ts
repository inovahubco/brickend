/**
 * Brickend Core Framework
 * 
 * Main entry point for the Brickend framework core functionality.
 * Provides template-based code generation capabilities.
 */

import { TemplateEngine } from './template-engine.js';
import { TemplateRegistry } from './registry.js';
import { ContextBuilder } from './context-builder.js';

export { TemplateEngine, TemplateRegistry, ContextBuilder };

export * from './types/index.js';

export * from './helpers/index.js';
export { templateHelpers } from './helpers/index.js';

/**
 * Create a new template engine with default configuration
 * @returns Configured template engine instance
 */
export function createTemplateEngine(options: {
    templatePaths?: string[];
    logger?: any;
} = {}): TemplateEngine {
    const registry = new TemplateRegistry({
        templatePaths: options.templatePaths,
        logger: options.logger,
    });

    const contextBuilder = new ContextBuilder({
        logger: options.logger,
    });

    return new TemplateEngine({
        registry,
        contextBuilder,
        logger: options.logger,
    });
}

/**
 * Quick generation function for simple use cases
 * @param templateName - Template to use
 * @param config - Project configuration
 * @param outputPath - Where to generate files
 * @returns Generation result
 */
export async function generateProject(
    templateName: string,
    config: import('./types/index.js').ProjectConfig,
    outputPath: string,
    options: Partial<import('./types/index.js').GenerationOptions> = {}
) {
    const engine = createTemplateEngine();
    const generationOptions: import('./types/index.js').GenerationOptions = {
        outputPath,
        overwrite: false,
        dryRun: false,
        ...options,
    };

    const result = await engine.generateProject(templateName, config, generationOptions);
    if (result.validation.success && !generationOptions.dryRun) {
        await engine.writeFiles(result.files, outputPath, generationOptions);
    }
    return result;
}
