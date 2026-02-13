from django.db.models.signals import post_save
from django.dispatch import receiver
import pandas as pd
from .models import NoiseQuestion, NoiseResponse, AudioEvaluation
from django.conf import settings
import os

CSV_FILE = os.path.join(settings.BASE_DIR, "csv", "user_survey_analysis.csv")


@receiver(post_save, sender=AudioEvaluation)
def update_csv_on_audio(sender, instance, **kwargs):
    try:
        export_user_row(instance.user, instance)
    except Exception as e:
        # IMPORTANT: never let CSV failure crash API
        print("CSV export failed:", e)


def export_user_row(user, evaluation):
    os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)

    row = {
        "UserID": user.user_id,
        "AudioTitle": evaluation.audio.title,
        "Age": user.age,
        "Gender": user.gender,
    }

    
    questions = NoiseQuestion.objects.all().order_by("number")
    for q in questions:
        response = NoiseResponse.objects.filter(
            user=user,
            question=q
        ).first()
        row[f"Q{q.number}"] = response.rating if response else None

    
    latest_eval = AudioEvaluation.objects.filter(
        user=user,
        audio=evaluation.audio
    ).order_by("-submitted_at").first()

    if latest_eval:
        row.update({
            "Annoyance": latest_eval.annoyance,
            "Eventfulness": latest_eval.eventfulness,
            "Pleasantness": latest_eval.pleasantness,
            "Chaotic": latest_eval.chaotic,
            "Vibrant": latest_eval.vibrant,
            "Uneventful": latest_eval.uneventful,
            "Calm": latest_eval.calm,
            "Monotonous": latest_eval.monotonous,
            "TrafficNoise": latest_eval.traffic_noise,
            "OtherNoise": latest_eval.other_noise,
            "HumanSounds": latest_eval.human_sounds,
            "NaturalSounds": latest_eval.natural_sounds,
            "SubmittedAt": latest_eval.submitted_at.replace(tzinfo=None),
        })

    try:
        df = pd.read_csv(CSV_FILE)

        # Remove old row for same user + same audio
        df = df[
            ~((df["UserID"] == user.user_id) &
              (df["AudioTitle"] == evaluation.audio.title))
        ]

        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)

    except FileNotFoundError:
        df = pd.DataFrame([row])

    df.to_csv(CSV_FILE, index=False)
