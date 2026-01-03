import logging
import os
import random
from typing import cast
from google import genai
from pydantic import BaseModel
from pydantic_ai import Agent
from core.config import config

logger = logging.getLogger(__name__)


class GeneratedPhrases(BaseModel):
    """Model for the generated cuñao phrases."""

    phrases: list[str]


# Ensure API key is set for pydantic-ai (it looks for GOOGLE_API_KEY)
# Using a dummy key for tests if not provided
os.environ.setdefault("GOOGLE_API_KEY", config.gemini_api_key or "dummy_key_for_tests")

phrase_generator_agent: Agent[None, GeneratedPhrases] = Agent(
    "google-gla:gemini-2.5-flash",
    output_type=GeneratedPhrases,
    system_prompt=(
        "Actúa como un 'cuñao' español de manual en una barra de bar. "
        "Genera frases lapidarias, cortas y directas. "
        "REGLAS CRÍTICAS: "
        "1. CADA FRASE DEBE TENER UNA SOLA IDEA O CONCEPTO (No mezcles temas). "
        "2. BREVEDAD: Máximo 15-20 palabras por frase. Que sean 'perlas' rápidas. "
        "3. TONO: Sentando cátedra, rancio, nostálgico, escéptico y políticamente incorrecto. "
        "4. TEMAS: Odio a lo moderno, el diésel, la mili, negacionismo climático de bar, chuletón, "
        "los jóvenes no quieren trabajar, nacionalismo rancio, machismo rancio."
    ),
)


