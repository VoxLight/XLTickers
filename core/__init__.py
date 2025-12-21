"""
Core module initialization.

Exports public API for core business logic.
"""

from core.config import Config, ConfigError

__all__ = ['Config', 'ConfigError']
