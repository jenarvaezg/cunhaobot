import os
import sys
from datetime import datetime, timezone

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from infrastructure.datastore.user import user_repository
from infrastructure.datastore.chat import chat_repository
from models.chat import Chat
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate():
    logger.info("Starting comprehensive migration of Users and Chats...")

    # 1. Migrate everything to the new structure
    # We use ignore_gdpr=True because we need to create the Chat entities 
    # even for GDPR users (just marked as inactive)
    users = user_repository.load_all(ignore_gdpr=True)
    migrated_chats_count = 0
    cleaned_users_count = 0

    for user in users:
        is_group_like = (isinstance(user.id, int) and user.id < 0) or getattr(user, "is_group", False)
        
        # Create a Chat entity for EVERY user/group
        logger.info(f"Creating Chat for {user.name} ({user.id})...")
        
        chat_type = "private"
        if is_group_like:
            chat_type = "group" # Could be supergroup but group is safe default
            
        chat = Chat(
            id=user.id,
            platform=user.platform,
            title=user.name,
            username=user.username,
            type=chat_type,
            usages=user.usages if is_group_like else 1, # Minimal usages for people
            is_active=not user.gdpr, # If GDPR is on, chat is inactive
            created_at=user.created_at or datetime.now(timezone.utc),
            last_seen_at=datetime.now(timezone.utc)
        )
        chat_repository.save(chat)
        migrated_chats_count += 1

        # If it was a group entity in the User kind, delete it from there
        if is_group_like:
            logger.info(f"Removing group entity {user.id} from User repository")
            user_repository.delete(user.id)
            cleaned_users_count += 1
        else:
            # It's a real person. We keep it but we might want to clean up is_group field if datastore was messy.
            # user_repository.save(user) # User model no longer has is_group, so save() will strip it.
            pass

    logger.info(f"Migration finished.")
    logger.info(f"- Total Chats created: {migrated_chats_count}")
    logger.info(f"- Group entities removed from User kind: {cleaned_users_count}")


if __name__ == "__main__":
    migrate()