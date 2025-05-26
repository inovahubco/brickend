/**
 * Jest tests for Brickend Core
 */

import { createBrickend, createPlugin } from '../index.js';
import { getTestPort, createTestUrl } from './setup.js';

describe('Brickend Core', () => {
    let app: ReturnType<typeof createBrickend>;

    beforeEach(() => {
        app = createBrickend({
            logger: false
        });
    });

    afterEach(async () => {
        if (app.isListening()) {
            await app.close();
        }
    });

    describe('Brickend instance', () => {
        test('should create instance successfully', () => {
            expect(app).toBeDefined();
            expect(app.getApp()).toBeDefined();
            expect(app.getPlugins()).toEqual([]);
        });

        test('should have FastifyInstance', () => {
            const fastify = app.getApp();
            expect(fastify).toBeDefined();
            expect(typeof fastify.get).toBe('function');
            expect(typeof fastify.post).toBe('function');
        });
    });

    describe('Plugin system', () => {
        test('should register plugin successfully', async () => {
            const testPlugin = createPlugin('test', async (fastify) => {
                fastify.get('/test', async () => ({ test: true }));
            });

            const result = await app.register(testPlugin);

            expect(result.success).toBe(true);
            expect(result.plugin.name).toBe('test');
            expect(app.getPlugins()).toHaveLength(1);
            expect(app.hasPlugin('test')).toBe(true);
            expect(app.getPlugin('test')).toBe(testPlugin);
        });

        test('should register multiple plugins', async () => {
            const plugin1 = createPlugin('plugin1', async () => { });
            const plugin2 = createPlugin('plugin2', async () => { });

            const results = await app.registerPlugins([
                { plugin: plugin1 },
                { plugin: plugin2, options: { test: true } }
            ]);

            expect(results).toHaveLength(2);
            expect(results[0]?.success).toBe(true);
            expect(results[1]?.success).toBe(true);
            expect(app.getPlugins()).toHaveLength(2);
        });

        test('should handle plugin registration errors', async () => {
            const errorPlugin = createPlugin('error', async () => {
                throw new Error('Plugin registration failed');
            });

            const result = await app.register(errorPlugin);

            expect(result.success).toBe(false);
            expect(result.error).toBeDefined();
            expect(result.error?.message).toBe('Plugin registration failed');
        });
    });

    describe('Server lifecycle', () => {
        test('should start and stop server', async () => {
            const port = getTestPort();

            // Start server
            const address = await app.listen({ port });
            expect(address).toContain(`${port}`);
            expect(app.isListening()).toBe(true);

            // Stop server
            await app.close();
            expect(app.isListening()).toBe(false);
        });

        test('should handle ready callback', async () => {
            const callback = jest.fn();
            await app.ready(callback);
            expect(callback).toHaveBeenCalled();
        });

        test('should handle async ready callback', async () => {
            let called = false;
            await app.ready(async () => {
                await new Promise(resolve => setTimeout(resolve, 10));
                called = true;
            });
            expect(called).toBe(true);
        });
    });

    describe('Health check', () => {
        test('should register health check endpoint', async () => {
            const port = getTestPort();
            app.registerHealthCheck('/status');

            await app.listen({ port });

            const response = await fetch(createTestUrl(port, '/status'));
            const data = await response.json();

            expect(response.status).toBe(200);
            expect(data.status).toBe('ok');
            expect(data.timestamp).toBeDefined();
            expect(data.uptime).toBeDefined();
            expect(Array.isArray(data.plugins)).toBe(true);
        });
    });

    describe('Error handling', () => {
        test('should handle 404 errors', async () => {
            const port = getTestPort();
            await app.listen({ port });

            const response = await fetch(createTestUrl(port, '/nonexistent'));
            const data = await response.json();

            expect(response.status).toBe(404);
            expect(data.statusCode).toBe(404);
            expect(data.error).toBe('Not Found');
        });

        test('should handle validation errors', async () => {
            const port = getTestPort();

            // Register a route with validation
            const fastify = app.getApp();
            fastify.post('/validate', {
                schema: {
                    body: {
                        type: 'object',
                        required: ['name'],
                        properties: {
                            name: { type: 'string' }
                        }
                    }
                }
            }, async (request) => {
                return { received: request.body };
            });

            await app.listen({ port });

            const response = await fetch(createTestUrl(port, '/validate'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });

            const data = await response.json();

            expect(response.status).toBe(400);
            expect(data.statusCode).toBe(400);
            expect(data.error).toBe('Bad Request');
        });
    });
});