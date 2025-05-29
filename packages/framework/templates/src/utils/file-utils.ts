/**
 * File Utilities for Brickend Templates
 * Helper functions for file and directory operations
 */

import * as fs from 'fs-extra';
import * as path from 'path';
import { promisify } from 'util';
import { exec } from 'child_process';

const execAsync = promisify(exec);

/**
 * File operation result
 */
export interface FileOperationResult {
    success: boolean;
    path?: string;
    error?: string;
    metadata?: {
        size?: number;
        created?: Date;
        modified?: Date;
    };
}

/**
 * Directory scanning options
 */
export interface ScanDirectoryOptions {
    /** Include hidden files/directories */
    includeHidden?: boolean;
    /** Maximum depth to scan */
    maxDepth?: number;
    /** File extensions to include (e.g., ['.ts', '.js']) */
    extensions?: string[];
    /** Patterns to exclude */
    exclude?: string[];
    /** Include file stats */
    includeStats?: boolean;
}

/**
 * File info with metadata
 */
export interface FileInfo {
    name: string;
    path: string;
    relativePath: string;
    isDirectory: boolean;
    isFile: boolean;
    size?: number;
    created?: Date;
    modified?: Date;
    extension?: string;
}

/**
 * Copy options
 */
export interface CopyOptions {
    /** Overwrite existing files */
    overwrite?: boolean;
    /** Preserve timestamps */
    preserveTimestamps?: boolean;
    /** Copy symbolic links as links */
    dereference?: boolean;
    /** Filter function for files */
    filter?: (src: string, dest: string) => boolean;
}

/**
 * Check if a file or directory exists
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
 */
export async function isFile(filePath: string): Promise<boolean> {
    try {
        const stat = await fs.stat(filePath);
        return stat.isFile();
    } catch {
        return false;
    }
}

/**
 * Check if path is a directory
 */
export async function isDirectory(filePath: string): Promise<boolean> {
    try {
        const stat = await fs.stat(filePath);
        return stat.isDirectory();
    } catch {
        return false;
    }
}

/**
 * Ensure directory exists, create if it doesn't
 */
export async function ensureDirectory(dirPath: string): Promise<FileOperationResult> {
    try {
        await fs.ensureDir(dirPath);
        return {
            success: true,
            path: dirPath
        };
    } catch (error) {
        return {
            success: false,
            error: error instanceof Error ? error.message : 'Unknown error'
        };
    }
}

/**
 * Write content to file, creating directories if needed
 */
export async function writeFile(
    filePath: string,
    content: string,
    options: {
        encoding?: BufferEncoding;
        createDirs?: boolean;
        backup?: boolean;
    } = {}
): Promise<FileOperationResult> {
    try {
        const {
            encoding = 'utf8',
            createDirs = true,
            backup = false
        } = options;

        // Create directories if needed
        if (createDirs) {
            const dir = path.dirname(filePath);
            await fs.ensureDir(dir);
        }

        // Create backup if requested and file exists
        if (backup && await exists(filePath)) {
            const backupPath = `${filePath}.backup.${Date.now()}`;
            await fs.copy(filePath, backupPath);
        }

        // Write file
        await fs.writeFile(filePath, content, { encoding });

        // Get file stats
        const stats = await fs.stat(filePath);

        return {
            success: true,
            path: filePath,
            metadata: {
                size: stats.size,
                created: stats.birthtime,
                modified: stats.mtime
            }
        };
    } catch (error) {
        return {
            success: false,
            error: error instanceof Error ? error.message : 'Unknown error'
        };
    }
}

/**
 * Read file content
 */
export async function readFile(
    filePath: string,
    encoding: BufferEncoding = 'utf8'
): Promise<{ success: boolean; content?: string; error?: string }> {
    try {
        const content = await fs.readFile(filePath, encoding);
        return {
            success: true,
            content
        };
    } catch (error) {
        return {
            success: false,
            error: error instanceof Error ? error.message : 'Unknown error'
        };
    }
}

/**
 * Copy file or directory
 */
