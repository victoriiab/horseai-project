from django.urls import path
from .views import (
    AnimalViewSet, VideoViewSet, AnalysisViewSet,
    FeedViewSet, RationViewSet
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'animals', AnimalViewSet)
router.register(r'videos', VideoViewSet)
router.register(r'analyses', AnalysisViewSet)
router.register(r'feeds', FeedViewSet)
router.register(r'rations', RationViewSet)

urlpatterns = router.urls

print("API URLs: простой вариант")
