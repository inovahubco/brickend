/**
 * String Utilities for Brickend Templates
 * Helper functions for string transformations and manipulations
 */

/**
 * String transformation options
 */
export interface StringTransformOptions {
    /** Preserve leading/trailing spaces */
    preserveSpaces?: boolean;
    /** Custom separator for joining words */
    separator?: string;
    /** Remove special characters */
    removeSpecial?: boolean;
    /** Preserve numbers */
    preserveNumbers?: boolean;
}

/**
 * Pluralization rules for irregular words
 */
const IRREGULAR_PLURALS: Record<string, string> = {
    'child': 'children',
    'person': 'people',
    'man': 'men',
    'woman': 'women',
    'tooth': 'teeth',
    'foot': 'feet',
    'mouse': 'mice',
    'goose': 'geese',
    'ox': 'oxen',
    'sheep': 'sheep',
    'deer': 'deer',
    'fish': 'fish',
    'series': 'series',
    'species': 'species',
    'datum': 'data',
    'medium': 'media',
    'criterion': 'criteria',
    'phenomenon': 'phenomena',
    'analysis': 'analyses',
    'basis': 'bases',
    'crisis': 'crises',
    'diagnosis': 'diagnoses',
    'thesis': 'theses'
};

/**
 * Convert string to camelCase
 * Examples: 'user_name' -> 'userName', 'user-name' -> 'userName'
 */
export function toCamelCase(str: string, options: StringTransformOptions = {}): string {
    if (!str || typeof str !== 'string') return '';

    const { preserveSpaces = false } = options;

    // Clean the string
    let cleaned = str.trim();

    // Handle spaces
    if (!preserveSpaces) {
        cleaned = cleaned.replace(/\s+/g, ' ');
    }

    // Convert to camelCase
    return cleaned
        .replace(/[-_\s]+(.)?/g, (_, char) => char ? char.toUpperCase() : '')
        .replace(/^[A-Z]/, char => char.toLowerCase());
}

/**
 * Convert string to PascalCase
 * Examples: 'user_name' -> 'UserName', 'user-name' -> 'UserName'
 */
export function toPascalCase(str: string, options: StringTransformOptions = {}): string {
    if (!str || typeof str !== 'string') return '';

    const camelCased = toCamelCase(str, options);
    return camelCased.charAt(0).toUpperCase() + camelCased.slice(1);
}

/**
 * Convert string to kebab-case
 * Examples: 'userName' -> 'user-name', 'UserName' -> 'user-name'
 */
export function toKebabCase(str: string, options: StringTransformOptions = {}): string {
    if (!str || typeof str !== 'string') return '';

    const { separator = '-' } = options;

    return str
        .replace(/([a-z])([A-Z])/g, `$1${separator}$2`)
        .replace(/[\s_]+/g, separator)
        .toLowerCase();
}

/**
 * Convert string to snake_case
 * Examples: 'userName' -> 'user_name', 'UserName' -> 'user_name'
 */
export function toSnakeCase(str: string, options: StringTransformOptions = {}): string {
    if (!str || typeof str !== 'string') return '';

    const { separator = '_' } = options;

    return str
        .replace(/([a-z])([A-Z])/g, `$1${separator}$2`)
        .replace(/[\s-]+/g, separator)
        .toLowerCase();
}

/**
 * Convert string to CONSTANT_CASE
 * Examples: 'userName' -> 'USER_NAME', 'user-name' -> 'USER_NAME'
 */
export function toConstantCase(str: string, options: StringTransformOptions = {}): string {
    return toSnakeCase(str, options).toUpperCase();
}

/**
 * Convert string to Title Case
 * Examples: 'user name' -> 'User Name', 'user-name' -> 'User Name'
 */
export function toTitleCase(str: string, options: StringTransformOptions = {}): string {
    if (!str || typeof str !== 'string') return '';

    const { separator = ' ' } = options;

    return str
        .replace(/[-_]/g, ' ')
        .replace(/([a-z])([A-Z])/g, '$1 $2')
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
        .join(separator);
}

/**
 * Convert string to dot.case
 * Examples: 'userName' -> 'user.name', 'user-name' -> 'user.name'
 */
