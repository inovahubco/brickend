/**
 * Validation Utilities for Brickend Templates
 * Helper functions for input validation and sanitization
 */

import * as path from 'path';
import { isValidVariableName } from './string-utils.js';
import type {
    TemplateField,
    TemplateFieldType,
    TemplateContext,
    TemplateDefinition,
    TemplateMetadata
} from '../types/index.js';

/**
 * Validation result interface
 */
export interface ValidationResult {
    isValid: boolean;
    errors: ValidationError[];
    warnings: ValidationWarning[];
}

/**
 * Validation error interface
 */
export interface ValidationError {
    field: string;
    message: string;
    code: string;
    value?: any;
    suggestion?: string;
}

/**
 * Validation warning interface
 */
export interface ValidationWarning {
    field: string;
    message: string;
    code: string;
    value?: any;
    suggestion?: string;
}

/**
 * Project name validation options
 */
export interface ProjectNameValidationOptions {
    /** Minimum length */
    minLength?: number;
    /** Maximum length */
    maxLength?: number;
    /** Allow numbers */
    allowNumbers?: boolean;
    /** Allow hyphens */
    allowHyphens?: boolean;
    /** Allow underscores */
    allowUnderscores?: boolean;
    /** Reserved names to disallow */
    reservedNames?: string[];
    /** Custom pattern */
    pattern?: RegExp;
}

/**
 * Field validation options
 */
export interface FieldValidationOptions {
    /** Require at least one field */
    requireFields?: boolean;
    /** Maximum number of fields */
    maxFields?: number;
    /** Allowed field types */
    allowedTypes?: TemplateFieldType[];
    /** Required fields */
    requiredFields?: string[];
}

/**
 * Reserved keywords that cannot be used as names
 */
const RESERVED_KEYWORDS = [
    // JavaScript reserved words
    'abstract', 'arguments', 'await', 'boolean', 'break', 'byte', 'case', 'catch',
    'char', 'class', 'const', 'continue', 'debugger', 'default', 'delete', 'do',
    'double', 'else', 'enum', 'eval', 'export', 'extends', 'false', 'final',
    'finally', 'float', 'for', 'function', 'goto', 'if', 'implements', 'import',
    'in', 'instanceof', 'int', 'interface', 'let', 'long', 'native', 'new',
    'null', 'package', 'private', 'protected', 'public', 'return', 'short',
    'static', 'super', 'switch', 'synchronized', 'this', 'throw', 'throws',
    'transient', 'true', 'try', 'typeof', 'var', 'void', 'volatile', 'while',
    'with', 'yield',

    // Node.js globals
    'global', 'process', 'buffer', 'console', 'module', 'exports', 'require',

    // Common names to avoid
    'test', 'tests', 'spec', 'specs', 'node_modules', 'package', 'src', 'dist',
    'build', 'public', 'assets', 'static', 'config', 'lib', 'utils', 'helpers',

    // OS reserved names
    'con', 'prn', 'aux', 'nul', 'com1', 'com2', 'com3', 'com4', 'com5', 'com6',
    'com7', 'com8', 'com9', 'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6',
    'lpt7', 'lpt8', 'lpt9'
];

/**
 * Common project names that should be avoided
 */
const DISCOURAGED_PROJECT_NAMES = [
    'app', 'api', 'server', 'client', 'frontend', 'backend', 'web', 'website',
    'project', 'demo', 'example', 'sample', 'template', 'boilerplate', 'starter',
    'hello-world', 'test-app', 'my-app', 'untitled'
];

/**
 * Valid field types for templates
 */
const VALID_FIELD_TYPES: TemplateFieldType[] = [
    'string', 'number', 'boolean', 'date', 'email', 'url', 'text',
    'json', 'uuid', 'array', 'object'
];

/**
 * Validate project name
 */
