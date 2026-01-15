from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Создаем router для ViewSets
router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'animals', views.AnimalViewSet)
router.register(r'videos', views.VideoViewSet)
router.register(r'analyses', views.AnalysisViewSet)
router.register(r'feeds', views.FeedViewSet)
router.register(r'rations', views.RationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
