/** @type {import('jest').Config} */
export default {
    // Usar ts-jest para TypeScript
    preset: 'ts-jest/presets/default-esm',

    // Configuración para ES modules
    extensionsToTreatAsEsm: ['.ts'],

    // Environment
    testEnvironment: 'node',

    // Module name mapping para imports
    moduleNameMapping: {
        '^(\\.{1,2}/.*)\\.js$': '$1',
    },

    // Transform settings
    transform: {
        '^.+\\.ts$': ['ts-jest', {
            useESM: true,
            tsconfig: {
                module: 'ESNext',
                target: 'ES2022'
            }
        }]
    },

    // Test file patterns
    testMatch: [
        '**/__tests__/**/*.test.ts',
        '**/*.test.ts'
    ],

    // Coverage settings
    collectCoverageFrom: [
        'src/**/*.ts',
        '!src/**/*.d.ts',
        '!src/**/__tests__/**',
        '!src/**/test.ts'
    ],

    // Coverage thresholds
    coverageThreshold: {
        global: {
            branches: 70,
            functions: 80,
            lines: 80,
            statements: 80
        }
    },

    // Setup files
    setupFilesAfterEnv: ['<rootDir>/src/__tests__/setup.ts'],

    // Timeout for tests
    testTimeout: 30000,

    // Clear mocks between tests
    clearMocks: true,

    // Verbose output
    verbose: true
};