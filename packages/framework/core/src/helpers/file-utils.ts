import fs from 'fs-extra';
import { glob } from 'glob';
import { pathUtils } from './path-utils.js';

/**
 * File system utilities for Brickend
 * Handles template reading, file generation, and directory operations
 */

/**
 * Check if a file or directory exists
 * @param filePath - Path to check
 * @returns True if path exists
 */
export async function exists(filePath: string): Promise<boolean> {
    try {
        await fs.access(filePath);
        return true;
    } catch {
        return false;
    }
}

/**
 * Check if path is a file
 * @param filePath - Path to check
 * @returns True if path is a file
 */
export async function isFile(filePath: string): Promise<boolean> {
    try {
        const stats = await fs.stat(filePath);
        return stats.isFile();
    } catch {
        return false;
    }
}

/**
 * Check if path is a directory
 * @param dirPath - Path to check
 * @returns True if path is a directory
 */
export async function isDirectory(dirPath: string): Promise<boolean> {
    try {
        const stats = await fs.stat(dirPath);
        return stats.isDirectory();
    } catch {
        return false;
    }
}

/**
 * Read file content as string
 * @param filePath - Path to file
 * @param encoding - File encoding (default: 'utf8')
 * @returns File content as string
 */
export async function readFile(filePath: string, encoding: BufferEncoding = 'utf8'): Promise<string> {
    try {
        return await fs.readFile(filePath, encoding);
    } catch (error) {
        throw new Error(`Failed to read file ${filePath}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
}

/**
 * Read file content as buffer
 * @param filePath - Path to file
 * @returns File content as buffer
 */
export async function readFileBuffer(filePath: string): Promise<Buffer> {
    try {
        return await fs.readFile(filePath);
    } catch (error) {
        throw new Error(`Failed to read file ${filePath}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
}

/**
 * Write string content to file
 * @param filePath - Path to file
 * @param content - Content to write
 * @param encoding - File encoding (default: 'utf8')
 */
export async function writeFile(filePath: string, content: string, encoding: BufferEncoding = 'utf8'): Promise<void> {
    try {
        // Ensure directory exists
        await ensureDir(pathUtils.getDirName(filePath));
        await fs.writeFile(filePath, content, encoding);
    } catch (error) {
        throw new Error(`Failed to write file ${filePath}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
}

/**
 * Write buffer content to file
 * @param filePath - Path to file
 * @param content - Buffer content to write
 */
export async function writeFileBuffer(filePath: string, content: Buffer): Promise<void> {
    try {
        // Ensure directory exists
        await ensureDir(pathUtils.getDirName(filePath));
        await fs.writeFile(filePath, content);
    } catch (error) {
        throw new Error(`Failed to write file ${filePath}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
}

/**
 * Copy file from source to destination
 * @param src - Source file path
 * @param dest - Destination file path
 * @param overwrite - Whether to overwrite existing file (default: false)
 */
export async function copyFile(src: string, dest: string, overwrite: boolean = false): Promise<void> {
    try {
        // Check if source exists
        if (!(await exists(src))) {
            throw new Error(`Source file does not exist: ${src}`);
        }

        // Check if destination exists and overwrite is false
        if (!overwrite && (await exists(dest))) {
            throw new Error(`Destination file already exists: ${dest}`);
        }

        // Ensure destination directory exists
        await ensureDir(pathUtils.getDirName(dest));

        await fs.copy(src, dest, { overwrite });
    } catch (error) {
        throw new Error(`Failed to copy file from ${src} to ${dest}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
}

/**
 * Create directory (including parent directories)
 * @param dirPath - Directory path to create
 */
export async function ensureDir(dirPath: string): Promise<void> {
    try {
        await fs.ensureDir(dirPath);
    } catch (error) {
        throw new Error(`Failed to create directory ${dirPath}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
}

/**
 * Remove file or directory
 * @param targetPath - Path to remove
 */
export async function remove(targetPath: string): Promise<void> {
    try {
        await fs.remove(targetPath);
    } catch (error) {
        throw new Error(`Failed to remove ${targetPath}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
}

/**
 * List files in directory
 * @param dirPath - Directory path
 * @param recursive - Whether to list recursively (default: false)
 * @returns Array of file paths
 */
export async function listFiles(dirPath: string, recursive: boolean = false): Promise<string[]> {
    try {
        if (!(await isDirectory(dirPath))) {
            return [];
        }

        const pattern = recursive ? '**/*' : '*';
        const files = await glob(pattern, {
            cwd: dirPath,
            nodir: true, // Only return files, not directories
            dot: false   // Don't include hidden files
        });

        return files.map(file => pathUtils.joinPath(dirPath, file));
    } catch (error) {
        throw new Error(`Failed to list files in ${dirPath}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
}

/**
 * List directories in directory
 * @param dirPath - Directory path
 * @param recursive - Whether to list recursively (default: false)
 * @returns Array of directory paths
 */
export async function listDirectories(
    dirPath: string,
    recursive: boolean = false
): Promise<string[]> {
    try {
        if (!(await isDirectory(dirPath))) return [];

        const pattern = recursive ? '**/*' : '*';
        // nodir: false = permite devolver tanto archivos como carpetas
        const entries: string[] = await glob(pattern, {
            cwd: dirPath,
            nodir: false,
            dot: false
        });

        const dirs: string[] = [];
        for (const entry of entries) {
            const full = pathUtils.joinPath(dirPath, entry);
            if (await isDirectory(full)) {
                dirs.push(full);
            }
        }

        return dirs;
    } catch (error) {
        throw new Error(
            `Failed to list directories in ${dirPath}: ${error instanceof Error ? error.message : 'Unknown error'
            }`
        );
    }
}


/**
 * Find files matching pattern
 * @param pattern - Glob pattern
 * @param options - Glob options
 * @returns Array of matching file paths
 */
export async function findFiles(pattern: string, options: { cwd?: string; ignore?: string[] } = {}): Promise<string[]> {
    try {
        const files = await glob(pattern, {
            cwd: options.cwd || process.cwd(),
            ignore: options.ignore || [],
            nodir: true,
            dot: false
        });

        if (options.cwd) {
            return files.map(file => pathUtils.joinPath(options.cwd!, file));
        }

        return files;
    } catch (error) {
        throw new Error(`Failed to find files with pattern ${pattern}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
}

/**
 * Read JSON file and parse content
 * @param filePath - Path to JSON file
 * @returns Parsed JSON content
 */
export async function readJsonFile<T = any>(filePath: string): Promise<T> {
    try {
        const content = await readFile(filePath);
        return JSON.parse(content) as T;
    } catch (error) {
        if (error instanceof SyntaxError) {
            throw new Error(`Invalid JSON in file ${filePath}: ${error.message}`);
        }
        throw error;
    }
}

/**
 * Write object to JSON file
 * @param filePath - Path to JSON file
 * @param data - Data to write
 * @param pretty - Whether to format JSON (default: true)
 */
export async function writeJsonFile(filePath: string, data: any, pretty: boolean = true): Promise<void> {
    try {
        const content = pretty
            ? JSON.stringify(data, null, 2)
            : JSON.stringify(data);

        await writeFile(filePath, content);
    } catch (error) {
        throw new Error(`Failed to write JSON file ${filePath}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
}

/**
 * Get file stats
 * @param filePath - Path to file
 * @returns File stats object
 */
export async function getFileStats(filePath: string): Promise<fs.Stats> {
    try {
        return await fs.stat(filePath);
    } catch (error) {
        throw new Error(`Failed to get stats for ${filePath}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
}

/**
 * Check if directory is empty
 * @param dirPath - Directory path
 * @returns True if directory is empty
 */
export async function isEmptyDirectory(dirPath: string): Promise<boolean> {
    try {
        if (!(await isDirectory(dirPath))) {
            return false;
        }

        const items = await fs.readdir(dirPath);
        return items.length === 0;
    } catch {
        return false;
    }
}

/**
 * Copy directory recursively
 * @param src - Source directory
 * @param dest - Destination directory
 * @param options - Copy options
 */
export async function copyDirectory(
    src: string,
    dest: string,
    options: { overwrite?: boolean; filter?: (src: string) => boolean } = {}
): Promise<void> {
    try {
        const { overwrite = false, filter } = options;

        await fs.copy(src, dest, {
            overwrite,
            filter: filter ? (srcPath: string) => filter(srcPath) : undefined
        });
    } catch (error) {
        throw new Error(`Failed to copy directory from ${src} to ${dest}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
}

/**
 * Make file executable (Unix-like systems only)
 * @param filePath - Path to file
 */
export async function makeExecutable(filePath: string): Promise<void> {
    try {
        if (process.platform !== 'win32') {
            await fs.chmod(filePath, '755');
        }
    } catch (error) {
        throw new Error(`Failed to make file executable ${filePath}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
}

/**
 * Get file size in bytes
 * @param filePath - Path to file
 * @returns File size in bytes
 */
export async function getFileSize(filePath: string): Promise<number> {
    try {
        const stats = await getFileStats(filePath);
        return stats.size;
    } catch (error) {
        throw new Error(`Failed to get file size for ${filePath}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
}

/**
 * Create temporary directory
 * @param prefix - Directory name prefix
 * @returns Path to created temporary directory
 */
export async function createTempDir(prefix: string = 'brickend-'): Promise<string> {
    try {
        const tempDir = await fs.mkdtemp(pathUtils.joinPath(require('os').tmpdir(), prefix));
        return tempDir;
    } catch (error) {
        throw new Error(`Failed to create temporary directory: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
}

/**
 * Template-specific file operations
 */
export const templateFiles = {
    /**
     * Read template file (handles .ejs extension)
     * @param templateDir - Template directory
     * @param fileName - File name (with or without .ejs)
     * @returns Template content
     */
    async readTemplate(templateDir: string, fileName: string): Promise<string> {
        const templatePath = pathUtils.getTemplateFilePath(templateDir, fileName);

        if (!(await exists(templatePath))) {
            throw new Error(`Template file not found: ${templatePath}`);
        }

        return readFile(templatePath);
    },

    /**
     * List all template files in directory
     * @param templateDir - Template directory
     * @returns Array of template file paths
     */
    async listTemplates(templateDir: string): Promise<string[]> {
        const files = await findFiles('**/*.ejs', { cwd: templateDir });
        return files.map(file => pathUtils.getRelativePath(templateDir, file));
    },

    /**
     * Check if template directory is valid
     * @param templateDir - Template directory
     * @returns True if directory contains template.config.json
     */
    async isValidTemplate(templateDir: string): Promise<boolean> {
        const configPath = pathUtils.joinPath(templateDir, 'template.config.json');
        return exists(configPath);
    }
};

/**
 * Utility object containing all file functions
 */
export const fileUtils = {
    exists,
    isFile,
    isDirectory,
    readFile,
    readFileBuffer,
    writeFile,
    writeFileBuffer,
    copyFile,
    ensureDir,
    remove,
    listFiles,
    listDirectories,
    findFiles,
    readJsonFile,
    writeJsonFile,
    getFileStats,
    isEmptyDirectory,
    copyDirectory,
    makeExecutable,
    getFileSize,
    createTempDir,
    templateFiles,
} as const;