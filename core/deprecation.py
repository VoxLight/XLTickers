"""
Deprecation utilities for phasing out old code.

Marks functions as deprecated and provides clear migration paths.
"""

import warnings
import functools
from typing import Callable


def deprecated(replacement: str = None, reason: str = None):
    """
    Decorator to mark functions as deprecated.
    
    Usage:
        @deprecated(replacement='new_function', reason='Use optimized version')
        def old_function():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            message = f"{func.__name__} is deprecated"
            
            if replacement:
                message += f". Use {replacement} instead"
            if reason:
                message += f". {reason}"
            
            warnings.warn(
                message,
                category=DeprecationWarning,
                stacklevel=2
            )
            
            return func(*args, **kwargs)
        
        # Add deprecation notice to docstring
        if func.__doc__:
            wrapper.__doc__ = f"⚠️  DEPRECATED: {replacement or 'This function'}\n\n{func.__doc__}"
        
        return wrapper
    
    return decorator


def deprecation_notice(message: str):
    """
    Issue a deprecation warning immediately.
    
    Usage:
        deprecation_notice("Module will be removed in v2.0")
    """
    warnings.warn(
        message,
        category=DeprecationWarning,
        stacklevel=2
    )
