/**
 * String transformation utilities for Brickend
 * These functions are used internally and also exposed to templates
 */

/**
 * Convert string to camelCase
 * @example camelCase('hello world') => 'helloWorld'
 * @example camelCase('user-profile') => 'userProfile'
 * @example camelCase('USER_NAME') => 'userName'
 */
export function camelCase(str: string): string {
    return str
        .toLowerCase()
        .replace(/[^a-zA-Z0-9]+(.)/g, (_, chr) => chr.toUpperCase())
        .replace(/^[A-Z]/, (chr) => chr.toLowerCase());
}

/**
 * Convert string to PascalCase
 * @example pascalCase('hello world') => 'HelloWorld'
 * @example pascalCase('user-profile') => 'UserProfile'
 * @example pascalCase('USER_NAME') => 'UserName'
 */
export function pascalCase(str: string): string {
    const camelCased = camelCase(str);
    return camelCased.charAt(0).toUpperCase() + camelCased.slice(1);
}

/**
 * Convert string to kebab-case
 * @example kebabCase('HelloWorld') => 'hello-world'
 * @example kebabCase('userProfile') => 'user-profile'
 * @example kebabCase('USER_NAME') => 'user-name'
 */
export function kebabCase(str: string): string {
    return str
        .replace(/([a-z])([A-Z])/g, '$1-$2')
        .replace(/[\s_]+/g, '-')
        .toLowerCase();
}

/**
 * Convert string to snake_case
 * @example snakeCase('HelloWorld') => 'hello_world'
 * @example snakeCase('userProfile') => 'user_profile'
 * @example snakeCase('user-name') => 'user_name'
 */
export function snakeCase(str: string): string {
    return str
        .replace(/([a-z])([A-Z])/g, '$1_$2')
        .replace(/[\s-]+/g, '_')
        .toLowerCase();
}

/**
 * Convert string to CONSTANT_CASE
 * @example constantCase('hello world') => 'HELLO_WORLD'
 * @example constantCase('userProfile') => 'USER_PROFILE'
 */
export function constantCase(str: string): string {
    return snakeCase(str).toUpperCase();
}

/**
 * Capitalize first letter of string
 * @example capitalize('hello') => 'Hello'
 * @example capitalize('WORLD') => 'WORLD'
 */
