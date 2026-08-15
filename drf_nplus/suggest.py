"""
Turn a captured serializer field path into an actionable ORM fix hint.

Given the segment stack for a query, walk each field against its parent
model to decide whether adding `.select_related(...)` or
`.prefetch_related(...)` would fold the query into the top-level SELECT.
"""

from django.core.exceptions import FieldDoesNotExist


def suggest_fix(segments) -> str | None:
    """
    Return a string like `.select_related("author")` (or None if we can't
    make a confident recommendation — e.g. non-ModelSerializer, or a field
    with no model attribute).

    For nested paths, source names are joined with `__` (Django's lookup
    separator). Once any hop is many-valued (M2M / reverse FK), the whole
    chain becomes `prefetch_related` since `select_related` only handles
    single-valued relations.
    """
    if len(segments) < 2:
        return None

    parts = []
    kind = None
    for seg in segments[1:]:
        if not seg.parent_model or not seg.source:
            return None
        try:
            model_field = seg.parent_model._meta.get_field(seg.source)
        except FieldDoesNotExist:
            return None
        parts.append(seg.source)
        if model_field.many_to_many or model_field.one_to_many:
            kind = "prefetch_related"
        elif kind is None and (model_field.many_to_one or model_field.one_to_one):
            kind = "select_related"

    if not kind:
        return None
    return f'.{kind}("{"__".join(parts)}")'
