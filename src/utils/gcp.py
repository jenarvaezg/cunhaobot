from google.cloud import datastore, storage

GCP_BUCKET = "cunhaobot.appspot.com"
audios_folder = "audios"


def get_storage_client() -> storage.Client:
    return storage.Client()  # pragma: no cover


def get_datastore_client() -> datastore.Client:
    return datastore.Client()


def get_bucket() -> storage.Bucket:
    return get_storage_client().get_bucket(GCP_BUCKET)  # pragma: no cover


def get_audio_url(file_name: str) -> str:
    file_path = f"{audios_folder}/{file_name}.ogg"
    bucket = get_bucket()
    blob = bucket.blob(file_path)

    return blob.public_url if blob.exists() else ""
