import pytest

from blog.models import Post
from blog.serializers import PostSerializer
from drf_nplus.testing import NPlusOneDetected, assert_no_nplus


@pytest.mark.django_db
def test_raises_on_unoptimized_queryset(seeded_blog):
    with pytest.raises(NPlusOneDetected) as exc_info:
        with assert_no_nplus():
            PostSerializer(Post.objects.all(), many=True).data
    message = str(exc_info.value)
    assert "PostSerializer.author" in message


@pytest.mark.django_db
def test_passes_on_optimized_queryset(seeded_blog):
    qs = Post.objects.select_related("author").prefetch_related("tags")
    with assert_no_nplus():
        PostSerializer(qs, many=True).data