export function validateProjectName(
    name: string,
    options: ProjectNameValidationOptions = {}
): ValidationResult {
    const errors: ValidationError[] = [];
    const warnings: ValidationWarning[] = [];

    const {
        minLength = 2,
        maxLength = 50,
        allowNumbers = true,
        allowHyphens = true,
        allowUnderscores = true,
        reservedNames = [],
        pattern
    } = options;

    // Check if name exists
    if (!name || typeof name !== 'string') {
        errors.push({
            field: 'name',
            message: 'Project name is required',
            code: 'REQUIRED'
        });
        return { isValid: false, errors, warnings };
    }

    const trimmedName = name.trim();

    // Check length
    if (trimmedName.length < minLength) {
        errors.push({
            field: 'name',
            message: `Project name must be at least ${minLength} characters`,
            code: 'MIN_LENGTH',
            value: trimmedName.length
        });
    }

    if (trimmedName.length > maxLength) {
        errors.push({
            field: 'name',
            message: `Project name must be no more than ${maxLength} characters`,
            code: 'MAX_LENGTH',
            value: trimmedName.length
        });
    }

    // Check if it starts with a letter
    if (!/^[a-zA-Z]/.test(trimmedName)) {
        errors.push({
            field: 'name',
            message: 'Project name must start with a letter',
            code: 'INVALID_START',
            value: trimmedName.charAt(0)
        });
    }

    // Build allowed characters pattern
    let allowedPattern = 'a-zA-Z';
    if (allowNumbers) allowedPattern += '0-9';
    if (allowHyphens) allowedPattern += '-';
    if (allowUnderscores) allowedPattern += '_';

    const allowedRegex = new RegExp(`^[${allowedPattern}]+$`);

    if (!allowedRegex.test(trimmedName)) {
        const disallowed = trimmedName.replace(new RegExp(`[${allowedPattern}]`, 'g'), '');
        errors.push({
            field: 'name',
            message: `Project name contains invalid characters: ${Array.from(new Set(disallowed)).join(', ')}`,
            code: 'INVALID_CHARACTERS',
            value: disallowed
        });
    }

    // Check custom pattern
    if (pattern && !pattern.test(trimmedName)) {
        errors.push({
            field: 'name',
            message: 'Project name does not match required pattern',
            code: 'PATTERN_MISMATCH',
            value: pattern.toString()
        });
    }

    // Check reserved names
    const allReservedNames = [...RESERVED_KEYWORDS, ...reservedNames];
    if (allReservedNames.includes(trimmedName.toLowerCase())) {
        errors.push({
            field: 'name',
            message: `"${trimmedName}" is a reserved name and cannot be used`,
            code: 'RESERVED_NAME',
            value: trimmedName,
            suggestion: `${trimmedName}-app`
        });
    }

    // Check discouraged names (warnings)
    if (DISCOURAGED_PROJECT_NAMES.includes(trimmedName.toLowerCase())) {
        warnings.push({
            field: 'name',
            message: `"${trimmedName}" is a generic name. Consider using a more descriptive name`,
            code: 'GENERIC_NAME',
            value: trimmedName,
            suggestion: `my-${trimmedName}`
        });
    }

    // Check if name is valid variable name
    if (!isValidVariableName(trimmedName.replace(/[-]/g, '_'))) {
        warnings.push({
            field: 'name',
            message: 'Project name may cause issues when used as a variable name',
            code: 'VARIABLE_NAME_WARNING',
            value: trimmedName
        });
    }

    return {
        isValid: errors.length === 0,
        errors,
        warnings
    };
}

/**
 * Validate resource name
 */
