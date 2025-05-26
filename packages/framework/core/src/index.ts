/**
 * Brickend Core
 * Provides the foundation for all Brickend functionality
 */

import fastify, { FastifyInstance, FastifyServerOptions, FastifyListenOptions } from 'fastify';

/**
 * Interface for Brickend plugins
 */
export interface BrickendPlugin {
    name: string;
    register: (app: FastifyInstance, options?: any) => void | Promise<void>;
}

/**
 * Brickend configuration options
 */
export interface BrickendOptions extends FastifyServerOptions {
    plugins?: {
        autoRegister?: boolean;
        loadDefaults?: boolean;
    };
}

/**
 * Plugin registration result
 */
export interface PluginRegistrationResult {
    success: boolean;
    plugin: BrickendPlugin;
    error?: Error;
}

/**
 * Main Brickend class
 */
export class Brickend {
    private plugins: BrickendPlugin[] = [];
    private app: FastifyInstance;
    private isStarted = false;

    /**
     * Create a new Brickend instance
     */
    constructor(options: BrickendOptions = {}) {
        // Extract Brickend-specific options
        const { plugins: pluginOptions, ...fastifyOptions } = options;

        // Create Fastify instance with default configuration
        this.app = fastify({
            logger: {
                level: process.env.LOG_LEVEL || 'info',
                transport: process.env.NODE_ENV === 'development' ? {
                    target: 'pino-pretty',
                    options: {
                        colorize: true
                    }
                } : undefined
            },
            trustProxy: true,
            ...fastifyOptions
        });

        // Register default plugins if enabled
        if (pluginOptions?.loadDefaults !== false) {
            this.registerDefaultPlugins();
        }

        // Setup error handling
        this.setupErrorHandling();
    }

    /**
     * Register default Fastify plugins
     */
    private async registerDefaultPlugins(): Promise<void> {
        try {
            // Register CORS
            await this.app.register(import('@fastify/cors'), {
                origin: process.env.CORS_ORIGIN || true,
                credentials: true
            });

            // Register Helmet for security
            await this.app.register(import('@fastify/helmet'), {
                global: true
            });

            // Register rate limiting
            await this.app.register(import('@fastify/rate-limit'), {
                max: parseInt(process.env.RATE_LIMIT_MAX || '100'),
                timeWindow: process.env.RATE_LIMIT_WINDOW || '1 minute'
            });

        } catch (error) {
            this.app.log.warn('Some default plugins failed to load:', error);
        }
    }

    /**
     * Setup global error handling
     */
    private setupErrorHandling(): void {
        // Global error handler
        this.app.setErrorHandler(async (error, request, reply) => {
            this.app.log.error(error);

            // Check if it's a validation error
            if (error.validation) {
                return reply.status(400).send({
                    statusCode: 400,
                    error: 'Bad Request',
                    message: 'Validation failed',
                    details: error.validation
                });
            }

            // Check if it's a known HTTP error
            if (error.statusCode) {
                return reply.status(error.statusCode).send({
                    statusCode: error.statusCode,
                    error: error.name || 'Error',
                    message: error.message
                });
            }

            // Generic server error
            return reply.status(500).send({
                statusCode: 500,
                error: 'Internal Server Error',
                message: 'An internal server error occurred'
            });
        });

        // Not found handler
        this.app.setNotFoundHandler(async (request, reply) => {
            return reply.status(404).send({
                statusCode: 404,
                error: 'Not Found',
                message: `Route ${request.method}:${request.url} not found`
            });
        });
    }

    /**
     * Get the Fastify instance
     */
    getApp(): FastifyInstance {
        return this.app;
    }

    /**
     * Register a plugin with Brickend
     */
    async register(plugin: BrickendPlugin, options?: any): Promise<PluginRegistrationResult> {
        try {
            this.app.log.info(`Registering plugin: ${plugin.name}`);

            await plugin.register(this.app, options);
            this.plugins.push(plugin);

            this.app.log.info(`Plugin registered successfully: ${plugin.name}`);

            return {
                success: true,
                plugin
            };
        } catch (error) {
            this.app.log.error(`Failed to register plugin ${plugin.name}:`, error);

            return {
                success: false,
                plugin,
                error: error as Error
            };
        }
    }

    /**
     * Register multiple plugins
     */
    async registerPlugins(plugins: Array<{ plugin: BrickendPlugin; options?: any }>): Promise<PluginRegistrationResult[]> {
        const results: PluginRegistrationResult[] = [];

        for (const { plugin, options } of plugins) {
            const result = await this.register(plugin, options);
            results.push(result);
        }

        return results;
    }

    /**
     * Get all registered plugins
     */
    getPlugins(): BrickendPlugin[] {
        return [...this.plugins];
    }

    /**
     * Get plugin by name
     */
    getPlugin(name: string): BrickendPlugin | undefined {
        return this.plugins.find(plugin => plugin.name === name);
    }

    /**
     * Check if plugin is registered
     */
    hasPlugin(name: string): boolean {
        return this.plugins.some(plugin => plugin.name === name);
    }

    /**
     * Start the server
     */
    async listen(options?: FastifyListenOptions): Promise<string> {
        const listenOptions: FastifyListenOptions = {
            port: parseInt(process.env.PORT || '3000'),
            host: process.env.HOST || '0.0.0.0',
            ...options
        };

        try {
            const address = await this.app.listen(listenOptions);
            this.isStarted = true;
            this.app.log.info(`🚀 Brickend server listening at ${address}`);
            return address;
        } catch (error) {
            this.app.log.error('Failed to start server:', error);
            throw error;
        }
    }

    /**
     * Stop the server gracefully
     */
    async close(): Promise<void> {
        if (this.isStarted) {
            await this.app.close();
            this.isStarted = false;
            this.app.log.info('Server stopped gracefully');
        }
    }

    /**
     * Check if server is running
     */
    isListening(): boolean {
        return this.isStarted;
    }

    /**
     * Add a ready hook
     */
    async ready(callback?: () => void | Promise<void>): Promise<void> {
        await this.app.ready();
        if (callback) {
            await callback();
        }
    }

    /**
     * Health check endpoint
     */
    registerHealthCheck(path = '/health'): void {
        this.app.get(path, async () => ({
            status: 'ok',
            timestamp: new Date().toISOString(),
            uptime: process.uptime(),
            plugins: this.plugins.map(p => p.name)
        }));
    }
}

/**
 * Create a new Brickend instance
 */
export const createBrickend = (options?: BrickendOptions): Brickend => {
    return new Brickend(options);
};

/**
 * Utility function to create a Brickend plugin
 */
export const createPlugin = (
    name: string,
    registerFn: (app: FastifyInstance, options?: any) => void | Promise<void>
): BrickendPlugin => {
    return {
        name,
        register: registerFn
    };
};

/**
 * Utility function to create a typed plugin
 */
export const createTypedPlugin = <T = any>(
    name: string,
    registerFn: (app: FastifyInstance, options?: T) => void | Promise<void>
): BrickendPlugin => {
    return {
        name,
        register: registerFn as any
    };
};

// Re-export Fastify types for convenience
export type {
    FastifyInstance,
    FastifyServerOptions,
    FastifyListenOptions
} from 'fastify';