export function toDotCase(str: string): string {
    return toKebabCase(str, { separator: '.' });
}

/**
 * Convert string to path/case
 * Examples: 'userName' -> 'user/name', 'user-name' -> 'user/name'
 */
export function toPathCase(str: string): string {
    return toKebabCase(str, { separator: '/' });
}

/**
 * Pluralize a word with English rules
 */
export function pluralize(str: string): string {
    if (!str || typeof str !== 'string') return '';

    const word = str.toLowerCase().trim();

    // Check irregular plurals
    if (IRREGULAR_PLURALS[word]) {
        return IRREGULAR_PLURALS[word];
    }

    // Words ending in 's', 'ss', 'sh', 'ch', 'x', 'z'
    if (/[sxz]$/.test(word) || /[sc]h$/.test(word)) {
        return word + 'es';
    }

    // Words ending in consonant + 'y'
    if (/[^aeiou]y$/.test(word)) {
        return word.slice(0, -1) + 'ies';
    }

    // Words ending in 'f' or 'fe'
    if (/f$/.test(word)) {
        return word.slice(0, -1) + 'ves';
    }
    if (/fe$/.test(word)) {
        return word.slice(0, -2) + 'ves';
    }

    // Words ending in consonant + 'o'
    if (/[^aeiou]o$/.test(word)) {
        return word + 'es';
    }

    // Default: add 's'
    return word + 's';
}

/**
 * Singularize a word with English rules
 */
export function singularize(str: string): string {
    if (!str || typeof str !== 'string') return '';

    const word = str.toLowerCase().trim();

    // Check reverse irregular plurals
    for (const [singular, plural] of Object.entries(IRREGULAR_PLURALS)) {
        if (word === plural) {
            return singular;
        }
    }

    // Words ending in 'ies'
    if (/ies$/.test(word)) {
        return word.slice(0, -3) + 'y';
    }

    // Words ending in 'ves'
    if (/ves$/.test(word)) {
        return word.slice(0, -3) + 'f';
    }

    // Words ending in 'es'
    if (/[sxz]es$/.test(word) || /[sc]hes$/.test(word)) {
        return word.slice(0, -2);
    }

    // Words ending in 'oes'
    if (/[^aeiou]oes$/.test(word)) {
        return word.slice(0, -2);
    }

    // Words ending in 's' (but not 'ss')
    if (/[^s]s$/.test(word)) {
        return word.slice(0, -1);
    }

    // Return as-is if no pattern matches
    return word;
}

/**
 * Capitalize first letter of string
 */
