"""
ContextVar-based stack of the current serializer field path.

Used by the patches in `drf_nplus.patches` to record which serializer field
is being resolved at the moment a SQL query fires. `ContextVar` (not
`threading.local`) so the stack behaves correctly under Django's async views.
"""

from contextvars import ContextVar

_path: ContextVar[tuple] = ContextVar("drf_nplus_path", default=())


def push(segment: str):
    return _path.set(_path.get() + (segment,))


def reset(token) -> None:
    _path.reset(token)


def current_path() -> str | None:
    parts = _path.get()
    if not parts:
        return None
    return ".".join(parts)


def is_empty() -> bool:
    return not _path.get()
