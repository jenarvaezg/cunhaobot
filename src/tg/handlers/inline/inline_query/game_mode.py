from telegram import InlineQueryResultGame
from typing import Any


async def get_game_mode_results(query: str) -> list[Any]:
    """Return the game as an inline result."""
    return [
        InlineQueryResultGame(
            id="palillo_cunhao_game", game_short_name="palillo_cunhao"
        )
    ]
