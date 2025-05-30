import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

/**
 * Path manipulation utilities for Brickend
 * Handles template paths, output paths, and file resolution
 */

/**
 * Get current file directory (useful for ES modules)
 * @param importMetaUrl - import.meta.url from calling module
 * @returns Directory path of the calling file
 */
export function getCurrentDirectory(importMetaUrl: string): string {
    return dirname(fileURLToPath(importMetaUrl));
}

/**
 * Normalize path separators for cross-platform compatibility
 * @param filePath - Path to normalize
 * @returns Normalized path with forward slashes
 */
export function normalizePath(filePath: string): string {
    return filePath.replace(/\\/g, '/');
}

/**
 * Join path segments safely
 * @param segments - Path segments to join
 * @returns Joined and normalized path
 */
export function joinPath(...segments: string[]): string {
    return normalizePath(path.join(...segments));
}

/**
 * Resolve absolute path from segments
 * @param segments - Path segments to resolve
 * @returns Absolute resolved path
 */
export function resolvePath(...segments: string[]): string {
    return normalizePath(path.resolve(...segments));
}

/**
 * Get relative path from one location to another
 * @param from - Source path
 * @param to - Target path
 * @returns Relative path from source to target
 */
export function getRelativePath(from: string, to: string): string {
    return normalizePath(path.relative(from, to));
}

/**
 * Get file extension from path
 * @param filePath - File path
 * @returns File extension including the dot (e.g., '.ts', '.json')
 */
export function getExtension(filePath: string): string {
    return path.extname(filePath);
}

/**
 * Get filename without extension
 * @param filePath - File path
 * @returns Filename without extension
 */
export function getBaseName(filePath: string): string {
    return path.basename(filePath, getExtension(filePath));
}

/**
 * Get filename with extension
 * @param filePath - File path
 * @returns Filename with extension
 */
export function getFileName(filePath: string): string {
    return path.basename(filePath);
}

/**
 * Get directory name from path
 * @param filePath - File path
 * @returns Directory path
 */
export function getDirName(filePath: string): string {
    return normalizePath(path.dirname(filePath));
}

/**
 * Check if path is absolute
 * @param filePath - Path to check
 * @returns True if path is absolute
 */
export function isAbsolute(filePath: string): boolean {
    return path.isAbsolute(filePath);
}

/**
 * Convert relative path to absolute based on base directory
 * @param relativePath - Relative path
 * @param baseDir - Base directory (defaults to process.cwd())
 * @returns Absolute path
 */
export function toAbsolute(relativePath: string, baseDir: string = process.cwd()): string {
    if (isAbsolute(relativePath)) {
        return normalizePath(relativePath);
    }
    return resolvePath(baseDir, relativePath);
}

/**
 * Ensure path ends with trailing slash (for directories)
 * @param dirPath - Directory path
 * @returns Path with trailing slash
 */
export function ensureTrailingSlash(dirPath: string): string {
    const normalized = normalizePath(dirPath);
    return normalized.endsWith('/') ? normalized : normalized + '/';
}

/**
 * Remove trailing slash from path
 * @param dirPath - Directory path
 * @returns Path without trailing slash
 */
export function removeTrailingSlash(dirPath: string): string {
    const normalized = normalizePath(dirPath);
    return normalized.endsWith('/') ? normalized.slice(0, -1) : normalized;
}

/**
 * Validate that a path is safe (no directory traversal)
 * @param filePath - Path to validate
 * @param allowedBase - Base directory that path must be within
 * @returns True if path is safe
 */
export function isSafePath(filePath: string, allowedBase: string): boolean {
    const resolvedPath = resolvePath(filePath);
    const resolvedBase = resolvePath(allowedBase);

    return resolvedPath.startsWith(resolvedBase);
}

/**
 * Create a safe filename from arbitrary string
 * @param input - Input string
 * @returns Safe filename string
 */
