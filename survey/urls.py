from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserProfileViewSet,
    AudioViewSet,
    NoiseQuestionViewSet,
    NoiseResponseViewSet,
    AudioEvaluationViewSet,
    AudioStreamView
    
)

router = DefaultRouter()
router.register(r'users', UserProfileViewSet)
router.register(r'audios', AudioViewSet)
router.register(r'noise-questions', NoiseQuestionViewSet)
router.register(r'noise-responses', NoiseResponseViewSet)
router.register(r'evaluations', AudioEvaluationViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('stream-audio/<int:audio_id>/', AudioStreamView.as_view(), name='stream-audio'),  
]
