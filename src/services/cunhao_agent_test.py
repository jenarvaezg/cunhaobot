import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from services.cunhao_agent import CunhaoAgent


@pytest.mark.asyncio
async def test_answer_calls_agent():
    service = CunhaoAgent(api_key="valid_key")
    mock_agent = AsyncMock()
    mock_agent.run.return_value = MagicMock(output="Respuesta de prueba")

    with patch.object(
        CunhaoAgent, "agent", new_callable=PropertyMock
    ) as mock_agent_prop:
        mock_agent_prop.return_value = mock_agent
        response = await service.answer("Hola")

        assert response == "Respuesta de prueba"
        # In the new version we pass deps
        mock_agent.run.assert_called_once()
        args, kwargs = mock_agent.run.call_args
        assert args[0] == "Hola"


@pytest.mark.asyncio
async def test_answer_handles_error():
    service = CunhaoAgent(api_key="valid_key")
    mock_agent = AsyncMock()
    mock_agent.run.side_effect = Exception("Error de API")

    with patch.object(
        CunhaoAgent, "agent", new_callable=PropertyMock
    ) as mock_agent_prop:
        mock_agent_prop.return_value = mock_agent
        response = await service.answer("Hola")

        assert "(Error)" in response
