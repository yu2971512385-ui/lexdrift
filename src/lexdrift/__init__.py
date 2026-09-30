"""lexdrift -- find syntax highlighters that never learned a language's newer keywords."""

__version__ = "0.2.0"

from .check import check, check_feature, check_library  # noqa: F401
from .corpus import load_corpus  # noqa: F401
from .model import Feature, LibraryReport, Result, Status, Token  # noqa: F401

__all__ = [
    "__version__",
    "check",
    "check_feature",
    "check_library",
    "load_corpus",
    "Feature",
    "LibraryReport",
    "Result",
    "Status",
    "Token",
]
