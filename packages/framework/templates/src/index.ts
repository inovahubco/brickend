/**
 * Factory Functions for Brickend Templates
 * Simple API interface for common template generation tasks
 */

import { Generator } from './generator.js';
import type {
  GenerationResult,
  ProjectGenerationOptions,
  ResourceGenerationOptions,
  ConfigGenerationOptions,
  GeneratorOptions,
  TemplateField,
  TemplateDefinition
} from './types/index.js';

/**
 * Global generator instance for factory functions
 */
let globalGenerator: Generator | null = null;

/**
 * Get or create the global generator instance
 */
function getGlobalGenerator(): Generator {
  if (!globalGenerator) {
    globalGenerator = new Generator();
  }
  return globalGenerator;
}

/**
 * Create a new Generator instance with custom options
 */
export function createGenerator(options: GeneratorOptions = {}): Generator {
  return new Generator(options);
}

/**
 * Generate a project using the global generator instance
 * 
 * @param name - Project name
 * @param templateId - Template identifier (e.g., 'basic-api')
 * @param options - Generation options
 * @returns Promise<GenerationResult>
 * 
 * @example
 * ```typescript
 * const result = await generateProject('my-api', 'basic-api', {
 *   outputDir: './projects',
 *   variables: {
 *     description: 'My awesome API',
 *     author: 'John Doe'
 *   }
 * });
 * 
 * if (result.success) {
 *   console.log(`Generated ${result.files.length} files`);
 * }
 * ```
 */
export async function generateProject(
  name: string,
  templateId: string = 'basic-api',
  options: Partial<ProjectGenerationOptions> = {}
): Promise<GenerationResult> {
  const generator = getGlobalGenerator();
  return generator.generateProject(name, templateId, options);
}

/**
 * Generate a resource (CRUD, component, etc.) using the global generator instance
 * 
 * @param name - Resource name
 * @param fields - Resource fields definition
 * @param options - Generation options
 * @returns Promise<GenerationResult>
 * 
 * @example
 * ```typescript
 * const result = await generateResource('User', [
 *   { name: 'name', type: 'string', required: true },
 *   { name: 'email', type: 'email', required: true },
 *   { name: 'age', type: 'number', required: false }
 * ], {
 *   outputDir: './src/resources',
 *   templateId: 'crud'
 * });
 * ```
 */
export async function generateResource(
  name: string,
  fields: TemplateField[],
  options: Partial<ResourceGenerationOptions> = {}
): Promise<GenerationResult> {
  const generator = getGlobalGenerator();
  return generator.generateResource(name, fields, options);
}

/**
 * Generate configuration files using the global generator instance
 * 
 * @param type - Configuration type (e.g., 'docker', 'vercel', 'package')
 * @param options - Generation options
 * @returns Promise<GenerationResult>
 * 
 * @example
 * ```typescript
 * const result = await generateConfig('docker', {
 *   variables: {
 *     database: 'postgresql',
 *     redis: true,
 *     monitoring: true
 *   }
 * });
 * ```
 */
export async function generateConfig(
  type: string,
  options: Partial<ConfigGenerationOptions> = {}
): Promise<GenerationResult> {
  const generator = getGlobalGenerator();
  return generator.generateConfig(type, options);
}

/**
 * Initialize the template system with templates from a directory
 * 
 * @param templatesPath - Path to templates directory
 * @param generatorOptions - Optional generator configuration
 * 
 * @example
 * ```typescript
 * await initializeTemplates('./templates', {
 *   verbose: true
 * });
 * ```
 */
export async function initializeTemplates(
  templatesPath: string,
  generatorOptions: GeneratorOptions = {}
): Promise<void> {
  globalGenerator = new Generator(generatorOptions);
  await globalGenerator.loadTemplates(templatesPath);
}

/**
 * Get all available templates
 * 
 * @returns Array of template definitions
 * 
 * @example
 * ```typescript
 * const templates = getAvailableTemplates();
 * console.log('Available templates:', templates.map(t => t.id));
 * ```
 */
export function getAvailableTemplates(): TemplateDefinition[] {
  const generator = getGlobalGenerator();
  return generator.getTemplates();
}

/**
 * Get templates by category
 * 
 * @param category - Template category
 * @returns Array of template definitions in the specified category
 * 
 * @example
 * ```typescript
 * const projectTemplates = getTemplatesByCategory('project');
 * const resourceTemplates = getTemplatesByCategory('resource');
 * ```
 */
export function getTemplatesByCategory(
  category: 'project' | 'resource' | 'config' | 'component'
): TemplateDefinition[] {
  const generator = getGlobalGenerator();
  return generator.getTemplatesByCategory(category);
}

/**
 * Check if a template exists
 * 
 * @param templateId - Template identifier
 * @returns Boolean indicating if template exists
 * 
 * @example
 * ```typescript
 * if (hasTemplate('basic-api')) {
 *   console.log('Basic API template is available');
 * }
 * ```
 */
export function hasTemplate(templateId: string): boolean {
  const generator = getGlobalGenerator();
  return generator.hasTemplate(templateId);
}

/**
 * Register a custom helper function for templates
 * 
 * @param name - Helper name
 * @param helper - Helper function
 * 
 * @example
 * ```typescript
 * registerHelper('formatCurrency', (amount: number) => {
 *   return new Intl.NumberFormat('en-US', {
 *     style: 'currency',
 *     currency: 'USD'
 *   }).format(amount);
 * });
 * ```
 */
