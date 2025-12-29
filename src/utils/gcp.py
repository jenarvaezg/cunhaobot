import subprocess
import logging
from google.cloud import datastore, storage
from google.oauth2 import credentials

logger = logging.getLogger(__name__)

GCP_BUCKET = "cunhaobot.appspot.com"
audios_folder = "audios"
PROJECT_ID = "cunhaobot"

# Singleton instances
_DATASTORE_CLIENT: datastore.Client | None = None
_STORAGE_CLIENT: storage.Client | None = None


def get_storage_client() -> storage.Client:
    global _STORAGE_CLIENT
    if _STORAGE_CLIENT is None:
        _STORAGE_CLIENT = storage.Client()
    return _STORAGE_CLIENT


def get_datastore_client() -> datastore.Client:
    global _DATASTORE_CLIENT
    if _DATASTORE_CLIENT is not None:
        return _DATASTORE_CLIENT

    # 1. Intento normal (Funciona en App Engine y local con ADC)
    try:
        _DATASTORE_CLIENT = datastore.Client(project=PROJECT_ID)
        return _DATASTORE_CLIENT
    except Exception:
        pass

    # 2. Intento via gcloud (Solo si el normal falla)
    try:
        logger.info("🔐 Obteniendo token de acceso vía gcloud (una sola vez)...")
        token = (
            subprocess.check_output(["gcloud", "auth", "print-access-token"])
            .decode("utf-8")
            .strip()
        )
        creds = credentials.Credentials(token)
        _DATASTORE_CLIENT = datastore.Client(credentials=creds, project=PROJECT_ID)
        return _DATASTORE_CLIENT
    except Exception as e:
        logger.error(f"❌ Error crítico al inicializar Datastore: {e}")
        return datastore.Client()


def get_bucket() -> storage.Bucket:
    return get_storage_client().get_bucket(GCP_BUCKET)  # pragma: no cover


def get_audio_url(file_name: str) -> str:
    file_path = f"{audios_folder}/{file_name}.ogg"
    bucket = get_bucket()
    blob = bucket.blob(file_path)

    return blob.public_url if blob.exists() else ""
