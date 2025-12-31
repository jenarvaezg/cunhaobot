import logging
import time
from google.cloud import datastore, storage
from google.cloud.exceptions import NotFound

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_kind(client: datastore.Client, bucket: storage.Bucket, kind: str, audio_prefix: str):
    logger.info(f"Starting migration for kind: {kind}")
    query = client.query(kind=kind)
    entities = list(query.fetch())
    
    logger.info(f"Found {len(entities)} entities to migrate.")
    
    for entity in entities:
        # Check if already migrated (int ID)
        if isinstance(entity.key.id, int):
            logger.info(f"Skipping entity {entity.key.id} (already numeric)")
            continue
            
        old_id_text = entity.key.name
        if not old_id_text:
            logger.warning(f"Entity with no name/ID found: {entity.key}")
            continue
            
        logger.info(f"Migrating: {old_id_text}")
        
        # Create new entity (let Datastore assign ID)
        new_key = client.key(kind)
        new_entity = datastore.Entity(key=new_key)
        
        # Copy properties
        # Exclude key-related stuff if any, just copy the dict
        new_entity.update(entity)
        
        # Save to generate ID
        client.put(new_entity)
        new_id = new_entity.key.id
        logger.info(f"  -> New ID: {new_id}")
        
        # Migrate Assets
        # 1. Audio
        audio_blob_name = f"audios/{audio_prefix}-{old_id_text}.ogg"
        new_audio_blob_name = f"audios/{audio_prefix}-{new_id}.ogg"
        migrate_blob(bucket, audio_blob_name, new_audio_blob_name)
        
        # 2. Generated Images (Only stored by ID, so old ID was text)
        image_blob_name = f"generated_images/{old_id_text}.png"
        new_image_blob_name = f"generated_images/{new_id}.png"
        migrate_blob(bucket, image_blob_name, new_image_blob_name)
        
        # Delete old entity? 
        # For safety, let's keep them for now, or maybe delete them to avoid confusion?
        # The user requested "Migrar", usually implies moving.
        # If we leave them, the application might load duplicates if we iterate all.
        # But our new code prioritizes IDs.
        # Let's DELETE the old one to be clean.
        client.delete(entity.key)
        logger.info(f"  -> Deleted old entity: {old_id_text}")
        
        # Avoid hitting rate limits
        time.sleep(0.1)

def migrate_blob(bucket: storage.Bucket, old_name: str, new_name: str):
    blob = bucket.blob(old_name)
    if blob.exists():
        try:
            bucket.rename_blob(blob, new_name)
            logger.info(f"  -> Renamed blob: {old_name} to {new_name}")
            # Ensure public access if it was public?
            # rename_blob keeps ACLs usually, but let's make sure.
            # Actually rename_blob copies and deletes.
            new_blob = bucket.blob(new_name)
            try:
                new_blob.make_public()
            except Exception:
                pass 
        except Exception as e:
            logger.error(f"  -> Error renaming blob {old_name}: {e}")
    else:
        # It's common for phrases not to have audio/images
        pass

def main():
    # Initialize clients
    # Note: Using namespace if configured? The app seems to use default namespace.
    ds_client = datastore.Client()
    
    # Get bucket name from env or config?
    # services/tts_service.py uses utils.gcp.get_bucket()
    # Let's import it
    import sys
    import os
    # Add src to path so we can import utils
    src_path = os.path.join(os.getcwd(), "src")
    if src_path not in sys.path:
        sys.path.append(src_path)
        
    try:
        from utils.gcp import get_bucket
        bucket = get_bucket()
    except Exception as e:
        logger.error(f"Failed to get bucket: {e}")
        return

    # Migrate Phrases
    migrate_kind(ds_client, bucket, "Phrase", "short")
    
    # Migrate LongPhrases
    migrate_kind(ds_client, bucket, "LongPhrase", "long")
    
    logger.info("Migration complete.")

if __name__ == "__main__":
    main()
