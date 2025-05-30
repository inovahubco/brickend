// String utilities
export * from './string-utils.js';
import { stringUtils } from './string-utils.js';

// Path utilities  
export * from './path-utils.js';
import { pathUtils } from './path-utils.js';

// File utilities
export * from './file-utils.js';
import { fileUtils } from './file-utils.js';

/**
 * Combined utilities object for template context
 */
export const templateHelpers = {
    // String utilities (most commonly used in templates)
    camelCase: stringUtils.camelCase,
    pascalCase: stringUtils.pascalCase,
    kebabCase: stringUtils.kebabCase,
    snakeCase: stringUtils.snakeCase,
    constantCase: stringUtils.constantCase,
    capitalize: stringUtils.capitalize,
    lowercase: stringUtils.lowercase,
    uppercase: stringUtils.uppercase,
    pluralize: stringUtils.pluralize,
    singularize: stringUtils.singularize,

    // Path utilities (for template file references)
    joinPath: pathUtils.joinPath,
    getRelativePath: pathUtils.getRelativePath,
    getFileName: pathUtils.getFileName,
    getBaseName: pathUtils.getBaseName,

    // Utility functions
    toIdentifier: stringUtils.toIdentifier,
    toFileName: stringUtils.toFileName,
    truncate: stringUtils.truncate,
    getInitials: stringUtils.getInitials,
    normalize: stringUtils.normalize,

    // File utilities
    existsFile: fileUtils.exists,
    readFile: fileUtils.readFile,
    writeFile: fileUtils.writeFile,
} as const;
