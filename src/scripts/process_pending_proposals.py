import asyncio
import logging
import os
import sys

# Add src to path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from models.proposal import Proposal, LongProposal
from tg import get_tg_application
from tg.handlers.utils.callback_query import approve_proposal, dismiss_proposal

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Starting pending proposals processing...")
    
    # Initialize Bot
    application = get_tg_application()
    await application.initialize()
    bot = application.bot

    # Load all proposals
    # Datastore might paginate, load_all should handle it
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
        
        if likes >= 4:
            logger.info(f"✅ Approving '{p.text}' (ID: {p.id}) - Likes: {likes}")
            try:
                await approve_proposal(p, bot)
                processed_count += 1
                # Small delay to avoid hitting API limits
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"Error approving proposal {p.id}: {e}")
                
        elif dislikes >= 4:
            logger.info(f"❌ Rejecting '{p.text}' (ID: {p.id}) - Dislikes: {dislikes}")
            try:
                await dismiss_proposal(p, bot)
                processed_count += 1
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"Error dismissing proposal {p.id}: {e}")

    logger.info(f"Finished processing. Total actions taken: {processed_count}")

if __name__ == "__main__":
    if "TG_TOKEN" not in os.environ:
        logger.error("TG_TOKEN environment variable is required.")
        sys.exit(1)
        
    asyncio.run(main())
