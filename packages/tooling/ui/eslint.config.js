import baseConfig from '../../tooling/eslint-config/base.js';

export default [
    ...baseConfig,
    {
        files: ['src/**/*.ts', 'src/**/*.tsx'],
    },
];