export function capitalize(str: string): string {
    if (!str || typeof str !== 'string') return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Uncapitalize first letter of string
 */
export function uncapitalize(str: string): string {
    if (!str || typeof str !== 'string') return '';
    return str.charAt(0).toLowerCase() + str.slice(1);
}

/**
 * Truncate string with ellipsis
 */
export function truncate(str: string, length: number, suffix: string = '...'): string {
    if (!str || typeof str !== 'string') return '';
    if (str.length <= length) return str;
    return str.slice(0, length - suffix.length) + suffix;
}

/**
 * Pad string to specified length
 */
export function pad(
    str: string,
    length: number,
    char: string = ' ',
    direction: 'left' | 'right' | 'both' = 'right'
): string {
    if (!str || typeof str !== 'string') return '';
    if (str.length >= length) return str;

    const padLength = length - str.length;
    const padChar = char.charAt(0);

    switch (direction) {
        case 'left':
            return padChar.repeat(padLength) + str;
        case 'both':
            const leftPad = Math.floor(padLength / 2);
            const rightPad = padLength - leftPad;
            return padChar.repeat(leftPad) + str + padChar.repeat(rightPad);
        case 'right':
        default:
            return str + padChar.repeat(padLength);
    }
}

/**
 * Remove all whitespace from string
 */
export function removeWhitespace(str: string): string {
    if (!str || typeof str !== 'string') return '';
    return str.replace(/\s+/g, '');
}

/**
 * Normalize whitespace (replace multiple spaces with single space)
 */
export function normalizeWhitespace(str: string): string {
    if (!str || typeof str !== 'string') return '';
    return str.replace(/\s+/g, ' ').trim();
}

/**
 * Remove special characters (keep only alphanumeric and spaces)
 */
export function removeSpecialChars(
    str: string,
    options: { keepSpaces?: boolean; keepNumbers?: boolean; additional?: string } = {}
): string {
    if (!str || typeof str !== 'string') return '';

    const { keepSpaces = true, keepNumbers = true, additional = '' } = options;

    let pattern = 'a-zA-Z';
    if (keepNumbers) pattern += '0-9';
    if (keepSpaces) pattern += '\\s';
    if (additional) pattern += additional.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

    const regex = new RegExp(`[^${pattern}]`, 'g');
    return str.replace(regex, '');
}

/**
 * Convert string to slug (URL-friendly)
 */
export function toSlug(str: string, separator: string = '-'): string {
    if (!str || typeof str !== 'string') return '';

    return str
        .toLowerCase()
        .trim()
        .replace(/[^\w\s-]/g, '') // Remove special characters
        .replace(/[\s_-]+/g, separator) // Replace spaces and underscores with separator
        .replace(new RegExp(`^${separator}+|${separator}+$`, 'g'), ''); // Remove leading/trailing separators
}

/**
 * Escape string for use in regular expressions
 */
export function escapeRegex(str: string): string {
    if (!str || typeof str !== 'string') return '';
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Check if string contains only alphanumeric characters
 */
export function isAlphanumeric(str: string): boolean {
    if (!str || typeof str !== 'string') return false;
    return /^[a-zA-Z0-9]+$/.test(str);
}

/**
 * Check if string is a valid variable name
 */
export function isValidVariableName(str: string): boolean {
    if (!str || typeof str !== 'string') return false;
    return /^[a-zA-Z_$][a-zA-Z0-9_$]*$/.test(str);
}

/**
 * Convert string to valid variable name
 */
export function toValidVariableName(str: string): string {
    if (!str || typeof str !== 'string') return '';

    // Remove special characters and normalize
    let cleaned = str
        .replace(/[^a-zA-Z0-9_$]/g, '_')
        .replace(/^[0-9]/, '_$&') // Prefix with underscore if starts with number
        .replace(/_+/g, '_') // Replace multiple underscores with single
        .replace(/^_+|_+$/g, ''); // Remove leading/trailing underscores

    // Ensure it starts with a valid character
    if (!/^[a-zA-Z_$]/.test(cleaned)) {
        cleaned = '_' + cleaned;
    }

    return cleaned || '_';
}

/**
 * Generate random string
 */
export function randomString(
    length: number = 8,
    chars: string = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
): string {
    let result = '';
    for (let i = 0; i < length; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}

/**
 * Generate UUID v4
 */
export function generateUUID(): string {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

/**
 * Word wrap text to specified width
 */
export function wordWrap(str: string, width: number = 80): string {
    if (!str || typeof str !== 'string') return '';

    const words = str.split(' ');
    const lines: string[] = [];
    let currentLine = '';

    for (const word of words) {
        if ((currentLine + word).length > width && currentLine.length > 0) {
            lines.push(currentLine.trim());
            currentLine = word + ' ';
        } else {
            currentLine += word + ' ';
        }
    }

    if (currentLine.trim()) {
        lines.push(currentLine.trim());
    }

    return lines.join('\n');
}

/**
 * Extract initials from name
 */
export function getInitials(str: string, maxLength: number = 2): string {
    if (!str || typeof str !== 'string') return '';

    return str
        .split(/\s+/)
        .map(word => word.charAt(0).toUpperCase())
        .slice(0, maxLength)
        .join('');
}

/**
 * Count words in string
 */
export function wordCount(str: string): number {
    if (!str || typeof str !== 'string') return 0;
    return str.trim().split(/\s+/).filter(word => word.length > 0).length;
}

/**
 * Reverse string
 */
export function reverse(str: string): string {
    if (!str || typeof str !== 'string') return '';
    return str.split('').reverse().join('');
}

/**
 * Check if string is palindrome
 */
export function isPalindrome(str: string): boolean {
    if (!str || typeof str !== 'string') return false;
    const cleaned = str.toLowerCase().replace(/[^a-z0-9]/g, '');
    return cleaned === reverse(cleaned);
}
