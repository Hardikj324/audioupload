from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class UserProfile(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    user_id = models.CharField(max_length=20,unique=True, db_index=True) 
    age = models.IntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='male')


class Audio(models.Model):
    title = models.CharField(max_length=100)
    file = models.FileField(upload_to='audios/')

class NoiseQuestion(models.Model):
    number = models.IntegerField()
    text = models.TextField()
    reverse_scale = models.BooleanField(default=False)  # for flipped agree/disagree

class NoiseResponse(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    question = models.ForeignKey(NoiseQuestion, on_delete=models.CASCADE)
    rating = models.IntegerField()  # 1 to 6

class AudioEvaluation(models.Model):
    audio = models.ForeignKey(Audio, on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)

    # Slider ratings
    annoyance = models.IntegerField(default=0)
    eventfulness = models.IntegerField(default=0)
    pleasantness = models.IntegerField(default=0)
    chaotic = models.IntegerField(default=0)
    vibrant = models.IntegerField(default=0)
    uneventful = models.IntegerField(default=0)
    calm = models.IntegerField(default=0)
    monotonous = models.IntegerField(default=0)

    # Sound source dominance (scale: 0–4)
    traffic_noise = models.IntegerField(default=0)
    other_noise = models.IntegerField(default=0)
    human_sounds = models.IntegerField(default=0)
    natural_sounds = models.IntegerField(default=0)

    submitted_at = models.DateTimeField(auto_now_add=True)
