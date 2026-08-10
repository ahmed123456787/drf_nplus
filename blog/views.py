from rest_framework import viewsets

from .models import Post
from .serializers import PostSerializer


class PostViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer


class PostOptimizedViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Post.objects.select_related("author").prefetch_related("tags")
    serializer_class = PostSerializer
