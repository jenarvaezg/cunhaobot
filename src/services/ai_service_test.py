import pytest
from unittest.mock import MagicMock, patch
from services.ai_service import AIService


class TestAIService:
    def test_client_init_error(self):
        """Test client raises ValueError if API key is missing or dummy."""
        service = AIService(api_key="")
        with pytest.raises(ValueError, match="GEMINI_API_KEY not set or invalid"):
            _ = service.client

        service = AIService(api_key="dummy")
        with pytest.raises(ValueError, match="GEMINI_API_KEY not set or invalid"):
            _ = service.client

    def test_client_init_success(self):
        """Test client initializes correctly with valid key."""
        with patch("google.genai.Client") as mock_client_cls:
            service = AIService(api_key="valid_key")
            client = service.client
            mock_client_cls.assert_called_once_with(api_key="valid_key")
            assert client == mock_client_cls.return_value
            # Check singleton behavior
            assert service.client == client
            mock_client_cls.assert_called_once()  # Should not be called again

    @pytest.mark.asyncio
    async def test_generate_cunhao_phrases_success(self):
        """Test generation success."""
        with patch("google.genai.Client") as mock_client_cls:
            mock_client_instance = mock_client_cls.return_value
            mock_response = MagicMock()
            mock_response.text = "Frase 1\nFrase 2\nFrase 3"
            mock_client_instance.models.generate_content.return_value = mock_response

            service = AIService(api_key="valid_key")
            phrases = await service.generate_cunhao_phrases(count=2)

            assert phrases == ["Frase 1", "Frase 2"]
            mock_client_instance.models.generate_content.assert_called_once()
            args, kwargs = mock_client_instance.models.generate_content.call_args
            assert kwargs["model"] == "gemini-2.5-flash"

    @pytest.mark.asyncio
    async def test_generate_cunhao_phrases_quota_error(self):
        """Test handling of 429 error."""
        with patch("google.genai.Client") as mock_client_cls:
            mock_client_instance = mock_client_cls.return_value
            # Simulate 429
            mock_client_instance.models.generate_content.side_effect = Exception(
                "429 Resource Exhausted"
            )

            service = AIService(api_key="valid_key")
            phrases = await service.generate_cunhao_phrases(count=5)

            assert len(phrases) == 1
            assert "Quota de AI agotada" in phrases[0]

    @pytest.mark.asyncio
    async def test_generate_cunhao_phrases_other_error(self):
        """Test handling of other errors."""
        with patch("google.genai.Client") as mock_client_cls:
            mock_client_instance = mock_client_cls.return_value
            mock_client_instance.models.generate_content.side_effect = Exception("Boom")

            service = AIService(api_key="valid_key")
            with pytest.raises(Exception, match="Boom"):
                await service.generate_cunhao_phrases(count=5)
