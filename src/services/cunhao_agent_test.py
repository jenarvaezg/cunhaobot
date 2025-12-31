import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.cunhao_agent import cunhao_agent, agent


@pytest.mark.asyncio
async def test_answer_calls_agent():
    with (
        patch.object(agent, "run", new_callable=AsyncMock) as mock_run,
        patch("services.cunhao_agent.config") as mock_config,
    ):
        mock_config.gemini_api_key = "valid_key"
        mock_run.return_value = MagicMock(output="Respuesta de prueba")

        response = await cunhao_agent.answer("Hola")

        assert response == "Respuesta de prueba"
        mock_run.assert_called_once_with("Hola")


@pytest.mark.asyncio
async def test_answer_handles_error():
    with (
        patch.object(agent, "run", new_callable=AsyncMock) as mock_run,
        patch("services.cunhao_agent.config") as mock_config,
    ):
        mock_config.gemini_api_key = "valid_key"
        mock_run.side_effect = Exception("Error de API")

        response = await cunhao_agent.answer("Hola")

        assert "Error interno" in response
