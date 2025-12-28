from google.cloud import storage

GCP_BUCKET = "cunhaobot.appspot.com"

storage_client = storage.Client()
bucket = storage_client.get_bucket(GCP_BUCKET)
audios_folder = "audios"


def get_audio_url(file_name: str) -> str:
    file_path = f"{audios_folder}/{file_name}.ogg"
    blob = bucket.blob(file_path)

    return blob.public_url if blob.exists() else ""
