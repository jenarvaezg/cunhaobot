import subprocess
from google.cloud import datastore, storage
from google.oauth2 import credentials
import logging

logger = logging.getLogger(__name__)

GCP_BUCKET = "cunhaobot.appspot.com"
audios_folder = "audios"
PROJECT_ID = "cunhaobot"


def get_storage_client() -> storage.Client:
    return storage.Client()  # pragma: no cover


def get_datastore_client() -> datastore.Client:
    try:
        # 1. Intento normal (Funciona en App Engine y local con ADC)
        return datastore.Client(project=PROJECT_ID)
    except Exception:
        try:
            # 2. Intento via gcloud (Plan B para local sin ADC configurado)
            token = (
                subprocess.check_output(["gcloud", "auth", "print-access-token"])
                .decode("utf-8")
                .strip()
            )
            creds = credentials.Credentials(token)
            return datastore.Client(credentials=creds, project=PROJECT_ID)
        except Exception as e:
            logger.error(f"Error crítico al inicializar Datastore: {e}")
            # Si todo falla, devolvemos el cliente por defecto y que pete con la traza original
            return datastore.Client()


def get_bucket() -> storage.Bucket:
    return get_storage_client().get_bucket(GCP_BUCKET)  # pragma: no cover


def get_audio_url(file_name: str) -> str:
    file_path = f"{audios_folder}/{file_name}.ogg"
    bucket = get_bucket()
    blob = bucket.blob(file_path)

    return blob.public_url if blob.exists() else ""
