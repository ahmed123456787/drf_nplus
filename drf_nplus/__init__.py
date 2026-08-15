"""drf-nplus: a DRF serializer-aware N+1 query detector."""

from .middleware import QueryCountMiddleware
from .patches import install, uninstall
from .testing import NPlusOneDetected, assert_no_nplus

__all__ = [
    "QueryCountMiddleware",
    "assert_no_nplus",
    "NPlusOneDetected",
    "install",
    "uninstall",
]

__version__ = "0.1.0"
