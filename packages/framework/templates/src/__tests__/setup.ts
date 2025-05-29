/**
 * Jest setup file for Templates package
 */

// Extend Jest matchers
import 'jest-extended';
import * as fs from 'fs-extra';
import * as path from 'path';
import * as os from 'os';

// Global test timeout
jest.setTimeout(30000);

// Global variables for testing
declare global {
    var testPort: number;
    var testTempDir: string;
}

// Assign unique ports for parallel tests
global.testPort = 3000 + Math.floor(Math.random() * 1000);

// Create temporary directory for tests
global.testTempDir = path.join(os.tmpdir(), 'brickend-templates-test');

// Mock console methods in tests if needed
const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;

beforeAll(() => {
    // Suppress console errors/warnings in tests unless needed
    console.error = jest.fn();
    console.warn = jest.fn();
});

afterAll(async () => {
    // Restore console methods
    console.error = originalConsoleError;
    console.warn = originalConsoleWarn;

    // Clean up test temp directory
    try {
        await fs.remove(global.testTempDir);
    } catch (error) {
        // Ignore cleanup errors
    }
});

// Global test utilities from core
export const getTestPort = (): number => {
    return global.testPort++;
};

export const waitFor = (ms: number): Promise<void> => {
    return new Promise(resolve => setTimeout(resolve, ms));
};

export const createTestUrl = (port: number, path: string = ''): string => {
    return `http://localhost:${port}${path}`;
};

// Templates-specific test utilities
export const createTempTestDir = async (name: string): Promise<string> => {
    const testDir = path.join(global.testTempDir, name);
    await fs.ensureDir(testDir);
    return testDir;
};

export const cleanupTestDir = async (dir: string): Promise<void> => {
    try {
        await fs.remove(dir);
    } catch (error) {
        // Ignore cleanup errors
    }
};

export const fileExists = async (filePath: string): Promise<boolean> => {
    try {
        await fs.access(filePath);
        return true;
    } catch {
        return false;
    }
};

export const readTestFile = async (filePath: string): Promise<string> => {
    return fs.readFile(filePath, 'utf-8');
};