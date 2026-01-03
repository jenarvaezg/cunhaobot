import pytest
from unittest.mock import MagicMock, patch, AsyncMock, PropertyMock
from services.ai_service import AIService, phrase_generator_agent


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
        with (
            patch.object(
                phrase_generator_agent, "run", new_callable=AsyncMock
            ) as mock_run,
            patch("services.phrase_service", create=True) as mock_phrase_service,
        ):
            mock_phrase_service.get_phrases.return_value = []

            mock_result = MagicMock()
            mock_result.output.phrases = ["Frase 1", "Frase 2", "Frase 3"]
            mock_run.return_value = mock_result

            service = AIService(api_key="valid_key")
            phrases = await service.generate_cunhao_phrases(count=2)

            assert phrases == ["Frase 1", "Frase 2"]
            mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_cunhao_phrases_quota_error(self):
        """Test handling of 429 error."""
        with (
            patch.object(
                phrase_generator_agent, "run", new_callable=AsyncMock
            ) as mock_run,
            patch("services.phrase_service", create=True) as mock_phrase_service,
        ):
            mock_phrase_service.get_phrases.return_value = []
            # Simulate 429 in a way that shows up in the exception string
            mock_run.side_effect = Exception("429 Resource Exhausted")

            service = AIService(api_key="valid_key")
            phrases = await service.generate_cunhao_phrases(count=5)

            assert len(phrases) == 1
            assert "Quota de AI agotada" in phrases[0]

    @pytest.mark.asyncio
    async def test_generate_cunhao_phrases_other_error(self):
        """Test handling of other errors."""
        with (
            patch.object(
                phrase_generator_agent, "run", new_callable=AsyncMock
            ) as mock_run,
            patch("services.phrase_service", create=True) as mock_phrase_service,
        ):
            mock_phrase_service.get_phrases.return_value = []
            mock_run.side_effect = Exception("Boom")

            service = AIService(api_key="valid_key")
            with pytest.raises(Exception, match="Boom"):
                await service.generate_cunhao_phrases(count=5)

    @pytest.mark.asyncio
    async def test_generate_cunhao_phrases_with_context(self):
        """Test generation with explicitly provided context phrases."""
        with (
            patch.object(
                phrase_generator_agent, "run", new_callable=AsyncMock
            ) as mock_run,
            patch("services.phrase_service", create=True) as mock_phrase_service,
        ):
            mock_result = MagicMock()
            mock_result.output.phrases = ["Gen 1", "Gen 2"]
            mock_run.return_value = mock_result

            service = AIService(api_key="valid_key")
            context = ["Context 1", "Context 2"]
            phrases = await service.generate_cunhao_phrases(
                count=2, context_phrases=context
            )

            assert phrases == ["Gen 1", "Gen 2"]
            mock_run.assert_called_once()
            # Verify phrase_service was NOT used
            mock_phrase_service.get_phrases.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_cunhao_phrases_context_fetch_error(self):
        """Test that generation continues even if context fetching fails."""
        with (
            patch.object(
                phrase_generator_agent, "run", new_callable=AsyncMock
            ) as mock_run,
            patch("services.phrase_service", create=True) as mock_phrase_service,
        ):
            mock_phrase_service.get_phrases.side_effect = Exception("DB Error")
            mock_result = MagicMock()
            mock_result.output.phrases = ["Gen 1"]
            mock_run.return_value = mock_result

            service = AIService(api_key="valid_key")
            phrases = await service.generate_cunhao_phrases(count=1)

            assert phrases == ["Gen 1"]
            mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_image_success(self):
        """Test successful image generation."""
        service = AIService(api_key="valid_key")
        mock_client = MagicMock()
        with patch.object(
            AIService, "client", new_callable=PropertyMock
        ) as mock_client_prop:
            mock_client_prop.return_value = mock_client

            mock_response = MagicMock()
            mock_part = MagicMock()
            mock_part.inline_data.data = b"fake_image_bytes"
            mock_part.text = None
            mock_response.candidates = [MagicMock(content=MagicMock(parts=[mock_part]))]
            mock_client.models.generate_content.return_value = mock_response

            image_bytes = await service.generate_image("test phrase")
            assert image_bytes == b"fake_image_bytes"

    @pytest.mark.asyncio
    async def test_generate_image_base64_fallback(self):
        """Test image generation with base64 text fallback."""
        import base64

        fake_data = b"fake_image_bytes"
        encoded_data = base64.b64encode(fake_data).decode()

        service = AIService(api_key="valid_key")
        mock_client = MagicMock()
        with patch.object(
            AIService, "client", new_callable=PropertyMock
        ) as mock_client_prop:
            mock_client_prop.return_value = mock_client

            mock_response = MagicMock()
            mock_part = MagicMock()
            mock_part.inline_data = None
            # Needs to be long to trigger fallback
            mock_part.text = encoded_data.ljust(1001, " ")
            mock_response.candidates = [MagicMock(content=MagicMock(parts=[mock_part]))]
            mock_client.models.generate_content.return_value = mock_response

            image_bytes = await service.generate_image("test phrase")
            assert image_bytes == fake_data

    @pytest.mark.asyncio
    async def test_generate_image_no_data_error(self):
        """Test error when no image data is found."""
        service = AIService(api_key="valid_key")
        mock_client = MagicMock()
        with patch.object(
            AIService, "client", new_callable=PropertyMock
        ) as mock_client_prop:
            mock_client_prop.return_value = mock_client

            mock_response = MagicMock()
            mock_response.candidates = [MagicMock(content=MagicMock(parts=[]))]
            mock_client.models.generate_content.return_value = mock_response

            with pytest.raises(
                ValueError, match="No candidates or parts in AI response"
            ):
                await service.generate_image("test phrase")

    @pytest.mark.asyncio
    async def test_analyze_image_success(self):
        """Test successful image analysis."""
        service = AIService(api_key="valid_key")
        mock_client = MagicMock()
        with patch.object(
            AIService, "client", new_callable=PropertyMock
        ) as mock_client_prop:
            mock_client_prop.return_value = mock_client

            mock_response = MagicMock()
            mock_response.text = "Eso está mal alicatao"
            mock_client.models.generate_content.return_value = mock_response

            roast = await service.analyze_image(b"fake_image_bytes")
            assert roast == "Eso está mal alicatao"
            mock_client.models.generate_content.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_image_error(self):
        """Test handling of error in image analysis."""
        service = AIService(api_key="valid_key")
        mock_client = MagicMock()
        with patch.object(
            AIService, "client", new_callable=PropertyMock
        ) as mock_client_prop:
            mock_client_prop.return_value = mock_client
            mock_client.models.generate_content.side_effect = Exception("AI Error")

            roast = await service.analyze_image(b"fake_image_bytes")
            assert "Error" in roast

    @pytest.mark.asyncio
    async def test_analyze_sentiment_and_react_success(self):
        """Test successful sentiment reaction."""
        service = AIService(api_key="valid_key")
        mock_client = MagicMock()
        with patch.object(
            AIService, "client", new_callable=PropertyMock
        ) as mock_client_prop:
            mock_client_prop.return_value = mock_client

            mock_response = MagicMock()
            mock_response.text = "🍺"
            mock_client.models.generate_content.return_value = mock_response

            emoji = await service.analyze_sentiment_and_react("Quiero una caña")
            assert emoji == "🍺"
            mock_client.models.generate_content.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_sentiment_and_react_none(self):
        """Test reaction when sentiment is neutral (NONE)."""
        service = AIService(api_key="valid_key")
        mock_client = MagicMock()
        with patch.object(
            AIService, "client", new_callable=PropertyMock
        ) as mock_client_prop:
            mock_client_prop.return_value = mock_client

            mock_response = MagicMock()
            mock_response.text = "NONE"
            mock_client.models.generate_content.return_value = mock_response

            emoji = await service.analyze_sentiment_and_react("Hola")
            assert emoji is None

    @pytest.mark.asyncio
    async def test_analyze_sentiment_and_react_invalid(self):
        """Test reaction when response is not an emoji."""
        service = AIService(api_key="valid_key")
        mock_client = MagicMock()
        with patch.object(
            AIService, "client", new_callable=PropertyMock
        ) as mock_client_prop:
            mock_client_prop.return_value = mock_client

            mock_response = MagicMock()
            mock_response.text = "Esto es un texto largo que no es un emoji"
            mock_client.models.generate_content.return_value = mock_response

            emoji = await service.analyze_sentiment_and_react("Texto")
            assert emoji is None

    @pytest.mark.asyncio
    async def test_analyze_sentiment_and_react_error(self):
        """Test error handling in sentiment reaction."""
        service = AIService(api_key="valid_key")
        mock_client = MagicMock()
        with patch.object(
            AIService, "client", new_callable=PropertyMock
        ) as mock_client_prop:
            mock_client_prop.return_value = mock_client
            mock_client.models.generate_content.side_effect = Exception("API Error")

            emoji = await service.analyze_sentiment_and_react("Texto")
            assert emoji is None