export function registerHelper(
  name: string,
  helper: (...args: any[]) => any
): void {
  const generator = getGlobalGenerator();
  generator.registerHelper(name, helper);
}

/**
 * Quick project generation with sensible defaults
 * 
 * @param name - Project name
 * @param options - Quick generation options
 * @returns Promise<GenerationResult>
 * 
 * @example
 * ```typescript
 * // Generate a basic API project
 * await quickProject('my-api');
 * 
 * // Generate with custom options
 * await quickProject('my-blog', {
 *   type: 'fullstack',
 *   database: true,
 *   auth: true
 * });
 * ```
 */
export async function quickProject(
  name: string,
  options: {
    type?: 'api' | 'cli' | 'library' | 'fullstack';
    database?: boolean;
    auth?: boolean;
    description?: string;
    author?: string;
    outputDir?: string;
  } = {}
): Promise<GenerationResult> {
  const templateId = options.type === 'api' || !options.type ? 'basic-api' : options.type;

  const variables = {
    description: options.description || `A ${options.type || 'API'} project built with Brickend`,
    author: options.author || '',
    database: options.database || false,
    auth: options.auth || false
  };

  return generateProject(name, templateId, {
    outputDir: options.outputDir || `./${name}`,
    variables
  });
}

/**
 * Quick resource generation with common field types
 * 
 * @param name - Resource name
 * @param options - Quick resource options
 * @returns Promise<GenerationResult>
 * 
 * @example
 * ```typescript
 * // Generate a user resource
 * await quickResource('User', {
 *   fields: {
 *     name: 'string',
 *     email: 'email', 
 *     age: 'number?'  // ? means optional
 *   }
 * });
 * ```
 */
export async function quickResource(
  name: string,
  options: {
    fields: Record<string, string>;
    outputDir?: string;
    templateId?: string;
  }
): Promise<GenerationResult> {
  // Convert simple field definition to TemplateField[]
  const fields: TemplateField[] = Object.entries(options.fields).map(([fieldName, fieldType]) => {
    const isOptional = fieldType.endsWith('?');
    const cleanType = isOptional ? fieldType.slice(0, -1) : fieldType;

    return {
      name: fieldName,
      type: cleanType as any,
      required: !isOptional,
      description: `${fieldName} field`
    };
  });

  return generateResource(name, fields, {
    outputDir: options.outputDir || './src',
    templateId: options.templateId || 'crud'
  });
}

/**
 * Batch generation - generate multiple items at once
 * 
 * @param operations - Array of generation operations
 * @returns Promise<GenerationResult[]>
 * 
 * @example
 * ```typescript
 * const results = await batchGenerate([
 *   { type: 'project', name: 'my-api', templateId: 'basic-api' },
 *   { type: 'resource', name: 'User', fields: [...] },
 *   { type: 'config', configType: 'docker' }
 * ]);
 * ```
 */
export async function batchGenerate(
  operations: Array<
    | { type: 'project'; name: string; templateId?: string; options?: Partial<ProjectGenerationOptions> }
    | { type: 'resource'; name: string; fields: TemplateField[]; options?: Partial<ResourceGenerationOptions> }
    | { type: 'config'; configType: string; options?: Partial<ConfigGenerationOptions> }
  >
): Promise<GenerationResult[]> {
  const results: GenerationResult[] = [];

  for (const operation of operations) {
    try {
      let result: GenerationResult;

      switch (operation.type) {
        case 'project':
          result = await generateProject(
            operation.name,
            operation.templateId || 'basic-api',
            operation.options || {}
          );
          break;

        case 'resource':
          result = await generateResource(
            operation.name,
            operation.fields,
            operation.options || {}
          );
          break;

        case 'config':
          result = await generateConfig(
            operation.configType,
            operation.options || {}
          );
          break;

        default:
          throw new Error(`Unknown operation type: ${(operation as any).type}`);
      }

      results.push(result);
    } catch (error) {
      // Create error result for failed operations
      results.push({
        success: false,
        files: [],
        errors: [{
          type: 'system',
          message: error instanceof Error ? error.message : 'Unknown error',
          originalError: error instanceof Error ? error : undefined
        }],
        warnings: [],
        metadata: {
          templateId: 'unknown',
          context: {} as any,
          duration: 0,
          timestamp: new Date()
        }
      });
    }
  }

  return results;
}

/**
 * Reset the global generator instance
 * Useful for testing or when you want to start fresh
 */
export function resetGlobalGenerator(): void {
  globalGenerator = null;
}

/**
 * Get statistics about the current template system
 * 
 * @returns Template system statistics
 * 
 * @example
 * ```typescript
 * const stats = getTemplateStats();
 * console.log(`Total templates: ${stats.totalTemplates}`);
 * console.log(`Project templates: ${stats.byCategory.project}`);
 * ```
 */
export function getTemplateStats(): {
  totalTemplates: number;
  byCategory: Record<string, number>;
  templateIds: string[];
} {
  const generator = getGlobalGenerator();
  const templates = generator.getTemplates();

  const byCategory = templates.reduce((acc, template) => {
    acc[template.category] = (acc[template.category] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return {
    totalTemplates: templates.length,
    byCategory,
    templateIds: templates.map(t => t.id)
  };
}