"""
ContextVar-based stack of the current serializer field path.

Each segment carries the display name plus optional metadata used to
suggest a fix (`select_related` / `prefetch_related`):

- `parent_model` — the model class of the serializer that owns this field
- `source` — the ORM attribute name the field reads from (i.e. `field.source`)

`ContextVar` (not `threading.local`) so the stack behaves correctly under
Django's async views.
"""

from contextvars import ContextVar
from dataclasses import dataclass


@dataclass(frozen=True)
class Segment:
    name: str
    parent_model: type | None = None
    source: str | None = None


_path: ContextVar[tuple] = ContextVar("drf_nplus_path", default=())


def push(name: str, *, parent_model=None, source=None):
    return _path.set(_path.get() + (Segment(name, parent_model, source),))


def reset(token) -> None:
    _path.reset(token)


def current_path() -> str | None:
    segs = _path.get()
    if not segs:
        return None
    return ".".join(s.name for s in segs)


def current_segments() -> tuple:
    return _path.get()


def is_empty() -> bool:
    return not _path.get()