export function capitalize(str: string): string {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Convert entire string to lowercase
 * @example lowercase('Hello World') => 'hello world'
 */
export function lowercase(str: string): string {
    return str.toLowerCase();
}

/**
 * Convert entire string to uppercase
 * @example uppercase('hello world') => 'HELLO WORLD'
 */
export function uppercase(str: string): string {
    return str.toUpperCase();
}

/**
 * Simple pluralization (English)
 * Note: This is a basic implementation. For production, consider using a library like 'pluralize'
 * @example pluralize('user') => 'users'
 * @example pluralize('category') => 'categories'
 * @example pluralize('child') => 'children'
 */
export function pluralize(str: string): string {
    const word = str.toLowerCase();

    // Special cases
    const irregulars: Record<string, string> = {
        'child': 'children',
        'person': 'people',
        'man': 'men',
        'woman': 'women',
        'tooth': 'teeth',
        'foot': 'feet',
        'mouse': 'mice',
        'goose': 'geese',
    };

    if (irregulars[word]) {
        return irregulars[word];
    }

    // Words ending in 'y' preceded by a consonant
    if (word.endsWith('y') && !/[aeiou]y$/.test(word)) {
        return word.slice(0, -1) + 'ies';
    }

    // Words ending in 's', 'ss', 'sh', 'ch', 'x', 'z'
    if (/[sxz]$/.test(word) || /[sh]$/.test(word) || word.endsWith('ch')) {
        return word + 'es';
    }

    // Words ending in 'f' or 'fe'
    if (word.endsWith('f')) {
        return word.slice(0, -1) + 'ves';
    }
    if (word.endsWith('fe')) {
        return word.slice(0, -2) + 'ves';
    }

    // Default: add 's'
    return word + 's';
}

/**
 * Simple singularization (English)
 * Note: This is a basic implementation. For production, consider using a library like 'pluralize'
 * @example singularize('users') => 'user'
 * @example singularize('categories') => 'category'
 * @example singularize('children') => 'child'
 */
export function singularize(str: string): string {
    const word = str.toLowerCase();

    // Special cases
    const irregulars: Record<string, string> = {
        'children': 'child',
        'people': 'person',
        'men': 'man',
        'women': 'woman',
        'teeth': 'tooth',
        'feet': 'foot',
        'mice': 'mouse',
        'geese': 'goose',
    };

    if (irregulars[word]) {
        return irregulars[word];
    }

    // Words ending in 'ies'
    if (word.endsWith('ies')) {
        return word.slice(0, -3) + 'y';
    }

    // Words ending in 'ves'
    if (word.endsWith('ves')) {
        return word.slice(0, -3) + 'f';
    }

    // Words ending in 'es' (but not 'oes')
    if (word.endsWith('es') && !word.endsWith('oes')) {
        // Check if removing 'es' leaves a valid word
        const withoutEs = word.slice(0, -2);
        if (/[sxz]$/.test(withoutEs) || /[sh]$/.test(withoutEs) || withoutEs.endsWith('ch')) {
            return withoutEs;
        }
    }

    // Words ending in 's' (but not 'ss')
    if (word.endsWith('s') && !word.endsWith('ss')) {
        return word.slice(0, -1);
    }

    // Return as-is if no rule applies
    return word;
}

/**
 * Clean and normalize string for use as identifier
 * @example toIdentifier('Hello World!') => 'HelloWorld'
 * @example toIdentifier('user-name@123') => 'userName123'
 */
export function toIdentifier(str: string): string {
    return str
        .replace(/[^a-zA-Z0-9\s-_]/g, '') // Remove special characters
        .replace(/\s+/g, ' ') // Normalize whitespace
        .trim()
        .split(/[\s-_]+/)
        .map((word, index) =>
            index === 0
                ? word.toLowerCase()
                : capitalize(word.toLowerCase())
        )
        .join('');
}

/**
 * Convert string to valid filename
 * @example toFileName('Hello World!') => 'hello-world'
 * @example toFileName('User Profile (Admin)') => 'user-profile-admin'
 */
export function toFileName(str: string): string {
    return str
        .replace(/[^a-zA-Z0-9\s-_.]/g, '') // Remove invalid filename characters
        .replace(/\s+/g, '-') // Replace spaces with hyphens
        .replace(/[-_]+/g, '-') // Normalize separators
        .toLowerCase()
        .replace(/^-+|-+$/g, ''); // Remove leading/trailing hyphens
}

/**
 * Truncate string to specified length with ellipsis
 * @example truncate('Hello World', 8) => 'Hello...'
 * @example truncate('Short', 10) => 'Short'
 */
export function truncate(str: string, length: number, suffix: string = '...'): string {
    if (str.length <= length) {
        return str;
    }
    return str.substring(0, length - suffix.length) + suffix;
}

/**
 * Pad string to specified length
 * @example padStart('5', 3, '0') => '005'
 * @example padEnd('hello', 8, '.') => 'hello...'
 */
export function padStart(str: string, length: number, fillString: string = ' '): string {
    return str.padStart(length, fillString);
}

export function padEnd(str: string, length: number, fillString: string = ' '): string {
    return str.padEnd(length, fillString);
}

/**
 * Extract initials from a name
 * @example getInitials('John Doe') => 'JD'
 * @example getInitials('Mary Jane Watson') => 'MJW'
 */
export function getInitials(str: string): string {
    return str
        .split(/\s+/)
        .map(word => word.charAt(0).toUpperCase())
        .join('');
}

/**
 * Check if string is empty or contains only whitespace
 * @example isBlank('') => true
 * @example isBlank('   ') => true
 * @example isBlank('hello') => false
 */
export function isBlank(str: string): boolean {
    return !str || str.trim().length === 0;
}

/**
 * Remove extra whitespace and normalize string
 * @example normalize('  hello   world  ') => 'hello world'
 */
export function normalize(str: string): string {
    return str.replace(/\s+/g, ' ').trim();
}

/**
 * Utility object containing all string functions for easy import
 * This is what gets passed to template context
 */
export const stringUtils = {
    camelCase,
    pascalCase,
    kebabCase,
    snakeCase,
    constantCase,
    capitalize,
    lowercase,
    uppercase,
    pluralize,
    singularize,
    toIdentifier,
    toFileName,
    truncate,
    padStart,
    padEnd,
    getInitials,
    isBlank,
    normalize,
} as const;