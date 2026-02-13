from django.contrib import admin
from .models import (
    UserProfile,
    NoiseQuestion,
    NoiseResponse,
    Audio,
    AudioEvaluation,
)

admin.site.register(UserProfile)
admin.site.register(NoiseQuestion)
admin.site.register(NoiseResponse)
admin.site.register(Audio)
admin.site.register(AudioEvaluation)
