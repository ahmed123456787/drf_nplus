"""
Monkey-patches DRF's Serializer.to_representation so we can tag each SQL query
with the serializer field path that triggered it.

Strategy: replace the inner field-iteration loop with one that pushes the field
name onto our ContextVar stack for the duration of `get_attribute` and
`to_representation`. Any query fired while a field is on the stack gets
attributed to that field path.

For nested serializers, descent happens naturally: the child's
`to_representation` runs while the parent's field name is still on the stack,
so its own pushes extend the path (e.g. `PostSerializer.author.name`).
"""

from rest_framework.fields import SkipField
from rest_framework.relations import PKOnlyObject
from rest_framework.serializers import Serializer

from . import context

_installed = False
_original_to_representation = None


def install() -> None:
    global _installed, _original_to_representation
    if _installed:
        return
    _original_to_representation = Serializer.to_representation
    Serializer.to_representation = _wrapped_to_representation
    _installed = True


def uninstall() -> None:
    global _installed, _original_to_representation
    if not _installed:
        return
    Serializer.to_representation = _original_to_representation
    _original_to_representation = None
    _installed = False


def _wrapped_to_representation(self, instance):
    root_token = None
    if context.is_empty():
        root_token = context.push(type(self).__name__)
    try:
        ret = {}
        for field in self._readable_fields:
            token = context.push(field.field_name)
            try:
                try:
                    attribute = field.get_attribute(instance)
                except SkipField:
                    continue

                check_for_none = (
                    attribute.pk if isinstance(attribute, PKOnlyObject) else attribute
                )
                if check_for_none is None:
                    ret[field.field_name] = None
                else:
                    ret[field.field_name] = field.to_representation(attribute)
            finally:
                context.reset(token)
        return ret
    finally:
        if root_token is not None:
            context.reset(root_token)
