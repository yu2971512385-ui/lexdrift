"""Highlighter adapters.

Importing this package registers every adapter that ships with lexdrift.
Adding one is a matter of writing a class with ``name``/``label``/``url``,
``version()``, ``supports()`` and ``tokenize()``, then calling ``register()``.
"""

from .base import (  # noqa: F401
    Adapter,
    AdapterUnavailable,
    available_names,
    get_adapter,
    get_adapters,
    map_category,
    register,
)
from . import chroma, node, pygments_adapter  # noqa: F401  (import for the side effect)

__all__ = [
    "Adapter",
    "AdapterUnavailable",
    "available_names",
    "get_adapter",
    "get_adapters",
    "map_category",
    "register",
]
