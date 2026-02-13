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
from django.http import StreamingHttpResponse, HttpResponse, Http404
from django.views import View
from wsgiref.util import FileWrapper
import os
import mimetypes
import re

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [AllowAny]
    http_method_names = ['post']

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
    def get(self, request, audio_id):
        try:
            audio = Audio.objects.get(id=audio_id)
            file_path = audio.file.path
        except Audio.DoesNotExist:
            raise Http404("Audio not found")
        
        file_size = os.path.getsize(file_path)
        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = 'audio/wav' if file_path.endswith('.wav') else 'audio/mpeg'
        
        range_header = request.META.get('HTTP_RANGE', '').strip()
        range_match = re.search(r'bytes=(\d+)-(\d*)', range_header) if range_header else None
        
        if range_match:
            start = int(range_match.group(1))
            end = int(range_match.group(2)) if range_match.group(2) else file_size - 1
            length = end - start + 1
            
            file_handle = open(file_path, 'rb')
            file_handle.seek(start)
            
            response = StreamingHttpResponse(
                FileWrapper(file_handle, 8192),
                status=206,
                content_type=content_type
            )
            response['Content-Length'] = str(length)
            response['Content-Range'] = f'bytes {start}-{end}/{file_size}'
        else:
            file_handle = open(file_path, 'rb')
            response = StreamingHttpResponse(
                FileWrapper(file_handle, 8192),
                content_type=content_type
            )
            response['Content-Length'] = str(file_size)
        
        response['Accept-Ranges'] = 'bytes'
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Expose-Headers'] = 'Content-Length, Content-Range, Accept-Ranges'
        response['X-Content-Type-Options'] = 'nosniff'
        
        return response
    
    def options(self, request, audio_id):
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, HEAD, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Range, Content-Type'
        return response