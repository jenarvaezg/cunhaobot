import logging
import os
from google import genai
from typing import List
from core.config import config

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self, api_key: str = config.gemini_api_key):
        self._api_key = api_key
        self._client = None

    @property
    def client(self):
        if self._client is None:
            if not self._api_key or self._api_key == "dummy":
                logger.error("GEMINI_API_KEY not set or invalid")
                raise ValueError("GEMINI_API_KEY not set or invalid")
            try:
                self._client = genai.Client(api_key=self._api_key)
            except Exception:
                logger.exception("Error initializing Gemini client:")
                raise
        return self._client

    async def generate_cunhao_phrases(self, count: int = 5) -> List[str]:
        """Generates cuñao-style phrases using Gemini."""
        prompt = f"""
        Actúa como un "cuñao" español de manual en una barra de bar.
        Genera {count} frases lapidarias, cortas y directas.

        REGLAS CRÍTICAS:
        1. CADA FRASE DEBE TENER UNA SOLA IDEA O CONCEPTO (No mezcles temas).
        2. BREVEDAD: Máximo 15-20 palabras por frase. Que sean "perlas" rápidas.
        3. TONO: Sentando cátedra, rancio, nostálgico, escéptico y políticamente incorrecto.

        Tópicos de ejemplo (elige uno distinto por frase):
        - Odio al lenguaje inclusivo o "moderneces".
        - El coche diésel/manual es lo único que vale.
        - La mili te hacía hombre.
        - El cambio climático es mentira porque hoy hace frío.
        - El chuletón/jamón cura cualquier tontería.
        - Los jóvenes no quieren trabajar.
        - Nacionalismo rancio o prejuicios sobre inmigración/paguitas.
        - Machismo rancio o prejuicios sobre género.

        IMPORTANTE: Devuelve SOLO las frases, una por línea, sin numeración ni explicaciones.
        """

        try:
            client = self.client
            response = client.models.generate_content(
                model="gemini-3-flash", contents=prompt
            )
            phrases = [
                line.strip()
                for line in response.text.strip().split("\n")
                if line.strip()
            ]
            return phrases[:count]
        except Exception as e:
            logger.exception("Error generating cuñao phrases:")
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


# Singleton instance
ai_service = AIService()
