"""
__init__.py

Engine module for Brickend Core.

This module contains the core code generation engine components.
"""

from .context_builder import ContextBuilder
from .template_engine import TemplateEngine
from .template_registry import TemplateRegistry
from .code_generator import CodeGenerator
from .protected_regions import ProtectedRegionsHandler, SmartProtectedRegionsHandler

__all__ = [
    "ContextBuilder",
    "TemplateEngine",
    "TemplateRegistry",
    "CodeGenerator",
    "ProtectedRegionsHandler",
    "SmartProtectedRegionsHandler",
]
