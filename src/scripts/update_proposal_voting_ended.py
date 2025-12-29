import os
import sys

# Add the project's root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.proposal import LongProposal


def run_update_script() -> None:
    all_proposals = LongProposal.get_proposals()
    for proposal in all_proposals:
        print(proposal.text)


if __name__ == "__main__":
    run_update_script()
