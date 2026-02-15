import os
import json
import threading
import base64
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from dotenv import load_dotenv


load_dotenv()

from .models import AudioEvaluation, NoiseQuestion, NoiseResponse


def _upload_worker(row_data, header_row):
    """
    Runs in a background thread.
    Checks if headers exist. If not, adds them. Then adds data.
    """
    try:
        b64_creds = os.getenv('GOOGLE_CREDENTIALS_JSON')
        sheet_id = os.getenv('GOOGLE_SHEET_ID')

        if not b64_creds or not sheet_id:
            print("❌ Export Error: Missing Render Environment Variables.")
            return

       
        # Decode Base64 to get the JSON string
        try:
            json_str = base64.b64decode(b64_creds).decode("utf-8")
            creds_dict = json.loads(json_str)
        except Exception as e:
            print(f"❌ Credential Decoding Error: {e}")
            return

        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)

        
        sheet = client.open_by_key(sheet_id).sheet1


        try:
            first_cell = sheet.acell('A1').value
            if not first_cell:
                print("📝 Sheet is empty. Adding headers...")
                sheet.append_row(header_row)
        except Exception:

            pass


        sheet.append_row(row_data)
        
        print(f"✅ Successfully saved row for User ID: {row_data[0]}")

    except Exception as e:
        print(f"❌ Google Sheets API Error: {e}")



def prepare_header_row():
    """
    Generates the list of column names (The first row of the Excel file).
    """
    headers = ["UserID", "AudioTitle", "Age", "Gender"]
    

    questions = NoiseQuestion.objects.all().order_by("number")
    for q in questions:
        headers.append(f"Q{q.number}")

    
    headers.extend([
        "Annoyance",
        "Eventfulness",
        "Pleasantness",
        "Chaotic",
        "Vibrant",
        "Uneventful",
        "Calm",
        "Monotonous",
        "TrafficNoise",
        "OtherNoise",
        "HumanSounds",
        "NaturalSounds",
        "SubmittedAt"
    ])
    return headers

def prepare_data_row(instance):
    """
    Extracts data from the instance to match the header row.
    """
    user = instance.user
    
    row = [
        str(user.user_id),
        str(instance.audio.title),
        str(user.age) if user.age else "",
        str(user.gender) if user.gender else "",
    ]

    questions = NoiseQuestion.objects.all().order_by("number")
    for q in questions:
        response = NoiseResponse.objects.filter(user=user, question=q).first()
        row.append(str(response.rating) if response else "NA")

    submitted_str = instance.submitted_at.strftime("%Y-%m-%d %H:%M:%S") if instance.submitted_at else ""

    row.extend([
        str(instance.annoyance ),
        str(instance.eventfulness ),
        str(instance.pleasantness ),
        str(instance.chaotic ),
        str(instance.vibrant ),
        str(instance.uneventful ),
        str(instance.calm ),
        str(instance.monotonous ),
        str(instance.traffic_noise ),
        str(instance.other_noise ),
        str(instance.human_sounds ),
        str(instance.natural_sounds ),
        submitted_str
    ])

    return row




@receiver(post_save, sender=AudioEvaluation)
def export_survey_data(sender, instance, created, **kwargs):
    """
    Triggered immediately after data is saved to the DB.
    """
    if created:
        try:
            # 1. Prepare Data & Headers (Run in main thread to access DB safely)
            data_row = prepare_data_row(instance)
            header_row = prepare_header_row()

            # 2. Send to Google Sheets (Background Thread)
            thread = threading.Thread(
                target=_upload_worker, 
                args=(data_row, header_row)
            )
            thread.start()

        except Exception as e:
            print(f"❌ Signal logic failed: {e}")