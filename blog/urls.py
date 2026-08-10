from rest_framework.routers import DefaultRouter

from .views import PostOptimizedViewSet, PostViewSet

router = DefaultRouter()
router.register(r"posts", PostViewSet, basename="post")
router.register(r"posts-optimized", PostOptimizedViewSet, basename="post-optimized")

urlpatterns = router.urls
