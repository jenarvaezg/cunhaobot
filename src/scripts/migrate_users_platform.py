import logging
from google.cloud import datastore
from infrastructure.datastore.user import user_repository
from utils.gcp import get_datastore_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_users_platform():
    client = get_datastore_client()
    query = client.query(kind="User")
    entities = list(query.fetch())
    
    logger.info(f"Found {len(entities)} User entities to check.")
    
    updated_count = 0
    for entity in entities:
        if "platform" not in entity:
            entity["platform"] = "telegram"
            client.put(entity)
            updated_count += 1
            if updated_count % 100 == 0:
                logger.info(f"Updated {updated_count} users...")

    # Also check InlineUser kind if any
    inline_query = client.query(kind="InlineUser")
    inline_entities = list(inline_query.fetch())
    logger.info(f"Found {len(inline_entities)} InlineUser entities to check.")
    
    for entity in inline_entities:
        if "platform" not in entity:
            entity["platform"] = "telegram"
            client.put(entity)
            updated_count += 1
            if updated_count % 100 == 0:
                logger.info(f"Updated {updated_count} users total...")

    logger.info(f"Migration complete. Total users updated: {updated_count}")


if __name__ == "__main__":
    migrate_users_platform()
