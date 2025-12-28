import pytest
from unittest.mock import MagicMock
from tg.handlers.utils.error import error_handler


@pytest.mark.asyncio
async def test_error_handler():
    context = MagicMock()
    context.error = ValueError("test error")
    with pytest.raises(ValueError):
        await error_handler(MagicMock(), context)