export async function copy(
    src: string,
    dest: string,
    options: CopyOptions = {}
): Promise<FileOperationResult> {
    try {
        const {
            overwrite = false,
            preserveTimestamps = true,
            dereference = true,
            filter
        } = options;

        // Check if destination exists and overwrite is false
        if (!overwrite && await exists(dest)) {
            return {
                success: false,
                error: `Destination already exists: ${dest}`
            };
        }

        // Ensure destination directory exists
        const destDir = path.dirname(dest);
        await fs.ensureDir(destDir);

        // Copy with options
        await fs.copy(src, dest, {
            overwrite,
            preserveTimestamps,
            dereference,
            filter
        });

        return {
            success: true,
            path: dest
        };
    } catch (error) {
        return {
            success: false,
            error: error instanceof Error ? error.message : 'Unknown error'
        };
    }
}

/**
 * Move/rename file or directory
 */
export async function move(
    src: string,
    dest: string,
    overwrite: boolean = false
): Promise<FileOperationResult> {
    try {
        // Check if destination exists and overwrite is false
        if (!overwrite && await exists(dest)) {
            return {
                success: false,
                error: `Destination already exists: ${dest}`
            };
        }

        // Ensure destination directory exists
        const destDir = path.dirname(dest);
        await fs.ensureDir(destDir);

        // Move file/directory
        await fs.move(src, dest, { overwrite });

        return {
            success: true,
            path: dest
        };
    } catch (error) {
        return {
            success: false,
            error: error instanceof Error ? error.message : 'Unknown error'
        };
    }
}

/**
 * Delete file or directory
 */
export async function remove(filePath: string): Promise<FileOperationResult> {
    try {
        await fs.remove(filePath);
        return {
            success: true,
            path: filePath
        };
    } catch (error) {
        return {
            success: false,
            error: error instanceof Error ? error.message : 'Unknown error'
        };
    }
}

/**
 * Get file or directory information
 */
export async function getFileInfo(filePath: string): Promise<FileInfo | null> {
    try {
        const stats = await fs.stat(filePath);
        const parsedPath = path.parse(filePath);

        return {
            name: parsedPath.base,
            path: filePath,
            relativePath: path.relative(process.cwd(), filePath),
            isDirectory: stats.isDirectory(),
            isFile: stats.isFile(),
            size: stats.size,
            created: stats.birthtime,
            modified: stats.mtime,
            extension: parsedPath.ext
        };
    } catch {
        return null;
    }
}

/**
 * Scan directory and return file information
 */
export async function scanDirectory(
    dirPath: string,
    options: ScanDirectoryOptions = {}
): Promise<FileInfo[]> {
    const {
        includeHidden = false,
        maxDepth = Infinity,
        extensions = [],
        exclude = [],
        includeStats = true
    } = options;

    const results: FileInfo[] = [];

    async function scan(currentPath: string, currentDepth: number = 0): Promise<void> {
        if (currentDepth > maxDepth) return;

        try {
            const entries = await fs.readdir(currentPath, { withFileTypes: true });

            for (const entry of entries) {
                const fullPath = path.join(currentPath, entry.name);
                const relativePath = path.relative(dirPath, fullPath);

                // Skip hidden files if not included
                if (!includeHidden && entry.name.startsWith('.')) {
                    continue;
                }

                // Check exclusion patterns
                if (exclude.some(pattern => {
                    if (pattern.includes('*')) {
                        const regex = new RegExp(pattern.replace(/\*/g, '.*'));
                        return regex.test(entry.name) || regex.test(relativePath);
                    }
                    return entry.name === pattern || relativePath === pattern;
                })) {
                    continue;
                }

                // For files, check extensions
                if (entry.isFile() && extensions.length > 0) {
                    const ext = path.extname(entry.name).toLowerCase();
                    if (!extensions.includes(ext)) {
                        continue;
                    }
                }

                // Get file info
                let fileInfo: FileInfo = {
                    name: entry.name,
                    path: fullPath,
                    relativePath,
                    isDirectory: entry.isDirectory(),
                    isFile: entry.isFile(),
                    extension: entry.isFile() ? path.extname(entry.name) : undefined
                };

                // Add stats if requested
                if (includeStats) {
                    try {
                        const stats = await fs.stat(fullPath);
                        fileInfo.size = stats.size;
                        fileInfo.created = stats.birthtime;
                        fileInfo.modified = stats.mtime;
                    } catch {
                        // Stats failed, continue without them
                    }
                }

                results.push(fileInfo);

                // Recursively scan directories
                if (entry.isDirectory()) {
                    await scan(fullPath, currentDepth + 1);
                }
            }
        } catch (error) {
            console.warn(`Warning: Could not scan directory ${currentPath}: ${error}`);
        }
    }

    await scan(dirPath);
    return results;
}

