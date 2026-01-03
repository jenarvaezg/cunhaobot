import logging
import asyncio
from google.cloud import storage
from core.config import config

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self, bucket_name: str = config.bucket_name):
        self.bucket_name = bucket_name
        self._client: storage.Client | None = None

    @property
    def client(self) -> storage.Client:
        if self._client is None:
            self._client = storage.Client()
        return self._client

    async def upload_bytes(
        self, data: bytes, filename: str, content_type: str = "image/png"
    ) -> str:
        """Uploads bytes to GCS and returns the public URL."""

        def _upload() -> str:
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(filename)
            blob.upload_from_string(data, content_type=content_type)
            # Make public ?? Or assume bucket is public/we use signed urls?
            # For simplicity, we assume we want a long lived public URL or we rely on bucket policy.
            # But making it public explicitly is safer for web access if bucket is not public.
            # blob.make_public()  # Be careful with this.
            return blob.public_url

        try:
            return await asyncio.to_thread(_upload)
        except Exception as e:
            logger.error(f"Failed to upload {filename} to GCS: {e}")
            raise e


storage_service = StorageService()