export function validateResourceName(name: string): ValidationResult {
    const errors: ValidationError[] = [];
    const warnings: ValidationWarning[] = [];

    if (!name || typeof name !== 'string') {
        errors.push({
            field: 'name',
            message: 'Resource name is required',
            code: 'REQUIRED'
        });
        return { isValid: false, errors, warnings };
    }

    const trimmedName = name.trim();

    // Resource names should be PascalCase or camelCase
    if (!/^[A-Za-z][A-Za-z0-9]*$/.test(trimmedName)) {
        errors.push({
            field: 'name',
            message: 'Resource name must contain only letters and numbers, starting with a letter',
            code: 'INVALID_FORMAT',
            value: trimmedName
        });
    }

    // Check length (reasonable for class names)
    if (trimmedName.length < 2) {
        errors.push({
            field: 'name',
            message: 'Resource name must be at least 2 characters',
            code: 'MIN_LENGTH',
            value: trimmedName.length
        });
    }

    if (trimmedName.length > 30) {
        warnings.push({
            field: 'name',
            message: 'Resource name is quite long. Consider a shorter name',
            code: 'LONG_NAME',
            value: trimmedName.length
        });
    }

    // Check if reserved
    if (RESERVED_KEYWORDS.includes(trimmedName.toLowerCase())) {
        errors.push({
            field: 'name',
            message: `"${trimmedName}" is a reserved name and cannot be used`,
            code: 'RESERVED_NAME',
            value: trimmedName
        });
    }

    // Suggest PascalCase if not already
    if (!/^[A-Z]/.test(trimmedName)) {
        warnings.push({
            field: 'name',
            message: 'Resource names typically use PascalCase (e.g., UserProfile)',
            code: 'NAMING_CONVENTION',
            value: trimmedName,
            suggestion: trimmedName.charAt(0).toUpperCase() + trimmedName.slice(1)
        });
    }

    return {
        isValid: errors.length === 0,
        errors,
        warnings
    };
}

/**
 * Validate template fields
 */
export function validateTemplateFields(
    fields: TemplateField[],
    options: FieldValidationOptions = {}
): ValidationResult {
    const errors: ValidationError[] = [];
    const warnings: ValidationWarning[] = [];

    const {
        requireFields = true,
        maxFields = 20,
        allowedTypes = VALID_FIELD_TYPES,
        requiredFields = []
    } = options;

    // Check if fields exist
    if (!Array.isArray(fields)) {
        errors.push({
            field: 'fields',
            message: 'Fields must be an array',
            code: 'INVALID_TYPE'
        });
        return { isValid: false, errors, warnings };
    }

    // Check minimum fields
    if (requireFields && fields.length === 0) {
        errors.push({
            field: 'fields',
            message: 'At least one field is required',
            code: 'MIN_FIELDS',
            value: fields.length
        });
    }

    // Check maximum fields
    if (fields.length > maxFields) {
        errors.push({
            field: 'fields',
            message: `Too many fields. Maximum allowed: ${maxFields}`,
            code: 'MAX_FIELDS',
            value: fields.length
        });
    }

    // Validate each field
    const fieldNames = new Set<string>();

    fields.forEach((field, index) => {
        const fieldPrefix = `fields[${index}]`;

        // Validate field structure
        if (!field || typeof field !== 'object') {
            errors.push({
                field: fieldPrefix,
                message: 'Field must be an object',
                code: 'INVALID_FIELD_TYPE'
            });
            return;
        }

        // Validate field name
        if (!field.name || typeof field.name !== 'string') {
            errors.push({
                field: `${fieldPrefix}.name`,
                message: 'Field name is required and must be a string',
                code: 'REQUIRED'
            });
        } else {
            const fieldName = field.name.trim();

            // Check for duplicate names
            if (fieldNames.has(fieldName.toLowerCase())) {
                errors.push({
                    field: `${fieldPrefix}.name`,
                    message: `Duplicate field name: "${fieldName}"`,
                    code: 'DUPLICATE_NAME',
                    value: fieldName
                });
            }
            fieldNames.add(fieldName.toLowerCase());

            // Validate field name format
            if (!/^[a-zA-Z][a-zA-Z0-9_]*$/.test(fieldName)) {
                errors.push({
                    field: `${fieldPrefix}.name`,
                    message: 'Field name must start with a letter and contain only letters, numbers, and underscores',
                    code: 'INVALID_NAME_FORMAT',
                    value: fieldName
                });
            }

            // Check for reserved names
            if (RESERVED_KEYWORDS.includes(fieldName.toLowerCase())) {
                errors.push({
                    field: `${fieldPrefix}.name`,
                    message: `"${fieldName}" is a reserved name and cannot be used as a field name`,
                    code: 'RESERVED_FIELD_NAME',
                    value: fieldName
                });
            }

            // Check naming convention
            if (!/^[a-z]/.test(fieldName)) {
                warnings.push({
                    field: `${fieldPrefix}.name`,
                    message: 'Field names typically use camelCase (e.g., firstName)',
                    code: 'NAMING_CONVENTION',
                    value: fieldName
                });
            }
        }

        // Validate field type
        if (!field.type || typeof field.type !== 'string') {
            errors.push({
                field: `${fieldPrefix}.type`,
                message: 'Field type is required and must be a string',
                code: 'REQUIRED'
            });
        } else if (!allowedTypes.includes(field.type)) {
            errors.push({
                field: `${fieldPrefix}.type`,
                message: `Invalid field type: "${field.type}". Allowed types: ${allowedTypes.join(', ')}`,
                code: 'INVALID_TYPE',
                value: field.type
            });
        }

        // Validate validation rules if present
        if (field.validation) {
            validateFieldValidationRules(field, `${fieldPrefix}.validation`, errors, warnings);
        }

        // Check for common field patterns
        if (field.name && field.type) {
            validateFieldPatterns(field, fieldPrefix, warnings);
        }
    });

    // Check for required fields
    requiredFields.forEach(requiredField => {
        if (!fields.some(field => field.name === requiredField)) {
            errors.push({
                field: 'fields',
                message: `Required field "${requiredField}" is missing`,
                code: 'MISSING_REQUIRED_FIELD',
                value: requiredField
            });
        }
    });

    return {
        isValid: errors.length === 0,
        errors,
        warnings
    };
}

