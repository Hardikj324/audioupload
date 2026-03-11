from rest_framework import viewsets, status
from .models import UserProfile, Audio, NoiseQuestion, NoiseResponse, AudioEvaluation
from .serializers import (
    UserProfileSerializer,
    AudioSerializer,
    NoiseQuestionSerializer,
    NoiseResponseSerializer,
    AudioEvaluationSerializer
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.http import HttpResponse, Http404
from django.views import View
from django.shortcuts import redirect
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "ok"})

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [AllowAny]
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("❌ Serializer errors:", serializer.errors)
            return Response(serializer.errors, status=400)
        return super().create(request, *args, **kwargs)


class AudioViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Audio.objects.all()
    serializer_class = AudioSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class NoiseQuestionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = NoiseQuestion.objects.all()
    serializer_class = NoiseQuestionSerializer


class NoiseResponseViewSet(viewsets.ModelViewSet):
    queryset = NoiseResponse.objects.all()
    serializer_class = NoiseResponseSerializer
    permission_classes = [AllowAny]
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        try:
            print("Incoming POST data:", request.data)
            response = super().create(request, *args, **kwargs)
            print("Saved response:", response.data)
            return response
        except Exception as e:
            print("Exception is:", e)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AudioEvaluationViewSet(viewsets.ModelViewSet):
    queryset = AudioEvaluation.objects.all()
    serializer_class = AudioEvaluationSerializer
    permission_classes = [AllowAny]
    http_method_names = ['post']


class AudioStreamView(View):
    """
    Redirects to the Cloudinary URL for the audio file.
    No more local file reading — Cloudinary hosts the file permanently.
    """
    def get(self, request, audio_id):
        try:
            audio = Audio.objects.get(id=audio_id)
        except Audio.DoesNotExist:
            raise Http404("Audio not found")

        if not audio.file:
            raise Http404("Audio file not uploaded")

        # audio.file.url now returns the Cloudinary URL (e.g. https://res.cloudinary.com/...)
        cloudinary_url = audio.file.url

        # Redirect the browser directly to Cloudinary — no local disk needed
        return redirect(cloudinary_url)

    def options(self, request, audio_id):
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, HEAD, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Range, Content-Type'
        return response