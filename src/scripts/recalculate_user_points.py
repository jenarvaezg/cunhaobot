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
    logger.info("Starting user points recalculation...")
    
    # Import here to ensure environment variables are already loaded
    from infrastructure.datastore.user import user_repository
    from infrastructure.datastore.phrase import phrase_repository, long_phrase_repository
    from infrastructure.datastore.proposal import proposal_repository, long_proposal_repository
    
    users = user_repository.load_all(ignore_gdpr=True)
    logger.info(f"Loaded {len(users)} users.")
    
    # Load phrases and proposals for lookup
    all_phrases = phrase_repository.load_all() + long_phrase_repository.load_all()
    all_proposals = proposal_repository.load_all() + long_proposal_repository.load_all()
    
    proposals_map = {p.id: p for p in all_proposals}
    
    logger.info(f"Loaded {len(all_phrases)} phrases and {len(all_proposals)} proposals.")
    
    updated_count = 0
    
    for user in users:
        # 1. Base points from usages (1 point per usage)
        calculated_points = user.usages
        
        # 2. Points from accepted phrases
        user_phrases = [p for p in all_phrases if p.user_id == user.id]
        
        points_from_phrases = 0
        points_from_votes = 0
        
        for phrase in user_phrases:
            # 10 points for having an accepted phrase
            points_from_phrases += 10
            
            # Points for votes on the proposal of this phrase
            if phrase.proposal_id and phrase.proposal_id in proposals_map:
                proposal = proposals_map[phrase.proposal_id]
                # 1 point per vote (like or dislike)
                vote_points = len(proposal.liked_by) + len(proposal.disliked_by)
                points_from_votes += vote_points
        
        total_new_points = calculated_points + points_from_phrases + points_from_votes
        
        if user.points != total_new_points:
            old_points = user.points
            user.points = total_new_points
            user_repository.save(user)
            updated_count += 1
            logger.info(f"User {user.id} ({user.name}): {old_points} -> {total_new_points} "
                        f"(Usages: {calculated_points}, Phrases: {points_from_phrases}, Votes: {points_from_votes})")
            
    logger.info(f"Recalculation complete. Updated {updated_count} users.")

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
