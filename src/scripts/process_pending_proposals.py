import asyncio
import logging
import os
import sys

# Add src to path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from telegram.error import RetryAfter, TimedOut, NetworkError
# Moved imports to main to ensure env vars are loaded first

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def safe_execute(action_name, coro, p_id):
    """Executes a coroutine with flood control handling."""
    max_retries = 3
    for i in range(max_retries):
        try:
            await coro
            return True
        except RetryAfter as e:
            wait_time = e.retry_after + 2
            logger.warning(f"⚠️ Flood control triggered for {action_name} (ID: {p_id}). Sleeping for {wait_time}s...")
            await asyncio.sleep(wait_time)
        except (TimedOut, NetworkError) as e:
            wait_time = 5 * (i + 1)
            logger.warning(f"⚠️ Network error for {action_name} (ID: {p_id}): {e}. Retrying in {wait_time}s...")
            await asyncio.sleep(wait_time)
        except Exception as e:
            logger.error(f"❌ Critical error executing {action_name} (ID: {p_id}): {e}")
            return False
    
    logger.error(f"❌ Failed to execute {action_name} (ID: {p_id}) after {max_retries} retries.")
    return False


async def main():
    logger.info("Starting pending proposals processing...")
    
    # Import here to ensure environment variables are already loaded
    from tg import get_tg_application
    from tg.handlers.utils.callback_query import approve_proposal, dismiss_proposal
    from models.proposal import Proposal, LongProposal

    # Initialize Bot
    application = get_tg_application()
    await application.initialize()
    bot = application.bot

    # Load all proposals
    proposals = Proposal.load_all()
    long_proposals = LongProposal.load_all()
    
    all_pending = [
        p for p in proposals + long_proposals 
        if not p.voting_ended
    ]
    
    logger.info(f"Found {len(all_pending)} pending proposals.")
    
    processed_count = 0
    
    for p in all_pending:
        likes = len(p.liked_by)
        dislikes = len(p.disliked_by)
        
        # Determine action
        action_coro = None
        action_name = ""
        
        if likes >= 4:
            action_name = "APPROVE"
            logger.info(f"Processing '{p.text}' (ID: {p.id}) -> APPROVE (Likes: {likes})")
            action_coro = approve_proposal(p, bot)
        elif dislikes >= 4:
            action_name = "DISMISS"
            logger.info(f"Processing '{p.text}' (ID: {p.id}) -> DISMISS (Dislikes: {dislikes})")
            action_coro = dismiss_proposal(p, bot)
            
        # Execute if action needed
        if action_coro:
            success = await safe_execute(action_name, action_coro, p.id)
            if success:
                processed_count += 1
                # Conservative baseline delay between actions
                await asyncio.sleep(3.0)

    logger.info(f"Finished processing. Total actions taken: {processed_count}")

def load_env():
    """Load .env.local or .env file manually."""
    # Script is in src/scripts, so root is two levels up
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    for env_file in [".env.local", ".env"]:
        path = os.path.join(root_dir, env_file)
        if os.path.exists(path):
            logger.info(f"Loading environment from {path}")
            with open(path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, value = line.split("=", 1)
                        # Remove quotes if present
                        if (value.startswith('"') and value.endswith('"')) or \
                           (value.startswith("'") and value.endswith("'")):
                            value = value[1:-1]
                        os.environ[key] = value
            return
    logger.warning("No .env.local or .env file found.")

if __name__ == "__main__":
    load_env()
    
    # Force removal of emulator host to ensure production connection
    if "DATASTORE_EMULATOR_HOST" in os.environ:
        logger.info("Removing DATASTORE_EMULATOR_HOST to ensure production connection.")
        del os.environ["DATASTORE_EMULATOR_HOST"]

    if "TG_TOKEN" not in os.environ:
        logger.error("TG_TOKEN environment variable is required.")
        sys.exit(1)

    # Mock other required vars if missing to satisfy Config.from_env()
    required_vars = ["MOD_CHAT_ID", "SESSION_SECRET", "OWNER_ID", "SLACK_CLIENT_ID", "SLACK_CLIENT_SECRET"]
    for var in required_vars:
        if var not in os.environ:
            logger.warning(f"{var} not found in env, using dummy value.")
            os.environ[var] = "0" if "ID" in var else "dummy"
        
    asyncio.run(main())