from django.db.models.signals import post_save
from django.dispatch import receiver
import pandas as pd
from .models import NoiseQuestion, NoiseResponse, AudioEvaluation
import os
import json
import io

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload


# ================= CONFIG =================

CSV_FILE = "/tmp/user_survey_analysis.csv"  # temp file (safe on Render)
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
FOLDER_ID = os.environ.get("GOOGLE_DRIVE_FOLDER_ID")


# ================= GOOGLE DRIVE =================

def get_drive_service():
    creds_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    creds_dict = json.loads(creds_json)

    credentials = service_account.Credentials.from_service_account_info(
        creds_dict, scopes=SCOPES
    )

    return build("drive", "v3", credentials=credentials)


def upload_csv_to_drive(filename="user_survey_analysis.csv"):
    service = get_drive_service()

    results = service.files().list(
        q=f"name='{filename}' and '{FOLDER_ID}' in parents and trashed=false",
        fields="files(id, name)",
    ).execute()

    media = MediaIoBaseUpload(
        io.FileIO(CSV_FILE, "rb"),
        mimetype="text/csv",
        resumable=True,
    )

    if results["files"]:
        file_id = results["files"][0]["id"]
        service.files().update(
            fileId=file_id,
            media_body=media
        ).execute()
    else:
        service.files().create(
            body={"name": filename, "parents": [FOLDER_ID]},
            media_body=media,
            fields="id",
        ).execute()


# ================= CSV GENERATION =================

def export_user_row(user, evaluation):
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

        # remove existing row for same user + same audio
        df = df[
            ~(
                (df["UserID"] == user.user_id) &
                (df["AudioTitle"] == evaluation.audio.title)
            )
        ]

        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)

    except FileNotFoundError:
        df = pd.DataFrame([row])

    df.to_csv(CSV_FILE, index=False)


# ================= SIGNAL =================

@receiver(post_save, sender=AudioEvaluation)
def update_csv_on_audio(sender, instance, **kwargs):
    try:
        export_user_row(instance.user, instance)
        upload_csv_to_drive()
    except Exception as e:
        print("CSV / Drive upload failed:", e)
