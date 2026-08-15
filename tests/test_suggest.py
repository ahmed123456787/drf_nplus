import pytest
from django.test import Client

from blog.models import Author, Post
from blog.serializers import PostSerializer
from drf_nplus.testing import NPlusOneDetected, assert_no_nplus


@pytest.mark.django_db
def test_middleware_suggests_select_related_for_fk(seeded_blog, caplog):
    import logging

    with caplog.at_level(logging.WARNING, logger="drf_nplus"):
        Client().get("/posts/")
    message = "\n".join(r.getMessage() for r in caplog.records)
    assert 'select_related("author")' in message
    assert 'prefetch_related("tags")' in message


@pytest.mark.django_db
def test_assert_no_nplus_includes_fix_hint(seeded_blog):
    with pytest.raises(NPlusOneDetected) as exc:
        with assert_no_nplus():
            PostSerializer(Post.objects.all(), many=True).data
    msg = str(exc.value)
    assert 'select_related("author")' in msg


@pytest.mark.django_db
def test_optimized_queryset_produces_no_offenders(seeded_blog):
    qs = Post.objects.select_related("author").prefetch_related("tags")
    with assert_no_nplus():
        PostSerializer(qs, many=True).data


@pytest.mark.django_db
@pytest.mark.no_nplus
def test_marker_passes_when_serializer_is_optimized(seeded_blog):
    """Smoke test: the pytest plugin's marker doesn't false-positive."""
    qs = Post.objects.select_related("author").prefetch_related("tags")
    PostSerializer(qs, many=True).data