/**
 * Validate field validation rules
 */
function validateFieldValidationRules(
    field: TemplateField,
    fieldPrefix: string,
    errors: ValidationError[],
    warnings: ValidationWarning[]
): void {
    const validation = field.validation!;

    // Validate min/max for different types
    if (field.type === 'string' || field.type === 'text') {
        if (validation.min !== undefined && validation.min < 0) {
            errors.push({
                field: `${fieldPrefix}.min`,
                message: 'Minimum length cannot be negative',
                code: 'INVALID_MIN',
                value: validation.min
            });
        }

        if (validation.max !== undefined && validation.max < 1) {
            errors.push({
                field: `${fieldPrefix}.max`,
                message: 'Maximum length must be at least 1',
                code: 'INVALID_MAX',
                value: validation.max
            });
        }
    }

    if (field.type === 'number') {
        if (validation.min !== undefined && validation.max !== undefined && validation.min > validation.max) {
            errors.push({
                field: `${fieldPrefix}`,
                message: 'Minimum value cannot be greater than maximum value',
                code: 'INVALID_RANGE',
                value: { min: validation.min, max: validation.max }
            });
        }
    }

    // Validate pattern
    if (validation.pattern) {
        try {
            new RegExp(validation.pattern);
        } catch (error) {
            errors.push({
                field: `${fieldPrefix}.pattern`,
                message: 'Invalid regular expression pattern',
                code: 'INVALID_PATTERN',
                value: validation.pattern
            });
        }
    }
}

/**
 * Validate common field patterns
 */
