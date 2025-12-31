import logging
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


# Singleton instance
ai_service = AIService()
