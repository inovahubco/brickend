/**
 * Template Registry implementation
 */

import * as fs from 'fs-extra';
import * as path from 'path';
import type {
    ITemplateRegistry,
    TemplateDefinition,
    TemplateCategory,
    TemplateMetadata
} from '../types/index.js';

/**
 * Template Registry implementation
 */
export class TemplateRegistry implements ITemplateRegistry {
    private templates: Map<string, TemplateDefinition> = new Map();

    /**
     * Register a template
     */
    register(template: TemplateDefinition): void {
        this.templates.set(template.id, template);
    }

    /**
     * Get a template by id
     */
    get(id: string): TemplateDefinition | undefined {
        return this.templates.get(id);
    }

    /**
     * List all templates
     */
    list(): TemplateDefinition[] {
        return Array.from(this.templates.values());
    }

    /**
     * List templates by category
     */
    listByCategory(category: TemplateCategory): TemplateDefinition[] {
        return this.list().filter(template => template.category === category);
    }

    /**
     * Check if template exists
     */
    exists(id: string): boolean {
        return this.templates.has(id);
    }

    /**
     * Remove a template
     */
    unregister(id: string): boolean {
        return this.templates.delete(id);
    }

    /**
     * Clear all templates
     */
    clear(): void {
        this.templates.clear();
    }

    /**
     * Get template count
     */
    count(): number {
        return this.templates.size;
    }

    /**
     * Load templates from a directory
     */
    async loadFromDirectory(directoryPath: string): Promise<void> {
        try {
            if (!await fs.pathExists(directoryPath)) {
                throw new Error(`Templates directory not found: ${directoryPath}`);
            }

            const entries = await fs.readdir(directoryPath, { withFileTypes: true });
            for (const entry of entries) {
                if (entry.isDirectory()) {
                    const templatePath = path.join(directoryPath, entry.name);
                    await this.loadTemplate(templatePath, entry.name);
                }
            }
        } catch (error) {
            throw new Error(
                `Failed to load templates from directory: ${error instanceof Error ? error.message : 'Unknown error'
                }`
            );
        }
    }

    /**
     * Load a single template from a directory
     */
    private async loadTemplate(templatePath: string, templateId: string): Promise<void> {
        try {
            const templateJsonPath = path.join(templatePath, 'template.json');
            let metadata: TemplateMetadata | undefined;

            if (await fs.pathExists(templateJsonPath)) {
                metadata = await fs.readJson(templateJsonPath);
            }

            const category = this.detectCategory(templatePath);
            const files = await this.discoverTemplateFiles(templatePath);

            const template: TemplateDefinition = {
                id: templateId,
                name: metadata?.name || templateId,
                description: metadata?.description,
                category,
                path: templatePath,
                files,
                metadata
            };

            this.register(template);
        } catch (error) {
            console.warn(
                `Failed to load template from ${templatePath}: ${error instanceof Error ? error.message : 'Unknown error'
                }`
            );
        }
    }

    /**
     * Detect template category from path
     */
    private detectCategory(templatePath: string): TemplateCategory {
        const pathParts = templatePath.split(path.sep);
        if (pathParts.includes('projects')) return 'project';
        if (pathParts.includes('resources')) return 'resource';
        if (pathParts.includes('configs')) return 'config';
        if (pathParts.includes('components')) return 'component';
        return 'project'; // default
    }

    /**
     * Discover template files in a directory
     */
    private async discoverTemplateFiles(
        templatePath: string
    ): Promise<TemplateDefinition['files']> {
        const files: TemplateDefinition['files'] = [];

        const scan = async (dir: string, relativePath: string = ''): Promise<void> => {
            const entries = await fs.readdir(dir, { withFileTypes: true });

            for (const entry of entries) {
                const fullPath = path.join(dir, entry.name);
                const relativeFilePath = path.join(relativePath, entry.name);

                if (entry.isDirectory()) {
                    await scan(fullPath, relativeFilePath);
                } else if (
                    entry.isFile() &&
                    !entry.name.startsWith('.') &&
                    entry.name !== 'template.json'
                ) {
                    const target = entry.name.endsWith('.ejs')
                        ? relativeFilePath.slice(0, -4)
                        : relativeFilePath;

                    files.push({
                        source: relativeFilePath,
                        target,
                        executable: await this.isExecutable(fullPath)
                    });
                }
            }
        };

        await scan(templatePath);
        return files;
    }

    /**
     * Check if a file is executable
     */
    private async isExecutable(filePath: string): Promise<boolean> {
        try {
            const stats = await fs.stat(filePath);
            return (stats.mode & parseInt('111', 8)) !== 0;
        } catch {
            return false;
        }
    }

    /**
     * Get templates that match a search term
     */
    search(term: string): TemplateDefinition[] {
        const searchTerm = term.toLowerCase();
        return this.list().filter(
            template =>
                template.id.toLowerCase().includes(searchTerm) ||
                template.name.toLowerCase().includes(searchTerm) ||
                template.description?.toLowerCase().includes(searchTerm) ||
                template.metadata?.tags?.some(tag =>
                    tag.toLowerCase().includes(searchTerm)
                )
        );
    }

    /**
     * Validate a template definition
     */
    validate(template: TemplateDefinition): string[] {
        const errors: string[] = [];

        if (!template.id) {
            errors.push('Template id is required');
        }
        if (!template.name) {
            errors.push('Template name is required');
        }
        if (!template.path) {
            errors.push('Template path is required');
        }
        if (!['project', 'resource', 'config', 'component'].includes(template.category)) {
            errors.push('Invalid template category');
        }
        if (!Array.isArray(template.files)) {
            errors.push('Template files must be an array');
        }

        return errors;
    }
}