function validateFieldPatterns(
    field: TemplateField,
    fieldPrefix: string,
    warnings: ValidationWarning[]
): void {
    const { name, type } = field;

    // Suggest better types for common field names
    const typesSuggestions: Record<string, TemplateFieldType> = {
        'email': 'email',
        'website': 'url',
        'url': 'url',
        'link': 'url',
        'description': 'text',
        'bio': 'text',
        'notes': 'text',
        'content': 'text',
        'id': 'uuid',
        'userId': 'uuid',
        'createdAt': 'date',
        'updatedAt': 'date',
        'birthDate': 'date',
        'birthday': 'date'
    };

    const suggestedType = typesSuggestions[name.toLowerCase()];
    if (suggestedType && type !== suggestedType) {
        warnings.push({
            field: `${fieldPrefix}.type`,
            message: `Consider using type "${suggestedType}" for field "${name}"`,
            code: 'TYPE_SUGGESTION',
            value: type,
            suggestion: suggestedType
        });
    }
}

/**
 * Validate template context
 */
export function validateTemplateContext(context: TemplateContext): ValidationResult {
    const errors: ValidationError[] = [];
    const warnings: ValidationWarning[] = [];

    // Validate required properties
    if (!context.name || typeof context.name !== 'string') {
        errors.push({
            field: 'name',
            message: 'Context name is required and must be a string',
            code: 'REQUIRED'
        });
    }

    if (!context.names || typeof context.names !== 'object') {
        errors.push({
            field: 'names',
            message: 'Context names object is required',
            code: 'REQUIRED'
        });
    } else {
        const requiredNameFormats = ['camelCase', 'pascalCase', 'kebabCase', 'snakeCase', 'plural', 'singular'];
        requiredNameFormats.forEach(format => {
            if (!context.names[format as keyof typeof context.names]) {
                errors.push({
                    field: `names.${format}`,
                    message: `Missing required name format: ${format}`,
                    code: 'MISSING_NAME_FORMAT',
                    value: format
                });
            }
        });
    }

    // Validate fields if present
    if (context.fields) {
        const fieldsValidation = validateTemplateFields(context.fields);
        errors.push(...fieldsValidation.errors.map(error => ({
            ...error,
            field: `context.${error.field}`
        })));
        warnings.push(...fieldsValidation.warnings.map(warning => ({
            ...warning,
            field: `context.${warning.field}`
        })));
    }

    return {
        isValid: errors.length === 0,
        errors,
        warnings
    };
}

/**
 * Validate template definition
 */
export function validateTemplateDefinition(template: TemplateDefinition): ValidationResult {
    const errors: ValidationError[] = [];
    const warnings: ValidationWarning[] = [];

    // Validate required properties
    if (!template.id || typeof template.id !== 'string') {
        errors.push({
            field: 'id',
            message: 'Template id is required and must be a string',
            code: 'REQUIRED'
        });
    }

    if (!template.name || typeof template.name !== 'string') {
        errors.push({
            field: 'name',
            message: 'Template name is required and must be a string',
            code: 'REQUIRED'
        });
    }

    if (!template.category || !['project', 'resource', 'config', 'component'].includes(template.category)) {
        errors.push({
            field: 'category',
            message: 'Template category must be one of: project, resource, config, component',
            code: 'INVALID_CATEGORY',
            value: template.category
        });
    }

    if (!template.path || typeof template.path !== 'string') {
        errors.push({
            field: 'path',
            message: 'Template path is required and must be a string',
            code: 'REQUIRED'
        });
    }

    if (!Array.isArray(template.files)) {
        errors.push({
            field: 'files',
            message: 'Template files must be an array',
            code: 'INVALID_TYPE'
        });
    } else {
        // Validate each file
        template.files.forEach((file, index) => {
            if (!file.source || typeof file.source !== 'string') {
                errors.push({
                    field: `files[${index}].source`,
                    message: 'File source is required and must be a string',
                    code: 'REQUIRED'
                });
            }

            if (!file.target || typeof file.target !== 'string') {
                errors.push({
                    field: `files[${index}].target`,
                    message: 'File target is required and must be a string',
                    code: 'REQUIRED'
                });
            }
        });
    }

    return {
        isValid: errors.length === 0,
        errors,
        warnings
    };
}

/**
 * Validate file path
 */