class AIService:
    def __init__(self, api_key: str | None = config.gemini_api_key):
        self._api_key = api_key
        self._client: genai.Client | None = None

    async def analyze_image(
        self, image_bytes: bytes, mime_type: str = "image/jpeg"
    ) -> str:
        """Analyzes an image and returns a cuñao-style roast using Gemini 2.0 Flash."""
        prompt = (
            "Actúa como un cuñao experto de barra de bar. "
            "Mira esta foto y suelta una crítica lapidaria, rancia y breve (máximo 15 palabras). "
            "Usa frases como 'Eso está mal alicatao', 'Menuda chapuza', 'Vaya pérdida de dinero', 'En mi pueblo lo hacemos mejor'. "
            "Sé condescendiente y sabelotodo. No saludes. No seas amable. Directo al fallo."
        )

        try:
            # We use gemini-2.0-flash for fast and high quality vision roast
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    prompt,
                    genai.types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                ],
            )

            if not response or not response.text:
                return "No tengo palabras para esta chapuza. (Sin respuesta)"

            return response.text.strip()
        except Exception as e:
            logger.error(f"Error in analyze_image: {e}")
            return "Eso es una milonga, no me deja ni verlo. (Error)"

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            if not self._api_key or self._api_key == "dummy":
                logger.error("GEMINI_API_KEY not set or invalid")
                raise ValueError("GEMINI_API_KEY not set or invalid")
            try:
                self._client = genai.Client(api_key=self._api_key)
            except Exception:
                logger.exception("Error initializing Gemini client:")
                raise
        return cast(genai.Client, self._client)

    async def generate_cunhao_phrases(
        self,
        count: int = 5,
        context_phrases: list[str] | None = None,
    ) -> list[str]:
        """Generates cuñao-style phrases using pydantic-ai, with database context."""

        existing_phrases = context_phrases if context_phrases is not None else []

        if not existing_phrases:
            from services import phrase_service

            try:
                # Get a sample of existing phrases to avoid repetition and set style
                all_short = phrase_service.get_phrases("", long=False)
                all_long = phrase_service.get_phrases("", long=True)

                sample_short = random.sample(all_short, min(len(all_short), 10))
                sample_long = random.sample(all_long, min(len(all_long), 10))

                existing_phrases = [p.text for p in sample_short + sample_long]
            except Exception as e:
                logger.warning(f"Could not fetch phrases for context: {e}")

        context_msg = ""
        if existing_phrases:
            # Limit context if it's too huge, though likely fine
            sample_context = (
                existing_phrases[:20]
                if len(existing_phrases) > 20
                else existing_phrases
            )
            context_str = "\n".join([f"- {p}" for p in sample_context])
            context_msg = f"\nAquí tienes ejemplos de frases que ya existen (ÚSALAS COMO INSPIRACIÓN PERO NO LAS REPITAS):\n{context_str}"

        prompt = f"Genera {count} frases nuevas e inspiradas.{context_msg}"

        try:
            result = await phrase_generator_agent.run(prompt)
            return result.output.phrases[:count]

        except Exception as e:
            logger.exception("Error generating cuñao phrases with pydantic-ai:")
            if "429" in str(e):
                return [
                    "⚠️ Quota de AI agotada. ¡Paco no puede más con el calor! Reintenta en un momento."
                ]
            raise e

    async def generate_image(self, phrase: str) -> bytes:
        """Generates an image from a phrase using the nanobanana pattern (Gemini 2.5 Flash Image)."""
        model_name = os.getenv("NANOBANANA_MODEL", "gemini-2.5-flash-image")
        prompt = f"""
A high-quality, satirical and funny illustration of a stereotypical Spanish 'cuñado'
(a middle-aged man with a mustache, wearing a classic polo shirt or a vest)
acting out or representing this phrase: "{phrase}".
The style should be a modern comic or a realistic but slightly caricatured digital painting.
Set the scene in a typical Spanish bar with a wooden counter and beer tapas.
"""
        try:
            # Following nanobanana pattern: use generate_content with gemini-2.5-flash-image
            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt,
            )

            if not response.candidates or not response.candidates[0].content.parts:
                raise ValueError("No candidates or parts in AI response")

            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    return part.inline_data.data
                # Fallback: check if it's in text (some versions might put base64 in text)
                if part.text and len(part.text) > 1000:
                    import base64

                    try:
                        return base64.b64decode(part.text)
                    except Exception:
                        continue

            raise ValueError("No image data found in AI response parts")
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            raise e

    async def analyze_sentiment_and_react(self, text: str) -> str | None:
        """Analyzes text sentiment and returns a reaction emoji or None."""
        if not text:
            return None

        prompt = (
            f"Eres el CuñaoBot. Analiza este mensaje: '{text}'. "
            "Tu misión es reaccionar SOLO si el mensaje es un 'caramelo' para un cuñado. "
            "Si es una conversación normal, aburrida o neutra, responde 'NONE'. "
            "Solo si detectas ALGO MUY CLARO responde ÚNICAMENTE con UNO de estos emojis: 🍺, 🇪🇸, 🥘, 🤡, 👎, ❤️, 🔥, 😂. "
            "\nEJEMPLOS CLAROS:\n"
            "- 'Viva España', 'Arriba': 🇪🇸\n"
            "- 'Me voy de cañas', 'Cerveza': 🍺\n"
            "- 'Esto es una vergüenza', 'Vaya estafa': 👎\n"
            "- 'Qué buena está la paella', 'Cocido': 🥘\n"
            "- 'La tierra es plana', 'El 5G nos controla' (SOLO verdaderas estupideces): 🤡\n"
            "- 'Te quiero', 'Grande': ❤️\n"
            "- 'Hola', '¿Qué tal?', 'Luego nos vemos' (Conversación normal): NONE\n"
            "- Opiniones moderadas o datos: NONE\n"
            "\nREGLA DE ORO: Ante la duda, responde 'NONE'. No seas un spammer de reacciones, especialmente con el 🤡."
        )

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )

            if not response or not response.text:
                return None

            result = response.text.strip()
            if result == "NONE":
                return None

            # Strict validation: Only allow specific emojis
            allowed = ["🍺", "🇪🇸", "🥘", "🤡", "👎", "❤️", "🔥", "😂"]

            # Check if any allowed emoji is in the result
            for e in allowed:
                if e in result:
                    return e

            return None

        except Exception as e:
            logger.error(f"Error in analyze_sentiment_and_react: {e}")
            return None


# Singleton instance
ai_service = AIService()
