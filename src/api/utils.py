from typing import Any, cast
from litestar import Request
from core.config import config
from infrastructure.protocols import ProposalRepository, LongProposalRepository


def get_proposals_context(
    request: Request,
    proposal_repo: ProposalRepository,
    long_proposal_repo: LongProposalRepository,
) -> dict[str, Any]:
    filters = {k: v for k, v in request.query_params.items() if k not in ["search"]}
    search_query = request.query_params.get("search", "")

    if "voting_ended" not in filters:
        filters["voting_ended"] = False

    all_short = proposal_repo.get_proposals(search=search_query, limit=50, **filters)
    all_long = long_proposal_repo.get_proposals(
        search=search_query, limit=50, **filters
    )

    user_session = cast(dict[str, str] | None, request.session.get("user"))
    is_htmx = bool(getattr(request, "htmx", False))

    return {
        "pending_short": all_short,
        "pending_long": all_long,
        "user": user_session,
        "owner_id": config.owner_id,
        "is_htmx": is_htmx,
        "request": request,
    }
