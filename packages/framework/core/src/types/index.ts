// Entity types
export type {
    FieldType,
    FieldValidation,
    FieldOptions,
    Field,
    RelationshipType,
    Relationship,
    EntityOptions,
    Entity,
    Schema
} from './entity.js';

// Template types
export type {
    TemplateCategory,
    TemplateVariableType,
    TemplateVariable,
    TemplateHooks,
    PostProcessor,
    TemplateDependency,
    FileInstruction,
    TemplateConfig,
    TemplateMetadata,
    DiscoveredTemplate
} from './template.js';

// Project types
export type {
    ProjectConfig,
    ProjectContext,
    GeneratedFile,
    GeneratedProject,
    GenerationOptions,
    ContextBuildOptions
} from './project.js';