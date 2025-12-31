import asyncio
import logging
import os
import sys

# Add src to path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting phrase score calculation...")
    
    # Import here to ensure environment variables are already loaded
    from models.phrase import Phrase, LongPhrase
    from models.proposal import Proposal, LongProposal
    from infrastructure.datastore.phrase import phrase_repository, long_phrase_repository
    from infrastructure.datastore.proposal import proposal_repository, long_proposal_repository

    # Load all phrases
    phrases = phrase_repository.load_all()
    long_phrases = long_phrase_repository.load_all()
    
    logger.info(f"Loaded {len(phrases)} Phrases and {len(long_phrases)} LongPhrases.")

    # Load all proposals to have them in memory for faster lookup if needed
    # (Though we can also load them one by one)
    proposals_map = {p.id: p for p in proposal_repository.load_all()}
    long_proposals_map = {p.id: p for p in long_proposal_repository.load_all()}
    
    logger.info(f"Loaded {len(proposals_map)} Proposals and {len(long_proposals_map)} LongProposals for reference.")

    def calculate_score(phrase, p_map):
        score = phrase.usages
        if phrase.proposal_id and phrase.proposal_id in p_map:
            proposal = p_map[phrase.proposal_id]
            likes = len(proposal.liked_by)
            dislikes = len(proposal.disliked_by)
            score += (likes - dislikes) * 5
        return int(score)

    # Process Phrases
    updated_phrases = 0
    for p in phrases:
        new_score = calculate_score(p, proposals_map)
        if p.score != new_score:
            p.score = new_score
            phrase_repository.save(p)
            updated_phrases += 1
            if updated_phrases % 50 == 0:
                logger.info(f"Updated {updated_phrases} Phrases...")

    # Process LongPhrases
    updated_long_phrases = 0
    for p in long_phrases:
        new_score = calculate_score(p, long_proposals_map)
        if p.score != new_score:
            p.score = new_score
            long_phrase_repository.save(p)
            updated_long_phrases += 1
            if updated_long_phrases % 50 == 0:
                logger.info(f"Updated {updated_long_phrases} LongPhrases...")

    logger.info(f"Finished. Updated {updated_phrases} Phrases and {updated_long_phrases} LongPhrases.")

def load_env():
    """Load .env.local or .env file manually."""
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
                        if (value.startswith('"') and value.endswith('"')) or \
                           (value.startswith("'") and value.endswith("'")):
                            value = value[1:-1]
                        os.environ[key] = value
            return
    logger.warning("No .env.local or .env file found.")

if __name__ == "__main__":
    load_env()
    
    # Mock required vars if missing to satisfy initialization
    required_vars = ["TG_TOKEN", "MOD_CHAT_ID", "SESSION_SECRET", "OWNER_ID", "SLACK_CLIENT_ID", "SLACK_CLIENT_SECRET"]
    for var in required_vars:
        if var not in os.environ:
            os.environ[var] = "0" if "ID" in var else "dummy"
        
    asyncio.run(main())
