import os
import sys
import logging
from google.cloud import datastore

# Add src to path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from utils.gcp import get_datastore_client

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def migrate_kind(client: datastore.Client, kind: str) -> int:
    query = client.query(kind=kind)
    entities = list(query.fetch())
    
    logger.info(f"Checking {len(entities)} {kind} entities...")
    
    to_update = []
    for entity in entities:
        if "platform" not in entity:
            entity["platform"] = "telegram"
            to_update.append(entity)
    
    if not to_update:
        logger.info(f"No {kind} entities need updating.")
        return 0
    
    # Use batches of 500 (max allowed by Datastore)
    batch_size = 500
    for i in range(0, len(to_update), batch_size):
        batch = to_update[i : i + batch_size]
        client.put_multi(batch)
        logger.info(f"Updated {i + len(batch)}/{len(to_update)} {kind} entities...")
    
    return len(to_update)


def migrate_users_platform():
    client = get_datastore_client()
    
    total_updated = 0
    total_updated += migrate_kind(client, "User")
    total_updated += migrate_kind(client, "InlineUser")
    
    logger.info(f"Migration complete. Total entities updated: {total_updated}")


if __name__ == "__main__":
    migrate_users_platform()