export function toSafeFileName(input: string): string {
    return input
        .replace(/[<>:"/\\|?*]/g, '-') // Replace unsafe characters
        .replace(/\s+/g, '-') // Replace spaces with hyphens
        .replace(/[-]+/g, '-') // Normalize multiple hyphens
        .replace(/^-+|-+$/g, '') // Remove leading/trailing hyphens
        .toLowerCase();
}

/**
 * Get template file path with proper extension handling
 * @param templatePath - Base template path
 * @param fileName - File name (may include .ejs extension)
 * @returns Proper template file path
 */
export function getTemplateFilePath(templatePath: string, fileName: string): string {
    // If fileName doesn't end with .ejs, assume it's the final filename
    // and look for fileName.ejs in the template directory
    if (!fileName.endsWith('.ejs')) {
        return joinPath(templatePath, fileName + '.ejs');
    }

    return joinPath(templatePath, fileName);
}

/**
 * Get output file path by removing .ejs extension and processing variables
 * @param templateFileName - Template file name (e.g., 'api.ts.ejs')
 * @returns Output file name (e.g., 'api.ts')
 */
export function getOutputFileName(templateFileName: string): string {
    if (templateFileName.endsWith('.ejs')) {
        return templateFileName.slice(0, -4); // Remove .ejs extension
    }
    return templateFileName;
}

/**
 * Build output path for generated file
 * @param outputDir - Base output directory
 * @param relativePath - Relative path from template
 * @returns Full output path for generated file
 */
export function buildOutputPath(outputDir: string, relativePath: string): string {
    const outputFileName = getOutputFileName(relativePath);
    return joinPath(outputDir, outputFileName);
}

/**
 * Parse template variable syntax in paths
 * @param pathTemplate - Path with template variables (e.g., '{{entity.name}}/api.ts')
 * @param variables - Variables to substitute
 * @returns Path with variables substituted
 */
export function parsePathTemplate(pathTemplate: string, variables: Record<string, any>): string {
    let result = pathTemplate;

    // Simple variable substitution {{variable.property}}
    result = result.replace(/\{\{([^}]+)\}\}/g, (match, expression) => {
        const keys = expression.trim().split('.');
        let value: any = variables;

        for (const key of keys) {
            value = value?.[key];
            if (value === undefined) {
                return match; // Keep original if variable not found
            }
        }

        return String(value);
    });

    return result;
}

/**
 * Find common base path among multiple paths
 * @param paths - Array of paths
 * @returns Common base path
 */
export function findCommonBasePath(paths: string[]): string {
    if (paths.length === 0) return '';
    if (paths.length === 1) {
        const only = paths[0];
        if (only === undefined) return '';
        return getDirName(only);
    }

    const normalizedPaths = paths.map(p => normalizePath(p));
    const first = normalizedPaths[0];
    if (first === undefined) return '';
    const segments = first.split('/');

    for (let i = 0; i < segments.length; i++) {
        const segment = segments[i];
        if (!normalizedPaths.every(p => {
            const segs = p.split('/');
            return segs[i] === segment;
        })) {
            return segments.slice(0, i).join('/');
        }
    }

    return segments.join('/');
}


/**
 * Check if path matches a glob pattern (basic implementation)
 * @param filePath - File path to test
 * @param pattern - Glob pattern (* and ** supported)
 * @returns True if path matches pattern
 */
export function matchesPattern(filePath: string, pattern: string): boolean {
    const normalizedPath = normalizePath(filePath);
    const normalizedPattern = normalizePath(pattern);

    // Convert glob pattern to regex
    const regexPattern = normalizedPattern
        .replace(/\*\*/g, '.*') // ** matches any path
        .replace(/\*/g, '[^/]*') // * matches any filename
        .replace(/\?/g, '.'); // ? matches single character

    const regex = new RegExp(`^${regexPattern}$`);
    return regex.test(normalizedPath);
}

/**
 * Ensure directory path exists in the context of template generation
 * This doesn't actually create directories, just validates the path structure
 * @param dirPath - Directory path to validate
 * @returns Validated directory path
 */
export function validateDirectoryPath(dirPath: string): string {
    const normalized = normalizePath(dirPath);

    // Check for invalid characters
    if (/[<>:"|?*]/.test(normalized)) {
        throw new Error(`Invalid characters in directory path: ${dirPath}`);
    }

    // Check for directory traversal attempts
    if (normalized.includes('../') || normalized.includes('..\\')) {
        throw new Error(`Directory traversal not allowed: ${dirPath}`);
    }

    return ensureTrailingSlash(normalized);
}

/**
 * Utility object containing all path functions
 */
export const pathUtils = {
    getCurrentDirectory,
    normalizePath,
    joinPath,
    resolvePath,
    getRelativePath,
    getExtension,
    getBaseName,
    getFileName,
    getDirName,
    isAbsolute,
    toAbsolute,
    ensureTrailingSlash,
    removeTrailingSlash,
    isSafePath,
    toSafeFileName,
    getTemplateFilePath,
    getOutputFileName,
    buildOutputPath,
    parsePathTemplate,
    findCommonBasePath,
    matchesPattern,
    validateDirectoryPath,
} as const;