/** @type {import('jest').Config} */
export default {
    preset: 'ts-jest/presets/default-esm',
    testEnvironment: 'node',
    extensionsToTreatAsEsm: ['.ts'],

    moduleNameMapper: {
        '^(\\.{1,2}/.*)\\.js$': '$1'
    },

    transform: {
        '^.+\\.tsx?$': ['ts-jest', {
            useESM: true,
            tsconfig: { module: 'ESNext', target: 'ES2022' }
        }]
    },
    transformIgnorePatterns: ['/node_modules/'],

    testMatch: [
        '**/__tests__/**/*.test.ts',
        '**/?(*.)+(spec|test).ts'
    ],

    collectCoverageFrom: [
        'src/**/*.{ts,tsx}',
        '!src/**/*.d.ts'
    ],
    coverageThreshold: {
        global: {
            branches: 70,
            functions: 80,
            lines: 80,
            statements: 80
        }
    },

    setupFilesAfterEnv: ['<rootDir>/src/__tests__/setup.ts'],
    clearMocks: true,
    verbose: true
};