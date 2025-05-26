/**
 * Jest setup file
 * This file runs before all tests
 */

// Extend Jest matchers
import 'jest-extended';

// Global test timeout
jest.setTimeout(30000);

// Global variables for testing
declare global {
    var testPort: number;
}

// Assign unique ports for parallel tests
global.testPort = 3000 + Math.floor(Math.random() * 1000);

// Mock console methods in tests if needed
const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;

beforeAll(() => {
    // Suppress console errors/warnings in tests unless needed
    console.error = jest.fn();
    console.warn = jest.fn();
});

afterAll(() => {
    // Restore console methods
    console.error = originalConsoleError;
    console.warn = originalConsoleWarn;
});

// Global test utilities
export const getTestPort = (): number => {
    return global.testPort++;
};

export const waitFor = (ms: number): Promise<void> => {
    return new Promise(resolve => setTimeout(resolve, ms));
};

export const createTestUrl = (port: number, path: string = ''): string => {
    return `http://localhost:${port}${path}`;
};