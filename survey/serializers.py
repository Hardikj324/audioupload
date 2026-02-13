from rest_framework import serializers
from .models import UserProfile, Audio, NoiseQuestion, NoiseResponse, AudioEvaluation


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'


class AudioSerializer(serializers.ModelSerializer):
    file = serializers.SerializerMethodField()
    stream_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Audio
        fields = '__all__'
    
    def get_file(self, obj):
        # Keep original for backwards compatibility
        if not obj.file:
            return None
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.file.url)

        return obj.file.url
    
    def get_stream_url(self, obj):
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(f"/api/stream-audio/{obj.id}/")

        return f"/api/stream-audio/{obj.id}/"



class NoiseQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoiseQuestion
        fields = '__all__'


class NoiseResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoiseResponse
        fields = '__all__'


class AudioEvaluationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AudioEvaluation
        fields = '__all__'