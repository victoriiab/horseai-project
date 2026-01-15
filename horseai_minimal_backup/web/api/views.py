from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, permissions
from web.database.models import User, Animal, Video, Analysis, Feed, Ration
from .serializers import UserSerializer, AnimalSerializer, VideoSerializer, AnalysisSerializer, FeedSerializer, RationSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class AnimalViewSet(viewsets.ModelViewSet):
    queryset = Animal.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = AnimalSerializer

class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = VideoSerializer

class AnalysisViewSet(viewsets.ModelViewSet):
    queryset = Analysis.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = AnalysisSerializer

class FeedViewSet(viewsets.ModelViewSet):
    queryset = Feed.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = FeedSerializer

class RationViewSet(viewsets.ModelViewSet):
    queryset = Ration.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = RationSerializer
    permission_classes = [permissions.AllowAny]