/**
 * Find files matching a pattern
 */
export async function findFiles(
    searchPath: string,
    pattern: string | RegExp,
    options: ScanDirectoryOptions = {}
): Promise<FileInfo[]> {
    const files = await scanDirectory(searchPath, options);

    const regex = typeof pattern === 'string'
        ? new RegExp(pattern.replace(/\*/g, '.*'), 'i')
        : pattern;

    return files.filter(file =>
        file.isFile && (
            regex.test(file.name) ||
            regex.test(file.relativePath)
        )
    );
}

/**
 * Get directory size (recursive)
 */
export async function getDirectorySize(dirPath: string): Promise<number> {
    let totalSize = 0;

    async function calculateSize(currentPath: string): Promise<void> {
        try {
            const entries = await fs.readdir(currentPath, { withFileTypes: true });

            for (const entry of entries) {
                const fullPath = path.join(currentPath, entry.name);

                if (entry.isFile()) {
                    const stats = await fs.stat(fullPath);
                    totalSize += stats.size;
                } else if (entry.isDirectory()) {
                    await calculateSize(fullPath);
                }
            }
        } catch (error) {
            console.warn(`Warning: Could not calculate size for ${currentPath}: ${error}`);
        }
    }

    await calculateSize(dirPath);
    return totalSize;
}

/**
 * Make file executable
 */
export async function makeExecutable(filePath: string): Promise<FileOperationResult> {
    try {
        await fs.chmod(filePath, 0o755);
        return {
            success: true,
            path: filePath
        };
    } catch (error) {
        return {
            success: false,
            error: error instanceof Error ? error.message : 'Unknown error'
        };
    }
}

/**
 * Create symbolic link
 */
export async function createSymlink(
    target: string,
    linkPath: string,
    type: 'file' | 'dir' = 'file'
): Promise<FileOperationResult> {
    try {
        // Ensure parent directory exists
        const parentDir = path.dirname(linkPath);
        await fs.ensureDir(parentDir);

        await fs.symlink(target, linkPath, type);

        return {
            success: true,
            path: linkPath
        };
    } catch (error) {
        return {
            success: false,
            error: error instanceof Error ? error.message : 'Unknown error'
        };
    }
}

/**
 * Empty directory (remove all contents but keep directory)
 */
export async function emptyDirectory(dirPath: string): Promise<FileOperationResult> {
    try {
        await fs.emptyDir(dirPath);
        return {
            success: true,
            path: dirPath
        };
    } catch (error) {
        return {
            success: false,
            error: error instanceof Error ? error.message : 'Unknown error'
        };
    }
}

/**
 * Create temporary directory
 */
export async function createTempDirectory(prefix: string = 'brickend-tmp-'): Promise<string> {
    const tmpDir = await fs.mkdtemp(path.join(require('os').tmpdir(), prefix));
    return tmpDir;
}

/**
 * Watch file or directory for changes
 */
export function watchPath(
    filePath: string,
    callback: (eventType: string, filename: string | null) => void
): fs.FSWatcher {
    return fs.watch(filePath, callback);
}

/**
 * Format file size in human readable format
 */
export function formatFileSize(bytes: number): string {
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 Bytes';

    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    const size = bytes / Math.pow(1024, i);

    return `${Math.round(size * 100) / 100} ${sizes[i]}`;
}

/**
 * Get relative path between two paths
 */
export function getRelativePath(from: string, to: string): string {
    return path.relative(from, to);
}

/**
 * Resolve path (handles ~, relative paths, etc.)
 */
export function resolvePath(filePath: string): string {
    // Handle home directory
    if (filePath.startsWith('~/')) {
        const homeDir = require('os').homedir();
        return path.resolve(homeDir, filePath.slice(2));
    }

    return path.resolve(filePath);
}

/**
 * Generate unique filename if file already exists
 */
export async function generateUniqueFilename(
    basePath: string,
    extension: string = ''
): Promise<string> {
    let counter = 1;
    let filePath = basePath + extension;

    while (await exists(filePath)) {
        const parsedPath = path.parse(basePath);
        filePath = path.join(
            parsedPath.dir,
            `${parsedPath.name}-${counter}${extension}`
        );
        counter++;
    }

    return filePath;
}