export function validateFilePath(filePath: string, options: {
    mustExist?: boolean;
    allowAbsolute?: boolean;
    allowRelative?: boolean;
    allowedExtensions?: string[];
} = {}): ValidationResult {
    const errors: ValidationError[] = [];
    const warnings: ValidationWarning[] = [];

    const {
        allowAbsolute = true,
        allowRelative = true,
        allowedExtensions = []
    } = options;

    if (!filePath || typeof filePath !== 'string') {
        errors.push({
            field: 'path',
            message: 'File path is required and must be a string',
            code: 'REQUIRED'
        });
        return { isValid: false, errors, warnings };
    }

    // Check path format
    if (path.isAbsolute(filePath) && !allowAbsolute) {
        errors.push({
            field: 'path',
            message: 'Absolute paths are not allowed',
            code: 'ABSOLUTE_PATH_NOT_ALLOWED',
            value: filePath
        });
    }

    if (!path.isAbsolute(filePath) && !allowRelative) {
        errors.push({
            field: 'path',
            message: 'Relative paths are not allowed',
            code: 'RELATIVE_PATH_NOT_ALLOWED',
            value: filePath
        });
    }

    // Check for dangerous patterns
    if (filePath.includes('..')) {
        warnings.push({
            field: 'path',
            message: 'Path contains ".." which may be unsafe',
            code: 'UNSAFE_PATH',
            value: filePath
        });
    }

    // Check extension if specified
    if (allowedExtensions.length > 0) {
        const ext = path.extname(filePath).toLowerCase();
        if (ext && !allowedExtensions.includes(ext)) {
            errors.push({
                field: 'path',
                message: `File extension "${ext}" is not allowed. Allowed: ${allowedExtensions.join(', ')}`,
                code: 'INVALID_EXTENSION',
                value: ext
            });
        }
    }

    return {
        isValid: errors.length === 0,
        errors,
        warnings
    };
}

/**
 * Sanitize string for safe usage
 */
export function sanitizeString(str: string, options: {
    maxLength?: number;
    allowedChars?: RegExp;
    removeWhitespace?: boolean;
} = {}): string {
    if (!str || typeof str !== 'string') return '';

    const {
        maxLength = 1000,
        allowedChars = /[a-zA-Z0-9\s-_\.]/,
        removeWhitespace = false
    } = options;

    let sanitized = str.trim();

    // Remove disallowed characters
    sanitized = sanitized
        .split('')
        .filter(char => allowedChars.test(char))
        .join('');

    // Remove whitespace if requested
    if (removeWhitespace) {
        sanitized = sanitized.replace(/\s+/g, '');
    }

    // Truncate if too long
    if (sanitized.length > maxLength) {
        sanitized = sanitized.slice(0, maxLength);
    }

    return sanitized;
}

/**
 * Check if value is safe for templates
 */
export function isSafeTemplateValue(value: any): boolean {
    if (value === null || value === undefined) return true;
    if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return true;
    if (Array.isArray(value)) return value.every(isSafeTemplateValue);
    if (typeof value === 'object') {
        return Object.values(value).every(isSafeTemplateValue);
    }
    return false;
}

/**
 * Format validation errors for display
 */
export function formatValidationErrors(result: ValidationResult): string {
    const messages: string[] = [];

    if (result.errors.length > 0) {
        messages.push('Errors:');
        result.errors.forEach(error => {
            let message = `  • ${error.field}: ${error.message}`;
            if (error.suggestion) {
                message += ` (suggestion: ${error.suggestion})`;
            }
            messages.push(message);
        });
    }

    if (result.warnings.length > 0) {
        if (messages.length > 0) messages.push('');
        messages.push('Warnings:');
        result.warnings.forEach(warning => {
            let message = `  • ${warning.field}: ${warning.message}`;
            if (warning.suggestion) {
                message += ` (suggestion: ${warning.suggestion})`;
            }
            messages.push(message);
        });
    }

    return messages.join('\n');
}